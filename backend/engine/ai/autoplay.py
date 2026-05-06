"""
F3.5 — Auto-play: AI vs AI Full Scenario.

Размещает юниты, запускает полную симуляцию AI vs AI через Scenario (F2.5),
сбор логов и возврат результата.
Интегрируется с F3.2 Faction AI Profiles для принятия решений.
"""

from __future__ import annotations

import contextlib
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from backend.engine.ai.deployment import (
    DeploymentType,
    deploy_game,
)
from backend.engine.ai.faction_ai import load_profile
from backend.engine.replay import ReplayRecorder
from backend.engine.scenario import Scenario
from backend.model.unit import Unit
from backend.state.game_state import GamePhase, GameState, PlayerState, UnitState
from backend.state.map import BattlefieldMap, TerrainType
from backend.state.roster import RosterState


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
    seed: int | None = None  # None → random at runtime
    time_limit_seconds: int = 30
    use_sticky_objectives: bool = True
    enable_stratagems: bool = True
    log_all_events: bool = True


@dataclass
class AutoPlayResult:
    """Результат полной симуляции."""

    game_state: GameState
    round_logs: list[dict[str, Any]]
    placements: dict[str, list[Any]]
    error: str | None = None
    total_duration_ms: float = 0.0
    summary: dict[str, Any] = field(default_factory=dict)
    replay: Any = None  # Replay object (F3.6), serialized in to_dict()

    def to_dict(self) -> dict[str, Any]:
        """Сериализация результата для JSON."""
        game_id = None
        if self.game_state and hasattr(self.game_state, "game_id"):
            game_id = self.game_state.game_id

        victory_points = {}
        if hasattr(self.game_state, "players"):
            for player_id, player in self.game_state.players.items():
                victory_points[player_id] = getattr(player, "victory_points", 0)

        return {
            "game_id": game_id,
            "rounds": len(self.round_logs),
            "victory_points": victory_points,
            "winner": self._determine_winner(),
            "summary": self.summary,
            "error": self.error,
            "duration_ms": self.total_duration_ms,
        }

    def _determine_winner(self) -> int | None:
        """Определить победителя по очкам победы."""
        if not hasattr(self.game_state, "players") or len(self.game_state.players) < 2:
            return None

        player_ids = list(self.game_state.players.keys())
        if len(player_ids) < 2:
            return None

        player_a_id, player_b_id = player_ids[0], player_ids[1]
        vp_a = getattr(self.game_state.players[player_a_id], "victory_points", 0)
        vp_b = getattr(self.game_state.players[player_b_id], "victory_points", 0)

        if vp_a > vp_b:
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


def _validate_rosters(roster_a: RosterState, roster_b: RosterState) -> list[str]:
    """Валидация ростеров перед симуляцией."""
    errors = []

    max_pts = 2000
    if hasattr(roster_a, "total_pts") and roster_a.total_pts > max_pts:
        errors.append(f"Roster A exceeds {max_pts} PTS: {roster_a.total_pts}")
    if hasattr(roster_b, "total_pts") and roster_b.total_pts > max_pts:
        errors.append(f"Roster B exceeds {max_pts} PTS: {roster_b.total_pts}")

    if hasattr(roster_a, "units") and len(roster_a.units) == 0:
        errors.append("Roster A has no units")
    if hasattr(roster_b, "units") and len(roster_b.units) == 0:
        errors.append("Roster B has no units")

    return errors


def _create_default_map(seed: int | None = None, pts_limit: int = 2000) -> BattlefieldMap:
    """Создать карту подходящего размера в зависимости от PTS лимита."""
    if seed is not None:
        np.random.seed(seed)

    # Determine map size by PTS limit
    if pts_limit <= 500:
        height, width = (30, 44)
    elif pts_limit <= 1000:
        height, width = (44, 44)
    elif pts_limit <= 2000:
        height, width = (44, 60)
    else:
        height, width = (44, 90)

    terrain = np.full((height, width), TerrainType.OPEN_GROUND, dtype=object)
    game_map = BattlefieldMap(width=width, height=height, terrain=terrain)

    return game_map


