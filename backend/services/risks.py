"""Automatic risk-flag generator (transparent rule set)."""
from __future__ import annotations
from typing import Dict, List


def generate_risk_flags(spring: Dict) -> List[Dict]:
    flags: List[Dict] = []

    def add(code: str, level: str, message: str):
        flags.append({"code": code, "level": level, "message": message})

    slope = float(spring.get("slope_deg", 0) or 0)
    rain = float(spring.get("annual_rainfall_mm", 0) or 0)
    score = float(spring.get("recharge_suitability", 50) or 50)
    depth = float(spring.get("groundwater_depth_m", 0) or 0)
    geo = str(spring.get("geology", "")).lower()
    seas = str(spring.get("seasonality", "")).lower()
    lu = str(spring.get("land_use", "")).lower()

    add("slope", "warn" if slope > 25 else "good",
        "High slope — runoff risk" if slope > 25 else f"Slope {slope:.0f}° within workable range")
    add("rainfall", "warn" if rain < 1000 else "good",
        "Low rainfall for recharge" if rain < 1000 else "Adequate rainfall")
    add("recharge", "warn" if score < 45 else "good",
        "Low recharge suitability" if score < 45 else f"Recharge suitability {score:.0f}")
    add("gw_depth", "warn" if depth > 30 else "good",
        "High groundwater depth" if depth > 30 else "Groundwater depth workable")
    add("runoff", "warn" if (slope > 25 and lu in ("barren", "settlement")) else "good",
        "High runoff potential" if (slope > 25 and lu in ("barren", "settlement")) else "Runoff manageable")
    add("geology", "warn" if geo in ("clay", "shale") else "good",
        "Poor geological suitability" if geo in ("clay", "shale") else "Favourable geology")
    add("seasonality", "warn" if seas == "seasonal" else "good",
        "Seasonal spring — dries up part of year" if seas == "seasonal" else "Perennial spring")
    if lu in ("unknown", "") or geo in ("unknown", ""):
        add("data", "warn", "Data uncertainty — unknown category present")
    else:
        add("data", "good", "Input categories recognised")
    return flags
