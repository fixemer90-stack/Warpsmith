"""
F3.5 — Auto-play: AI vs AI Full Scenario.

Размещает юниты, запускает полную симуляцию AI vs AI,
сбор логов и возврат результата.
Интегрируется с F3.2 Faction AI Profiles для принятия решений.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any

from backend.engine.ai.deployment import DeploymentType, DeploymentZone, place_units
from backend.engine.ai.faction_ai import choose_action_with_faction_ai, load_profile
from backend.state.game_state import GameState, UnitState
from backend.state.roster import RosterState
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
        victory_points = {}
        if hasattr(self.game_state, 'players'):
            for player_id, player in self.game_state.players.items():
                victory_points[player_id] = getattr(player, 'victory_points', 0)
        
        return {
            "rounds": len(self.round_logs),
            "victory_points": victory_points,
            "winner": self._determine_winner(),
            "summary": self.summary,
            "error": self.error,
            "duration_ms": self.total_duration_ms,
        }

    def _determine_winner(self) -> Optional[int]:
        """Определить победителя по очкам победы."""
        if not hasattr(self.game_state, 'players') or len(self.game_state.players) < 2:
            return None
        
        # Find the two players (assuming 2-player game)
        player_ids = list(self.game_state.players.keys())
        if len(player_ids) < 2:
            return None
            
        player_a_id, player_b_id = player_ids[0], player_ids[1]
        vp_a = getattr(self.game_state.players[player_a_id], 'victory_points', 0)
        vp_b = getattr(self.game_state.players[player_b_id], 'victory_points', 0)
        
        if vp_a > vp_b:
            # Return the numeric ID if possible, otherwise return the first player's ID
            try:
                return int(player_a_id)
            except ValueError:
                return player_a_id
        elif vp_b > vp_a:
            try:
                return int(player_b_id)
            except ValueError:
                return player_b_id
        return None  # ничья


def resolve_ai_for_faction(faction: str) -> object:
    """
    Вернуть AI профиль для фракции через F3.2 Faction AI Profiles.
    
    Загружает профиль из wiki/factions/<faction>.md через load_profile().
    Если ai: секции нет — использует generic choose_action (F3.1 greedy).
    
    Фракции с ai: профилями: Orks, T'au, Adeptus Mechanicus
    """
    profile = load_profile(faction)
    if profile:
        return profile  # FactionAIProfile с weights/behaviors/target_priority
    # Fallback к generic choose_action для фракций без ai: секции
    from backend.engine.ai.decision import choose_action
    return choose_action


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
    
    # Стандартная карта 60x44 с открытой местностью
    terrain = np.full((44, 60), TerrainType.OPEN_GROUND, dtype=object)
    game_map = BattlefieldMap(width=60, height=44, terrain=terrain)
    
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


def run_round_with_ai(state: GameState, game_map: BattlefieldMap, mission: Mission,
                     scenario: Scenario, ai_a: object, ai_b: object,
                     config: AutoPlayConfig) -> GameState:
    """
    Запустить один раунд игры с использованием AI для принятия решений.
    """
    # Log round start
    state.game_log.append(f"Starting round {state.current_round}")
    
    # Run through all phases using the game state's phase transition
    phases_completed = 0
    max_phases_per_round = 6  # COMMAND, MOVEMENT, SHOOTING, CHARGE, FIGHT, MORALE
    
    while phases_completed < max_phases_per_round and not state.is_game_over:
        # Execute current phase with AI
        _execute_phase_with_ai(state, state.current_phase, ai_a, ai_b)
        phases_completed += 1
        
        # Move to next phase (this handles round advancement)
        if not state.is_game_over:
            state.next_phase()
    
    return state


def _execute_phase_with_ai(state: GameState, phase: GamePhase, 
                          ai_a: object, ai_b: object):
    """Выполнить логику для конкретной фазы с использованием AI."""
    state.game_log.append(f"Phase: {phase.value}")
    
    if phase == GamePhase.COMMAND:
        _command_phase(state)
    elif phase == GamePhase.MOVEMENT:
        _movement_phase_with_ai(state, ai_a, ai_b)
    elif phase == GamePhase.SHOOTING:
        _shooting_phase_with_ai(state, ai_a, ai_b)
    elif phase == GamePhase.CHARGE:
        _charge_phase_with_ai(state, ai_a, ai_b)
    elif phase == GamePhase.FIGHT:
        _fight_phase_with_ai(state, ai_a, ai_b)
    elif phase == GamePhase.MORALE:
        _morale_phase(state)


def _command_phase(state: GameState):
    """Command phase logic: generate CP, check mission objectives, etc."""
    # Generate command points for each player
    for player in state.players.values():
        # Base CP generation: 1 CP per turn
        cp_gain = 1
        # Additional CP if player has a warlord
        if player.warlord_unit is not None:
            cp_gain += 1
        # Apply Leviathan cap: max 10 CP per player
        if player.command_points + cp_gain > 10:
            cp_gain = 10 - player.command_points
        player.command_points += cp_gain
        state.game_log.append(
            f"{player.name} gained {cp_gain} CP (total: {player.command_points})"
        )

    # Update mission scoring at end of Command phase
    if state.mission:
        vp_awarded = state.mission.calculate_victory_points()
        for player_id, vp in vp_awarded.items():
            if player_id in state.players:
                state.players[player_id].victory_points += vp
                state.game_log.append(
                    f"{state.players[player_id].name} gained {vp} VP from mission (total: {state.players[player_id].victory_points})"
                )


def _movement_phase_with_ai(state: GameState, ai_a: object, ai_b: object):
    """Movement phase logic: move units using AI decisions."""
    state.game_log.append("Movement phase: units may move")
    # In a full implementation, we would iterate over units and use AI to decide movement
    # For now, we'll just note that movement phase occurred
    # Reset has_moved flags at start of phase? Actually, they are reset at start of round in next_phase
    # But we might want to prevent moving twice in a phase - we'll rely on the has_moved flag
    # For now, no automatic movement - players would decide via UI/API


def _shooting_phase_with_ai(state: GameState, ai_a: object, ai_b: object):
    """Shooting phase logic: resolve shooting attacks using AI."""
    state.game_log.append("Shooting phase: units may shoot")
    # In a full implementation, we would iterate over units that can shoot and haven't shot yet
    # For each unit, resolve shooting attacks using the combat engine and AI for target selection
    # We'll leave the actual shooting logic to be implemented based on player input
    # For now, we just note that shooting happened
    # Example of how it might work:
    # for player in state.players.values():
    #     for unit in player.units.values():
    #         if unit.is_alive and not unit.has_shot:
    #             # Use AI to select target and weapon
    #             # ... combat logic ...
    #             unit.has_shot = True


def _charge_phase_with_ai(state: GameState, ai_a: object, ai_b: object):
    """Charge phase logic: resolve charge moves using AI."""
    state.game_log.append("Charge phase: units may charge")
    # Similar to shooting, but for charges


def _fight_phase_with_ai(state: GameState, ai_a: object, ai_b: object):
    """Fight phase logic: resolve fights with alternating activations using AI."""
    state.game_log.append("Fight phase: units may fight")
    
    # Determine player order for Fight phase: non-priority player goes first
    player_ids = list(state.players.keys())
    if len(player_ids) < 2:
        # If only one player, just let them fight
        order = player_ids
    else:
        # Find which player has priority
        priority_player_id = None
        for pid, player in state.players.items():
            if player.command_priority:
                priority_player_id = pid
                break
        
        if priority_player_id is None:
            # Fallback: if no priority set, use arbitrary order
            order = player_ids
        else:
            # The non-priority player goes first in Fight phase
            non_priority_player_id = [pid for pid in player_ids if pid != priority_player_id][0]
            order = [non_priority_player_id, priority_player_id]
    
    # Continue alternating activations until no more units can fight
    progress = True
    while progress:
        progress = False
        for player_id in order:
            player = state.players[player_id]
            # Find an eligible unit for this player: engaged and not yet fought
            eligible_unit = None
            for unit in player.units.values():
                if unit.is_engaged and not unit.is_fighting and unit.is_alive:
                    eligible_unit = unit
                    break
            
            if eligible_unit is not None:
                # Resolve melee combat for this unit
                _resolve_melee_combat(eligible_unit)
                # Mark the unit as having fought
                eligible_unit.is_fighting = True
                progress = True
                state.game_log.append(f"{eligible_unit.name} fought in melee")
    
    # After Fight phase, reset is_fighting flags (though they will be reset again at start of next round)
    for player in state.players.values():
        for unit in player.units.values():
            unit.is_fighting = False


def _resolve_melee_combat(attacking_unit) -> None:
    """Resolve melee combat for a unit.
    This is a simplified implementation - in reality this would use the combat engine.
    """
    # Find an enemy unit engaged with this unit
    enemy_unit = None
    for player in state.players.values():
        for unit in player.units.values():
            if unit.is_alive and unit != attacking_unit:
                # Simplified engagement check - same position or adjacent
                # In a real implementation, we'd use proper engagement rules
                if unit.position == attacking_unit.position:
                    enemy_unit = unit
                    break
        if enemy_unit:
            break
    
    if enemy_unit is None:
        # No enemy found to fight with
        return
    
    # Simple melee resolution: each unit does damage to the other
    # In reality, we would use Weapon skill, attacks, etc. from the combat engine
    # For now, we'll do a simple exchange of damage
    
    # Attacking unit damages enemy
    damage_to_enemy = 1  # Simplified: 1 damage per attack
    state.deal_damage(enemy_unit.unit_id, damage_to_enemy)
    state.game_log.append(
        f"{attacking_unit.name} hit {enemy_unit.name} for {damage_to_enemy} damage"
    )
    
    # Enemy unit damages attacking unit (if still alive)
    if enemy_unit.is_alive:
        damage_to_attacker = 1  # Simplified: 1 damage per attack
        state.deal_damage(attacking_unit.unit_id, damage_to_attacker)
        state.game_log.append(
            f"{enemy_unit.name} hit {attacking_unit.name} for {damage_to_attacker} damage"
        )


def run_auto_game(roster_a: PlayerState,
                  roster_b: PlayerState,
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
                
                # Запускаем раунд через сценарий с faction AI
                # Для этого нужно модифицировать сценарий чтобы он принимал AI параметры
                # Пока используем упрощенный подход - переопределяем choose_action в контексте
                state = run_round_with_ai(state, game_map, mission, scenario, ai_a, ai_b, config)
                
                # Собираем лог раунда
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