def _roster_to_player_state(
    roster: RosterState, player_id: str, config: AutoPlayConfig
) -> PlayerState:
    """Convert a RosterState (data) to a PlayerState (runtime game state)."""
    units: dict[str, UnitState] = {}
    for unit_name, unit_model in roster.units.items():
        # Infer squad size from model_count
        min_size, _ = unit_model.model_count
        # Use min size for test simplicity; could be parameterized
        squad_size = min_size

        unit_state = UnitState(
            unit_id=unit_name,
            name=unit_name,
            faction=roster.faction,
            position=(0, 0),
            current_wounds=unit_model.wounds * squad_size,
            max_wounds=unit_model.wounds * squad_size,
            models_remaining=squad_size,
            models_total=squad_size,
            leadership=unit_model.leadership,
            objective_control=unit_model.objective_control,
            is_warlord=(unit_name == roster.warlord_unit_name),
        )
        units[unit_name] = unit_state

    return PlayerState(
        player_id=player_id,
        name=roster.name,
        faction=roster.faction,
        units=units,
    )


def _build_unit_models(roster_a: RosterState, roster_b: RosterState) -> dict[str, Unit]:
    """Build a flat dict of unit_id → Unit model for both rosters."""
    models: dict[str, Unit] = {}
    for unit_name, unit_model in roster_a.units.items():
        models[unit_name] = unit_model
    for unit_name, unit_model in roster_b.units.items():
        models[unit_name] = unit_model
    return models


def _build_summary(
    state: GameState, round_logs: list[dict[str, Any]], _placements: dict[str, list[Any]]
) -> dict[str, Any]:
    """Построить сводку симуляции."""
    total_kills: dict[str, int] = {}
    total_damage: dict[str, int] = {}
    charge_count: dict[str, int] = {}

    for log in round_logs:
        if isinstance(log, dict) and "events" in log:
            for event in log["events"]:
                player = str(event.get("player", "0"))
                if event.get("type") == "kill":
                    total_kills[player] = total_kills.get(player, 0) + 1
                if event.get("damage", 0) > 0:
                    total_damage[player] = total_damage.get(player, 0) + event["damage"]
                if event.get("action") == "charge":
                    charge_count[player] = charge_count.get(player, 0) + 1

    # Army info from state.players
    army_info: dict[str, dict[str, Any]] = {}
    for pid, player in state.players.items():
        army_info[pid] = {
            "name": player.name,
            "faction": player.faction,
        }

    return {
        "winner": None,  # Будет заполнено в to_dict()
        "total_kills": total_kills,
        "total_damage": total_damage,
        "charge_count": charge_count,
        "rounds_played": len(round_logs),
        "armies": army_info,
    }


def _check_game_end(state: GameState) -> bool:
    """Проверить условия окончания игры."""
    if hasattr(state, "players"):
        players_alive = 0
        for player in state.players.values():
            if hasattr(player, "units"):
                alive_units = [u for u in player.units.values() if getattr(u, "is_alive", True)]
                if len(alive_units) > 0:
                    players_alive += 1

        if players_alive < 2:
            return True

    return bool(
        hasattr(state, "current_round")
        and hasattr(state, "max_rounds")
        and state.current_round >= state.max_rounds
    )


