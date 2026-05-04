"""
F3.4 — Deployment AI: Zone Placement Logic.

Размещает юниты в deploy zone согласно миссии.
Поддержка: STANDARD, HAMMER_AND_ANVIL, SEARCH_AND_DESTROY, DAWN_OF_WAR.

Зависимости: backend.state.game_state (GameState, UnitState, TerrainType),
             backend.state.map (BattlefieldMap),
             backend.state.mission (Mission, MissionObjective),
             backend.model.unit (Unit)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from backend.model.unit import Unit
from backend.state.game_state import GameState, TerrainType, UnitState
from backend.state.map import BattlefieldMap
from backend.state.mission import MissionObjective


class DeploymentType(Enum):
    STANDARD = "standard"
    HAMMER_AND_ANVIL = "hammer_and_anvil"
    SEARCH_AND_DESTROY = "search_and_destroy"
    DAWN_OF_WAR = "dawn_of_war"


@dataclass
class DeploymentZone:
    player: int
    x_min: int
    x_max: int
    y_min: int
    y_max: int
    label: str = ""

    def contains(self, x: int, y: int) -> bool:
        return self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max


@dataclass
class Placement:
    unit_id: str
    x: int
    y: int
    is_in_cover: bool = False
    is_on_objective: bool = False


def get_deployment_zone(
    deployment_type: DeploymentType,
    player: int,
    map_size: tuple[int, int],
) -> DeploymentZone:
    w, h = map_size

    if deployment_type == DeploymentType.STANDARD:
        if player == 1:
            return DeploymentZone(1, 0, w // 3, 0, h, "P1 Standard")
        return DeploymentZone(2, 2 * w // 3, w, 0, h, "P2 Standard")

    if deployment_type == DeploymentType.HAMMER_AND_ANVIL:
        if player == 1:
            return DeploymentZone(1, 0, w // 4, 0, h, "P1 Hammer")
        return DeploymentZone(2, 3 * w // 4, w, 0, h, "P2 Anvil")

    if deployment_type == DeploymentType.SEARCH_AND_DESTROY:
        if player == 1:
            return DeploymentZone(1, 0, w // 3, 0, h // 3, "P1 S&D")
        return DeploymentZone(2, 2 * w // 3, w, 2 * h // 3, h, "P2 S&D")

    if deployment_type == DeploymentType.DAWN_OF_WAR:
        if player == 1:
            return DeploymentZone(1, 0, w // 2, 0, h // 4, "P1 DoW")
        return DeploymentZone(2, 0, w // 2, 3 * h // 4, h, "P2 DoW")

    msg = f"Unknown deployment type: {deployment_type}"
    raise ValueError(msg)


def _distance(a: tuple[int, int], b: tuple[int, int]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def _is_melee_unit(unit_state: UnitState, unit_model: Unit | None = None) -> bool:
    if unit_model is not None:
        if unit_model.melee_weapons and not unit_model.ranged_weapons:
            return True
        melee_total = sum(_avg_dice_simple(w.attacks_dice) for w in unit_model.melee_weapons)
        ranged_total = sum(_avg_dice_simple(w.attacks_dice) for w in unit_model.ranged_weapons)
        return melee_total > ranged_total
    keywords = getattr(unit_state, "keywords", [])
    if isinstance(keywords, (list, tuple)):
        return any(k in keywords for k in ("melee", "assault", "berserker"))
    return False


def _is_ranged_unit(unit_state: UnitState, unit_model: Unit | None = None) -> bool:
    if unit_model is not None:
        if unit_model.ranged_weapons and not unit_model.melee_weapons:
            return True
        melee_total = sum(_avg_dice_simple(w.attacks_dice) for w in unit_model.melee_weapons)
        ranged_total = sum(_avg_dice_simple(w.attacks_dice) for w in unit_model.ranged_weapons)
        return ranged_total >= melee_total
    return not _is_melee_unit(unit_state, unit_model)


def _avg_dice_simple(dice: tuple[int, int, int]) -> float:
    count, sides, modifier = dice
    if count == 0:
        return float(modifier)
    return count * (sides + 1) / 2 + modifier


def _has_cover_at(battlefield: BattlefieldMap | None, x: int, y: int) -> bool:
    if battlefield is None:
        return False
    if not (0 <= x < battlefield.width and 0 <= y < battlefield.height):
        return False
    terrain = battlefield.get_terrain(x, y)
    return terrain in (TerrainType.DIFFICULT_TERRAIN, TerrainType.DANGEROUS_TERRAIN)


def _is_walkable(battlefield: BattlefieldMap | None, x: int, y: int) -> bool:
    if battlefield is None:
        return True
    if not (0 <= x < battlefield.width and 0 <= y < battlefield.height):
        return False
    return battlefield.get_terrain(x, y) != TerrainType.IMPASSABLE


def _is_on_objective(
    pos: tuple[int, int],
    objectives: list[MissionObjective],
) -> bool:
    return any(_distance(pos, (obj.x, obj.y)) <= 3 for obj in objectives)


def _is_occupied(
    x: int,
    y: int,
    occupied: set[tuple[int, int]],
    margin: int = 2,
) -> bool:
    return any(abs(x - ox) <= margin and abs(y - oy) <= margin for ox, oy in occupied)


def _sort_units_by_role(
    units: list[UnitState],
    unit_models: dict[str, Unit] | None = None,
    warlord_id: str | None = None,
) -> list[UnitState]:
    def sort_key(unit: UnitState) -> int:
        model = unit_models.get(unit.unit_id) if unit_models else None
        if warlord_id and unit.unit_id == warlord_id:
            return 0
        keywords = getattr(unit, "keywords", [])
        if isinstance(keywords, (list, tuple)) and "transport" in keywords:
            return 1
        if _is_melee_unit(unit, model):
            return 2
        if isinstance(keywords, (list, tuple)) and "battleline" in keywords:
            return 3
        if _is_ranged_unit(unit, model):
            return 4
        return 5

    return sorted(units, key=sort_key)


def _find_first_free(
    zone: DeploymentZone,
    occupied: set[tuple[int, int]],
) -> tuple[int, int] | None:
    for x in range(zone.x_min, zone.x_max + 1):
        for y in range(zone.y_min, zone.y_max + 1):
            if (x, y) not in occupied:
                return (x, y)
    return None


def _find_best_position(
    unit: UnitState,
    zone: DeploymentZone,
    battlefield: BattlefieldMap | None,
    objectives: list[MissionObjective],
    occupied: set[tuple[int, int]],
    unit_model: Unit | None = None,
    warlord_id: str | None = None,
    is_p1: bool = True,
) -> tuple[int, int] | None:
    best_score = -1.0
    best_pos: tuple[int, int] | None = None

    front_edge_x = zone.x_max if is_p1 else zone.x_min
    center = (
        (zone.x_min + zone.x_max) // 2,
        (zone.y_min + zone.y_max) // 2,
    )

    for x in range(zone.x_min, zone.x_max + 1):
        for y in range(zone.y_min, zone.y_max + 1):
            if _is_occupied(x, y, occupied, margin=2):
                continue
            if not _is_walkable(battlefield, x, y):
                continue

            score = 0.0

            if _is_ranged_unit(unit, unit_model) and _has_cover_at(battlefield, x, y):
                score += 0.5

            if _is_melee_unit(unit, unit_model):
                dist_to_front = abs(x - front_edge_x)
                max_depth = abs(zone.x_max - zone.x_min) or 1
                score += 0.8 * (1.0 - dist_to_front / max_depth)
                if _is_on_objective((x, y), objectives):
                    score += 0.8

            if warlord_id and unit.unit_id == warlord_id:
                dist_center = _distance((x, y), center)
                score += 0.3 * max(0.0, 1.0 - dist_center / 20.0)

            if score > best_score:
                best_score = score
                best_pos = (x, y)

    return best_pos or _find_first_free(zone, occupied)


def place_units(
    player_units: list[UnitState],
    unit_models: dict[str, Unit] | None = None,
    deployment_type: DeploymentType = DeploymentType.STANDARD,
    player: int = 1,
    map_size: tuple[int, int] = (60, 44),
    battlefield: BattlefieldMap | None = None,
    objectives: list[MissionObjective] | None = None,
    warlord_id: str | None = None,
) -> list[Placement]:
    zone = get_deployment_zone(deployment_type, player, map_size)
    sorted_units = _sort_units_by_role(player_units, unit_models, warlord_id)
    occupied: set[tuple[int, int]] = set()
    placements: list[Placement] = []
    is_p1 = player == 1

    for unit in sorted_units:
        model = unit_models.get(unit.unit_id) if unit_models else None
        pos = _find_best_position(
            unit,
            zone,
            battlefield,
            objectives or [],
            occupied,
            model,
            warlord_id,
            is_p1,
        )
        if pos is not None:
            placements.append(
                Placement(
                    unit_id=unit.unit_id,
                    x=pos[0],
                    y=pos[1],
                    is_in_cover=_has_cover_at(battlefield, pos[0], pos[1]),
                    is_on_objective=_is_on_objective(pos, objectives or []),
                )
            )
            occupied.add(pos)

    return placements


def deploy_game(
    game_state: GameState,
    unit_models: dict[str, Unit] | None = None,
    deployment_type: DeploymentType = DeploymentType.STANDARD,
    battlefield: BattlefieldMap | None = None,
    objectives: list[MissionObjective] | None = None,
) -> dict[str, list[Placement]]:
    map_size = (game_state.map_width, game_state.map_height)
    result: dict[str, list[Placement]] = {}
    player_list = list(game_state.players.values())
    if len(player_list) < 2:
        return result

    for idx, player in enumerate(player_list, start=1):
        units = [u for u in player.units.values() if u.is_alive]
        warlord = player.warlord_unit
        warlord_id = warlord.unit_id if warlord else None

        placements = place_units(
            player_units=units,
            unit_models=unit_models,
            deployment_type=deployment_type,
            player=idx,
            map_size=map_size,
            battlefield=battlefield,
            objectives=objectives,
            warlord_id=warlord_id,
        )
        result[player.player_id] = placements

        for p in placements:
            if p.unit_id in player.units:
                player.units[p.unit_id].position = (p.x, p.y)

    return result
