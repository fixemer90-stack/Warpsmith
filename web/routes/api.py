"""JSON API для симуляции."""

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from backend.loader.registry import registry as wiki
from backend.engine.combat import simulate_weapon_attack, simulate_unit_attack, MultiAttackResult
from backend.engine.dice import DicePool
from backend.auth import get_current_user, User
from backend.billing.plans import UserFeatures
from backend.db.database import db
from backend.state.roster import validate_roster


router = APIRouter()


class SimulationRequest(BaseModel):
    attacker_faction: str = Field(..., description="Faction of the attacking unit")
    attacker_unit: str = Field(..., description="Name of the attacking unit")
    defender_faction: str = Field(..., description="Faction of the defending unit")
    defender_unit: str = Field(..., description="Name of the defending unit")
    weapon_name: str = Field(..., description="Name of the weapon to use")
    distance: Optional[int] = Field(None, description="Distance in inches (for rapid fire, etc.)")
    squad_size: int = Field(1, description="Size of the target squad (for blast weapons)")
    n_iterations: int = Field(10000, description="Number of Monte Carlo iterations")


def _unit_icons(unit) -> list[str]:
    """All SVG icons for a unit based on its YAML tags, in priority order."""
    tags = {t.lower().replace(" ", "-") for t in unit.tags}
    priority = ["epic-hero", "psyker", "titanic", "monster", "dreadnought",
                "walker", "transport", "vehicle", "fly", "artillery",
                "battleline", "character", "elite", "infantry", "medic", "speed-freek"]
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
            result.append({
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
            })

    return {"faction": faction, "units": result}


@router.post("/simulate")
async def run_simulation(request: SimulationRequest):
    """Запуск симуляции сценария."""
    # Fetch units and weapon from the wiki registry
    try:
        wiki.load()
    except Exception:
        pass

    attacker_unit = wiki.get_unit(request.attacker_unit)
    defender_unit = wiki.get_unit(request.defender_unit)

    if not attacker_unit:
        raise HTTPException(status_code=404, detail=f"Attacker unit not found: {request.attacker_faction}/{request.attacker_unit}")
    if not defender_unit:
        raise HTTPException(status_code=404, detail=f"Defender unit not found: {request.defender_faction}/{request.defender_unit}")

    # Find weapon in attacker's weapon lists
    weapon = None
    for w in attacker_unit.ranged_weapons + attacker_unit.melee_weapons:
        if w.name.lower() == request.weapon_name.lower():
            weapon = w
            break
    if not weapon:
        raise HTTPException(status_code=404, detail=f"Weapon not found: {request.weapon_name} (check name or weapon list)")

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
    try:
        wiki.load()
    except Exception:
        pass

    attacker_unit = wiki.get_unit(request.attacker_unit)
    defender_unit = wiki.get_unit(request.defender_unit)

    if not attacker_unit:
        raise HTTPException(status_code=404, detail=f"Attacker unit not found: {request.attacker_faction}/{request.attacker_unit}")
    if not defender_unit:
        raise HTTPException(status_code=404, detail=f"Defender unit not found: {request.defender_faction}/{request.defender_unit}")

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
    faction: Optional[str] = None,
    category: Optional[str] = None,
    pts_min: Optional[int] = None,
    pts_max: Optional[int] = None,
    search: Optional[str] = None,
    role: Optional[str] = None,
    sort_by: str = "name",
    sort_dir: str = "asc",
    page: int = 1,
    per_page: int = 50,
):
    from backend.loader.icon_map import ICON_MAP, CATEGORY_COLORS, CATEGORY_ORDER

    try:
        wiki.load()
    except Exception:
        return {"items": [], "total": 0, "page": page, "pages": 0,
                "factions": [], "categories": []}

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
            all_units = [u for u in all_units if u.is_leader or u.can_be_warlord or u.category.lower() == "character"]
        elif role == "transport":
            all_units = [u for u in all_units if "transport" in u.tags or u.category.lower() == "transport"]
        elif role == "battleline":
            all_units = [u for u in all_units if u.category.lower() == "battleline" or "battleline" in u.tags]

    reverse = sort_dir.lower() == "desc"
    if sort_by == "points":
        all_units.sort(key=lambda u: u.points, reverse=reverse)
    elif sort_by == "category":
        cat_order = {c: i for i, c in enumerate(CATEGORY_ORDER)}
        all_units.sort(key=lambda u: (cat_order.get(u.category.lower(), 99), u.name), reverse=reverse)
    else:
        all_units.sort(key=lambda u: u.name.lower(), reverse=reverse)

    total = len(all_units)
    pages = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page
    page_units = all_units[start:start + per_page]

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

        items.append({
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
        })

    factions = sorted(set(u.faction for u in wiki.units.values()))
    categories = sorted(set(u.category for u in wiki.units.values()), key=lambda c: CATEGORY_ORDER.index(c.lower()) if c.lower() in CATEGORY_ORDER else 99)

    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": pages,
        "factions": factions,
        "categories": categories,
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
            {"id": f, "label": labels.get(f, f.replace("-", " ").title())}
            for f in faction_names
        ]
    }


