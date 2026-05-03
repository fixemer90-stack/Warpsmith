"""Tests for leader compatibility checker."""

from backend.model.unit import Unit
from backend.state.leader_checker import (
    LeaderCompatibilityResult,
    check_leader_compatibility,
    validate_leader_assignments,
    get_leader_hints,
)


def test_leader_can_attach():
    warboss = Unit(
        name="Warboss",
        faction="Orks",
        category="Character",
        movement=4,
        toughness=4,
        save=4,
        wounds=3,
        leadership=7,
        objective_control=1,
        is_leader=True,
        leader_for=["Boyz"],
        keywords=["Character"],
        faction_keywords=["Orks"],
    )
    boyz = Unit(
        name="Boyz",
        faction="Orks",
        category="Battleline",
        movement=4,
        toughness=3,
        save=6,
        wounds=1,
        leadership=5,
        objective_control=1,
        keywords=["Infantry", "Battleline"],
    )
    result = check_leader_compatibility(warboss, boyz)
    assert result.is_compatible


def test_leader_wrong_unit():
    warboss = Unit(
        name="Warboss",
        faction="Orks",
        category="Character",
        movement=4,
        toughness=4,
        save=4,
        wounds=3,
        leadership=7,
        objective_control=1,
        is_leader=True,
        leader_for=["Boyz"],
        keywords=["Character"],
        faction_keywords=["Orks"],
    )
    marine = Unit(
        name="Tactical Marine",
        faction="Space Marines",
        category="Battleline",
        movement=4,
        toughness=4,
        save=3,
        wounds=2,
        leadership=6,
        objective_control=1,
        keywords=["Infantry"],
    )
    result = check_leader_compatibility(warboss, marine)
    assert not result.is_compatible
    assert "cannot lead" in result.issues[0]


def test_not_a_leader():
    boyz = Unit(
        name="Boyz",
        faction="Orks",
        category="Battleline",
        movement=4,
        toughness=3,
        save=6,
        wounds=1,
        leadership=5,
        objective_control=1,
        is_leader=False,
        keywords=["Infantry"],
    )
    boyz2 = Unit(
        name="Boyz",
        faction="Orks",
        category="Battleline",
        movement=4,
        toughness=3,
        save=6,
        wounds=1,
        leadership=5,
        objective_control=1,
        keywords=["Infantry"],
    )
    result = check_leader_compatibility(boyz, boyz2)
    assert not result.is_compatible
    assert "not a leader" in result.issues[0]


def test_max_two_leaders():
    warboss = Unit(
        name="Warboss",
        faction="Orks",
        category="Character",
        movement=4,
        toughness=4,
        save=4,
        wounds=3,
        leadership=7,
        objective_control=1,
        is_leader=True,
        leader_for=["Boyz"],
        keywords=["Character", "Orks", "Infantry"],
        faction_keywords=["Orks"],
    )
    weirdboy = Unit(
        name="Weirdboy",
        faction="Orks",
        category="Character",
        movement=4,
        toughness=3,
        save=5,
        wounds=2,
        leadership=6,
        objective_control=1,
        is_leader=True,
        leader_for=["Boyz"],
        keywords=["Character", "Orks", "Infantry", "Psyker"],
        faction_keywords=["Orks"],
    )
    nob = Unit(
        name="Nob",
        faction="Orks",
        category="Character",
        movement=4,
        toughness=4,
        save=4,
        wounds=2,
        leadership=6,
        objective_control=1,
        is_leader=True,
        leader_for=["Boyz"],
        keywords=["Character", "Orks", "Infantry"],
        faction_keywords=["Orks"],
    )
    boyz = Unit(
        name="Boyz",
        faction="Orks",
        category="Battleline",
        movement=4,
        toughness=3,
        save=6,
        wounds=1,
        leadership=5,
        objective_control=1,
        keywords=["Infantry", "Battleline"],
    )
    result = check_leader_compatibility(nob, boyz, existing_leaders=[warboss, weirdboy])
    assert not result.is_compatible
    assert "Max 2 leaders" in result.issues[0]


def test_wildcard_battleline():
    """Лидер с leader_for=['BATTLELINE'] может присоединиться к любому Battleline."""
    leader = Unit(
        name="Generic Leader",
        faction="Imperium",
        category="Character",
        movement=4,
        toughness=3,
        save=4,
        wounds=2,
        leadership=5,
        objective_control=1,
        is_leader=True,
        leader_for=["BATTLELINE"],
        keywords=["Character"],
        faction_keywords=["Imperium"],
    )
    boyz = Unit(
        name="Boyz",
        faction="Orks",
        category="Battleline",
        movement=4,
        toughness=3,
        save=6,
        wounds=1,
        leadership=5,
        objective_control=1,
        keywords=["Battleline"],
    )
    result = check_leader_compatibility(leader, boyz)
    assert result.is_compatible


