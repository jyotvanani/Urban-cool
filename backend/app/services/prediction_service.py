"""Prediction service: heat risk scoring, drivers and feature contribution."""

from ..models.ml_model import (
    SAFE_DEFAULTS,
    feature_contributions,
    heat_model,
    identify_main_drivers,
)
from ..utils.validators import categorize_heat
from .recommendation_service import recommend_action


def safe_float(value, default: float = 0.0) -> float:
    """Convert ``value`` to float, returning ``default`` on failure."""
    try:
        if value is None or value == "":
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def calculate_heat_category(score) -> str:
    """Map a 0-100 score to Low / Moderate / High / Severe."""
    return categorize_heat(safe_float(score, 0))


def calculate_feature_contribution(payload: dict) -> dict:
    """Return driver contribution percentages that total 100."""
    return feature_contributions(payload)


def detect_main_drivers(payload: dict) -> list:
    """Return the top 3-4 human-readable heat drivers."""
    return identify_main_drivers(payload, limit=4)


def predict_heat_risk(payload: dict) -> dict:
    """Run a full heat-risk prediction for a feature payload.

    Always succeeds: the model falls back to rule-based scoring, and any
    error yields a safe fallback prediction.
    """
    try:
        # Fill safe defaults for any missing fields.
        clean = {k: safe_float(payload.get(k), v) for k, v in SAFE_DEFAULTS.items()}

        prediction = heat_model.predict(clean)
        score = prediction["heat_risk_score"]
        category = prediction["hotspot_category"]

        drivers = detect_main_drivers(clean)
        contribution = calculate_feature_contribution(clean)
        action, _explanation = recommend_action(clean, score)

        return {
            "heat_risk_score": score,
            "hotspot_category": category,
            "confidence": prediction["confidence"],
            "main_drivers": drivers,
            "feature_contribution": contribution,
            "recommended_action": action,
            "model_used": prediction["model_used"],
        }
    except Exception:
        # Absolute last-resort fallback so the API never crashes.
        fallback = heat_model.fallback_predict(payload or {})
        score = fallback["heat_risk_score"]
        return {
            "heat_risk_score": score,
            "hotspot_category": fallback["hotspot_category"],
            "confidence": fallback["confidence"],
            "main_drivers": ["Low vegetation", "High built-up density"],
            "feature_contribution": {
                "Vegetation Loss": 30,
                "Built-up Density": 28,
                "Surface Temperature": 24,
                "Water Distance": 10,
                "Weather Impact": 8,
            },
            "recommended_action": "Increase tree cover and apply cool roofs",
            "model_used": fallback["model_used"],
        }


# Backwards-compatible alias used by the prediction route.
def predict(payload: dict) -> dict:
    return predict_heat_risk(payload)
