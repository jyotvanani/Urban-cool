"""Cost advisor: cost of cooling and the most cost-effective methods.

For a zone and a target temperature reduction, finds the minimum-cost plan by
allocating to the highest cooling-per-rupee interventions first, and explains
how to get more cooling for less money.
"""

from ..models.ml_model import _safe
from ..utils.validators import clamp
from .data_service import get_hotspot_by_id

# Intervention economics (planning estimates for a typical neighbourhood):
#   max_effect   = max cooling (C) at full coverage
#   cost_per_100 = cost in INR lakh to apply at full coverage
ECON = {
    "high_albedo_surface": {"max_effect": 0.9, "cost_per_100": 6, "label": "High-albedo surfaces"},
    "cool_roof_percentage": {"max_effect": 1.2, "cost_per_100": 9, "label": "Cool roofs"},
    "tree_cover_increase": {"max_effect": 1.5, "cost_per_100": 14, "label": "Tree cover"},
    "green_roof_percentage": {"max_effect": 0.8, "cost_per_100": 18, "label": "Green roofs"},
    "water_body_improvement": {"max_effect": 0.7, "cost_per_100": 22, "label": "Water body improvement"},
}

TOTAL_CAP = 4.0


def _efficiency(name: str) -> float:
    """Cooling per INR lakh at full coverage (higher = more cost-effective)."""
    e = ECON[name]
    return e["max_effect"] / e["cost_per_100"]


def efficiency_ranking() -> list:
    """Methods ranked by cost-effectiveness (cooling per rupee)."""
    ranked = sorted(ECON.keys(), key=_efficiency, reverse=True)
    out = []
    for name in ranked:
        e = ECON[name]
        out.append({
            "method": e["label"],
            "key": name,
            "max_cooling": e["max_effect"],
            "cost_per_100_lakh": e["cost_per_100"],
            "cooling_per_lakh": round(_efficiency(name), 4),
        })
    return out


def cost_advisor(zone_id: str, target: float = 2.0) -> dict:
    """Build a minimum-cost plan to reach a target cooling for a zone."""
    zone = get_hotspot_by_id(zone_id) or {"zone_id": zone_id, "lst_temperature": 40.0}
    current_lst = _safe(zone, "lst_temperature") or 40.0

    target = round(clamp(float(target or 0), 0.1, TOTAL_CAP), 2)

    # Greedy: spend on the most cost-effective interventions first.
    ranked = sorted(ECON.keys(), key=_efficiency, reverse=True)
    remaining = target
    total_cost = 0.0
    plan = []

    for name in ranked:
        if remaining <= 0:
            break
        e = ECON[name]
        # How much of this lever (0-100%) is needed for the remaining target.
        needed_pct = clamp((remaining / e["max_effect"]) * 100, 0, 100)
        cooling = round((needed_pct / 100) * e["max_effect"], 2)
        cost = round((needed_pct / 100) * e["cost_per_100"], 1)
        if needed_pct <= 0.5:
            continue
        plan.append({
            "method": e["label"],
            "key": name,
            "coverage_pct": round(needed_pct),
            "cooling": cooling,
            "cost_lakh": cost,
            "cooling_per_lakh": round(_efficiency(name), 4),
        })
        remaining = round(remaining - cooling, 2)
        total_cost += cost

    achieved = round(target - max(remaining, 0), 2)
    total_cost = round(total_cost, 1)

    # Baseline: cost of the SAME cooling using an unoptimised (average-efficiency)
    # approach. This is a believable comparison, not a worst-case extreme.
    avg_eff = sum(_efficiency(n) for n in ECON) / len(ECON)
    naive_cost = round(achieved / avg_eff, 1) if avg_eff else total_cost
    if naive_cost < total_cost:
        naive_cost = total_cost
    savings = round(max(naive_cost - total_cost, 0), 1)
    savings_pct = round((savings / naive_cost) * 100) if naive_cost else 0

    best_method = plan[0]["method"].lower() if plan else "high-albedo surfaces"
    tip = (
        f"Prioritise {best_method} and cool roofs — they deliver the most cooling "
        f"per rupee. Spending on these high-efficiency measures first reaches the "
        f"{target} C target for about Rs {total_cost} lakh, roughly {savings_pct}% "
        f"cheaper than an unplanned mix."
    ) if plan else "Set a higher target to see cost-saving recommendations."

    return {
        "zone_id": zone.get("zone_id", zone_id),
        "zone_name": zone.get("zone_name"),
        "current_lst": round(current_lst, 2),
        "target_reduction": target,
        "achieved_reduction": achieved,
        "estimated_new_lst": round(current_lst - achieved, 2),
        "total_cost_lakh": total_cost,
        "naive_cost_lakh": naive_cost,
        "savings_lakh": savings,
        "savings_pct": savings_pct,
        "plan": plan,
        "efficiency_ranking": efficiency_ranking(),
        "tip": tip,
    }
