"""Data models for WH40k units, weapons, and abilities."""

import re
from dataclasses import dataclass, field
from typing import Literal, Optional

import numpy as np

DiceExpr = tuple[int, int, int]


def parse_dice_expression(expr: str) -> DiceExpr:
    """Parse a dice expression into (num_dice, sides, bonus)."""
    normalized = expr.strip()
    match = re.fullmatch(r"(?:(\d+))?[Dd](\d+)(?:\s*\+\s*(\d+))?", normalized)
    if match:
        num_dice = int(match.group(1)) if match.group(1) else 1
        sides = int(match.group(2))
        bonus = int(match.group(3)) if match.group(3) else 0
        return (num_dice, sides, bonus)

    fixed_match = re.fullmatch(r"(\d+)", normalized)
    if fixed_match:
        return (0, 0, int(fixed_match.group(1)))

    return (0, 0, 0)


def resolve_dice(dice: DiceExpr, rng: np.random.Generator) -> int:
    """Resolve a DiceExpr to an integer using the supplied RNG."""
    num_dice, sides, bonus = dice
    if num_dice == 0:
        return bonus
    total = int(rng.integers(1, sides + 1, size=num_dice).sum())
    return total + bonus


def dice_expr_to_str(dice: DiceExpr) -> str:
    num_dice, sides, bonus = dice
    if num_dice == 0:
        return str(bonus)
    base = f"{num_dice if num_dice > 1 else ''}D{sides}"
    return f"{base}+{bonus}" if bonus else base


@dataclass
class Weapon:
    name: str
    type: Literal["ranged", "melee"]
    range_max: int | None
    attacks_dice: DiceExpr
    skill: int
    strength: int
    ap: int
    damage_dice: DiceExpr
    tags: list[str] = field(default_factory=list)
    abilities: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.type == "melee" and self.range_max is not None:
            msg = "melee weapons must not define range_max"
            raise ValueError(msg)
        if self.type == "ranged" and self.range_max is not None and self.range_max < 0:
            msg = "range_max must be non-negative"
            raise ValueError(msg)
        if self.skill < 2 or self.skill > 6:
            msg = "skill must be between 2 and 6"
            raise ValueError(msg)
        if self.strength < 0:
            msg = "strength must be non-negative"
            raise ValueError(msg)


@dataclass
class WargearSlot:
    slot_name: str
    choices: list[str]
    default_index: int = 0

    def __post_init__(self) -> None:
        if not self.choices:
            msg = "choices must not be empty"
            raise ValueError(msg)
        if not 0 <= self.default_index < len(self.choices):
            msg = "default_index must reference an existing choice"
            raise ValueError(msg)


@dataclass
class Unit:
    name: str
    faction: str
    category: str  # Character, Battleline, Vehicle, Infantry, etc.
    movement: int  # M — Movement in inches
    toughness: int  # T
    save: int  # SV — Save (e.g. 3 means 3+)
    wounds: int  # W
    leadership: int  # LD (e.g. 6 means 6+)
    objective_control: int  # OC
    ranged_weapons: list[Weapon] = field(default_factory=list)
    melee_weapons: list[Weapon] = field(default_factory=list)
    abilities: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    faction_keywords: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    points: int = 0
    model_count: tuple[int, int] = (1, 1)  # (min, max) models per unit
    invulnerable_save: int | None = None  # 4 means 4++
    feel_no_pain: int | None = None  # 5 means 5+++
    wargear_options: list[WargearSlot] = field(default_factory=list)
    transports: list[str] = field(default_factory=list)
    is_epic_hero: bool = False
    can_be_warlord: bool = False
    is_leader: bool = False
    leader_for: list[str] = field(default_factory=list)
    # F4.2: Extended wargear system for team builder modal
    squad_size: dict[str, int] = field(default_factory=lambda: {"min": 1, "max": 1, "step": 1})
    extended_wargear_options: list[dict] = field(default_factory=list)
    nob_options: list[dict] = field(default_factory=list)
    edition: str = "10e"

    def __post_init__(self) -> None:
        if not 2 <= self.save <= 7:
            msg = "save must be between 2 and 7"
            raise ValueError(msg)
        if self.invulnerable_save is not None and not 3 <= self.invulnerable_save <= 7:
            msg = "invulnerable_save must be between 3 and 7"
            raise ValueError(msg)
        if self.feel_no_pain is not None and not 4 <= self.feel_no_pain <= 6:
            msg = "feel_no_pain must be between 4 and 6"
            raise ValueError(msg)
        if self.movement < 0:
            msg = "movement cannot be negative"
            raise ValueError(msg)
        if self.toughness < 1:
            msg = "toughness must be at least 1"
            raise ValueError(msg)
        if self.wounds < 1:
            msg = "wounds must be at least 1"
            raise ValueError(msg)
        if self.points < 0:
            msg = "points must be at least 0"
            raise ValueError(msg)

        min_models, max_models = self.model_count
        if min_models < 1 or max_models < 1:
            msg = "model_count values must be at least 1"
            raise ValueError(msg)
        if min_models > max_models:
            msg = "model_count min must be less than or equal to max"
            raise ValueError(msg)

    def effective_toughness(self, strength: int) -> int:
        """Return the wound roll target using the Strength vs Toughness table."""
        if strength >= self.toughness * 2:
            return 2
        if strength > self.toughness:
            return 3
        if strength == self.toughness:
            return 4
        if strength * 2 <= self.toughness:
            return 6
        return 5

    def best_save(self, ap: int) -> int:
        """Return the best available save after AP is applied."""
        modified_save = self.save - ap
        if self.invulnerable_save is not None and self.invulnerable_save < modified_save:
            return self.invulnerable_save
        return max(2, min(6, modified_save))

    def max_wounds_in_squad(self, squad_size: int) -> int:
        return self.wounds * squad_size
