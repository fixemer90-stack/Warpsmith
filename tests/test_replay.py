"""
Tests for F3.6 — Replay Recording: JSON Event Log per Round/Phase.
"""

import json
import sqlite3
from datetime import datetime

import pytest

from backend.engine.replay import (
    TABLE_REPLAYS,
    Replay,
    ReplayEvent,
    ReplayRecorder,
    ReplayRound,
    _pos_dict,
    _snapshot_state,
    _unit_snapshot,
    list_replays,
    load_replay,
    replay_from_json,
    replay_to_json,
    save_replay,
)
from backend.model.unit import Unit, Weapon
from backend.state.game_state import GamePhase, GameState, PlayerState, UnitState
from web.routes.api_replays import _parse_log_events


def make_test_unit(name: str = "Test Unit") -> Unit:
    """Create a simple Unit model for tests."""
    return Unit(
        name=name,
        faction="test",
        category="Infantry",
        movement=5,
        toughness=3,
        save=3,
        wounds=2,
        leadership=7,
        objective_control=1,
        ranged_weapons=[
            Weapon(
                name="Test Weapon",
                type="ranged",
                range_max=24,
                attacks_dice=(1, 6, 0),
                skill=4,
                strength=4,
                ap=0,
                damage_dice=(1, 3, 0),
            )
        ],
        points=100,
    )


def make_test_unit_state(
    name: str = "Test Unit",
    unit_id: str | None = None,
) -> UnitState:
    """Create a simple UnitState for tests."""
    return UnitState(
        unit_id=unit_id or name,
        name=name,
        faction="test",
        position=(10, 20),
        current_wounds=2,
        max_wounds=2,
        models_remaining=1,
        models_total=1,
        leadership=7,
        objective_control=1,
    )


def make_test_game_state() -> GameState:
    """Create a minimal GameState for tests."""
    unit_a = make_test_unit_state("Unit A", "unit-a-1")
    unit_b = make_test_unit_state("Unit B", "unit-b-1")
    unit_b.position = (30, 40)

    return GameState(
        game_id="test-game",
        mission_name="only_war",
        map_width=60,
        map_height=44,
        current_round=1,
        current_phase=GamePhase.SHOOTING,
        players={
            "1": PlayerState(
                player_id="1",
                name="Player 1",
                faction="orks",
                units={"unit-a-1": unit_a},
            ),
            "2": PlayerState(
                player_id="2",
                name="Player 2",
                faction="tau",
                units={"unit-b-1": unit_b},
            ),
        },
    )


# ── Data model tests ────────────────────────────────────────────


def test_replay_event_creation():
    """Test: creating a replay event."""
    event = ReplayEvent(
        timestamp=1000.0,
        round=1,
        phase="shooting",
        turn=1,
        event_type="shoot",
        actor_id="unit-1",
        actor_name="Test Unit",
        target_id="unit-2",
        target_name="Target Unit",
        weapon_name="Bolter",
        dice_rolled=[4, 5, 6],
        result_value=3.0,
        position_before={"x": 10, "y": 20},
        position_after={"x": 10, "y": 20},
    )

    assert event.timestamp == 1000.0
    assert event.event_type == "shoot"
    assert event.actor_name == "Test Unit"
    assert event.dice_rolled == [4, 5, 6]


def test_parse_log_events_uses_runtime_ids_when_metadata_present():
    """Parsed replay events keep runtime IDs separate from display labels."""
    events = _parse_log_events(
        [
            "Boyz hits Boyz for 3 damage [actor_id=p1:Boyz:0; target_id=p2:Boyz:0]",
            "Boyz was destroyed [target_id=p2:Boyz:0]",
        ],
        round_num=1,
    )

    assert events[0].actor_id == "p1:Boyz:0"
    assert events[0].actor_name == "Boyz"
    assert events[0].target_id == "p2:Boyz:0"
    assert events[0].target_name == "Boyz"
    assert events[1].target_id == "p2:Boyz:0"
    assert events[1].target_name == "Boyz"


