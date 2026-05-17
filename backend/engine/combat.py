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
from backend.model.unit import Unit, Weapon, resolve_dice
from backend.state.game_state import TerrainType


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
class MultiAttackResult:
    """Result of simulating multiple weapons or squad attacks."""

    total_damage_per_iter: np.ndarray
    total_stats: SimulationStats
    weapon_results: list[CombatResult]
    squad_size: int
    n_iterations: int
    attacker_name: str
    defender_name: str
    simulation_time_ms: float


@dataclass
class RollResult:
    success: bool
    roll: int
    is_crit: bool


def _single_attack_sequence(
    rng: np.random.Generator,
    weapon: Weapon,
    attacker: Unit,
    defender: Unit,
    modifiers: list[Modifier],
    distance: int | None,
    is_stationary: bool,
    squad_size: int,
    has_cover: bool = False,
    ignores_cover: bool = False,
) -> int:
    """Simulate a single weapon attack and return damage dealt."""
    context = _build_modifier_context(
        attacker=attacker,
        defender=defender,
        weapon=weapon,
        distance=distance,
        is_stationary=is_stationary,
        squad_size=squad_size,
        has_cover=has_cover,
        ignores_cover=ignores_cover,
    )

    # Resolve number of attacks
    attacks = _resolve_attacks(weapon, squad_size, modifiers, context, rng)
    if attacks == 0:
        return 0

    total_damage = 0
    for _ in range(attacks):
        damage = _resolve_attack_chain(rng, weapon, defender, modifiers, context)
        total_damage += damage

    return min(total_damage, defender.wounds)


