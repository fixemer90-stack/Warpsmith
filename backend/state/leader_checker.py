"""Leader compatibility checking for Warhammer 40k roster building."""

from dataclasses import dataclass, field
from typing import Optional, List

from backend.model.unit import Unit


@dataclass
class LeaderCompatibilityResult:
    """Result of leader compatibility check."""
    is_compatible: bool
    issues: List[str] = field(default_factory=list)

    @classmethod
    def ok(cls) -> "LeaderCompatibilityResult":
        return cls(is_compatible=True)

    @classmethod
    def fail(cls, *issues: str) -> "LeaderCompatibilityResult":
        return cls(is_compatible=False, issues=list(issues))


def check_leader_compatibility(
    leader: Unit,
    target_unit: Unit,
    existing_leaders: Optional[List[Unit]] = None,
) -> LeaderCompatibilityResult:
    """Проверить, может ли лидер присоединиться к отряду.

    Args:
        leader: The leader unit attempting to attach
        target_unit: The unit the leader wants to join
        existing_leaders: List of leaders already attached to target_unit

    Returns:
        LeaderCompatibilityResult indicating compatibility and any issues
    """
    if existing_leaders is None:
        existing_leaders = []

    # Rule 1: Leader must have is_leader=True
    if not leader.is_leader:
        return LeaderCompatibilityResult.fail(
            f"{leader.name} is not a leader"
        )

    # Rule 2: Target must be in leader.leader_for list
    if not _is_compatible_unit(leader, target_unit):
        return LeaderCompatibilityResult.fail(
            f"{leader.name} cannot lead {target_unit.name}"
        )

    # Rule 3: Max 2 leaders per unit (Captain + Lieutenant rule)
    if existing_leaders and len(existing_leaders) >= 2:
        return LeaderCompatibilityResult.fail(
            f"Max 2 leaders per unit (already has {len(existing_leaders)})"
        )

    # Rule 4: Only 1 "Captain" type leader (not both can lead)
    if existing_leaders:
        leader_types = {_get_leader_type(l) for l in existing_leaders}
        new_type = _get_leader_type(leader)
        if new_type in leader_types:
            return LeaderCompatibilityResult.fail(
                f"{leader.name} cannot join: unit already has a {new_type}"
            )

    return LeaderCompatibilityResult.ok()


def _is_compatible_unit(leader: Unit, target: Unit) -> bool:
    """Проверка leader_for списка.

    Args:
        leader: The leader unit
        target: The target unit to check compatibility with

    Returns:
        True if leader can lead target unit, False otherwise
    """
    for allowed in leader.leader_for:
        if allowed == target.name:
            return True
        # Wildcard: "BATTLELINE" keyword
        if allowed.upper() == "BATTLELINE" and "Battleline" in target.keywords:
            return True
        if allowed.upper() == "INFANTRY" and "Infantry" in target.keywords:
            return True
    return False


def _get_leader_type(leader: Unit) -> str:
    """Определить тип лидера (Captain / Lieutenant / Other).

    Args:
        leader: The leader unit to classify

    Returns:
        String indicating leader type: "captain", "lieutenant", or "other"
    """
    name_lower = leader.name.lower()
    if "captain" in name_lower:
        return "captain"
    if "lieutenant" in name_lower:
        return "lieutenant"
    return "other"


def validate_leader_assignments(
    roster_units: List[tuple[Unit, int]],
) -> List[LeaderCompatibilityResult]:
    """Валидация всех привязок лидеров в ростере.

    Args:
        roster_units: List of (unit, squad_size) tuples representing the roster

    Returns:
        List of LeaderCompatibilityResult for each leader assignment issue
    """
    results = []
    leaders_by_unit: dict[str, List[Unit]] = {}

    # Group leaders by their target unit (simplified: assume they attach to first suitable non-leader unit)
    for unit, squad_size in roster_units:
        if unit.is_leader:
            # Find the first non-leader unit that this leader could lead
            for target_unit, target_squad_size in roster_units:
                if not target_unit.is_leader and _is_compatible_unit(unit, target_unit):
                    target_name = target_unit.name
                    if target_name not in leaders_by_unit:
                        leaders_by_unit[target_name] = []
                    leaders_by_unit[target_name].append(unit)
                    break

    # Check each group of leader->bodyguard
    for unit_name, attached_leaders in leaders_by_unit.items():
        bodyguard = _find_unit(unit_name, roster_units)
        if not bodyguard:
            continue
        for leader in attached_leaders:
            # Exclude the current leader from existing_leaders when checking compatibility
            existing_leaders = [l for l in attached_leaders if l != leader]
            result = check_leader_compatibility(leader, bodyguard, existing_leaders)
            if not result.is_compatible:
                results.append(result)

    return results


def _find_unit(unit_name: str, roster_units: List[tuple[Unit, int]]) -> Optional[Unit]:
    """Find a unit by name in the roster."""
    for unit, _ in roster_units:
        if unit.name == unit_name:
            return unit
    return None


def get_leader_hints(unit: Unit, all_units: dict[str, Unit]) -> List[str]:
    """Подсказка: какие лидеры подходят к юниту.

    Args:
        unit: The unit to find compatible leaders for
        all_units: Dictionary of all available units by name

    Returns:
        List of hint strings indicating which leaders can lead this unit
    """
    hints = []
    for name, candidate in all_units.items():
        if not candidate.is_leader:
            continue
        if _is_compatible_unit(candidate, unit):
            hints.append(f"{candidate.name} can lead this unit")
    return hints