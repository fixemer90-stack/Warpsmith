"""Roster API — CRUD, random generation, synergy checks."""

import contextlib
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.auth import User, get_current_user
from backend.billing.plans import UserFeatures
from backend.db.database import db
from backend.loader.registry import registry as wiki
from backend.state.roster import (
    RosterState,
    calculate_squad_pts,
    is_unit_eligible_warlord,
    validate_roster,
)

router = APIRouter()


class RosterUnit(BaseModel):
    unit_name: str
    squad_size: int = 1
    pts: int | float | None = None
    loadout: str | None = None
    nob_option: str | None = None
    weapons: list[str] | None = None
    is_warlord: bool = False


class RosterCreate(BaseModel):
    name: str
    faction: str
    pts_limit: int = 2000
    detachment: str | None = None
    units: list[RosterUnit]
    is_public: bool = False


def _warlord_validation_errors(units: list[RosterUnit]) -> list[dict]:
    """Require an explicit Warlord when a roster has multiple Character choices."""

    candidates: list[RosterUnit] = []
    for roster_unit in units:
        unit = wiki.get_unit(roster_unit.unit_name)
        if not unit:
            continue
        if is_unit_eligible_warlord(unit):
            candidates.append(roster_unit)

    if len(candidates) <= 1:
        return []

    selected = [u for u in candidates if u.is_warlord]
    if len(selected) == 1:
        return []
    return [
        {
            "code": "warlord_required",
            "message": "Roster has multiple Characters. Select exactly one Warlord.",
            "detail": {"candidates": [u.unit_name for u in candidates]},
        }
    ]


def _resolve_loadout_pts(unit_name: str, loadout_name: str | None) -> int:
    """Resolve a loadout option name to its point cost from the wiki."""
    if not loadout_name:
        return 0
    unit = wiki.get_unit(unit_name)
    if not unit:
        return 0
    # Search extended_wargear_options for matching name
    for option in getattr(unit, "extended_wargear_options", []) or []:
        if isinstance(option, dict) and option.get("name") == loadout_name:
            return int(option.get("points", 0))
    return 0


