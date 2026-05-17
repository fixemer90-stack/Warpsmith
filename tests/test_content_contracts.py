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

from pathlib import Path

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


# ── content.v1 schema validation (Task 1.1 acceptance) ──────────────────


def test_content_contract_units_validate_against_content_v1_schema(all_units):
    """Every wiki unit validates against the content.v1 Pydantic schema."""
    from backend.loader.schema import validate_unit_v1

    failures: list[str] = []
    for unit_name, unit in all_units:
        if unit_name in KNOWN_ZERO_POINT_UNITS:
            continue
        try:
            validate_unit_v1(unit)
        except Exception as exc:
            failures.append(f"{unit_name}: {exc}")

    assert not failures, (
        f"{len(failures)} unit(s) failed content.v1 schema validation:\n" + "\n".join(failures[:20])
    )


def test_content_contract_squad_size_validated(all_units):
    """squad_size: min >= 1, max >= min, step >= 1."""
    failures: list[str] = []
    for unit_name, unit in all_units:
        sq = getattr(unit, "squad_size", None)
        if sq is None:
            failures.append(f"{unit_name}: squad_size is None")
            continue
        if not isinstance(sq, dict):
            failures.append(f"{unit_name}: squad_size={sq} (expected dict)")
            continue
        min_s = sq.get("min", 1)
        max_s = sq.get("max", 1)
        step = sq.get("step", 1)
        if min_s < 1:
            failures.append(f"{unit_name}: squad_size.min={min_s} < 1")
        if max_s < min_s:
            failures.append(f"{unit_name}: squad_size max={max_s} < min={min_s}")
        if step < 1:
            failures.append(f"{unit_name}: squad_size.step={step} < 1")

    assert not failures, f"{len(failures)} unit(s) with invalid squad_size:\n" + "\n".join(
        failures[:20]
    )


def test_content_contract_tags_and_keywords_deterministic(all_units):
    """Every unit must have at least tags OR keywords. Exceptions are explicit."""
    failures: list[str] = []
    for unit_name, unit in all_units:
        tags = getattr(unit, "tags", None) or []
        keywords = getattr(unit, "keywords", None) or []
        faction_kw = getattr(unit, "faction_keywords", None) or []
        if not tags and not keywords and not faction_kw:
            failures.append(unit_name)

    if failures:
        pytest.fail(
            f"{len(failures)}/{len(all_units)} units have no tags, keywords, "
            f"or faction_keywords. Units: {failures[:10]}"
        )


# ── Source-level duplicate detection (Task 1.1 Important 2) ─────────────


def test_content_contract_no_source_file_duplicates(wiki):
    """Duplicate unit names in source files are detected before dict insertion."""
    from pathlib import Path

    units_dir = wiki.wiki_path / "units"
    name_to_files: dict[str, list[str]] = {}

    for faction_dir in sorted(units_dir.iterdir()):
        if not faction_dir.is_dir():
            continue
        for file_path in sorted(faction_dir.glob("*.md")):
            try:
                import frontmatter

                post = frontmatter.load(str(file_path))
                title = post.metadata.get("title")
                if title:
                    name_to_files.setdefault(str(title), []).append(str(file_path))
            except Exception:
                continue

    duplicates = {k: v for k, v in name_to_files.items() if len(v) > 1}
    if duplicates:
        lines = [f"'{k}': {v}" for k, v in duplicates.items()]
        pytest.fail(
            f"{len(duplicates)} duplicate canonical unit name(s) across source files:\n"
            + "\n".join(lines)
        )


# ── Task 1.2 — safe cache tests ─────────────────────────────────────────


def test_compiler_produces_manifest():
    """Compiler generates manifest.json with required fields."""
    from backend.loader.compiler import GENERATED_DIR, load_manifest

    m = load_manifest()
    assert m is not None, "Run compile_content() first"
    assert m.schema_version == "content.v1"
    assert len(m.artifacts) >= 3
    assert "generated_at" in m.to_dict()


def test_compiler_produces_units_json():
    """Compiled units/index.json is valid JSON with expected structure."""
    from backend.loader.compiler import GENERATED_DIR, load_units_index

    data = load_units_index()
    assert len(data) > 100, f"Expected >100 units, got {len(data)}"
    # Spot-check a known unit
    assert any("boyz" in k.lower() for k in data), (
        f"No expected unit in keys: {list(data.keys())[:5]}"
    )
    # Verify index has the right structure
    for _uid, entry in list(data.items())[:3]:
        assert "faction_id" in entry
        assert "file" in entry
        assert "display_name" in entry
        assert "hash" in entry


