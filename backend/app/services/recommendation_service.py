"""Rule-based cooling strategy recommendation engine."""

from typing import Optional, Tuple

from ..models.ml_model import _safe
from ..utils.validators import categorize_heat


def recommend_action(payload: dict, heat_score: Optional[float] = None) -> Tuple[str, str]:
    """Return (recommended_action, explanation) for a zone.

    Rules (in priority order):
      1. Severe heat              -> combined strategy
      2. Low vegetation           -> tree cover + roadside plantation
      3. High built-up + NDBI     -> cool roofs + high-albedo surfaces
      4. Low water / far water    -> blue-green corridors
      5. Moderate heat            -> low-cost shading + micro-greening
      6. Low heat                 -> maintain green cover
    """
    ndvi = _safe(payload, "ndvi")
    ndbi = _safe(payload, "ndbi")
    ndwi = _safe(payload, "ndwi")
    built = _safe(payload, "built_up_density")
    green = _safe(payload, "green_cover_percentage")
    water_dist = _safe(payload, "water_body_distance_km")

    if heat_score is None:
        heat_score = _safe(payload, "heat_risk_score") or 0
    category = categorize_heat(heat_score)

    if category == "Severe" or heat_score >= 81:
        return (
            "Increase tree cover, apply cool roofs, and improve blue-green infrastructure",
            "This zone is in the Severe heat category. A combined strategy of greening, "
            "reflective roofs and blue-green infrastructure delivers the largest cooling.",
        )

    if ndvi < 0.25 or green < 15:
        return (
            "Increase tree cover and roadside plantation",
            "Vegetation cover is low, so adding tree canopy and roadside planting will "
            "provide shade and evapotranspiration cooling.",
        )

    if ndbi > 0.65 and built > 0.70:
        return (
            "Apply cool roofs and high-albedo surfaces",
            "Built-up density and surface imperviousness are high; reflective roofs and "
            "high-albedo pavements reduce absorbed heat.",
        )

    if ndwi < 0.15 or water_dist > 2:
        return (
            "Develop blue-green corridors and improve water body access",
            "The zone has low surface moisture or limited water access; blue-green "
            "corridors improve local cooling and humidity balance.",
        )

    if category == "Moderate":
        return (
            "Low-cost shading, reflective surfaces, and micro-greening",
            "Moderate heat can be managed with affordable shading, reflective surfaces "
            "and small-scale greening interventions.",
        )

    return (
        "Maintain green cover and monitor heat conditions",
        "This zone is in the Low heat category; preserving existing greenery and "
        "monitoring conditions is sufficient.",
    )


def estimate_expected_reduction(payload: dict) -> float:
    """Estimate expected temperature reduction (C) for the recommended action."""
    heat_score = _safe(payload, "heat_risk_score")
    if heat_score == 0:
        # Derive a rough score from drivers if not present.
        from ..models.ml_model import rule_based_score
        heat_score = rule_based_score(payload)

    category = categorize_heat(heat_score)
    # Map intervention intensity to a representative midpoint reduction.
    if category == "Severe":
        return 3.0   # combined intervention: 2.0 - 4.0
    if category == "High":
        return 2.4   # high intervention: 1.8 - 3.0
    if category == "Moderate":
        return 1.4   # moderate intervention: 1.0 - 1.8
    return 0.8       # low intervention: 0.5 - 1.0


def get_cost_level(action: str) -> str:
    """Return a cost level (Low / Medium / High) for an action string."""
    action = (action or "").lower()
    if "blue-green" in action or "combined" in action or "water body" in action:
        return "High"
    if "cool roof" in action or "tree cover" in action or "high-albedo" in action:
        return "Medium"
    return "Low"


def get_feasibility(action: str) -> str:
    """Return a feasibility level (High / Medium) for an action string."""
    action = (action or "").lower()
    if "blue-green" in action or "water body" in action:
        return "Medium"
    return "High"


def get_implementation_suggestions(payload: dict) -> list:
    """Return concrete implementation steps for a zone."""
    ndvi = _safe(payload, "ndvi")
    ndbi = _safe(payload, "ndbi")
    built = _safe(payload, "built_up_density")
    water_dist = _safe(payload, "water_body_distance_km")
    green = _safe(payload, "green_cover_percentage")

    steps = []
    if ndvi < 0.25 or green < 15:
        steps.append("Plant native shade trees along streets and in open plots.")
    if ndbi > 0.65 or built > 0.70:
        steps.append("Roll out cool-roof coatings on public and commercial buildings.")
        steps.append("Replace dark pavements with high-albedo / reflective materials.")
    if water_dist > 2:
        steps.append("Create a blue-green corridor linking the zone to nearby water bodies.")
    steps.append("Add shaded walkways and pocket parks to improve pedestrian comfort.")
    if not steps:
        steps.append("Maintain existing green cover and monitor heat trends seasonally.")
    return steps


# Backwards-compatible alias used by hotspots route and prediction service.
def recommend(payload: dict, heat_score: Optional[float] = None) -> Tuple[str, str]:
    return recommend_action(payload, heat_score)
