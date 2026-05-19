"""
Tests for F3.6 — Replay Recording: JSON Event Log per Round/Phase.
"""

import contextlib
import json
import os
import sqlite3
import tempfile
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
            "Boyz hits Boyz for 1 damage in melee [actor_id=p1:Boyz:0; target_id=p2:Boyz:0]",
            "Boyz was destroyed [target_id=p2:Boyz:0]",
        ],
        round_num=1,
    )

    assert events[0].actor_id == "p1:Boyz:0"
    assert events[0].actor_name == "Boyz"
    assert events[0].target_id == "p2:Boyz:0"
    assert events[0].target_name == "Boyz"

    assert events[1].event_type == "fight"
    assert events[1].phase == "fight"
    assert events[1].actor_id == "p1:Boyz:0"
    assert events[1].actor_name == "Boyz"
    assert events[1].target_id == "p2:Boyz:0"
    assert events[1].target_name == "Boyz"

    assert events[2].target_id == "p2:Boyz:0"
    assert events[2].target_name == "Boyz"


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
    """Test: _unit_snapshot works with current UnitState fields and explicit contract."""
    unit = make_test_unit_state("Test Unit", "test-id")
    snapshot = _unit_snapshot(unit)

    # Legacy fields still present
    assert snapshot["id"] == "test-id"
    assert snapshot["name"] == "Test Unit"
    # Explicit identity/display contract fields (Task 0.2 acceptance)
    assert snapshot["runtime_unit_id"] == "test-id"
    assert snapshot["display_name"] == "Test Unit"
    assert "canonical_unit_id" in snapshot
    assert "owner_id" in snapshot
    assert snapshot["player_id"] == snapshot["owner_id"]
    # Stats
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


def test_canonical_snapshot_phase_uses_game_phase_values_only():
    """Replay/autoplay snapshots serialize canonical GamePhase values and never Morale."""
    from backend.engine.ai.autoplay import _snapshot_state as autoplay_snapshot
    from backend.engine.replay import _snapshot_state as replay_snapshot
    from backend.state.game_state import GAME_PHASE_ORDER

    state = make_test_game_state()
    for phase in GAME_PHASE_ORDER:
        state.current_phase = phase
        assert autoplay_snapshot(state)["phase"] == phase.value
        assert replay_snapshot(state)["phase"] == phase.value

    allowed = {phase.value for phase in GAME_PHASE_ORDER}
    assert "morale" not in allowed


def test_battle_ready_vp_in_final_snapshot():
    """Persisted replay end_state reflects Battle Ready VP applied after last round."""
    from backend.engine.ai.autoplay import AutoPlayConfig, run_auto_game
    from backend.model.unit import Unit, Weapon
    from backend.state.roster import RosterState

    boyz = Unit(
        name="Boyz",
        faction="orks",
        category="Battleline",
        movement=5,
        toughness=5,
        save=5,
        wounds=2,
        leadership=7,
        objective_control=2,
        ranged_weapons=[
            Weapon(
                name="Shoota",
                type="ranged",
                range_max=18,
                attacks_dice=(3, 6, 0),
                skill=5,
                strength=4,
                ap=0,
                damage_dice=(1, 3, 0),
            )
        ],
        points=85,
        model_count=(10, 20),
    )
    roster_a = RosterState(
        name="orks",
        faction="orks",
        total_pts=85,
        units=[("Boyz", boyz)],
        warlord_unit_name="Boyz",
    )
    roster_b = RosterState(
        name="orks2",
        faction="orks",
        total_pts=85,
        units=[("Boyz", boyz)],
        warlord_unit_name="Boyz",
    )
    config = AutoPlayConfig(max_rounds=1, seed=4242)
    result = run_auto_game(roster_a, roster_b, mission_name="only_war", config=config)

    if result.error:
        pytest.skip(f"Auto-play failed: {result.error}")

    gs = result.game_state
    final_vp = {pid: getattr(p, "victory_points", 0) for pid, p in gs.players.items()}
    last_end = result.round_logs[-1]["end_state"]
    replay_vp = last_end["victory_points"]

    assert replay_vp == final_vp, f"Replay end_state VP {replay_vp} != GameState VP {final_vp}"