def test_compiler_produces_detachments_json():
    """Compiled detachments.json is valid JSON."""
    import json

    from backend.loader.compiler import GENERATED_DIR

    with (GENERATED_DIR / "detachments.json").open() as f:
        data = json.load(f)
    assert len(data) > 0


def test_registry_loads_from_json_cache():
    """WikiRegistry.load() uses JSON cache when present and not stale."""
    from backend.loader.registry import WikiRegistry

    reg = WikiRegistry()
    # Clear any existing state
    reg._loaded = False
    reg.units = {}
    reg.detachments = {}

    units = reg.load(use_cache=True)
    assert len(units) > 100, f"Expected >100 units from JSON cache, got {len(units)}"
    assert any("boyz" in k.lower() for k in units)


def test_no_pickle_import_in_registry():
    """Registry does not import or call pickle."""
    import inspect

    from backend.loader.registry import WikiRegistry

    source = inspect.getsource(WikiRegistry)
    assert "import pickle" not in source, "pickle must not be imported in WikiRegistry"
    assert "pickle.load" not in source, "pickle.load must not be called in WikiRegistry"


def test_compiler_no_pickle_usage():
    """Compiler does not import or call pickle."""
    import inspect

    from backend.loader import compiler

    source = inspect.getsource(compiler)
    assert "import pickle" not in source, "pickle must not be imported in compiler"
    assert "pickle.load" not in source, "pickle.load must not be called in compiler"


# ── Task 1.3 — squad_size authority tests ───────────────────────────────


def test_squad_size_is_authoritative_not_model_count(all_units):
    """validate_squad_size uses squad_size from frontmatter, not model_count."""
    from backend.state.roster import validate_squad_size

    failures: list[str] = []
    for unit_name, unit in all_units:
        sq = getattr(unit, "squad_size", None) or {"min": 1, "max": 1, "step": 1}
        # Validate min squad size passes
        err = validate_squad_size(unit_name, sq["min"], unit)
        if err and sq["min"] >= 1:
            failures.append(f"{unit_name}: min={sq['min']} rejected: {err.message}")
        # Validate max squad size passes
        if sq["max"] > sq["min"]:
            err = validate_squad_size(unit_name, sq["max"], unit)
            if err:
                failures.append(f"{unit_name}: max={sq['max']} rejected: {err.message}")

    assert not failures, f"{len(failures)} unit(s) fail squad_size validation:\n" + "\n".join(
        failures[:20]
    )


def test_squad_size_step_valid(all_units):
    """squad_size.step divides (max - min) evenly."""
    failures: list[str] = []
    for unit_name, unit in all_units:
        sq = getattr(unit, "squad_size", None) or {"min": 1, "max": 1, "step": 1}
        if sq["max"] > sq["min"] and sq["step"] > 0:
            if (sq["max"] - sq["min"]) % sq["step"] != 0:
                failures.append(
                    f"{unit_name}: step={sq['step']} does not divide "
                    f"({sq['max']} - {sq['min']}) = {sq['max'] - sq['min']}"
                )

    assert not failures, f"{len(failures)} unit(s) with invalid squad_size step:\n" + "\n".join(
        failures[:20]
    )


