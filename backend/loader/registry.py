"""Wiki registry for loading unit datasheets from markdown files."""

import logging
import os
import pickle
from pathlib import Path

from backend.loader.parser import parse_unit
from backend.model.unit import Unit
from dataclasses import dataclass, field
from typing import Dict, List, Optional

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
    detachment_rule: Optional[DetachmentRule] = None
    stratagems: List[Stratagem] = field(default_factory=list)
    enhancements: List[Enhancement] = field(default_factory=list)


class WikiRegistry:
    """In-memory index of units loaded from the wiki vault."""

    def __init__(self, wiki_path: str = ""):
        self.wiki_path = Path(wiki_path) if wiki_path else self._detect_wiki_path()
        self.cache_path = Path.home() / ".cache" / "wiki_registry.pkl"
        self.units: dict[str, Unit] = {}
        self.detachments: dict[str, Detachment] = {}
        self._file_mtimes: dict[str, float] = {}
        self._loaded = False

    def _detect_wiki_path(self) -> Path:
        env_path = os.getenv("WIKI_PATH")
        candidates = [
            Path(env_path) if env_path else None,
            Path.cwd() / "wiki",
            Path.cwd().parent / "wiki",
            Path("/mnt/d/Python/Balthier/wiki"),
            Path("/mnt/d/Python/Maksim/wiki"),
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

        if use_cache and self._load_from_cache():
            return self.units

        self.units = self._scan_and_parse()
        self._loaded = True

        if use_cache:
            self._save_cache()

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
        logger.info("Wiki loaded: %s units, %s detachments from %s files",
                   len(units), len(detachments), len(self._file_mtimes))
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
                    description=rule_data.get("description", "")
                )

        # Parse stratagems
        stratagems = []
        for strat_data in metadata.get("stratagems", []):
            if isinstance(strat_data, dict):
                stratagems.append(Stratagem(
                    name=strat_data.get("name", ""),
                    cost=int(strat_data.get("cost", 1)),
                    when=strat_data.get("when", ""),
                    effect=strat_data.get("effect", "")
                ))

        # Parse enhancements
        enhancements = []
        for enh_data in metadata.get("enhancements", []):
            if isinstance(enh_data, dict):
                enhancements.append(Enhancement(
                    name=enh_data.get("name", ""),
                    points=int(enh_data.get("points", 0)),
                    effect=enh_data.get("effect", "")
                ))

        return Detachment(
            name=name,
            faction=faction,
            description=metadata.get("description", ""),
            detachment_rule=detachment_rule,
            stratagems=stratagems,
            enhancements=enhancements
        )

    def _load_from_cache(self) -> bool:
        try:
            with self.cache_path.open("rb") as cache_file:
                data = pickle.load(cache_file)
        except (FileNotFoundError, pickle.UnpicklingError, EOFError):
            return False

        units = data.get("units")
        mtimes = data.get("mtimes")
        if not isinstance(units, dict) or not isinstance(mtimes, dict):
            return False

        for path_str, cached_mtime in mtimes.items():
            path = Path(path_str)
            if not path.exists() or path.stat().st_mtime != cached_mtime:
                return False

        self.units = units
        self.detachments = data.get("detachments", {})
        self._file_mtimes = mtimes
        self._loaded = True
        logger.info("Loaded %s units, %s detachments from cache",
                   len(self.units), len(self.detachments))
        return True

    def _save_cache(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with self.cache_path.open("wb") as cache_file:
            pickle.dump({
                "units": self.units,
                "detachments": self.detachments,
                "mtimes": self._file_mtimes
            }, cache_file)

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
        """List all available factions."""
        unit_factions = set(unit.faction for unit in self.units.values())
        det_factions = set(det.faction for det in self.detachments.values())
        return sorted(unit_factions.union(det_factions))


registry: WikiRegistry | None = None
try:
    registry = WikiRegistry()
except FileNotFoundError:
    logger.warning("Wiki registry singleton was not initialized because no wiki path was found")
