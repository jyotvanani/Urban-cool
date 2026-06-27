"""Health check endpoint."""

from datetime import datetime

from fastapi import APIRouter

from ..config import settings
from ..models.ml_model import heat_model
from ..utils.logger import logger

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health():
    """Return backend health information."""
    try:
        return {
            "status": "healthy",
            "backend": "running",
            "ml_model": "available" if heat_model.is_available else "fallback-rule",
            "data_source": "fallback/demo" if settings.DATA_MODE == "demo" else "live",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Health check error: %s", exc)
        return {
            "status": "degraded",
            "backend": "running",
            "ml_model": "fallback-rule",
            "data_source": "fallback/demo",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
