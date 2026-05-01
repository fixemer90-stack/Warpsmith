"""JSON API для симуляции."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/units/{faction}")
async def list_units(faction: str):
    """Список юнитов фракции."""
    # TODO: интеграция с WikiRegistry
    return {"faction": faction, "units": []}


@router.post("/simulate")
async def run_simulation(data: dict):
    """Запуск симуляции сценария."""
    # TODO: интеграция с Game Engine
    return {"status": "ok", "result": "simulation placeholder"}


@router.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
