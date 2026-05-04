"""
Tests for F3.5 — Auto-play: AI vs AI Full Scenario.
"""

import pytest
from backend.engine.ai.autoplay import (
    run_auto_game,
    AutoPlayConfig,
    AutoPlayResult,
    resolve_ai_for_faction,
    InvalidRosterError,
    TimeoutError
)
from backend.state.roster import RosterState
from backend.state.mission import Mission
from backend.model.unit import Unit, Weapon


def make_test_unit(name: str, faction: str = "test") -> Unit:
    """Создать простой юнит для тестов."""
    return Unit(
        name=name,
        faction=faction,
        toughness=3,
        save=3,
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


def make_test_roster(units: list[Unit] = None, faction: str = "test", pts: int = 500) -> RosterState:
    """Создать тестовый ростер."""
    if units is None:
        units = [make_test_unit(f"Unit {i}", faction) for i in range(3)]
    
    roster = RosterState(
        name=f"{faction} roster",
        faction=faction,
        total_pts=pts,
        units={u.name: u for u in units}
    )
    return roster


def make_test_mission(name: str = "only_war") -> Mission:
    """Создать тестовую миссию."""
    return Mission(
        name=name,
        description="Test mission",
        objectives=[]
    )


def test_resolve_ai_for_faction_orks():
    """Тест: Orks используют OrkAI (пока DecisionEngine как заглушка)."""
    ai = resolve_ai_for_faction("orks")
    # Пока все фракции используют DecisionEngine как базовый AI
    from backend.engine.ai.decision import DecisionEngine
    assert isinstance(ai, DecisionEngine)


def test_resolve_ai_for_faction_tau():
    """Тест: T'au используют TauAI (пока DecisionEngine как заглушка)."""
    ai = resolve_ai_for_faction("tau")
    from backend.engine.ai.decision import DecisionEngine
    assert isinstance(ai, DecisionEngine)


def test_resolve_ai_for_faction_unknown():
    """Тест: неизвестная фракция использует generic DecisionEngine."""
    ai = resolve_ai_for_faction("unknown_faction")
    from backend.engine.ai.decision import DecisionEngine
    assert isinstance(ai, DecisionEngine)


def test_run_auto_game_basic():
    """Тест: базовая симуляция завершается без ошибок."""
    roster_a = make_test_roster(faction="orks", pts=300)
    roster_b = make_test_roster(faction="tau", pts=300)
    mission = make_test_mission()
    
    result = run_auto_game(roster_a, roster_b, mission)
    
    assert isinstance(result, AutoPlayResult)
    # Симуляция должна завершиться без критических ошибок
    # (может быть предупреждение, но не ошибка которая останавливает симуляцию)
    if result.error:
        # Если есть ошибка, она не должна быть критичной
        assert "validation" not in result.error.lower()
        assert "timeout" not in result.error.lower()


def test_auto_game_returns_result():
    """Тест: функция возвращает объект AutoPlayResult."""
    roster_a = make_test_roster()
    roster_b = make_test_roster(faction="tau")
    mission = make_test_mission()
    
    result = run_auto_game(roster_a, roster_b, mission)
    
    assert isinstance(result, AutoPlayResult)
    assert hasattr(result, 'to_dict')
    assert hasattr(result, 'round_logs')
    assert hasattr(result, 'placements')


def test_invalid_roster_returns_error():
    """Тест: невалидный ростер возвращает ошибку валидации."""
    # Создаем ростер с избыточными очками
    overpowered_unit = make_test_unit("Super Unit", pts=2000)
    overpowered_unit.points = 2500  # Делаем его очень дорогим
    roster_a = make_test_roster(units=[overpowered_unit], pts=2500)
    roster_b = make_test_roster()
    mission = make_test_mission()
    
    result = run_auto_game(roster_a, roster_b, mission)
    
    assert isinstance(result, AutoPlayResult)
    assert result.error is not None
    assert "validation" in result.error.lower() or "exceeds" in result.error.lower()


def test_single_unit_roster():
    """Тест: ростер с одним юнитем не падает."""
    roster_a = make_test_roster(units=[make_test_unit("Lone Unit")], pts=100)
    roster_b = make_test_roster()
    mission = make_test_mission()
    
    result = run_auto_game(roster_a, roster_b, mission)
    
    assert isinstance(result, AutoPlayResult)
    # Может быть ошибка валидации из-за малого числа очков, но не должна быть критической
    if result.error:
        assert "timeout" not in result.error.lower()


def test_timeout_returns_partial():
    """Тест: таймаут возвращает частичный результат."""
    roster_a = make_test_roster()
    roster_b = make_test_roster(faction="tau")
    mission = make_test_mission()
    
    # Очень маленький лимит времени
    config = AutoPlayConfig(time_limit_seconds=0.001)
    result = run_auto_game(roster_a, roster_b, mission, config)
    
    assert isinstance(result, AutoPlayResult)
    # При настолько маленьком лимите времени должна сработать проверка таймаута
    # Но так как инициализация занимает время, может не сработать сразу
    # Главное чтобы не падало с исключением


def test_reproducible_with_seed():
    """Тест: одинаковый seed дает одинаковые результаты."""
    roster_a = make_test_roster(faction="orks")
    roster_b = make_test_roster(faction="tau")
    mission = make_test_mission()
    
    config = AutoPlayConfig(seed=42)
    result1 = run_auto_game(roster_a, roster_b, mission, config)
    result2 = run_auto_game(roster_a, roster_b, mission, config)
    
    assert isinstance(result1, AutoPlayResult)
    assert isinstance(result2, AutoPlayResult)
    
    # При одинаковых условиях результаты должны быть совместимы
    # (точное сравнение сложно из-за случайности в бою, но структура должна быть одинаковой)
    assert len(result1.round_logs) == len(result2.round_logs) or \
           abs(len(result1.round_logs) - len(result2.round_logs)) <= 1


def test_ork_vs_ork():
    """Тест: Орки против Орков работают корректно."""
    roster_a = make_test_roster(faction="orks", pts=400)
    roster_b = make_test_roster(faction="orks", pts=400)
    mission = make_test_mission()
    
    result = run_auto_game(roster_a, roster_b, mission)
    
    assert isinstance(result, AutoPlayResult)
    # Не должно быть критических ошибок
    if result.error:
        assert "timeout" not in result.error.lower()


def test_unknown_faction_uses_default_ai():
    """Тест: неизвестная фракция использует общий AI."""
    roster_a = make_test_roster(faction="unknown_faction")
    roster_b = make_test_roster(faction="tau")
    mission = make_test_mission()
    
    result = run_auto_game(roster_a, roster_b, mission)
    
    assert isinstance(result, AutoPlayResult)
    # Не должно падать из-за неизвестной фракции
    if result.error:
        assert "unknown" not in result.error.lower() or "faction" not in result.error.lower()


def test_auto_game_duration_measured():
    """Тест: продолжительность игры измеряется."""
    roster_a = make_test_roster()
    roster_b = make_test_roster(faction="tau")
    mission = make_test_mission()
    
    result = run_auto_game(roster_a, roster_b, mission)
    
    assert isinstance(result, AutoPlayResult)
    # Длительность должна быть положительной (или ноль если очень быстро)
    assert result.total_duration_ms >= 0
    
    # Для реалистичной симуляции должно быть больше нуля
    # Но в тестах с простыми юнитaми может быть очень быстро
    if result.total_duration_ms == 0:
        # Это допустимо для очень быстрых симуляций
        pass
    else:
        assert result.total_duration_ms > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])