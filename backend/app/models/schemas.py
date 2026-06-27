"""Pydantic request/response schemas for UrbanCool AI."""

from typing import List, Optional

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Core domain models
# --------------------------------------------------------------------------- #
class City(BaseModel):
    city_id: str
    name: str
    state: str
    country: str
    center_lat: float
    center_lng: float


class Hotspot(BaseModel):
    zone_id: str
    zone_name: str
    city: str
    latitude: float
    longitude: float
    lst_temperature: float
    ndvi: float
    ndbi: float
    ndwi: float
    built_up_density: float
    green_cover_percentage: float
    water_body_distance_km: float
    air_temperature: float
    humidity: float
    wind_speed: float
    heat_risk_score: float
    hotspot_category: str
    main_drivers: List[str]
    recommended_action: str
    expected_temp_reduction: float
    priority_level: str


# --------------------------------------------------------------------------- #
# Prediction
# --------------------------------------------------------------------------- #
class PredictRequest(BaseModel):
    lst_temperature: float = Field(..., example=42.5)
    ndvi: float = Field(..., example=0.18)
    ndbi: float = Field(..., example=0.74)
    ndwi: float = Field(..., example=0.08)
    built_up_density: float = Field(..., example=0.82)
    green_cover_percentage: float = Field(..., example=12)
    water_body_distance_km: float = Field(..., example=2.5)
    air_temperature: float = Field(..., example=39)
    humidity: float = Field(..., example=38)
    wind_speed: float = Field(..., example=7)


class PredictResponse(BaseModel):
    heat_risk_score: float
    hotspot_category: str
    confidence: float
    main_drivers: List[str]
    recommended_action: str
    model_used: str


# --------------------------------------------------------------------------- #
# Simulation
# --------------------------------------------------------------------------- #
class SimulateRequest(BaseModel):
    zone_id: str = Field(..., example="ahm_zone_01")
    tree_cover_increase: float = Field(0, example=25)
    cool_roof_percentage: float = Field(0, example=40)
    green_roof_percentage: float = Field(0, example=10)
    water_body_improvement: float = Field(0, example=5)
    high_albedo_surface: float = Field(0, example=20)


class SimulateResponse(BaseModel):
    zone_id: str
    current_lst: float
    estimated_new_lst: float
    estimated_temp_reduction: float
    impact_score: float
    cost_level: str
    feasibility: str
    recommended_strategy: str
    explanation: str


# --------------------------------------------------------------------------- #
# Generic envelope models (for Swagger documentation)
# --------------------------------------------------------------------------- #
class StandardResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: Optional[str] = None
    error: Optional[str] = None
    fallback_used: Optional[bool] = None


# --------------------------------------------------------------------------- #
# Spec-named models (ML engine I/O)
# --------------------------------------------------------------------------- #
class PredictionInput(BaseModel):
    lst_temperature: float = Field(42.5, ge=0, le=70)
    ndvi: float = Field(0.18, ge=-1, le=1)
    ndbi: float = Field(0.74, ge=-1, le=1)
    ndwi: float = Field(0.08, ge=-1, le=1)
    built_up_density: float = Field(0.82, ge=0, le=1)
    green_cover_percentage: float = Field(12, ge=0, le=100)
    water_body_distance_km: float = Field(2.5, ge=0, le=100)
    air_temperature: float = Field(39, ge=0, le=60)
    humidity: float = Field(38, ge=0, le=100)
    wind_speed: float = Field(7, ge=0, le=50)


class PredictionOutput(BaseModel):
    heat_risk_score: float
    hotspot_category: str
    confidence: float
    main_drivers: List[str]
    feature_contribution: dict
    recommended_action: str
    model_used: str


class SimulationInput(BaseModel):
    zone_id: str = Field(..., example="ahm_zone_01")
    tree_cover_increase: float = Field(0, ge=0, le=100)
    cool_roof_percentage: float = Field(0, ge=0, le=100)
    green_roof_percentage: float = Field(0, ge=0, le=100)
    water_body_improvement: float = Field(0, ge=0, le=100)
    high_albedo_surface: float = Field(0, ge=0, le=100)


class SimulationOutput(BaseModel):
    zone_id: str
    current_lst: float
    estimated_new_lst: float
    estimated_temp_reduction: float
    impact_score: float
    cost_level: str
    feasibility: str
    recommended_strategy: str
    explanation: str


class HotspotData(BaseModel):
    zone_id: str
    zone_name: str
    city: str
    latitude: float
    longitude: float
    lst_temperature: float
    ndvi: float
    ndbi: float
    ndwi: float
    built_up_density: float
    green_cover_percentage: float
    water_body_distance_km: float
    air_temperature: float
    humidity: float
    wind_speed: float
    heat_risk_score: float
    hotspot_category: str
    main_drivers: List[str]
    recommended_action: str
    expected_temp_reduction: float
    priority_level: str
    feature_contribution: Optional[dict] = None


class ReportData(BaseModel):
    zone_summary: dict
    heat_condition: dict
    main_causes: List[str]
    recommended_actions: str
    expected_temperature_reduction: float
    priority_level: str
    implementation_suggestions: List[str]
    generated_at: Optional[str] = None
