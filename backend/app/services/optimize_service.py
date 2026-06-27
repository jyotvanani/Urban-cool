"""City-wide cooling optimization.

Given a city and a budget (how many zones can be treated), select the
highest-impact zones and the best return-on-effort interventions to maximize
total temperature reduction, then return a prioritized action plan.
"""

from ..models.ml_model import _safe
from ..utils.validators import clamp
from .cost_service import ECON as COST_ECON
from .data_service import load_hotspots
from .priority_service import rank_hotspots
from .simulation_service import MAX_EFFECTS, simulate_cooling


def _plan_cost(inputs: dict) -> float:
    """Cost of an intervention mix in INR lakh, from the cost model."""
    total = 0.0
    for key, pct in inputs.items():
        econ = COST_ECON.get(key)
        if econ:
            total += (clamp(pct, 0, 100) / 100.0) * econ["cost_per_100"]
    return round(total, 1)


def _cost_level(cost_lakh: float) -> str:
    if cost_lakh < 11:
        return "Low"
    if cost_lakh < 20:
        return "Medium"
    return "High"


def _signals(zone: dict):
    """Normalised, independent need scores (0-1) from real satellite signals."""
    ndvi = _safe(zone, "ndvi")
    ndbi = _safe(zone, "ndbi_sentinel2")
    if ndbi == 0:
        ndbi = _safe(zone, "ndbi")  # fallback for older zones
    ndwi = _safe(zone, "ndwi")
    lst = _safe(zone, "lst_temperature")

    greening = clamp((0.36 - ndvi) / 0.26, 0, 1)      # low vegetation -> high need
    reflective = clamp((ndbi + 0.04) / 0.14, 0, 1)    # high built-up -> high need
    water = clamp((-0.12 - ndwi) / 0.29, 0, 1)        # very dry -> high need
    intensity = clamp((lst - 37) / 8.0, 0.4, 1.0)     # hotter -> more aggressive
    return greening, reflective, water, intensity


def _strategy_for(zone: dict, inputs: dict) -> str:
    """Strategy label from the zone's dominant real drivers (varies per zone)."""
    greening, reflective, water, _ = _signals(zone)
    themes = [
        ("Urban greening (tree cover)", greening),
        ("Reflective roofs & surfaces", reflective),
        ("Blue-green corridor", water if inputs.get("water_body_improvement", 0) else 0),
    ]
    themes.sort(key=lambda t: t[1], reverse=True)
    chosen = [name for name, score in themes if score > 0.3][:2]
    if not chosen:
        chosen = [themes[0][0]]
    return " + ".join(chosen)


def _recommend_interventions(zone: dict) -> dict:
    """Pick intervention percentages tailored to a zone's actual heat drivers.

    The mix varies per zone (vegetation deficit, built-up density, water
    access and heat severity), so different zones get genuinely different
    plans, reductions and costs.
    """
    greening, reflective, water, intensity = _signals(zone)
    inputs = {k: 0 for k in MAX_EFFECTS}

    inputs["tree_cover_increase"] = round(clamp(greening * 95 * intensity, 0, 100))
    inputs["cool_roof_percentage"] = round(clamp(reflective * 85 * intensity, 0, 100))
    inputs["high_albedo_surface"] = round(clamp(reflective * 60 * intensity, 0, 100))

    # Green roofs only where built-up density is genuinely high.
    if reflective > 0.5:
        inputs["green_roof_percentage"] = round(clamp(reflective * 35 * intensity, 0, 100))

    # Water-body work only for the genuinely driest zones (keeps cost down
    # everywhere else, since this is the most expensive lever).
    if water > 0.6:
        inputs["water_body_improvement"] = round(clamp(water * 50 * intensity, 0, 100))

    # Floor: ensure every treated zone has a meaningful action.
    if sum(inputs.values()) < 20:
        inputs["tree_cover_increase"] = max(inputs["tree_cover_increase"], 30)
        inputs["cool_roof_percentage"] = max(inputs["cool_roof_percentage"], 25)

    return inputs


_STRATEGY_LABELS = {
    "tree_cover_increase": "tree cover",
    "cool_roof_percentage": "cool roofs",
    "high_albedo_surface": "high-albedo surfaces",
    "green_roof_percentage": "green roofs",
    "water_body_improvement": "blue-green corridors",
}


def _strategy_label(interventions: dict) -> str:
    """Human-readable strategy from the chosen interventions (top 3 by effect)."""
    contrib = {
        k: (interventions.get(k, 0) / 100.0) * MAX_EFFECTS[k]
        for k in MAX_EFFECTS
    }
    ranked = [k for k in sorted(contrib, key=contrib.get, reverse=True) if contrib[k] > 0]
    labels = [_STRATEGY_LABELS[k] for k in ranked[:3]]
    if not labels:
        return "No intervention selected"
    if len(labels) == 1:
        return labels[0].capitalize()
    head = ", ".join(labels[:-1])
    return f"{head} + {labels[-1]}".capitalize()


def optimize_city(city: str, budget: int = 8) -> dict:
    """Return an optimized cooling plan for a city. Never raises."""
    zones = load_hotspots(city)
    if not zones:
        return {
            "city": city,
            "budget": budget,
            "zones_treated": 0,
            "total_expected_reduction": 0,
            "average_reduction": 0,
            "plan": [],
            "summary": "No zones available to optimize.",
        }

    budget = max(1, min(int(budget or 8), len(zones)))
    ranked = rank_hotspots(zones)
    selected = ranked[:budget]

    plan = []
    total_reduction = 0.0
    cost_rank = {"Low": 0, "Medium": 1, "High": 2}
    cost_sum = 0
    total_cost_lakh = 0.0

    for z in selected:
        interventions = _recommend_interventions(z)
        sim = simulate_cooling(z, interventions)
        cost_lakh = _plan_cost(interventions)
        cost_level = _cost_level(cost_lakh)
        strategy = _strategy_for(z, interventions)

        total_reduction += sim["estimated_temp_reduction"]
        total_cost_lakh += cost_lakh
        cost_sum += cost_rank.get(cost_level, 1)

        plan.append({
            "zone_id": z.get("zone_id"),
            "zone_name": z.get("zone_name"),
            "hotspot_category": z.get("hotspot_category"),
            "priority_score": z.get("priority_score"),
            "current_lst": sim["current_lst"],
            "estimated_new_lst": sim["estimated_new_lst"],
            "estimated_temp_reduction": sim["estimated_temp_reduction"],
            "impact_score": sim["impact_score"],
            "recommended_strategy": strategy,
            "cost_level": cost_level,
            "cost_lakh": cost_lakh,
            "interventions": interventions,
        })

    total_reduction = round(total_reduction, 2)
    total_cost_lakh = round(total_cost_lakh, 1)
    avg = round(total_reduction / len(plan), 2) if plan else 0
    # Overall cost reflects the typical (average) zone, not the single priciest.
    avg_rank = round(cost_sum / len(plan)) if plan else 1
    overall_cost = ["Low", "Medium", "High"][min(max(avg_rank, 0), 2)]

    return {
        "city": city,
        "budget": budget,
        "zones_treated": len(plan),
        "total_expected_reduction": total_reduction,
        "average_reduction": avg,
        "overall_cost_level": overall_cost,
        "total_cost_lakh": total_cost_lakh,
        "plan": plan,
        "summary": (
            f"Treating the top {len(plan)} priority zones in {city.title()} can deliver "
            f"about {total_reduction} C of combined cooling (avg {avg} C per zone), "
            f"at an overall {overall_cost.lower()} cost level."
        ),
    }
