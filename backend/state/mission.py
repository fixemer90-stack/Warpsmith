"""Mission system for Warhammer 40k battles."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .game_state import GameState
import numpy as np


@dataclass
class VPTracker:
    """Подсчёт VP на протяжении игры."""

    history: dict[int, list[int]] = field(default_factory=lambda: {1: [], 2: []})
    total: dict[int, int] = field(default_factory=lambda: {1: 0, 2: 0})

    def add(self, player: int, vp: int) -> None:
        self.history[player].append(vp)
        self.total[player] += vp

    def round_vp(self, player: int, round_num: int) -> int:
        """VP полученные в конкретном раунде."""
        if round_num <= len(self.history[player]):
            return self.history[player][round_num - 1]
        return 0

    def leader(self) -> int:
        """Текущий лидер по VP."""
        return 1 if self.total[1] >= self.total[2] else 2

    def is_tied(self) -> bool:
        return self.total[1] == self.total[2]

    def margin(self) -> int:
        return abs(self.total[1] - self.total[2])

    def summary(self) -> dict:
        return {
            "player_1": {"total": self.total[1], "per_round": self.history[1]},
            "player_2": {"total": self.total[2], "per_round": self.history[2]},
            "winner": self.leader() if not self.is_tied() else "tie",
            "margin": self.margin(),
        }


@dataclass
class GameResult:
    winner: str | None  # None = tie
    reason: str  # "rounds_completed", "army_wiped", "vp_cap"
    vp_tracker: VPTracker
    total_rounds: int
    summary: dict


def _int_to_player(player_num: int) -> str:
    """Convert VPTracker int (1, 2) to GameState player_id ("1", "2")."""
    return str(player_num)


def check_end_game(
    state: GameState, mission: Mission, vp: VPTracker, round_num: int
) -> GameResult | None:
    """Проверить условия окончания игры."""

    # 1. Victory Point cap (100 VP)
    for player_num in [1, 2]:
        if vp.total[player_num] >= 100:
            return GameResult(
                winner=_int_to_player(player_num),
                reason="vp_cap",
                vp_tracker=vp,
                total_rounds=round_num,
                summary=vp.summary(),
            )

    # 2. Army wiped
    for player_id, player_state in state.players.items():
        if player_state and all(u.models_remaining <= 0 for u in player_state.units.values()):
            winner = "2" if player_id in ("p1", "1") else "1"
            return GameResult(
                winner=winner,
                reason="army_wiped",
                vp_tracker=vp,
                total_rounds=round_num,
                summary=vp.summary(),
            )

    # 3. Max rounds reached
    if round_num >= mission.config.max_rounds:
        leader = vp.leader()
        if vp.is_tied():
            # Tie-breakers:
            # 1. Who killed more pts?
            # 2. Who has more objectives?
            # 3. Random
            leader = _resolve_tie(state)
        return GameResult(
            winner=_int_to_player(leader) if not vp.is_tied() else None,
            reason="rounds_completed",
            vp_tracker=vp,
            total_rounds=round_num,
            summary=vp.summary(),
        )

    return None  # game continues


def _resolve_tie(state: GameState) -> int:
    """Tie-break: больше убитых очков -> больше контролируемых точек -> random."""
    # Calculate killed points for each player
    killed_points = {}
    for player_id, player_state in [
        ("p1", state.players.get("p1")),
        ("p2", state.players.get("p2")),
    ]:
        if player_state:
            killed = 0
            for unit in player_state.units.values():
                # Points killed = (starting wounds - current wounds) * points per wound
                # Simplified: assume 10 points per wound
                killed += (unit.max_wounds - unit.current_wounds) * 10
            killed_points[player_id] = killed
        else:
            killed_points[player_id] = 0

    p1_killed = killed_points.get("p1", 0)
    p2_killed = killed_points.get("p2", 0)

    if p1_killed != p2_killed:
        return 1 if p1_killed > p2_killed else 2

    # TODO: count controlled objectives
    # For now, fallback to player 1 winning
    return 1


def score_standard(mission: Mission) -> dict[int, int]:
    """Standard scoring: VP = number of objectives controlled."""
    mission.update_objective_control()

    vp = {player_id: 0 for player_id in mission.state.players}
    for player_id in mission.state.players:
        for obj in mission.config.objectives:
            if obj.controlled_by == player_id and not obj.is_contested:
                vp[player_id] += 1  # 1 VP per objective controlled
    return vp


def score_progressive(mission: Mission) -> dict[int, int]:
    """Progressive scoring: VP = objectives controlled + bonus for controlling more than opponent."""
    mission.update_objective_control()

    vp = {player_id: 0 for player_id in mission.state.players}
    player_ids = list(mission.state.players.keys())

    if len(player_ids) >= 2:
        p1_obj = 0
        p2_obj = 0

        for obj in mission.config.objectives:
            if obj.controlled_by == player_ids[0] and not obj.is_contested:
                p1_obj += 1
            elif obj.controlled_by == player_ids[1] and not obj.is_contested:
                p2_obj += 1

        vp[player_ids[0]] = p1_obj
        vp[player_ids[1]] = p2_obj

        # Bonus for controlling more objectives
        if p1_obj > p2_obj:
            vp[player_ids[0]] += 2
        elif p2_obj > p1_obj:
            vp[player_ids[1]] += 2

    return vp


def score_kill_points(mission: Mission) -> dict[int, int]:
    """Kill points scoring: VP = percentage of opponent's army destroyed."""
    mission.update_objective_control()

    vp = {player_id: 0 for player_id in mission.state.players}
    player_ids = list(mission.state.players.keys())

    if len(player_ids) >= 2:
        # Calculate destroyed points for each player
        p1_destroyed = 0  # points destroyed by player 1 (of player 2's army)
        p2_destroyed = 0  # points destroyed by player 2 (of player 1's army)

        # Points destroyed by player 1 (against player 2)
        if player_ids[1] in mission.state.players:
            for unit in mission.state.players[player_ids[1]].units.values():
                if not unit.is_alive:
                    # Simplified: assume unit cost is proportional to max wounds
                    p1_destroyed += unit.max_wounds * 10

        # Points destroyed by player 2 (against player 1)
        if player_ids[0] in mission.state.players:
            for unit in mission.state.players[player_ids[0]].units.values():
                if not unit.is_alive:
                    # Simplified: assume unit cost is proportional to max wounds
                    p2_destroyed += unit.max_wounds * 10

        # Calculate total army points for each player
        p1_total = 0
        p2_total = 0

        if player_ids[0] in mission.state.players:
            for unit in mission.state.players[player_ids[0]].units.values():
                p1_total += unit.max_wounds * 10  # Rough approximation

        if player_ids[1] in mission.state.players:
            for unit in mission.state.players[player_ids[1]].units.values():
                p2_total += unit.max_wounds * 10  # Rough approximation

        # Calculate VP as percentage of opponent's army destroyed
        if p2_total > 0:
            vp[player_ids[0]] = int(
                (p1_destroyed / p2_total) * 100
            )  # p1 gets VP for what they destroyed of p2
        if p1_total > 0:
            vp[player_ids[1]] = int(
                (p2_destroyed / p1_total) * 100
            )  # p2 gets VP for what they destroyed of p1

    return vp