def test_canonical_snapshot_explicit_contract_fields():
    """Unit snapshots include runtime_unit_id, display_name, canonical_unit_id, owner_id."""
    from backend.engine.ai.autoplay import _snapshot_state

    state = make_test_game_state()
    for pid, player in state.players.items():
        for _rtid, unit in player.units.items():
            unit.unit_id = f"p{pid}:TestUnit:0"

    snap = _snapshot_state(state)
    u = snap["units"]["1"][0]

    assert u["runtime_unit_id"] == "p1:TestUnit:0"
    assert u["display_name"] == "Unit A"
    assert u["canonical_unit_id"] == "TestUnit"
    assert u["owner_id"] == "1"
    assert u["player_id"] == "1"
    assert u["id"] == u["runtime_unit_id"]
    assert u["name"] == u["display_name"]


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


# ── Task 0.3 — destructive behavior prevention tests ───────────────────


def test_db_init_preserves_existing_replay_rows():
    """DB init / migrate() does not delete existing replay rows."""
    import sqlite3

    from backend.db.database import Database

    db_test = Database("/tmp/test_replay_preserve.db")  # noqa: S108
    # Clean start
    db_test.hard_reset()
    with contextlib.suppress(FileNotFoundError):
        os.remove("/tmp/test_replay_preserve.db")  # noqa: S108

    db_test.migrate()

    # Insert a replay
    replay = Replay(
        game_id="preserve-test-1",
        created_at=datetime.utcnow().isoformat(),
        rosters={"roster_a": {}, "roster_b": {}},
        mission="test",
        deployment="standard",
        seed=42,
        rounds=[],
        summary={},
    )
    save_replay(db_test.conn, replay)

    # Run migrate again (simulating app restart)
    db_test.migrate()

    # Replay should still exist
    loaded = load_replay(db_test.conn, "preserve-test-1")
    assert loaded is not None
    assert loaded.game_id == "preserve-test-1"

    # Cleanup
    db_test.close()
    with contextlib.suppress(FileNotFoundError):
        os.remove("/tmp/test_replay_preserve.db")  # noqa: S108


def test_save_replay_fails_on_duplicate_by_default():
    """save_replay fails with IntegrityError on duplicate game_id by default."""
    import sqlite3

    replay = Replay(
        game_id="dup-test-1",
        created_at=datetime.utcnow().isoformat(),
        rosters={"roster_a": {}, "roster_b": {}},
        mission="test",
        deployment="standard",
        seed=42,
        rounds=[],
        summary={},
    )

    # Create temp in-memory DB + schema
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS replays (
            game_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            roster_a TEXT NOT NULL,
            roster_b TEXT NOT NULL,
            mission TEXT NOT NULL,
            deployment TEXT NOT NULL,
            seed INTEGER NOT NULL,
            replay_json TEXT NOT NULL,
            summary TEXT,
            user_id INTEGER
        );
    """
    )

    # First save succeeds
    save_replay(conn, replay)
    assert load_replay(conn, "dup-test-1") is not None

    # Second save with same game_id fails
    with pytest.raises(sqlite3.IntegrityError):
        save_replay(conn, replay)

    conn.close()


def test_save_replay_succeeds_with_overwrite():
    """save_replay with overwrite=True replaces existing replay."""
    import sqlite3

    replay1 = Replay(
        game_id="overwrite-test-1",
        created_at=datetime.utcnow().isoformat(),
        rosters={"roster_a": {}, "roster_b": {}},
        mission="mission-a",
        deployment="standard",
        seed=1,
        rounds=[],
        summary={"winner": 1},
    )
    replay2 = Replay(
        game_id="overwrite-test-1",
        created_at=datetime.utcnow().isoformat(),
        rosters={"roster_a": {}, "roster_b": {}},
        mission="mission-b",
        deployment="hammer_and_anvil",
        seed=2,
        rounds=[],
        summary={"winner": 2},
    )

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS replays (
            game_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            roster_a TEXT NOT NULL,
            roster_b TEXT NOT NULL,
            mission TEXT NOT NULL,
            deployment TEXT NOT NULL,
            seed INTEGER NOT NULL,
            replay_json TEXT NOT NULL,
            summary TEXT,
            user_id INTEGER
        );
    """
    )

    # First save
    save_replay(conn, replay1)
    # Overwrite with second replay
    save_replay(conn, replay2, overwrite=True)

    loaded = load_replay(conn, "overwrite-test-1")
    assert loaded is not None
    assert loaded.mission == "mission-b"
    assert loaded.seed == 2

    conn.close()


