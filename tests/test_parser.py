from pathlib import Path

import pytest

from backend.loader.parser import _parse_weapons_from_markdown, parse_unit
from backend.loader.registry import WikiRegistry

SAMPLE_BOY = """---
title: Boyz
faction: orks
category: Battleline
movement: 5
toughness: 5
save: 5
wounds: 2
leadership: 7
objective_control: 2
model_count: 10-20
points: 85
keywords: [Infantry, Battleline, Core, Orks]
faction_keywords: [Orks, Waaagh!]
weapons:
  - name: Shoota
    range: 18
    attacks: "3"
    skill: "5+"
    strength: 4
    ap: 0
    damage: "1"
    tags: [assault]
---
Boyz are the backbone of a Waaagh!
"""


def test_parse_unit_from_frontmatter() -> None:
    tmp_path = Path("tests/.tmp_parser/frontmatter")
    filepath = tmp_path / "units" / "orks" / "Boyz.md"
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(SAMPLE_BOY, encoding="utf8")

    unit = parse_unit(filepath)

    assert unit is not None
    assert unit.name == "Boyz"
    assert unit.faction == "orks"
    assert unit.movement == 5
    assert unit.toughness == 5
    assert unit.model_count == (10, 20)
    assert len(unit.ranged_weapons) == 1
    assert unit.ranged_weapons[0].name == "Shoota"
    assert unit.ranged_weapons[0].attacks_dice == (0, 0, 3)


def test_parse_weapons_from_markdown() -> None:
    markdown = """| Weapon | Range | A | BS | S | AP | D | Abilities |
|--------|-------|---|----|---|----|---|-----------|
| Shoota | 18" | 3 | 5+ | 4 | 0 | 1 | Assault |
| Choppa | Melee | 3 | 4+ | 4 | 0 | 1 | - |
"""
    ranged, melee = _parse_weapons_from_markdown(markdown)

    assert len(ranged) == 1
    assert len(melee) == 1
    assert ranged[0].name == "Shoota"
    assert ranged[0].range_max == 18
    assert melee[0].name == "Choppa"
    assert melee[0].type == "melee"


def test_registry_cache() -> None:
    tmp_path = Path("tests/.tmp_parser/cache")
    wiki_path = tmp_path / "wiki"
    units_path = wiki_path / "units" / "orks"
    units_path.mkdir(parents=True, exist_ok=True)
    (units_path / "Boyz.md").write_text(SAMPLE_BOY, encoding="utf8")

    registry = WikiRegistry(str(wiki_path))
    registry.cache_path = tmp_path / "wiki_registry.pkl"

    units = registry.load(use_cache=True)
    assert "Boyz" in units
    assert registry.cache_path.exists()

    cached_registry = WikiRegistry(str(wiki_path))
    cached_registry.cache_path = registry.cache_path
    cached_units = cached_registry.load(use_cache=True)
    assert "Boyz" in cached_units
    assert cached_units["Boyz"].toughness == 5


def test_parse_real_ork_boy_if_available() -> None:
    candidates = [
        Path("d:/Python/Balthier/wiki/units/orks/Boyz.md"),
        Path("/mnt/d/Python/Balthier/wiki/units/orks/Boyz.md"),
    ]
    real_path = next((candidate for candidate in candidates if candidate.exists()), None)
    if real_path is None:
        pytest.skip("Real Boyz.md not available in this environment")

    unit = parse_unit(real_path)
    assert unit is not None
    assert unit.name == "Boyz"
    assert unit.faction == "orks"
    assert unit.toughness >= 1
    assert unit.ranged_weapons or unit.melee_weapons
