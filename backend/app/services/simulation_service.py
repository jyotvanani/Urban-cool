"""Transparent cooling-intervention simulation engine.

Each intervention scales linearly (0-100%) up to a maximum reduction.
Total reduction is capped at 4.0 C.
"""

from ..utils.validators import clamp
from .data_service import get_hotspot_by_id

# Maximum reduction (C) achievable per intervention at 100%.
MAX_EFFECTS = {
    "tree_cover_increase": 1.5,
    "cool_roof_percentage": 1.2,
    "green_roof_percentage": 0.8,
    "water_body_improvement": 0.7,
    "high_albedo_surface": 0.9,
}

TOTAL_CAP = 4.0

LABELS = {
    "tree_cover_increase": "Tree cover",
    "cool_roof_percentage": "Cool roofs",
    "green_roof_percentage": "Green roofs",
    "water_body_improvement": "Water body improvement",
    "high_albedo_surface": "High-albedo surfaces",
}


def _pct(inputs: dict, key: str) -> float:
    try:
        return clamp(float(inputs.get(key, 0) or 0), 0, 100)
    except (TypeError, ValueError):
        return 0.0


def calculate_reduction(inputs: dict) -> float:
    """Return the total estimated temperature reduction (C), capped at 4.0."""
    total = 0.0
    for key, max_effect in MAX_EFFECTS.items():
        total += (_pct(inputs, key) / 100.0) * max_effect
    return round(min(total, TOTAL_CAP), 2)


def calculate_impact_score(reduction: float) -> int:
    """Map a temperature reduction to a 0-100 impact score."""
    return int(round(clamp((reduction / TOTAL_CAP) * 100, 0, 100)))


def _spend(inputs: dict) -> float:
    weights = {
        "tree_cover_increase": 0.6,
        "cool_roof_percentage": 0.8,
        "green_roof_percentage": 1.0,
        "water_body_improvement": 1.2,
        "high_albedo_surface": 0.7,
    }
    return sum((_pct(inputs, k) / 100.0) * w for k, w in weights.items())


def calculate_cost_level(inputs: dict) -> str:
    spend = _spend(inputs)
    if spend < 0.8:
        return "Low"
    if spend < 1.8:
        return "Medium"
    return "High"


def calculate_feasibility(inputs: dict) -> str:
    spend = _spend(inputs)
    if spend < 1.0:
        return "High"
    if spend < 2.2:
        return "Medium"
    return "Low"


def generate_strategy(inputs: dict) -> str:
    """Return the top two contributing interventions as a strategy string."""
    contributions = {
        key: (_pct(inputs, key) / 100.0) * effect
        for key, effect in MAX_EFFECTS.items()
    }
    ranked = sorted(contributions.items(), key=lambda kv: kv[1], reverse=True)
    top = [LABELS[name] for name, value in ranked if value > 0][:2]
    return " + ".join(top) if top else "No intervention selected"


def generate_explanation(zone_data: dict, inputs: dict, reduction: float) -> str:
    current = float(zone_data.get("lst_temperature", 42.0))
    if reduction <= 0:
        return "No interventions were selected, so no temperature reduction is expected."
    strategy = generate_strategy(inputs).lower()
    new_lst = round(current - reduction, 2)
    return (
        f"Increasing {strategy} can reduce heat intensity in this zone by about "
        f"{reduction} C, lowering land surface temperature from {current} C to {new_lst} C."
    )


def simulate_cooling(zone_data: dict, inputs: dict) -> dict:
    """Run the full simulation for a zone given intervention inputs."""
    zone_data = zone_data or {}
    current_lst = float(zone_data.get("lst_temperature", 42.0))

    reduction = calculate_reduction(inputs)
    new_lst = round(current_lst - reduction, 2)

    return {
        "zone_id": zone_data.get("zone_id", inputs.get("zone_id", "unknown")),
        "current_lst": round(current_lst, 2),
        "estimated_new_lst": new_lst,
        "estimated_temp_reduction": reduction,
        "impact_score": calculate_impact_score(reduction),
        "cost_level": calculate_cost_level(inputs),
        "feasibility": calculate_feasibility(inputs),
        "recommended_strategy": generate_strategy(inputs),
        "explanation": generate_explanation(zone_data, inputs, reduction),
    }


def simulate(payload: dict) -> dict:
    """Route-facing wrapper: resolve the zone, then simulate."""
    zone_id = payload.get("zone_id", "unknown")
    zone = get_hotspot_by_id(zone_id) or {"zone_id": zone_id, "lst_temperature": 42.0}
    return simulate_cooling(zone, payload)
