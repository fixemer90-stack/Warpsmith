"""JSON API для симуляции."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from backend.loader.registry import WikiRegistry
from backend.engine.combat import simulate_weapon_attack, simulate_unit_attack, MultiAttackResult
from backend.engine.dice import DicePool


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


@router.get("/units/{faction}")
async def list_units(faction: str):
    """Список юнитов фракции."""
    # TODO: интеграция с WikiRegistry
    return {"faction": faction, "units": []}


@router.post("/simulate")
async def run_simulation(request: SimulationRequest):
    """Запуск симуляции сценария."""
    # Fetch units and weapon from the wiki registry
    attacker_unit = WikiRegistry.get_unit(request.attacker_faction, request.attacker_unit)
    defender_unit = WikiRegistry.get_unit(request.defender_faction, request.defender_unit)
    weapon = WikiRegistry.get_weapon(request.attacker_faction, request.weapon_name)

    if not attacker_unit:
        raise HTTPException(status_code=404, detail=f"Attacker unit not found: {request.attacker_faction}/{request.attacker_unit}")
    if not defender_unit:
        raise HTTPException(status_code=404, detail=f"Defender unit not found: {request.defender_faction}/{request.defender_unit}")
    if not weapon:
        raise HTTPException(status_code=404, detail=f"Weapon not found: {request.attacker_faction}/{request.weapon_name}")

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
    attacker_unit = WikiRegistry.get_unit(request.attacker_faction, request.attacker_unit)
    defender_unit = WikiRegistry.get_unit(request.defender_faction, request.defender_unit)

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