SCORING_MAP = {
    "standard": score_standard,
    "progressive": score_progressive,
    "kill_points": score_kill_points,
}


def apply_scoring(state: GameState, mission: Mission, vp: VPTracker) -> VPTracker:
    """Подсчитать VP за текущий раунд, добавить в трекер."""
    scorer = SCORING_MAP.get(mission.config.scoring_rule, score_standard)
    round_vp = scorer(mission)
    for player_id in state.players:
        # Convert string player_id to int for VPTracker:
        #   "p1" / "1" → 1,  "p2" / "2" → 2
        player_num = 1 if player_id in ("p1", "1") else 2
        vp.add(player_num, round_vp.get(player_id, 0))
    return vp


class DeploymentType(Enum):
    """Types of deployment zones."""

    DAWN_OF_WAR = "dawn_of_war"  # 24" deploy zone, 12" gap
    SEARCH_AND_DESTROY = "search_and_destroy"
    CRUCIBLE_OF_BATTLE = "crucible_of_battle"


class MissionObjective:
    """Objective point on the map."""

    def __init__(self, x: int, y: int, label: str = ""):
        self.x = x
        self.y = y
        self.label = label
        self.controlled_by: int | None = None  # player_id
        self.is_contested: bool = False

    @property
    def position(self) -> tuple[int, int]:
        return (self.x, self.y)

    def __repr__(self):
        return f"MissionObjective({self.x}, {self.y}, label='{self.label}', controlled_by={self.controlled_by})"


