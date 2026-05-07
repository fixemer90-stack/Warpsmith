"""JSON API для симуляции."""

import contextlib
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.engine.combat import MultiAttackResult, simulate_unit_attack, simulate_weapon_attack
from backend.engine.dice import DicePool
from backend.loader.registry import registry as wiki

router = APIRouter()


class SimulationRequest(BaseModel):
    attacker_faction: str = Field(..., description="Faction of the attacking unit")

    attacker_unit: str = Field(..., description="Name of the attacking unit")

    defender_faction: str = Field(..., description="Faction of the defending unit")

    defender_unit: str = Field(..., description="Name of the defending unit")

    weapon_name: str = Field(..., description="Name of the weapon to use")

    distance: int | None = Field(None, description="Distance in inches (for rapid fire, etc.)")

    squad_size: int = Field(1, description="Size of the target squad (for blast weapons)")

    n_iterations: int = Field(10000, description="Number of Monte Carlo iterations")


def _unit_icons(unit) -> list[str]:
    """All SVG icons for a unit based on its YAML tags, in priority order."""

    tags = {t.lower().replace(" ", "-") for t in unit.tags}

    priority = [
        "legends",
        "epic-hero",
        "psyker",
        "titanic",
        "monster",
        "dreadnought",
        "walker",
        "battlesuit",
        "transport",
        "vehicle",
        "fly",
        "artillery",
        "battleline",
        "character",
        "elite",
        "infantry",
        "medic",
        "speed-freek",
    ]

    seen = set()

    result = []

    for icon in priority:
        if icon in tags and icon not in seen:
            result.append(icon)

            seen.add(icon)

    return result


@router.get("/units")
async def list_units(faction: str = ""):
    """Список юнитов (всех или по фракции)."""

    try:
        wiki.load()

    except Exception:
        return {"faction": faction, "units": []}

    if faction:
        unit_names = wiki.list_units(faction)

    else:
        unit_names = wiki.list_units()

    result = []

    for name in unit_names:
        unit = wiki.get_unit(name)

        if unit:
            # Derive squad_size from model_count if still default
            squad = getattr(unit, "squad_size", {"min": 1, "max": 1, "step": 1})
            if squad.get("min") == 1 and squad.get("max") == 1:
                min_m, max_m = unit.model_count
                if min_m != 1 or max_m != 1:
                    squad = {"min": min_m, "max": max_m, "step": 1}

            result.append(
                {
                    "name": unit.name,
                    "faction": unit.faction,
                    "category": unit.category,
                    "icon": _unit_icons(unit),
                    "points": unit.points,
                    "movement": unit.movement,
                    "toughness": unit.toughness,
                    "save": unit.save,
                    "wounds": unit.wounds,
                    "leadership": unit.leadership,
                    "oc": unit.objective_control,
                    "squad_size": squad,
                    "abilities": unit.abilities,
                    "weapons": [
                        {"name": w.name, "type": w.type}
                        for w in (unit.ranged_weapons + unit.melee_weapons)
                    ],
                }
            )

    return {"faction": faction, "units": result}


@router.post("/simulate")
async def run_simulation(request: SimulationRequest):
    """Запуск симуляции сценария."""

    # Fetch units and weapon from the wiki registry

    with contextlib.suppress(Exception):
        wiki.load()

    attacker_unit = wiki.get_unit(request.attacker_unit)

    defender_unit = wiki.get_unit(request.defender_unit)

    if not attacker_unit:
        raise HTTPException(
            status_code=404,
            detail=f"Attacker unit not found: {request.attacker_faction}/{request.attacker_unit}",
        )

    if not defender_unit:
        raise HTTPException(
            status_code=404,
            detail=f"Defender unit not found: {request.defender_faction}/{request.defender_unit}",
        )

    # Find weapon in attacker's weapon lists

    weapon = None

    for w in attacker_unit.ranged_weapons + attacker_unit.melee_weapons:
        if w.name.lower() == request.weapon_name.lower():
            weapon = w

            break

    if not weapon:
        raise HTTPException(
            status_code=404,
            detail=f"Weapon not found: {request.weapon_name} (check name or weapon list)",
        )

    # Create a dice pool (we can use a random seed or None for true randomness)

    pool = DicePool()

    # Run the simulation

    result = simulate_weapon_attack(
        weapon=weapon,
        attacker=attacker_unit,
        defender=defender_unit,
        pool=pool,
        n_iterations=request.n_iterations,
        distance=request.distance,
        squad_size=request.squad_size,
    )

    # Convert the CombatResult to a dictionary for JSON response

    response = {
        "weapon": result.weapon_name,
        "target": result.target_name,
        "stats": {
            "mean": result.stats.mean,
            "median": result.stats.median,
            "std": result.stats.std,
            "min": result.stats.min_val,
            "max": result.stats.max_val,
            "percentiles": result.stats.percentiles,
            "pmf": [[damage, prob] for damage, prob in result.stats.pmf],
            "kill_probability": result.stats.kill_probability,
        },
        "avg_attacks": result.avg_attacks,
        "avg_hits": result.avg_hits,
        "avg_wounds": result.avg_wounds,
        "avg_unsaved_wounds": result.avg_unsaved_wounds,
        "avg_damage_per_success": result.avg_damage_per_success,
        "n_iterations": result.n_iterations,
        "simulation_time_ms": result.simulation_time_ms,
    }

    return response