def _resolve_attacks(
    weapon: Weapon,
    squad_size: int,
    modifiers: list[Modifier],
    context: ModifierContext,
    rng: np.random.Generator | None,
) -> int:
    """Resolve the number of attacks for this weapon."""
    attacks_dice = weapon.attacks_dice
    attacks = resolve_dice(attacks_dice, rng or np.random.default_rng())

    # Apply modifiers
    attack_modifiers = [m for m in modifiers if m.target == "attack_count"]
    for modifier in attack_modifiers:
        if modifier.condition and not _check_condition(modifier.condition, context):
            continue
        if modifier.operation == "add":
            attacks += int(modifier.value)
        elif modifier.operation == "subtract":
            attacks -= int(modifier.value)
        elif modifier.operation == "blast_bonus":
            blast_bonus = min(4, context.squad_size // 5)
            attacks += blast_bonus

    # Rapid fire modifier
    rapid_fire_modifiers = [
        m for m in modifiers if m.operation == "add" and "rapid_fire" in str(m.source)
    ]
    for modifier in rapid_fire_modifiers:
        if modifier.condition and not _check_condition(modifier.condition, context):
            continue
        attacks += int(modifier.value)

    return max(0, attacks)


def _resolve_attack_chain(
    rng: np.random.Generator,
    weapon: Weapon,
    defender: Unit,
    modifiers: list[Modifier],
    context: ModifierContext,
) -> int:
    """Resolve a single attack: Hit → Wound → Save → Damage → FNP."""
    # Hit roll
    hit_result, _hit_modifiers = _resolve_hit_roll(rng, weapon, modifiers, context)
    if not hit_result.success:
        return 0

    # Wound roll — auto_wound only if this was a Critical Hit AND Lethal Hits is active
    critical_effect = handle_critical_hit(hit_result, "hit_roll", modifiers, context)
    wound_result = _resolve_wound_chain(
        rng, weapon, defender, modifiers, context, critical_effect.auto_wound
    )
    return wound_result


def _resolve_hit_roll(
    rng: np.random.Generator,
    weapon: Weapon,
    modifiers: list[Modifier],
    context: ModifierContext,
) -> tuple[RollResult, ModifierResult]:
    hit_modifiers = apply_modifiers("hit_roll", weapon.skill, modifiers, context, rng)
    hit_result = _roll_with_modifiers(rng, hit_modifiers, modifiers, "hit_roll")
    return hit_result, hit_modifiers


def _resolve_wound_chain(
    rng: np.random.Generator,
    weapon: Weapon,
    defender: Unit,
    modifiers: list[Modifier],
    context: ModifierContext,
    auto_wound: bool,
) -> int:
    if auto_wound:
        wound_result = RollResult(success=True, roll=6, is_crit=False)
        # is_crit=False: auto-wounds from Lethal Hits are NOT Critical Wounds.
        # Devastating Wounds only triggers on actual Critical Wound rolls (per 10e).
        wound_modifiers = ModifierResult(target_value=2)
    else:
        wound_target = defender.effective_toughness(weapon.strength)
        wound_modifiers = apply_modifiers("wound_roll", wound_target, modifiers, context, rng)
        wound_result = _roll_with_modifiers(rng, wound_modifiers, modifiers, "wound_roll")
        anti_critical = _resolve_anti_critical(weapon.tags, wound_result.roll, context.defender)
        if anti_critical:
            wound_result = RollResult(success=True, roll=wound_result.roll, is_crit=True)
        if not wound_result.success:
            return 0

    wound_critical = handle_critical_hit(wound_result, "wound_roll", modifiers, context)
    ignore_save = wound_modifiers.ignore_save or wound_critical.ignore_save
    if not ignore_save:
        # Save with Cover: +1 SV if has_cover and not ignores_cover
        save_target = defender.best_save(weapon.ap)
        if context.has_cover and not context.ignores_cover:
            save_target = max(2, save_target - 1)  # +1 save = lower target (SV3+ → SV2+)
        save_target = max(1, min(6, save_target - weapon.ap))
        save_modifiers = apply_modifiers("save_roll", save_target, modifiers, context, rng)
        save_result = _roll_with_modifiers(rng, save_modifiers, modifiers, "save_roll")
        if save_result.success:
            return 0

    damage = resolve_dice(weapon.damage_dice, rng)
    damage_modifiers = [m for m in modifiers if m.target == "damage"]
    for modifier in damage_modifiers:
        if modifier.condition and not _check_condition(modifier.condition, context):
            continue
        if modifier.operation == "add":
            damage += int(modifier.value)
    damage_dealt = min(damage, defender.wounds)
    if defender.feel_no_pain:
        fnp_rolls = rng.integers(1, 7, size=damage_dealt)
        fnp_saves = int(np.sum(fnp_rolls >= defender.feel_no_pain))
        damage_dealt -= fnp_saves
    return max(0, damage_dealt)


def _resolve_anti_critical(tags: list[str], roll: int, defender: Any) -> bool:
    """Check if anti-keyword makes this a critical wound."""
    for tag in tags:
        anti = parse_anti_tag(tag)
        if anti and resolve_anti_wound(roll, anti, defender):
            return True
    return False


def _roll_with_modifiers(
    rng: np.random.Generator,
    modifier_result: ModifierResult,
    modifiers: list[Modifier],
    step: str,
) -> RollResult:
    if modifier_result.auto_success:
        return RollResult(success=True, roll=6, is_crit=True)

    roll = rng.integers(1, 7)
    original_roll = roll

    # Apply rerolls
    while should_reroll(roll, modifier_result.target_value, modifiers, step):
        roll = rng.integers(1, 7)

    success = roll >= modifier_result.target_value
    is_crit = roll == 6

    # Sustained hits
    if step == "hit_roll" and is_crit:
        sustained_count = modifier_result.extra_rolls
        for _ in range(sustained_count):
            extra_roll = rng.integers(1, 7)
            if extra_roll >= modifier_result.target_value:
                success = True  # Extra hits count as successes

    return RollResult(success=success, roll=original_roll, is_crit=is_crit)


def _expected_steps(
    weapon: Weapon,
    attacker: Unit,
    defender: Unit,
    modifiers: list[Modifier],
    distance: int | None,
    is_stationary: bool,
    squad_size: int,
    has_cover: bool = False,
    ignores_cover: bool = False,
) -> tuple[float, float, float]:
    """Calculate expected values for hits, wounds, and unsaved wounds."""
    context = _build_modifier_context(
        attacker, defender, weapon, distance, is_stationary, squad_size, has_cover, ignores_cover
    )

    # Expected hits (simplified)
    hit_target = weapon.skill
    apply_modifiers("hit_roll", hit_target, modifiers, context, None)
    hit_prob = max(0, min(1, (7 - hit_target) / 6))
    avg_hits = hit_prob

    # Expected wounds
    wound_target = defender.effective_toughness(weapon.strength)
    apply_modifiers("wound_roll", wound_target, modifiers, context, None)
    wound_prob = max(0, min(1, (7 - wound_target) / 6))
    avg_wounds = avg_hits * wound_prob

    # Expected unsaved wounds — with Cover
    save_target = defender.best_save(weapon.ap)
    save_prob = compute_save(save_target, has_cover, ignores_cover)
    avg_unsaved = avg_wounds * (1 - save_prob)

    return avg_hits, avg_wounds, avg_unsaved


def _build_modifier_context(
    attacker: Unit,
    defender: Unit,
    weapon: Weapon,
    distance: int | None,
    is_stationary: bool,
    squad_size: int,
    has_cover: bool = False,
    ignores_cover: bool = False,
) -> ModifierContext:
    """Build modifier context for this attack."""
    return ModifierContext(
        attacker=attacker,
        defender=defender,
        weapon=weapon,
        distance=distance,
        is_stationary=is_stationary,
        squad_size=squad_size,
        has_cover=has_cover,
        ignores_cover=ignores_cover,
    )


def _check_condition(condition: dict[str, Any], context: ModifierContext) -> bool:
    """Check whether a conditional modifier is active."""
    if condition.get("half_range"):
        if context.distance is None:
            return False
        if context.weapon is None or context.weapon.range_max is None:
            return False
        if context.distance > context.weapon.range_max / 2:
            return False

    if condition.get("stationary") and not context.is_stationary:
        return False

    squad_size_min = condition.get("squad_size_min")
    return not (squad_size_min is not None and context.squad_size < squad_size_min)


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
    has_cover: bool = False,
    ignores_cover: bool = False,
) -> CombatResult:
    """Run a Monte Carlo simulation for weapon against defender."""
    if pool is None:
        pool = DicePool()  # random seed per call

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
            has_cover=has_cover,
            ignores_cover=ignores_cover,
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
        has_cover=has_cover,
        ignores_cover=ignores_cover,
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
            has_cover=has_cover,
            ignores_cover=ignores_cover,
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


