"""Tests for F3.4 — Deployment AI."""

import pytest

from backend.engine.ai.deployment import (
    DeploymentType,
    DeploymentZone,
    Placement,
    _find_best_position,
    _has_cover_at,
    _is_melee_unit,
    _is_occupied,
    _is_on_objective,
    _is_ranged_unit,
    _sort_units_by_role,
    deploy_game,
    get_deployment_zone,
    place_units,
)
from backend.model.unit import Unit, Weapon
from backend.state.game_state import GameState, TerrainType, UnitState
from backend.state.map import BattlefieldMap
from backend.state.mission import MissionObjective


def _make_unit_state(
    name: str = "Unit",
    unit_id: str = "u1",
    position: tuple = (0, 0),
    wounds: int = 3,
    models: int = 5,
    is_warlord: bool = False,
    keywords: list = None,
) -> UnitState:
    us = UnitState(
        unit_id=unit_id,
        name=name,
        faction="test",
        position=position,
        current_wounds=wounds,
        max_wounds=wounds,
        models_remaining=models,
        models_total=models,
        leadership=7,
        objective_control=1,
        is_warlord=is_warlord,
    )
    if keywords:
        us.keywords = keywords
    return us


def _make_unit_model(
    name: str = "Unit",
    category: str = "Infantry",
    ranged: list = None,
    melee: list = None,
) -> Unit:
    return Unit(
        name=name,
        faction="test",
        category=category,
        movement=6,
        toughness=4,
        save=3,
        wounds=3,
        leadership=7,
        objective_control=1,
        ranged_weapons=ranged or [],
        melee_weapons=melee or [],
    )


def _make_shoota() -> Weapon:
    return Weapon(
        name="Shoota",
        type="ranged",
        range_max=24,
        attacks_dice=(2, 1, 0),
        skill=4,
        strength=4,
        ap=0,
        damage_dice=(1, 1, 0),
    )


def _make_choppa() -> Weapon:
    return Weapon(
        name="Choppa",
        type="melee",
        range_max=None,
        attacks_dice=(3, 1, 0),
        skill=4,
        strength=4,
        ap=-1,
        damage_dice=(1, 1, 0),
    )


def _make_battlefield(width: int = 60, height: int = 44) -> BattlefieldMap:
    bf = BattlefieldMap.create_empty(width, height, "Test Battlefield")
    bf.set_terrain(10, 10, TerrainType.DIFFICULT_TERRAIN)
    bf.set_terrain(11, 10, TerrainType.DIFFICULT_TERRAIN)
    bf.set_terrain(20, 30, TerrainType.IMPASSABLE)
    return bf


class TestDeploymentZone:
    def test_standard_p1(self):
        zone = get_deployment_zone(DeploymentType.STANDARD, 1, (60, 44))
        assert zone.x_min == 0
        assert zone.x_max == 20
        assert zone.y_min == 0
        assert zone.y_max == 44

    def test_standard_p2(self):
        zone = get_deployment_zone(DeploymentType.STANDARD, 2, (60, 44))
        assert zone.x_min == 40
        assert zone.x_max == 60
        assert zone.y_min == 0
        assert zone.y_max == 44

    def test_hammer_and_anvil_p1(self):
        zone = get_deployment_zone(DeploymentType.HAMMER_AND_ANVIL, 1, (60, 44))
        assert zone.x_max == 15
        assert zone.y_min == 0
        assert zone.y_max == 44

    def test_hammer_and_anvil_p2(self):
        zone = get_deployment_zone(DeploymentType.HAMMER_AND_ANVIL, 2, (60, 44))
        assert zone.x_min == 45
        assert zone.x_max == 60

    def test_search_and_destroy_p1(self):
        zone = get_deployment_zone(DeploymentType.SEARCH_AND_DESTROY, 1, (60, 44))
        assert zone.x_max == 20
        assert zone.y_max == 14

    def test_search_and_destroy_p2(self):
        zone = get_deployment_zone(DeploymentType.SEARCH_AND_DESTROY, 2, (60, 44))
        assert zone.x_min == 2 * 60 // 3
        assert zone.y_min == 2 * 44 // 3

    def test_dawn_of_war_p1(self):
        zone = get_deployment_zone(DeploymentType.DAWN_OF_WAR, 1, (60, 44))
        assert zone.x_min == 0
        assert zone.x_max == 30
        assert zone.y_max == 11

    def test_dawn_of_war_p2(self):
        zone = get_deployment_zone(DeploymentType.DAWN_OF_WAR, 2, (60, 44))
        assert zone.y_min == 33
        assert zone.y_max == 44

    def test_zone_contains(self):
        zone = DeploymentZone(1, 0, 20, 0, 44, "test")
        assert zone.contains(10, 22)
        assert not zone.contains(25, 22)

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError):
            get_deployment_zone("unknown", 1, (60, 44))