@router.post("/simulate-unit")
async def simulate_unit(request: SimulationRequest):
    """Simulate attack from a unit with multiple weapons against a defender."""

    # Fetch units from the wiki registry

    with contextlib.suppress(Exception):
        wiki.load()

    attacker_unit = wiki.get_unit(request.attacker_unit)

    defender_unit = wiki.get_unit(request.defender_unit)

    if not attacker_unit:
        raise HTTPException(
            status_code=404,
            detail=f"Attacker unit not found: {request.attacker_faction}/{request.attacker_unit}",
        )

    if not defender_unit:
        raise HTTPException(
            status_code=404,
            detail=f"Defender unit not found: {request.defender_faction}/{request.defender_unit}",
        )

    # Create a dice pool

    pool = DicePool()

    # Run the simulation

    result = simulate_unit_attack(
        attacker=attacker_unit,
        defender=defender_unit,
        pool=pool,
        n_iterations=request.n_iterations,
        distance=request.distance,
        squad_size=request.squad_size,
    )

    # Convert the MultiAttackResult to a dictionary for JSON response

    response = {
        "attacker": result.attacker_name,
        "defender": result.defender_name,
        "squad_size": result.squad_size,
        "total_stats": {
            "mean": result.total_stats.mean,
            "median": result.total_stats.median,
            "std": result.total_stats.std,
            "min": result.total_stats.min_val,
            "max": result.total_stats.max_val,
            "percentiles": result.total_stats.percentiles,
            "pmf": [[damage, prob] for damage, prob in result.total_stats.pmf],
            "kill_probability": result.total_stats.kill_probability,
        },
        "weapons": [
            {
                "name": weapon_result.weapon_name,
                "stats": {
                    "mean": weapon_result.stats.mean,
                    "median": weapon_result.stats.median,
                    "std": weapon_result.stats.std,
                    "kill_probability": weapon_result.stats.kill_probability,
                },
                "avg_attacks": weapon_result.avg_attacks,
                "avg_hits": weapon_result.avg_hits,
                "avg_wounds": weapon_result.avg_wounds,
                "avg_unsaved_wounds": weapon_result.avg_unsaved_wounds,
            }
            for weapon_result in result.weapon_results
        ],
        "n_iterations": result.n_iterations,
        "simulation_time_ms": result.simulation_time_ms,
    }

    return response


