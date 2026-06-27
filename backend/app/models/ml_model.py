"""Machine learning model wrapper with a guaranteed rule-based fallback.

Safety strategy:
  1. Try the trained ML model (model.joblib + optional scaler.joblib).
  2. If the model is missing or fails, use the rule-based fallback.
  3. Missing/invalid inputs are filled with safe defaults.
  4. Any error returns a fallback prediction; the engine never crashes.
"""

from typing import Tuple

import numpy as np

from ..config import settings
from ..utils.logger import logger
from ..utils.validators import categorize_heat, clamp

# Feature ordering must match ml/train_model.py exactly.
FEATURE_ORDER = [
    "lst_temperature",
    "ndvi",
    "ndbi",
    "ndwi",
    "built_up_density",
    "green_cover_percentage",
    "water_body_distance_km",
    "air_temperature",
    "humidity",
    "wind_speed",
]

# Safe default values used when an input field is missing or invalid.
SAFE_DEFAULTS = {
    "lst_temperature": 35.0,
    "ndvi": 0.30,
    "ndbi": 0.50,
    "ndwi": 0.20,
    "built_up_density": 0.50,
    "green_cover_percentage": 25.0,
    "water_body_distance_km": 2.0,
    "air_temperature": 35.0,
    "humidity": 45.0,
    "wind_speed": 8.0,
}

ML_CONFIDENCE = 0.88        # within 0.85 - 0.92
FALLBACK_CONFIDENCE = 0.76  # within 0.70 - 0.82


def _safe(payload: dict, key: str) -> float:
    """Return a float for ``key`` from payload, or a safe default.

    Falls back to SAFE_DEFAULTS when available, otherwise 0.0. Never raises.
    """
    default = float(SAFE_DEFAULTS.get(key, 0.0))
    try:
        value = payload.get(key, None) if isinstance(payload, dict) else None
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


class HeatRiskModel:
    """Loads and serves the heat-risk model with a safe fallback."""

    def __init__(self) -> None:
        self.model = None
        self.scaler = None
        self.model_available = False
        self.load_model()

    def load_model(self) -> None:
        """Attempt to load model + scaler; never raises."""
        try:
            import joblib  # lazy import so a missing dep can't break import

            if settings.MODEL_PATH.exists():
                self.model = joblib.load(settings.MODEL_PATH)
                if settings.SCALER_PATH.exists():
                    self.scaler = joblib.load(settings.SCALER_PATH)
                self.model_available = True
                logger.info("ML model loaded from %s", settings.MODEL_PATH)
            else:
                self.model_available = False
                logger.warning(
                    "Model file not found at %s; using rule-based fallback",
                    settings.MODEL_PATH,
                )
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to load ML model, using fallback: %s", exc)
            self.model = None
            self.scaler = None
            self.model_available = False

    def is_model_available(self) -> bool:
        return self.model_available and self.model is not None

    # Backwards-compatible property used elsewhere in the codebase.
    @property
    def is_available(self) -> bool:
        return self.is_model_available()

    def _features_from_dict(self, payload: dict) -> np.ndarray:
        values = [_safe(payload, name) for name in FEATURE_ORDER]
        return np.array(values, dtype=float).reshape(1, -1)

    def predict(self, input_data: dict) -> dict:
        """Return a prediction dict: score, category, confidence, model_used.

        Tries the ML model first, then falls back to rule-based prediction.
        """
        if self.is_model_available():
            try:
                features = self._features_from_dict(input_data)
                if self.scaler is not None:
                    features = self.scaler.transform(features)
                raw = float(self.model.predict(features)[0])
                score = round(clamp(raw, 0, 100), 2)
                return {
                    "heat_risk_score": score,
                    "hotspot_category": categorize_heat(score),
                    "confidence": ML_CONFIDENCE,
                    "model_used": "RandomForestRegressor",
                }
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("ML prediction failed, using fallback: %s", exc)

        return self.fallback_predict(input_data)

    def fallback_predict(self, input_data: dict) -> dict:
        """Rule-based prediction that always works."""
        score = round(rule_based_score(input_data), 2)
        return {
            "heat_risk_score": score,
            "hotspot_category": categorize_heat(score),
            "confidence": FALLBACK_CONFIDENCE,
            "model_used": "rule-based-fallback",
        }

    def predict_heat_risk(self, payload: dict) -> Tuple[float, float, str]:
        """Backwards-compatible tuple API: (score, confidence, model_used)."""
        result = self.predict(payload)
        return (
            result["heat_risk_score"],
            result["confidence"],
            result["model_used"],
        )


