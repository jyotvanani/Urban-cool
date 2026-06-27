"""Heat-risk prediction endpoint."""

from fastapi import APIRouter

from ..models.schemas import PredictRequest
from ..services.prediction_service import predict
from ..utils.logger import logger
from ..utils.response import error_response, success_response

router = APIRouter(tags=["prediction"])


@router.post("/api/predict")
def predict_heat(request: PredictRequest):
    """Predict heat risk from raw zone features.

    Tries the ML model first and falls back to rule-based scoring, so this
    endpoint always returns a valid prediction.
    """
    try:
        result = predict(request.model_dump())
        return success_response(result, "Prediction completed successfully")
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Prediction failed: %s", exc)
        # Last-resort fallback so we never return a 500.
        try:
            from ..models.ml_model import rule_based_score
            from ..utils.validators import categorize_heat

            score = rule_based_score(request.model_dump())
            fallback = {
                "heat_risk_score": round(score, 2),
                "hotspot_category": categorize_heat(score),
                "confidence": 0.6,
                "main_drivers": ["Low vegetation", "High built-up density"],
                "recommended_action": "Increase tree cover and apply cool roofs",
                "model_used": "fallback-rule",
            }
            return error_response(
                "Prediction used emergency fallback",
                fallback_used=True,
                data=fallback,
            )
        except Exception as inner:  # pragma: no cover - defensive
            logger.error("Emergency prediction fallback failed: %s", inner)
            return error_response("Prediction unavailable", fallback_used=True)