def simulate_unit_attack(
    attacker: Unit,
    defender: Unit,
    pool: DicePool | None = None,
    modifiers: list[Modifier] | None = None,
    squad_size: int = 1,
    n_iterations: int = 10000,
    distance: int | None = None,
    is_stationary: bool = False,
    has_cover: bool = False,
    ignores_cover: bool = False,
) -> MultiAttackResult:
    """Simulate attack from a unit with multiple weapons against a defender."""
    if pool is None:
        pool = DicePool()  # random seed per call

    start = time.monotonic()

    # Get all weapons from the attacker
    all_weapons = []
    if hasattr(attacker, "ranged_weapons") and attacker.ranged_weapons:
        all_weapons.extend(attacker.ranged_weapons)
    if hasattr(attacker, "melee_weapons") and attacker.melee_weapons:
        all_weapons.extend(attacker.melee_weapons)

    # If no weapons found, use a default placeholder
    if not all_weapons:
        from backend.model.unit import Weapon

        all_weapons = [
            Weapon(
                name="Default Weapon",
                type="ranged",
                range_max=24,
                attacks_dice=(0, 0, 1),
                skill=3,
                strength=4,
                ap=0,
                damage_dice=(0, 0, 1),
                tags=[],
            )
        ]

    # Simulate each weapon
    weapon_results = []
    total_damage_per_iter = np.zeros(n_iterations, dtype=int)

    for weapon in all_weapons:
        weapon_result = simulate_weapon_attack(
            weapon=weapon,
            attacker=attacker,
            defender=defender,
            pool=pool,
            modifiers=modifiers,
            n_iterations=n_iterations,
            distance=distance,
            is_stationary=is_stationary,
            squad_size=squad_size,
            has_cover=has_cover,
            ignores_cover=ignores_cover,
        )
        weapon_results.append(weapon_result)
        total_damage_per_iter += weapon_result.damage_per_iter

    # Calculate total stats
    total_stats = compute_stats(total_damage_per_iter, target_wounds=defender.wounds * squad_size)

    end = time.monotonic()

    return MultiAttackResult(
        total_damage_per_iter=total_damage_per_iter,
        total_stats=total_stats,
        weapon_results=weapon_results,
        squad_size=squad_size,
        n_iterations=n_iterations,
        attacker_name=attacker.name,
        defender_name=defender.name,
        simulation_time_ms=(end - start) * 1000,
    )


