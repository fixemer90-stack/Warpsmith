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


@router.get("/health")
async def health():
    return {"status": "ok", "version": "0.2.1"}


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
