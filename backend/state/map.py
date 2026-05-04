"""2D battlefield map management with terrain and deployment zones."""

from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from backend.state.game_state import TerrainType


class DeploymentType(Enum):
    """Types of deployment zones."""

    PLAYER_1 = "player_1"
    PLAYER_2 = "player_2"
    SHARED = "shared"
    OBJECTIVE = "objective"


@dataclass
class DeploymentZone:
    """A deployment zone on the battlefield."""

    name: str
    deployment_type: DeploymentType
    coordinates: set[tuple[int, int]]
    description: str = ""

    @property
    def area(self) -> int:
        """Get the area (number of cells) in this zone."""
        return len(self.coordinates)

    def contains_position(self, x: int, y: int) -> bool:
        """Check if a position is within this zone."""
        return (x, y) in self.coordinates


@dataclass
class BattlefieldMap:
    """2D representation of the Warhammer 40k battlefield."""

    width: int
    height: int
    terrain: np.ndarray
    deployment_zones: dict[str, DeploymentZone] = field(default_factory=dict)
    objectives: dict[str, tuple[int, int]] = field(default_factory=dict)
    name: str = "Standard Battlefield"

    def __post_init__(self):
        """Validate terrain array dimensions."""
        if self.terrain.shape != (self.height, self.width):
            msg = (
                f"Terrain array shape {self.terrain.shape} does not match map dimensions {self.height}x{self.width}"
            )
            raise ValueError(msg)

    @classmethod
    def create_empty(
        cls, width: int = 6, height: int = 4, name: str = "Empty Battlefield"
    ) -> "BattlefieldMap":
        """Create an empty battlefield with open ground."""
        terrain = np.full((height, width), TerrainType.OPEN_GROUND, dtype=object)
        return cls(width=width, height=height, terrain=terrain, name=name)

    @classmethod
    def create_standard(cls) -> "BattlefieldMap":
        """Create a standard 6x4 battlefield with typical terrain."""
        battlefield = cls.create_empty(6, 4, "Standard Battlefield")

        # Add terrain features
        battlefield.set_terrain(1, 2, TerrainType.DIFFICULT_TERRAIN)
        battlefield.set_terrain(2, 3, TerrainType.DIFFICULT_TERRAIN)
        battlefield.set_terrain(5, 0, TerrainType.DANGEROUS_TERRAIN)
        battlefield.set_terrain(3, 1, TerrainType.DIFFICULT_TERRAIN)

        # Add deployment zones
        battlefield.add_deployment_zone(
            "player1_deployment",
            DeploymentType.PLAYER_1,
            [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)],
            "Player 1 deployment zone",
        )

        battlefield.add_deployment_zone(
            "player2_deployment",
            DeploymentType.PLAYER_2,
            [(3, 2), (4, 2), (5, 2), (3, 3), (4, 3), (5, 3)],
            "Player 2 deployment zone",
        )

        # Add objectives
        battlefield.add_objective("objective_a", (1, 2))
        battlefield.add_objective("objective_b", (4, 1))
        battlefield.add_objective("objective_c", (2, 3))

        return battlefield

    def set_terrain(self, x: int, y: int, terrain_type: TerrainType):
        """Set terrain type at a specific position."""
        if not self._is_valid_position(x, y):
            msg = f"Position ({x}, {y}) is out of bounds"
            raise ValueError(msg)
        self.terrain[y, x] = terrain_type

    def get_terrain(self, x: int, y: int) -> TerrainType:
        """Get terrain type at a specific position."""
        if not self._is_valid_position(x, y):
            msg = f"Position ({x}, {y}) is out of bounds"
            raise ValueError(msg)
        return self.terrain[y, x]

    def add_deployment_zone(
        self,
        name: str,
        deployment_type: DeploymentType,
        coordinates: list[tuple[int, int]],
        description: str = "",
    ):
        """Add a deployment zone to the map."""
        # Validate coordinates
        for x, y in coordinates:
            if not self._is_valid_position(x, y):
                msg = f"Invalid coordinate ({x}, {y}) in deployment zone {name}"
                raise ValueError(msg)

        zone = DeploymentZone(
            name=name,
            deployment_type=deployment_type,
            coordinates=set(coordinates),
            description=description,
        )
        self.deployment_zones[name] = zone

    def add_objective(self, name: str, position: tuple[int, int]):
        """Add an objective marker at a position."""
        x, y = position
        if not self._is_valid_position(x, y):
            msg = f"Invalid objective position ({x}, {y})"
            raise ValueError(msg)
        self.objectives[name] = position

    def get_deployment_zone_for_player(self, player_id: str) -> DeploymentZone | None:
        """Get the deployment zone for a specific player."""
        # Simple mapping: player1 -> PLAYER_1, player2 -> PLAYER_2
        if player_id.endswith("1") or player_id == "player1":
            deployment_type = DeploymentType.PLAYER_1
        elif player_id.endswith("2") or player_id == "player2":
            deployment_type = DeploymentType.PLAYER_2
        else:
            return None

        for zone in self.deployment_zones.values():
            if zone.deployment_type == deployment_type:
                return zone
        return None

    def is_valid_deployment_position(self, x: int, y: int, player_id: str) -> bool:
        """Check if a position is valid for deploying a unit."""
        zone = self.get_deployment_zone_for_player(player_id)
        if zone is None:
            return True  # No specific zones defined, allow anywhere
        return zone.contains_position(x, y)

    def get_terrain_cost(self, x: int, y: int) -> int:
        """Get movement cost for terrain at position."""
        terrain = self.get_terrain(x, y)
        if terrain == TerrainType.IMPASSABLE:
            return 999  # Effectively infinite cost
        elif terrain == TerrainType.DANGEROUS_TERRAIN:
            return 2  # Dangerous terrain costs extra
        elif terrain == TerrainType.DIFFICULT_TERRAIN:
            return 2  # Difficult terrain costs extra
        else:
            return 1  # Open ground costs 1

    def get_neighbors(self, x: int, y: int) -> list[tuple[int, int]]:
        """Get valid neighboring positions (8 directions)."""
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if self._is_valid_position(nx, ny):
                    neighbors.append((nx, ny))
        return neighbors

    def calculate_distance(self, start: tuple[int, int], end: tuple[int, int]) -> float:
        """Calculate Euclidean distance between two positions."""
        x1, y1 = start
        x2, y2 = end
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    def find_path(
        self, start: tuple[int, int], end: tuple[int, int]
    ) -> list[tuple[int, int]] | None:
        """Find a path using A* algorithm (simplified implementation)."""
        # This is a basic implementation - in a real game you'd want a more sophisticated pathfinding
        if not self._is_valid_position(*start) or not self._is_valid_position(*end):
            return None

        if self.get_terrain(*end) == TerrainType.IMPASSABLE:
            return None

        # Simple direct path (ignoring terrain for now)
        path = [start]
        current = start
        while current != end:
            cx, cy = current
            ex, ey = end

            # Move towards end
            dx = 1 if ex > cx else -1 if ex < cx else 0
            dy = 1 if ey > cy else -1 if ey < cy else 0

            next_pos = (cx + dx, cy + dy)
            if next_pos == current:  # Can't move
                return None

            if not self._is_valid_position(*next_pos):
                return None

            if self.get_terrain(*next_pos) == TerrainType.IMPASSABLE:
                return None

            path.append(next_pos)
            current = next_pos

            # Prevent infinite loops
            if len(path) > 100:
                return None

        return path

    def get_map_summary(self) -> dict[str, any]:
        """Get a summary of the map state."""
        terrain_counts = {}
        for terrain_type in TerrainType:
            count = np.sum(self.terrain == terrain_type)
            terrain_counts[terrain_type.value] = int(count)

        return {
            "name": self.name,
            "dimensions": f"{self.width}x{self.height}",
            "terrain_distribution": terrain_counts,
            "deployment_zones": {
                name: {
                    "type": zone.deployment_type.value,
                    "area": zone.area,
                    "description": zone.description,
                }
                for name, zone in self.deployment_zones.items()
            },
            "objectives": list(self.objectives.keys()),
        }

    def _is_valid_position(self, x: int, y: int) -> bool:
        """Check if a position is within map bounds."""
        return 0 <= x < self.width and 0 <= y < self.height

    # ── Line of Sight ─────────────────────────────────────────────

    _los_cache: dict[tuple[int, int, int, int], bool] = field(default_factory=dict)

    @staticmethod
    def _is_blocking_los(terrain_type: TerrainType) -> bool:
        """Return True if terrain type blocks line of sight entirely."""
        return terrain_type == TerrainType.IMPASSABLE

    def has_los(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """Check LoS between (x1,y1) and (x2,y2) via Bresenham ray casting.

        Impassable terrain cells block LoS. Start/end cells are ignored
        (a unit can always see from its own cell and to the target cell).
        Results are cached for performance.
        """
        # Normalize cache key (always low-to-high)
        ax, ay = (x1, y1) if x1 < x2 or (x1 == x2 and y1 < y2) else (x2, y2)
        bx, by = (x2, y2) if x1 < x2 or (x1 == x2 and y1 < y2) else (x1, y1)
        key = (ax, ay, bx, by)
        if key in self._los_cache:
            return self._los_cache[key]

        dx = abs(x2 - x1)
        dy = -abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx + dy

        x, y = x1, y1
        blocked = False

        while True:
            # Check terrain at current cell (skip start and end)
            if (x, y) != (x1, y1) and (x, y) != (x2, y2) and self._is_blocking_los(self.terrain[y, x]):
                blocked = True
                break

            if (x, y) == (x2, y2):
                break

            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

        self._los_cache[key] = not blocked
        return not blocked

    def clear_los_cache(self):
        """Clear the LoS cache (call when terrain changes)."""
        self._los_cache.clear()


# Utility functions for creating specific mission maps
def create_dawn_of_war_map() -> BattlefieldMap:
    """Create a Dawn of War deployment map."""
    battlefield = BattlefieldMap.create_empty(6, 4, "Dawn of War")

    # Deployment zones are table corners
    battlefield.add_deployment_zone(
        "player1_deployment",
        DeploymentType.PLAYER_1,
        [(0, 0), (1, 0), (0, 1), (1, 1)],
        "Northwest corner",
    )

    battlefield.add_deployment_zone(
        "player2_deployment",
        DeploymentType.PLAYER_2,
        [(4, 2), (5, 2), (4, 3), (5, 3)],
        "Southeast corner",
    )

    # Center objectives
    battlefield.add_objective("objective_1", (2, 1))
    battlefield.add_objective("objective_2", (3, 1))
    battlefield.add_objective("objective_3", (2, 2))
    battlefield.add_objective("objective_4", (3, 2))

    return battlefield


def create_spearhead_map() -> BattlefieldMap:
    """Create a Spearhead deployment map."""
    battlefield = BattlefieldMap.create_empty(6, 4, "Spearhead")

    # Deployment zones are table edges
    battlefield.add_deployment_zone(
        "player1_deployment",
        DeploymentType.PLAYER_1,
        [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (0, 1), (1, 1), (2, 1)],
        "North edge",
    )

    battlefield.add_deployment_zone(
        "player2_deployment",
        DeploymentType.PLAYER_2,
        [(0, 2), (1, 2), (2, 2), (0, 3), (1, 3), (2, 3), (3, 3), (4, 3), (5, 3)],
        "South edge",
    )

    return battlefield
