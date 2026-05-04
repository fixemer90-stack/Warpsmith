"""
F3.1 — Greedy Decision Engine.

Оценивает все возможные действия для юнита в текущей фазе
и возвращает лучшее по взвешенной сумме критериев.

Совместимость: backend.model.unit (Unit, Weapon, DiceExpr),
               backend.state.game_state (GameState, UnitState, GamePhase)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

import numpy as np

from backend.model.unit import Unit, Weapon, resolve_dice
from backend.state.game_state import GamePhase, GameState, UnitState

# ── Data Model ─────────────────────────────────────────────────


class ActionType(Enum):
    """Типы действий, доступные AI."""

    SHOOT = "shoot"
    CHARGE = "charge"
    MOVE = "move"
    ADVANCE = "advance"
    FALL_BACK = "fall_back"
    HOLD = "hold"
    USE_ABILITY = "use_ability"
    USE_STRATAGEM = "use_stratagem"


@dataclass
class Action:
    """Одно действие, оценённое decision engine."""

    type: ActionType
    target_id: str | None = None
    weapon_index: int | None = None
    mode: str | None = None
    target_position: tuple[int, int] | None = None
    score: float = 0.0
    rationale: str = ""


@dataclass
class EvaluationContext:
    """Контекст для оценки действий юнита."""

    actor: UnitState
    actor_unit: Unit
    state: GameState
    opponent_units: list[UnitState]
    phase: GamePhase
    turn: int
    opponent_units_map: dict[str, Unit] = field(default_factory=dict)
    rng: np.random.Generator = field(default_factory=lambda: np.random.default_rng())
    weights: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))


# ── Weights ────────────────────────────────────────────────────

DEFAULT_WEIGHTS = {
    "kill_efficiency": 1.0,
    "threat_reduction": 0.8,
    "objective_value": 0.6,
    "survival_risk": 0.4,
    "synergy_bonus": 0.3,
}


# ── Helpers ────────────────────────────────────────────────────


def _distance(a: tuple[int, int], b: tuple[int, int]) -> float:
    """Евклидово расстояние между двумя точками."""
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def _avg_dice(dice) -> float:
    """Среднее значение DiceExpr (count, dice_type, modifier)."""
    count, dice_type, modifier = dice
    return count * (dice_type + 1) / 2 + modifier


def _weapon_max_range(weapon: Weapon) -> float:
    """Максимальная дальность оружия в дюймах."""
    if weapon.type == "melee":
        return 1.0
    if weapon.range_max is not None:
        return float(weapon.range_max)
    return float("inf")


def _in_weapon_range(actor: UnitState, target: UnitState, weapon: Weapon) -> bool:
    """Проверить, входит ли цель в дальность оружия."""
    dist = _distance(actor.position, target.position)
    if weapon.type == "melee":
        return dist <= 1.0
    if weapon.range_max is not None and dist > weapon.range_max:
        return False
    return True


def _has_valid_los(actor: UnitState, target: UnitState, state: GameState) -> bool:
    """Проверить наличие прямой видимости (stub — всегда True)."""
    return True


def _wound_table(strength: int, toughness: int) -> float:
    """Вероятность ранения по таблице 10-й редакции."""
    if strength >= 2 * toughness:
        return 5 / 6  # 2+
    if strength > toughness:
        return 4 / 6  # 3+
    if strength == toughness:
        return 3 / 6  # 4+
    if strength > toughness / 2:
        return 2 / 6  # 5+
    return 1 / 6  # 6+


def _compute_expected_damage_ranged(
    weapon: Weapon,
    target_toughness: int,
    target_save: int,
) -> float:
    """Ожидаемый урон одного выстрела (упрощённо, без модификаторов)."""
    if weapon.type == "melee":
        return 0.0

    avg_attacks = _avg_dice(weapon.attacks_dice)
    hit_prob = max(1 / 6, min(5 / 6, (7 - weapon.skill) / 6))
    wound_prob = _wound_table(weapon.strength, target_toughness)

    effective_save = max(1, min(6, target_save - weapon.ap))  # AP ухудшает сейв
    save_success = (7 - effective_save) / 6  # шанс спастись
    fail_save = 1 - save_success

    avg_damage = _avg_dice(weapon.damage_dice)

    return avg_attacks * hit_prob * wound_prob * fail_save * avg_damage


def _estimate_melee_damage(
    unit: Unit,
    target_toughness: int,
    target_save: int,
) -> float:
    """Суммарный ожидаемый урон по всем melee-оружиям."""
    total = 0.0
    for weapon in unit.melee_weapons:
        avg_attacks = _avg_dice(weapon.attacks_dice)
        hit_prob = max(1 / 6, min(5 / 6, (7 - weapon.skill) / 6))
        wound_prob = _wound_table(weapon.strength, target_toughness)
        effective_save = max(1, min(6, target_save - weapon.ap))  # AP ухудшает сейв
        fail_save = 1 - (7 - effective_save) / 6
        avg_damage = _avg_dice(weapon.damage_dice)
        total += avg_attacks * hit_prob * wound_prob * fail_save * avg_damage
    return total


# ── Candidate generation ───────────────────────────────────────


def _get_opponent_unit(target: UnitState, ctx: EvaluationContext) -> Unit | None:
    """Получить полную модель Unit оппонента."""
    return ctx.opponent_units_map.get(target.unit_id)


def _get_opponent_toughness(target: UnitState, ctx: EvaluationContext) -> int:
    opp = _get_opponent_unit(target, ctx)
    if opp:
        return opp.toughness
    return getattr(target, "toughness", 4)


def _get_opponent_save(target: UnitState, ctx: EvaluationContext) -> int:
    opp = _get_opponent_unit(target, ctx)
    if opp:
        return opp.save
    return getattr(target, "sv", 3)


def _generate_candidates(
    actor: UnitState,
    actor_unit: Unit,
    ctx: EvaluationContext,
) -> list[Action]:
    """Сгенерировать все возможные действия для юнита в текущей фазе."""
    candidates: list[Action] = []

    if ctx.phase == GamePhase.SHOOTING:
        if actor.is_engaged or actor.is_battle_shocked:
            return [Action(type=ActionType.HOLD, rationale="cannot shoot")]
        for wi, weapon in enumerate(actor_unit.ranged_weapons):
            for target in ctx.opponent_units:
                if not target.is_alive:
                    continue
                if not _in_weapon_range(actor, target, weapon):
                    continue
                if not _has_valid_los(actor, target, ctx.state):
                    continue
                candidates.append(
                    Action(
                        type=ActionType.SHOOT,
                        target_id=target.unit_id,
                        weapon_index=wi,
                        mode="normal",
                    )
                )

    elif ctx.phase == GamePhase.CHARGE:
        if actor.is_battle_shocked:
            return [Action(type=ActionType.HOLD, rationale="battle-shocked")]
        for target in ctx.opponent_units:
            if not target.is_alive:
                continue
            dist = _distance(actor.position, target.position)
            if dist <= 12:
                candidates.append(Action(type=ActionType.CHARGE, target_id=target.unit_id))

    elif ctx.phase == GamePhase.MOVEMENT:
        for target in ctx.opponent_units:
            if not target.is_alive:
                continue
            candidates.append(
                Action(
                    type=ActionType.MOVE,
                    target_id=target.unit_id,
                    target_position=target.position,
                )
            )
            candidates.append(
                Action(
                    type=ActionType.ADVANCE,
                    target_id=target.unit_id,
                    target_position=target.position,
                )
            )

    if not candidates:
        candidates.append(Action(type=ActionType.HOLD, rationale="no valid actions"))
    return candidates


# ── Evaluation ─────────────────────────────────────────────────


def score_shoot(
    actor: UnitState,
    actor_unit: Unit,
    target: UnitState,
    weapon_idx: int,
    ctx: EvaluationContext,
) -> float:
    """Оценка одного выстрела."""
    if weapon_idx < 0 or weapon_idx >= len(actor_unit.ranged_weapons):
        return 0.0
    weapon = actor_unit.ranged_weapons[weapon_idx]
    expected_dmg = _compute_expected_damage_ranged(
        weapon,
        _get_opponent_toughness(target, ctx),
        _get_opponent_save(target, ctx),
    )
    if expected_dmg <= 0:
        return 0.0
    return expected_dmg * 5.0 * ctx.weights.get("kill_efficiency", 1.0)


def score_charge(
    actor: UnitState,
    actor_unit: Unit,
    target: UnitState,
    ctx: EvaluationContext,
) -> float:
    """Оценка заряда."""
    dist = _distance(actor.position, target.position)
    # Упрощённая вероятность 2D6 >= dist
    if dist <= 6:
        success_prob = 1.0
    elif dist <= 7:
        success_prob = 0.9
    elif dist <= 8:
        success_prob = 0.75
    elif dist <= 9:
        success_prob = 0.55
    elif dist <= 10:
        success_prob = 0.35
    elif dist <= 11:
        success_prob = 0.15
    else:
        success_prob = 0.03

    melee_dmg = _estimate_melee_damage(
        actor_unit,
        _get_opponent_toughness(target, ctx),
        _get_opponent_save(target, ctx),
    )
    return success_prob * melee_dmg * ctx.weights.get("kill_efficiency", 1.0)


def score_move(
    actor: UnitState,
    target_pos: tuple[int, int],
    ctx: EvaluationContext,
) -> float:
    """Оценка движения к цели."""
    current_dist = _distance(actor.position, target_pos)
    if current_dist < 1:
        return 0.0
    move_range = 6
    improvement = min(1.0, move_range / current_dist)
    return improvement * ctx.weights.get("objective_value", 0.6)


def evaluate_action(
    actor: UnitState,
    actor_unit: Unit,
    action: Action,
    ctx: EvaluationContext,
) -> Action:
    """Оценить гипотетическое action, вернуть action с проставленным score."""
    score = 0.0
    rationale = action.type.value

    if action.type == ActionType.SHOOT and action.target_id:
        target = _find_target(action.target_id, ctx.opponent_units)
        if target:
            score = score_shoot(actor, actor_unit, target, action.weapon_index or 0, ctx)
            rationale = f"shoot {target.name} (w={action.weapon_index})"

    elif action.type == ActionType.CHARGE and action.target_id:
        target = _find_target(action.target_id, ctx.opponent_units)
        if target:
            score = score_charge(actor, actor_unit, target, ctx)
            rationale = f"charge {target.name}"

    elif action.type in (ActionType.MOVE, ActionType.ADVANCE) and action.target_position:
        score = score_move(actor, action.target_position, ctx)
        if action.type == ActionType.ADVANCE:
            score *= 0.8
            rationale = "advance toward enemy"
        else:
            rationale = "move toward enemy"

    action.score = round(score, 4)
    action.rationale = rationale
    return action


def _find_target(target_id: str, units: list[UnitState]) -> UnitState | None:
    for u in units:
        if u.unit_id == target_id:
            return u
    return None


# ── Main entry point ───────────────────────────────────────────


def choose_action(
    actor: UnitState,
    actor_unit: Unit,
    ctx: EvaluationContext,
) -> Action:
    """Главная точка входа: выбрать лучшее действие для юнита в фазе."""
    candidates = _generate_candidates(actor, actor_unit, ctx)
    if not candidates:
        return Action(type=ActionType.HOLD, score=0.0, rationale="no actions generated")

    results = [evaluate_action(actor, actor_unit, a, ctx) for a in candidates]
    best = max(results, key=lambda a: a.score)
    return best
