"""Validation and coercion helpers for wiki frontmatter.

Includes content.v1 canonical schema contracts (Task 1.1).
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator


# ── Coercion helpers ────────────────────────────────────────────────────


def parse_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, str) and value.strip().lower() in {"", "none", "-"}:
        return None
    return int(str(value).replace("+", "").strip())


def parse_model_count(value: Any) -> tuple[int, int]:
    if isinstance(value, tuple) and len(value) == 2:
        return (int(value[0]), int(value[1]))
    if isinstance(value, list) and len(value) == 2:
        return (int(value[0]), int(value[1]))
    if isinstance(value, str):
        normalized = value.replace(" ", "")
        if "-" in normalized:
            min_count, max_count = normalized.split("-", 1)
            return (int(min_count), int(max_count))
        count = int(normalized)
        return (count, count)
    return (1, 1)


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


# ── content.v1 canonical schema (Task 1.1) ─────────────────────────────


class WeaponV1(BaseModel):
    """Canonical weapon record — content.v1 schema."""

    name: str = Field(min_length=1)
    type: str = Field(pattern="^(ranged|melee)$")
    range_max: int | None = None
    attacks_dice: tuple[int, int, int] = Field(default=(1, 6, 0))
    skill: int = Field(ge=2, le=6)
    strength: int = Field(ge=0)
    ap: int = Field(ge=-6, le=6)
    damage_dice: tuple[int, int, int] = Field(default=(1, 3, 0))
    tags: list[str] = Field(default_factory=list)
    abilities: list[str] = Field(default_factory=list)


class UnitV1(BaseModel):
    """Canonical unit record — content.v1 schema.

    All required gameplay fields are present.  Missing/zero values must
    be explicit in the source, not silently defaulted by the parser.
    """

    name: str = Field(min_length=1)
    faction: str = Field(min_length=1)
    category: str = Field(min_length=1)
    movement: int = Field(ge=0)
    toughness: int = Field(ge=1)
    save: int = Field(ge=2, le=7)
    wounds: int = Field(ge=1)
    leadership: int = Field(ge=2, le=12)
    objective_control: int = Field(ge=0)
    points: int = Field(ge=0)
    model_count: tuple[int, int] = Field(default=(1, 1))
    squad_size: dict[str, int] = Field(
        default_factory=lambda: {"min": 1, "max": 1, "step": 1}
    )
    ranged_weapons: list[WeaponV1] = Field(default_factory=list)
    melee_weapons: list[WeaponV1] = Field(default_factory=list)
    abilities: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    faction_keywords: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    invulnerable_save: int | None = Field(default=None, ge=3, le=7)
    feel_no_pain: int | None = Field(default=None, ge=4, le=6)
    is_epic_hero: bool = False
    can_be_warlord: bool = False
    is_leader: bool = False
    leader_for: list[str] = Field(default_factory=list)
    edition: str = "10e"

    @field_validator("model_count")
    @classmethod
    def model_count_valid(cls, v: tuple[int, int]) -> tuple[int, int]:
        if v[0] < 1:
            raise ValueError(f"model_count min={v[0]} must be >= 1")
        if v[0] > v[1]:
            raise ValueError(f"model_count min={v[0]} > max={v[1]}")
        return v

    @field_validator("squad_size")
    @classmethod
    def squad_size_valid(cls, v: dict[str, int]) -> dict[str, int]:
        min_s = v.get("min", 1)
        max_s = v.get("max", 1)
        step = v.get("step", 1)
        if min_s < 1 or max_s < 1 or step < 1:
            raise ValueError("squad_size min/max/step must be >= 1")
        if min_s > max_s:
            raise ValueError(f"squad_size min={min_s} > max={max_s}")
        return v


def validate_unit_v1(unit: Any) -> UnitV1:
    """Validate a runtime Unit object against the content.v1 schema.

    Returns a validated UnitV1 record or raises ValidationError.
    """
    weapons_ranged = [
        WeaponV1(
            name=w.name,
            type=w.type,
            range_max=w.range_max,
            attacks_dice=w.attacks_dice,
            skill=w.skill,
            strength=w.strength,
            ap=w.ap,
            damage_dice=w.damage_dice,
            tags=getattr(w, "tags", []) or [],
            abilities=getattr(w, "abilities", []) or [],
        )
        for w in (getattr(unit, "ranged_weapons", []) or [])
    ]
    weapons_melee = [
        WeaponV1(
            name=w.name,
            type=w.type,
            range_max=w.range_max,
            attacks_dice=w.attacks_dice,
            skill=w.skill,
            strength=w.strength,
            ap=w.ap,
            damage_dice=w.damage_dice,
            tags=getattr(w, "tags", []) or [],
            abilities=getattr(w, "abilities", []) or [],
        )
        for w in (getattr(unit, "melee_weapons", []) or [])
    ]

    return UnitV1(
        name=unit.name,
        faction=unit.faction,
        category=unit.category,
        movement=unit.movement,
        toughness=unit.toughness,
        save=unit.save,
        wounds=unit.wounds,
        leadership=unit.leadership,
        objective_control=unit.objective_control,
        points=unit.points,
        model_count=unit.model_count,
        squad_size=getattr(unit, "squad_size", {"min": 1, "max": 1, "step": 1}),
        ranged_weapons=weapons_ranged,
        melee_weapons=weapons_melee,
        abilities=getattr(unit, "abilities", []) or [],
        keywords=getattr(unit, "keywords", []) or [],
        faction_keywords=getattr(unit, "faction_keywords", []) or [],
        tags=getattr(unit, "tags", []) or [],
        invulnerable_save=getattr(unit, "invulnerable_save", None),
        feel_no_pain=getattr(unit, "feel_no_pain", None),
        is_epic_hero=getattr(unit, "is_epic_hero", False),
        can_be_warlord=getattr(unit, "can_be_warlord", False),
        is_leader=getattr(unit, "is_leader", False),
        leader_for=getattr(unit, "leader_for", []) or [],
        edition=getattr(unit, "edition", "10e"),
    )