@router.get("/units/browse")
async def browse_units(
    faction: str | None = None,
    category: str | None = None,
    pts_min: int | None = None,
    pts_max: int | None = None,
    search: str | None = None,
    role: str | None = None,
    sort_by: str = "name",
    sort_dir: str = "asc",
    page: int = 1,
    per_page: int = 50,
):

    from backend.loader.icon_map import CATEGORY_COLORS, CATEGORY_ORDER, ICON_MAP

    try:
        wiki.load()

    except Exception:
        return {"items": [], "total": 0, "page": page, "pages": 0, "factions": [], "categories": []}

    all_units = list(wiki.units.values())

    if faction:
        all_units = [u for u in all_units if u.faction == faction]

    if category:
        all_units = [u for u in all_units if u.category.lower() == category.lower()]

    if pts_min is not None:
        all_units = [u for u in all_units if u.points >= pts_min]

    if pts_max is not None:
        all_units = [u for u in all_units if u.points <= pts_max]

    if search:
        q = search.lower()

        all_units = [u for u in all_units if q in u.name.lower() or q in u.faction.lower()]

    if role:
        role = role.lower()

        if role == "leader":
            all_units = [
                u
                for u in all_units
                if u.is_leader or u.can_be_warlord or u.category.lower() == "character"
            ]

        elif role == "transport":
            all_units = [
                u for u in all_units if "transport" in u.tags or u.category.lower() == "transport"
            ]

        elif role == "battleline":
            all_units = [
                u for u in all_units if u.category.lower() == "battleline" or "battleline" in u.tags
            ]

    reverse = sort_dir.lower() == "desc"

    if sort_by == "points":
        all_units.sort(key=lambda u: u.points, reverse=reverse)

    elif sort_by == "category":
        cat_order = {c: i for i, c in enumerate(CATEGORY_ORDER)}

        all_units.sort(
            key=lambda u: (cat_order.get(u.category.lower(), 99), u.name), reverse=reverse
        )

    else:
        all_units.sort(key=lambda u: u.name.lower(), reverse=reverse)

    total = len(all_units)

    pages = max(1, (total + per_page - 1) // per_page)

    start = (page - 1) * per_page

    page_units = all_units[start : start + per_page]

    items = []

    for u in page_units:
        cat_lower = u.category.lower()

        icon_file = ICON_MAP.get(cat_lower, "infantry.svg")

        color = CATEGORY_COLORS.get(cat_lower, "#6b7280")

        role_flags = []

        if u.is_leader or u.can_be_warlord or cat_lower == "character":
            role_flags.append("leader")

        if "transport" in u.tags or cat_lower == "transport":
            role_flags.append("transport")

        if cat_lower == "battleline" or "battleline" in u.tags:
            role_flags.append("battleline")

        if u.is_epic_hero:
            role_flags.append("epic-hero")

        items.append(
            {
                "name": u.name,
                "faction": u.faction,
                "category": u.category,
                "points": u.points,
                "movement": u.movement,
                "toughness": u.toughness,
                "save": u.save,
                "wounds": u.wounds,
                "leadership": u.leadership,
                "oc": u.objective_control,
                "icon_url": f"/static/icons/{icon_file}",
                "color": color,
                "role_flags": role_flags,
            }
        )

    factions = sorted(set(u.faction for u in wiki.units.values()))

    categories = sorted(
        set(u.category for u in wiki.units.values()),
        key=lambda c: CATEGORY_ORDER.index(c.lower()) if c.lower() in CATEGORY_ORDER else 99,
    )

    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": pages,
        "factions": factions,
        "categories": categories,
    }


@router.get("/units/{unit_name}/detail")
async def unit_detail(unit_name: str):
    """Полные данные юнита для модалки."""

    with contextlib.suppress(Exception):
        wiki.load()

    unit = wiki.get_unit(unit_name)

    if not unit:
        raise HTTPException(404, detail="Unit not found")

    from backend.loader.icon_map import CATEGORY_COLORS, ICON_MAP

    # Get all weapons (ranged + melee)

    weapons = []

    for w in getattr(unit, "ranged_weapons", []) + getattr(unit, "melee_weapons", []):
        weapons.append(
            {
                "name": w.name,
                "type": w.type,
                "range": w.range_max if w.type == "ranged" else None,
                "attacks": f"{w.attacks_dice[0]}D{w.attacks_dice[1]}"
                if w.attacks_dice[0] > 0
                else str(w.attacks_dice[2]),
                "skill": w.skill,
                "strength": w.strength,
                "ap": w.ap,
                "damage": f"{w.damage_dice[0]}D{w.damage_dice[1]}"
                if w.damage_dice[0] > 0
                else str(w.damage_dice[2]),
                "keywords": getattr(w, "tags", []),
            }
        )

    # Get wargear options from frontmatter (F4.2 extended system)

    extended_wargear_options = getattr(unit, "extended_wargear_options", [])

    nob_options = getattr(unit, "nob_options", [])

    squad_size = getattr(unit, "squad_size", {"min": 1, "max": 1, "step": 1})
    # If squad_size is still default (1:1), derive from model_count
    if squad_size.get("min") == 1 and squad_size.get("max") == 1:
        min_m, max_m = unit.model_count
        if min_m != 1 or max_m != 1:
            squad_size = {"min": min_m, "max": max_m, "step": 1}

    # Abilities

    abilities = getattr(unit, "abilities", [])

    if isinstance(abilities, list):
        abilities = [{"name": a, "description": ""} if isinstance(a, str) else a for a in abilities]

    return {
        "name": unit.name,
        "faction": unit.faction,
        "category": unit.category,
        "points": unit.points,
        "movement": unit.movement,
        "toughness": unit.toughness,
        "save": unit.save,
        "wounds": unit.wounds,
        "leadership": unit.leadership,
        "oc": unit.objective_control,
        "abilities": abilities,
        "squad_size": squad_size,
        "wargear_options": extended_wargear_options,
        "nob_options": nob_options,
        "weapons": weapons,
        "transport_capacity": getattr(unit, "transport_capacity", None),
        "leader_for": getattr(unit, "leader_for", []),
        "keywords": getattr(unit, "keywords", []),
        "faction_keywords": getattr(unit, "faction_keywords", []),
        "icon_url": f"/static/icons/{ICON_MAP.get(unit.category.lower(), 'infantry.svg')}",
        "color": CATEGORY_COLORS.get(unit.category.lower(), "#6b7280"),
        "icon_tags": [unit.category.lower().replace(" ", "-")]
        + [t for t in _unit_icons(unit) if t != unit.category.lower().replace(" ", "-")],
    }


