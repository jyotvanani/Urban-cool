"""Priority scoring and ranking for hotspot zones."""

from ..models.ml_model import _safe
from ..utils.validators import clamp


def calculate_priority_score(hotspot: dict) -> float:
    """Compute a 0-100 priority score for a hotspot.

    Considers heat risk, expected cooling, category, feasibility,
    green cover and built-up density.
    """
    heat = _safe(hotspot, "heat_risk_score")
    reduction = _safe(hotspot, "expected_temp_reduction")
    green = _safe(hotspot, "green_cover_percentage")
    built = _safe(hotspot, "built_up_density")

    category_boost = {
        "Low": 0,
        "Moderate": 5,
        "High": 10,
        "Severe": 18,
    }.get(hotspot.get("hotspot_category", ""), 0)

    feasibility_boost = {
        "High": 8,
        "Medium": 4,
        "Low": 0,
    }.get(hotspot.get("feasibility", "High"), 6)

    # Weighted blend: heat dominates, then cooling potential and exposure.
    score = (
        0.55 * heat                       # higher heat -> higher priority
        + 0.15 * (reduction / 4.0 * 100)  # more achievable cooling -> higher
        + 0.10 * (100 - green)            # less green cover -> higher
        + 0.10 * (built * 100)            # denser built-up -> higher
        + category_boost
        + feasibility_boost
    )
    return round(clamp(score, 0, 100), 1)


def assign_priority_level(score: float) -> str:
    """Map a priority score to a level. 0-40 Low | 41-70 Medium | 71-100 High."""
    try:
        score = clamp(float(score), 0, 100)
    except (TypeError, ValueError):
        score = 0
    if score <= 40:
        return "Low"
    if score <= 70:
        return "Medium"
    return "High"


def rank_hotspots(hotspots: list) -> list:
    """Return hotspots sorted by priority score (descending).

    Each returned item is enriched with ``priority_score`` and ``priority_level``.
    """
    ranked = []
    for h in hotspots or []:
        item = dict(h)
        score = calculate_priority_score(item)
        item["priority_score"] = score
        item["priority_level"] = assign_priority_level(score)
        ranked.append(item)

    ranked.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
    for i, item in enumerate(ranked, start=1):
        item["priority_rank"] = i
    return ranked
