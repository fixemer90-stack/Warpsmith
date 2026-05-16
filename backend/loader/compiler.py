"""Content compiler — Task 1.2.

Compiles wiki/frontmatter markdown into safe JSON artifacts.
Replaces the unsafe `pickle`-based cache with a manifest-driven
content pipeline.

Output:
  data/generated/content/manifest.json
  data/generated/content/units.json
  data/generated/content/detachments.json
  data/generated/content/factions.json
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.loader.parser import parse_unit
from backend.loader.registry import WikiRegistry

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "content.v1"
GENERATED_DIR = Path(__file__).parent.parent.parent / "data" / "generated" / "content"


@dataclass
class ManifestEntry:
    """Metadata for one generated artifact."""

    filename: str
    sha256: str

    def to_dict(self) -> dict[str, str]:
        return {"filename": self.filename, "sha256": self.sha256}


@dataclass
class Manifest:
    """Canonical manifest for generated content artifacts."""

    schema_version: str
    generated_at: str  # ISO 8601
    source_paths: list[str]
    source_hashes: dict[str, str]  # filename → sha256
    artifacts: list[ManifestEntry]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "source_paths": self.source_paths,
            "source_hashes": self.source_hashes,
            "artifacts": [a.to_dict() for a in self.artifacts],
        }


# ── Public API ──────────────────────────────────────────────────────────


def compile_content(wiki_path: str | None = None, output_dir: str | None = None):
    """Compile wiki content into JSON artifacts and manifest.

    Args:
        wiki_path: Path to wiki vault.  Auto-detected if None.
        output_dir: Output directory.  Defaults to data/generated/content/.
    """
    reg = WikiRegistry(wiki_path or "")
    reg.load(use_cache=False)  # Always scan fresh — no pickle cache
    out = Path(output_dir) if output_dir else GENERATED_DIR
    out.mkdir(parents=True, exist_ok=True)

    wiki = reg.wiki_path
    source_files: list[Path] = []
    for ext in ("*.md",):
        source_files.extend(sorted(wiki.rglob(ext)))

    source_paths = sorted(str(p.relative_to(wiki.parent)) for p in source_files)
    source_hashes = {
        str(p.relative_to(wiki.parent)): _sha256(p) for p in source_files
    }

    artifacts: list[ManifestEntry] = []

    # Units
    units_data = _serialize_units(reg)
    _write_json(out / "units.json", units_data)
    artifacts.append(_entry(out / "units.json"))

    # Detachments
    det_data = _serialize_detachments(reg)
    _write_json(out / "detachments.json", det_data)
    artifacts.append(_entry(out / "detachments.json"))

    # Factions
    factions_data = {
        "factions": sorted(reg.list_factions()),
        "unit_count": len(reg.units),
        "detachment_count": len(reg.detachments),
    }
    _write_json(out / "factions.json", factions_data)
    artifacts.append(_entry(out / "factions.json"))

    manifest = Manifest(
        schema_version=SCHEMA_VERSION,
        generated_at=datetime.now(timezone.utc).isoformat(),
        source_paths=source_paths,
        source_hashes=source_hashes,
        artifacts=artifacts,
    )
    _write_json(out / "manifest.json", manifest.to_dict())

    logger.info(
        "Compiled %d units, %d detachments → %s",
        len(reg.units), len(reg.detachments), out,
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
        source_paths=data.get("source_paths", []),
        source_hashes=data.get("source_hashes", {}),
        artifacts=entries,
    )


def is_content_stale(manifest: Manifest, wiki_path: str) -> bool:
    """Check whether wiki source files have changed since compilation."""
    wiki = Path(wiki_path)
    for rel_path, cached_hash in manifest.source_hashes.items():
        full = (wiki.parent / rel_path).resolve()
        if not full.exists():
            return True
        current = _sha256(full)
        if current != cached_hash:
            return True
    # Also check for new files not in manifest
    current_files = set()
    for ext in ("*.md",):
        for p in wiki.rglob(ext):
            current_files.add(str(p.relative_to(wiki.parent)))
    manifest_files = set(manifest.source_paths)
    return current_files != manifest_files


def load_units_from_json(output_dir: str | None = None) -> dict[str, Any]:
    """Load compiled units from JSON artifact.

    Returns dict[name, unit_dict].  Caller must convert to Unit objects if needed.
    """
    out = Path(output_dir) if output_dir else GENERATED_DIR
    with (out / "units.json").open("r", encoding="utf-8") as f:
        return json.load(f)


def load_detachments_from_json(output_dir: str | None = None) -> dict[str, Any]:
    """Load compiled detachments from JSON artifact."""
    out = Path(output_dir) if output_dir else GENERATED_DIR
    with (out / "detachments.json").open("r", encoding="utf-8") as f:
        return json.load(f)


# ── Internal helpers ────────────────────────────────────────────────────


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


def _entry(path: Path) -> ManifestEntry:
    return ManifestEntry(filename=path.name, sha256=_sha256(path))


def _serialize_units(reg: WikiRegistry) -> dict[str, Any]:
    from dataclasses import asdict

    result: dict[str, Any] = {}
    for name, unit in reg.units.items():
        unit_dict = asdict(unit)
        # Convert non-serializable fields
        unit_dict["ranged_weapons"] = [
            asdict(w) for w in getattr(unit, "ranged_weapons", []) or []
        ]
        unit_dict["melee_weapons"] = [
            asdict(w) for w in getattr(unit, "melee_weapons", []) or []
        ]
        result[name] = unit_dict
    return result


def _serialize_detachments(reg: WikiRegistry) -> dict[str, Any]:
    from dataclasses import asdict

    result: dict[str, Any] = {}
    for name, det in reg.detachments.items():
        result[name] = asdict(det)
    return result
