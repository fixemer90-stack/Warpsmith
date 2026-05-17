"""Game state management for Warhammer 40k battles."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

import numpy as np

from backend.state.runtime_id import format_event_identity

if TYPE_CHECKING:
    from .mission import Mission


class TerrainType(Enum):
    """Types of terrain on the battlefield."""

    OPEN_GROUND = "open_ground"
    DIFFICULT_TERRAIN = "difficult_terrain"
    DANGEROUS_TERRAIN = "dangerous_terrain"
    IMPASSABLE = "impassable"
    RUINS = "ruins"
    WOODS = "woods"
    CRATER = "crater"
    BARRICADE = "barricade"


class GamePhase(Enum):
    """Phases of a Warhammer 40k 10th edition turn."""

    COMMAND = "command"
    MOVEMENT = "movement"
    SHOOTING = "shooting"
    CHARGE = "charge"
    FIGHT = "fight"


GAME_PHASE_ORDER: tuple[GamePhase, ...] = tuple(GamePhase)
"""Canonical 10e runtime phase order: Command -> Movement -> Shooting -> Charge -> Fight."""


@dataclass
class UnitState:
    """State of a single unit in the game."""

    unit_id: str
    name: str
    faction: str
    position: tuple[int, int]  # (x, y) coordinates on the map
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
    is_engaged: bool = False
    is_fighting: bool = False
    is_battle_shocked: bool = False
    has_advanced: bool = False
    weapon_usage: dict[str, bool] = field(default_factory=dict)

    @property
    def is_above_half_strength(self) -> bool:
        """Check if the unit is at or above half strength."""
        return self.models_remaining > (self.models_total / 2)

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
    command_points: int = 0
    victory_points: int = 0
    units: dict[str, UnitState] = field(default_factory=dict)
    stratagems_used: list[str] = field(default_factory=list)
    is_active: bool = True
    command_priority: bool = False  # Whether this player has priority this round

    @property
    def total_objective_control(self) -> int:
        """Calculate total objective control from all units."""
        return sum(unit.objective_control for unit in self.units.values() if unit.is_alive)

    @property
    def warlord_unit(self) -> UnitState | None:
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
    active_player: str | None = None
    players: dict[str, PlayerState] = field(default_factory=dict)
    terrain_map: np.ndarray | None = None
    deployment_zones: dict[str, list[tuple[int, int]]] = field(default_factory=dict)
    objectives: dict[str, tuple[int, int]] = field(default_factory=dict)
    max_rounds: int = 5
    previous_round_priority_player_id: str | None = None
    victory_conditions: dict[str, any] = field(default_factory=dict)
    game_log: list[str] = field(default_factory=list)
    mission: Mission | None = None  # Current mission being played

    def __post_init__(self):
        """Initialize terrain map and mission if not provided."""
        if self.terrain_map is None:
            self.terrain_map = np.full(
                (self.map_height, self.map_width), TerrainType.OPEN_GROUND, dtype=object
            )

        # Initialize mission if mission_name is provided
        if self.mission_name and self.mission is None:
            from .mission import create_mission

            self.mission = create_mission(self.mission_name, self)

    @property
    def is_game_over(self) -> bool:
        """Check if the game has ended — rounds limit only."""
        return self.current_round > self.max_rounds

    @property
    def winner(self) -> str | None:
        """Get the winner if game is over."""
        if not self.is_game_over:
            return None

        max_vp = max(player.victory_points for player in self.players.values())
        winners = [pid for pid, player in self.players.items() if player.victory_points == max_vp]

        return winners[0] if len(winners) == 1 else None  # None for tie

    def get_unit_at_position(self, x: int, y: int) -> UnitState | None:
        """Find unit at the given position."""
        for player in self.players.values():
            for unit in player.units.values():
                if unit.position == (x, y):
                    return unit
        return None

    def move_unit(self, unit_id: str, new_position: tuple[int, int]) -> bool:
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

    def _is_valid_move(self, unit: UnitState, new_position: tuple[int, int]) -> bool:
        """Check if a move is valid (simplified)."""
        x, y = new_position
        # Check bounds
        if not (0 <= x < self.map_width and 0 <= y < self.map_height):
            return False

        # Check terrain
        if self.terrain_map[y, x] == TerrainType.IMPASSABLE:
            return False

        # Check if position is occupied
        return self.get_unit_at_position(x, y) is None

    def deal_damage(self, unit_id: str, damage: int) -> bool:
        """Deal damage to a unit."""
        for player in self.players.values():
            if unit_id in player.units:
                unit = player.units[unit_id]
                unit.current_wounds = max(0, unit.current_wounds - damage)

                # Update models remaining (simplified)
                if unit.current_wounds == 0:
                    unit.models_remaining = 0

                target_meta = format_event_identity(target_id=unit.unit_id)
                self.game_log.append(f"{unit.name} took {damage} damage{target_meta}")
                if unit.current_wounds == 0 and unit.models_remaining == 0:
                    self.game_log.append(f"{unit.name} was destroyed{target_meta}")
                return True
        return False

    def add_victory_points(self, player_id: str, points: int):
        """Add victory points to a player."""
        if player_id in self.players:
            self.players[player_id].victory_points += points
            self.game_log.append(f"{self.players[player_id].name} gained {points} VP")

    def _determine_command_priority(self) -> None:
        """Determine which player has command priority for the current round.
        Round 1: roll-off (random), Round 2+: swap priority from previous round.
        """
        player_ids = list(self.players.keys())
        if len(player_ids) < 2:
            if player_ids:
                self.players[player_ids[0]].command_priority = True
            return

        if self.current_round == 1:
            import random

            winner_id = random.choice(player_ids)
            for pid in player_ids:
                self.players[pid].command_priority = pid == winner_id
            self.previous_round_priority_player_id = winner_id
        else:
            if self.previous_round_priority_player_id is not None:
                for pid in player_ids:
                    self.players[pid].command_priority = (
                        pid != self.previous_round_priority_player_id
                    )
                nxt = [pid for pid in player_ids if pid != self.previous_round_priority_player_id]
                if nxt:
                    self.previous_round_priority_player_id = nxt[0]
            else:
                import random

                winner_id = random.choice(player_ids)
                for pid in player_ids:
                    self.players[pid].command_priority = pid == winner_id
                self.previous_round_priority_player_id = winner_id

    def next_phase(self):
        """Advance to the next phase."""
        phases = GAME_PHASE_ORDER
        current_index = phases.index(self.current_phase)
        next_index = (current_index + 1) % len(phases)

        if next_index == 0:  # New turn starting with Command phase
            self.current_round += 1
            # Reset unit states for new turn
            for player in self.players.values():
                for unit in player.units.values():
                    unit.has_moved = False
                    unit.has_advanced = False
                    unit.has_shot = False
                    unit.has_charged = False
                    unit.has_fought = False
                    # Reset fight-related flags for new round
                    unit.is_fighting = False
                    # NOTE: is_engaged persists (only cleared by Fall Back or unit death)
                    # NOTE: is_battle_shocked persists (lasts until NEXT Command phase per 10ed)

            # Determine command priority for the new round
            self._determine_command_priority()

        self.current_phase = phases[next_index]
        self.game_log.append(f"Phase changed to {self.current_phase.value}")

    def get_game_summary(self) -> dict[str, any]:
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


# ── Canonical GameState serializer (Task 0.2) ──────────────────────────


def snapshot_game_state(state: GameState) -> dict[str, Any]:
    """Canonical serialization of GameState for round snapshots, replay payloads,
    and API payloads consumed by round-viewer and result screens.

    This is the SINGLE source of truth for GameState shape.  All other
    snapshot/serialization helpers MUST delegate here.
    """
    units_by_player: dict[str, list[dict[str, Any]]] = {}
    for player_id, player in state.players.items():
        units_by_player[player_id] = [_unit_snapshot(u, player_id) for u in player.units.values()]

    victory_points = {pid: getattr(p, "victory_points", 0) for pid, p in state.players.items()}

    phase_str = (
        state.current_phase.value
        if hasattr(state.current_phase, "value")
        else str(state.current_phase)
    )

    return {
        "round": state.current_round,
        "phase": phase_str,
        "map_width": state.map_width,
        "map_height": state.map_height,
        "victory_points": victory_points,
        "units": units_by_player,
    }


def _unit_snapshot(unit, player_id: str) -> dict[str, Any]:
    """Serialize a single UnitState into the canonical unit record shape.

    Explicit identity/display contract (Task 0.2 acceptance criteria):
      - ``runtime_unit_id`` — authoritative identity (e.g. ``p1:Boyz:0``)
      - ``display_name`` — UI text only; MUST NOT be used as lookup key
      - ``canonical_unit_id`` — unit name without player/index prefix
      - ``owner_id`` / ``player_id`` — owning player

    Legacy aliases ``id`` and ``name`` are kept for existing JS consumers
    (round-viewer, result-chart).  New code MUST use the explicit fields.
    """
    pos = unit.position if hasattr(unit, "position") else (0, 0)
    rtid = getattr(unit, "unit_id", "")
    dname = getattr(unit, "name", str(unit))

    # Derive canonical_unit_id from runtime_id: strip p<num>: prefix and :<idx> suffix
    canonical = rtid
    if rtid and ":" in rtid:
        parts = rtid.split(":")
        if len(parts) >= 2:
            canonical = parts[1]  # the unit name part
        if len(parts) >= 3:
            # Re-join if name itself contains colons (unlikely but safe)
            canonical = ":".join(parts[1:-1]) if len(parts) > 3 else parts[1]

    return {
        # ── Explicit identity/display contract ──
        "runtime_unit_id": rtid,
        "display_name": dname,
        "canonical_unit_id": canonical,
        "owner_id": player_id,
        "player_id": player_id,
        # ── Legacy aliases (keep for JS compatibility) ──
        "id": rtid,
        "name": dname,
        # ── Position & stats ──
        "position": {"x": int(pos[0]), "y": int(pos[1])},
        "models_remaining": getattr(unit, "models_remaining", 1),
        "models_total": getattr(unit, "models_total", 1),
        "current_wounds": getattr(unit, "current_wounds", getattr(unit, "wounds", 1)),
        "max_wounds": getattr(unit, "max_wounds", getattr(unit, "wounds", 1)),
        "is_alive": getattr(unit, "is_alive", True),
        "is_engaged": getattr(unit, "is_engaged", False),
        "is_battle_shocked": getattr(unit, "is_battle_shocked", False),
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
