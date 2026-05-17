"""Wiki registry for loading unit datasheets from markdown files."""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from backend.loader.parser import parse_unit
from backend.model.unit import Unit

logger = logging.getLogger(__name__)


@dataclass
class DetachmentRule:
    """Detachment rule with name and description."""

    name: str
    description: str


@dataclass
class Stratagem:
    """Stratagem with name, cost, when, and effect."""

    name: str
    cost: int
    when: str
    effect: str


@dataclass
class Enhancement:
    """Enhancement with name, points, and effect."""

    name: str
    points: int
    effect: str


@dataclass
class Detachment:
    """Detachment with all its data."""

    name: str
    faction: str
    description: str
    detachment_rule: DetachmentRule | None = None
    stratagems: list[Stratagem] = field(default_factory=list)
    enhancements: list[Enhancement] = field(default_factory=list)


class WikiRegistry:
    """In-memory index of units loaded from the wiki vault."""

    def __init__(self, wiki_path: str = ""):
        self.wiki_path = Path(wiki_path) if wiki_path else self._detect_wiki_path()
        self.generated_dir = Path(__file__).parent.parent.parent / "data" / "generated" / "content"
        self.units: dict[str, Unit] = {}
        self.detachments: dict[str, Detachment] = {}
        self._file_mtimes: dict[str, float] = {}
        self._loaded = False

    def _detect_wiki_path(self) -> Path:
        env_path = os.getenv("WIKI_PATH")
        candidates = [
            Path(env_path) if env_path else None,
            Path(__file__).parent.parent.parent / "wiki",
            Path.cwd() / "wiki",
            Path.cwd().parent / "wiki",
        ]
        for candidate in candidates:
            if candidate is not None and (candidate / "units").exists():
                logger.info("Wiki found at: %s", candidate)
                return candidate
        msg = "Wiki vault not found. Set WIKI_PATH env var."
        raise FileNotFoundError(msg)

    def load(self, use_cache: bool = True) -> dict[str, Unit]:
        if self._loaded:
            return self.units

        if use_cache and self._load_from_json_cache():
            return self.units

        self.units = self._scan_and_parse()
        self._loaded = True

        if use_cache:
            self._save_json_cache()

        return self.units

    def _scan_and_parse(self) -> dict[str, Unit]:
        units: dict[str, Unit] = {}
        detachments: dict[str, Detachment] = {}
        self._file_mtimes = {}

        units_dir = self.wiki_path / "units"
        if units_dir.exists():
            for faction_dir in sorted(units_dir.iterdir()):
                if not faction_dir.is_dir():
                    continue
                for file_path in sorted(faction_dir.glob("*.md")):
                    unit = parse_unit(file_path)
                    if unit is None:
                        continue
                    units[unit.name] = unit
                    self._file_mtimes[str(file_path)] = file_path.stat().st_mtime

        # Load detachments
        detachments_dir = self.wiki_path / "detachments"
        if detachments_dir.exists():
            for faction_dir in sorted(detachments_dir.iterdir()):
                if not faction_dir.is_dir():
                    continue
                for file_path in sorted(faction_dir.glob("*.md")):
                    detachment = self._parse_detachment(file_path)
                    if detachment is None:
                        continue
                    detachments[detachment.name] = detachment
                    self._file_mtimes[str(file_path)] = file_path.stat().st_mtime

        self.detachments = detachments
        logger.info(
            "Wiki loaded: %s units, %s detachments from %s files",
            len(units),
            len(detachments),
            len(self._file_mtimes),
        )
        return units

    def _parse_detachment(self, filepath: Path) -> Detachment | None:
        """Parse a detachment markdown file into a Detachment instance."""
        try:
            import frontmatter

            post = frontmatter.load(str(filepath))
        except Exception as exc:
            logger.error("Failed to parse detachment %s: %s", filepath, exc)
            return None

        metadata = post.metadata
        name = metadata.get("name") or metadata.get("title")
        if not name:
            logger.warning("No name/title in detachment file: %s", filepath)
            return None

        faction = metadata.get("faction", filepath.parent.name)

        # Parse detachment rule
        detachment_rule = None
        if "detachment_rule" in metadata:
            rule_data = metadata["detachment_rule"]
            if isinstance(rule_data, dict):
                detachment_rule = DetachmentRule(
                    name=rule_data.get("name", "Unknown Rule"),
                    description=rule_data.get("description", ""),
                )

        # Parse stratagems
        stratagems = []
        for strat_data in metadata.get("stratagems", []):
            if isinstance(strat_data, dict):
                stratagems.append(
                    Stratagem(
                        name=strat_data.get("name", ""),
                        cost=int(strat_data.get("cost", 1)),
                        when=strat_data.get("when", ""),
                        effect=strat_data.get("effect", ""),
                    )
                )

        # Parse enhancements
        enhancements = []
        for enh_data in metadata.get("enhancements", []):
            if isinstance(enh_data, dict):
                enhancements.append(
                    Enhancement(
                        name=enh_data.get("name", ""),
                        points=int(enh_data.get("points", 0)),
                        effect=enh_data.get("effect", ""),
                    )
                )

        return Detachment(
            name=name,
            faction=faction,
            description=metadata.get("description", ""),
            detachment_rule=detachment_rule,
            stratagems=stratagems,
            enhancements=enhancements,
        )

    def _load_from_json_cache(self) -> bool:
        """Load compiled JSON artifacts if present and not stale."""
        from backend.loader.compiler import is_content_stale, load_manifest

        manifest = load_manifest()
        if manifest is None:
            return False
        if manifest.schema_version != "content.v1":
            logger.info("Manifest schema version mismatch — recompiling")
            return False
        if is_content_stale(manifest, str(self.wiki_path)):
            logger.info("Wiki content changed since compilation — recompiling")
            return False

        try:
            from backend.loader.compiler import (
                load_all_units,
                load_detachments_from_json,
            )

            units_dict = load_all_units(str(self.generated_dir))
            det_dict = load_detachments_from_json(str(self.generated_dir))

            # Reconstruct Unit objects from dict
            self.units = {}
            for name, data in units_dict.items():
                try:
                    # Map canonical fields to Unit dataclass fields
                    ud = dict(data)
                    if "unit_id" in ud and "name" not in ud:
                        ud["name"] = ud.pop("unit_id")
                    if "display_name" in ud:
                        ud["name"] = ud.pop("display_name")
                    if "faction_id" in ud and "faction" not in ud:
                        ud["faction"] = ud.pop("faction_id")
                    # Remove canonical-only fields not in Unit.__init__
                    for kw in ("unit_id", "display_name", "faction_id", "source_path",
                               "ranged_weapons", "melee_weapons", "wargear_options",
                               "extended_wargear_options", "nob_options"):
                        ud.pop(kw, None)
                    unit = Unit(**ud)
                except Exception as exc:
                    logger.warning("Failed to load unit %s from JSON: %s", name, exc)
                    continue
                self.units[name] = unit

            # Reconstruct Detachment objects from dict
            self.detachments = {}
            for name, data in det_dict.items():
                try:
                    det_data = dict(data)
                    # Map canonical field names to Detachment dataclass fields
                    if "faction_id" in det_data and "faction" not in det_data:
                        det_data["faction"] = det_data.pop("faction_id")
                    rule_data = det_data.pop("detachment_rule", None)
                    if rule_data and isinstance(rule_data, dict):
                        det_data["detachment_rule"] = DetachmentRule(**rule_data)
                    strat_data = det_data.pop("stratagems", [])
                    det_data["stratagems"] = [Stratagem(**s) for s in strat_data]
                    enh_data = det_data.pop("enhancements", [])
                    det_data["enhancements"] = [Enhancement(**e) for e in enh_data]
                    self.detachments[name] = Detachment(**det_data)
                except Exception as exc:
                    logger.warning("Failed to load detachment %s from JSON: %s", name, exc)

            self._loaded = True
            logger.info(
                "Loaded %s units, %s detachments from JSON artifacts (manifest %s)",
                len(self.units),
                len(self.detachments),
                manifest.generated_at,
            )
            return True
        except Exception as exc:
            logger.warning("Failed to load JSON artifacts: %s — falling back to parse", exc)
            return False

    def _save_json_cache(self) -> None:
        """Compile content to JSON artifacts."""
        from backend.loader.compiler import compile_content

        compile_content(str(self.wiki_path))

    def get_unit(self, name: str) -> Unit | None:
        return self.units.get(name)

    def get_detachment(self, name: str) -> Detachment | None:
        return self.detachments.get(name)

    def get_weapon(self, faction: str, weapon_name: str):
        """Get a weapon by faction and name."""
        # TODO: Implement proper weapon loading from wiki
        # For now, return None to indicate weapon not found
        return None

    def list_units(self, faction: str = "") -> list[str]:
        if faction:
            return [name for name, unit in self.units.items() if unit.faction == faction]
        return list(self.units.keys())

    def list_detachments(self, faction: str = "") -> list[str]:
        if faction:
            return [name for name, det in self.detachments.items() if det.faction == faction]
        return list(self.detachments.keys())

    def list_factions(self) -> list[str]:
        """List all available factions (from units only)."""
        return sorted(set(unit.faction for unit in self.units.values()))


