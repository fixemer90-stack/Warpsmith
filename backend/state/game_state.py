"""Game state management for Warhammer 40k battles."""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from enum import Enum

import numpy as np


class TerrainType(Enum):
    """Types of terrain on the battlefield."""
    OPEN_GROUND = "open_ground"
    DIFFICULT_TERRAIN = "difficult_terrain"
    DANGEROUS_TERRAIN = "dangerous_terrain"
    IMPASSABLE = "impassable"


class GamePhase(Enum):
    """Phases of a Warhammer 40k turn."""
    COMMAND = "command"
    MOVEMENT = "movement"
    SHOOTING = "shooting"
    CHARGE = "charge"
    FIGHT = "fight"
    MORALE = "morale"


@dataclass
class UnitState:
    """State of a single unit in the game."""
    unit_id: str
    name: str
    faction: str
    position: Tuple[int, int]  # (x, y) coordinates on the map
    current_wounds: int
    max_wounds: int
    models_remaining: int
    models_total: int
    leadership: int
    objective_control: int
    is_warlord: bool = False
    has_moved: bool = False
    has_shot: bool = False
    has_charged: bool = False
    has_fought: bool = False
    is_pinned: bool = False
    command_points: int = 0

    @property
    def is_alive(self) -> bool:
        """Check if the unit is still alive."""
        return self.models_remaining > 0 and self.current_wounds > 0

    @property
    def wounds_per_model(self) -> float:
        """Calculate average wounds per remaining model."""
        if self.models_remaining == 0:
            return 0
        return self.current_wounds / self.models_remaining


@dataclass
class PlayerState:
    """State for a single player."""
    player_id: str
    name: str
    faction: str
    command_points: int = 6
    victory_points: int = 0
    units: Dict[str, UnitState] = field(default_factory=dict)
    stratagems_used: List[str] = field(default_factory=list)
    is_active: bool = True

    @property
    def total_objective_control(self) -> int:
        """Calculate total objective control from all units."""
        return sum(unit.objective_control for unit in self.units.values() if unit.is_alive)

    @property
    def warlord_unit(self) -> Optional[UnitState]:
        """Get the warlord unit if it exists."""
        for unit in self.units.values():
            if unit.is_warlord:
                return unit
        return None


@dataclass
class GameState:
    """Complete state of a Warhammer 40k game."""
    game_id: str
    mission_name: str
    map_width: int = 6  # Standard 6x4 feet table
    map_height: int = 4
    current_round: int = 1
    current_phase: GamePhase = GamePhase.COMMAND
    active_player: Optional[str] = None
    players: Dict[str, PlayerState] = field(default_factory=dict)
    terrain_map: Optional[np.ndarray] = None
    deployment_zones: Dict[str, List[Tuple[int, int]]] = field(default_factory=dict)
    objectives: Dict[str, Tuple[int, int]] = field(default_factory=dict)
    max_rounds: int = 5
    victory_conditions: Dict[str, any] = field(default_factory=dict)
    game_log: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize terrain map if not provided."""
        if self.terrain_map is None:
            self.terrain_map = np.full((self.map_height, self.map_width),
                                     TerrainType.OPEN_GROUND, dtype=object)

    @property
    def is_game_over(self) -> bool:
        """Check if the game has ended."""
        # Game ends after max rounds or if victory conditions are met
        if self.current_round > self.max_rounds:
            return True

        # Check victory conditions (simplified)
        for player in self.players.values():
            if player.victory_points >= 10:  # Example VP threshold
                return True

        return False

    @property
    def winner(self) -> Optional[str]:
        """Get the winner if game is over."""
        if not self.is_game_over:
            return None

        max_vp = max(player.victory_points for player in self.players.values())
        winners = [pid for pid, player in self.players.items()
                  if player.victory_points == max_vp]

        return winners[0] if len(winners) == 1 else None  # None for tie

    def get_unit_at_position(self, x: int, y: int) -> Optional[UnitState]:
        """Find unit at the given position."""
        for player in self.players.values():
            for unit in player.units.values():
                if unit.position == (x, y):
                    return unit
        return None

    def move_unit(self, unit_id: str, new_position: Tuple[int, int]) -> bool:
        """Move a unit to a new position."""
        for player in self.players.values():
            if unit_id in player.units:
                unit = player.units[unit_id]
                # Check if move is valid (basic check)
                if self._is_valid_move(unit, new_position):
                    unit.position = new_position
                    unit.has_moved = True
                    self.game_log.append(f"{unit.name} moved to {new_position}")
                    return True
        return False

    def _is_valid_move(self, unit: UnitState, new_position: Tuple[int, int]) -> bool:
        """Check if a move is valid (simplified)."""
        x, y = new_position
        # Check bounds
        if not (0 <= x < self.map_width and 0 <= y < self.map_height):
            return False

        # Check terrain
        if self.terrain_map[y, x] == TerrainType.IMPASSABLE:
            return False

        # Check if position is occupied
        if self.get_unit_at_position(x, y) is not None:
            return False

        return True

    def deal_damage(self, unit_id: str, damage: int) -> bool:
        """Deal damage to a unit."""
        for player in self.players.values():
            if unit_id in player.units:
                unit = player.units[unit_id]
                unit.current_wounds = max(0, unit.current_wounds - damage)

                # Update models remaining (simplified)
                if unit.current_wounds == 0:
                    unit.models_remaining = 0

                self.game_log.append(f"{unit.name} took {damage} damage")
                return True
        return False

    def add_victory_points(self, player_id: str, points: int):
        """Add victory points to a player."""
        if player_id in self.players:
            self.players[player_id].victory_points += points
            self.game_log.append(f"{self.players[player_id].name} gained {points} VP")

    def next_phase(self):
        """Advance to the next phase."""
        phases = list(GamePhase)
        current_index = phases.index(self.current_phase)
        next_index = (current_index + 1) % len(phases)

        if next_index == 0:  # New turn
            self.current_round += 1
            # Reset unit states for new turn
            for player in self.players.values():
                for unit in player.units.values():
                    unit.has_moved = False
                    unit.has_shot = False
                    unit.has_charged = False
                    unit.has_fought = False

        self.current_phase = phases[next_index]
        self.game_log.append(f"Phase changed to {self.current_phase.value}")

    def get_game_summary(self) -> Dict[str, any]:
        """Get a summary of the current game state."""
        return {
            "game_id": self.game_id,
            "mission": self.mission_name,
            "round": self.current_round,
            "phase": self.current_phase.value,
            "players": {
                pid: {
                    "name": player.name,
                    "faction": player.faction,
                    "cp": player.command_points,
                    "vp": player.victory_points,
                    "units_alive": sum(1 for unit in player.units.values() if unit.is_alive),
                    "total_oc": player.total_objective_control,
                }
                for pid, player in self.players.items()
            },
            "is_game_over": self.is_game_over,
            "winner": self.winner,
        }


# Factory functions for creating game states
def create_empty_game(game_id: str, mission_name: str = "Standard Mission") -> GameState:
    """Create a new empty game state."""
    return GameState(
        game_id=game_id,
        mission_name=mission_name,
    )


def create_standard_map() -> np.ndarray:
    """Create a standard 6x4 map with some terrain."""
    terrain = np.full((4, 6), TerrainType.OPEN_GROUND, dtype=object)

    # Add some difficult terrain
    terrain[1, 2] = TerrainType.DIFFICULT_TERRAIN
    terrain[2, 3] = TerrainType.DIFFICULT_TERRAIN

    # Add dangerous terrain
    terrain[0, 5] = TerrainType.DANGEROUS_TERRAIN

    return terrain