def test_replay_round_creation():
    """Test: creating a replay round."""
    round_obj = ReplayRound(
        round=1,
        start_state={"round": 1, "phase": "movement"},
        end_state={"round": 1, "phase": "shooting"},
        events=[],
    )

    assert round_obj.round == 1
    assert round_obj.start_state["round"] == 1
    assert len(round_obj.events) == 0


def test_replay_creation():
    """Test: creating a full replay."""
    replay = Replay(
        game_id="test-game-123",
        created_at="2026-01-01T12:00:00Z",
        rosters={"roster_a": {"faction": "orks"}, "roster_b": {"faction": "tau"}},
        mission="only_war",
        deployment="standard",
        seed=42,
        rounds=[],
        summary={"winner": 1},
    )

    assert replay.game_id == "test-game-123"
    assert replay.mission == "only_war"
    assert replay.seed == 42
    assert replay.summary["winner"] == 1


# ── ReplayRecorder tests ────────────────────────────────────────


def test_replay_recorder_initialization():
    """Test: recorder initialization."""
    recorder = ReplayRecorder(
        game_id="test-123",
        rosters={"a": {}, "b": {}},
        mission="test_mission",
        deployment="standard",
        seed=123,
    )

    assert recorder.replay.game_id == "test-123"
    assert recorder.replay.mission == "test_mission"
    assert recorder.replay.seed == 123
    assert len(recorder.replay.rounds) == 0
    assert recorder._start_time is None


def test_replay_recorder_start_game():
    """Test: starting the game timer."""
    recorder = ReplayRecorder("test", {}, "mission", "deploy", 42)
    recorder.start_game()

    assert recorder._start_time is not None
    assert isinstance(recorder._start_time, float)


def test_replay_recorder_record_event():
    """Test: recording an event via recorder."""
    recorder = ReplayRecorder("test-123", {}, "mission", "deploy", 42)
    recorder.start_game()

    game_state = make_test_game_state()
    recorder.start_round(1, game_state)

    actor = make_test_unit_state("Actor", "actor-1")
    target = make_test_unit_state("Target", "target-1")

    recorder.record_shoot(
        round_num=1,
        phase="shooting",
        turn=1,
        actor=actor,
        target=target,
        weapon_name="Test Gun",
        damage=2.5,
    )

    recorder.end_round(game_state)

    assert len(recorder.replay.rounds) == 1
    assert len(recorder.replay.rounds[0].events) == 1

    event = recorder.replay.rounds[0].events[0]
    assert event.event_type == "shoot"
    assert event.actor_name == "Actor"
    assert event.target_name == "Target"
    assert event.weapon_name == "Test Gun"
    assert event.result_value == 2.5


def test_replay_recorder_round_lifecycle():
    """Test: full round lifecycle in recorder."""
    recorder = ReplayRecorder("test-123", {}, "mission", "deploy", 42)
    recorder.start_game()

    game_state = make_test_game_state()

    recorder.start_round(1, game_state)
    assert recorder._current_round is not None
    assert recorder._current_round.round == 1

    actor = make_test_unit_state("Actor", "actor-1")
    target = make_test_unit_state("Target", "target-1")

    recorder.record_shoot(1, "shooting", 1, actor, target, "Gun", 1.0)

    recorder.end_round(game_state)

    assert recorder._current_round is None
    assert len(recorder.replay.rounds) == 1
    assert len(recorder.replay.rounds[0].events) == 1


# ── Serialization tests ─────────────────────────────────────────


def test_replay_to_json_from_json():
    """Test: replay serialization roundtrip."""
    replay = Replay(
        game_id="json-test-123",
        created_at="2026-01-01T12:00:00Z",
        rosters={"test": "data"},
        mission="test_mission",
        deployment="test_deploy",
        seed=999,
        rounds=[
            ReplayRound(
                round=1,
                start_state={"round": 1},
                end_state={"round": 1, "completed": True},
                events=[
                    ReplayEvent(
                        timestamp=1000.0,
                        round=1,
                        phase="shooting",
                        turn=1,
                        event_type="shoot",
                        actor_id="unit-1",
                        actor_name="Test Actor",
                        target_id="unit-2",
                        target_name="Test Target",
                        weapon_name="Test Weapon",
                        result_value=2.0,
                    )
                ],
            )
        ],
        summary={"winner": 1, "total_rounds": 1},
    )

    json_str = replay_to_json(replay)
    assert isinstance(json_str, str)
    assert "json-test-123" in json_str
    assert "test_mission" in json_str

    restored = replay_from_json(json_str)

    assert restored.game_id == replay.game_id
    assert restored.mission == replay.mission
    assert restored.seed == replay.seed
    assert len(restored.rounds) == len(replay.rounds)
    assert len(restored.rounds[0].events) == 1
    assert restored.rounds[0].events[0].event_type == "shoot"
    assert restored.rounds[0].events[0].result_value == 2.0
    assert restored.summary["winner"] == 1


