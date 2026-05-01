"""Wiki Loader — парсинг .md файлов из вики и построение Registry."""

import logging
import os
import re
from pathlib import Path
from typing import Optional

import frontmatter
import yaml

from backend.model.unit import Unit, Weapon

logger = logging.getLogger(__name__)


class WikiRegistry:
    """In-memory index всех юнитов, оружия, способностей."""

    def __init__(self, wiki_path: str = ""):
        self.wiki_path = Path(wiki_path) if wiki_path else self._detect_wiki_path()
        self.units: dict[str, Unit] = {}
        self._loaded = False

    def _detect_wiki_path(self) -> Path:
        """Автоопределение пути к вики."""
        # Ищем рядом с simulator/
        candidates = [
            Path.cwd() / "wiki",
            Path.cwd().parent / "wiki",
            Path("/mnt/d/Python/Maksim/wiki"),
            Path("/mnt/d/Python/Balthier/wiki"),
        ]
        for c in candidates:
            if (c / "index.md").exists():
                logger.info(f"Wiki found at: {c}")
                return c
        msg = "Wiki vault not found. Set WIKI_PATH env var."
        raise FileNotFoundError(msg)

    def load(self) -> dict[str, Unit]:
        """Загрузить все даташиты из вики."""
        if self._loaded:
            return self.units

        units_dir = self.wiki_path / "units"
        if not units_dir.exists():
            logger.warning(f"Units directory not found: {units_dir}")
            return {}

        for faction_dir in units_dir.iterdir():
            if not faction_dir.is_dir():
                continue
            faction = faction_dir.name
            for file in faction_dir.glob("*.md"):
                unit = self._parse_unit(file, faction)
                if unit:
                    self.units[unit.name] = unit

        self._loaded = True
        logger.info(f"Registry loaded: {len(self.units)} units")
        return self.units

    def _parse_unit(self, filepath: Path, faction: str) -> Unit | None:
        """Парсинг YAML frontmatter + markdown."""
        try:
            post = frontmatter.load(str(filepath))
        except Exception as e:
            logger.error(f"Failed to parse {filepath}: {e}")
            return None

        fm = post.metadata if hasattr(post, "metadata") else {}
        if not fm.get("title"):
            return None

        # TODO: парсинг M/T/SV/W/LD/OC из markdown-таблиц в содержимом
        # Пока заглушка — будет реализовано в parser.py
        return None

    def get_unit(self, name: str) -> Unit | None:
        """Получить юнит по имени."""
        return self.units.get(name)

    def list_units(self, faction: str = "") -> list[str]:
        """Список всех юнитов (опционально — по фракции)."""
        if faction:
            return [n for n, u in self.units.items() if u.faction == faction]
        return list(self.units.keys())


# Singleton
registry = WikiRegistry()
