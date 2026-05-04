"""JSON API для симуляции."""

import contextlib
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.auth import User, get_current_user
from backend.billing.plans import UserFeatures
from backend.db.database import db
from backend.engine.ai.autoplay import AutoPlayConfig, run_auto_game
from backend.engine.combat import MultiAttackResult, simulate_unit_attack, simulate_weapon_attack
from backend.engine.dice import DicePool
from backend.loader.registry import registry as wiki
from backend.state.mission import Mission
from backend.state.roster import RosterState, validate_roster

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
                    "abilities": unit.abilities,  # Add abilities for team builder modal
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
    }


@router.get("/detachments")
async def list_detachments(faction: str | None = None):
    """Вернуть список детачментов. С фильтрацией по faction."""
    try:
        wiki.load()
    except Exception:
        return []

    detachment_names = wiki.list_detachments(faction=faction)
    result = []
    for name in detachment_names:
        det = wiki.get_detachment(name)
        if det:
            result.append(
                {
                    "name": det.name,
                    "faction": det.faction,
                    "description": det.description[:100] + "..."
                    if len(det.description) > 100
                    else det.description,
                    "rule_name": det.detachment_rule.name if det.detachment_rule else None,
                    "rule_description": det.detachment_rule.description[:80] + "..."
                    if det.detachment_rule and len(det.detachment_rule.description) > 80
                    else (det.detachment_rule.description if det.detachment_rule else None),
                    "stratagem_count": len(det.stratagems),
                    "enhancement_count": len(det.enhancements),
                }
            )
    return result


