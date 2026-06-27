"""Cities listing endpoint."""

from fastapi import APIRouter

from ..services.data_service import get_cities
from ..utils.logger import logger
from ..utils.response import error_response, success_response

router = APIRouter(tags=["cities"])


@router.get("/api/cities")
def list_cities():
    """Return the list of supported cities."""
    try:
        cities = get_cities()
        return success_response(cities, "Cities retrieved successfully")
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to list cities: %s", exc)
        return error_response(
            "Could not load cities, returned fallback list",
            fallback_used=True,
            data=get_cities(),
        )