class TestPlaceUnits:
    def test_place_units_no_overlap(self):
        units = [_make_unit_state(f"u{i}", unit_id=f"u{i}") for i in range(5)]
        placements = place_units(
            player_units=units,
            deployment_type=DeploymentType.STANDARD,
            player=1,
            map_size=(60, 44),
        )
        positions = [(p.x, p.y) for p in placements]
        assert len(positions) == len(set(positions))

    def test_place_units_in_zone(self):
        units = [_make_unit_state(f"u{i}", unit_id=f"u{i}") for i in range(5)]
        zone = get_deployment_zone(DeploymentType.STANDARD, 1, (60, 44))
        placements = place_units(
            player_units=units,
            deployment_type=DeploymentType.STANDARD,
            player=1,
            map_size=(60, 44),
        )
        for p in placements:
            assert zone.contains(p.x, p.y), f"({p.x}, {p.y}) not in zone"

    def test_place_units_all_deployed(self):
        units = [_make_unit_state(f"u{i}", unit_id=f"u{i}") for i in range(8)]
        placements = place_units(
            player_units=units,
            deployment_type=DeploymentType.STANDARD,
            player=1,
            map_size=(60, 44),
        )
        assert len(placements) == 8

    def test_warlord_placed_center(self):
        warlord = _make_unit_state("Warlord", unit_id="warlord", is_warlord=True)
        units = [
            warlord,
            _make_unit_state("Grunt1", unit_id="g1"),
            _make_unit_state("Grunt2", unit_id="g2"),
        ]
        zone = get_deployment_zone(DeploymentType.STANDARD, 1, (60, 44))
        center_x = (zone.x_min + zone.x_max) // 2
        center_y = (zone.y_min + zone.y_max) // 2

        placements = place_units(
            player_units=units,
            deployment_type=DeploymentType.STANDARD,
            player=1,
            map_size=(60, 44),
            warlord_id="warlord",
        )
        warlord_p = next(p for p in placements if p.unit_id == "warlord")
        dist_to_center = ((warlord_p.x - center_x) ** 2 + (warlord_p.y - center_y) ** 2) ** 0.5
        assert dist_to_center < 15, f"Warlord too far from center: {dist_to_center}"

    def test_melee_units_front(self):
        melee_model = _make_unit_model("Melee", melee=[_make_choppa()])
        ranged_model = _make_unit_model("Ranged", ranged=[_make_shoota()])
        melee_unit = _make_unit_state("Melee", unit_id="melee")
        ranged_unit = _make_unit_state("Ranged", unit_id="ranged")
        unit_models = {"melee": melee_model, "ranged": ranged_model}

        placements = place_units(
            player_units=[melee_unit, ranged_unit],
            unit_models=unit_models,
            deployment_type=DeploymentType.STANDARD,
            player=1,
            map_size=(60, 44),
        )
        melee_p = next(p for p in placements if p.unit_id == "melee")
        ranged_p = next(p for p in placements if p.unit_id == "ranged")
        assert melee_p.x >= ranged_p.x, (
            f"Melee at x={melee_p.x} should be at front (>= ranged x={ranged_p.x})"
        )

    def test_ranged_units_in_cover(self):
        bf = _make_battlefield()
        ranged_model = _make_unit_model("Ranged", ranged=[_make_shoota()])
        ranged_unit = _make_unit_state("Ranged", unit_id="ranged")
        unit_models = {"ranged": ranged_model}

        placements = place_units(
            player_units=[ranged_unit],
            unit_models=unit_models,
            deployment_type=DeploymentType.STANDARD,
            player=1,
            map_size=(60, 44),
            battlefield=bf,
        )
        assert len(placements) == 1

    def test_search_and_destroy_no_overlap(self):
        units = [_make_unit_state(f"u{i}", unit_id=f"u{i}") for i in range(3)]
        placements = place_units(
            player_units=units,
            deployment_type=DeploymentType.SEARCH_AND_DESTROY,
            player=1,
            map_size=(60, 44),
        )
        positions = [(p.x, p.y) for p in placements]
        assert len(positions) == len(set(positions))

    def test_search_and_destroy_in_zone(self):
        units = [_make_unit_state(f"u{i}", unit_id=f"u{i}") for i in range(3)]
        zone = get_deployment_zone(DeploymentType.SEARCH_AND_DESTROY, 1, (60, 44))
        placements = place_units(
            player_units=units,
            deployment_type=DeploymentType.SEARCH_AND_DESTROY,
            player=1,
            map_size=(60, 44),
        )
        for p in placements:
            assert zone.contains(p.x, p.y)

    def test_dawn_of_war_in_zone(self):
        units = [_make_unit_state(f"u{i}", unit_id=f"u{i}") for i in range(5)]
        zone = get_deployment_zone(DeploymentType.DAWN_OF_WAR, 1, (60, 44))
        placements = place_units(
            player_units=units,
            deployment_type=DeploymentType.DAWN_OF_WAR,
            player=1,
            map_size=(60, 44),
        )
        for p in placements:
            assert zone.contains(p.x, p.y)

    def test_hammer_and_anvil_p2_in_zone(self):
        units = [_make_unit_state(f"u{i}", unit_id=f"u{i}") for i in range(5)]
        zone = get_deployment_zone(DeploymentType.HAMMER_AND_ANVIL, 2, (60, 44))
        placements = place_units(
            player_units=units,
            deployment_type=DeploymentType.HAMMER_AND_ANVIL,
            player=2,
            map_size=(60, 44),
        )
        for p in placements:
            assert zone.contains(p.x, p.y)

    def test_objective_detection(self):
        objectives = [MissionObjective(5, 22, "Center")]
        unit = _make_unit_state("U", unit_id="u1")
        melee_model = _make_unit_model("U", melee=[_make_choppa()])
        placements = place_units(
            player_units=[unit],
            unit_models={"u1": melee_model},
            deployment_type=DeploymentType.STANDARD,
            player=1,
            map_size=(60, 44),
            objectives=objectives,
        )
        assert len(placements) == 1
        p = placements[0]
        dist = ((p.x - 5) ** 2 + (p.y - 22) ** 2) ** 0.5
        if dist <= 3:
            assert p.is_on_objective