def simulate_squad_attack(
    attackers: list[Unit],
    defender: Unit,
    pool: DicePool | None = None,
    modifiers: list[Modifier] | None = None,
    n_iterations: int = 10000,
    distance: int | None = None,
    is_stationary: bool = False,
) -> MultiAttackResult:
    """Simulate attack from multiple units (squad) against a defender."""
    if pool is None:
        pool = DicePool()  # random seed per call

    start = time.monotonic()

    # Simulate each attacker
    attacker_results = []
    total_damage_per_iter = np.zeros(n_iterations, dtype=int)

    for attacker in attackers:
        attacker_result = simulate_unit_attack(
            attacker=attacker,
            defender=defender,
            pool=pool,
            modifiers=modifiers,
            squad_size=1,  # Each attacker is treated as a single model
            n_iterations=n_iterations,
            distance=distance,
            is_stationary=is_stationary,
        )
        attacker_results.append(attacker_result)
        total_damage_per_iter += attacker_result.total_damage_per_iter

    # Combine weapon results from all attackers
    all_weapon_results = []
    for attacker_result in attacker_results:
        all_weapon_results.extend(attacker_result.weapon_results)

    # Calculate total stats
    total_stats = compute_stats(total_damage_per_iter, target_wounds=defender.wounds)

    end = time.monotonic()

    return MultiAttackResult(
        total_damage_per_iter=total_damage_per_iter,
        total_stats=total_stats,
        weapon_results=all_weapon_results,
        squad_size=len(attackers),
        n_iterations=n_iterations,
        attacker_name=f"Squad ({len(attackers)} models)",
        defender_name=defender.name,
        simulation_time_ms=(end - start) * 1000,
    )


# ── Cover & Terrain Functions ─────────────────────────────────────────────────


def _bresenham_line(x0: int, y0: int, x1: int, y1: int) -> list[tuple[int, int]]:
    """All cells on the line between two points using Bresenham's algorithm."""
    cells = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    while True:
        cells.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy
    return cells


def _has_cover(
    target_pos: tuple[int, int],
    shooter_pos: tuple[int, int],
    terrain_map: np.ndarray | None,
    target_category: str,
) -> bool:
    """Check if target has Benefit of Cover.

    Cover is granted if:
    1. Target is INFANTRY and terrain exists between shooter and target
    2. Target is in terrain that grants cover to all (woods)
    3. Target is within 1" of barricade
    """
    if terrain_map is None:
        return False

    tx, ty = target_pos
    sx, sy = shooter_pos

    # Check: target is ON woods terrain (cover for all)
    target_tile = terrain_map[ty, tx]
    if target_tile in (TerrainType.WOODS, TerrainType.RUINS):
        return True

    # INFANTRY gets cover from ruins/woods/barricade on line of fire
    if target_category.lower() not in ("infantry", "character", "epic hero"):
        return False

    # Check: is there terrain between shooter and target (Bresenham)
    cells_between = _bresenham_line(sx, sy, tx, ty)
    for cx, cy in cells_between[1:-1]:  # exclude start/end
        tile = terrain_map[cy, cx]
        if tile in (TerrainType.RUINS, TerrainType.WOODS, TerrainType.BARRICADE):
            return True

    return False


def compute_save(
    effective_sv: int,  # already adjusted for AP (from best_save)
    has_cover: bool,
    ignores_cover: bool,
) -> float:
    """Probability of successful save roll with Cover and Ignores Cover.

    effective_sv is the post-AP save value (e.g., SV3+ with AP-1 = SV4+).
    Cover: +1 SV (improves save by 1, e.g., SV4+ → SV3+)
    Ignores Cover: cancels Cover benefit
    """
    if has_cover and not ignores_cover:
        effective_sv = max(2, effective_sv - 1)  # +1 save = lower target

    effective = max(1, min(6, effective_sv))
    return (7 - effective) / 6


def apply_indirect_fire(
    hit_prob: float,
    has_los: bool,
    target_has_cover: bool,
) -> float:
    """Apply Indirect Fire modifier.

    Indirect Fire: -1 to hit without LoS, additional -1 if target has Cover.
    """
    if has_los:
        return hit_prob  # direct fire - no penalty

    # Without LoS: -1 to hit
    hit_prob = max(1 / 6, hit_prob - 1 / 6)

    # If target also in Cover: additional -1 (within cap)
    if target_has_cover:
        hit_prob = max(1 / 6, hit_prob - 1 / 6)

    return hit_prob
