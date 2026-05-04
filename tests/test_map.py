"""Test the 2D battlefield map system."""

import numpy as np
import pytest

from backend.state.map import (
    BattlefieldMap,
    DeploymentType,
    DeploymentZone,
    TerrainType,
    create_dawn_of_war_map,
    create_spearhead_map,
)


def test_battlefield_map_creation():
    """Test basic battlefield map creation."""
    battlefield = BattlefieldMap.create_empty(6, 4, "Test Map")

    assert battlefield.width == 6
    assert battlefield.height == 4
    assert battlefield.name == "Test Map"
    assert battlefield.terrain.shape == (4, 6)
    assert np.all(battlefield.terrain == TerrainType.OPEN_GROUND)


def test_terrain_operations():
    """Test setting and getting terrain."""
    battlefield = BattlefieldMap.create_empty(6, 4)

    # Set terrain
    battlefield.set_terrain(2, 1, TerrainType.DIFFICULT_TERRAIN)
    battlefield.set_terrain(3, 2, TerrainType.DANGEROUS_TERRAIN)

    # Get terrain
    assert battlefield.get_terrain(2, 1) == TerrainType.DIFFICULT_TERRAIN
    assert battlefield.get_terrain(3, 2) == TerrainType.DANGEROUS_TERRAIN
    assert battlefield.get_terrain(0, 0) == TerrainType.OPEN_GROUND

    # Test out of bounds
    with pytest.raises(ValueError):
        battlefield.set_terrain(6, 0, TerrainType.IMPASSABLE)

    with pytest.raises(ValueError):
        battlefield.get_terrain(-1, 2)


def test_deployment_zones():
    """Test deployment zone management."""
    battlefield = BattlefieldMap.create_empty(6, 4)

    # Add deployment zone
    coords = [(0, 0), (1, 0), (0, 1)]
    battlefield.add_deployment_zone(
        "test_zone", DeploymentType.PLAYER_1, coords, "Test deployment zone"
    )

    assert "test_zone" in battlefield.deployment_zones
    zone = battlefield.deployment_zones["test_zone"]
    assert zone.deployment_type == DeploymentType.PLAYER_1
    assert zone.area == 3
    assert zone.contains_position(0, 0)
    assert zone.contains_position(1, 0)
    assert zone.contains_position(0, 1)
    assert not zone.contains_position(2, 2)

    # Test invalid coordinates
    with pytest.raises(ValueError):
        battlefield.add_deployment_zone("invalid", DeploymentType.PLAYER_2, [(-1, 0)])


def test_objectives():
    """Test objective placement."""
    battlefield = BattlefieldMap.create_empty(6, 4)

    battlefield.add_objective("obj_a", (2, 1))
    battlefield.add_objective("obj_b", (3, 2))

    assert battlefield.objectives["obj_a"] == (2, 1)
    assert battlefield.objectives["obj_b"] == (3, 2)

    # Test invalid position
    with pytest.raises(ValueError):
        battlefield.add_objective("invalid", (6, 4))


def test_deployment_validation():
    """Test deployment position validation."""
    battlefield = BattlefieldMap.create_empty(6, 4)

    # Add deployment zones
    battlefield.add_deployment_zone("p1_zone", DeploymentType.PLAYER_1, [(0, 0), (1, 0), (0, 1)])

    battlefield.add_deployment_zone("p2_zone", DeploymentType.PLAYER_2, [(4, 2), (5, 2), (4, 3)])

    # Test valid deployments
    assert battlefield.is_valid_deployment_position(0, 0, "player1")
    assert battlefield.is_valid_deployment_position(4, 2, "player2")

    # Test invalid deployments
    assert not battlefield.is_valid_deployment_position(4, 2, "player1")
    assert not battlefield.is_valid_deployment_position(0, 0, "player2")

    # Test player zone lookup
    p1_zone = battlefield.get_deployment_zone_for_player("player1")
    assert p1_zone is not None
    assert p1_zone.deployment_type == DeploymentType.PLAYER_1

    p2_zone = battlefield.get_deployment_zone_for_player("player2")
    assert p2_zone is not None
    assert p2_zone.deployment_type == DeploymentType.PLAYER_2


