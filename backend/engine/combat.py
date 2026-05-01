"""Full weapon attack simulation with Monte Carlo."""

import time
from dataclasses import dataclass
from typing import Any

import numpy as np

from backend.engine.dice import DicePool, SimulationStats, compute_stats
from backend.engine.modifiers import (
    Modifier,
    ModifierContext,
    ModifierResult,
    apply_modifiers,
    build_weapon_modifiers,
    handle_critical_hit,
    parse_anti_tag,
    resolve_anti_wound,
    should_reroll,
)
from backend.model.unit import Unit, Weapon


@dataclass
class CombatResult:
    damage_per_iter: np.ndarray
    stats: SimulationStats
    avg_attacks: float
    avg_hits: float
    avg_wounds: float
    avg_unsaved_wounds: float
    avg_damage_per_success: float
    n_iterations: int
    weapon_name: str
    target_name: str
    simulation_time_ms: float


@dataclass
class RollResult:
    success: bool
    roll: int
    is_crit: bool


def simulate_weapon_attack(
    weapon: Weapon,
    attacker: Unit,
    defender: Unit,
    pool: DicePool | None = None,
    modifiers: list[Modifier] | None = None,
    n_iterations: int = 10000,
    distance: int | None = None,
    is_stationary: bool = False,
    squad_size: int = 1,
) -> CombatResult:
    """Run a Monte Carlo simulation for weapon against defender."""
    if pool is None:
        pool = DicePool(seed=42)

    all_modifiers = list(modifiers or []) + build_weapon_modifiers(weapon)
    start = time.monotonic()
    damage = pool.simulate(
        lambda rng: _single_attack_sequence(
            rng=rng,
            weapon=weapon,
            attacker=attacker,
            defender=defender,
            modifiers=all_modifiers,
            distance=distance,
            is_stationary=is_stationary,
            squad_size=squad_size,
        ),
        n=n_iterations,
    )
    end = time.monotonic()

    avg_hits, avg_wounds, avg_unsaved = _expected_steps(
        weapon=weapon,
        attacker=attacker,
        defender=defender,
        modifiers=all_modifiers,
        distance=distance,
        is_stationary=is_stationary,
        squad_size=squad_size,
    )
    avg_attacks = _resolve_attacks(
        weapon=weapon,
        squad_size=squad_size,
        modifiers=all_modifiers,
        context=_build_modifier_context(
            attacker=attacker,
            defender=defender,
            weapon=weapon,
            distance=distance,
            is_stationary=is_stationary,
            squad_size=squad_size,
        ),
        rng=None,
    )
    stats = compute_stats(damage, target_wounds=defender.wounds)

    return CombatResult(
        damage_per_iter=damage,
        stats=stats,
        avg_attacks=avg_attacks,
        avg_hits=avg_hits,
        avg_wounds=avg_wounds,
        avg_unsaved_wounds=avg_unsaved,
        avg_damage_per_success=avg_hits / avg_attacks if avg_attacks > 0 else 0,
        n_iterations=n_iterations,
        weapon_name=weapon.name,
        target_name=defender.name,
        simulation_time_ms=(end - start) * 1000,
    )