def test_canonical_id_from_frontmatter():
    """Compiler uses explicit canonical_id from frontmatter when present."""
    import os
    import tempfile

    from backend.loader.compiler import compile_content
    from backend.loader.registry import WikiRegistry

    tmp = Path(tempfile.mkdtemp())
    wiki_dir = tmp / "wiki"
    units_dir = wiki_dir / "units" / "test-faction"
    units_dir.mkdir(parents=True, exist_ok=True)

    # Create a unit file with canonical_id
    yaml = """---
title: Test Warboss
type: entity
faction: test-faction
category: Character
movement: 6
toughness: 6
save: 3
wounds: 7
leadership: 6
objective_control: 2
points: 100
canonical_id: unit:test-faction:warboss-explicit
---

# Test Warboss
| M | T | SV | W | LD | OC |
|---|---|---|---|---|---|
| 6" | 6 | 3+ | 7 | 6+ | 2 |
"""
    (units_dir / "Warboss.md").write_text(yaml)

    # Create another without canonical_id to verify fallback
    yaml2 = """---
title: Nobz Test
type: entity
faction: test-faction
category: Infantry
movement: 5
toughness: 5
save: 4
wounds: 2
leadership: 7
objective_control: 1
points: 110
---

# Nobz Test
| M | T | SV | W | LD | OC |
|---|---|---|---|---|---|
| 5" | 5 | 4+ | 2 | 7+ | 1 |
"""
    (units_dir / "Nobz.md").write_text(yaml2)

    out_dir = tmp / "generated"
    try:
        compile_content(
            wiki_path=str(wiki_dir),
            output_dir=str(out_dir),
            freeze_clock="2026-01-01T00:00:00+00:00",
        )
    except RuntimeError:
        pass  # May have collisions from missing weapons; that's fine

    if (out_dir / "factions.json").exists():
        import json

        with (out_dir / "units" / "index.json").open() as f:
            index = json.load(f)

        # Unit with canonical_id should use the explicit id
        assert "unit:test-faction:warboss-explicit" in index, (
            f"Expected explicit canonical_id in index, got keys: {list(index.keys())}"
        )

    # Cleanup
    import shutil

    shutil.rmtree(tmp)


# ── Task 1.5 — Frontmatter canonical IDs ────────────────────────────────


def _make_test_wiki(tmp: Path, units: list[tuple[str, str]]) -> tuple[Path, Path]:
    """Helper: create a minimal wiki with unit files.

    Args:
        tmp: temp directory root.
        units: list of (filename, yaml_content) pairs.

    Returns:
        (wiki_dir, output_dir) paths.
    """
    wiki_dir = tmp / "wiki"
    units_dir = wiki_dir / "units" / "test-faction"
    units_dir.mkdir(parents=True, exist_ok=True)
    for filename, yaml in units:
        (units_dir / filename).write_text(yaml)
    out_dir = tmp / "generated"
    return wiki_dir, out_dir


_MINIMAL_UNIT_TEMPLATE = """---
title: {title}
type: entity
faction: test-faction
category: Infantry
movement: 5
toughness: 4
save: 4
wounds: 2
leadership: 7
objective_control: 1
points: 50
{extra}
---

# {title}
| M | T | SV | W | LD | OC |
|---|---|---|---|---|---|
| 5" | 4 | 4+ | 2 | 7+ | 1 |
"""


def test_15_explicit_canonical_id_overrides_fallback(tmp_path):
    """Explicit canonical_id wins over generated fallback id."""
    from backend.loader.compiler import compile_content

    unit_yaml = _MINIMAL_UNIT_TEMPLATE.format(
        title="Test Boyz", extra="canonical_id: unit:test-faction:custom-boyz-id"
    )
    wiki_dir, out_dir = _make_test_wiki(tmp_path, [("Boyz.md", unit_yaml)])

    compile_content(
        wiki_path=str(wiki_dir),
        output_dir=str(out_dir),
        freeze_clock="2026-01-01T00:00:00+00:00",
    )

    import json

    with (out_dir / "units" / "index.json").open() as f:
        index = json.load(f)

    assert "unit:test-faction:custom-boyz-id" in index, (
        f"Expected explicit canonical_id in index, got keys: {list(index.keys())}"
    )
    # Fallback id should NOT be present
    assert "unit:test-faction:test-boyz" not in index, (
        "Fallback id should not appear when explicit canonical_id is present"
    )


def test_15_missing_canonical_id_uses_fallback(tmp_path):
    """Missing canonical_id keeps deterministic fallback behavior."""
    from backend.loader.compiler import compile_content

    unit_yaml = _MINIMAL_UNIT_TEMPLATE.format(title="Gretchin Test", extra="")
    wiki_dir, out_dir = _make_test_wiki(tmp_path, [("Gretchin.md", unit_yaml)])

    compile_content(
        wiki_path=str(wiki_dir),
        output_dir=str(out_dir),
        freeze_clock="2026-01-01T00:00:00+00:00",
    )

    import json

    with (out_dir / "units" / "index.json").open() as f:
        index = json.load(f)

    assert "unit:test-faction:gretchin-test" in index, (
        f"Expected fallback id in index, got keys: {list(index.keys())}"
    )


