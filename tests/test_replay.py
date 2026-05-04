"""
Tests for F3.6 — Replay Recording: JSON Event Log per Round/Phase.
"""

import pytest
import json
import sqlite3
from datetime import datetime
from backend.engine.replay import (
    ReplayRecorder,
    ReplayEvent,
    ReplayRound,
    Replay,
    replay_to_json,
    replay_from_json,
    save_replay,
    load_replay,
    list_replays,
    TABLE_REPLAYS,
    _snapshot_state,
    _unit_snapshot,
    _pos_dict
)
from backend.state.game_state import GameState
from backend.model.unit import Unit, Weapon
from backend.state.roster import RosterState


def make_test_unit(name: str = "Test Unit", unit_id: str = "test-unit-1") -> Unit:
    """Создать простой юнит для тестов."""
    return Unit(
        name=name,
        faction="test",
        toughness=3,
        save=3,
        wounds=1,
        squad_size=1,
        weapons=[
            Weapon(
                name="Test Weapon",
                type="ranged",
                skill=3,
                strength=3,
                ap=0,
                damage_dice=(1, 6, 0),
                attacks_dice=(1, 6, 0),
                range_max=24,
                range_min=0
            )
        ],
        points=100
    )


def make_test_roster(units: list[Unit] = None, faction: str = "test") -> RosterState:
    """Создать тестовый ростер."""
    if units is None:
        units = [make_test_unit(f"Unit {i}") for i in range(2)]
    
    # Создаем простой ростер без сложной логики
    class MockRosterState:
        def __init__(self, units_list, faction_name):
            self.faction = faction_name
            self.units = {u.name: u for u in units_list}
            self.total_pts = sum(getattr(u, 'points', 100) for u in units_list)
    
    return MockRosterState(units, faction)


def make_test_game_state() -> GameState:
    """Создать тестовое состояние игры."""
    # Упрощенная версия GameState для тестов
    class MockGameState:
        def __init__(self):
            self.current_round = 1
            self.current_phase = type('obj', (), {'value': 'shooting'})()
            self.turn = 1
            self.victory_points = {"1": 0, "2": 0}
            
            # Создаем простые ростеры
            unit_a = make_test_unit("Unit A", "unit-a-1")
            unit_b = make_test_unit("Unit B", "unit-b-1")
            
            class MockPlayer:
                def __init__(self, player_id, units_dict):
                    self.player_id = player_id
                    self.units = units_dict
                    self.victory_points = 0
                    
            class MockRoster:
                def __init__(self, units_dict):
                    self.units = units_dict
                    self.faction = "test"
                    
            self.players = {
                "1": MockPlayer("1", {"unit-a-1": unit_a}),
                "2": MockPlayer("2", {"unit-b-1": unit_b})
            }
            
            self.roster_a = MockRoster({"unit-a-1": unit_a})
            self.roster_b = MockRoster({"unit-b-1": unit_b})
    
    return MockGameState()


def test_replay_event_creation():
    """Тест: создание события реплея."""
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
        position_after={"x": 10, "y": 20}
    )
    
    assert event.timestamp == 1000.0
    assert event.event_type == "shoot"
    assert actor.actor_name == "Test Unit"
    assert event.dice_rolled == [4, 5, 6]


def test_replay_round_creation():
    """Тест: создание раунда реплея."""
    round_obj = ReplayRound(
        round=1,
        start_state={"round": 1, "phase": "movement"},
        end_state={"round": 1, "phase": "shooting"},
        events=[]
    )
    
    assert round_obj.round == 1
    assert round_obj.start_state["round"] == 1
    assert len(round_obj.events) == 0


def test_replay_creation():
    """Тест: создание полного реплея."""
    replay = Replay(
        game_id="test-game-123",
        created_at="2026-01-01T12:00:00Z",
        rosters={"roster_a": {"faction": "orks"}, "roster_b": {"faction": "tau"}},
        mission="only_war",
        deployment="standard",
        seed=42,
        rounds=[],
        summary={"winner": 1}
    )
    
    assert replay.game_id == "test-game-123"
    assert replay.mission == "only_war"
    assert replay.seed == 42
    assert replay.summary["winner"] == 1