# ── SQLite persistence tests ────────────────────────────────────


def test_sqlite_replay_persistence():
    """Test: saving and loading replay from SQLite."""
    db = sqlite3.connect(":memory:")
    db.execute(TABLE_REPLAYS)

    replay = Replay(
        game_id="sqlite-test-123",
        created_at="2026-01-01T12:00:00Z",
        rosters={"a": {"faction": "orks"}, "b": {"faction": "tau"}},
        mission="only_war",
        deployment="hammer_and_anvil",
        seed=42,
        rounds=[],
        summary={"winner": 2},
    )

    save_replay(db, replay, user_id=1)

    loaded = load_replay(db, "sqlite-test-123")

    assert loaded is not None
    assert loaded.game_id == replay.game_id
    assert loaded.mission == replay.mission
    assert loaded.deployment == replay.deployment
    assert loaded.seed == replay.seed
    assert loaded.summary["winner"] == 2


def test_sqlite_load_nonexistent_replay():
    """Test: loading non-existent replay returns None."""
    db = sqlite3.connect(":memory:")
    db.execute(TABLE_REPLAYS)

    result = load_replay(db, "nonexistent-id")
    assert result is None


def test_sqlite_list_replays():
    """Test: listing replays from database."""
    db = sqlite3.connect(":memory:")
    db.execute(TABLE_REPLAYS)

    replay1 = Replay(
        game_id="replay-1",
        created_at="2026-01-01T12:00:00Z",
        rosters={"a": {}, "b": {}},
        mission="mission1",
        deployment="std",
        seed=1,
        rounds=[],
        summary={"winner": 1},
    )

    replay2 = Replay(
        game_id="replay-2",
        created_at="2026-01-02T12:00:00Z",
        rosters={"a": {}, "b": {}},
        mission="mission2",
        deployment="std",
        seed=2,
        rounds=[],
        summary={"winner": 2},
    )

    save_replay(db, replay1, user_id=1)
    save_replay(db, replay2, user_id=1)

    replays = list_replays(db, user_id=1)
    assert len(replays) == 2

    assert replays[0]["game_id"] == "replay-2"
    assert replays[1]["game_id"] == "replay-1"

    all_replays = list_replays(db)
    assert len(all_replays) == 2


def test_empty_replay_roundtrip():
    """Test: replay with no events roundtrips correctly."""
    replay = Replay(
        game_id="empty-replay",
        created_at="2026-01-01T12:00:00Z",
        rosters={"a": {}, "b": {}},
        mission="",
        deployment="",
        seed=0,
        rounds=[],
        summary={},
    )

    json_str = replay_to_json(replay)
    restored = replay_from_json(json_str)

    assert restored.game_id == replay.game_id
    assert len(restored.rounds) == 0
    assert restored.summary == {}


# ── Timestamp tests ─────────────────────────────────────────────


def test_recorder_timestamp_ordering():
    """Test: events have monotonically increasing timestamps."""
    recorder = ReplayRecorder("test-ts", {}, "mission", "deploy", 42)
    recorder.start_game()

    game_state = make_test_game_state()
    recorder.start_round(1, game_state)

    actor = make_test_unit_state("Actor", "actor-1")
    target = make_test_unit_state("Target", "target-1")

    recorder.record_shoot(1, "shooting", 1, actor, target, "Gun1", 1.0)
    recorder.record_shoot(1, "shooting", 1, actor, target, "Gun2", 2.0)
    recorder.record_shoot(1, "shooting", 1, actor, target, "Gun3", 3.0)

    recorder.end_round(game_state)

    events = recorder.replay.rounds[0].events
    timestamps = [e.timestamp for e in events]

    # Check timestamps are monotonically non-decreasing
    for i in range(len(timestamps) - 1):
        assert timestamps[i] <= timestamps[i + 1]


