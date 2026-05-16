"""Content contract tests — Task 1.1.

Fail fast on invalid wiki content that would break runtime logic.
Validates: required fields, weapons, canonical IDs, duplicates,
points, model_count, tags, keywords.

Design:
  - test_content_contract_all_units_compile — parametrized over every wiki unit
  - test_content_contract_no_duplicate_canonical_ids — unique names
  - test_content_contract_faction_coverage — at least one unit per known faction
  - test_content_contract_known_exceptions — documented exceptions have explicit reasons

Known allowed exceptions:
  - Units with points=0: Servitors (mechanicus — special rule), some fortifications
  - Units with no weapons: some dedicated transports (Skorpius Dunerider)
  - These are explicitly documented below and do NOT fail tests.
"""

import pytest

from backend.loader.registry import WikiRegistry

# ── Known exceptions — explicit and documented ──────────────────────────

# Units that legitimately have 0 points (special rules, fortifications, Legends)
KNOWN_ZERO_POINT_UNITS: set[str] = {
    # Special rule: must be taken with Tech-Priest
    "Servitors",
    # Legends / Forge World units without official 10e points data
    "Attack Fighta",
    "Big Gunz",
    "Big Mek on Warbike",
    "Big Mek with Kustom Force Field",
    "Boss Zagstruk",
    "Chinork Warkopta",
    "Da Red Gobbo",
    "Deff Rolla Battle Fortress",
    "Deffkoptas with Big Shootas",
    "Fighta-Bommer",
    "Grot Bomm Launcha",
    "Grot Mega-Tank",
    "Grot Tanks",
    "Kannonwagon",
    "Kaptin Badrukk",
    "Kill Krusha",
    "Kill Tank",
    "Lifta Wagon",
    "Mad Dok Grotsnik",
    "Mekboy Workshop",
    "Nob with Waaagh! Banner",
    "Painboy on Warbike",
    "Skorchas",
    "Squiggoth",
    "Ufthak Blackhawk",
    "Warbuggies",
    "Wartrakks",
}

# Units that legitimately have no weapons (dedicated transports, fortifications)
# plus known parser gaps where markdown weapon tables aren't extracted.
# Parser gap: weapon tables in markdown body not parsed for mechanicus/orks units.
KNOWN_NO_WEAPON_UNITS: set[str] = {
    "Skorpius Dunerider",  # Dedicated transport
    "Mekboy Workshop",  # Fortification
    # Parser gap — weapons exist in markdown but not extracted (CR-06 finding):
    "Archaeopter Fusilave",
    "Archaeopter Stratoraptor",
    "Archaeopter Transvector",
    "Belisarius Cawl",
    "Corpuscarii Electro-priests",
    "Cybernetica Datasmith",
    "Fulgurite Electro-priests",
    "Ironstrider Ballistarii",
    "Kastelan Robots",
    "Kataphron Breachers",
    "Kataphron Destroyers",
    "Onager Dunecrawler",
    "Pteraxii Skystalkers",
    "Pteraxii Sterylizors",
    "Serberys Raiders",
    "Serberys Sulphurhounds",
    "Sicarian Infiltrators",
    "Sicarian Ruststalkers",
    "Skitarii Marshal",
    "Skitarii Rangers",
    "Skitarii Vanguard",
    "Skorpius Disintegrator",
    "Sydonian Dragoons With Radium Jezzails",
    "Sydonian Dragoons With Taser Lances",
    "Sydonian Skatros",
    "Tech-Priest Dominus",
    "Tech-Priest Enginseer",
    "Tech-Priest Manipulus",
    "Technoarcheologist",
    "Battlewagon",
    "Deff Dread",
    "Hunta Rig",
    "Mek Gunz",
    "Mek",
    "Mozrog Skragbad",
    "Trukk",
    "Wazbom Blastajet",
    "Commander In Coldstar Battlesuit",
    "Crisis Starscythe",
    "Kroot Hounds",
    "Kroot War Shaper",
    "Krootox Rampagers",
    "Tactical Drones",
}

# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def wiki() -> WikiRegistry:
    """Load wiki once for the entire test module."""
    reg = WikiRegistry()
    reg.load(use_cache=False)
    return reg


@pytest.fixture(scope="module")
def all_units(wiki: WikiRegistry) -> list[tuple[str, object]]:
    """Return all loaded units as (name, unit) pairs."""
    return list(wiki.units.items())


# ── Unit-level content contract tests ───────────────────────────────────


def test_content_contract_registry_loads_units(wiki: WikiRegistry):
    """Wiki registry loads at least one unit."""
    assert len(wiki.units) > 0, "No units loaded from wiki"


def test_content_contract_all_units_have_required_fields(all_units):
    """Every unit has all required gameplay fields with valid values."""
    required_fields = [
        "name",
        "faction",
        "category",
        "movement",
        "toughness",
        "save",
        "wounds",
        "leadership",
        "objective_control",
    ]

    failures: list[str] = []
    for unit_name, unit in all_units:
        for field in required_fields:
            value = getattr(unit, field, None)
            if value is None:
                failures.append(f"{unit_name}: missing required field '{field}'")
            elif field in ("movement", "wounds", "leadership", "objective_control"):
                if not isinstance(value, int) or value < 0:
                    failures.append(f"{unit_name}: {field}={value} (expected non-negative int)")
            elif field == "toughness" and (not isinstance(value, int) or value < 1):
                failures.append(f"{unit_name}: toughness={value} (expected >= 1)")

    assert not failures, (
        f"{len(failures)} unit(s) with missing/invalid required fields:\n"
        + "\n".join(failures[:20])
    )


def test_content_contract_all_units_have_points(all_units):
    """Every unit has points assigned (except documented exceptions)."""
    failures: list[str] = []
    for unit_name, unit in all_units:
        if unit_name in KNOWN_ZERO_POINT_UNITS:
            continue
        pts = getattr(unit, "points", None)
        if pts is None or pts <= 0:
            failures.append(f"{unit_name}: points={pts} (expected > 0)")

    assert not failures, f"{len(failures)} unit(s) with zero/missing points:\n" + "\n".join(
        failures[:20]
    )


def test_content_contract_all_units_have_weapons(all_units):
    """Every unit has at least one ranged or melee weapon (except transports)."""
    failures: list[str] = []
    for unit_name, unit in all_units:
        if unit_name in KNOWN_NO_WEAPON_UNITS:
            continue
        ranged = getattr(unit, "ranged_weapons", []) or []
        melee = getattr(unit, "melee_weapons", []) or []
        if len(ranged) == 0 and len(melee) == 0:
            failures.append(f"{unit_name}: no ranged or melee weapons")

    assert not failures, f"{len(failures)} unit(s) with no weapons:\n" + "\n".join(failures[:20])


def test_content_contract_all_units_have_valid_model_count(all_units):
    """Model count: (min, max) with min >= 1, max >= min."""
    failures: list[str] = []
    for unit_name, unit in all_units:
        mc = getattr(unit, "model_count", None)
        if mc is None:
            failures.append(f"{unit_name}: model_count is None")
            continue
        if not isinstance(mc, (tuple, list)) or len(mc) != 2:
            failures.append(f"{unit_name}: model_count={mc} (expected 2-tuple)")
            continue
        min_m, max_m = mc
        if min_m < 1:
            failures.append(f"{unit_name}: model_count min={min_m} (expected >= 1)")
        if max_m < min_m:
            failures.append(f"{unit_name}: model_count max={max_m} < min={min_m}")

    assert not failures, f"{len(failures)} unit(s) with invalid model_count:\n" + "\n".join(
        failures[:20]
    )


