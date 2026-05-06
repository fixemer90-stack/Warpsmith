"""Roster API — CRUD, random generation, synergy checks."""

import contextlib
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.auth import User, get_current_user
from backend.billing.plans import UserFeatures
from backend.db.database import db
from backend.loader.registry import registry as wiki
from backend.state.roster import RosterState, validate_roster

router = APIRouter()


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


@router.post("/rosters/generate")
async def generate_roster(data: dict | None = None):
    data = data or {}
    faction = data.get("faction", "")
    pts_limit = data.get("pts_limit", 2000)
    """Сгенерировать случайный валидный ростер для AI-оппонента."""

    import random

    try:
        wiki.load()
    except Exception:
        raise HTTPException(500, detail="Wiki not loaded") from None

    # If no faction specified, pick a random one
    if not faction:
        all_factions = wiki.list_factions()
        if not all_factions:
            raise HTTPException(404, detail="No factions available")
        faction = random.choice(all_factions)

    # Filter units by faction
    candidates = []

    for name, unit in wiki.units.items():
        if unit.points <= 0 or unit.points is None:
            continue
        if unit.faction != faction:
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
            if total + cost <= pts_limit:  # only if it fits
                selected.insert(0, {"unit_name": n, "squad_size": 1})
                total += cost

    return {
        "roster": {
            "name": f"AI {faction.title() if faction else 'Random'} Army",
            "faction": faction,
            "pts_limit": pts_limit,
            "total_pts": total,
            "units": selected,
        }
    }


@router.get("/rosters/{roster_id}")
async def get_roster(roster_id: int, user: User = Depends(get_current_user)):
    """Получить ростер по id."""

    row = db.fetchone("SELECT * FROM rosters WHERE id = ?", (roster_id,))

    if not row:
        raise HTTPException(404, detail="Roster not found")

    if row["user_id"] != user.id and not row["is_public"]:
        raise HTTPException(403, detail="Not authorized")

    data = dict(row)
    if isinstance(data.get("units"), str):
        data["units"] = json.loads(data["units"])
    return data


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
