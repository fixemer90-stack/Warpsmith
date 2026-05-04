"""Roster validation for Warhammer 40k 10th edition.

Validates:
- PTS limit by game size (Boarding Patrol 500, Incursion 1000,
  Strike Force 2000, Onslaught 3000)
- Exactly one Warlord in roster
- Max 3 copies of non-Battleline, 6 copies of Battleline
- Unique Epic Heroes
- Squad size within unit's model_count range
- Empty roster check
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.model.unit import Unit


@dataclass
class RosterState:
    """Сохранённый ростер: данные из БД или генерации.
    Отличается от PlayerState (игровой процесс) — это просто данные."""
    name: str
    faction: str
    total_pts: int
    units: dict[str, "Unit"] = field(default_factory=dict)
    warlord_unit_name: str | None = None
    detachment: str = ""


class GameSize(Enum):
    """Standard game sizes in Warhammer 40k 10th edition."""

    COMBAT_PATROL = "combat_patrol"
    INCURSION = "incursion"
    STRIKE_FORCE = "strike_force"
    ONSLAUGHT = "onslaught"

    @property
    def pts_limit(self) -> int:
        return _GAME_SIZE_LIMITS[self]

    @property
    def label(self) -> str:
        return _GAME_SIZE_LABELS[self]


_GAME_SIZE_LIMITS: dict[GameSize, int] = {
    GameSize.COMBAT_PATROL: 500,
    GameSize.INCURSION: 1000,
    GameSize.STRIKE_FORCE: 2000,
    GameSize.ONSLAUGHT: 3000,
}

_GAME_SIZE_LABELS: dict[GameSize, str] = {
    GameSize.COMBAT_PATROL: "Combat Patrol (500pts)",
    GameSize.INCURSION: "Incursion (1000pts)",
    GameSize.STRIKE_FORCE: "Strike Force (2000pts)",
    GameSize.ONSLAUGHT: "Onslaught (3000pts)",
}


@dataclass
class RosterValidationError:
    """A single validation error with machine-readable code."""

    code: str
    message: str
    detail: dict | None = None


@dataclass
class RosterValidationResult:
    """Result of roster validation."""

    is_valid: bool = True
    errors: list[RosterValidationError] = field(default_factory=list)
    total_pts: int = 0
    total_models: int = 0

    def add_error(self, code: str, message: str, **detail) -> None:
        self.errors.append(RosterValidationError(code, message, detail or None))
        self.is_valid = False


def validate_roster(
    units: list[tuple[str, int]],
    unit_registry: dict[str, "Unit"],
    pts_limit: int | None = None,
    game_size: GameSize = GameSize.STRIKE_FORCE,
) -> RosterValidationResult:
    """Validate a roster against 10th edition rules.

    Args:
        units: List of (unit_name, squad_size) tuples.
        unit_registry: Dict mapping unit names to Unit objects.
        pts_limit: Maximum points allowed. Overrides game_size if set.
        game_size: Named game size (default Strike Force = 2000pts).
                  Ignored when pts_limit is explicitly provided.

    Returns:
        RosterValidationResult with errors if any violations found.
    """
    if pts_limit is None:
        pts_limit = game_size.pts_limit
    result = RosterValidationResult()
    counts: dict[str, int] = {}
    has_warlord = False
    total_pts = 0
    total_models = 0
    epic_heroes_seen: set[str] = set()

    for unit_name, squad_size in units:
        unit = unit_registry.get(unit_name)
        if unit is None:
            result.add_error(
                "unknown_unit",
                f"Unit '{unit_name}' not found in registry",
                unit_name=unit_name,
            )
            continue

        # Squad size validation
        squad_err = validate_squad_size(unit_name, squad_size, unit)
        if squad_err:
            result.errors.append(squad_err)
            result.is_valid = False

        # Count copies of this unit
        counts[unit_name] = counts.get(unit_name, 0) + 1

        # 3x cap (6x for Battleline)
        is_battleline = "BATTLELINE" in [kw.upper() for kw in unit.keywords]
        max_copies = 6 if is_battleline else 3
        if counts[unit_name] > max_copies:
            label = "Battleline" if is_battleline else "non-Battleline"
            result.add_error(
                "too_many_copies",
                f"Max {max_copies} copies of {unit_name} ({label})",
                unit_name=unit_name,
                max_count=max_copies,
                current_count=counts[unit_name],
            )

        # Epic Hero: unique
        if unit.is_epic_hero:
            if unit_name in epic_heroes_seen:
                result.add_error(
                    "duplicate_epic_hero",
                    f"Epic Hero '{unit_name}' can only be taken once",
                    unit_name=unit_name,
                )
            epic_heroes_seen.add(unit_name)

        # Warlord tracking
        if unit.can_be_warlord:
            has_warlord = True

        # Points
        unit_pts = unit.points * squad_size
        total_pts += unit_pts
        total_models += squad_size * unit.model_count[1]

    # PTS limit
    if total_pts > pts_limit:
        result.add_error(
            "pts_exceeded",
            f"Total {total_pts}pts exceeds limit of {pts_limit}pts",
            pts_limit=pts_limit,
            total_pts=total_pts,
        )

    # Warlord requirement
    if not has_warlord:
        result.add_error(
            "no_warlord",
            "Roster must include at least one model that can be Warlord",
        )

    # Empty roster
    if not units:
        result.add_error("empty_roster", "Roster is empty")

    result.total_pts = total_pts
    result.total_models = total_models
    return result


def validate_squad_size(
    unit_name: str,
    squad_size: int,
    unit: "Unit",
) -> RosterValidationError | None:
    """Check that squad size is within the unit's allowed range.

    Returns an error if out of range, None if valid.
    """
    min_size, max_size = unit.model_count
    if squad_size < min_size:
        return RosterValidationError(
            "squad_too_small",
            f"{unit_name}: min {min_size} models, got {squad_size}",
            detail=dict(min_size=min_size, current_size=squad_size),
        )
    if squad_size > max_size:
        return RosterValidationError(
            "squad_too_large",
            f"{unit_name}: max {max_size} models, got {squad_size}",
            detail=dict(max_size=max_size, current_size=squad_size),
        )
    return None
