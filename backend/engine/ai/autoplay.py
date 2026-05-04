"""
F3.5 — Auto-play: AI vs AI Full Scenario.

Размещает юниты, запускает полную симуляцию AI vs AI,
сбор логов и возврат результата.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any

from backend.engine.ai.deployment import DeploymentType, DeploymentZone, place_units
from backend.engine.ai.decision import DecisionEngine
from backend.state.game_state import GameState, RosterState
from backend.engine.scenario import Scenario
from backend.state.mission import Mission
from backend.state.map import BattlefieldMap


class AutoPlayError(Exception):
    """Базовое исключение AutoPlay."""


class InvalidRosterError(AutoPlayError):
    """Ростер не прошёл валидацию."""


class TimeoutError(AutoPlayError):
    """Симуляция превысила лимит времени."""


@dataclass
class AutoPlayConfig:
    """Конфигурация симуляции."""
    max_rounds: int = 5
    deployment_type: DeploymentType = DeploymentType.STANDARD
    seed: int = 42
    time_limit_seconds: int = 30
    use_sticky_objectives: bool = True
    enable_stratagems: bool = True
    log_all_events: bool = True


@dataclass
class AutoPlayResult:
    """Результат полной симуляции."""
    game_state: GameState
    round_logs: List[Dict[str, Any]]
    placements: Dict[int, List[Any]]  # player → [Placement]
    error: Optional[str] = None
    total_duration_ms: float = 0.0
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Сериализация результата для JSON."""
        return {
            "rounds": len(self.round_logs),
            "victory_points": dict(self.game_state.players[1].victory_points, **self.game_state.players[2].victory_points) if hasattr(self.game_state, 'players') else {},
            "winner": self._determine_winner(),
            "summary": self.summary,
            "error": self.error,
            "duration_ms": self.total_duration_ms,
        }

    def _determine_winner(self) -> Optional[int]:
        """Определить победителя по очкам победы."""
        if not hasattr(self.game_state, 'players') or len(self.game_state.players) < 2:
            return None
        
        vp_1 = self.game_state.players.get("1", {}).victory_points if "1" in self.game_state.players else 0
        vp_2 = self.game_state.players.get("2", {}).victory_points if "2" in self.game_state.players else 0
        
        if vp_1 > vp_2:
            return 1
        elif vp_2 > vp_1:
            return 2
        return None  # ничья


def resolve_ai_for_faction(faction: str) -> object:
    """
    Вернуть AI класс для фракции.
    
    Registry расширяемый: при добавлении новой фракции
    нужно зарегистрировать AI класс здесь.
    
    Orks → OrkAI
    T'au → TauAI
    default → DecisionEngine (generic greedy)
    """
    # Для простоты пока используем только DecisionEngine
    # В будущем здесь можно добавить специфичные AI для фракций
    return DecisionEngine()


def _validate_rosters(roster_a: RosterState, roster_b: RosterState) -> List[str]:
    """Валидация ростеров перед симуляцией."""
    errors = []
    
    # Проверка PTS лимитов (примерно 2000 PTS стандартный лимит)
    max_pts = 2000
    if hasattr(roster_a, 'total_pts') and roster_a.total_pts > max_pts:
        errors.append(f"Roster A exceeds {max_pts} PTS: {roster_a.total_pts}")
    if hasattr(roster_b, 'total_pts') and roster_b.total_pts > max_pts:
        errors.append(f"Roster B exceeds {max_pts} PTS: {roster_b.total_pts}")
        
    # Проверка наличия_units
    if hasattr(roster_a, 'units') and len(roster_a.units) == 0:
        errors.append("Roster A has no units")
    if hasattr(roster_b, 'units') and len(roster_b.units) == 0:
        errors.append("Roster B has no units")
        
    return errors


def _create_default_map(seed: int = 42) -> BattlefieldMap:
    """Создать стандартную карту для симуляции."""
    # Импортируем здесь чтобы избежать циклических зависимостей
    from backend.state.map import BattlefieldMap, TerrainType
    import numpy as np
    
    # Устанавливаем seed для воспроизводимости
    np.random.seed(seed)
    
    # Стандартная карта 60x44
    game_map = BattlefieldMap(width=60, height=44)
    
    # Добавляем немного простого terrains для разнообразия
    # В реальной реализации здесь была бы более сложная генерация карты
    return game_map