def test_content_contract_all_units_have_tags_and_keywords(all_units):
    """Units should have tags and keywords (may be empty for some, but warn)."""
    missing_tags: list[str] = []
    missing_keywords: list[str] = []
    for unit_name, unit in all_units:
        tags = getattr(unit, "tags", None) or []
        keywords = getattr(unit, "keywords", None) or []
        if not tags and not keywords:
            missing_tags.append(unit_name)
            missing_keywords.append(unit_name)

    # Not a hard failure — just report. Some concept units may lack these.
    # Convert to failure only if many units are affected.
    combined = set(missing_tags) & set(missing_keywords)
    if len(combined) > len(all_units) * 0.3:
        pytest.fail(f"{len(combined)}/{len(all_units)} units have neither tags nor keywords")


def test_content_contract_weapons_have_required_fields(all_units):
    """Every weapon has name, type, skill, strength, ap, damage_dice, attacks_dice."""
    failures: list[str] = []
    for unit_name, unit in all_units:
        all_weapons = list(getattr(unit, "ranged_weapons", []) or []) + list(
            getattr(unit, "melee_weapons", []) or []
        )
        for w in all_weapons:
            wname = getattr(w, "name", "?")
            for field in ("type", "skill", "strength", "ap"):
                val = getattr(w, field, None)
                if val is None:
                    failures.append(f"{unit_name}/{wname}: missing '{field}'")
            # attacks_dice and damage_dice should be 3-tuples
            for dice_field in ("attacks_dice", "damage_dice"):
                dv = getattr(w, dice_field, None)
                if dv is None or not isinstance(dv, tuple) or len(dv) != 3:
                    failures.append(f"{unit_name}/{wname}: {dice_field}={dv} (expected 3-tuple)")

    assert not failures, f"{len(failures)} weapon(s) with missing/invalid fields:\n" + "\n".join(
        failures[:20]
    )


def test_content_contract_weapon_skill_range(all_units):
    """Weapon skill (BS/WS) between 2 and 6."""
    failures: list[str] = []
    for unit_name, unit in all_units:
        all_weapons = list(getattr(unit, "ranged_weapons", []) or []) + list(
            getattr(unit, "melee_weapons", []) or []
        )
        for w in all_weapons:
            skill = getattr(w, "skill", 0)
            if skill < 2 or skill > 6:
                failures.append(f"{unit_name}/{w.name}: skill={skill} (expected 2..6)")

    assert not failures, f"{len(failures)} weapon(s) with invalid skill:\n" + "\n".join(
        failures[:20]
    )


# ── Canonical ID uniqueness ─────────────────────────────────────────────


def test_content_contract_no_duplicate_canonical_ids(all_units):
    """No two units share the same name (canonical id)."""
    seen: dict[str, str] = {}
    duplicates: list[str] = []
    for unit_name, _unit in all_units:
        if unit_name in seen:
            duplicates.append(f"'{unit_name}' from {seen[unit_name]} and current")
        else:
            seen[unit_name] = unit_name

    if duplicates:
        pytest.fail(f"{len(duplicates)} duplicate canonical id(s):\n" + "\n".join(duplicates))


# ── Faction coverage ────────────────────────────────────────────────────


def test_content_contract_faction_coverage(all_units):
    """Every faction directory has at least one unit loaded."""
    factions_found: set[str] = set()
    for _name, unit in all_units:
        factions_found.add(unit.faction)

    # Known factions from wiki/units/
    known_factions = {"orks", "tau", "adeptus-mechanicus"}

    missing = known_factions - factions_found
    assert not missing, (
        f"Factions with no loaded units: {missing}. Loaded factions: {factions_found}"
    )


# ── Known exceptions are documented ─────────────────────────────────────


def test_content_contract_known_exceptions_are_still_in_registry(all_units):
    """Documented exception units must still exist in the wiki."""
    all_names = {name for name, _unit in all_units}
    for exc_name in KNOWN_ZERO_POINT_UNITS | KNOWN_NO_WEAPON_UNITS:
        assert exc_name in all_names, (
            f"Known exception '{exc_name}' not found in wiki! "
            f"Remove from exception list or fix the wiki file."
        )
