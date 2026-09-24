"""Pydantic request/response schemas. Never expose raw tracebacks."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RechargeCalculateRequest(BaseModel):
    rainfall: float = Field(default=1200, ge=0, le=4000)
    slope: float = Field(default=12, ge=0, le=60)
    soil_moisture: float = Field(default=0.7, ge=0, le=1)
    land_use: str = Field(default="forest")
    geology: str = Field(default="fractured_rock")
    distance_to_stream: float = Field(default=250, ge=0, le=5000)
    lineament_density: float = Field(default=0.8, ge=0, le=1)
    groundwater_depth: float = Field(default=15, ge=0, le=200)
    weights: Optional[Dict[str, float]] = None


class MLPredictRequest(BaseModel):
    elevation_m: float = 600
    slope_deg: float = 12
    annual_rainfall_mm: float = 1200
    soil_moisture_index: float = 0.6
    land_use: str = "forest"
    geology: str = "fractured_rock"
    distance_to_stream_m: float = 250
    lineament_density_index: float = 0.6
    groundwater_depth_m: float = 15


class InterventionSimulateRequest(BaseModel):
    intervention_type: str = "recharge_trench"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    spring_id: Optional[str] = None
    quantity: float = Field(default=1, gt=0, le=500)
    base_score: Optional[float] = None


# ---- Feature 1: groundwater early warning ----
class ThresholdOverride(BaseModel):
    decline_short_slope: Optional[float] = None
    decline_medium_slope: Optional[float] = None
    strong_decline_slope: Optional[float] = None
    below_baseline_m: Optional[float] = None
    rain_deficit_pct: Optional[float] = None
    persistent_days: Optional[float] = None
    warn_score: Optional[float] = None
    warning_score: Optional[float] = None
    critical_score: Optional[float] = None


class ForecastRequest(BaseModel):
    horizon_days: int = Field(default=30, ge=7, le=90)


# ---- Feature 2: community reporting ----
class CommunityReportCreate(BaseModel):
    problem_type: str = "other"
    description: str = Field(default="", max_length=1000)
    village: str = Field(default="", max_length=200)
    latitude: float = Field(default=0, ge=-90, le=90)
    longitude: float = Field(default=0, ge=-180, le=180)
    severity: str = "MEDIUM"


class CommunityReportStatusUpdate(BaseModel):
    status: str


class ChatMessage(BaseModel):
    session: Dict[str, Any] = Field(default_factory=dict)
    message: str = Field(default="", max_length=500)
