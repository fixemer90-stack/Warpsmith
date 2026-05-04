"""HTML-страницы веб-интерфейса."""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from backend.loader.icon_map import CATEGORY_COLORS, get_card_style, get_icon_html

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))
# Jinja2 globals для карточек юнитов
templates.env.globals["unit_icon"] = get_icon_html
templates.env.globals["card_style"] = get_card_style
templates.env.globals["CATEGORY_COLORS"] = CATEGORY_COLORS


@router.get("/faction-browser", response_class=HTMLResponse)
async def faction_browser(request: Request):
    return templates.TemplateResponse(
        request,
        "faction_browser.html",
        {"request": request, "title": "Faction Browser — Warpsmith"},
    )


@router.get("/team-builder", response_class=HTMLResponse)
async def team_builder(request: Request):
    """Сбор армии."""
    import json
    from pathlib import Path

    from backend.loader.icon_map import get_icon_svg_map

    # Load factions for the selector
    from backend.loader.registry import registry as wiki

    try:
        wiki.load()
        raw_factions = wiki.list_factions()
    except Exception:
        raw_factions = []
    import frontmatter

    factions = []
    for f_id in raw_factions:
        fp = wiki.wiki_path / "factions" / f"{f_id}.md"
        if not fp.exists():
            for f in (wiki.wiki_path / "factions").iterdir():
                if f.is_file() and f.stem.lower() == f_id.lower():
                    fp = f
                    break
        label = f_id.replace("-", " ").title()
        if fp.exists():
            try:
                post = frontmatter.load(str(fp))
                label = str(post.metadata.get("title", label))
            except Exception:  # noqa: S110
                pass
        factions.append({"id": f_id, "label": label})

    return templates.TemplateResponse(
        request,
        "team_builder.html",
        {
            "request": request,
            "title": "Team Builder",
            "factions": factions,
            "_icon_svg_map_json": json.dumps(get_icon_svg_map()),
        },
    )


@router.get("/scenario-setup", response_class=HTMLResponse)
async def scenario_setup(request: Request):
    """Выбор миссии, карты и ростера."""
    factions = []
    rosters = []

    try:
        from backend.loader.registry import registry as wiki

        wiki.load()
        for f_id in wiki.list_factions():
            fp = wiki.wiki_path / "factions" / f"{f_id}.md"
            label = f_id.replace("-", " ").title()
            if fp.exists():
                try:
                    import frontmatter

                    post = frontmatter.load(str(fp))
                    label = str(post.metadata.get("title", label))
                except Exception:  # noqa: S110
                    pass
            factions.append({"id": f_id, "label": label})
    except Exception:  # noqa: S110
        pass

    # Get user's rosters if authenticated
    from backend.auth import get_current_user_optional
    from backend.db.database import db

    try:
        user = await get_current_user_optional(request)
        if user:
            rows = db.fetchall(
                "SELECT id, name, faction, pts_limit, detachment, units FROM rosters WHERE user_id = ? ORDER BY id DESC",
                (user.id,),
            )
            for row in rows:
                rosters.append(
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "faction": row["faction"],
                        "pts_limit": row["pts_limit"],
                    }
                )
    except Exception:  # noqa: S110
        pass

    import json

    return templates.TemplateResponse(
        request,
        "scenario_setup.html",
        {
            "request": request,
            "title": "Scenario Setup",
            "factions": factions,
            "rosters": rosters,
            "rosters_json": json.dumps(rosters),
        },
    )


@router.get("/pmf-chart", response_class=HTMLResponse)
async def pmf_chart(request: Request):
    """PMF chart page for visualizing damage distributions."""
    return templates.TemplateResponse(
        request,
        "pmf_chart.html",
        {"request": request, "title": "PMF Chart — Warpsmith"},
    )


@router.get("/round-viewer/{scenario_id}", response_class=HTMLResponse)
async def round_viewer(request: Request, scenario_id: int):
    """Просмотр результатов симуляции."""
    return templates.TemplateResponse(
        request,
        "round_viewer.html",
        {"request": request, "scenario_id": scenario_id},
    )


@router.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    """Страница с планами подписки."""
    return templates.TemplateResponse(
        request,
        "pricing.html",
        {"request": request, "title": "Pricing — Warpsmith"},
    )


@router.get("/account/billing", response_class=HTMLResponse)
async def billing_page(request: Request):
    """Управление подпиской (Stripe Customer Portal stub)."""
    return templates.TemplateResponse(
        request,
        "pricing.html",
        {"request": request, "title": "Billing — Warpsmith"},
    )
