"""Detachment API — faction detachments with rules, stratagems, enhancements."""

import contextlib

from fastapi import APIRouter, HTTPException

from backend.loader.registry import registry as wiki

router = APIRouter()


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
