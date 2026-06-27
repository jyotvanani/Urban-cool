"""Air Quality Index endpoint (data.gov.in)."""

from fastapi import APIRouter, Query

from ..services.air_quality_service import get_air_quality
from ..utils.logger import logger
from ..utils.response import error_response, success_response

router = APIRouter(tags=["air-quality"])


@router.get("/api/air-quality")
def air_quality(city: str = Query("ahmedabad", description="City id, e.g. ahmedabad or surat")):
    """Return aggregated real-time AQI for the selected city."""
    try:
        data = get_air_quality(city)
        return success_response(data, "Air quality retrieved successfully")
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Air quality fetch failed for %s: %s", city, exc)
        return error_response(
            "Could not load air quality, returned fallback data",
            fallback_used=True,
            data=get_air_quality(city),
        )
