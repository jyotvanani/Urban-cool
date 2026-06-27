"""Lightweight validation and normalization helpers."""

from typing import Optional


def clamp(value: float, low: float, high: float) -> float:
    """Clamp ``value`` into the inclusive range [low, high]."""
    return max(low, min(high, value))


def normalize_city(city: Optional[str]) -> str:
    """Normalize a city identifier to a lowercase, trimmed slug."""
    if not city:
        return ""
    return str(city).strip().lower().replace(" ", "_")


def categorize_heat(score: float) -> str:
    """Map a 0-100 heat risk score to a category label.

    0-30 Low | 31-60 Moderate | 61-80 High | 81-100 Severe
    """
    score = clamp(float(score), 0, 100)
    if score <= 30:
        return "Low"
    if score <= 60:
        return "Moderate"
    if score <= 80:
        return "High"
    return "Severe"


def priority_from_category(category: str) -> str:
    """Map a hotspot category to an implementation priority level."""
    mapping = {
        "Low": "Low",
        "Moderate": "Medium",
        "High": "High",
        "Severe": "Critical",
    }
    return mapping.get(category, "Medium")
