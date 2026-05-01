"""Modifier system for combat resolution steps."""

from dataclasses import dataclass
from typing import Any, Literal, Optional

import numpy as np

Operation = Literal[
    "add",
    "subtract",
    "reroll_all",
    "reroll_hits",
    "reroll_wounds",
    "reroll_saves",
    "reroll_ones",
    "reroll_ones_hit",
    "reroll_ones_wound",
    "sustained_hits",
    "lethal_hits",
    "devastating_wounds",
    "ignore_cover",
    "ignore_modifiers",
    "auto_hit",
    "auto_wound",
]

TargetStep = Literal[
    "attack_count",
    "hit_roll",
    "wound_roll",
    "save_roll",
    "damage",
    "fnp_roll",
]


@dataclass
class Modifier:
    target: TargetStep
    operation: Operation
    value: Any = 0
    source: str = "ability"
    condition: dict[str, Any] | None = None


@dataclass
class ModifierContext:
    attacker: Any
    defender: Any
    weapon: Any
    distance: int | None = None
    is_stationary: bool = False
    squad_size: int = 1


@dataclass
class ModifierResult:
    target_value: int
    extra_rolls: int = 0
    auto_success: bool = False
    ignore_save: bool = False
    reroll: bool = False


def apply_modifiers(
    step: TargetStep,
    base_target: int,
    modifiers: list[Modifier],
    context: ModifierContext,
    rng: np.random.Generator,
) -> ModifierResult:
    """Apply relevant modifiers to a combat step."""
    del rng

    total_delta = 0
    reroll = False
    ignore_numeric_modifiers = False
    result = ModifierResult(target_value=base_target)

    for modifier in modifiers:
        if modifier.target != step:
            continue
        if modifier.condition and not _check_condition(modifier.condition, context):
            continue

        if modifier.operation == "ignore_modifiers":
            ignore_numeric_modifiers = True
        elif modifier.operation == "add":
            total_delta += int(modifier.value)
        elif modifier.operation == "subtract":
            total_delta -= int(modifier.value)
        elif modifier.operation == "sustained_hits":
            result.extra_rolls = max(result.extra_rolls, int(modifier.value))
        elif modifier.operation in {"lethal_hits", "auto_hit", "auto_wound"}:
            result.auto_success = True
        elif modifier.operation == "devastating_wounds":
            result.ignore_save = True
        elif modifier.operation in {
            "reroll_all",
            "reroll_hits",
            "reroll_wounds",
            "reroll_saves",
            "reroll_ones",
            "reroll_ones_hit",
            "reroll_ones_wound",
        }:
            reroll = True

    if ignore_numeric_modifiers:
        total_delta = 0

    if step in ("hit_roll", "wound_roll"):
        total_delta = max(-1, min(1, total_delta))

    # 40k rule: "+1 to hit" means target 4+ → 3+ (easier).
    # So modifiers are SUBTRACTED from the base target value.
    result.target_value = max(2, min(6, base_target - total_delta))
    result.reroll = reroll
    return result


def _check_condition(condition: dict[str, Any], context: ModifierContext) -> bool:
    """Check whether a conditional modifier is active in the current context."""
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


def build_weapon_modifiers(weapon: Any) -> list[Modifier]:
    """Build combat modifiers from weapon tags."""
    modifiers: list[Modifier] = []
    for tag in getattr(weapon, "tags", []):
        if tag == "torrent":
            modifiers.append(Modifier("hit_roll", "auto_hit", source="wargear"))
        elif tag == "heavy":
            modifiers.append(
                Modifier(
                    "hit_roll",
                    "add",
                    1,
                    source="wargear",
                    condition={"stationary": True},
                )
            )
        elif tag == "twin-linked":
            modifiers.append(Modifier("wound_roll", "reroll_wounds", source="wargear"))
        elif tag.startswith("sustained_hits_"):
            value = int(tag.rsplit("_", 1)[1])
            modifiers.append(Modifier("hit_roll", "sustained_hits", value, source="wargear"))
        elif tag == "lethal_hits":
            modifiers.append(Modifier("hit_roll", "lethal_hits", source="wargear"))
        elif tag == "devastating_wounds":
            modifiers.append(Modifier("wound_roll", "devastating_wounds", source="wargear"))
        elif tag == "ignores_cover":
            modifiers.append(Modifier("save_roll", "ignore_cover", source="wargear"))
    return modifiers


def should_reroll(
    roll: int,
    target: int,
    modifiers: list[Modifier],
    step: TargetStep,
) -> bool:
    """Return whether the roll should be rerolled."""
    del target

    for modifier in modifiers:
        if modifier.target != step:
            continue
        if modifier.operation == "reroll_all":
            return True
        if modifier.operation == "reroll_ones" and roll == 1:
            return True
        if modifier.operation == "reroll_hits" and step == "hit_roll":
            return True
        if modifier.operation == "reroll_wounds" and step == "wound_roll":
            return True
        if modifier.operation == "reroll_saves" and step == "save_roll":
            return True
        if modifier.operation == "reroll_ones_hit" and step == "hit_roll" and roll == 1:
            return True
        if modifier.operation == "reroll_ones_wound" and step == "wound_roll" and roll == 1:
            return True
    return False