@dataclass
class MissionConfig:
    """Mission configuration."""

    name: str
    deployment: DeploymentType
    description: str
    objectives: list[MissionObjective]
    max_rounds: int = 5
    scoring_rule: str = "standard"  # standard, progressive, only_war, kill_points
    deployment_zone_rows: int = 24  # 24" from edge
    no_mans_land_start: int = 24
    no_mans_land_end: int = 36


@dataclass
class Mission:
    """Mission in the game."""

    config: MissionConfig
    state: GameState

    def score_vp(self, player_id: str) -> int:
        """Calculate VP for player at end of Command phase."""
        # Update objective control first
        self.update_objective_control()

        vp = 0
        for obj in self.config.objectives:
            if obj.controlled_by == player_id and not obj.is_contested:
                vp += 1  # 1 VP per objective controlled
        return vp

    def update_objective_control(self, control_range: float = 3.0):
        """Update which players control each objective (within control_range cells).

        Per 10ed: player with highest total OC within range controls.
        Contested only when OC is equal.
        """
        for obj in self.config.objectives:
            obj.controlled_by = None
            obj.is_contested = False

        for obj in self.config.objectives:
            # Sum OC per player within range
            oc_by_player: dict[str, int] = {}

            for player in self.state.players.values():
                total_oc = 0
                for unit in player.units.values():
                    if not unit.is_alive:
                        continue
                    dist = (
                        (unit.position[0] - obj.position[0]) ** 2
                        + (unit.position[1] - obj.position[1]) ** 2
                    ) ** 0.5
                    if dist <= control_range:
                        total_oc += getattr(unit, "objective_control", 1)
                if total_oc > 0:
                    oc_by_player[player.player_id] = total_oc

            if not oc_by_player:
                continue  # No one controls

            if len(oc_by_player) == 1:
                obj.controlled_by = next(iter(oc_by_player))
                obj.is_contested = False
            else:
                # Multiple players — highest OC wins
                max_oc = max(oc_by_player.values())
                top_players = [pid for pid, oc in oc_by_player.items() if oc == max_oc]
                if len(top_players) == 1:
                    obj.controlled_by = top_players[0]
                    obj.is_contested = False
                else:
                    obj.controlled_by = None
                    obj.is_contested = True

    def calculate_victory_points(self) -> dict[str, int]:
        """Calculate victory points for all players based on mission scoring rule."""
        # Update objective control first
        self.update_objective_control()

        vp = {player_id: 0 for player_id in self.state.players}

        if self.config.scoring_rule == "standard":
            # VP = number of objectives controlled
            for player_id in self.state.players:
                vp[player_id] = self.score_vp(player_id)

        elif self.config.scoring_rule == "progressive":
            # VP = objectives controlled + bonus for controlling more than opponent
            player_ids = list(self.state.players.keys())
            if len(player_ids) >= 2:
                p1_obj = self.score_vp(player_ids[0])
                p2_obj = self.score_vp(player_ids[1])

                vp[player_ids[0]] = p1_obj
                vp[player_ids[1]] = p2_obj

                # Bonus for controlling more objectives
                if p1_obj > p2_obj:
                    vp[player_ids[0]] += 2
                elif p2_obj > p1_obj:
                    vp[player_ids[1]] += 2

        elif self.config.scoring_rule == "kill_points":
            # VP = percentage of opponent's army destroyed
            # Simplified implementation
            player_ids = list(self.state.players.keys())
            if len(player_ids) >= 2:
                p1_killed = self._calculate_destroyed_points(player_ids[0], player_ids[1])
                p2_killed = self._calculate_destroyed_points(player_ids[1], player_ids[0])

                p1_total = self._calculate_army_points(player_ids[1])  # opponent's total
                p2_total = self._calculate_army_points(player_ids[0])  # opponent's total

                if p1_total > 0:
                    vp[player_ids[0]] = int((p1_killed / p1_total) * 100)
                if p2_total > 0:
                    vp[player_ids[1]] = int((p2_killed / p2_total) * 100)

        return vp

    def _calculate_destroyed_points(
        self, attacking_player_id: str, defending_player_id: str
    ) -> int:
        """Calculate points worth of units destroyed by attacking player."""
        destroyed_points = 0
        defending_player = self.state.players.get(defending_player_id)
        if not defending_player:
            return 0

        for unit in defending_player.units.values():
            # If unit is destroyed (no models remaining)
            if not unit.is_alive:
                # Simplified: assume unit cost is proportional to max wounds
                destroyed_points += unit.max_wounds * 10  # Rough approximation
        return destroyed_points

    def _calculate_army_points(self, player_id: str) -> int:
        """Calculate total army points for a player."""
        total_points = 0
        player = self.state.players.get(player_id)
        if not player:
            return 0

        for unit in player.units.values():
            # Simplified: assume unit cost is proportional to max wounds
            total_points += unit.max_wounds * 10  # Rough approximation
        return total_points

    def get_deployment_zones(self) -> dict[str, list[tuple[int, int]]]:
        """Get deployment zones for each player based on mission type."""
        zones = {}
        player_ids = list(self.state.players.keys())

        if not player_ids:
            return zones

        map_width = self.state.map_width
        map_height = self.state.map_height

        # Convert deployment zone from inches to map units
        # Assuming map height in units represents height in feet
        # So 4 units = 4 feet = 48 inches
        # Therefore, 1 unit = 12 inches = 1 foot
        # deployment_zone_rows is in inches, so convert to units: inches / 12
        zone_depth_units = max(1, self.config.deployment_zone_rows // 12)

        if self.config.deployment == DeploymentType.DAWN_OF_WAR:
            # Each player deploys in their own zone, with gap in middle
            if len(player_ids) >= 2:
                # Player 1: bottom edge
                zones[player_ids[0]] = [
                    (x, y)
                    for x in range(map_width)
                    for y in range(min(zone_depth_units, map_height))
                ]

                # Player 2: top edge
                zones[player_ids[1]] = [
                    (x, y)
                    for x in range(map_width)
                    for y in range(max(0, map_height - zone_depth_units), map_height)
                ]

        elif self.config.deployment == DeploymentType.SEARCH_AND_DESTROY:
            # Players deploy in opposite corners
            zone_size = min(6, map_width // 2, map_height // 2)  # 6x6 or smaller in units

            if len(player_ids) >= 2:
                # Player 1: bottom-left corner
                zones[player_ids[0]] = [
                    (x, y)
                    for x in range(min(zone_size, map_width))
                    for y in range(min(zone_size, map_height))
                ]

                # Player 2: top-right corner
                zones[player_ids[1]] = [
                    (x, y)
                    for x in range(max(0, map_width - zone_size), map_width)
                    for y in range(max(0, map_height - zone_size), map_height)
                ]

        elif self.config.deployment == DeploymentType.CRUCIBLE_OF_BATTLE and len(player_ids) >= 2:
            # Players deploy in long table edges
            # Player 1: bottom edge
            zones[player_ids[0]] = [
                (x, y) for x in range(map_width) for y in range(min(zone_depth_units, map_height))
            ]

            # Player 2: top edge
            zones[player_ids[1]] = [
                (x, y)
                for x in range(map_width)
                for y in range(max(0, map_height - zone_depth_units), map_height)
            ]

        return zones

    def is_valid_deployment_position(self, player_id: str, position: tuple[int, int]) -> bool:
        """Check if a position is valid for player deployment."""
        zones = self.get_deployment_zones()
        if player_id not in zones:
            return False

        return position in zones[player_id]

    def get_mission_summary(self) -> dict[str, any]:
        """Get summary of mission state."""
        return {
            "mission_name": self.config.name,
            "deployment_type": self.config.deployment.value,
            "scoring_rule": self.config.scoring_rule,
            "objectives": [
                {
                    "x": obj.x,
                    "y": obj.y,
                    "label": obj.label,
                    "controlled_by": obj.controlled_by,
                    "is_contested": obj.is_contested,
                }
                for obj in self.config.objectives
            ],
            "current_vp": self.calculate_victory_points(),
        }


# Factory functions for creating missions
def create_mission(mission_name: str, game_state: GameState) -> Mission | None:
    """Create a mission by name, scaling objectives to actual map size."""
    mission_func = MISSIONS.get(mission_name.lower().replace(" ", "_").replace("-", "_"))
    if mission_func:
        config = mission_func()
        # Scale objectives to actual map size if empty (dynamic placement)
        if not config.objectives and game_state:
            w = game_state.map_width
            h = game_state.map_height
            cx, cy = w // 2, h // 2
            if config.scoring_rule in ("standard", "progressive", "kill_points"):
                # 5 objectives for standard/Take-and-Hold/kill_points, 3 for progressive/Only War
                if config.scoring_rule in ("standard", "kill_points"):
                    config.objectives = [
                        MissionObjective(cx, cy, "Center"),
                        MissionObjective(cx // 2, cy, "Flank Left"),
                        MissionObjective(cx + cx // 2, cy, "Flank Right"),
                        MissionObjective(cx, cy // 2, "Home A"),
                        MissionObjective(cx, cy + cy // 2, "Home B"),
                    ]
                else:
                    config.objectives = [
                        MissionObjective(cx, cy, "Center"),
                        MissionObjective(cx // 2, cy, "Flank Left"),
                        MissionObjective(cx + cx // 2, cy, "Flank Right"),
                    ]
        return Mission(config=config, state=game_state)
    return None


def _only_war() -> MissionConfig:
    """Only War: progressive-scoring mission. Objectives placed dynamically by create_mission()."""
    return MissionConfig(
        name="Only War",
        deployment=DeploymentType.DAWN_OF_WAR,
        description="Control objectives to score VP each round.",
        objectives=[],  # placed dynamically based on map size
        scoring_rule="progressive",
    )


def _purge_the_foe() -> MissionConfig:
    """Purge the Foe: Slay the Warlord + kill points."""
    return MissionConfig(
        name="Purge the Foe",
        deployment=DeploymentType.SEARCH_AND_DESTROY,
        description="Kill more pts than opponent each round.",
        objectives=[],
        scoring_rule="kill_points",
    )


def _take_and_hold() -> MissionConfig:
    """Take and Hold: 5 objectives, score end of each Command phase."""
    return MissionConfig(
        name="Take and Hold",
        deployment=DeploymentType.CRUCIBLE_OF_BATTLE,
        description="Control objectives to score at end of Command phase.",
        objectives=[],  # placed dynamically based on map size (5 objectives)
        scoring_rule="standard",
    )


# Registry of available missions
MISSIONS: dict[str, Callable[[], MissionConfig]] = {}

MISSIONS["only_war"] = _only_war
MISSIONS["purge_the_foe"] = _purge_the_foe
MISSIONS["take_and_hold"] = _take_and_hold