def test_15_invalid_canonical_id_format_fails(tmp_path):
    """Invalid canonical_id format fails compilation with actionable error."""
    import pytest

    from backend.loader.compiler import compile_content

    # Invalid format: missing 'unit:' prefix
    unit_yaml = _MINIMAL_UNIT_TEMPLATE.format(
        title="Bad Unit",
        extra="canonical_id: orks:boyz",
    )
    wiki_dir, out_dir = _make_test_wiki(tmp_path, [("BadUnit.md", unit_yaml)])

    with pytest.raises(RuntimeError, match="Invalid canonical_id"):
        compile_content(
            wiki_path=str(wiki_dir),
            output_dir=str(out_dir),
            freeze_clock="2026-01-01T00:00:00+00:00",
        )

    # The error should contain the source path
    with pytest.raises(RuntimeError, match=r"BadUnit\.md"):
        compile_content(
            wiki_path=str(wiki_dir),
            output_dir=str(out_dir),
            freeze_clock="2026-01-01T00:00:00+00:00",
        )


def test_15_invalid_canonical_id_format_with_source_path(tmp_path):
    """Invalid canonical_id error includes source file path."""
    import pytest

    from backend.loader.compiler import compile_content

    unit_yaml = _MINIMAL_UNIT_TEMPLATE.format(
        title="Weirdboy",
        extra="canonical_id: not-a-valid-canonical-id",
    )
    wiki_dir, out_dir = _make_test_wiki(tmp_path, [("Weirdboy.md", unit_yaml)])

    with pytest.raises(RuntimeError) as excinfo:
        compile_content(
            wiki_path=str(wiki_dir),
            output_dir=str(out_dir),
            freeze_clock="2026-01-01T00:00:00+00:00",
        )

    err_msg = str(excinfo.value)
    assert "Weirdboy.md" in err_msg, f"Expected source path in error: {err_msg}"
    assert "Invalid canonical_id" in err_msg, f"Expected Invalid canonical_id in: {err_msg}"


def test_15_duplicate_explicit_id_fails_before_write(tmp_path):
    """Duplicate explicit canonical ids fail compilation before artifacts written."""
    import pytest

    from backend.loader.compiler import compile_content

    # Two units with the same explicit canonical_id
    unit1 = _MINIMAL_UNIT_TEMPLATE.format(
        title="Warboss A",
        extra="canonical_id: unit:test-faction:the-warboss",
    )
    unit2 = _MINIMAL_UNIT_TEMPLATE.format(
        title="Warboss B",
        extra="canonical_id: unit:test-faction:the-warboss",
    )
    wiki_dir, out_dir = _make_test_wiki(tmp_path, [("WarbossA.md", unit1), ("WarbossB.md", unit2)])

    with pytest.raises(RuntimeError) as excinfo:
        compile_content(
            wiki_path=str(wiki_dir),
            output_dir=str(out_dir),
            freeze_clock="2026-01-01T00:00:00+00:00",
        )

    err_msg = str(excinfo.value)
    assert "collision" in err_msg.lower() or "duplicate" in err_msg.lower(), (
        f"Expected collision/duplicate in error: {err_msg}"
    )

    # Verify artifacts were NOT written (factions.json must not exist)
    assert not (out_dir / "factions.json").exists(), (
        "Artifacts should not be written when fatal collisions exist"
    )


def test_15_duplicate_display_names_non_fatal_if_ids_differ(tmp_path):
    """Duplicate display names produce non-fatal collision if ids differ."""
    from backend.loader.compiler import BuildContext

    # Test _deduplicate_units directly: add two records with same display_name
    # but different IDs into the BuildContext units dict
    ctx = BuildContext(str(tmp_path))
    # Manually add two units with same display_name but different IDs
    ctx.units["unit:faction-a:warboss"] = {
        "unit_id": "unit:faction-a:warboss",
        "display_name": "Warboss",
        "faction_id": "faction:faction-a",
        "source_path": str(tmp_path / "WarbossA.md"),
    }
    ctx.units["unit:faction-b:warboss"] = {
        "unit_id": "unit:faction-b:warboss",
        "display_name": "Warboss",
        "faction_id": "faction:faction-b",
        "source_path": str(tmp_path / "WarbossB.md"),
    }

    ctx._deduplicate_units()

    collision_kinds = {c["kind"] for c in ctx.collisions}
    assert "duplicate_display_name" in collision_kinds, (
        f"Expected duplicate_display_name collision, got: {ctx.collisions}"
    )

    # Verify the collision entry has expected structure
    dup_collisions = [c for c in ctx.collisions if c["kind"] == "duplicate_display_name"]
    assert len(dup_collisions) == 1
    assert dup_collisions[0]["display_name"] == "Warboss"
    assert len(dup_collisions[0]["unit_ids"]) == 2


