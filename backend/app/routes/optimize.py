"""City-wide cooling optimization endpoint."""

from fastapi import APIRouter, Query

from ..services.optimize_service import optimize_city
from ..utils.logger import logger
from ..utils.response import error_response, success_response

router = APIRouter(tags=["optimize"])


@router.get("/api/optimize")
def optimize(
    city: str = Query("ahmedabad", description="City id, e.g. ahmedabad or surat"),
    budget: int = Query(8, ge=1, le=30, description="Number of zones to treat"),
):
    """Return an optimized cooling action plan for the city."""
    try:
        data = optimize_city(city, budget)
        return success_response(data, "Optimization completed successfully")
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Optimization failed for %s: %s", city, exc)
        return error_response("Optimization failed, please retry", fallback_used=True)
