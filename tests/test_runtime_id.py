"""Tests for runtime unit identity contract — Task 0.1."""

import pytest

from backend.state.runtime_id import (
    RUNTIME_UNIT_ID_SEPARATOR,
    is_valid_runtime_unit_id,
    make_runtime_unit_id,
    parse_runtime_unit_id,
)

# ── make_runtime_unit_id ──────────────────────────────────────────


def test_make_runtime_unit_id_basic():
    """Generates correct format for a single unit."""
    rid = make_runtime_unit_id("1", "Nobz", 0)
    assert rid == "p1:Nobz:0"


def test_make_runtime_unit_id_strips_p_prefix():
    """Strips 'p' prefix if caller passes 'p1'."""
    assert make_runtime_unit_id("p1", "Gretchin", 2) == "p1:Gretchin:2"
    assert make_runtime_unit_id("P2", "Fire Warriors", 0) == "p2:Fire Warriors:0"


def test_make_runtime_unit_id_increments_index():
    """Index increments produce distinct IDs for the same canonical unit."""
    ids = [make_runtime_unit_id("1", "Boyz", i) for i in range(3)]
    assert ids == ["p1:Boyz:0", "p1:Boyz:1", "p1:Boyz:2"]


def test_make_runtime_unit_id_different_players():
    """Same unit name, different players → different runtime IDs."""
    a = make_runtime_unit_id("1", "Intercessor", 0)
    b = make_runtime_unit_id("2", "Intercessor", 0)
    assert a == "p1:Intercessor:0"
    assert b == "p2:Intercessor:0"
    assert a != b


def test_make_runtime_unit_id_uniqueness():
    """Every generated ID is unique within reasonable bounds."""
    ids = set()
    for player in ("1", "2"):
        for unit in ("A", "B", "C"):
            for idx in range(5):
                rid = make_runtime_unit_id(player, unit, idx)
                assert rid not in ids, f"Collision: {rid}"
                ids.add(rid)
    assert len(ids) == 2 * 3 * 5  # 30 unique IDs


# ── parse_runtime_unit_id ─────────────────────────────────────────


def test_parse_valid():
    """Parses a valid runtime unit ID."""
    result = parse_runtime_unit_id("p1:Nobz:0")
    assert result == {"player_num": 1, "canonical_id": "Nobz", "index": 0}


def test_parse_with_spaces_in_canonical():
    """Canonical ID with spaces."""
    result = parse_runtime_unit_id("p1:Fire Warriors:0")
    assert result == {"player_num": 1, "canonical_id": "Fire Warriors", "index": 0}


def test_parse_invalid_format():
    """Rejects malformed IDs."""
    bad_ids = [
        "Nobz:0",  # no p prefix
        "p1:Nobz",  # missing index
        "p:Nobz:0",  # non-numeric player
        "p1:Nobz:abc",  # non-numeric index
        "1:Nobz:0",  # no p prefix
        "",  # empty
        "p1::0",  # empty canonical
    ]
    for bid in bad_ids:
        with pytest.raises(ValueError):
            parse_runtime_unit_id(bid)


# ── is_valid_runtime_unit_id ──────────────────────────────────────


def test_is_valid_accepts_good():
    """Valid IDs return True."""
    assert is_valid_runtime_unit_id("p1:Nobz:0") is True
    assert is_valid_runtime_unit_id("p2:Fire Warriors:5") is True
    assert is_valid_runtime_unit_id("p1:A:0") is True


def test_is_valid_rejects_bad():
    """Invalid IDs return False."""
    assert is_valid_runtime_unit_id("Nobz") is False
    assert is_valid_runtime_unit_id("p1:Nobz") is False
    assert is_valid_runtime_unit_id("") is False


# ── Round-trip ────────────────────────────────────────────────────


def test_round_trip():
    """make → parse should recover the original components."""
    for player in ("1", "2"):
        for unit in ("Nobz", "Gretchin", "Fire Warriors"):
            for idx in (0, 1, 7):
                rid = make_runtime_unit_id(player, unit, idx)
                parsed = parse_runtime_unit_id(rid)
                assert parsed["player_num"] == int(player)
                assert parsed["canonical_id"] == unit
                assert parsed["index"] == idx


# ── Contract invariants ───────────────────────────────────────────


def test_runtime_id_not_equal_to_display_name():
    """Runtime ID MUST NOT equal the display name."""
    rid = make_runtime_unit_id("1", "Nobz", 0)
    assert rid != "Nobz"
    assert "Nobz" in rid  # contains, but is not equal to


def test_runtime_ids_stable_across_regeneration():
    """Same inputs always produce the same runtime ID."""
    for _ in range(100):
        assert make_runtime_unit_id("1", "Nobz", 0) == "p1:Nobz:0"


def test_runtime_id_not_derived_from_name_alone():
    """Runtime ID includes player and occurrence index beyond just name."""
    rid = make_runtime_unit_id("1", "X", 0)
    # The ID must contain more information than just the name
    assert rid != "X"
    assert "p1" in rid
    assert "0" in rid.split(RUNTIME_UNIT_ID_SEPARATOR)[-1]
