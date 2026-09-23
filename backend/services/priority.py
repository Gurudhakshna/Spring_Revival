"""Transparent priority algorithm (formula is public, returned in every response).

Priority = 40% recharge suitability + 20% spring vulnerability
         + 15% population dependency + 15% intervention feasibility
         + 10% water stress, all normalised to 0-100.
"""
from __future__ import annotations
from typing import Dict, List


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def compute_priority(spring: Dict, village_pop: int = 800,
                     max_pop: int = 2200) -> Dict:
    score = float(spring.get("recharge_suitability", 50) or 50)
    recharge_c = _clip01(score / 100.0)

    seasonal = str(spring.get("seasonality", "")).lower() == "seasonal"
    discharge = float(spring.get("discharge_lpm", 15) or 15)
    vuln = (0.6 if seasonal else 0.25) + _clip01(1 - discharge / 40.0) * 0.4
    vuln = _clip01(vuln)

    pop_dep = _clip01((village_pop or 0) / (max_pop or 2200))

    slope = float(spring.get("slope_deg", 12) or 12)
    dist = float(spring.get("distance_to_stream_m", 300) or 300)
    geo = str(spring.get("geology", "")).lower()
    geo_ok = {"fractured_rock": 1.0, "weathered_granite": 0.85, "sandstone": 0.7,
              "shale": 0.5, "clay": 0.3}.get(geo, 0.5)
    feas = _clip01((1 - _clip01((slope - 2) / 33.0)) * 0.5
                   + (1 - _clip01(dist / 1200.0)) * 0.2 + geo_ok * 0.3)

    depth = float(spring.get("groundwater_depth_m", 15) or 15)
    rain = float(spring.get("annual_rainfall_mm", 1200) or 1200)
    stress = _clip01(_clip01((depth - 5) / 35.0) * 0.6
                     + _clip01((1200 - rain) / 500.0) * 0.4)

    components = {
        "recharge_suitability": round(recharge_c * 100, 1),
        "spring_vulnerability": round(vuln * 100, 1),
        "population_dependency": round(pop_dep * 100, 1),
        "intervention_feasibility": round(feas * 100, 1),
        "water_stress": round(stress * 100, 1),
    }
    total = round(recharge_c * 40 + vuln * 20 + pop_dep * 15 + feas * 15 + stress * 10, 1)
    pclass = "HIGH" if total >= 65 else ("MEDIUM" if total >= 40 else "LOW")

    reasons: List[str] = []
    if score >= 70:
        reasons.append("High recharge potential")
    elif score >= 45:
        reasons.append("Moderate recharge potential")
    else:
        reasons.append("Low recharge potential — needs investigation")
    if dist <= 400:
        reasons.append("Near existing stream/spring source")
    if slope <= 15:
        reasons.append("Moderate slope — intervention feasible")
    elif slope > 25:
        reasons.append("Steep slope — runoff risk, needs contour measures")
    if geo in ("fractured_rock", "weathered_granite"):
        reasons.append("Good geological conditions for recharge")
    if seasonal:
        reasons.append("Seasonal spring — vulnerable, priority for revival")
    if village_pop >= 1200:
        reasons.append("High community dependency")
    if not reasons:
        reasons.append("Prototype estimate — field validation required")

    return {
        "spring_id": spring.get("spring_id"),
        "priority_score": total,
        "priority_class": pclass,
        "components": components,
        "formula": "0.40*recharge + 0.20*vulnerability + 0.15*population + 0.15*feasibility + 0.10*water_stress",
        "why": reasons,
        "disclaimer": "Prototype Decision-Support Estimate — requires field validation.",
    }