# ── Helper function tests ───────────────────────────────────────


def test_helper_functions():
    """Test: helper functions."""

    # Test _pos_dict with tuple
    result = _pos_dict((10, 20))
    assert result == {"x": 10, "y": 20}

    # Test _pos_dict with object attributes
    class MockPos:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    pos = MockPos(10, 20)
    result = _pos_dict(pos)
    assert result == {"x": 10, "y": 20}

    # Test _pos_dict with bad object
    class BadPos:
        pass

    bad_pos = BadPos()
    result = _pos_dict(bad_pos)
    assert result == {"x": 0, "y": 0}


def test_snapshot_state_with_current_api():
    """Test: _snapshot_state works with current GameState (players dict)."""
    state = make_test_game_state()
    snapshot = _snapshot_state(state)

    assert snapshot["round"] == 1
    assert snapshot["phase"] == "shooting"
    assert "victory_points" in snapshot
    assert "units" in snapshot
    # Should have player keys, not roster_a/b
    assert "1" in snapshot["units"]
    assert "2" in snapshot["units"]
    assert len(snapshot["units"]["1"]) == 1
    assert snapshot["units"]["1"][0]["name"] == "Unit A"


def test_unit_snapshot_with_current_api():
    """Test: _unit_snapshot works with current UnitState fields."""
    unit = make_test_unit_state("Test Unit", "test-id")
    snapshot = _unit_snapshot(unit)

    assert snapshot["id"] == "test-id"
    assert snapshot["name"] == "Test Unit"
    assert snapshot["models_remaining"] == 1
    assert snapshot["models_total"] == 1
    assert snapshot["current_wounds"] == 2
    assert snapshot["max_wounds"] == 2
    assert snapshot["position"]["x"] == 10
    assert snapshot["position"]["y"] == 20


# ── Task 0.2 — canonical snapshot tests ────────────────────────────────


def test_canonical_snapshot_round_and_final_identical_shape():
    """Round and final snapshots have identical top-level and unit keys."""
    from backend.engine.ai.autoplay import _snapshot_state as autoplay_snapshot
    from backend.engine.replay import _snapshot_state as replay_snapshot

    state = make_test_game_state()
    snap_a = autoplay_snapshot(state)
    snap_r = replay_snapshot(state)

    # Same top-level keys
    assert set(snap_a.keys()) == set(snap_r.keys())
    assert "round" in snap_a and "phase" in snap_a
    assert "victory_points" in snap_a and "units" in snap_a
    assert "map_width" in snap_a and "map_height" in snap_a

    # Same unit-level keys for first player's first unit
    ua = snap_a["units"]["1"][0]
    ur = snap_r["units"]["1"][0]
    assert set(ua.keys()) == set(ur.keys())


def test_canonical_snapshot_runtime_id_keys():
    """Unit entries include runtime_unit_id as authoritative id field."""
    from backend.engine.ai.autoplay import _snapshot_state

    state = make_test_game_state()
    # Give units proper runtime IDs
    for pid, player in state.players.items():
        for _rtid, unit in player.units.items():
            unit.unit_id = f"p{pid}:TestUnit:0"

    snap = _snapshot_state(state)
    for pid in ("1", "2"):
        for unit in snap["units"][pid]:
            assert unit["id"].startswith(f"p{pid}:")
            assert unit["name"]  # display_name still present


def test_canonical_snapshot_display_name_present():
    """display_name remains present for UI text even with runtime_id as key."""
    from backend.engine.ai.autoplay import _snapshot_state

    state = make_test_game_state()
    snap = _snapshot_state(state)

    for pid in ("1", "2"):
        for unit in snap["units"][pid]:
            assert "name" in unit
            assert len(unit["name"]) > 0


