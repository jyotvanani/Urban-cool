"""Cost advisor endpoint."""

from fastapi import APIRouter, Query

from ..services.cost_service import cost_advisor
from ..utils.logger import logger
from ..utils.response import error_response, success_response

router = APIRouter(tags=["cost"])


@router.get("/api/cost-advisor")
def cost(
    zone_id: str = Query(..., description="Zone id, e.g. ahm_zone_01"),
    target: float = Query(2.0, ge=0.1, le=4.0, description="Target cooling in C"),
):
    """Return a minimum-cost cooling plan and cost-saving advice for a zone."""
    try:
        data = cost_advisor(zone_id, target)
        return success_response(data, "Cost advisor completed successfully")
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Cost advisor failed for %s: %s", zone_id, exc)
        return error_response("Cost advisor failed, please retry", fallback_used=True)