# ── CanonicalContentRegistry (Task 1.4) ─────────────────────────────────


class CanonicalContentRegistry:
    """Immutable registry loaded from generated JSON artifacts.

    Loads every canonical object kind: factions, units (sharded),
    faction_units, weapons, detachments, stratagems, enhancements, rules.
    All records are keyed by stable canonical IDs.
    """

    def __init__(self, output_dir: str | None = None):
        from backend.loader.compiler import GENERATED_DIR

        self._dir = Path(output_dir) if output_dir else GENERATED_DIR
        self.factions: dict[str, dict] = {}
        self.units: dict[str, dict] = {}
        self.faction_units: dict[str, dict] = {}
        self.weapons: dict[str, dict] = {}
        self.detachments: dict[str, dict] = {}
        self.stratagems: dict[str, dict] = {}
        self.enhancements: dict[str, dict] = {}
        self.rules: dict[str, dict] = {}
        self._loaded = False

    def load(self) -> bool:
        """Load all artifacts. Returns False if artifacts are missing."""
        try:
            from backend.loader.compiler import (
                load_all_units,
                load_faction_units_index,
                load_units_index,
            )

            # Factions
            with (self._dir / "factions.json").open("r", encoding="utf-8") as f:
                self.factions = json.load(f)

            # Weapons
            with (self._dir / "weapons.json").open("r", encoding="utf-8") as f:
                self.weapons = json.load(f)

            # Detachments
            with (self._dir / "detachments.json").open("r", encoding="utf-8") as f:
                self.detachments = json.load(f)

            # Stratagems
            with (self._dir / "stratagems.json").open("r", encoding="utf-8") as f:
                self.stratagems = json.load(f)

            # Enhancements
            with (self._dir / "enhancements.json").open("r", encoding="utf-8") as f:
                self.enhancements = json.load(f)

            # Rules
            with (self._dir / "rules.json").open("r", encoding="utf-8") as f:
                self.rules = json.load(f)

            # Units (sharded — load all shards via compiler helper)
            self.units = load_all_units(str(self._dir))

            # Faction units (availability)
            fu_index = load_faction_units_index(str(self._dir))
            for fid, entry in fu_index.items():
                # entry["file"] is like "faction_units/orks.json" — resolve relative to self._dir
                shard_rel = Path(entry["file"])
                if shard_rel.parent == Path("faction_units"):
                    shard_path = self._dir / shard_rel
                else:
                    shard_path = self._dir / "faction_units" / shard_rel
                with shard_path.open("r", encoding="utf-8") as f:
                    self.faction_units[fid] = json.load(f)

            self._loaded = True
            logger.info(
                "CanonicalContentRegistry loaded: %d factions, %d units, "
                "%d detachments, %d weapons, %d faction_units",
                len(self.factions),
                len(self.units),
                len(self.detachments),
                len(self.weapons),
                len(self.faction_units),
            )
            return True
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as exc:
            logger.warning("Failed to load canonical content: %s", exc)
            return False

    def get_unit(self, unit_id: str) -> dict | None:
        return self.units.get(unit_id)

    def get_units_by_faction(self, faction_id: str) -> list[dict]:
        """Resolve available units for a faction via faction_units links."""
        avail = self.faction_units.get(faction_id, {})
        unit_ids = avail.get("available_unit_ids", [])
        return [self.units[uid] for uid in unit_ids if uid in self.units]

    def get_faction(self, faction_id: str) -> dict | None:
        return self.factions.get(faction_id)

    def get_weapon(self, weapon_id: str) -> dict | None:
        return self.weapons.get(weapon_id)


registry: WikiRegistry | None = None
try:
    registry = WikiRegistry()
except FileNotFoundError:
    logger.warning("Wiki registry singleton was not initialized because no wiki path was found")
