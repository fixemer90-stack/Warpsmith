"""Canonical content compiler — Task 1.4.

Transforms wiki/frontmatter markdown into schema-validated, deterministically
serialized JSON artifacts sharded by logical kind and source faction.

Artifact layout::

  data/generated/content/
    manifest.json          → list of all artifacts + source hashes
    factions.json          → all factions
    weapons.json           → all weapons keyed by weapon_id
    detachments.json       → all detachments
    stratagems.json        → all stratagems (faction-agnostic references)
    enhancements.json      → all enhancements
    rules.json             → core / special rules
    units/
      index.json           → lightweight lookup: unit_id → {faction_id, file, display_name, hash}
      <faction>.json       → canonical unit definitions for that faction
    faction_units/
      index.json           → lightweight lookup: faction_id → {file}
      <faction>.json       → availability/link records (not duplicated unit definitions)

Canonical IDs (format ``type:scoped-name``)::

  unit:orks:boyz
  weapon:orks:shoota
  faction:orks
  detachment:orks:waagh
  stratagem:orks:ere_we_go
  enhancement:orks:kunnin
  rule:core:waagh
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

from backend.loader.parser import parse_unit
from backend.loader.registry import WikiRegistry
from backend.loader.schema import (
    DetachmentV1,
    FactionV1,
    UnitIndexEntryV1,
    UnitV1Strict,
    WeaponV1,
)

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "content.v1"
GENERATED_DIR = Path(__file__).parent.parent.parent / "data" / "generated" / "content"

# ── Canonical ID validation ──────────────────────────────────────────────

# Pattern for unit canonical IDs: unit:<scope>:<name>
_VALID_UNIT_CID_RE = re.compile(r"^unit:[a-z][a-z0-9_-]*:[a-z][a-z0-9_-]*$")


def _validate_unit_canonical_id(cid: str, source_path: str) -> str | None:
    """Validate an explicit unit canonical_id format.

    Returns an error message string if invalid, or None if valid.
    The error message includes the source path for actionable diagnostics.
    """
    if not _VALID_UNIT_CID_RE.match(cid):
        return (
            f"Invalid canonical_id '{cid}' in {source_path}: "
            f"expected format 'unit:<scope>:<name>' (e.g. 'unit:orks:boyz')"
        )
    return None


# ── Manifest dataclasses ─────────────────────────────────────────────────


@dataclass
class ManifestEntry:
    filename: str
    sha256: str

    def to_dict(self) -> dict[str, str]:
        return {"filename": self.filename, "sha256": f"sha256:{self.sha256}"}


@dataclass
class Manifest:
    schema_version: str
    generated_at: str
    content_hash: str
    source_paths: list[str]
    source_hashes: dict[str, str]
    artifacts: list[ManifestEntry]
    collisions: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "content_hash": self.content_hash,
            "source_paths": sorted(self.source_paths),
            "source_hashes": dict(sorted(self.source_hashes.items())),
            "artifacts": [a.to_dict() for a in self.artifacts],
            "collisions": self.collisions,
        }


# ── Build context (validation state) ────────────────────────────────────


class BuildContext:
    """Accumulates artifacts, validates cross-refs, tracks collisions."""

    def __init__(self, wiki_path: str):
        self.wiki_path = (
            Path(wiki_path) if wiki_path else Path(__file__).parent.parent.parent / "wiki"
        )
        self.registry = WikiRegistry(str(self.wiki_path))
        self.registry.load(use_cache=False)

        # Canonical records by kind
        self.units: dict[str, dict[str, Any]] = {}  # unit_id → record
        self.weapons: dict[str, dict[str, Any]] = {}  # weapon_id → record
        self.factions: dict[str, dict[str, Any]] = {}  # faction_id → record
        self.detachments: dict[str, dict[str, Any]] = {}  # detachment_id → record
        self.stratagems: dict[str, dict[str, Any]] = {}
        self.enhancements: dict[str, dict[str, Any]] = {}
        self.rules: dict[str, dict[str, Any]] = {}

        # Collision / cross-ref tracking
        self.collisions: list[dict[str, Any]] = []

    def _slug(self, name: str) -> str:
        """Produce a deterministic slug from a display name."""
        return (
            name.lower()
            .replace(" ", "-")
            .replace("'", "")
            .replace('"', "")
            .replace(".", "")
            .replace(",", "")
            .replace("(", "")
            .replace(")", "")
            .replace("!", "")
            .replace("?", "")
            .replace(":", "-")
            .replace("--", "-")
            .strip("-")
        )

    def _make_unit_id(self, name: str, faction: str) -> str:
        return f"unit:{self._slug(faction)}:{self._slug(name)}"

    def _make_weapon_id(self, wname: str, faction: str) -> str:
        return f"weapon:{self._slug(faction)}:{self._slug(wname)}"

    def _make_faction_id(self, name: str) -> str:
        return f"faction:{self._slug(name)}"

    def _weapon_to_dict(self, w: Any) -> dict[str, Any]:
        return {
            "name": getattr(w, "name", ""),
            "type": getattr(w, "type", "ranged"),
            "range_max": getattr(w, "range_max", None),
            "attacks_dice": list(getattr(w, "attacks_dice", (1, 6, 0))),
            "skill": getattr(w, "skill", 5),
            "strength": getattr(w, "strength", 4),
            "ap": getattr(w, "ap", 0),
            "damage_dice": list(getattr(w, "damage_dice", (1, 3, 0))),
            "tags": getattr(w, "tags", []) or [],
            "abilities": getattr(w, "abilities", []) or [],
        }

    def build(self):
        """Run the full build pipeline: collect → validate → emit."""
        self._collect_factions()
        self._collect_units()
        self._collect_weapons()
        self._collect_detachments()
        self._collect_stratagems_enhancements()
        self._validate_cross_refs()
        self._deduplicate_units()

    def _collect_factions(self):
        factions_raw = self.registry.list_factions()
        for f in factions_raw:
            fid = self._make_faction_id(f)
            if fid in self.factions:
                self.collisions.append(
                    {
                        "kind": "faction_id",
                        "id": fid,
                        "sources": [f],
                    }
                )
            self.factions[fid] = {
                "faction_id": fid,
                "display_name": f.title(),
                "unit_count": 0,
                "detachment_count": 0,
            }

    def _collect_units(self):
        """Scan wiki source files directly to detect duplicate display names.

        Iterates source files rather than ``self.registry.units`` (which is
        flattened by unit name), so duplicate display names with different
        explicit canonical IDs are caught before registry collapse.
        """
        source_entries: list[tuple[str, Any, str]] = []  # (_filepath, unit_obj, source_path)

        units_dir = self.wiki_path / "units"
        if not units_dir.exists():
            logger.warning("No units directory at %s", units_dir)
            return

        for faction_dir in sorted(units_dir.iterdir()):
            if not faction_dir.is_dir():
                continue
            for file_path in sorted(faction_dir.glob("*.md")):
                unit = parse_unit(file_path)
                if unit is None:
                    continue
                source_entries.append((str(file_path), unit, str(file_path)))

        # Track display name duplicates across source files
        seen_display_names: dict[str, str] = {}

        for _filepath, unit, source_path in source_entries:
            display_name = unit.name
            fid = self._make_faction_id(unit.faction)

            # Detect duplicate display names before they get collapsed
            if display_name in seen_display_names:
                self.collisions.append(
                    {
                        "kind": "duplicate_display_name",
                        "display_name": display_name,
                        "unit_ids": [],
                        "sources": [seen_display_names[display_name], source_path],
                    }
                )
                # Continue processing both units — they have different source files
            seen_display_names.setdefault(display_name, source_path)

            # Determine unit id: explicit canonical_id or generated fallback
            cid = getattr(unit, "canonical_id", None)
            if cid:
                err = _validate_unit_canonical_id(cid, source_path)
                if err:
                    raise RuntimeError(err)
                uid = cid
                id_kind = "explicit"
            else:
                uid = self._make_unit_id(display_name, unit.faction)
                id_kind = "fallback"

            if uid in self.units:
                existing_source = self.units[uid].get("source_path", "")
                self.collisions.append(
                    {
                        "kind": "unit_id",
                        "id": uid,
                        "id_kind": id_kind,
                        "display_names": [display_name, self.units[uid].get("display_name", "")],
                        "sources": [source_path, existing_source],
                    }
                )
                continue

            weapons_ranged = [self._weapon_to_dict(w) for w in (unit.ranged_weapons or [])]
            weapons_melee = [self._weapon_to_dict(w) for w in (unit.melee_weapons or [])]
            sq = getattr(unit, "squad_size", None) or {"min": 1, "max": 1, "step": 1}

            record = {
                "unit_id": uid,
                "display_name": display_name,
                "faction_id": fid,
                "source_path": source_path,
                "_id_kind": id_kind,
                "category": getattr(unit, "category", "Infantry"),
                "movement": getattr(unit, "movement", 5),
                "toughness": getattr(unit, "toughness", 3),
                "save": getattr(unit, "save", 4),
                "wounds": getattr(unit, "wounds", 1),
                "leadership": getattr(unit, "leadership", 7),
                "objective_control": getattr(unit, "objective_control", 1),
                "points": getattr(unit, "points", 0),
                "model_count": list(getattr(unit, "model_count", (1, 1))),
                "squad_size": sq,
                "ranged_weapons": weapons_ranged,
                "melee_weapons": weapons_melee,
                "abilities": getattr(unit, "abilities", []) or [],
                "keywords": getattr(unit, "keywords", []) or [],
                "faction_keywords": getattr(unit, "faction_keywords", []) or [],
                "tags": getattr(unit, "tags", []) or [],
                "invulnerable_save": getattr(unit, "invulnerable_save", None),
                "feel_no_pain": getattr(unit, "feel_no_pain", None),
                "is_epic_hero": getattr(unit, "is_epic_hero", False),
                "can_be_warlord": getattr(unit, "can_be_warlord", False),
                "is_leader": getattr(unit, "is_leader", False),
                "leader_for": getattr(unit, "leader_for", []) or [],
                "edition": getattr(unit, "edition", "10e"),
            }

            # Strip internal fields before schema validation and storage
            clean_record = {k: v for k, v in record.items() if not k.startswith("_")}

            # Validate against strict schema before storing
            try:
                UnitV1Strict(**clean_record)
            except Exception as exc:
                logger.warning("Unit %s failed schema validation: %s", uid, exc)
                self.collisions.append(
                    {
                        "kind": "schema_failure",
                        "id": uid,
                        "error": str(exc),
                        "source_path": source_path,
                    }
                )
                continue

            self.units[uid] = clean_record
            # Track weapons for weapons.json
            for w in weapons_ranged + weapons_melee:
                wid = self._make_weapon_id(w["name"], unit.faction)
                if wid not in self.weapons:
                    self.weapons[wid] = w

            # Update faction count
            if fid in self.factions:
                self.factions[fid]["unit_count"] = self.factions[fid].get("unit_count", 0) + 1

    def _collect_weapons(self):
        # Already collected as a side-effect of _collect_units
        pass

    def _collect_detachments(self):
        for name, det in self.registry.detachments.items():
            fid = self._make_faction_id(det.faction)
            did = f"detachment:{self._slug(det.faction)}:{self._slug(name)}"
            rule_dict = None
            if det.detachment_rule:
                rule_dict = {
                    "name": det.detachment_rule.name,
                    "description": det.detachment_rule.description,
                }
            record = {
                "name": name,
                "faction_id": fid,
                "description": det.description,
                "detachment_rule": rule_dict,
                "stratagems": [
                    {"name": s.name, "cost": s.cost, "when": s.when, "effect": s.effect}
                    for s in (det.stratagems or [])
                ],
                "enhancements": [
                    {"name": e.name, "points": e.points, "effect": e.effect}
                    for e in (det.enhancements or [])
                ],
            }
            self.detachments[did] = record
            if fid in self.factions:
                self.factions[fid]["detachment_count"] = (
                    self.factions[fid].get("detachment_count", 0) + 1
                )

    def _collect_stratagems_enhancements(self):
        for _did, det in self.detachments.items():
            for s in det.get("stratagems", []):
                key = f"stratagem:{self._slug(s['name'])}"
                if key not in self.stratagems:
                    self.stratagems[key] = s
            for e in det.get("enhancements", []):
                key = f"enhancement:{self._slug(e['name'])}"
                if key not in self.enhancements:
                    self.enhancements[key] = e

    def _validate_cross_refs(self):
        # Validate unit faction_ids reference existing factions
        faction_ids = set(self.factions.keys())
        for uid, record in self.units.items():
            if record["faction_id"] not in faction_ids:
                self.collisions.append(
                    {
                        "kind": "dangling_ref",
                        "field": "unit.faction_id",
                        "id": uid,
                        "ref": record["faction_id"],
                    }
                )

        # Validate detachment faction_ids
        for _did, record in self.detachments.items():
            if record["faction_id"] not in faction_ids:
                # Auto-create placeholder factions for meta-pages (e.g. "core")
                self.factions[record["faction_id"]] = {
                    "faction_id": record["faction_id"],
                    "display_name": record["faction_id"].split(":", 1)[1].title(),
                    "unit_count": 0,
                    "detachment_count": 0,
                }
                faction_ids.add(record["faction_id"])

    def _deduplicate_units(self):
        """Emit collision report for duplicate display names (different IDs OK)."""
        seen: dict[str, str] = {}
        for uid, record in self.units.items():
            dn = record["display_name"]
            if dn in seen:
                self.collisions.append(
                    {
                        "kind": "duplicate_display_name",
                        "display_name": dn,
                        "unit_ids": [seen[dn], uid],
                    }
                )
            seen[dn] = uid


# ── Output emitter ──────────────────────────────────────────────────────


def _serialize_deterministic(data: Any) -> str:
    """Serialize to deterministic JSON byte output."""

    def _sort(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: _sort(v) for k, v in sorted(obj.items())}
        if isinstance(obj, list):
            return [_sort(v) for v in obj]
        return obj

    sorted_data = _sort(data)
    return json.dumps(sorted_data, indent=2, ensure_ascii=False, default=str) + "\n"


def _write_json(path: Path, data: Any) -> str:
    """Write deterministic JSON, return sha256 of written content."""
    content = _serialize_deterministic(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ── Public API ──────────────────────────────────────────────────────────


def compile_content(
    wiki_path: str | None = None,
    output_dir: str | None = None,
    freeze_clock: str | None = None,
):
    """Compile wiki content into canonical JSON artifacts.

    Args:
        wiki_path: Path to wiki vault. Auto-detected if None.
        output_dir: Output directory. Defaults to data/generated/content/.
        freeze_clock: ISO timestamp for deterministic rebuilds (testing only).

    Returns:
        ``Manifest`` dataclass with build results.
    """
    ctx = BuildContext(wiki_path or "")
    ctx.build()
    out = Path(output_dir) if output_dir else GENERATED_DIR
    out.mkdir(parents=True, exist_ok=True)

    # Fatal collision check BEFORE any artifact writes (Task 1.5)
    fatal_kinds = {"dangling_ref", "unit_id", "faction_id"}
    fatal = [c for c in ctx.collisions if c.get("kind") in fatal_kinds]
    if fatal:
        msg_lines = [f"Fatal collision: {c}" for c in fatal]
        raise RuntimeError("Compilation failed due to fatal collision(s):\n" + "\n".join(msg_lines))

    # ── Source tracking ──
    wiki = ctx.wiki_path
    source_files = sorted(wiki.rglob("*.md"))
    source_paths = sorted(str(p.relative_to(wiki.parent)) for p in source_files)
    source_hashes = {
        str(p.relative_to(wiki.parent)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in source_files
    }

    artifacts: list[ManifestEntry] = []

    # ── 1. Factions ──
    factions_sorted = dict(sorted(ctx.factions.items()))
    for _fid, data in ctx.factions.items():
        FactionV1(**data)
    h = _write_json(out / "factions.json", factions_sorted)
    artifacts.append(ManifestEntry(filename="factions.json", sha256=h))

    # ── 2. Weapons ──
    weapons_sorted = dict(sorted(ctx.weapons.items()))
    for _wid, data in ctx.weapons.items():
        WeaponV1(**data)
    h = _write_json(out / "weapons.json", weapons_sorted)
    artifacts.append(ManifestEntry(filename="weapons.json", sha256=h))

    # ── 3. Detachments ──
    det_sorted = dict(sorted(ctx.detachments.items()))
    for _did, data in ctx.detachments.items():
        DetachmentV1(**data)
    h = _write_json(out / "detachments.json", det_sorted)
    artifacts.append(ManifestEntry(filename="detachments.json", sha256=h))

    # ── 4. Stratagems ──
    strat_sorted = dict(sorted(ctx.stratagems.items()))
    h = _write_json(out / "stratagems.json", strat_sorted)
    artifacts.append(ManifestEntry(filename="stratagems.json", sha256=h))

    # ── 5. Enhancements ──
    enh_sorted = dict(sorted(ctx.enhancements.items()))
    h = _write_json(out / "enhancements.json", enh_sorted)
    artifacts.append(ManifestEntry(filename="enhancements.json", sha256=h))

    # ── 6. Rules (placeholder) ──
    rules_data: dict[str, Any] = {}
    h = _write_json(out / "rules.json", rules_data)
    artifacts.append(ManifestEntry(filename="rules.json", sha256=h))

    # ── 7. Units (sharded by faction) ──
    units_dir = out / "units"
    units_dir.mkdir(parents=True, exist_ok=True)

    index: dict[str, dict[str, str]] = {}
    by_faction: dict[str, dict[str, Any]] = {}

    for uid, record in sorted(ctx.units.items()):
        fid = record["faction_id"]
        # Map faction id to a filename-safe name
        fname = fid.split(":", 1)[1] if ":" in fid else fid
        by_faction.setdefault(fname, {})[uid] = record

        entry_hash = hashlib.sha256(_serialize_deterministic(record).encode("utf-8")).hexdigest()
        index[uid] = {
            "faction_id": fid,
            "file": f"units/{fname}.json",
            "display_name": record["display_name"],
            "hash": f"sha256:{entry_hash}",
        }

    # Write shards
    for fname, unit_dict in sorted(by_faction.items()):
        sorted_dict = dict(sorted(unit_dict.items()))
        h = _write_json(units_dir / f"{fname}.json", sorted_dict)
        artifacts.append(ManifestEntry(filename=f"units/{fname}.json", sha256=h))

    # Write index
    sorted_index = dict(sorted(index.items()))
    for _uid, entry in sorted_index.items():
        UnitIndexEntryV1(**entry)
    h = _write_json(units_dir / "index.json", sorted_index)
    artifacts.append(ManifestEntry(filename="units/index.json", sha256=h))

    # ── 8. Faction_units (availability shards) ──
    fu_dir = out / "faction_units"
    fu_dir.mkdir(parents=True, exist_ok=True)

    fu_index: dict[str, dict[str, str]] = {}
    for fid in sorted(ctx.factions.keys()):
        fname = fid.split(":", 1)[1] if ":" in fid else fid
        # Collect unit IDs available to this faction
        available = sorted(uid for uid, record in ctx.units.items() if record["faction_id"] == fid)
        avail_record = {
            "faction_id": fid,
            "available_unit_ids": available,
        }
        h = _write_json(fu_dir / f"{fname}.json", avail_record)
        artifacts.append(ManifestEntry(filename=f"faction_units/{fname}.json", sha256=h))

        fu_index[fid] = {
            "file": f"faction_units/{fname}.json",
        }

    sorted_fu_index = dict(sorted(fu_index.items()))
    h = _write_json(fu_dir / "index.json", sorted_fu_index)
    artifacts.append(ManifestEntry(filename="faction_units/index.json", sha256=h))

    # ── Content hash ──
    all_content = ""
    for a in artifacts:
        all_content += f"{a.filename}:{a.sha256}\n"
    content_hash = hashlib.sha256(all_content.encode("utf-8")).hexdigest()

    # ── Collisions ──
    collisions = sorted(ctx.collisions, key=lambda c: c.get("kind", ""))
    if collisions:
        logger.warning("Compilation completed with %d non-fatal collision(s)", len(collisions))

    # ── Manifest (written after all other artifacts) ──
    # Build manifest with all artifact entries INCLUDING a placeholder for manifest
    # itself.  We compute the manifest content, hash it, and overwrite the placeholder.
    manifest_content = _serialize_deterministic(
        {
            "schema_version": SCHEMA_VERSION,
            "generated_at": freeze_clock or datetime.now(UTC).isoformat(),
            "content_hash": content_hash,
            "source_paths": sorted(source_paths),
            "source_hashes": dict(sorted(source_hashes.items())),
            "artifacts": [a.to_dict() for a in artifacts] + [],
            "collisions": collisions,
        }
    )
    manifest_hash = hashlib.sha256(manifest_content.encode("utf-8")).hexdigest()
    artifacts.append(ManifestEntry(filename="manifest.json", sha256=manifest_hash))

    # Rebuild content_hash with manifest included
    all_content = ""
    for a in artifacts:
        all_content += f"{a.filename}:{a.sha256}\n"
    content_hash = hashlib.sha256(all_content.encode("utf-8")).hexdigest()

    manifest_content = _serialize_deterministic(
        {
            "schema_version": SCHEMA_VERSION,
            "generated_at": freeze_clock or datetime.now(UTC).isoformat(),
            "content_hash": content_hash,
            "source_paths": sorted(source_paths),
            "source_hashes": dict(sorted(source_hashes.items())),
            "artifacts": [a.to_dict() for a in artifacts],
            "collisions": collisions,
        }
    )
    (out / "manifest.json").write_text(manifest_content, encoding="utf-8")

    manifest = Manifest(
        schema_version=SCHEMA_VERSION,
        generated_at=freeze_clock or datetime.now(UTC).isoformat(),
        content_hash=content_hash,
        source_paths=source_paths,
        source_hashes=source_hashes,
        artifacts=artifacts,
        collisions=collisions,
    )
    manifest.content_hash = content_hash

    logger.info(
        "Compiled %d units, %d detachments, %d weapons, %d factions → %s "
        "(%d artifacts, %d collisions)",
        len(ctx.units),
        len(ctx.detachments),
        len(ctx.weapons),
        len(ctx.factions),
        out,
        len(artifacts),
        len(collisions),
    )
    return manifest


def load_manifest(output_dir: str | None = None) -> Manifest | None:
    """Load the manifest from generated content directory."""
    out = Path(output_dir) if output_dir else GENERATED_DIR
    manifest_path = out / "manifest.json"
    if not manifest_path.exists():
        return None
    with manifest_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    entries = [ManifestEntry(**e) for e in data.get("artifacts", [])]
    return Manifest(
        schema_version=data["schema_version"],
        generated_at=data["generated_at"],
        content_hash=data.get("content_hash", ""),
        source_paths=data.get("source_paths", []),
        source_hashes=data.get("source_hashes", {}),
        artifacts=entries,
        collisions=data.get("collisions", []),
    )


def is_content_stale(manifest: Manifest, wiki_path: str) -> bool:
    """Check whether wiki source files have changed since compilation."""
    wiki = Path(wiki_path)
    if not manifest.source_hashes:
        return True
    for rel_path, cached_hash in manifest.source_hashes.items():
        full = (wiki.parent / rel_path).resolve()
        if not full.exists():
            return True
        current = hashlib.sha256(full.read_bytes()).hexdigest()
        if current != cached_hash:
            return True
    current_files = set()
    for p in wiki.rglob("*.md"):
        current_files.add(str(p.relative_to(wiki.parent)))
    manifest_files = set(manifest.source_paths)
    return current_files != manifest_files


# ── Fast access helpers ─────────────────────────────────────────────────


def load_units_index(output_dir: str | None = None) -> dict[str, Any]:
    out = Path(output_dir) if output_dir else GENERATED_DIR
    with (out / "units" / "index.json").open("r", encoding="utf-8") as f:
        return json.load(f)


def load_unit_shard(faction_slug: str, output_dir: str | None = None) -> dict[str, Any]:
    out = Path(output_dir) if output_dir else GENERATED_DIR
    with (out / "units" / f"{faction_slug}.json").open("r", encoding="utf-8") as f:
        return json.load(f)


def load_all_units(output_dir: str | None = None) -> dict[str, Any]:
    """Load all units from all shards into one dict."""
    out = Path(output_dir) if output_dir else GENERATED_DIR
    index = load_units_index(output_dir)
    all_units: dict[str, Any] = {}
    for _uid, entry in index.items():
        shard_file = Path(entry["file"])
        with (out / shard_file).open("r", encoding="utf-8") as f:
            shard = json.load(f)
        all_units.update(shard)
    return all_units


def load_faction_units_index(output_dir: str | None = None) -> dict[str, Any]:
    out = Path(output_dir) if output_dir else GENERATED_DIR
    with (out / "faction_units" / "index.json").open("r", encoding="utf-8") as f:
        return json.load(f)


def load_detachments_from_json(output_dir: str | None = None) -> dict[str, Any]:
    out = Path(output_dir) if output_dir else GENERATED_DIR
    with (out / "detachments.json").open("r", encoding="utf-8") as f:
        return json.load(f)
