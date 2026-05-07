"""Line of Sight (LoS) calculations using ray casting."""

import math

from backend.state.map import BattlefieldMap, TerrainType


class LineOfSightCalculator:
    """Calculates line of sight between positions on the battlefield."""

    def __init__(self, battlefield: BattlefieldMap):
        self.battlefield = battlefield

    def has_line_of_sight(
        self, start: tuple[int, int], end: tuple[int, int], ignore_units: bool = True
    ) -> bool:
        """
        Check if there's a clear line of sight between two positions.

        Args:
            start: Starting position (x, y)
            end: Ending position (x, y)
            ignore_units: If True, ignore unit positions (only check terrain)

        Returns:
            True if line of sight is clear, False if blocked
        """
        if start == end:
            return True

        # Get all cells along the line
        cells = self._get_cells_along_line(start, end)

        # Remove start position from check
        cells = cells[1:]

        # Check each cell for blocking terrain
        for cell_x, cell_y in cells:
            if not self.battlefield._is_valid_position(cell_x, cell_y):
                return False

            terrain = self.battlefield.get_terrain(cell_x, cell_y)
            if terrain == TerrainType.IMPASSABLE:
                return False

            # Difficult terrain partially blocks LoS
            if terrain == TerrainType.DIFFICULT_TERRAIN:
                # In Warhammer 40k, difficult terrain doesn't block LoS
                # but we might want to add this as a configurable option
                pass

        return True

    def get_visibility_distance(
        self, position: tuple[int, int], max_distance: int = 12
    ) -> list[tuple[int, int]]:
        """
        Get all positions visible from the given position within max_distance.

        Args:
            position: Starting position (x, y)
            max_distance: Maximum distance to check (in inches, Warhammer scale)

        Returns:
            List of visible positions (x, y)
        """
        visible_positions = []

        start_x, start_y = position

        # Check all positions within max_distance
        for x in range(
            max(start_x - max_distance, 0), min(start_x + max_distance + 1, self.battlefield.width)
        ):
            for y in range(
                max(start_y - max_distance, 0),
                min(start_y + max_distance + 1, self.battlefield.height),
            ):
                if (x, y) == position:
                    continue

                distance = self.battlefield.calculate_distance(position, (x, y))

                if distance <= max_distance and self.has_line_of_sight(position, (x, y)):
                    visible_positions.append((x, y))

        return visible_positions

    def can_shoot_at(
        self, shooter_pos: tuple[int, int], target_pos: tuple[int, int], weapon_range: int
    ) -> bool:
        """
        Check if a shooter can shoot at a target position.

        Args:
            shooter_pos: Position of the shooter (x, y)
            target_pos: Position of the target (x, y)
            weapon_range: Maximum range of the weapon (in inches)

        Returns:
            True if shooting is possible
        """
        distance = self.battlefield.calculate_distance(shooter_pos, target_pos)

        if distance > weapon_range:
            return False

        return self.has_line_of_sight(shooter_pos, target_pos)

    def can_charge_at(
        self,
        charger_pos: tuple[int, int],
        target_pos: tuple[int, int],
        max_charge_distance: int = 12,
    ) -> bool:
        """
        Check if a unit can charge to a target position.

        Args:
            charger_pos: Position of the charging unit (x, y)
            target_pos: Position of the target (x, y)
            max_charge_distance: Maximum charge distance (usually 12")

        Returns:
            True if charging is possible
        """
        distance = self.battlefield.calculate_distance(charger_pos, target_pos)

        if distance > max_charge_distance:
            return False

        # For charges, we need to check if the path is clear of impassable terrain
        # but units can be charged through (unlike shooting)
        return self.has_line_of_sight(charger_pos, target_pos, ignore_units=True)

    def _get_cells_along_line(
        self, start: tuple[int, int], end: tuple[int, int]
    ) -> list[tuple[int, int]]:
        """
        Get all grid cells that a line between two points passes through.
        Uses Bresenham's line algorithm adapted for grid-based LoS.

        Args:
            start: Starting position (x, y)
            end: Ending position (x, y)

        Returns:
            List of cells (x, y) along the line
        """
        x1, y1 = start
        x2, y2 = end

        cells = []

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)

        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1

        err = dx - dy

        while True:
            cells.append((x1, y1))

            if x1 == x2 and y1 == y2:
                break

            e2 = 2 * err

            if e2 > -dy:
                err -= dy
                x1 += sx

            if e2 < dx:
                err += dx
                y1 += sy

        return cells

    def get_cover_status(self, unit_pos: tuple[int, int], enemy_pos: tuple[int, int]) -> str:
        """
        Determine cover status for shooting from unit_pos to enemy_pos.

        Args:
            unit_pos: Position of the unit seeking cover (x, y)
            enemy_pos: Position of the enemy (x, y)

        Returns:
            "none", "partial", or "full" cover status
        """
        if not self.has_line_of_sight(unit_pos, enemy_pos):
            return "full"  # No LoS means full cover

        # Check for terrain between positions that could provide cover
        cells = self._get_cells_along_line(unit_pos, enemy_pos)
        cover_cells = 0
        total_cells = len(cells)

        for cell_x, cell_y in cells:
            if (cell_x, cell_y) in [unit_pos, enemy_pos]:
                continue

            terrain = self.battlefield.get_terrain(cell_x, cell_y)
            if terrain in [TerrainType.DIFFICULT_TERRAIN, TerrainType.DANGEROUS_TERRAIN]:
                cover_cells += 1

        # Simple cover calculation
        cover_ratio = cover_cells / max(1, total_cells)
        if cover_ratio >= 0.5:
            return "full"
        elif cover_ratio >= 0.25:
            return "partial"
        else:
            return "none"

    def get_optimal_firing_position(
        self, target_pos: tuple[int, int], weapon_range: int, current_pos: tuple[int, int]
    ) -> tuple[int, int] | None:
        """
        Find the optimal firing position within weapon range of target.

        Args:
            target_pos: Position of the target (x, y)
            weapon_range: Maximum weapon range
            current_pos: Current position of the shooter (x, y)

        Returns:
            Best firing position (x, y) or None if no valid position found
        """
        target_x, target_y = target_pos
        _current_x, _current_y = current_pos

        # Look for positions within range that have LoS
        best_pos = None
        best_distance = float("inf")

        for dx in range(-weapon_range, weapon_range + 1):
            for dy in range(-weapon_range, weapon_range + 1):
                if dx == 0 and dy == 0:
                    continue

                pos_x = target_x + dx
                pos_y = target_y + dy

                if not self.battlefield._is_valid_position(pos_x, pos_y):
                    continue

                distance_to_target = self.battlefield.calculate_distance((pos_x, pos_y), target_pos)
                if distance_to_target > weapon_range:
                    continue

                if self.has_line_of_sight((pos_x, pos_y), target_pos):
                    distance_from_current = self.battlefield.calculate_distance(
                        (pos_x, pos_y), current_pos
                    )
                    if distance_from_current < best_distance:
                        best_distance = distance_from_current
                        best_pos = (pos_x, pos_y)

        return best_pos


# Utility functions
def calculate_angle(start: tuple[int, int], end: tuple[int, int]) -> float:
    """Calculate angle in degrees between two positions."""
    x1, y1 = start
    x2, y2 = end
    return math.degrees(math.atan2(y2 - y1, x2 - x1))


def get_positions_in_arc(
    center: tuple[int, int], radius: int, start_angle: float, arc_angle: float
) -> list[tuple[int, int]]:
    """
    Get all positions within an arc from center position.

    Args:
        center: Center position (x, y)
        radius: Radius of the arc
        start_angle: Starting angle in degrees (0 = East, 90 = North)
        arc_angle: Arc angle in degrees (width of the arc)

    Returns:
        List of positions within the arc
    """
    positions = []
    cx, cy = center

    for x in range(cx - radius, cx + radius + 1):
        for y in range(cy - radius, cy + radius + 1):
            distance = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            if distance <= radius and distance > 0:
                angle = calculate_angle(center, (x, y))
                # Normalize angle to 0-360
                angle = angle % 360
                # Check if angle is within the arc
                angle_diff = (angle - start_angle) % 360
                if angle_diff <= arc_angle:
                    positions.append((x, y))

    return positions