def _find_unit_in_roster(roster: RosterState, unit_id: str) -> Optional[Any]:
    """Найти юнит в ростере по ID."""
    if hasattr(roster, 'units'):
        return roster.units.get(unit_id)
    return None


def _check_game_end(state: GameState, mission: Mission) -> bool:
    """Проверить условия окончания игры."""
    # Простая проверка: если у одного из игроков нет юнитов
    if hasattr(state, 'players'):
        players_alive = 0
        for player in state.players.values():
            if hasattr(player, 'units'):
                alive_units = [u for u in player.units.values() if getattr(u, 'is_alive', True)]
                if len(alive_units) > 0:
                    players_alive += 1
        
        if players_alive < 2:
            return True
            
    # Проверка по максимальному количеству раундов
    if hasattr(state, 'current_round') and hasattr(state, 'max_rounds'):
        if state.current_round >= state.max_rounds:
            return True
            
    return False


def _build_summary(state: GameState, round_logs: List[Dict[str, Any]], 
                  placements: Dict[int, List[Any]]) -> Dict[str, Any]:
    """Построить сводку симуляции."""
    total_kills = {1: 0, 2: 0}
    total_damage = {1: 0, 2: 0}
    charge_count = {1: 0, 2: 0}
    
    # Извлекаем информацию из логов раундов
    for log in round_logs:
        # Предполагаем структуру лога в зависимости от реализации
        if isinstance(log, dict) and 'events' in log:
            for event in log['events']:
                player = event.get('player', 0)
                if event.get('type') == 'kill':
                    total_kills[player] = total_kills.get(player, 0) + 1
                if event.get('damage', 0) > 0:
                    total_damage[player] = total_damage.get(player, 0) + event['damage']
                if event.get('action') == 'charge':
                    charge_count[player] = charge_count.get(player, 0) + 1
    
    # Информация об армиях
    army_a_info = {"faction": "unknown", "pts": 0}
    army_b_info = {"faction": "unknown", "pts": 0}
    
    if hasattr(state, 'roster_a') and hasattr(state.roster_a, 'faction'):
        army_a_info["faction"] = state.roster_a.faction
        army_a_info["pts"] = getattr(state.roster_a, 'total_pts', 0)
    if hasattr(state, 'roster_b') and hasattr(state.roster_b, 'faction'):
        army_b_info["faction"] = state.roster_b.faction
        army_b_info["pts"] = getattr(state.roster_b, 'total_pts', 0)
    
    return {
        "victory_points": {
            "1": getattr(state.players.get("1", type('obj', (), {'victory_points': 0}))(), 'victory_points', 0) if hasattr(state, 'players') else 0,
            "2": getattr(state.players.get("2", type('obj', (), {'victory_points': 0}))(), 'victory_points', 0) if hasattr(state, 'players') else 0,
        },
        "winner": None,  # Будет заполнено в to_dict()
        "total_kills": total_kills,
        "total_damage": total_damage,
        "charge_count": charge_count,
        "rounds_played": len(round_logs),
        "army_a": army_a_info,
        "army_b": army_b_info,
    }