def run_auto_game(
    roster_a: RosterState,
    roster_b: RosterState,
    mission_name: str = "only_war",
    config: AutoPlayConfig | None = None,
) -> AutoPlayResult:
    """
    Запустить полную AI vs AI симуляцию.

    Flow:
    1. Валидация ростеров (RosterState)
    2. Конвертация RosterState → PlayerState/UnitState
    3. Создание GameState (миссия создаётся автоматически из mission_name)
    4. Deploy юнитов на карту
    5. Запуск Scenario.run_round() × max_rounds
    6. Сбор логов и summary
    7. Возврат результата
    """
    start = time.time()
    config = config or AutoPlayConfig()

    # Generate seed if not provided (logged for reproducibility)
    actual_seed = (
        config.seed if config.seed is not None else np.random.default_rng().integers(1, 99999)
    )

    # 1. Validate
    errors = _validate_rosters(roster_a, roster_b)
    if errors:
        return AutoPlayResult(
            game_state=None,  # type: ignore[arg-type]
            round_logs=[],
            placements={},
            error=f"Roster validation failed: {'; '.join(errors)}",
        )

    try:
        # 2. Create map (size based on PTS limit)
        pts_limit = max(
            getattr(roster_a, "total_pts", 2000),
            getattr(roster_b, "total_pts", 2000),
        )
        game_map = _create_default_map(seed=actual_seed, pts_limit=pts_limit)

        # 3. Convert rosters to PlayerState
        player_a = _roster_to_player_state(roster_a, "1", config)
        player_b = _roster_to_player_state(roster_b, "2", config)

        # 4. Create GameState — __post_init__ auto-creates Mission from mission_name
        state = GameState(
            game_id=f"auto_{actual_seed}",
            mission_name=mission_name,
            map_width=game_map.width,
            map_height=game_map.height,
            current_round=1,
            current_phase=GamePhase.COMMAND,
            players={"1": player_a, "2": player_b},
            terrain_map=game_map.terrain if hasattr(game_map, "terrain") else None,
            max_rounds=config.max_rounds,
        )

        # 5. Build unit_models dict for combat engine
        unit_models = _build_unit_models(roster_a, roster_b)

        # 5.5. Load faction AI profiles (needed for deployment + scenario)
        faction_ai_profiles: dict[str, object] = {}
        for roster, player_id in [(roster_a, "1"), (roster_b, "2")]:
            with contextlib.suppress(Exception):
                profile = load_profile(roster.faction)
                if profile:
                    faction_ai_profiles[player_id] = profile
                    faction_ai_profiles[roster.faction] = profile

        # 6. Deploy units
        placements = deploy_game(
            game_state=state,
            unit_models=unit_models,
            deployment_type=config.deployment_type,
            battlefield=game_map,
            objectives=[],
            faction_ai_profiles=faction_ai_profiles,
        )

        state.game_log.append(
            f"Deployed {len(player_a.units)} units for Player 1, "
            f"{len(player_b.units)} units for Player 2"
        )

        # 7. Create Scenario and run game loop
        scenario = Scenario(
            game_state=state,
            unit_models=unit_models,
            battlefield=game_map,
            faction_ai_profiles=faction_ai_profiles,
        )

        round_logs: list[dict[str, Any]] = []
        last_log_len = 0

        # Run rounds through Scenario
        for r in range(config.max_rounds):
            # Time check
            elapsed = (time.time() - start) * 1000
            if elapsed > config.time_limit_seconds * 1000:
                raise TimeoutError(f"Simulation exceeded {config.time_limit_seconds}s")

            # Run one round via Scenario
            scenario.run_round()

            # Collect round log — capture ALL entries since last round start
            round_log = {
                "round": r + 1,
                "events": [],
                "phase_logs": state.game_log[last_log_len:],
            }
            round_logs.append(round_log)
            last_log_len = len(state.game_log)

            # Check end condition
            if _check_game_end(state):
                break

        # 8. Summary
        summary = _build_summary(state, round_logs, placements)

        return AutoPlayResult(
            game_state=state,
            round_logs=round_logs,
            placements=placements,
            total_duration_ms=(time.time() - start) * 1000,
            summary=summary,
        )

    except AutoPlayError as e:
        return AutoPlayResult(
            game_state=state if "state" in locals() else None,  # type: ignore[arg-type]
            round_logs=round_logs if "round_logs" in locals() else [],
            placements=placements if "placements" in locals() else {},
            error=str(e),
            total_duration_ms=(time.time() - start) * 1000,
        )

    except Exception as e:
        return AutoPlayResult(
            game_state=None,  # type: ignore[arg-type]
            round_logs=[],
            placements={},
            error=f"Unexpected error during simulation: {e!s}",
            total_duration_ms=(time.time() - start) * 1000,
        )
