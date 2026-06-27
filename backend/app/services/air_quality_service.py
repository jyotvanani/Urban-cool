"""Real-time Air Quality Index from data.gov.in, with safe fallback.

Fetches per-station pollutant readings for a city, aggregates them, and
computes a CPCB-style AQI (max of pollutant sub-indices). If the API is
unavailable or no key is set, returns realistic demo AQI data so the app
never breaks.
"""

import time
from typing import Optional

import requests

from ..config import settings
from ..utils.logger import logger
from ..utils.validators import normalize_city

AQI_RESOURCE = "3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69"
AQI_URL = f"https://api.data.gov.in/resource/{AQI_RESOURCE}"

# City id -> the city name used by data.gov.in.
CITY_NAMES = {
    "ahmedabad": "Ahmedabad",
    "surat": "Surat",
}

# CPCB sub-index breakpoints: pollutant -> list of (Clow, Chigh, Ilow, Ihigh).
_BREAKPOINTS = {
    "PM2.5": [(0, 30, 0, 50), (31, 60, 51, 100), (61, 90, 101, 200),
              (91, 120, 201, 300), (121, 250, 301, 400), (251, 500, 401, 500)],
    "PM10": [(0, 50, 0, 50), (51, 100, 51, 100), (101, 250, 101, 200),
             (251, 350, 201, 300), (351, 430, 301, 400), (431, 600, 401, 500)],
    "NO2": [(0, 40, 0, 50), (41, 80, 51, 100), (81, 180, 101, 200),
            (181, 280, 201, 300), (281, 400, 301, 400), (401, 600, 401, 500)],
    "SO2": [(0, 40, 0, 50), (41, 80, 51, 100), (81, 380, 101, 200),
            (381, 800, 201, 300), (801, 1600, 301, 400), (1601, 2000, 401, 500)],
    "CO": [(0, 1, 0, 50), (1.1, 2, 51, 100), (2.1, 10, 101, 200),
           (10.1, 17, 201, 300), (17.1, 34, 301, 400), (34.1, 50, 401, 500)],
    "OZONE": [(0, 50, 0, 50), (51, 100, 51, 100), (101, 168, 101, 200),
              (169, 208, 201, 300), (209, 748, 301, 400), (749, 1000, 401, 500)],
}

_CACHE: dict = {}
_TTL_SECONDS = 1800  # 30 minutes


def _category(aqi: float) -> str:
    if aqi <= 50:
        return "Good"
    if aqi <= 100:
        return "Satisfactory"
    if aqi <= 200:
        return "Moderate"
    if aqi <= 300:
        return "Poor"
    if aqi <= 400:
        return "Very Poor"
    return "Severe"


def _sub_index(pollutant: str, conc: float) -> Optional[float]:
    table = _BREAKPOINTS.get(pollutant)
    if not table or conc is None:
        return None
    for clow, chigh, ilow, ihigh in table:
        if clow <= conc <= chigh:
            # Linear interpolation within the band.
            return round(((ihigh - ilow) / (chigh - clow)) * (conc - clow) + ilow)
    # Above the top band -> cap at 500.
    return 500 if conc > table[-1][1] else None


def _to_float(value) -> Optional[float]:
    try:
        if value in (None, "", "NA"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _demo_air_quality(city: str) -> dict:
    """Realistic fallback AQI data."""
    presets = {
        "ahmedabad": {"aqi": 142, "dominant": "PM2.5",
                      "pollutants": {"PM2.5": 54, "PM10": 61, "NO2": 22, "SO2": 19, "OZONE": 26, "CO": 18}},
        "surat": {"aqi": 118, "dominant": "PM10",
                  "pollutants": {"PM2.5": 41, "PM10": 88, "NO2": 18, "SO2": 15, "OZONE": 22, "CO": 12}},
    }
    p = presets.get(city, presets["ahmedabad"])
    return {
        "city": CITY_NAMES.get(city, city.title()),
        "aqi": p["aqi"],
        "category": _category(p["aqi"]),
        "dominant_pollutant": p["dominant"],
        "pollutants": p["pollutants"],
        "stations_count": 3,
        "source": "demo",
        "last_update": None,
    }


def _fetch_records(city_name: str) -> list:
    """Fetch raw records from data.gov.in for a city. Returns [] on failure."""
    if not settings.DATA_GOV_API_KEY:
        return []
    params = {
        "api-key": settings.DATA_GOV_API_KEY,
        "format": "json",
        "limit": 200,
        "filters[city]": city_name,
    }
    try:
        resp = requests.get(AQI_URL, params=params, timeout=12)
        resp.raise_for_status()
        return resp.json().get("records", []) or []
    except requests.RequestException as exc:
        logger.warning("Air quality API failed for %s: %s", city_name, exc)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Air quality API error for %s: %s", city_name, exc)
    return []


def get_air_quality(city: Optional[str]) -> dict:
    """Return aggregated AQI for a city, with demo fallback. Never raises."""
    city_slug = normalize_city(city) or "ahmedabad"
    if city_slug not in CITY_NAMES:
        city_slug = "ahmedabad"

    cached = _CACHE.get(city_slug)
    if cached and (time.time() - cached["ts"]) < _TTL_SECONDS:
        return cached["data"]

    city_name = CITY_NAMES[city_slug]
    records = _fetch_records(city_name)

    if not records:
        data = _demo_air_quality(city_slug)
        _CACHE[city_slug] = {"ts": time.time(), "data": data}
        return data

    # Aggregate average concentration per pollutant across stations.
    sums, counts, last_update = {}, {}, None
    for rec in records:
        pol = (rec.get("pollutant_id") or "").upper()
        val = _to_float(rec.get("avg_value") or rec.get("pollutant_avg"))
        if pol and val is not None:
            sums[pol] = sums.get(pol, 0.0) + val
            counts[pol] = counts.get(pol, 0) + 1
        last_update = rec.get("last_update") or last_update

    pollutants = {p: round(sums[p] / counts[p]) for p in sums if counts[p]}

    # AQI = max of available pollutant sub-indices (CPCB method).
    sub = {p: _sub_index(p, v) for p, v in pollutants.items()}
    sub = {p: s for p, s in sub.items() if s is not None}
    if sub:
        dominant = max(sub, key=sub.get)
        aqi = int(sub[dominant])
    else:
        return _demo_air_quality(city_slug)

    data = {
        "city": city_name,
        "aqi": aqi,
        "category": _category(aqi),
        "dominant_pollutant": dominant,
        "pollutants": pollutants,
        "stations_count": len({r.get("station") for r in records if r.get("station")}),
        "source": "data.gov.in",
        "last_update": last_update,
    }
    _CACHE[city_slug] = {"ts": time.time(), "data": data}
    return data
