"""Modifier system for combat resolution steps."""

import re
from dataclasses import dataclass
from typing import Any, Literal

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
    "blast_bonus",
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
    has_cover: bool = False
    ignores_cover: bool = False


@dataclass
class ModifierResult:
    target_value: int
    extra_rolls: int = 0
    auto_success: bool = False
    ignore_save: bool = False
    reroll: bool = False


@dataclass
class CriticalEffect:
    auto_wound: bool = False
    extra_attacks: int = 0
    ignore_save: bool = False


@dataclass
class AntiKeyword:
    threshold: int
    target_keyword: str


TAG_TO_MODIFIERS: dict[str, list[Modifier]] = {
    "torrent": [
        Modifier("hit_roll", "auto_hit", source="wargear"),
    ],
    "heavy": [
        Modifier("hit_roll", "add", 1, source="wargear", condition={"stationary": True}),
    ],
    "sustained_hits_1": [
        Modifier("hit_roll", "sustained_hits", 1, source="wargear"),
    ],
    "sustained_hits_2": [
        Modifier("hit_roll", "sustained_hits", 2, source="wargear"),
    ],
    "sustained_hits_3": [
        Modifier("hit_roll", "sustained_hits", 3, source="wargear"),
    ],
    "lethal_hits": [
        Modifier("hit_roll", "lethal_hits", source="wargear"),
    ],
    "twin-linked": [
        Modifier("wound_roll", "reroll_wounds", source="wargear"),
    ],
    "twin_linked": [
        Modifier("wound_roll", "reroll_wounds", source="wargear"),
    ],
    "devastating_wounds": [
        Modifier("wound_roll", "devastating_wounds", source="wargear"),
    ],
    "ignores_cover": [
        Modifier("save_roll", "ignore_cover", source="wargear"),
    ],
    "lance": [
        Modifier("wound_roll", "add", 1, source="wargear", condition={"has_charged": True}),
    ],
    "precision": [
        Modifier("allocation", "precision", source="wargear"),
    ],
    "blast": [
        Modifier("attack_count", "blast_bonus", source="wargear"),
    ],
    "rapid_fire_1": [
        Modifier("attack_count", "add", 1, source="wargear", condition={"half_range": True}),
    ],
    "rapid_fire_2": [
        Modifier("attack_count", "add", 2, source="wargear", condition={"half_range": True}),
    ],
    "melta_1": [
        Modifier("damage", "add", 1, source="wargear", condition={"half_range": True}),
    ],
    "melta_2": [
        Modifier("damage", "add", 2, source="wargear", condition={"half_range": True}),
    ],
    "melta_3": [
        Modifier("damage", "add", 3, source="wargear", condition={"half_range": True}),
    ],
    "pistol": [
        Modifier("eligibility", "pistol", source="wargear"),
    ],
}


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
        elif modifier.operation == "blast_bonus":
            blast_bonus = min(4, context.squad_size // 5)
            total_delta += blast_bonus
        elif modifier.operation in {"auto_hit", "auto_wound"}:
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

    if step in ("hit_roll", "wound_roll", "save_roll", "fnp_roll"):
        result.target_value = max(2, min(6, base_target - total_delta))
    else:
        result.target_value = max(0, base_target + total_delta)
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

    if condition.get("has_charged"):
        attacker_state = getattr(context.attacker, "unit_state", None)
        if attacker_state is None or not getattr(attacker_state, "has_charged", False):
            return False

    squad_size_min = condition.get("squad_size_min")
    return not (squad_size_min is not None and context.squad_size < squad_size_min)


def build_weapon_modifiers(weapon: Any) -> list[Modifier]:
    """Build combat modifiers from weapon tags."""
    modifiers: list[Modifier] = []
    for tag in getattr(weapon, "tags", []):
        modifiers.extend(TAG_TO_MODIFIERS.get(tag, []))
    return modifiers


def handle_critical_hit(
    roll_result: Any,
    step: str,
    modifiers: list[Modifier],
    context: ModifierContext | None,
) -> CriticalEffect:
    """Resolve critical hit or wound side effects."""
    del context

    if step == "hit_roll" and roll_result.is_crit:
        has_lethal = any(
            modifier.target == "hit_roll" and modifier.operation == "lethal_hits"
            for modifier in modifiers
        )
        sustained_count = max(
            (
                int(modifier.value)
                for modifier in modifiers
                if modifier.target == "hit_roll" and modifier.operation == "sustained_hits"
            ),
            default=0,
        )
        return CriticalEffect(auto_wound=has_lethal, extra_attacks=sustained_count)

    if step == "wound_roll" and roll_result.is_crit:
        has_devastating = any(
            modifier.target == "wound_roll" and modifier.operation == "devastating_wounds"
            for modifier in modifiers
        )
        return CriticalEffect(ignore_save=has_devastating)

    return CriticalEffect()


def parse_anti_tag(tag: str) -> AntiKeyword | None:
    """Parse anti-keyword tags like anti_infantry_4."""
    match = re.fullmatch(r"anti_(\w+)_(\d+)", tag)
    if not match:
        return None
    return AntiKeyword(
        threshold=int(match.group(2)),
        target_keyword=match.group(1).replace("_", " ").title(),
    )


def resolve_anti_wound(
    roll: int,
    anti: AntiKeyword,
    defender: Any,
) -> bool:
    """Return whether the wound roll counts as a critical wound via anti-keyword."""
    defender_keywords = {keyword.lower() for keyword in getattr(defender, "keywords", [])}
    target_keyword = anti.target_keyword.lower()
    return target_keyword in defender_keywords and roll >= anti.threshold


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
