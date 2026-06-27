"""UrbanCool AI FastAPI application entry point.

Workflow supported: Detect -> Explain -> Predict -> Simulate -> Recommend -> Report
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes import (
    air_quality,
    cities,
    cost,
    health,
    hotspots,
    optimize,
    prediction,
    reports,
    simulation,
    status,
)
from .utils.logger import logger

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI/ML decision-support backend for urban heat mitigation. "
        "Detect hotspots, explain heat drivers, predict risk, simulate "
        "cooling interventions, recommend strategies, and generate reports."
    ),
)

# CORS so the React frontend can connect.
# allow_origin_regex permits any localhost / 127.0.0.1 port, so the app works
# even when Vite falls back to a different port (5173, 5174, 5175, ...).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["root"])
def root():
    """Return project name, version, and status."""
    return {
        "project": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "message": "AI-powered urban heat mitigation backend is active",
    }


# Register all routers.
app.include_router(health.router)
app.include_router(status.router)
app.include_router(cities.router)
app.include_router(hotspots.router)
app.include_router(prediction.router)
app.include_router(simulation.router)
app.include_router(reports.router)
app.include_router(air_quality.router)
app.include_router(optimize.router)
app.include_router(cost.router)


@app.on_event("startup")
def on_startup():
    logger.info("%s v%s started in %s mode", settings.APP_NAME,
                settings.APP_VERSION, settings.ENVIRONMENT)
    logger.info("CORS origins: %s", settings.cors_origins)
