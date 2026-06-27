"""Cooling intervention simulation endpoint."""

from fastapi import APIRouter

from ..models.schemas import SimulateRequest
from ..services.simulation_service import simulate
from ..utils.logger import logger
from ..utils.response import error_response, success_response

router = APIRouter(tags=["simulation"])


@router.post("/api/simulate")
def simulate_interventions(request: SimulateRequest):
    """Simulate the cooling impact of selected interventions for a zone."""
    try:
        result = simulate(request.model_dump())
        return success_response(result, "Simulation completed successfully")
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Simulation failed: %s", exc)
        return error_response(
            "Simulation failed, please retry",
            fallback_used=True,
        )
