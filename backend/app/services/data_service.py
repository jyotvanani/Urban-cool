"""Data access layer implementing the demo-safe fallback strategy.

Loading order for any data request:
    1. Live API / external data (only if USE_LIVE_API is enabled).
    2. Cached data (in-memory cache populated on first successful read).
    3. Local fallback demo JSON data.

The service never raises to the caller; it always returns usable data so the
backend cannot crash because of missing API data.
"""

import json
import time
from pathlib import Path
from typing import List, Optional

import requests

from ..config import settings
from ..utils.logger import logger
from ..utils.validators import normalize_city

# In-memory cache: { filename: parsed_json }
_CACHE: dict = {}

# Short-lived cache for live weather lookups: { "lat,lon": {ts, data} }
_WEATHER_CACHE: dict = {}
_WEATHER_TTL_SECONDS = 600  # 10 minutes


def _read_json_file(path: Path) -> Optional[object]:
    """Read and parse a JSON file, returning None on any failure."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        logger.warning("Data file not found: %s", path)
    except json.JSONDecodeError as exc:
        logger.error("Invalid JSON in %s: %s", path, exc)
    except Exception as exc:  # pragma: no cover - defensive catch-all
        logger.error("Unexpected error reading %s: %s", path, exc)
    return None


def _load_with_fallback(filename: str) -> Optional[object]:
    """Load a data file using cache first, then disk, with logging."""
    if filename in _CACHE:
        return _CACHE[filename]

    data = _read_json_file(settings.DATA_DIR / filename)
    if data is not None:
        _CACHE[filename] = data
    return data


def _try_live_api(city: str) -> Optional[List[dict]]:
    """Attempt to fetch live data. Disabled by default for demo safety.

    Returns None whenever live data is unavailable so callers fall through to
    cached / fallback data. Network errors are swallowed by design.
    """
    if not settings.USE_LIVE_API:
        return None

    # City -> base hotspot file. We keep satellite indices from demo data and
    # overlay only live weather (air temperature, humidity, wind speed).
    file_map = {
        "ahmedabad": "hotspots_ahmedabad.json",
        "surat": "hotspots_surat.json",
    }
    filename = file_map.get(city)
    if not filename:
        return None

    base = _load_with_fallback(filename)
    if not isinstance(base, list) or not base:
        return None

    enriched_any = False
    result = [dict(z) for z in base]

    # Fetch weather for all zones concurrently to keep the endpoint fast.
    from concurrent.futures import ThreadPoolExecutor

    def _fetch_for(zone):
        return _fetch_live_weather(zone.get("latitude"), zone.get("longitude"))

    try:
        with ThreadPoolExecutor(max_workers=8) as pool:
            weathers = list(pool.map(_fetch_for, result))
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Concurrent weather fetch failed: %s", exc)
        weathers = [None] * len(result)

    for zone, weather in zip(result, weathers):
        if weather:
            zone.update(weather)
            zone["data_source"] = "live"
            enriched_any = True

    if enriched_any:
        logger.info("Applied live weather to %s zones for %s", len(result), city)
        return result

    # No zone could be updated -> fall through to cached/demo data.
    return None


def _fetch_live_weather(lat, lon) -> Optional[dict]:
    """Fetch current weather from Open-Meteo (free, no API key).

    Results are cached in-memory for a few minutes so repeated requests stay
    fast. Returns {air_temperature, humidity, wind_speed} or None on failure.
    """
    if lat is None or lon is None:
        return None

    cache_key = f"{round(float(lat), 3)},{round(float(lon), 3)}"
    cached = _WEATHER_CACHE.get(cache_key)
    if cached and (time.time() - cached["ts"]) < _WEATHER_TTL_SECONDS:
        return cached["data"]

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
    )
    try:
        response = requests.get(url, timeout=4)
        response.raise_for_status()
        current = (response.json() or {}).get("current", {})
        temp = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        wind = current.get("wind_speed_10m")
        if temp is None and humidity is None and wind is None:
            return None
        result = {}
        if temp is not None:
            result["air_temperature"] = round(float(temp), 1)
        if humidity is not None:
            result["humidity"] = round(float(humidity), 1)
        if wind is not None:
            # Open-Meteo wind is km/h by default; convert to m/s for our data.
            result["wind_speed"] = round(float(wind) / 3.6, 1)
        data = result or None
        _WEATHER_CACHE[cache_key] = {"ts": time.time(), "data": data}
        return data
    except requests.RequestException as exc:
        logger.warning("Open-Meteo request failed (%s,%s): %s", lat, lon, exc)
    except Exception as exc:  # pragma: no cover - defensive catch-all
        logger.warning("Open-Meteo error (%s,%s): %s", lat, lon, exc)
    return None


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def get_cities() -> List[dict]:
    """Return the list of supported cities (always returns at least one)."""
    data = _load_with_fallback("cities.json")
    if isinstance(data, list) and data:
        return data

    logger.warning("cities.json missing/empty, using built-in fallback cities")
    return [
        {
            "city_id": "ahmedabad",
            "name": "Ahmedabad",
            "state": "Gujarat",
            "country": "India",
            "center_lat": 23.0225,
            "center_lng": 72.5714,
        },
        {
            "city_id": "surat",
            "name": "Surat",
            "state": "Gujarat",
            "country": "India",
            "center_lat": 21.1702,
            "center_lng": 72.8311,
        },
    ]


def get_fallback_hotspots() -> List[dict]:
    """Return the universal fallback hotspot list."""
    data = _load_with_fallback("fallback_hotspots.json")
    if isinstance(data, list) and data:
        return data
    # Hard-coded last-resort so this can never be empty.
    return [
        {
            "zone_id": "demo_zone_01",
            "zone_name": "Demo City Center",
            "city": "demo",
            "latitude": 23.0,
            "longitude": 72.5,
            "lst_temperature": 42.0,
            "ndvi": 0.18,
            "ndbi": 0.70,
            "ndwi": 0.09,
            "built_up_density": 0.80,
            "green_cover_percentage": 12,
            "water_body_distance_km": 2.5,
            "air_temperature": 38.5,
            "humidity": 40,
            "wind_speed": 7.0,
            "heat_risk_score": 82,
            "hotspot_category": "Severe",
            "main_drivers": ["Low vegetation", "High built-up density", "Low water presence"],
            "recommended_action": "Increase tree cover and apply cool roofs",
            "expected_temp_reduction": 2.5,
            "priority_level": "Critical",
        }
    ]


def get_hotspots(city: Optional[str] = None) -> List[dict]:
    """Return hotspot zones for a city following the fallback strategy.

    If ``city`` is None, return all known hotspots across cities.
    """
    city_slug = normalize_city(city)

    # 1) Live API (disabled by default).
    if city_slug:
        live = _try_live_api(city_slug)
        if live:
            return live

    # 2) Cached / disk data per city.
    file_map = {
        "ahmedabad": "hotspots_ahmedabad.json",
        "surat": "hotspots_surat.json",
    }

    if city_slug:
        filename = file_map.get(city_slug)
        if filename:
            data = _load_with_fallback(filename)
            if isinstance(data, list) and data:
                return data
        logger.warning("No hotspot file for city '%s', using fallback data", city_slug)
        return get_fallback_hotspots()

    # No city specified -> aggregate everything we have.
    aggregated: List[dict] = []
    for filename in file_map.values():
        data = _load_with_fallback(filename)
        if isinstance(data, list):
            aggregated.extend(data)

    if aggregated:
        return aggregated
    return get_fallback_hotspots()


def get_hotspot_by_id(zone_id: str) -> Optional[dict]:
    """Return a single hotspot by zone_id searching all known sources."""
    if not zone_id:
        return None

    target = zone_id.strip().lower()
    sources = ["hotspots_ahmedabad.json", "hotspots_surat.json"]

    for filename in sources:
        data = _load_with_fallback(filename)
        if isinstance(data, list):
            for zone in data:
                if str(zone.get("zone_id", "")).lower() == target:
                    return zone

    # Fall back to demo zones.
    for zone in get_fallback_hotspots():
        if str(zone.get("zone_id", "")).lower() == target:
            return zone

    return None


def get_data_source_status() -> List[dict]:
    """Describe the status of each data source for the status endpoint."""
    has_ahmedabad = _load_with_fallback("hotspots_ahmedabad.json") is not None
    lst_status = "demo" if has_ahmedabad else "fallback"

    if settings.USE_LIVE_API:
        weather_status = "live"
        weather_message = "Using live Open-Meteo weather data"
    else:
        weather_status = "cached"
        weather_message = "Using cached weather values"

    return [
        {
            "name": "Landsat 8 LST",
            "status": lst_status,
            "message": "Using preprocessed demo data",
        },
        {
            "name": "Weather API",
            "status": weather_status,
            "message": weather_message,
        },
    ]


# --------------------------------------------------------------------------- #
# Spec-named helpers (aliases + enrichment)
# --------------------------------------------------------------------------- #
def load_cities() -> List[dict]:
    """Alias for get_cities()."""
    return get_cities()


def load_fallback_hotspots() -> List[dict]:
    """Alias for get_fallback_hotspots()."""
    return get_fallback_hotspots()


def enrich_hotspot_data(hotspot: dict) -> dict:
    """Ensure a hotspot has all prediction fields needed by the frontend.

    Missing heat score, category, drivers, recommendation, feature
    contribution, expected reduction or priority level are computed using the
    prediction / recommendation services. Never raises.
    """
    if not isinstance(hotspot, dict):
        return hotspot

    enriched = dict(hotspot)
    try:
        # Lazy imports to avoid circular imports at module load time.
        from .prediction_service import (
            calculate_feature_contribution,
            detect_main_drivers,
            predict_heat_risk,
        )
        from .recommendation_service import (
            estimate_expected_reduction,
            recommend_action,
        )
        from ..utils.validators import categorize_heat, priority_from_category

        if not enriched.get("heat_risk_score"):
            prediction = predict_heat_risk(enriched)
            enriched["heat_risk_score"] = prediction["heat_risk_score"]
            enriched.setdefault("hotspot_category", prediction["hotspot_category"])
            enriched.setdefault("main_drivers", prediction["main_drivers"])
            enriched.setdefault("feature_contribution", prediction["feature_contribution"])
            enriched.setdefault("recommended_action", prediction["recommended_action"])

        score = float(enriched.get("heat_risk_score", 0) or 0)
        enriched.setdefault("hotspot_category", categorize_heat(score))
        if not enriched.get("main_drivers"):
            enriched["main_drivers"] = detect_main_drivers(enriched)
        if not enriched.get("feature_contribution"):
            enriched["feature_contribution"] = calculate_feature_contribution(enriched)
        if not enriched.get("recommended_action"):
            action, _ = recommend_action(enriched, score)
            enriched["recommended_action"] = action
        if not enriched.get("expected_temp_reduction"):
            enriched["expected_temp_reduction"] = estimate_expected_reduction(enriched)
        if not enriched.get("priority_level"):
            enriched["priority_level"] = priority_from_category(
                enriched.get("hotspot_category", "Moderate")
            )
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to enrich hotspot, returning as-is: %s", exc)
    return enriched


def load_hotspots(city: Optional[str] = None) -> List[dict]:
    """Load hotspots for a city and enrich any that lack prediction fields."""
    hotspots = get_hotspots(city)
    return [enrich_hotspot_data(h) for h in hotspots]