def test_replay_recorder_initialization():
    """Тест: инициализация рекордера реплея."""
    recorder = ReplayRecorder(
        game_id="test-123",
        rosters={"a": {}, "b": {}},
        mission="test_mission",
        deployment="standard",
        seed=123
    )
    
    assert recorder.replay.game_id == "test-123"
    assert recorder.replay.mission == "test_mission"
    assert recorder.replay.seed == 123
    assert len(recorder.replay.rounds) == 0
    assert recorder._start_time is None


def test_replay_recorder_start_game():
    """Тест: запуск таймера рекордера."""
    recorder = ReplayRecorder("test", {}, "mission", "deploy", 42)
    recorder.start_game()
    
    assert recorder._start_time is not None
    assert isinstance(recorder._start_time, float)


def test_replay_recorder_record_event():
    """Тест: запись события через рекордер."""
    recorder = ReplayRecorder("test-123", {}, "mission", "deploy", 42)
    recorder.start_game()
    
    # Начинаем раунд
    game_state = make_test_game_state()
    recorder.start_round(1, game_state)
    
    # Записываем событие
    actor_unit = make_test_unit("Actor", "actor-1")
    target_unit = make_test_unit("Target", "target-1")
    
    recorder.record_shoot(
        round_num=1,
        phase="shooting",
        turn=1,
        actor=actor_unit,
        target=target_unit,
        weapon_name="Test Gun",
        damage=2.5
    )
    
    assert len(recorder.replay.rounds) == 1
    assert len(recorder.replay.rounds[0].events) == 1
    
    event = recorder.replay.rounds[0].events[0]
    assert event.event_type == "shoot"
    assert event.actor_name == "Actor"
    assert event.target_name == "Target"
    assert event.weapon_name == "Test Gun"
    assert event.result_value == 2.5


def test_replay_recorder_round_lifecycle():
    """Тест: полный жизненный цикл раунда в рекордере."""
    recorder = ReplayRecorder("test-123", {}, "mission", "deploy", 42)
    recorder.start_game()
    
    game_state = make_test_game_state()
    
    # Начинаем раунд
    recorder.start_round(1, game_state)
    assert recorder._current_round is not None
    assert recorder._current_round.round == 1
    
    # Записываем событие
    actor_unit = make_test_unit("Actor", "actor-1")
    target_unit = make_test_unit("Target", "target-1")
    
    recorder.record_shoot(1, "shooting", 1, actor_unit, target_unit, "Gun", 1.0)
    
    # Завершаем раунд
    recorder.end_round(game_state)
    
    assert recorder._current_round is None
    assert len(recorder.replay.rounds) == 1
    assert len(recorder.replay.rounds[0].events) == 1
    assert "end_state" in recorder.replay.rounds[0]


def test_replay_to_json_from_json():
    """Тест: сериализация и десериализация реплея."""
    # Создаем тестовый реплей
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
                        result_value=2.0
                    )
                ]
            )
        ],
        summary={"winner": 1, "total_rounds": 1}
    )
    
    # Сериализуем в JSON
    json_str = replay_to_json(replay)
    assert isinstance(json_str, str)
    assert "json-test-123" in json_str
    assert "test_mission" in json_str
    
    # Десериализуем обратно
    restored = replay_from_json(json_str)
    
    assert restored.game_id == replay.game_id
    assert restored.mission == replay.mission
    assert restored.seed == replay.seed
    assert len(restored.rounds) == len(replay.rounds)
    assert len(restored.rounds[0].events) == 1
    assert restored.rounds[0].events[0].event_type == "shoot"
    assert restored.rounds[0].events[0].result_value == 2.0
    assert restored.summary["winner"] == 1


def test_sqlite_replay_persistence():
    """Тест: сохранение и загрузка реплея из SQLite."""
    # Используем in-memory базу для теста
    db = sqlite3.connect(":memory:")
    db.execute(TABLE_REPLAYS)
    
    # Создаем тестовый реплей
    replay = Replay(
        game_id="sqlite-test-123",
        created_at="2026-01-01T12:00:00Z",
        rostersrbitros={"a": {"faction": "orks"}, "b": {"faction": "tau"}},
        mission="only_war",
        deployment="hammer_and_anvil",
        seed=42,
        rounds=[],
        summary={"winner": 2}
    )
    
    # Сохраняем в базу
    save_replay(db, replay, user_id=1)
    
    # Загружаем из базы
    loaded = load_replay(db, "sqlite-test-123")
    
    assert loaded is not None
    assert loaded.game_id == replay.game_id
    assert loaded.mission == replay.mission
    assert loaded.deployment == replay.deployment
    assert loaded.seed == replay.seed
    assert loaded.summary["winner"] == 2