def run_auto_game(roster_a: RosterState,
                  roster_b: RosterState,
                  mission: Mission,
                  config: AutoPlayConfig = None) -> AutoPlayResult:
    """
    Запустить полную AI vs AI симуляцию.
    
    Flow:
    1. Валидация ростеров
    2. Создание GameState
    3. Deploy юнитов на карту
    4. Создание AI инстансов
    5. Запуск game loop (run_round × max_rounds)
    6. Сбор логов и summary
    7. Возврат результата
    """
    import time
    start = time.time()
    config = config or AutoPlayConfig()
    
    # 1. Validate
    errors = _validate_rosters(roster_a, roster_b)
    if errors:
        return AutoPlayResult(
            game_state=None, 
            round_logs=[],
            placements={},
            error=f"Roster validation failed: {'; '.join(errors)}",
        )
    
    # 2. Create game state
    try:
        game_map = _create_default_map(seed=config.seed)
        
        # Создаем базовое GameState
        state = GameState(
            roster_a=roster_a,
            roster_b=roster_b,
            seed=config.seed,
            mission=mission.name if hasattr(mission, 'name') else str(mission),
            map_width=game_map.width,
            map_height=game_map.height,
        )
        state.map = game_map  # Привязываем карту к состоянию
        
        # 3. Deploy
        deployments = {}
        unit_models = {}  # В реальной реализации здесь были бы модели единиц из wiki
        
        for player, roster in [(1, roster_a), (2, roster_b)]:
            placements = place_units(
                player_units=list(getattr(roster, 'units', {}).values()) if hasattr(roster, 'units') else [],
                unit_models=unit_models,
                deployment_type=config.deployment_type,
                player=player,
                map_size=(game_map.width, game_map.height),
                battlefield=game_map,
                objectives=getattr(mission, 'objectives', []),
                warlord_id=getattr(roster, 'warlord_unit_id', None) if hasattr(roster, 'warlord_unit_id') else None,
            )
            deployments[player] = placements
            
            # Обновляем позиции юнитов в ростере
            for placement in placements:
                unit = _find_unit_in_roster(roster, placement.unit_id)
                if unit and hasattr(unit, 'position'):
                    unit.position = (placement.x, placement.y)
        
        # 4. Create AIs
        ai_a = resolve_ai_for_faction(getattr(roster_a, 'faction', 'unknown'))
        ai_b = resolve_ai_for_faction(getattr(roster_b, 'faction', 'unknown'))
        
        # 5. Game loop
        round_logs = []
        scenario = Scenario(state)
        
        try:
            for r in range(config.max_rounds):
                # Time check
                elapsed = (time.time() - start) * 1000
                if elapsed > config.time_limit_seconds * 1000:
                    raise TimeoutError(
                        f"Simulation exceeded {config.time_limit_seconds}s"
                    )
                
                # Запускаем раунд через сценарий
                # В реальной реализации нужно передать AI в сценарий
                # Для простоты пока используем базовый сценарий
                scenario.run_round()
                
                # Собираем лог раунда (упрощенно)
                round_log = {
                    "round": r + 1,
                    "events": [],  # В реальности здесь были бы события боя
                    "phase_logs": getattr(state, 'game_log', [])[-10:],  # Последние записи лога
                }
                round_logs.append(round_log)
                
                # Проверяем условие окончания игры
                if _check_game_end(state, mission):
                    break
                    
                # Подготавливаемся к следующему раунду
                if not state.is_game_over:
                    # Сбрасываем флаги для следующего раунда
                    for player in getattr(state, 'players', {}).values():
                        if hasattr(player, 'units'):
                            for unit in player.units.values():
                                if hasattr(unit, 'has_shot'):
                                    unit.has_shot = False
                                if hasattr(unit, 'has_charged'):
                                    unit.has_charged = False
                                if hasattr(unit, 'is_fighting'):
                                    unit.is_fighting = False
                                if hasattr(unit, 'is_battle_shocked'):
                                    unit.is_battle_shocked = False
        
        except AutoPlayError as e:
            return AutoPlayResult(
                game_state=state, 
                round_logs=round_logs,
                placements=deployments, 
                error=str(e),
                total_duration_ms=(time.time() - start) * 1000,
            )
        
        # 6. Summary
        summary = _build_summary(state, round_logs, deployments)
        
        return AutoPlayResult(
            game_state=state, 
            round_logs=round_logs,
            placements=deployments,
            total_duration_ms=(time.time() - start) * 1000,
            summary=summary,
        )
        
    except Exception as e:
        return AutoPlayResult(
            game_state=None, 
            round_logs=[],
            placements={},
            error=f"Unexpected error during simulation: {str(e)}",
            total_duration_ms=(time.time() - start) * 1000,
        )


# TODO: Добавить API endpoint в web/routes/api.py
# POST /api/auto-play
# {
#   "roster_a_id": "uuid",
#   "roster_b_id": "uuid", 
#   "mission": "only_war",
#   "deployment": "standard",
#   "max_rounds": 5,
#   "seed": 42
# }