"""Transparent prototype recharge-suitability scoring engine.

Weights sum to 100 and are configurable per-request (POST /api/recharge/calculate
accepts an optional `weights` override). Clearly labelled everywhere as a
"Prototype Decision-Support Estimate" - never a guarantee.
"""
from __future__ import annotations
import math
from typing import Dict, Tuple

DEFAULT_WEIGHTS: Dict[str, float] = {
    "rainfall": 20.0,
    "slope": 15.0,
    "soil_moisture": 15.0,
    "land_use": 10.0,
    "geology": 15.0,
    "distance_to_stream": 10.0,
    "lineament_density": 10.0,
    "groundwater_depth": 5.0,
}

LAND_USE_SCORES = {
    "forest": 0.90, "agroforestry": 0.75, "agriculture": 0.55,
    "grassland": 0.50, "settlement": 0.25, "barren": 0.20, "unknown": 0.40,
}
GEOLOGY_SCORES = {
    "fractured_rock": 0.90, "weathered_granite": 0.75, "sandstone": 0.65,
    "shale": 0.45, "clay": 0.25, "unknown": 0.40,
}


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def factor_scores(
    rainfall: float = 1200, slope: float = 12, soil_moisture: float = 0.7,
    land_use: str = "forest", geology: str = "fractured_rock",
    distance_to_stream: float = 250, lineament_density: float = 0.8,
    groundwater_depth: float = 15, weights: Dict[str, float] | None = None,
) -> Tuple[Dict[str, float], Dict[str, float]]:
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        for k, v in weights.items():
            if k in w:
                try:
                    w[k] = max(0.0, float(v))
                except (TypeError, ValueError):
                    pass
    total = sum(w.values()) or 1.0
    w = {k: v / total * 100.0 for k, v in w.items()}  # renormalise

    lu = (land_use or "unknown").lower()
    geo = (geology or "unknown").lower()
    n_rain = _clip01((rainfall - 700) / 900.0)
    n_slope = 1.0 - _clip01((slope - 2) / 33.0)
    n_sm = _clip01(soil_moisture)
    n_lu = LAND_USE_SCORES.get(lu, 0.40)
    n_geo = GEOLOGY_SCORES.get(geo, 0.40)
    n_dist = math.exp(-max(0.0, distance_to_stream) / 600.0)
    n_lin = _clip01(lineament_density)
    n_depth = 1.0 - _clip01((groundwater_depth - 3) / 47.0)

    factors = {
        "rainfall": round(n_rain * w["rainfall"], 2),
        "slope": round(n_slope * w["slope"], 2),
        "soil_moisture": round(n_sm * w["soil_moisture"], 2),
        "land_use": round(n_lu * w["land_use"], 2),
        "geology": round(n_geo * w["geology"], 2),
        "distance_to_stream": round(n_dist * w["distance_to_stream"], 2),
        "lineament_density": round(n_lin * w["lineament_density"], 2),
        "groundwater_depth": round(n_depth * w["groundwater_depth"], 2),
    }
    return factors, w


def classify(score: float) -> str:
    if score >= 70:
        return "HIGH"
    if score >= 45:
        return "MEDIUM"
    return "LOW"


def confidence_for(score: float, land_use: str = "", geology: str = "") -> float:
    """Deterministic prototype confidence: higher away from class boundaries,
    slightly lower for unknown categories (data uncertainty)."""
    dist = abs(score - 50) / 50.0
    conf = 0.62 + 0.28 * dist
    if (land_use or "").lower() in ("unknown", ""):
        conf -= 0.06
    if (geology or "").lower() in ("unknown", ""):
        conf -= 0.06
    return round(max(0.55, min(0.95, conf)), 2)


def calculate(payload: dict) -> dict:
    factors, weights = factor_scores(
        rainfall=float(payload.get("rainfall", 1200) or 0),
        slope=float(payload.get("slope", 12) or 0),
        soil_moisture=float(payload.get("soil_moisture", 0.5) or 0),
        land_use=str(payload.get("land_use", "unknown")),
        geology=str(payload.get("geology", "unknown")),
        distance_to_stream=float(payload.get("distance_to_stream", 300) or 0),
        lineament_density=float(payload.get("lineament_density", 0.5) or 0),
        groundwater_depth=float(payload.get("groundwater_depth", 15) or 0),
        weights=payload.get("weights"),
    )
    score = round(max(0.0, min(100.0, sum(factors.values()))), 1)
    return {
        "score": score,
        "class": classify(score),
        "confidence": confidence_for(score, str(payload.get("land_use", "")), str(payload.get("geology", ""))),
        "factors": factors,
        "weights": {k: round(v, 2) for k, v in weights.items()},
        "disclaimer": "Prototype Decision-Support Estimate — does not guarantee groundwater recharge. Requires field validation.",
    }