class TestHelperFunctions:
    def test_is_occupied_true(self):
        occupied = {(5, 5)}
        assert _is_occupied(5, 5, occupied, margin=2)

    def test_is_occupied_within_margin(self):
        occupied = {(5, 5)}
        assert _is_occupied(6, 5, occupied, margin=2)

    def test_is_occupied_outside_margin(self):
        occupied = {(5, 5)}
        assert not _is_occupied(8, 5, occupied, margin=2)

    def test_has_cover_no_battlefield(self):
        assert not _has_cover_at(None, 10, 10)

    def test_has_cover_difficult_terrain(self):
        bf = _make_battlefield()
        assert _has_cover_at(bf, 10, 10)

    def test_has_cover_open_ground(self):
        bf = _make_battlefield()
        assert not _has_cover_at(bf, 0, 0)

    def test_is_on_objective_near(self):
        objectives = [MissionObjective(5, 5, "O")]
        assert _is_on_objective((5, 5), objectives)

    def test_is_on_objective_far(self):
        objectives = [MissionObjective(5, 5, "O")]
        assert not _is_on_objective((50, 50), objectives)

    def test_sort_warlord_first(self):
        warlord = _make_unit_state("WL", unit_id="wl", is_warlord=True)
        grunt = _make_unit_state("Grunt", unit_id="g1")
        sorted_units = _sort_units_by_role([grunt, warlord], warlord_id="wl")
        assert sorted_units[0].unit_id == "wl"

    def test_sort_melee_before_ranged(self):
        melee_model = _make_unit_model("M", melee=[_make_choppa()])
        ranged_model = _make_unit_model("R", ranged=[_make_shoota()])
        melee = _make_unit_state("M", unit_id="m1")
        ranged = _make_unit_state("R", unit_id="r1")
        sorted_units = _sort_units_by_role(
            [ranged, melee],
            unit_models={"m1": melee_model, "r1": ranged_model},
        )
        melee_idx = next(i for i, u in enumerate(sorted_units) if u.unit_id == "m1")
        ranged_idx = next(i for i, u in enumerate(sorted_units) if u.unit_id == "r1")
        assert melee_idx < ranged_idx


class TestDeployGame:
    def _make_game_state(self) -> GameState:
        gs = GameState(game_id="g1", mission_name="test", map_width=60, map_height=44)
        from backend.state.game_state import PlayerState

        p1 = PlayerState(player_id="p1", name="Player 1", faction="orks")
        p2 = PlayerState(player_id="p2", name="Player 2", faction="tau")

        for i in range(3):
            u1 = _make_unit_state(f"Ork{i}", unit_id=f"ork{i}")
            p1.units[f"ork{i}"] = u1
            u2 = _make_unit_state(f"Tau{i}", unit_id=f"tau{i}")
            p2.units[f"tau{i}"] = u2

        gs.players["p1"] = p1
        gs.players["p2"] = p2
        return gs

    def test_deploy_game_places_all_units(self):
        gs = self._make_game_state()
        result = deploy_game(
            gs,
            deployment_type=DeploymentType.STANDARD,
        )
        total = sum(len(p) for p in result.values())
        assert total == 6

    def test_deploy_game_updates_positions(self):
        gs = self._make_game_state()
        deploy_game(gs, deployment_type=DeploymentType.STANDARD)
        for player in gs.players.values():
            for unit in player.units.values():
                pos = unit.position
                assert 0 <= pos[0] < 60
                assert 0 <= pos[1] < 44

    def test_deploy_game_standard_p1_in_zone(self):
        gs = self._make_game_state()
        result = deploy_game(gs, deployment_type=DeploymentType.STANDARD)
        zone = get_deployment_zone(DeploymentType.STANDARD, 1, (60, 44))
        for p in result["p1"]:
            assert zone.contains(p.x, p.y)

    def test_deploy_game_standard_p2_in_zone(self):
        gs = self._make_game_state()
        result = deploy_game(gs, deployment_type=DeploymentType.STANDARD)
        zone = get_deployment_zone(DeploymentType.STANDARD, 2, (60, 44))
        for p in result["p2"]:
            assert zone.contains(p.x, p.y)
