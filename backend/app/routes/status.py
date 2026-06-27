"""Data source status endpoint."""

from datetime import datetime

from fastapi import APIRouter

from ..config import settings
from ..models.ml_model import heat_model
from ..services.data_service import get_data_source_status
from ..utils.logger import logger

router = APIRouter(tags=["status"])


@router.get("/api/data/status")
def data_status():
    """Return the status of each data source plus the ML model."""
    try:
        sources = get_data_source_status()
        sources.append(
            {
                "name": "ML Model",
                "status": "active" if heat_model.is_available else "fallback",
                "message": (
                    "Prediction model loaded successfully"
                    if heat_model.is_available
                    else "Using rule-based fallback prediction"
                ),
            }
        )
        return {
            "sources": sources,
            "mode": "demo-safe",
            "last_updated": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Data status error: %s", exc)
        return {
            "sources": [
                {"name": "Landsat 8 LST", "status": "demo", "message": "Using preprocessed demo data"},
                {"name": "Weather API", "status": "cached", "message": "Using cached weather values"},
                {"name": "ML Model", "status": "fallback", "message": "Using rule-based fallback prediction"},
            ],
            "mode": "demo-safe",
            "last_updated": datetime.utcnow().isoformat() + "Z",
        }