def test_sqlite_load_nonexistent_replay():
    """Тест: загрузка несуществующего реплея возвращает None."""
    db = sqlite3.connect(":memory:")
    db.execute(TABLE_REPLAYS)
    
    result = load_replay(db, "nonexistent-id")
    assert result is None


def test_sqlite_list_replays():
    """Тест: список реплеев из базы данных."""
    db = sqlite3.connect(":memory:")
    db.execute(TABLE_REPLAYS)
    
    # Сохраняем несколько реплеев
    replay1 = Replay(
        game_id="replay-1",
        created_at="2026-01-01T12:00:00Z",
        rosters={"a": {}, "b": {}},
        mission="mission1",
        deployment="std",
        seed=1,
        rounds=[],
        summary={"winner": 1}
    )
    
    replay2 = Replay(
        game_id="replay-2",
        created_at="2026-01-02T12:00:00Z",
        rosters={"a": {}, "b": {}},
        mission="mission2",
        deployment="std",
        seed=2,
        rounds=[],
        summary={"winner": 2}
    )
    
    save_replay(db, replay1, user_id=1)
    save_replay(db, replay2, user_id=1)
    
    # Список реплеев для пользователя
    replays = list_replays(db, user_id=1)
    assert len(replays) == 2
    
    # Проверяем порядок (сначала новые)
    assert replays[0]["game_id"] == "replay-2"  # Новый сначала
    assert replays[1]["game_id"] == "replay-1"  # Старый потом
    
    # Список всех реплеев (без фильтра по пользователю)
    all_replays = list_replays(db)
    assert len(all_replays) == 2


def test_empty_replay_roundtrip():
    """Тест: реплей без событий сохраняется и загружается корректно."""
    replay = Replay(
        game_id="empty-replay",
        created_at="2026-01-01T12:00:00Z",
        rosters={"a": {}, "b": {}},
        mission="",
        deployment="",
        seed=0,
        rounds=[],
        summary={}
    )
    
    json_str = replay_to_json(replay)
    restored = replay_from_json(json_str)
    
    assert restored.game_id == replay.game_id
    assert len(restored.rounds) == 0
    assert restored.summary == {}


def test_recorder_timestamp_ordering():
    """Тест: события имеют возрастающие timestamp'ы."""
    recorder = ReplayRecorder("test-ts", {}, "mission", "deploy", 42)
    recorder.start_game()
    
    game_state = make_test_game_state()
    recorder.start_round(1, game_state)
    
    # Записываем несколько событий с небольшой паузой
    actor = make_test_unit("Actor", "actor-1")
    target = make_test_unit("Target", "target-1")
    
    recorder.record_shoot(1, "shooting", 1, actor, target, "Gun1", 1.0)
    recorder.record_shoot(1, "shooting", 1, actor, target, "Gun2", 2.0)
    recorder.record_shoot(1, "shooting", 1, actor, target, "Gun3", 3.0)
    
    events = recorder.replay.rounds[0].events
    timestamps = [e.timestamp for e in events]
    
    # Проверяем, что timestamp'ы не убывают (允许相等 из-за быстрого выполнения)
    for i in range(len(timestamps) - 1):
        assert timestamps[i] <= timestamps[i + 1]


def test_helper_functions():
    """Тест: вспомогательные функции."""
    # Тест _pos_dict
    class MockPos:
        def __init__(self, x, y):
            self.x = x
            self.y = y
    
    pos = MockPos(10, 20)
    result = _pos_dict(pos)
    assert result == {"x": 10, "y": 20}
    
    # Тест с None-подобным объектом
    class BadPos:
        pass
    
    bad_pos = BadPos()
    result = _pos_dict(bad_pos)
    assert result == {"x": 0, "y": 0}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])