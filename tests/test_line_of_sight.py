"""Test the Line of Sight calculations."""

import pytest

from backend.state.line_of_sight import LineOfSightCalculator, calculate_angle, get_positions_in_arc
from backend.state.map import BattlefieldMap, TerrainType


def test_line_of_sight_calculator_creation():
    """Test LoS calculator initialization."""
    battlefield = BattlefieldMap.create_empty(6, 4)
    los_calc = LineOfSightCalculator(battlefield)

    assert los_calc.battlefield == battlefield


def test_clear_line_of_sight():
    """Test line of sight in open terrain."""
    battlefield = BattlefieldMap.create_empty(6, 4)
    los_calc = LineOfSightCalculator(battlefield)

    # Adjacent positions
    assert los_calc.has_line_of_sight((0, 0), (1, 0))
    assert los_calc.has_line_of_sight((0, 0), (0, 1))

    # Diagonal
    assert los_calc.has_line_of_sight((0, 0), (2, 2))

    # Same position
    assert los_calc.has_line_of_sight((1, 1), (1, 1))


def test_blocked_line_of_sight():
    """Test line of sight blocked by terrain."""
    battlefield = BattlefieldMap.create_empty(6, 4)
    los_calc = LineOfSightCalculator(battlefield)

    # Place impassable terrain
    battlefield.set_terrain(2, 1, TerrainType.IMPASSABLE)

    # Direct line should be blocked
    assert not los_calc.has_line_of_sight((1, 0), (3, 2))

    # But adjacent positions still work
    assert los_calc.has_line_of_sight((1, 0), (2, 0))


def test_line_of_sight_boundaries():
    """Test line of sight at map boundaries."""
    battlefield = BattlefieldMap.create_empty(6, 4)
    los_calc = LineOfSightCalculator(battlefield)

    # Valid positions
    assert los_calc.has_line_of_sight((0, 0), (5, 3))

    # Invalid end position
    assert not los_calc.has_line_of_sight((0, 0), (6, 4))


def test_visibility_distance():
    """Test visibility distance calculation."""
    battlefield = BattlefieldMap.create_empty(6, 4)
    los_calc = LineOfSightCalculator(battlefield)

    visible = los_calc.get_visibility_distance((2, 1), max_distance=3)

    # Should include positions within range
    assert (2, 1) not in visible  # Exclude self
    assert len(visible) > 0

    # Check some specific positions
    assert (2, 2) in visible  # Adjacent
    assert (5, 1) in visible  # Within range

    # Too far
    assert (5, 3) not in visible


def test_shooting_capability():
    """Test shooting capability checks."""
    battlefield = BattlefieldMap.create_empty(6, 4)
    los_calc = LineOfSightCalculator(battlefield)

    # Within range and LoS
    assert los_calc.can_shoot_at((0, 0), (3, 0), weapon_range=6)

    # Out of range
    assert not los_calc.can_shoot_at((0, 0), (5, 3), weapon_range=3)

    # Blocked LoS
    battlefield.set_terrain(2, 0, TerrainType.IMPASSABLE)
    assert not los_calc.can_shoot_at((0, 0), (4, 0), weapon_range=6)


def test_charge_capability():
    """Test charge capability checks."""
    battlefield = BattlefieldMap.create_empty(6, 4)
    los_calc = LineOfSightCalculator(battlefield)

    # Valid charge
    assert los_calc.can_charge_at((0, 0), (2, 1), max_charge_distance=12)

    # Too far
    assert not los_calc.can_charge_at((0, 0), (5, 3), max_charge_distance=3)

    # Blocked by terrain
    battlefield.set_terrain(1, 1, TerrainType.IMPASSABLE)
    assert not los_calc.can_charge_at((0, 0), (2, 2), max_charge_distance=12)


def test_cells_along_line():
    """Test cell calculation along a line."""
    battlefield = BattlefieldMap.create_empty(6, 4)
    los_calc = LineOfSightCalculator(battlefield)

    # Horizontal line
    cells = los_calc._get_cells_along_line((0, 0), (3, 0))
    assert (0, 0) in cells
    assert (1, 0) in cells
    assert (2, 0) in cells
    assert (3, 0) in cells

    # Diagonal line
    cells = los_calc._get_cells_along_line((0, 0), (2, 2))
    assert (0, 0) in cells
    assert (1, 1) in cells
    assert (2, 2) in cells


def test_cover_status():
    """Test cover status determination."""
    battlefield = BattlefieldMap.create_empty(6, 4)
    los_calc = LineOfSightCalculator(battlefield)

    # No cover in open terrain
    assert los_calc.get_cover_status((0, 0), (3, 0)) == "none"

    # Add difficult terrain
    battlefield.set_terrain(1, 0, TerrainType.DIFFICULT_TERRAIN)
    battlefield.set_terrain(2, 0, TerrainType.DIFFICULT_TERRAIN)

    # Should provide partial cover
    cover = los_calc.get_cover_status((0, 0), (3, 0))
    assert cover in ["partial", "full"]  # Depending on exact calculation


def test_optimal_firing_position():
    """Test finding optimal firing position."""
    battlefield = BattlefieldMap.create_empty(6, 4)
    los_calc = LineOfSightCalculator(battlefield)

    # Place target at center
    target_pos = (3, 2)
    current_pos = (0, 0)

    # Find best position within range 4
    best_pos = los_calc.get_optimal_firing_position(
        target_pos, weapon_range=4, current_pos=current_pos
    )

    assert best_pos is not None
    distance_to_target = battlefield.calculate_distance(best_pos, target_pos)
    assert distance_to_target <= 4

    # Should have LoS
    assert los_calc.has_line_of_sight(best_pos, target_pos)


def test_angle_calculation():
    """Test angle calculation between positions."""
    # Right (0 degrees)
    angle = calculate_angle((0, 0), (1, 0))
    assert abs(angle - 0) < 0.1

    # Up (90 degrees)
    angle = calculate_angle((0, 0), (0, 1))
    assert abs(angle - 90) < 0.1

    # Left (180 degrees)
    angle = calculate_angle((0, 0), (-1, 0))
    assert abs(angle - 180) < 0.1

    # Down (-90 degrees)
    angle = calculate_angle((0, 0), (0, -1))
    assert abs(angle + 90) < 0.1


def test_positions_in_arc():
    """Test getting positions within an arc."""
    center = (2, 2)
    positions = get_positions_in_arc(center, radius=2, start_angle=0, arc_angle=90)

    # Should include positions in the first quadrant (0-90 degrees: East to North)
    assert (3, 2) in positions  # East (0 degrees)
    assert (2, 3) in positions  # North (90 degrees)
    assert (3, 3) in positions  # Northeast (45 degrees)

    # Should not include positions outside arc
    assert (1, 2) not in positions  # West (180 degrees)
    assert (2, 1) not in positions  # South (270 degrees)

    # Should not include positions outside radius
    assert (5, 2) not in positions  # Too far east
    assert (2, 5) not in positions  # Too far north