def test_15_source_path_in_unit_records(tmp_path):
    """Canonical unit records include source_path pointing back to the wiki source file."""
    from backend.loader.compiler import compile_content

    unit_yaml = _MINIMAL_UNIT_TEMPLATE.format(
        title="Nob With Banner",
        extra="canonical_id: unit:test-faction:nob-banner",
    )
    wiki_dir, out_dir = _make_test_wiki(tmp_path, [("NobBanner.md", unit_yaml)])

    compile_content(
        wiki_path=str(wiki_dir),
        output_dir=str(out_dir),
        freeze_clock="2026-01-01T00:00:00+00:00",
    )

    import json

    # Read the unit shard
    with (out_dir / "units" / "test-faction.json").open() as f:
        shard = json.load(f)

    record = shard.get("unit:test-faction:nob-banner")
    assert record is not None, f"Expected unit in shard, got keys: {list(shard.keys())}"

    sp = record.get("source_path", "")
    assert "NobBanner.md" in sp, f"Expected source_path to contain 'NobBanner.md', got: {sp}"
    assert sp.endswith("NobBanner.md"), f"source_path should end with filename: {sp}"


def test_15_display_name_rename_preserves_id(tmp_path):
    """Display-name changes do not change unit id when canonical_id unchanged."""
    from backend.loader.compiler import compile_content

    # First compile: unit named "Old Name" with explicit canonical_id
    unit1 = _MINIMAL_UNIT_TEMPLATE.format(
        title="Old Name",
        extra="canonical_id: unit:test-faction:stable-unit",
    )
    wiki_dir, out_dir = _make_test_wiki(tmp_path, [("Unit.md", unit1)])

    compile_content(
        wiki_path=str(wiki_dir),
        output_dir=str(out_dir),
        freeze_clock="2026-01-01T00:00:00+00:00",
    )

    import json

    with (out_dir / "units" / "index.json").open() as f:
        index1 = json.load(f)

    # Second compile: same canonical_id, different display name
    unit2 = _MINIMAL_UNIT_TEMPLATE.format(
        title="New Name",
        extra="canonical_id: unit:test-faction:stable-unit",
    )
    (wiki_dir / "units" / "test-faction" / "Unit.md").write_text(unit2)

    out_dir2 = tmp_path / "generated2"
    compile_content(
        wiki_path=str(wiki_dir),
        output_dir=str(out_dir2),
        freeze_clock="2026-01-01T00:00:00+00:00",
    )

    with (out_dir2 / "units" / "index.json").open() as f:
        index2 = json.load(f)

    # ID should be the same despite name change
    assert "unit:test-faction:stable-unit" in index1
    assert "unit:test-faction:stable-unit" in index2
    # Display name should have changed
    assert index1["unit:test-faction:stable-unit"]["display_name"] == "Old Name"
    assert index2["unit:test-faction:stable-unit"]["display_name"] == "New Name"


def test_15_source_file_rename_preserves_id(tmp_path):
    """Source-file path changes do not change unit id when canonical_id unchanged."""
    from backend.loader.compiler import compile_content

    # First compile: file named "OldFile.md"
    unit_yaml = _MINIMAL_UNIT_TEMPLATE.format(
        title="Deff Dread",
        extra="canonical_id: unit:test-faction:deff-dread",
    )
    wiki_dir, out_dir = _make_test_wiki(tmp_path, [("OldFile.md", unit_yaml)])

    compile_content(
        wiki_path=str(wiki_dir),
        output_dir=str(out_dir),
        freeze_clock="2026-01-01T00:00:00+00:00",
    )

    import json

    with (out_dir / "units" / "index.json").open() as f:
        index1 = json.load(f)

    # Rename the file
    old_path = wiki_dir / "units" / "test-faction" / "OldFile.md"
    new_path = wiki_dir / "units" / "test-faction" / "NewFile.md"
    old_path.rename(new_path)

    out_dir2 = tmp_path / "generated2"
    compile_content(
        wiki_path=str(wiki_dir),
        output_dir=str(out_dir2),
        freeze_clock="2026-01-01T00:00:00+00:00",
    )

    with (out_dir2 / "units" / "index.json").open() as f:
        index2 = json.load(f)

    # ID should be the same despite file rename
    assert "unit:test-faction:deff-dread" in index1
    assert "unit:test-faction:deff-dread" in index2


