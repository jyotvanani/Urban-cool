"""Application configuration loaded from environment variables.

Uses python-dotenv to read a local .env file when present. All values have
safe defaults so the backend runs even without a .env file.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the backend root if it exists (non-fatal if missing).
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")


def _as_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    """Central settings object used across the app."""

    APP_NAME: str = os.getenv("APP_NAME", "UrbanCool AI")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    USE_LIVE_API: bool = _as_bool(os.getenv("USE_LIVE_API", "false"))
    DATA_MODE: str = os.getenv("DATA_MODE", "demo")

    # Google Earth Engine (optional satellite data source).
    USE_GEE: bool = _as_bool(os.getenv("USE_GEE", "false"))
    GEE_PROJECT: str = os.getenv("GEE_PROJECT", "")
    GEE_SERVICE_ACCOUNT: str = os.getenv("GEE_SERVICE_ACCOUNT", "")
    GEE_KEY_FILE: str = os.getenv("GEE_KEY_FILE", "")

    # data.gov.in Real-time Air Quality Index API.
    DATA_GOV_API_KEY: str = os.getenv("DATA_GOV_API_KEY", "")

    # Important filesystem locations.
    BASE_DIR: Path = BASE_DIR
    APP_DIR: Path = BASE_DIR / "app"
    DATA_DIR: Path = BASE_DIR / "app" / "data"
    ML_DIR: Path = BASE_DIR / "ml"
    REPORTS_DIR: Path = BASE_DIR / "reports"
    MODEL_PATH: Path = BASE_DIR / "ml" / "model.joblib"
    SCALER_PATH: Path = BASE_DIR / "ml" / "scaler.joblib"

    @property
    def gee_key_path(self) -> Path:
        """Absolute path to the GEE service-account key file."""
        key = self.GEE_KEY_FILE
        if not key:
            return self.BASE_DIR / "secrets" / "gee-key.json"
        p = Path(key)
        return p if p.is_absolute() else self.BASE_DIR / p

    @property
    def cors_origins(self) -> list:
        """Origins allowed to call the API."""
        origins = {
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        }
        if self.FRONTEND_URL:
            origins.add(self.FRONTEND_URL)
        return sorted(origins)


settings = Settings()

# Make sure the reports directory always exists.
settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