def _faction_detachment_dir(wiki_path, faction_id: str):
    """Map faction ID (e.g. 'adeptus-mechanicus') to its detachments directory name ('mechanicus')."""
    from pathlib import Path
    import frontmatter

    units_dir = wiki_path / "units"
    if not units_dir.exists():
        return None

    # Scan units subdirectories to find which one has the matching faction YAML
    for subdir in sorted(units_dir.iterdir()):
        if not subdir.is_dir():
            continue
        # Check if the directory name itself matches (common case: orks→orks)
        if subdir.name == faction_id:
            det_dir = wiki_path / "detachments" / subdir.name
            if det_dir.exists():
                return det_dir
        # Check first .md file for faction: field
        for f in subdir.glob("*.md"):
            try:
                post = frontmatter.load(str(f))
                if post.metadata.get("faction") == faction_id:
                    det_dir = wiki_path / "detachments" / subdir.name
                    return det_dir if det_dir.exists() else None
            except Exception:
                continue
            break  # only need first file
    return None


@router.get("/detachments")
async def list_detachments(faction: str = ""):
    """Список детачментов (всех или по фракции)."""
    try:
        wiki.load()
    except Exception:
        return {"detachments": []}

    from pathlib import Path
    wiki_path = wiki.wiki_path
    det_dir = wiki_path / "detachments" / faction
    if not det_dir.exists():
        # Try resolving faction ID → directory name (e.g. adeptus-mechanicus → mechanicus)
        det_dir = _faction_detachment_dir(wiki_path, faction)
    if not det_dir or not det_dir.exists():
        return {"detachments": []}

    detachments = sorted(f.stem for f in det_dir.glob("*.md"))
    return {"detachments": detachments}


# ── Roster CRUD ─────────────────────────────────────────


class RosterUnit(BaseModel):
    unit_name: str
    squad_size: int = 1


class RosterCreate(BaseModel):
    name: str
    faction: str
    pts_limit: int = 2000
    detachment: Optional[str] = None
    units: list[RosterUnit]
    is_public: bool = False


class RosterUpdate(BaseModel):
    name: Optional[str] = None
    units: Optional[list[RosterUnit]] = None
    is_public: Optional[bool] = None


@router.post("/rosters")
async def create_roster(data: RosterCreate, user: User = Depends(get_current_user)):
    """Создать новый ростер."""

    # Check Free tier limit
    features = UserFeatures.for_user(user)
    current = db.fetchone(
        "SELECT COUNT(*) as cnt FROM rosters WHERE user_id = ?", (user.id,)
    )["cnt"]
    if current >= features["max_rosters"]:
        raise HTTPException(403, detail="Max rosters limit reached. Upgrade to Premium.")

    # Load wiki and validate
    try:
        wiki.load()
    except Exception:
        pass
    units_list = [(u.unit_name, u.squad_size) for u in data.units]
    validation = validate_roster(units_list, wiki.units, pts_limit=data.pts_limit)
    if not validation.is_valid:
        raise HTTPException(400, detail={
            "error": "roster_invalid",
            "validation_errors": [e.__dict__ for e in validation.errors],
        })

    cur = db.execute(
        """INSERT INTO rosters (user_id, name, faction, pts_limit, detachment, units, is_public)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user.id, data.name, data.faction, data.pts_limit,
         data.detachment, json.dumps([u.model_dump() for u in data.units]),
         int(data.is_public)),
    )
    db.commit()
    return {"id": cur.lastrowid, **data.model_dump()}


@router.get("/rosters")
async def list_rosters(user: User = Depends(get_current_user), public_only: bool = False):
    """Список ростереров текущего пользователя."""

    if public_only:
        rows = db.fetchall(
            "SELECT * FROM rosters WHERE is_public = 1 ORDER BY updated_at DESC"
        )
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


@router.post("/rosters/generate")
async def generate_roster(faction: str = "", pts_limit: int = 2000):
    """Сгенерировать случайный валидный ростер для AI-оппонента."""
    import random

    try:
        wiki.load()
    except Exception:
        raise HTTPException(500, detail="Wiki not loaded")

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
            min_m, max_m = unit.model_count
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
        warlords = [(n, u) for n, u in wiki.units.items()
                    if u.can_be_warlord and u.points > 0
                    and (not faction or u.faction == faction)]
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