@router.get("/detachments/{detachment_name}")
async def detachment_detail(detachment_name: str):
    """Вернуть полные данные детачмента: правила, стратагемы, энхансменты."""
    with contextlib.suppress(Exception):
        wiki.load()

    det = wiki.get_detachment(detachment_name)
    if not det:
        raise HTTPException(404, detail="Detachment not found")

    return {
        "name": det.name,
        "faction": det.faction,
        "description": det.description,
        "detachment_rule": {
            "name": det.detachment_rule.name if det.detachment_rule else "No Rule",
            "description": det.detachment_rule.description if det.detachment_rule else "",
        }
        if det.detachment_rule
        else None,
        "stratagems": [
            {
                "name": s.name,
                "cost": s.cost,
                "when": s.when,
                "effect": s.effect,
            }
            for s in det.stratagems
        ],
        "enhancements": [
            {
                "name": e.name,
                "points": e.points,
                "effect": e.effect,
            }
            for e in det.enhancements
        ],
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
            elif 5 <= x <= 10 and 5 <= y <= 10 and tile_type == TileType.OPEN.value and (x + y) % 3 == 0:
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


@router.post("/auto-play")
async def auto_play_simulation(
    roster_a_id: int,
    roster_b_id: int,
    mission: str = "only_war",
    deployment: str = "standard",
    max_rounds: int = 5,
    seed: int = 42
):
    """Запуск полной AI vs AI симуляции."""
    try:
        # Load rosters from database
        roster_a_row = db.fetchone("SELECT * FROM rosters WHERE id = ?", (roster_a_id,))
        roster_b_row = db.fetchone("SELECT * FROM rosters WHERE id = ?", (roster_b_id,))

        if not roster_a_row:
            raise HTTPException(status_code=404, detail=f"Roster A not found: {roster_a_id}")
        if not roster_b_row:
            raise HTTPException(status_code=404, detail=f"Roster B not found: {roster_b_id}")

        # Convert database rows to RosterState objects
        import json

        from backend.model.unit import Unit, Weapon
        from backend.state.roster import RosterState

        def units_from_db(units_json):
            units_dict = {}
            units_data = json.loads(units_json)
            for u_data in units_data:
                unit = wiki.get_unit(u_data["unit_name"])
                if unit:
                    # Create a copy of the unit with the specified squad size
                    unit_copy = Unit(
                        name=unit.name,
                        faction=unit.faction,
                        toughness=unit.toughness,
                        save=unit.save,
                        wounds=unit.wounds,
                        squad_size=u_data["squad_size"],
                        weapons=unit.weapons,
                        points=unit.points
                    )
                    units_dict[unit.name] = unit_copy
            return units_dict

        roster_a = RosterState(
            name=roster_a_row["name"],
            faction=roster_a_row["faction"],
            total_pts=roster_a_row["pts_limit"],  # This should be total_pts, but we'll use pts_limit for now
            units=units_from_db(roster_a_row["units"])
        )

        roster_b = RosterState(
            name=roster_b_row["name"],
            faction=roster_b_row["faction"],
            total_pts=roster_b_row["pts_limit"],
            units=units_from_db(roster_b_row["units"])
        )

        # Get mission object
        mission_obj = Mission(
            name=mission,
            description=f"{mission} mission",
            objectives=[]
        )

        # Run auto-play simulation
        config = AutoPlayConfig(
            max_rounds=max_rounds,
            deployment_type=deployment,
            seed=seed
        )

        result = run_auto_game(roster_a, roster_b, mission_obj, config)

        if result.error:
            raise HTTPException(status_code=400, detail=result.error)

        return {
            "success": True,
            "result": result.to_dict(),
            "replay_log": result.round_logs  # This would be enhanced with actual replay data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


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


class RosterUnit(BaseModel):
    unit_name: str
    squad_size: int = 1


class RosterCreate(BaseModel):
    name: str
    faction: str
    pts_limit: int = 2000
    detachment: str | None = None
    units: list[RosterUnit]
    is_public: bool = False


class RosterUpdate(BaseModel):
    name: str | None = None
    units: list[RosterUnit] | None = None
    is_public: bool | None = None


class SynergyCheck(BaseModel):
    type: str  # "leader" | "transport" | "synergy"
    severity: str  # "info" | "warning" | "error"
    source_unit: str
    target_unit: str | None = None
    message: str
    icon: str = "💡"
    action_url: str | None = None


@router.post("/rosters")
async def create_roster(data: RosterCreate, user: User = Depends(get_current_user)):
    """Создать новый ростер."""

    # Check Free tier limit
    features = UserFeatures.for_user(user)
    current = db.fetchone("SELECT COUNT(*) as cnt FROM rosters WHERE user_id = ?", (user.id,))[
        "cnt"
    ]
    if current >= features["max_rosters"]:
        raise HTTPException(403, detail="Max rosters limit reached. Upgrade to Premium.")

    # Load wiki and validate
    with contextlib.suppress(Exception):
        wiki.load()
    units_list = [(u.unit_name, u.squad_size) for u in data.units]
    validation = validate_roster(units_list, wiki.units, pts_limit=data.pts_limit)
    if not validation.is_valid:
        raise HTTPException(
            400,
            detail={
                "error": "roster_invalid",
                "validation_errors": [e.__dict__ for e in validation.errors],
            },
        )

    cur = db.execute(
        """INSERT INTO rosters (user_id, name, faction, pts_limit, detachment, units, is_public)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            user.id,
            data.name,
            data.faction,
            data.pts_limit,
            data.detachment,
            json.dumps([u.model_dump() for u in data.units]),
            int(data.is_public),
        ),
    )
    db.commit()
    return {"id": cur.lastrowid, **data.model_dump()}


@router.get("/rosters")
async def list_rosters(user: User = Depends(get_current_user), public_only: bool = False):
    """Список ростереров текущего пользователя."""

    if public_only:
        rows = db.fetchall("SELECT * FROM rosters WHERE is_public = 1 ORDER BY updated_at DESC")
    else:
        rows = db.fetchall(
            "SELECT * FROM rosters WHERE user_id = ? ORDER BY updated_at DESC",
            (user.id,),
        )
    return {"rosters": [dict(r) for r in rows]}


@router.get("/rosters/{roster_id}")
async def get_roster(roster_id: int, user: User = Depends(get_current_user)):
    """Получить ростер по id."""

    row = db.fetchone("SELECT * FROM rosters WHERE id = ?", (roster_id,))
    if not row:
        raise HTTPException(404, detail="Roster not found")
    if row["user_id"] != user.id and not row["is_public"]:
        raise HTTPException(403, detail="Not authorized")

    return dict(row)


@router.get("/rosters/generate")
async def generate_roster(faction: str = "", pts_limit: int = 2000):
    """Сгенерировать случайный валидный ростер для AI-оппонента."""
    import random

    try:
        wiki.load()
    except Exception:
        raise HTTPException(500, detail="Wiki not loaded") from None

    # Filter units by faction (or all factions)
    candidates = []
    for name, unit in wiki.units.items():
        if unit.points <= 0 or unit.points is None:
            continue
        if faction and unit.faction != faction:
            continue
        if unit.is_epic_hero:
            candidates.append((name, unit, 1))
        else:
            min_m, _max_m = unit.model_count
            candidates.append((name, unit, min_m))

    if not candidates:
        raise HTTPException(404, detail=f"No valid units for faction '{faction}'")

    random.shuffle(candidates)

    selected = []
    total = 0
    has_warlord = False
    epic_heroes = set()
    counts = {}

    for name, unit, squad_size in candidates:
        if total >= pts_limit:
            break

        # Respect 3x cap
        if counts.get(name, 0) >= 3:
            continue

        # Epic Hero unique
        if unit.is_epic_hero:
            if name in epic_heroes:
                continue
            epic_heroes.add(name)

        cost = unit.points * squad_size
        if total + cost > pts_limit:
            continue

        selected.append({"unit_name": name, "squad_size": squad_size})
        total += cost
        counts[name] = counts.get(name, 0) + 1
        if unit.can_be_warlord:
            has_warlord = True

    if not has_warlord:
        # Force-add a cheap warlord-capable unit
        warlords = [
            (n, u)
            for n, u in wiki.units.items()
            if u.can_be_warlord and u.points > 0 and (not faction or u.faction == faction)
        ]
        if warlords:
            n, u = random.choice(warlords)
            cost = u.points
            if total + cost <= pts_limit or True:  # force even if over
                selected.insert(0, {"unit_name": n, "squad_size": 1})
                total += cost

    return {
        "roster": {
            "name": f"AI {faction.title() if faction else 'Random'} Army",
            "faction": faction or "mixed",
            "pts_limit": pts_limit,
            "total_pts": total,
            "units": selected,
        }
    }


@router.delete("/rosters/{roster_id}")
async def delete_roster(roster_id: int, user: User = Depends(get_current_user)):
    """Удалить ростер."""

    row = db.fetchone("SELECT user_id FROM rosters WHERE id = ?", (roster_id,))
    if not row:
        raise HTTPException(404, detail="Roster not found")
    if row["user_id"] != user.id:
        raise HTTPException(403, detail="Not authorized")

    db.execute("DELETE FROM rosters WHERE id = ?", (roster_id,))
    db.commit()
    return {"status": "deleted", "id": roster_id}


@router.post("/rosters/synergies")
async def check_roster_synergies(data: dict):
    """
    Проверить ростер на синергии.
    request: { "faction": str, "units": list[{"name": str, "squad_size": int, ...}] }
    response: { "checks": list[SynergyCheck], "score": int }
    """
    try:
        wiki.load()
    except Exception:
        return {"checks": [], "score": 0}

    checks: list[dict] = []
    units_data = data.get("units", [])

    # Get unit objects
    unit_objs = []
    for u_data in units_data:
        unit = wiki.get_unit(u_data["name"])
        if unit:
            unit_objs.append((unit, u_data))

    # 1. Leader → Bodyguard compatibility
    leaders = [
        (u, ud)
        for u, ud in unit_objs
        if getattr(u, "is_leader", False) or getattr(u, "can_be_warlord", False)
    ]
    non_leaders = [
        (u, ud)
        for u, ud in unit_objs
        if not (getattr(u, "is_leader", False) or getattr(u, "can_be_warlord", False))
    ]

    for leader, _leader_data in leaders:
        compatible = []
        incompatible = []

        # Check leader_for compatibility
        leader_for = getattr(leader, "leader_for", [])
        if leader_for:
            for unit, _unit_data in non_leaders:
                if any(
                    lf.lower() in [kw.lower() for kw in getattr(unit, "keywords", [])]
                    or lf.lower() in unit.category.lower()
                    for lf in leader_for
                ):
                    compatible.append(unit.name)
                else:
                    incompatible.append(unit.name)
        else:
            # Default: assume leaders can lead infantry/battleline
            for unit, _unit_data in non_leaders:
                if unit.category.lower() in ["infantry", "battleline"]:
                    compatible.append(unit.name)
                else:
                    incompatible.append(unit.name)

        if compatible:
            checks.append(
                {
                    "type": "leader",
                    "severity": "info",
                    "source_unit": leader.name,
                    "message": f"{leader.name} can lead: {', '.join(compatible)}",
                    "icon": "✅",
                }
            )
        elif incompatible:
            checks.append(
                {
                    "type": "leader",
                    "severity": "warning",
                    "source_unit": leader.name,
                    "message": f"{leader.name} has no compatible units to lead",
                    "icon": "⚠️",
                }
            )

    # 2. Transport capacity
    transports = [(u, ud) for u, ud in unit_objs if getattr(u, "transport_capacity", None)]
    for transport, _transport_data in transports:
        capacity = transport.transport_capacity
        # Find units that can embark (infantry, battleline, etc.)
        embarked_count = 0
        embarked_units = []
        for unit, unit_data in non_leaders:
            # Skip if it's another transport or epic hero
            if getattr(unit, "transport_capacity", None) or getattr(unit, "is_epic_hero", False):
                continue
            # Check if unit can be transported (infantry/battleline typically)
            if unit.category.lower() in ["infantry", "battleline"]:
                embarked_count += unit_data.get("squad_size", 1)
                embarked_units.append(unit.name)

        if embarked_count > capacity:
            checks.append(
                {
                    "type": "transport",
                    "severity": "error",
                    "source_unit": transport.name,
                    "message": f"{transport.name} can carry {capacity} models, but roster has {embarked_count} eligible models",
                    "icon": "🚫",
                }
            )
        elif embarked_count == 0 and capacity > 0:
            checks.append(
                {
                    "type": "transport",
                    "severity": "info",
                    "source_unit": transport.name,
                    "message": f"{transport.name} is empty — add infantry to transport",
                    "icon": "🚌",
                }
            )
        elif embarked_count > 0:
            checks.append(
                {
                    "type": "transport",
                    "severity": "info",
                    "source_unit": transport.name,
                    "message": f"{transport.name} carrying {embarked_count}/{capacity} models: {', '.join(embarked_units)}",
                    "icon": "🚌",
                }
            )

    # 3. Wiki synergy hints (from YAML frontmatter synergies field)
    for unit, _unit_data in unit_objs:
        synergies = getattr(unit, "synergies", [])
        for syn in synergies:
            if isinstance(syn, dict):
                with_unit = syn.get("with", "")
                if with_unit:
                    # Check if target unit is in roster
                    matched = [ud for u, ud in unit_objs if ud["name"].lower() == with_unit.lower()]
                    if matched:
                        checks.append(
                            {
                                "type": "synergy",
                                "severity": syn.get("type", "info"),
                                "source_unit": unit.name,
                                "target_unit": with_unit,
                                "message": syn.get("text", f"Synergy with {with_unit}"),
                                "icon": "💡",
                            }
                        )

    # Calculate score: errors = 3 points, warnings = 1 point, info = 0
    score = sum(
        (3 if c["severity"] == "error" else 1 if c["severity"] == "warning" else 0) for c in checks
    )

    return {"checks": checks, "score": score}