def test_validate_leader_assignments():
    # Valid assignment: one leader attached to a unit
    warboss = Unit(
        name="Warboss",
        faction="Orks",
        category="Character",
        movement=4,
        toughness=4,
        save=4,
        wounds=3,
        leadership=7,
        objective_control=1,
        is_leader=True,
        leader_for=["Boyz"],
        keywords=["Character"],
        faction_keywords=["Orks"],
    )
    boyz = Unit(
        name="Boyz",
        faction="Orks",
        category="Battleline",
        movement=4,
        toughness=3,
        save=6,
        wounds=1,
        leadership=5,
        objective_control=1,
        keywords=["Infantry", "Battleline"],
    )
    roster = [(warboss, 1), (boyz, 10)]
    results = validate_leader_assignments(roster)
    assert len(results) == 0  # No issues

    # Invalid: two leaders of same type (both Captain-like? Actually we don't have type in name, but by our rule, if both are leaders and same type by name?)
    # Let's test with two Warboss (both have "Warboss" in name, so both would be considered "captain" by our _get_leader_type? Actually no, we check for "captain" substring.
    # We'll change the test to use units that have "captain" and "lieutenant" in name to test the type rule.
    captain = Unit(
        name="Captain Squad",
        faction="Imperium",
        category="Character",
        movement=4,
        toughness=3,
        save=3,
        wounds=2,
        leadership=7,
        objective_control=1,
        is_leader=True,
        leader_for=["Tactical Marine"],
        keywords=["Character"],
        faction_keywords=["Imperium"],
    )
    lieutenant = Unit(
        name="Lieutenant Squad",
        faction="Imperium",
        category="Character",
        movement=4,
        toughness=3,
        save=3,
        wounds=2,
        leadership=6,
        objective_control=1,
        is_leader=True,
        leader_for=["Tactical Marine"],
        keywords=["Character"],
        faction_keywords=["Imperium"],
    )
    marine = Unit(
        name="Tactical Marine",
        faction="Imperium",
        category="Battleline",
        movement=4,
        toughness=3,
        save=3,
        wounds=2,
        leadership=6,
        objective_control=1,
        keywords=["Infantry"],
    )
    # Now test: two leaders (captain and lieutenant) on the same unit should be ok (different types)
    roster = [(captain, 1), (lieutenant, 1), (marine, 10)]
    results = validate_leader_assignments(roster)
    # Should be ok because they are different types
    assert len(results) == 0

    # Now test: two captains (same type) -> should fail
    captain2 = Unit(
        name="Captain Squad 2",
        faction="Imperium",
        category="Character",
        movement=4,
        toughness=3,
        save=3,
        wounds=2,
        leadership=7,
        objective_control=1,
        is_leader=True,
        leader_for=["Tactical Marine"],
        keywords=["Character"],
        faction_keywords=["Imperium"],
    )
    roster = [(captain, 1), (captain2, 1), (marine, 10)]
    results = validate_leader_assignments(roster)
    assert len(results) > 0
    assert any("cannot join" in r.issues[0] and "captain" in r.issues[0] for r in results)


def test_get_leader_hints():
    warboss = Unit(
        name="Warboss",
        faction="Orks",
        category="Character",
        movement=4,
        toughness=4,
        save=4,
        wounds=3,
        leadership=7,
        objective_control=1,
        is_leader=True,
        leader_for=["Boyz"],
        keywords=["Character"],
        faction_keywords=["Orks"],
    )
    boyz = Unit(
        name="Boyz",
        faction="Orks",
        category="Battleline",
        movement=4,
        toughness=3,
        save=6,
        wounds=1,
        leadership=5,
        objective_control=1,
        keywords=["Infantry", "Battleline"],
    )
    marine = Unit(
        name="Tactical Marine",
        faction="Space Marines",
        category="Battleline",
        movement=4,
        toughness=4,
        save=3,
        wounds=2,
        leadership=6,
        objective_control=1,
        keywords=["Infantry"],
    )
    all_units = {
        "Warboss": warboss,
        "Boyz": boyz,
        "Tactical Marine": marine,
    }
    hints = get_leader_hints(boyz, all_units)
    assert len(hints) == 1
    assert "Warboss can lead this unit" in hints[0]

    # Marine should not be led by Warboss (if Warboss only leads Boyz)
    hints = get_leader_hints(marine, all_units)
    assert len(hints) == 0