@router.get("/map/tiles")
async def get_map_tiles(
    map_id: int | None = None,
    scenario: str | None = None,
):
    """

    Вернуть сетку тайлов для отображения на Canvas.

    Response: {

        "width": 16, "height": 16,

        "tiles": [[tile_type, ...], ...],  # 16×16 matrix of TileType values

        "deploy_zones": {

            "player1": [(x1,y1), (x2,y2), ...],

            "player2": [(x3,y3), (x4,y4), ...],

        },

        "units": [

            {"name": "Warboss", "x": 2, "y": 3, "faction": "orks",

             "icon": "/static/icons/character.svg", "color": "#a855f7"},

        ],

    }

    """

    from enum import Enum

    from backend.loader.icon_map import CATEGORY_COLORS, ICON_MAP

    class TileType(Enum):
        OPEN = 0

        LIGHT_COVER = 1

        HEAVY_COVER = 2

        OBSTACLE = 3

        DIFFICULT = 4

        DEPLOY_ZONE = 5

    grid_size = 16

    # Generate a balanced map with central obstacles

    tiles = []

    for y in range(grid_size):
        row = []

        for x in range(grid_size):
            # Default to open ground

            tile_type = TileType.OPEN.value

            # Central obstacle cluster

            if 6 <= x <= 9 and 6 <= y <= 9:
                tile_type = TileType.OBSTACLE.value

            # Light cover on flanks

            elif (x == 3 or x == 12) and 4 <= y <= 11:
                tile_type = TileType.LIGHT_COVER.value

            # Heavy cover in corners

            elif (x <= 2 or x >= 13) and (y <= 2 or y >= 13):
                tile_type = TileType.HEAVY_COVER.value

            # Difficult terrain near obstacles

            elif (
                5 <= x <= 10
                and 5 <= y <= 10
                and tile_type == TileType.OPEN.value
                and (x + y) % 3 == 0
            ):
                tile_type = TileType.DIFFICULT.value

            row.append(tile_type)

        tiles.append(row)

    # Deploy zones

    deploy_zones = {
        "player1": [],  # left side (x: 0-3)
        "player2": [],  # right side (x: 12-15)
    }

    for x in range(4):  # player1: x 0-3
        for y in range(grid_size):
            deploy_zones["player1"].append([x, y])

    for x in range(12, grid_size):  # player2: x 12-15
        for y in range(grid_size):
            deploy_zones["player2"].append([x, y])

    # Mark deploy zone tiles

    for coord in deploy_zones["player1"] + deploy_zones["player2"]:
        x, y = coord

        if tiles[y][x] == TileType.OPEN.value:
            tiles[y][x] = TileType.DEPLOY_ZONE.value

    return {
        "width": grid_size,
        "height": grid_size,
        "tiles": tiles,
        "deploy_zones": deploy_zones,
        "units": [],  # Empty for now, can be populated from scenario
    }


@router.get("/health")
async def health():

    return {"status": "ok", "version": "0.3.0"}


@router.get("/factions")
async def list_factions():
    """Список доступных фракций."""

    try:
        wiki.load()

    except Exception:
        return {"factions": []}

    faction_names = wiki.list_factions()

    # Try to get proper labels from wiki faction pages

    from pathlib import Path

    import frontmatter

    labels = {}

    for f_id in faction_names:
        fp = wiki.wiki_path / "factions" / f"{f_id}.md"

        if not fp.exists():
            # Try case-insensitive match

            for f in (wiki.wiki_path / "factions").iterdir():
                if f.is_file() and f.stem.lower() == f_id.lower():
                    fp = f

                    break

        if fp.exists():
            try:
                post = frontmatter.load(str(fp))

                labels[f_id] = str(post.metadata.get("title", f_id.replace("-", " ").title()))

            except Exception:
                labels[f_id] = f_id.replace("-", " ").title()

        else:
            labels[f_id] = f_id.replace("-", " ").title()

    return {
        "factions": [
            {"id": f, "label": labels.get(f, f.replace("-", " ").title())} for f in faction_names
        ]
    }


# ── Roster CRUD ─────────────────────────────────────────
