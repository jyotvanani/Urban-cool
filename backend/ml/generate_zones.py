"""Generate real hotspot zones for a city from Google Earth Engine.

Default mode uses a curated list of real neighbourhoods: each name is
forward-geocoded to its true coordinates (OpenStreetMap), GEE NDVI/NDBI/NDWI/LST
are sampled there, and the zone is scored. This guarantees real names AND real
locations (no regular grid).

Run from backend/:
    python ml/generate_zones.py --city surat
    python ml/generate_zones.py --city ahmedabad

Safe: if GEE is unavailable, it exits without changing data.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config import settings  # noqa: E402
from app.services import gee_service  # noqa: E402
from app.services.prediction_service import (  # noqa: E402
    calculate_feature_contribution,
    detect_main_drivers,
    predict_heat_risk,
)
from app.services.recommendation_service import (  # noqa: E402
    estimate_expected_reduction,
    recommend_action,
)
from app.utils.validators import priority_from_category  # noqa: E402

CITY_FILES = {"ahmedabad": "hotspots_ahmedabad.json", "surat": "hotspots_surat.json"}
PREFIX = {"ahmedabad": "ahm", "surat": "sur"}

# Curated real neighbourhoods (forward-geocoded to true coordinates).
PLACES = {
    "ahmedabad": [
        "Maninagar", "Navrangpura", "Vastrapur", "Satellite", "Bopal",
        "Bodakdev", "Thaltej", "SG Highway", "Naroda", "Sabarmati",
        "Chandkheda", "Motera", "Gota", "Vejalpur", "Paldi",
        "Ellisbridge", "Naranpura", "Ghatlodia", "Memnagar", "Vastral",
        "Nikol", "Bapunagar", "Isanpur", "Vatva", "Ramol",
        "Odhav", "Sarkhej", "Jodhpur", "Ranip", "Chandlodia",
    ],
    "surat": [
        "Adajan", "Pal", "Vesu", "Piplod", "Athwa",
        "City Light", "Ghod Dod Road", "Rander", "Katargam", "Varachha",
        "Kapodra", "Nana Varachha", "Udhna", "Pandesara", "Limbayat",
        "Dindoli", "Sarthana", "Punagam", "Bhatar", "Majura Gate",
        "Bhestan", "Magob", "Palanpur", "Jahangirpura", "Althan",
        "Bamroli", "Godadara", "Parvat Patiya", "Bhatar Road", "Sagrampura",
    ],
}


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _load_city(city):
    cities = json.load(open(settings.DATA_DIR / "cities.json", encoding="utf-8"))
    for c in cities:
        if c.get("city_id") == city:
            return c
    return None


def _forward_geocode(query):
    """Forward geocode a place name to its real coordinates (lat, lon) or None."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json", "limit": 1}
    headers = {"User-Agent": "UrbanCoolAI/1.0 (hackathon project)"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        results = r.json() or []
        if results:
            return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception:
        pass
    return None


def _in_bbox(lat, lon, bbox, pad=0.04):
    min_lon, min_lat, max_lon, max_lat = bbox
    return (min_lat - pad) <= lat <= (max_lat + pad) and (min_lon - pad) <= lon <= (max_lon + pad)


def _derive_zone(lat, lon, indices):
    """Build the model-facing fields from real GEE indices."""
    ndvi = float(indices.get("ndvi_sentinel2", 0.2))
    lst = float(indices.get("lst_landsat8_celsius", 40.0))
    ndwi = float(indices.get("ndwi", -0.2))
    ndbi_real = float(indices.get("ndbi", 0.0))

    green = round(_clamp(ndvi / 0.6, 0, 1) * 100)
    built = round(_clamp(1 - ndvi / 0.5, 0, 1), 2)
    water_dist = round(_clamp(2.5 - ndwi * 5, 0.3, 5.0), 1)

    return {
        "latitude": round(lat, 5),
        "longitude": round(lon, 5),
        "lst_temperature": round(lst, 2),
        "ndvi": round(ndvi, 3),
        "ndbi": built,            # model-facing (0-1 range)
        "ndwi": round(ndwi, 3),
        "built_up_density": built,
        "green_cover_percentage": green,
        "water_body_distance_km": water_dist,
        "air_temperature": round(lst - 3.5, 1),
        "humidity": 45,
        "wind_speed": 7,
        "ndvi_sentinel2": round(ndvi, 3),
        "ndbi_sentinel2": round(ndbi_real, 3),
        "lst_landsat8_celsius": round(lst, 2),
        "data_source": "gee",
    }


def process_city(city):
    city = city.strip().lower()
    if city not in CITY_FILES:
        print(f"Unknown city '{city}'. Known: {', '.join(CITY_FILES)}")
        return 1

    cfg = _load_city(city)
    if not cfg:
        print(f"City '{city}' not found in cities.json")
        return 1

    if not gee_service.is_configured() or not gee_service.initialize():
        print("GEE not available. Set USE_GEE=true and authenticate first. No changes made.")
        return 1

    city_name = cfg.get("name", city.title())
    bbox = cfg.get("bbox")
    names = PLACES.get(city, [])
    print(f"Generating zones for {city_name} from {len(names)} real neighbourhoods...")

    zones = []
    used_coords = set()
    idx = 0
    for place in names:
        coords = _forward_geocode(f"{place}, {city_name}, Gujarat, India")
        time.sleep(1.1)  # respect Nominatim 1 req/sec policy
        if not coords:
            print(f"  --   {place:<22} (no geocode, skipped)")
            continue
        lat, lon = coords
        if bbox and not _in_bbox(lat, lon, bbox):
            print(f"  --   {place:<22} (outside city, skipped)")
            continue
        ckey = (round(lat, 3), round(lon, 3))
        if ckey in used_coords:
            continue
        used_coords.add(ckey)

        indices = gee_service.fetch_indices(lat, lon)
        if not indices or "lst_landsat8_celsius" not in indices or "ndvi_sentinel2" not in indices:
            print(f"  --   {place:<22} (no GEE data, skipped)")
            continue

        idx += 1
        zone = _derive_zone(lat, lon, indices)
        prediction = predict_heat_risk(zone)
        zone["zone_id"] = f"{PREFIX[city]}_zone_{idx:02d}"
        zone["zone_name"] = place
        zone["city"] = city_name
        zone["heat_risk_score"] = prediction["heat_risk_score"]
        zone["hotspot_category"] = prediction["hotspot_category"]
        zone["main_drivers"] = detect_main_drivers(zone)
        zone["feature_contribution"] = calculate_feature_contribution(zone)
        action, _ = recommend_action(zone, prediction["heat_risk_score"])
        zone["recommended_action"] = action
        zone["expected_temp_reduction"] = estimate_expected_reduction(zone)
        zone["priority_level"] = priority_from_category(zone["hotspot_category"])

        zones.append(zone)
        print(f"  [{idx:02d}] {place:<22} ({lat:.4f},{lon:.4f}) LST {zone['lst_temperature']:.1f}C "
              f"-> {zone['heat_risk_score']} ({zone['hotspot_category']})")

    if not zones:
        print("No zones generated. File left unchanged.")
        return 1

    path = settings.DATA_DIR / CITY_FILES[city]
    json.dump(zones, open(path, "w", encoding="utf-8"), indent=2)
    print(f"\nWrote {len(zones)} zones to {path}")
    return 0


def main():
    p = argparse.ArgumentParser(description="Generate GEE-based hotspot zones from real neighbourhoods.")
    p.add_argument("--city", default="ahmedabad")
    args = p.parse_args()
    sys.exit(process_city(args.city))


if __name__ == "__main__":
    main()