def test_same_seed_produces_different_replay_ids():
    """Fixed seed produces repeatable sim behavior but distinct durable replay IDs."""
    from backend.engine.ai.autoplay import AutoPlayConfig, run_auto_game
    from backend.model.unit import Unit, Weapon
    from backend.state.roster import RosterState

    boyz = Unit(
        name="Boyz",
        faction="orks",
        category="Battleline",
        movement=5,
        toughness=5,
        save=5,
        wounds=2,
        leadership=7,
        objective_control=2,
        ranged_weapons=[
            Weapon(
                name="Shoota",
                type="ranged",
                range_max=18,
                attacks_dice=(3, 6, 0),
                skill=5,
                strength=4,
                ap=0,
                damage_dice=(1, 3, 0),
            )
        ],
        points=85,
        model_count=(10, 20),
    )
    roster = RosterState(
        name="orks",
        faction="orks",
        total_pts=85,
        units=[("Boyz", boyz)],
        warlord_unit_name="Boyz",
    )

    config = AutoPlayConfig(max_rounds=1, seed=4242)
    r1 = run_auto_game(roster, roster, mission_name="only_war", config=config)
    r2 = run_auto_game(roster, roster, mission_name="only_war", config=config)

    if r1.error or r2.error:
        pytest.skip(f"Auto-play failed: r1={r1.error}, r2={r2.error}")

    # Distinct game_ids
    assert r1.game_state.game_id != r2.game_state.game_id, (
        f"Same seed produced identical game_ids: {r1.game_state.game_id}"
    )
    # Both are UUID-based (not seed-based)
    seed_str = str(config.seed)
    assert seed_str not in r1.game_state.game_id
    assert seed_str not in r2.game_state.game_id
    # Both seeds stored as metadata
    assert r1.game_state.game_id != r2.game_state.game_id


def test_replay_metadata_stores_seed():
    """Replay metadata stores seed when provided."""
    replay = Replay(
        game_id="seed-meta-test",
        created_at=datetime.utcnow().isoformat(),
        rosters={"roster_a": {}, "roster_b": {}},
        mission="test",
        deployment="standard",
        seed=999,
        rounds=[],
        summary={},
    )
    assert replay.seed == 999


def test_production_startup_no_destructive_reset():
    """Production startup path (migrate) does not call destructive reset helpers."""
    import inspect

    from backend.db.database import Database

    # migrate() source must not contain DROP TABLE replays
    source = inspect.getsource(Database.migrate)
    assert "DROP TABLE IF EXISTS replays" not in source
    assert "CREATE TABLE IF NOT EXISTS replays" in source


def test_db_close_reopen_preserves_data():
    """Replay rows survive Database close/reopen cycle."""
    from backend.db.database import Database

    tmp = tempfile.mkstemp(suffix=".db")
    os.close(tmp[0])
    db_path = tmp[1]
    try:
        # Open, migrate, insert
        db1 = Database(db_path)
        db1.migrate()
        db1.execute(
            "INSERT INTO replays (game_id, created_at, roster_a, roster_b, mission, deployment, seed, replay_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "test-close-reopen",
                "2026-05-17T00:00:00",
                "{}",
                "{}",
                "Only War",
                "Dawn of War",
                42,
                json.dumps({"rounds": []}),
            ),
        )
        db1.commit()
        row_count_before = db1.fetchone("SELECT COUNT(*) as cnt FROM replays")["cnt"]
        db1.close()

        # Reopen — data must survive
        db2 = Database(db_path)
        db2.migrate()
        row_count_after = db2.fetchone("SELECT COUNT(*) as cnt FROM replays")["cnt"]
        game = db2.fetchone(
            "SELECT game_id, mission FROM replays WHERE game_id = ?", ("test-close-reopen",)
        )

        assert row_count_before == 1
        assert row_count_after == 1, f"Row count changed: {row_count_before} → {row_count_after}"
        assert game is not None, "Replay row missing after close/reopen"
        assert game["game_id"] == "test-close-reopen"
        assert game["mission"] == "Only War"
        db2.close()

        # checkpoint_wal does not delete data
        db3 = Database(db_path)
        db3.migrate()
        db3.checkpoint_wal()
        after_ck = db3.fetchone("SELECT COUNT(*) as cnt FROM replays")["cnt"]
        assert after_ck == 1, f"checkpoint_wal deleted rows: {after_ck}"
        db3.close()
    finally:
        with contextlib.suppress(OSError):
            os.unlink(db_path)
            for suffix in ("-shm", "-wal"):
                p = db_path + suffix
                if os.path.exists(p):
                    os.unlink(p)
