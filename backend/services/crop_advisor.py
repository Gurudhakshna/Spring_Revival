"""Water-Aware Crop Advisor — uses recharge + rainfall + soil to recommend crops.
Data: backend/data/crops.json (15 crops, ICAR prototype). Real IMD/soil integrated.
"""
from __future__ import annotations
import json, os
from typing import List, Dict, Any, Optional

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CROP_FILE = os.path.join(BASE, "crops.json")
_cache = None

def _load_crops():
    global _cache
    if _cache is not None:
        return _cache
    try:
        with open(CROP_FILE, encoding="utf-8") as f:
            _cache = json.load(f)
            return _cache
    except Exception:
        _cache = []
        return _cache

def _soil_status(district: Optional[str]) -> Dict[str,Any]:
    if not district:
        return {}
    try:
        from services import real_data as rd
        rows = rd.soil(district=district, limit=1)
        if rows:
            return rows[0]
    except: pass
    return {}

def recommend(recharge: float, rainfall: float, soil_moisture: float = 0.5, district: Optional[str]=None, early_risk: Optional[str]=None) -> Dict[str,Any]:
    crops = _load_crops()
    soil = _soil_status(district)
    rec, caution, avoid = [], [], []
    for c in crops:
        c = dict(c)
        water_min = float(c.get("water_min_mm") or 0)
        water_max = float(c.get("water_max_mm") or 3000)
        recharge_min = float(c.get("recharge_min") or 0)
        # Score logic
        water_ok = water_min <= rainfall <= water_max
        # Allow 20% buffer for caution
        water_close = (rainfall >= water_min*0.8 and rainfall <= water_max*1.2)
        recharge_ok = recharge >= recharge_min
        recharge_close = recharge >= recharge_min*0.85
        # Soil moisture check
        soil_ok = soil_moisture >= float(c.get("soil_moisture_min") or 0)
        # Early warning risk: if CRITICAL, avoid high water crops
        risk_high = (early_risk or "").upper() in ("CRITICAL","WARNING")
        if risk_high and water_min > 900:
            # Force avoid paddy/sugarcane if critical
            avoid.append({**c, "reason": f"Avoid — {early_risk} groundwater warning, needs {water_min}mm but risk high", "suitability":"AVOID"})
            continue
        if water_ok and recharge_ok and soil_ok:
            reason = f"Recommended — rainfall {rainfall:.0f}mm in {water_min}-{water_max}mm window, recharge {recharge:.0f}% >= {recharge_min}%"
            if soil and soil.get("zn") and float(soil.get("zn") or 0) < 50 and "Pulses" not in c["crop"]:
                reason += f" | Soil Zn {soil.get('zn')}% low — pulses fix nitrogen"
            rec.append({**c, "reason": reason, "suitability":"RECOMMENDED"})
        elif water_close and recharge_close:
            reason = f"Caution — rainfall {rainfall:.0f}mm near {water_min}-{water_max}mm or recharge {recharge:.0f}% near {recharge_min}%"
            caution.append({**c, "reason": reason, "suitability":"CAUTION"})
        else:
            # Why avoid
            why = []
            if rainfall < water_min: why.append(f"needs {water_min}mm but you have {rainfall:.0f}mm")
            if rainfall > water_max: why.append(f"needs <{water_max}mm but you have {rainfall:.0f}mm (excess)")
            if recharge < recharge_min: why.append(f"needs recharge {recharge_min}% but you have {recharge:.0f}%")
            if not soil_ok: why.append(f"needs soil moisture {c.get('soil_moisture_min')} but you have {soil_moisture}")
            reason = f"Avoid — {', '.join(why) if why else 'water mismatch'}"
            avoid.append({**c, "reason": reason, "suitability":"AVOID"})
    # Sort recommended by water gap (closest)
    rec.sort(key=lambda x: abs(rainfall - float(x.get("water_min_mm") or 0)))
    # Limit to top
    return {
        "input": {"recharge": recharge, "rainfall_mm": rainfall, "soil_moisture": soil_moisture, "district": district, "early_risk": early_risk, "soil": soil},
        "recommended": rec[:5],
        "caution": caution[:4],
        "avoid": avoid[:5],
        "counts": {"recommended": len(rec), "caution": len(caution), "avoid": len(avoid)},
        "disclaimer": "Prototype Decision-Support Estimate — consult local agri extension (KVK) before sowing."
    }

def for_spring(spring: Dict[str,Any], early_risk: Optional[str]=None) -> Dict[str,Any]:
    recharge = float(spring.get("recharge_suitability") or spring.get("recharge") or 50)
    rainfall = float(spring.get("annual_rainfall_mm") or 1000)
    soil_moisture = float(spring.get("soil_moisture_index") or 0.5)
    district = spring.get("nearby_village") or spring.get("village") or ""
    # Try to get district from village lookup: use state + try real_data
    # If village name is district-like, use it; else try state
    # For now use district = nearby_village or state
    if not district:
        district = spring.get("state") or ""
    # Also try to enrich rainfall from real IMD if spring's rainfall is synthetic and district found in real
    try:
        from services import real_data as rd
        # Try find district normal for this village's district
        # Village district maybe in villages.geojson district field — we need to lookup
        # For simplicity, use state avg from tribal_belt_stats if available
        belt_stats = rd.tribal_belt_stats()
        # Map state to belt
        state_lower = str(spring.get("state","")).lower()
        for belt, stats in belt_stats.items():
            if any(k in state_lower for k in [belt]):
                # Use belt avg as rainfall if synthetic is far off
                pass
    except: pass
    return recommend(recharge, rainfall, soil_moisture, district=district, early_risk=early_risk)
