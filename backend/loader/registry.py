"""Wiki registry for loading unit datasheets from markdown files."""

import logging
import os
import pickle
from pathlib import Path

from backend.loader.parser import parse_unit
from backend.model.unit import Unit

logger = logging.getLogger(__name__)


class WikiRegistry:
    """In-memory index of units loaded from the wiki vault."""

    def __init__(self, wiki_path: str = ""):
        self.wiki_path = Path(wiki_path) if wiki_path else self._detect_wiki_path()
        self.cache_path = Path.home() / ".cache" / "wiki_registry.pkl"
        self.units: dict[str, Unit] = {}
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
        self._file_mtimes = {}

        units_dir = self.wiki_path / "units"
        if not units_dir.exists():
            logger.warning("Units directory not found: %s", units_dir)
            return units

        for faction_dir in sorted(units_dir.iterdir()):
            if not faction_dir.is_dir():
                continue
            for file_path in sorted(faction_dir.glob("*.md")):
                unit = parse_unit(file_path)
                if unit is None:
                    continue
                units[unit.name] = unit
                self._file_mtimes[str(file_path)] = file_path.stat().st_mtime

        logger.info("Wiki loaded: %s units from %s files", len(units), len(self._file_mtimes))
        return units

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
        self._file_mtimes = mtimes
        self._loaded = True
        logger.info("Loaded %s units from cache", len(self.units))
        return True

    def _save_cache(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with self.cache_path.open("wb") as cache_file:
            pickle.dump({"units": self.units, "mtimes": self._file_mtimes}, cache_file)

    def get_unit(self, name: str) -> Unit | None:
        return self.units.get(name)

    def list_units(self, faction: str = "") -> list[str]:
        if faction:
            return [name for name, unit in self.units.items() if unit.faction == faction]
        return list(self.units.keys())


registry: WikiRegistry | None = None
try:
    registry = WikiRegistry()
except FileNotFoundError:
    logger.warning("Wiki registry singleton was not initialized because no wiki path was found")
