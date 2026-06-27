"""Precompute Google Earth Engine indices into the hotspot JSON files.

Run from the backend/ directory:
    python ml/fetch_gee_data.py --city ahmedabad

For each zone it fetches NDVI / NDBI / NDWI / LST from GEE and writes them into
app/data/hotspots_<city>.json, adding the columns ``ndvi_sentinel2`` and
``lst_landsat8_celsius`` and refreshing the core fields used by the model.

Safe by design: if GEE is not configured or unavailable, the data files are
left unchanged and a readable message is printed.
"""

import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config import settings  # noqa: E402
from app.services import gee_service  # noqa: E402

CITY_FILES = {
    "ahmedabad": "hotspots_ahmedabad.json",
    "surat": "hotspots_surat.json",
}


def process_city(city: str) -> int:
    city = city.strip().lower()
    filename = CITY_FILES.get(city)
    if not filename:
        print(f"Unknown city '{city}'. Known: {', '.join(CITY_FILES)}")
        return 1

    path = settings.DATA_DIR / filename
    if not path.exists():
        print(f"Data file not found: {path}")
        return 1

    if not gee_service.is_configured():
        print("GEE is not configured. Set USE_GEE=true, GEE_PROJECT, "
              "GEE_SERVICE_ACCOUNT and GEE_KEY_FILE in backend/.env.")
        print("No changes made; the app keeps using existing demo data.")
        return 1

    if not gee_service.initialize():
        print("Could not initialize Earth Engine. Check authentication and "
              "project registration. No changes made.")
        return 1

    with open(path, "r", encoding="utf-8") as fh:
        zones = json.load(fh)

    updated = 0
    for zone in zones:
        name = zone.get("zone_name", zone.get("zone_id", "?"))
        indices = gee_service.fetch_indices(zone.get("latitude"), zone.get("longitude"))
        if not indices:
            print(f"  {name:<14} -> no GEE data (kept existing values)")
            continue

        # Add explicit satellite columns.
        if "ndvi_sentinel2" in indices:
            zone["ndvi_sentinel2"] = indices["ndvi_sentinel2"]
            zone["ndvi"] = indices["ndvi_sentinel2"]
        if "lst_landsat8_celsius" in indices:
            zone["lst_landsat8_celsius"] = indices["lst_landsat8_celsius"]
            zone["lst_temperature"] = indices["lst_landsat8_celsius"]
        if "ndbi" in indices:
            zone["ndbi"] = indices["ndbi"]
        if "ndwi" in indices:
            zone["ndwi"] = indices["ndwi"]
        zone["data_source"] = "gee"
        updated += 1
        print(f"  {name:<14} -> {indices}")

    if updated:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(zones, fh, indent=2)
        print(f"\nUpdated {updated}/{len(zones)} zones in {path}")
    else:
        print("\nNo zones updated; file left unchanged.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch GEE indices into hotspot data.")
    parser.add_argument("--city", default="ahmedabad", help="City id (ahmedabad or surat)")
    args = parser.parse_args()
    code = process_city(args.city)
    sys.exit(code)


if __name__ == "__main__":
    main()