def test_terrain_cost():
    """Test terrain movement cost calculation."""
    battlefield = BattlefieldMap.create_empty(6, 4)

    battlefield.set_terrain(1, 1, TerrainType.DIFFICULT_TERRAIN)
    battlefield.set_terrain(2, 2, TerrainType.DANGEROUS_TERRAIN)
    battlefield.set_terrain(3, 3, TerrainType.IMPASSABLE)

    assert battlefield.get_terrain_cost(0, 0) == 1  # Open ground
    assert battlefield.get_terrain_cost(1, 1) == 2  # Difficult
    assert battlefield.get_terrain_cost(2, 2) == 2  # Dangerous
    assert battlefield.get_terrain_cost(3, 3) == 999  # Impassable


def test_neighbors():
    """Test neighbor position calculation."""
    battlefield = BattlefieldMap.create_empty(6, 4)

    # Corner position
    neighbors = battlefield.get_neighbors(0, 0)
    assert len(neighbors) == 3
    assert (0, 1) in neighbors
    assert (1, 0) in neighbors
    assert (1, 1) in neighbors

    # Center position
    neighbors = battlefield.get_neighbors(2, 1)
    assert len(neighbors) == 8

    # Edge position
    neighbors = battlefield.get_neighbors(5, 2)
    assert len(neighbors) == 5


def test_distance_calculation():
    """Test distance calculations."""
    battlefield = BattlefieldMap.create_empty(6, 4)

    assert battlefield.calculate_distance((0, 0), (3, 4)) == 5.0
    assert battlefield.calculate_distance((1, 1), (1, 1)) == 0.0
    assert battlefield.calculate_distance((0, 0), (1, 1)) == 1.4142135623730951


def test_simple_pathfinding():
    """Test basic pathfinding."""
    battlefield = BattlefieldMap.create_empty(6, 4)

    # Set impassable terrain
    battlefield.set_terrain(2, 1, TerrainType.IMPASSABLE)

    # Test valid path
    path = battlefield.find_path((0, 0), (3, 2))
    assert path is not None
    assert len(path) > 1
    assert path[0] == (0, 0)
    assert path[-1] == (3, 2)

    # Test blocked path
    path = battlefield.find_path((0, 0), (2, 1))
    assert path is None  # Impassable terrain

    # Test invalid positions
    path = battlefield.find_path((-1, 0), (3, 2))
    assert path is None


def test_standard_map():
    """Test the standard battlefield creation."""
    battlefield = BattlefieldMap.create_standard()

    assert battlefield.width == 6
    assert battlefield.height == 4
    assert battlefield.name == "Standard Battlefield"

    # Check terrain placement
    assert battlefield.get_terrain(1, 2) == TerrainType.DIFFICULT_TERRAIN
    assert battlefield.get_terrain(2, 3) == TerrainType.DIFFICULT_TERRAIN
    assert battlefield.get_terrain(5, 0) == TerrainType.DANGEROUS_TERRAIN

    # Check deployment zones
    assert len(battlefield.deployment_zones) == 2
    p1_zone = battlefield.deployment_zones["player1_deployment"]
    assert p1_zone.deployment_type == DeploymentType.PLAYER_1
    assert p1_zone.area == 6

    # Check objectives
    assert len(battlefield.objectives) == 3
    assert battlefield.objectives["objective_a"] == (1, 2)


def test_mission_maps():
    """Test specific mission map creation."""
    dawn_of_war = create_dawn_of_war_map()
    assert dawn_of_war.name == "Dawn of War"
    assert len(dawn_of_war.deployment_zones) == 2
    assert len(dawn_of_war.objectives) == 4

    spearhead = create_spearhead_map()
    assert spearhead.name == "Spearhead"
    assert len(spearhead.deployment_zones) == 2

    # Player 1 zone should have 9 cells (north edge)
    p1_zone = spearhead.deployment_zones["player1_deployment"]
    assert p1_zone.area == 9

    # Player 2 zone should have 9 cells (south edge)
    p2_zone = spearhead.deployment_zones["player2_deployment"]
    assert p2_zone.area == 9


def test_map_summary():
    """Test map summary generation."""
    battlefield = BattlefieldMap.create_standard()
    summary = battlefield.get_map_summary()

    assert summary["name"] == "Standard Battlefield"
    assert summary["dimensions"] == "6x4"
    assert "terrain_distribution" in summary
    assert "deployment_zones" in summary
    assert "objectives" in summary

    # Check terrain counts
    terrain_dist = summary["terrain_distribution"]
    assert terrain_dist["open_ground"] == 6 * 4 - 4  # Total cells minus special terrain
    assert terrain_dist["difficult_terrain"] == 3
    assert terrain_dist["dangerous_terrain"] == 1
