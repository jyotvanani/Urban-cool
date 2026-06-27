"""Hotspot listing and detail endpoints."""

from fastapi import APIRouter, Query

from ..models.ml_model import feature_contributions, identify_main_drivers
from ..services.data_service import get_hotspot_by_id, get_hotspots
from ..services.recommendation_service import recommend
from ..utils.logger import logger
from ..utils.response import error_response, success_response

router = APIRouter(tags=["hotspots"])


@router.get("/api/hotspots")
def hotspots(city: str = Query(None, description="City id, e.g. ahmedabad or surat")):
    """Return hotspot zones for the selected city (or all cities)."""
    try:
        data = get_hotspots(city)
        message = (
            f"Hotspots for '{city}' retrieved successfully"
            if city
            else "All hotspots retrieved successfully"
        )
        return success_response(data, message)
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to load hotspots for %s: %s", city, exc)
        return error_response(
            "Could not load hotspots, returned fallback data",
            fallback_used=True,
            data=get_hotspots(None),
        )


@router.get("/api/hotspots/{zone_id}")
def hotspot_detail(zone_id: str):
    """Return detailed, explainable data for a single hotspot zone."""
    try:
        zone = get_hotspot_by_id(zone_id)
        if not zone:
            return error_response(
                f"Hotspot '{zone_id}' not found",
                fallback_used=False,
            )

        contributions = feature_contributions(zone)
        drivers = zone.get("main_drivers") or identify_main_drivers(zone)
        action, explanation = recommend(zone, float(zone.get("heat_risk_score", 0)))

        detail = {
            "basic_info": {
                "zone_id": zone.get("zone_id"),
                "zone_name": zone.get("zone_name"),
                "city": zone.get("city"),
                "latitude": zone.get("latitude"),
                "longitude": zone.get("longitude"),
                "lst_temperature": zone.get("lst_temperature"),
                "air_temperature": zone.get("air_temperature"),
                "humidity": zone.get("humidity"),
                "wind_speed": zone.get("wind_speed"),
            },
            "heat_score": zone.get("heat_risk_score"),
            "hotspot_category": zone.get("hotspot_category"),
            "driver_analysis": drivers,
            "feature_contribution_percentages": contributions,
            "recommendation": {
                "recommended_action": zone.get("recommended_action") or action,
                "explanation": explanation,
                "expected_temp_reduction": zone.get("expected_temp_reduction"),
                "priority_level": zone.get("priority_level"),
            },
            "simulation_ready_parameters": {
                "zone_id": zone.get("zone_id"),
                "current_lst": zone.get("lst_temperature"),
                "ndvi": zone.get("ndvi"),
                "ndbi": zone.get("ndbi"),
                "ndwi": zone.get("ndwi"),
                "built_up_density": zone.get("built_up_density"),
                "green_cover_percentage": zone.get("green_cover_percentage"),
                "water_body_distance_km": zone.get("water_body_distance_km"),
            },
        }
        return success_response(detail, "Hotspot detail retrieved successfully")
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to load hotspot %s: %s", zone_id, exc)
        return error_response(
            f"Could not load hotspot '{zone_id}'",
            fallback_used=True,
        )