def test_canonical_snapshot_player_id_per_unit():
    """Each unit record includes owner player_id."""
    from backend.engine.ai.autoplay import _snapshot_state

    state = make_test_game_state()
    snap = _snapshot_state(state)

    for pid in ("1", "2"):
        for unit in snap["units"][pid]:
            assert unit["player_id"] == pid


def test_canonical_snapshot_mirrored_names_distinct_ids():
    """Same display name across players → distinct runtime IDs in snapshot."""
    from backend.engine.ai.autoplay import _snapshot_state
    from backend.state.game_state import UnitState

    state = make_test_game_state()
    # Force same display name for both players
    state.players["1"].units = {
        "p1:Boyz:0": UnitState(
            unit_id="p1:Boyz:0",
            name="Boyz",
            faction="orks",
            position=(0, 0),
            current_wounds=2,
            max_wounds=2,
            models_remaining=1,
            models_total=1,
            leadership=7,
            objective_control=2,
        )
    }
    state.players["2"].units = {
        "p2:Boyz:0": UnitState(
            unit_id="p2:Boyz:0",
            name="Boyz",
            faction="orks",
            position=(10, 10),
            current_wounds=2,
            max_wounds=2,
            models_remaining=1,
            models_total=1,
            leadership=7,
            objective_control=2,
        )
    }

    snap = _snapshot_state(state)
    ids = {u["id"] for pid in snap["units"] for u in snap["units"][pid]}
    assert ids == {"p1:Boyz:0", "p2:Boyz:0"}
    # Display names identical but IDs distinct
    names = {u["name"] for pid in snap["units"] for u in snap["units"][pid]}
    assert names == {"Boyz"}


def test_canonical_snapshot_vp_consistency():
    """VP fields use same names and nesting in all snapshots."""
    from backend.engine.ai.autoplay import _snapshot_state

    state = make_test_game_state()
    state.players["1"].victory_points = 15
    state.players["2"].victory_points = 10

    snap = _snapshot_state(state)
    assert snap["victory_points"]["1"] == 15
    assert snap["victory_points"]["2"] == 10
    # VP is at top level only, not embedded per-unit
    for pid in ("1", "2"):
        for unit in snap["units"][pid]:
            assert "victory_points" not in unit


def test_canonical_snapshot_status_flags():
    """Snapshot includes wounds, models, and status flags."""
    from backend.engine.ai.autoplay import _snapshot_state

    state = make_test_game_state()
    snap = _snapshot_state(state)

    u = snap["units"]["1"][0]
    assert "current_wounds" in u
    assert "max_wounds" in u
    assert "models_remaining" in u
    assert "models_total" in u
    assert "is_alive" in u
    assert "is_engaged" in u
    assert "is_battle_shocked" in u


def test_recorder_many_event_types():
    """Test: all event type recording methods work."""
    recorder = ReplayRecorder("multi-test", {}, "mission", "deploy", 42)
    recorder.start_game()
    gs = make_test_game_state()
    recorder.start_round(1, gs)

    actor = make_test_unit_state("Actor", "actor-1")
    target = make_test_unit_state("Target", "target-1")

    recorder.record_shoot(1, "shooting", 1, actor, target, "Gun", 1.0)
    recorder.record_charge(1, "charge", 1, actor, target, 9, True)
    recorder.record_kill(1, "shooting", 1, actor, target)
    recorder.record_move(1, "movement", 1, actor, (10, 20), (15, 22))
    recorder.record_damage(1, "shooting", 1, actor, target, 2.0)
    recorder.record_cp_spend(1, "command", 1, actor.unit_id, actor.name, 1)

    recorder.end_round(gs)

    events = recorder.replay.rounds[0].events
    assert len(events) == 6
    assert [e.event_type for e in events] == [
        "shoot",
        "charge",
        "kill",
        "move",
        "damage",
        "cp_spend",
    ]


def test_recorder_no_events():
    """Test: empty round without events does not crash."""
    recorder = ReplayRecorder("empty", {}, "mission", "deploy", 42)
    recorder.start_game()
    recorder.start_round(1, make_test_game_state())
    recorder.end_round(make_test_game_state())

    assert len(recorder.replay.rounds) == 1
    assert len(recorder.replay.rounds[0].events) == 0