def _resolve_nob_pts(unit_name: str, nob_name: str | None) -> int:
    """Resolve a Nob option name to its point cost from the wiki."""
    if not nob_name:
        return 0
    unit = wiki.get_unit(unit_name)
    if not unit:
        return 0
    for option in getattr(unit, "nob_options", []) or []:
        if isinstance(option, dict) and option.get("name") == nob_name:
            return int(option.get("points", 0))
    return 0


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
    loadout_pts = [_resolve_loadout_pts(u.unit_name, u.loadout) for u in data.units]
    nob_pts = [_resolve_nob_pts(u.unit_name, u.nob_option) for u in data.units]
    is_warlord_list = [bool(u.is_warlord) for u in data.units]
    validation = validate_roster(
        units_list,
        wiki.units,
        pts_limit=data.pts_limit,
        loadout_pts=loadout_pts,
        nob_pts=nob_pts,
        is_warlord=is_warlord_list,
    )
    warlord_errors = _warlord_validation_errors(data.units)

    if not validation.is_valid or warlord_errors:
        raise HTTPException(
            400,
            detail={
                "error": "roster_invalid",
                "validation_errors": [e.__dict__ for e in validation.errors] + warlord_errors,
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

    return {
        "id": cur.lastrowid,
        **data.model_dump(),
        "total_pts": validation.total_pts,
        "squad_pts": validation.squad_pts,
    }


def _parse_roster_row(row: dict) -> dict:
    """Parse units from JSON string to list for API response."""
    data = dict(row)
    if isinstance(data.get("units"), str):
        data["units"] = json.loads(data["units"])
    return data


def _recalc_roster_total_pts(units_data: list[dict]) -> dict:
    """Recalculate total_pts and squad_pts from stored roster units.

    Uses the canonical calculate_squad_pts() formula with wiki lookups
    for unit base points and squad_size min.  Lightweight — does not
    run full validate_roster() (no warlord/copy/duplicate checks).

    Returns dict with ``total_pts`` (int) and ``squad_pts`` (list[dict]).
    """
    total = 0
    sq_pts: list[dict] = []
    for u in units_data:
        unit_name = u.get("unit_name", "")
        squad_size = u.get("squad_size", 1)
        unit = wiki.get_unit(unit_name)
        if unit is None:
            sq_pts.append({"unit_name": unit_name, "squad_pts": 0})
            continue
        sq = getattr(unit, "squad_size", None) or {"min": 1, "max": 1, "step": 1}
        min_sq = sq["min"]
        loadout_name = u.get("loadout")
        nob_name = u.get("nob_option")
        loadout_p = _resolve_loadout_pts(unit_name, loadout_name)
        nob_p = _resolve_nob_pts(unit_name, nob_name)
        pts = calculate_squad_pts(
            points=unit.points,
            min_squad=min_sq,
            squad_size=squad_size,
            loadout_pts=loadout_p,
            nob_pts=nob_p,
        )
        total += pts
        sq_pts.append(
            {
                "unit_name": unit_name,
                "squad_size": squad_size,
                "base_pts": unit.points,
                "min_squad": min_sq,
                "squad_pts": pts,
            }
        )
    return {"total_pts": total, "squad_pts": sq_pts}


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

    return {"rosters": [_parse_roster_row(r) for r in rows]}


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
            sq = getattr(unit, "squad_size", None) or {"min": 1, "max": 1, "step": 1}
            candidates.append((name, unit, sq["min"]))

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

        sq = getattr(unit, "squad_size", None) or {"min": 1, "max": 1, "step": 1}
        cost = calculate_squad_pts(
            points=unit.points,
            min_squad=sq["min"],
            squad_size=squad_size,
        )

        if total + cost > pts_limit:
            continue

        selected.append(
            {
                "unit_name": name,
                "squad_size": squad_size,
                "is_warlord": False,
                "squad_pts": cost,
            }
        )
        total += cost
        counts[name] = counts.get(name, 0) + 1

        if is_unit_eligible_warlord(unit):
            has_warlord = True

    if not has_warlord:
        # Force-add the cheapest Warlord-capable unit. If the random roster is full,
        # remove last non-warlord picks until the Warlord fits; generated rosters must
        # be directly saveable and runnable.
        warlords = [
            (n, u)
            for n, u in wiki.units.items()
            if is_unit_eligible_warlord(u)
            and u.points > 0
            and (not faction or u.faction == faction)
        ]
        if warlords:
            n, u = min(warlords, key=lambda item: item[1].points)
            cost = calculate_squad_pts(points=u.points, min_squad=1, squad_size=1)
            while selected and total + cost > pts_limit:
                removed = selected.pop()
                removed_unit = wiki.get_unit(removed["unit_name"])
                if removed_unit:
                    sq = getattr(removed_unit, "squad_size", None) or {
                        "min": 1,
                        "max": 1,
                        "step": 1,
                    }
                    total -= calculate_squad_pts(
                        points=removed_unit.points,
                        min_squad=sq["min"],
                        squad_size=removed["squad_size"],
                    )
            if total + cost <= pts_limit:
                selected.insert(
                    0,
                    {
                        "unit_name": n,
                        "squad_size": 1,
                        "is_warlord": True,
                        "squad_pts": cost,
                    },
                )
                total += cost

    if selected and not any(u.get("is_warlord") for u in selected):
        for item in selected:
            unit = wiki.get_unit(item["unit_name"])
            if unit and is_unit_eligible_warlord(unit):
                item["is_warlord"] = True
                break

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
    with contextlib.suppress(Exception):
        wiki.load()
    totals = _recalc_roster_total_pts(data["units"])
    data.update(totals)
    return data


@router.put("/rosters/{roster_id}")
async def update_roster(roster_id: int, data: RosterCreate, user: User = Depends(get_current_user)):
    """Обновить существующий ростер."""
    # Проверить принадлежность
    row = db.fetchone("SELECT id, user_id FROM rosters WHERE id = ?", (roster_id,))
    if not row:
        raise HTTPException(404, "Roster not found")
    if row["user_id"] != user.id:
        raise HTTPException(403, "Not your roster")
    # Валидация как в create_roster
    with contextlib.suppress(Exception):
        wiki.load()
    units_list = [(u.unit_name, u.squad_size) for u in data.units]
    loadout_pts = [_resolve_loadout_pts(u.unit_name, u.loadout) for u in data.units]
    nob_pts = [_resolve_nob_pts(u.unit_name, u.nob_option) for u in data.units]
    is_warlord_list = [bool(u.is_warlord) for u in data.units]
    validation = validate_roster(
        units_list,
        wiki.units,
        pts_limit=data.pts_limit,
        loadout_pts=loadout_pts,
        nob_pts=nob_pts,
        is_warlord=is_warlord_list,
    )
    warlord_errors = _warlord_validation_errors(data.units)

    if not validation.is_valid or warlord_errors:
        raise HTTPException(
            400,
            detail={
                "error": "roster_invalid",
                "validation_errors": [e.__dict__ for e in validation.errors] + warlord_errors,
            },
        )

    db.execute(
        """UPDATE rosters SET name=?, faction=?, pts_limit=?, detachment=?,
           units=?, updated_at=datetime('now') WHERE id=?""",
        (
            data.name,
            data.faction,
            data.pts_limit,
            data.detachment or "",
            json.dumps([u.model_dump() for u in data.units]),
            roster_id,
        ),
    )
    db.commit()

    # Return updated roster
    result = db.fetchone("SELECT * FROM rosters WHERE id = ?", (roster_id,))
    row_data = _parse_roster_row(result)
    row_data["total_pts"] = validation.total_pts
    row_data["squad_pts"] = validation.squad_pts
    return row_data


@router.post("/rosters/{roster_id}/duplicate")
async def duplicate_roster(roster_id: int, user: User = Depends(get_current_user)):
    """Копировать ростер."""

    row = db.fetchone("SELECT * FROM rosters WHERE id = ?", (roster_id,))
    if not row or (row["user_id"] != user.id and not row["is_public"]):
        raise HTTPException(404, "Roster not found")

    new_name = row["name"] + " (copy)"
    result = db.execute(
        """INSERT INTO rosters (user_id, name, faction, pts_limit, detachment, units, is_public)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user.id, new_name, row["faction"], row["pts_limit"], row["detachment"], row["units"], 0),
    )
    db.commit()
    new_id = result.lastrowid

    duplicated = db.fetchone("SELECT * FROM rosters WHERE id = ?", (new_id,))
    row_data = _parse_roster_row(duplicated)
    with contextlib.suppress(Exception):
        wiki.load()
    totals = _recalc_roster_total_pts(row_data["units"])
    row_data.update(totals)
    return row_data


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