def rule_based_score(payload: dict) -> float:
    """Deterministic rule-based heat risk score in the range 0-100.

    Weighted contributions (sum to 1.0):
      LST 30% | Vegetation 20% | Built-up 20% | Water 10% | Weather 15% | Wind 5%
    """
    lst = _safe(payload, "lst_temperature")
    ndvi = _safe(payload, "ndvi")
    ndbi = _safe(payload, "ndbi")
    ndwi = _safe(payload, "ndwi")
    built = _safe(payload, "built_up_density")
    green = _safe(payload, "green_cover_percentage")
    water_dist = _safe(payload, "water_body_distance_km")
    air = _safe(payload, "air_temperature")
    wind = _safe(payload, "wind_speed")

    # Normalize each driver to a 0-1 contribution.
    lst_c = clamp((lst - 28) / (48 - 28), 0, 1)          # 28C..48C
    veg_c = clamp(
        0.6 * clamp((0.25 - ndvi) / 0.25 if ndvi < 0.25 else (0.6 - ndvi) / 0.6, 0, 1)
        + 0.4 * clamp((25 - green) / 25, 0, 1),
        0, 1,
    )
    built_c = clamp(0.5 * clamp(ndbi, 0, 1) + 0.5 * clamp(built, 0, 1), 0, 1)
    water_c = clamp(
        0.5 * clamp((0.15 - ndwi) / 0.15 if ndwi < 0.15 else 0, 0, 1)
        + 0.5 * clamp(water_dist / 5.0, 0, 1),
        0, 1,
    )
    weather_c = clamp((air - 28) / (45 - 28), 0, 1)      # 28C..45C
    wind_c = clamp((6 - wind) / 6 if wind < 6 else (12 - wind) / 12, 0, 1)

    weighted = (
        0.30 * lst_c
        + 0.20 * veg_c
        + 0.20 * built_c
        + 0.10 * water_c
        + 0.15 * weather_c
        + 0.05 * wind_c
    )
    return clamp(weighted * 100.0, 0, 100)


def feature_contributions(payload: dict) -> dict:
    """Return percentage contribution of 5 driver groups, totalling ~100."""
    lst = _safe(payload, "lst_temperature")
    ndvi = _safe(payload, "ndvi")
    ndbi = _safe(payload, "ndbi")
    ndwi = _safe(payload, "ndwi")
    built = _safe(payload, "built_up_density")
    green = _safe(payload, "green_cover_percentage")
    water_dist = _safe(payload, "water_body_distance_km")
    air = _safe(payload, "air_temperature")
    wind = _safe(payload, "wind_speed")

    raw = {
        "Vegetation Loss": 0.20 * clamp(
            0.5 * clamp((0.6 - ndvi) / 0.6, 0, 1) + 0.5 * clamp((50 - green) / 50, 0, 1),
            0, 1,
        ),
        "Built-up Density": 0.20 * clamp(0.5 * clamp(ndbi, 0, 1) + 0.5 * clamp(built, 0, 1), 0, 1),
        "Surface Temperature": 0.30 * clamp((lst - 28) / 20, 0, 1),
        "Water Distance": 0.10 * clamp(
            0.5 * clamp((0.4 - ndwi) / 0.4, 0, 1) + 0.5 * clamp(water_dist / 5.0, 0, 1),
            0, 1,
        ),
        "Weather Impact": 0.20 * clamp(
            0.6 * clamp((air - 28) / 17, 0, 1) + 0.4 * clamp((12 - wind) / 12, 0, 1),
            0, 1,
        ),
    }
    total = sum(raw.values()) or 1.0
    pct = {k: round((v / total) * 100) for k, v in raw.items()}

    # Adjust rounding so the values total exactly 100.
    drift = 100 - sum(pct.values())
    if pct:
        top_key = max(pct, key=pct.get)
        pct[top_key] += drift
    return pct


def identify_main_drivers(payload: dict, limit: int = 4) -> list:
    """Return the main heat drivers as human-readable strings (top 3-4)."""
    ndvi = _safe(payload, "ndvi")
    ndbi = _safe(payload, "ndbi")
    ndwi = _safe(payload, "ndwi")
    built = _safe(payload, "built_up_density")
    green = _safe(payload, "green_cover_percentage")
    water_dist = _safe(payload, "water_body_distance_km")
    lst = _safe(payload, "lst_temperature")
    air = _safe(payload, "air_temperature")
    wind = _safe(payload, "wind_speed")

    drivers = []
    if ndvi < 0.25 or green < 15:
        drivers.append("Low vegetation")
    if ndbi > 0.65 or built > 0.70:
        drivers.append("High built-up density")
    if lst > 42:
        drivers.append("High surface temperature")
    if ndwi < 0.15 or water_dist > 2:
        drivers.append("Low water presence")
    if air > 38:
        drivers.append("High ambient temperature")
    if wind < 6:
        drivers.append("Low wind circulation")

    if not drivers:
        drivers = ["Balanced conditions", "Adequate vegetation"]
    return drivers[: max(3, min(limit, len(drivers)))][:limit]


# Singleton model instance loaded once at import time.
heat_model = HeatRiskModel()