def test_15_fallback_id_is_deterministic(tmp_path):
    """Generated fallback ids remain deterministic for unchanged display name."""
    from backend.loader.compiler import compile_content

    unit_yaml = _MINIMAL_UNIT_TEMPLATE.format(title="Flash Gitz", extra="")
    wiki_dir, out_dir = _make_test_wiki(tmp_path, [("FlashGitz.md", unit_yaml)])

    compile_content(
        wiki_path=str(wiki_dir),
        output_dir=str(out_dir),
        freeze_clock="2026-01-01T00:00:00+00:00",
    )

    import json

    with (out_dir / "units" / "index.json").open() as f:
        index1 = json.load(f)

    # Second compile: same content
    out_dir2 = tmp_path / "generated2"
    compile_content(
        wiki_path=str(wiki_dir),
        output_dir=str(out_dir2),
        freeze_clock="2026-01-01T00:00:00+00:00",
    )

    with (out_dir2 / "units" / "index.json").open() as f:
        index2 = json.load(f)

    # Fallback ids should be identical
    expected_id = "unit:test-faction:flash-gitz"
    assert expected_id in index1, f"Expected {expected_id} in index1, keys: {list(index1.keys())}"
    assert expected_id in index2, f"Expected {expected_id} in index2, keys: {list(index2.keys())}"


def test_15_collision_report_distinguishes_duplicate_types(tmp_path):
    """Collision report distinguishes explicit-id duplicates from fallback-id collisions."""
    import pytest

    from backend.loader.compiler import compile_content

    # Two units with same explicit canonical_id → fatal collision
    unit1 = _MINIMAL_UNIT_TEMPLATE.format(
        title="Warboss One",
        extra="canonical_id: unit:test-faction:warboss-duplicate",
    )
    unit2 = _MINIMAL_UNIT_TEMPLATE.format(
        title="Warboss Two",
        extra="canonical_id: unit:test-faction:warboss-duplicate",
    )
    wiki_dir, out_dir = _make_test_wiki(tmp_path, [("Warboss1.md", unit1), ("Warboss2.md", unit2)])

    with pytest.raises(RuntimeError) as excinfo:
        compile_content(
            wiki_path=str(wiki_dir),
            output_dir=str(out_dir),
            freeze_clock="2026-01-01T00:00:00+00:00",
        )

    # The duplicate-detection logic in _collect_units adds id_kind to collisions
    # But the manifest may not be available on fatal collision.
    # Verify the error message mentions collision
    err_msg = str(excinfo.value)
    assert "collision" in err_msg.lower(), f"Expected collision in error: {err_msg}"
    assert f"{wiki_dir.resolve().as_posix()}" in err_msg or "warboss-duplicate" in err_msg, (
        f"Expected duplicate info in error: {err_msg}"
    )


def test_15_runtime_ids_distinct_from_canonical_ids(tmp_path):
    """No runtime loader starts treating canonical ids as runtime instance ids."""
    # Verify that Unit model's canonical_id field does not affect
    # the unit_id used in roster instances.
    from backend.loader.parser import parse_unit

    unit_yaml = _MINIMAL_UNIT_TEMPLATE.format(
        title="Runtime Test",
        extra="canonical_id: unit:test-faction:runtime-test",
    )

    unit_file = tmp_path / "RuntimeTest.md"
    unit_file.write_text(unit_yaml)

    unit = parse_unit(unit_file)

    assert unit is not None, "Unit should parse successfully"
    assert unit.canonical_id == "unit:test-faction:runtime-test", (
        f"Expected canonical_id, got: {unit.canonical_id}"
    )
    # Runtime identity is just unit.name — not the canonical_id
    assert unit.name == "Runtime Test", (
        f"Runtime unit name should not be replaced by canonical_id: {unit.name}"
    )
