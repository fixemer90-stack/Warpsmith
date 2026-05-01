"""Mission system for Warhammer 40k battles."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple, Optional, Callable, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .game_state import GameState
import numpy as np


class DeploymentType(Enum):
    """Types of deployment zones."""
    DAWN_OF_WAR = "dawn_of_war"         # 24" deploy zone, 12" gap
    SEARCH_AND_DESTROY = "search_and_destroy"
    CRUCIBLE_OF_BATTLE = "crucible_of_battle"


class MissionObjective:
    """Objective point on the map."""
    
    def __init__(self, x: int, y: int, label: str = ""):
        self.x = x
        self.y = y
        self.label = label
        self.controlled_by: Optional[int] = None  # player_id
        self.is_contested: bool = False
    
    @property
    def position(self) -> Tuple[int, int]:
        return (self.x, self.y)
    
    def __repr__(self):
        return f"MissionObjective({self.x}, {self.y}, label='{self.label}', controlled_by={self.controlled_by})"


@dataclass
class MissionConfig:
    """Mission configuration."""
    name: str
    deployment: DeploymentType
    description: str
    objectives: List[MissionObjective]
    max_rounds: int = 5
    scoring_rule: str = "standard"  # standard, progressive, only_war, kill_points
    deployment_zone_rows: int = 24  # 24" from edge
    no_mans_land_start: int = 24
    no_mans_land_end: int = 36


@dataclass
class Mission:
    """Mission in the game."""
    config: MissionConfig
    state: 'GameState'
    
    def score_vp(self, player_id: str) -> int:
        """Calculate VP for player at end of Command phase."""
        # Update objective control first
        self.update_objective_control()
        
        vp = 0
        for obj in self.config.objectives:
            if obj.controlled_by == player_id and not obj.is_contested:
                vp += 1  # 1 VP per objective controlled
        return vp
    
    def update_objective_control(self):
        """Update which players control each objective."""
        # Reset all objectives
        for obj in self.config.objectives:
            obj.controlled_by = None
            obj.is_contested = False
        
        # For each objective, check which units control it
        for obj in self.config.objectives:
            controlling_players = set()
            
            # Check all units from all players
            for player in self.state.players.values():
                for unit in player.units.values():
                    if unit.is_alive and unit.position == obj.position:
                        controlling_players.add(player.player_id)
            
            # Update objective status
            if len(controlling_players) == 1:
                obj.controlled_by = next(iter(controlling_players))
                obj.is_contested = False
            elif len(controlling_players) > 1:
                obj.controlled_by = None  # Contested
                obj.is_contested = True
            # else: no one controls it
    
    def calculate_victory_points(self) -> Dict[str, int]:
        """Calculate victory points for all players based on mission scoring rule."""
        # Update objective control first
        self.update_objective_control()
        
        vp = {player_id: 0 for player_id in self.state.players.keys()}
        
        if self.config.scoring_rule == "standard":
            # VP = number of objectives controlled
            for player_id in self.state.players.keys():
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
    
    def _calculate_destroyed_points(self, attacking_player_id: str, defending_player_id: str) -> int:
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
    
    def get_deployment_zones(self) -> Dict[str, List[Tuple[int, int]]]:
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
                    (x, y) for x in range(map_width) 
                    for y in range(min(zone_depth_units, map_height))
                ]
                
                # Player 2: top edge
                zones[player_ids[1]] = [
                    (x, y) for x in range(map_width) 
                    for y in range(max(0, map_height - zone_depth_units), map_height)
                ]
                
        elif self.config.deployment == DeploymentType.SEARCH_AND_DESTROY:
            # Players deploy in opposite corners
            zone_size = min(6, map_width // 2, map_height // 2)  # 6x6 or smaller in units
            
            if len(player_ids) >= 2:
                # Player 1: bottom-left corner
                zones[player_ids[0]] = [
                    (x, y) for x in range(min(zone_size, map_width)) 
                    for y in range(min(zone_size, map_height))
                ]
                
                # Player 2: top-right corner
                zones[player_ids[1]] = [
                    (x, y) for x in range(max(0, map_width - zone_size), map_width) 
                    for y in range(max(0, map_height - zone_size), map_height)
                ]
                
        elif self.config.deployment == DeploymentType.CRUCIBLE_OF_BATTLE:
            # Players deploy in long table edges
            if len(player_ids) >= 2:
                # Player 1: bottom edge
                zones[player_ids[0]] = [
                    (x, y) for x in range(map_width) 
                    for y in range(min(zone_depth_units, map_height))
                ]
                
                # Player 2: top edge
                zones[player_ids[1]] = [
                    (x, y) for x in range(map_width) 
                    for y in range(max(0, map_height - zone_depth_units), map_height)
                ]
        
        return zones
    
    def is_valid_deployment_position(self, player_id: str, position: Tuple[int, int]) -> bool:
        """Check if a position is valid for player deployment."""
        zones = self.get_deployment_zones()
        if player_id not in zones:
            return False
            
        return position in zones[player_id]
    
    def get_mission_summary(self) -> Dict[str, any]:
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
                    "is_contested": obj.is_contested
                }
                for obj in self.config.objectives
            ],
            "current_vp": self.calculate_victory_points()
        }


# Factory functions for creating missions
def create_mission(mission_name: str, game_state: 'GameState') -> Optional['Mission']:
    """Create a mission by name."""
    mission_func = MISSIONS.get(mission_name.lower().replace(" ", "_"))
    if mission_func:
        config = mission_func()
        return Mission(config=config, state=game_state)
    return None


def _only_war() -> MissionConfig:
    """Only War: 3 objectives, hold more = VP, progressive scoring."""
    return MissionConfig(
        name="Only War",
        deployment=DeploymentType.DAWN_OF_WAR,
        description="Standard mission: hold more objectives to score.",
        objectives=[
            MissionObjective(2, 2, "Center"),      # Adjusted for 6x4 map
            MissionObjective(1, 3, "Flank Left"),
            MissionObjective(4, 3, "Flank Right"),
        ],
        scoring_rule="progressive",
    )


def _purge_the_foe() -> MissionConfig:
    """Purge the Foe: Slay the Warlord + kill points."""
    return MissionConfig(
        name="Purge the Foe",
        deployment=DeploymentType.SEARCH_AND_DESTROY,
        description="Kill more pts than opponent each round.",
        objectives=[],  # no objectives
        scoring_rule="kill_points",
    )


def _take_and_hold() -> MissionConfig:
    """Take and Hold: 5 objectives, score end of each Command phase."""
    return MissionConfig(
        name="Take and Hold",
        deployment=DeploymentType.CRUCIBLE_OF_BATTLE,
        description="Control objectives to score at end of Command phase.",
        objectives=[
            MissionObjective(2, 1, "Home A"),      # Adjusted for 6x4 map
            MissionObjective(1, 3, "Mid Left"),
            MissionObjective(4, 3, "Mid Right"),
            MissionObjective(2, 3, "Center"),
            MissionObjective(2, 2, "Home B"),
        ],
        scoring_rule="standard",
    )


# Registry of available missions
MISSIONS: Dict[str, Callable[[], MissionConfig]] = {}

MISSIONS["only_war"] = _only_war
MISSIONS["purge_the_foe"] = _purge_the_foe
MISSIONS["take_and_hold"] = _take_and_hold