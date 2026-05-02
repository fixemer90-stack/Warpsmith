"""HTML-страницы веб-интерфейса."""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


@router.get("/team-builder", response_class=HTMLResponse)
async def team_builder(request: Request):
    """Сбор армии."""
    return templates.TemplateResponse(
        request, "team_builder.html",
        {"request": request, "title": "Team Builder"},
    )


@router.get("/scenario-setup", response_class=HTMLResponse)
async def scenario_setup(request: Request):
    """Выбор миссии и карты."""
    return templates.TemplateResponse(
        request, "scenario_setup.html",
        {"request": request, "title": "Scenario Setup"},
    )


@router.get("/pmf-chart", response_class=HTMLResponse)
async def pmf_chart(request: Request):
    """PMF chart page for visualizing damage distributions."""
    return templates.TemplateResponse(
        request, "pmf_chart.html",
        {"request": request, "title": "PMF Chart — Warpsmith"},
    )


@router.get("/round-viewer/{scenario_id}", response_class=HTMLResponse)
async def round_viewer(request: Request, scenario_id: int):
    """Просмотр результатов симуляции."""
    return templates.TemplateResponse(
        request, "round_viewer.html",
        {"request": request, "scenario_id": scenario_id},
    )


@router.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    """Страница с планами подписки."""
    return templates.TemplateResponse(
        request, "pricing.html",
        {"request": request, "title": "Pricing — Warpsmith"},
    )


@router.get("/account/billing", response_class=HTMLResponse)
async def billing_page(request: Request):
    """Управление подпиской (Stripe Customer Portal stub)."""
    return templates.TemplateResponse(
        request, "pricing.html",
        {"request": request, "title": "Billing — Warpsmith"},
    )