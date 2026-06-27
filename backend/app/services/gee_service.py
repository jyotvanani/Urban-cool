"""Google Earth Engine integration (optional satellite data source).

Computes NDVI, NDBI, NDWI and land surface temperature (LST) for a point from
Sentinel-2 and Landsat 8/9. All imports are lazy and every call is guarded, so
importing this module never breaks the app even when ``earthengine-api`` is not
installed or GEE is not configured.

Enable by setting in .env:
    USE_GEE=true
    GEE_PROJECT=your-cloud-project-id
    GEE_SERVICE_ACCOUNT=svc@project.iam.gserviceaccount.com
    GEE_KEY_FILE=secrets/gee-key.json
"""

from typing import Optional

from ..config import settings
from ..utils.logger import logger

# Module state for a single lazy initialization.
_initialized = False
_init_failed = False


def is_configured() -> bool:
    """True if GEE is enabled and usable.

    Two auth modes are accepted:
      - Service account: GEE_SERVICE_ACCOUNT set + key file present.
      - Interactive: no service account set (uses `earthengine authenticate`).
    """
    if not (settings.USE_GEE and settings.GEE_PROJECT):
        return False
    if settings.GEE_SERVICE_ACCOUNT:
        return settings.gee_key_path.exists()
    return True  # interactive credentials


def initialize() -> bool:
    """Initialize Earth Engine once. Returns True on success, never raises."""
    global _initialized, _init_failed
    if _initialized:
        return True
    if _init_failed:
        return False

    if not settings.USE_GEE:
        _init_failed = True
        return False

    try:
        import ee  # lazy import

        if settings.GEE_SERVICE_ACCOUNT and settings.gee_key_path.exists():
            credentials = ee.ServiceAccountCredentials(
                settings.GEE_SERVICE_ACCOUNT, str(settings.gee_key_path)
            )
            ee.Initialize(credentials, project=settings.GEE_PROJECT or None)
        else:
            # Falls back to interactive credentials saved by `earthengine authenticate`.
            ee.Initialize(project=settings.GEE_PROJECT or None)

        _initialized = True
        logger.info("Google Earth Engine initialized (project=%s)", settings.GEE_PROJECT)
        return True
    except Exception as exc:  # pragma: no cover - depends on external auth
        _init_failed = True
        logger.warning("GEE initialization failed, using fallback data: %s", exc)
        return False


def fetch_indices(
    lat: float,
    lon: float,
    buffer_m: int = 500,
    months_back: int = 6,
) -> Optional[dict]:
    """Return satellite indices for a point, or None if GEE is unavailable.

    Output keys:
        ndvi_sentinel2, ndbi, ndwi, lst_landsat8_celsius
    """
    if lat is None or lon is None:
        return None
    if not initialize():
        return None

    try:
        import datetime as _dt

        import ee

        point = ee.Geometry.Point([float(lon), float(lat)])
        region = point.buffer(buffer_m)

        end = _dt.date.today()
        start = end - _dt.timedelta(days=months_back * 30)
        start_s, end_s = start.isoformat(), end.isoformat()

        result = {}

        # --- Sentinel-2: NDVI, NDBI, NDWI (cloud-filtered median) ---
        s2 = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(region)
            .filterDate(start_s, end_s)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
        )
        if s2.size().getInfo() > 0:
            img = s2.median()
            ndvi = img.normalizedDifference(["B8", "B4"]).rename("ndvi")     # (NIR-Red)
            ndbi = img.normalizedDifference(["B11", "B8"]).rename("ndbi")    # (SWIR-NIR)
            ndwi = img.normalizedDifference(["B3", "B8"]).rename("ndwi")     # (Green-NIR)
            stats = (
                ndvi.addBands(ndbi).addBands(ndwi)
                .reduceRegion(
                    reducer=ee.Reducer.mean(), geometry=region, scale=20, maxPixels=1e9
                )
                .getInfo()
            )
            if stats.get("ndvi") is not None:
                result["ndvi_sentinel2"] = round(float(stats["ndvi"]), 3)
            if stats.get("ndbi") is not None:
                result["ndbi"] = round(float(stats["ndbi"]), 3)
            if stats.get("ndwi") is not None:
                result["ndwi"] = round(float(stats["ndwi"]), 3)

        # --- Landsat 8/9 Collection 2 L2: LST in Celsius ---
        landsat = (
            ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
            .merge(ee.ImageCollection("LANDSAT/LC09/C02/T1_L2"))
            .filterBounds(region)
            .filterDate(start_s, end_s)
            .filter(ee.Filter.lt("CLOUD_COVER", 30))
        )
        if landsat.size().getInfo() > 0:
            lst_img = landsat.median().select("ST_B10")
            # Collection 2 scaling: DN * 0.00341802 + 149.0 (Kelvin) -> Celsius.
            lst_c = lst_img.multiply(0.00341802).add(149.0).subtract(273.15).rename("lst")
            lst_stats = lst_c.reduceRegion(
                reducer=ee.Reducer.mean(), geometry=region, scale=30, maxPixels=1e9
            ).getInfo()
            if lst_stats.get("lst") is not None:
                result["lst_landsat8_celsius"] = round(float(lst_stats["lst"]), 2)

        return result or None
    except Exception as exc:  # pragma: no cover - depends on external service
        logger.warning("GEE fetch_indices failed (%s,%s): %s", lat, lon, exc)
        return None
