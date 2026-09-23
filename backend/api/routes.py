"""All API routes. Every handler guards against missing data and never
leaks tracebacks to the client."""
from __future__ import annotations
import json as _json
import random
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query, UploadFile, File

from models.schemas import (
    ChatMessage, CommunityReportCreate, CommunityReportStatusUpdate,
    ForecastRequest, InterventionSimulateRequest, MLPredictRequest,
    RechargeCalculateRequest, ThresholdOverride,
)
from services import community_reports as cr_svc
from services import early_warning as ew_svc
from services import interventions as sim_svc
from services import priority as prio_svc
from services import recharge as rech_svc
from services import risks as risk_svc
from services import real_data as real_svc
from services.data_provider import DATA_BADGE

router = APIRouter(prefix="/api")

# Injected by main.py at startup
provider = None          # type: ignore
ml = None                # type: ignore

_grid_cache: Optional[List[Dict[str, Any]]] = None


def _prov():
    if provider is None:
        raise RuntimeError("Data provider not initialised")
    return provider


def _friendly(action: str) -> Dict[str, str]:
    return {"detail": f"Unable to load {action}. Please check the dataset."}


def _village_pop_map() -> Dict[str, int]:
    pops = {}
    for v in _prov().get_villages():
        vid = v.get("village_id") or v.get("id") or ""
        try:
            pops[vid] = int(v.get("population") or 0)
        except (TypeError, ValueError):
            pops[vid] = 0
    return pops


def _spring_by_id(spring_id: str) -> Optional[Dict[str, Any]]:
    for s in _prov().get_springs():
        if s.get("spring_id") == spring_id:
            return s
    return None


# ---------------- health ----------------
@router.get("/health")
def health():
    return {"status": "ok", "data_badge": DATA_BADGE}


# ---------------- dashboard ----------------
@router.get("/dashboard")
def dashboard():
    try:
        springs = _prov().get_springs()
        villages = _prov().get_villages()
        wells = _prov().get_wells()
        costs = _prov().get_intervention_costs()
        scores = [float(s.get("recharge_suitability", 0) or 0) for s in springs]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
        high = sum(1 for s in scores if s >= 70)
        medium = sum(1 for s in scores if 45 <= s < 70)
        low = sum(1 for s in scores if s < 45)
        pops = _village_pop_map()
        max_pop = max(pops.values()) if pops else 2200
        priorities = [prio_svc.compute_priority(s, pops.get(s.get("nearby_village_id", ""), 800), max_pop) for s in springs]
        high_prio = sum(1 for p in priorities if p["priority_class"] == "HIGH")
        potential = sum(1 for s in scores if 40 <= s <= 78)
        seasonal = sum(1 for s in springs if str(s.get("seasonality", "")).lower() == "seasonal")
        dis = [float(s.get("discharge_lpm", 0) or 0) for s in springs]
        return {
            "total_springs": len(springs),
            "total_wells": len(wells),
            "villages_covered": len(villages),
            "avg_recharge_suitability": avg_score,
            "high_priority_zones": high_prio,
            "potential_intervention_sites": potential,
            "recharge_classes": {"HIGH": high, "MEDIUM": medium, "LOW": low},
            "seasonal_springs": seasonal,
            "perennial_springs": len(springs) - seasonal,
            "avg_discharge_lpm": round(sum(dis) / len(dis), 1) if dis else 0.0,
            "intervention_types": len(costs),
            "study_area": "Pan-India Tribal Belts (7 zones) — 126 springs, 84 villages",
            "source": _prov().source_label,
            "data_badge": DATA_BADGE,
            "disclaimer": "Prototype Decision-Support Estimate — Pan-India synthetic demo",
        }
    except Exception:
        return _friendly("dashboard data")


# ---------------- geo entities ----------------
@router.get("/villages")
def villages(search: Optional[str] = None, state: Optional[str] = None, belt_id: Optional[str] = None):
    try:
        rows = _prov().get_villages()
        if state:
            q = state.lower()
            rows = [v for v in rows if q in str(v.get("state", "")).lower() or q in str(v.get("tribal_belt", "")).lower()]
        if belt_id:
            q = belt_id.lower()
            rows = [v for v in rows if q == str(v.get("belt_id", "")).lower()]
        if search:
            q = search.lower()
            rows = [v for v in rows if q in str(v.get("name", "")).lower()
                     or q in str(v.get("village_id", "")).lower()]
        return {"count": len(rows), "villages": rows, "source": _prov().source_label}
    except Exception:
        return {"count": 0, "villages": [], **_friendly("village data")}


@router.get("/springs")
def springs(search: Optional[str] = None, suitability_class: Optional[str] = None,
            seasonality: Optional[str] = None, state: Optional[str] = None, belt_id: Optional[str] = None, tribal_belt: Optional[str] = None):
    try:
        rows = _prov().get_springs()
        # State / belt filters - core for pan-India
        if state:
            q = state.lower()
            rows = [s for s in rows if q in str(s.get("state", "")).lower()]
        if tribal_belt:
            q = tribal_belt.lower()
            rows = [s for s in rows if q in str(s.get("tribal_belt", "")).lower()]
        if belt_id:
            # map belt_id to state/belt for backward compat
            belt_map = {"jhk":"jharkhand","mp":"madhya pradesh","rj":"rajasthan","ne":"meghalaya","ghats":"kerala","tn":"tamil","mh":"maharashtra"}
            q = belt_map.get(belt_id.lower(), belt_id.lower())
            rows = [s for s in rows if q in str(s.get("state", "")).lower() or q in str(s.get("tribal_belt", "")).lower()]
        if search:
            q = search.lower()
            rows = [s for s in rows if q in str(s.get("spring_id", "")).lower()
                     or q in str(s.get("nearby_village", "")).lower() or q in str(s.get("state", "")).lower()]
        if suitability_class:
            q = suitability_class.upper()
            rows = [s for s in rows
                     if rech_svc.classify(float(s.get("recharge_suitability", 0) or 0)) == q]
        if seasonality:
            q = seasonality.lower()
            rows = [s for s in rows if str(s.get("seasonality", "")).lower() == q]
        for s in rows:
            s["suitability_class"] = rech_svc.classify(float(s.get("recharge_suitability", 0) or 0))
            s["confidence"] = rech_svc.confidence_for(
                float(s.get("recharge_suitability", 0) or 0),
                str(s.get("land_use", "")), str(s.get("geology", "")))
        return {"count": len(rows), "springs": rows, "source": _prov().source_label,
                 "data_badge": DATA_BADGE}
    except Exception:
        return {"count": 0, "springs": [], **_friendly("spring data")}


@router.get("/springs/{spring_id}")
def spring_detail(spring_id: str):
    try:
        s = _spring_by_id(spring_id)
        if not s:
            return {"detail": f"Spring {spring_id} not found."}
        s = dict(s)
        score = float(s.get("recharge_suitability", 0) or 0)
        s["suitability_class"] = rech_svc.classify(score)
        s["confidence"] = rech_svc.confidence_for(score, str(s.get("land_use", "")), str(s.get("geology", "")))
        pops = _village_pop_map()
        max_pop = max(pops.values()) if pops else 2200
        s["priority"] = prio_svc.compute_priority(s, pops.get(s.get("nearby_village_id", ""), 800), max_pop)
        s["risk_flags"] = risk_svc.generate_risk_flags(s)
        # Estimated prototype springshed: circle sized by score (visual aid only)
        radius_m = int(250 + score * 6)
        s["estimated_springshed"] = {
            "type": "circle", "center": [s["latitude"], s["longitude"]],
            "radius_m": radius_m,
            "label": "Estimated Prototype Springshed (not an officially delineated springshed)",
        }
        s["disclaimer"] = "Prototype Decision-Support Estimate — requires field validation."
        return s
    except Exception:
        return _friendly("spring data")


@router.get("/wells")
def wells(state: Optional[str] = None, belt_id: Optional[str] = None):
    try:
        rows = _prov().get_wells()
        if state:
            q = state.lower()
            rows = [w for w in rows if q in str(w.get("state", "")).lower()]
        if belt_id:
            belt_map = {"jhk":"jharkhand","mp":"madhya pradesh","rj":"rajasthan","ne":"meghalaya","ghats":"kerala","tn":"tamil","mh":"maharashtra"}
            q = belt_map.get(belt_id.lower(), belt_id.lower())
            rows = [w for w in rows if q in str(w.get("state", "")).lower()]
        return {"count": len(rows), "wells": rows, "source": _prov().source_label}
    except Exception:
        return {"count": 0, "wells": [], **_friendly("well data")}


@router.get("/rainfall")
def rainfall():
    try:
        return {"monthly": _prov().get_monthly_rainfall(),
                "annual": _prov().get_annual_rainfall(),
                "source": _prov().source_label}
    except Exception:
        return {"monthly": [], "annual": [], **_friendly("rainfall data")}


@router.get("/study-areas")
def study_areas():
    return {"areas": [
        {"id": "jhk", "name": "Jharkhand-Odisha-Chhattisgarh Belt", "active": True,
         "note": "Pan-India Tribal Belt 1/7 — Central Plateau (18 springs)", "state": "Jharkhand", "center": [23.45, 84.95]},
        {"id": "mp", "name": "Madhya Pradesh Tribal Belt", "active": True,
         "note": "Pan-India Tribal Belt 2/7 — Satpura (18 springs)", "state": "Madhya Pradesh", "center": [22.90, 78.60]},
        {"id": "rj", "name": "Rajasthan-Gujarat Bhil Belt", "active": True,
         "note": "Pan-India Tribal Belt 3/7 — Arid Desert (18 springs) — LOW recharge demo", "state": "Rajasthan", "center": [23.80, 73.50]},
        {"id": "ne", "name": "Northeast Tribal Belt", "active": True,
         "note": "Pan-India Tribal Belt 4/7 — Himalayan Foothills (18 springs) — HIGH rainfall", "state": "Meghalaya-Nagaland", "center": [26.10, 92.90]},
        {"id": "ghats", "name": "Western Ghats Tribal Belt", "active": True,
         "note": "Pan-India Tribal Belt 5/7 — Western Ghats (18 springs) — HIGH recharge demo", "state": "Kerala-Karnataka", "center": [11.80, 76.10]},
        {"id": "tn", "name": "Tamil Nadu-Andhra Tribal Belt", "active": True,
         "note": "Pan-India Tribal Belt 6/7 — Eastern Ghats (18 springs)", "state": "Tamil Nadu", "center": [13.50, 79.00]},
        {"id": "mh", "name": "Maharashtra-Chhattisgarh Central Belt", "active": True,
         "note": "Pan-India Tribal Belt 7/7 — Deccan (18 springs)", "state": "Maharashtra", "center": [19.50, 80.20]},
    ]}


# ---------------- recharge ----------------
# Belt centers for pan-India grid generation
_BELT_CENTERS = {
    "jhk": (23.45, 84.95), "mp": (22.90, 78.60), "rj": (23.80, 73.50),
    "ne": (26.10, 92.90), "ghats": (11.80, 76.10), "tn": (13.50, 79.00), "mh": (19.50, 80.20),
}
_BELT_RANGES = {
    "jhk": {"rain": (950,1450), "slope": (4,28), "geo": ["fractured_rock","sandstone","weathered_granite","shale","clay"]},
    "mp": {"rain": (700,1100), "slope": (3,18), "geo": ["sandstone","shale","fractured_rock"]},
    "rj": {"rain": (380,700), "slope": (2,12), "geo": ["clay","shale","sandstone"]},
    "ne": {"rain": (1600,2600), "slope": (12,35), "geo": ["fractured_rock","weathered_granite"]},
    "ghats": {"rain": (1800,3000), "slope": (8,30), "geo": ["weathered_granite","fractured_rock"]},
    "tn": {"rain": (650,1050), "slope": (5,22), "geo": ["shale","clay","sandstone"]},
    "mh": {"rain": (850,1350), "slope": (5,25), "geo": ["sandstone","shale","fractured_rock"]},
}
_grid_cache_by_belt: Dict[str, List[Dict[str, Any]]] = {}

@router.get("/recharge/map")
def recharge_map(belt_id: Optional[str] = None, state: Optional[str] = None):
    try:
        springs = _prov().get_springs()
        # Filter points by belt/state if requested
        filtered = springs
        if belt_id:
            belt_map = {"jhk":"jharkhand","mp":"madhya pradesh","rj":"rajasthan","ne":"meghalaya","ghats":"kerala","tn":"tamil","mh":"maharashtra"}
            q = belt_map.get(belt_id.lower(), belt_id.lower())
            filtered = [s for s in springs if q in str(s.get("state","")).lower()]
        elif state:
            q = state.lower()
            filtered = [s for s in springs if q in str(s.get("state","")).lower()]
        points = [{
            "spring_id": s.get("spring_id"), "latitude": s.get("latitude"),
            "longitude": s.get("longitude"),
            "score": float(s.get("recharge_suitability", 0) or 0),
            "class": rech_svc.classify(float(s.get("recharge_suitability", 0) or 0)),
            "state": s.get("state"), "tribal_belt": s.get("tribal_belt"),
        } for s in filtered]
        # Grid: pan-India when no filter (all belts), else belt-specific
        cache_key = belt_id or state or "all"
        if cache_key not in _grid_cache_by_belt:
            rng = random.Random(7)
            grid = []
            if cache_key == "all":
                # 16 points per belt = 112
                for belt, (clat, clon) in _BELT_CENTERS.items():
                    br = _BELT_RANGES[belt]
                    for i in range(16):
                        lat = rng.uniform(clat-0.08, clat+0.08)
                        lon = rng.uniform(clon-0.08, clon+0.08)
                        payload = {
                            "rainfall": rng.uniform(*br["rain"]), "slope": rng.uniform(*br["slope"]),
                            "soil_moisture": rng.uniform(0.15, 0.95),
                            "land_use": rng.choice(["forest", "agroforestry", "agriculture", "grassland", "barren"]),
                            "geology": rng.choice(br["geo"]),
                            "distance_to_stream": rng.uniform(30, 1300),
                            "lineament_density": rng.uniform(0.05, 0.95),
                            "groundwater_depth": rng.uniform(4, 45),
                        }
                        r = rech_svc.calculate(payload)
                        grid.append({"id": f"GRID-{belt.upper()}-{i+1:02d}", "latitude": round(lat, 5),
                                     "longitude": round(lon, 5), "score": r["score"], "class": r["class"], "belt_id": belt})
            else:
                # Single belt: 110 points around that belt center
                belt = None
                if belt_id and belt_id.lower() in _BELT_CENTERS:
                    belt = belt_id.lower()
                elif state:
                    # find belt by state name
                    for k in _BELT_CENTERS:
                        if state.lower() in k or state.lower() in str(_BELT_CENTERS[k]):
                            belt = k
                            break
                if belt is None:
                    belt = "jhk"
                clat, clon = _BELT_CENTERS[belt]
                br = _BELT_RANGES[belt]
                for i in range(110):
                    lat = rng.uniform(clat-0.08, clat+0.08)
                    lon = rng.uniform(clon-0.08, clon+0.08)
                    payload = {
                        "rainfall": rng.uniform(*br["rain"]), "slope": rng.uniform(*br["slope"]),
                        "soil_moisture": rng.uniform(0.15, 0.95),
                        "land_use": rng.choice(["forest", "agroforestry", "agriculture", "grassland", "barren"]),
                        "geology": rng.choice(br["geo"]),
                        "distance_to_stream": rng.uniform(30, 1300),
                        "lineament_density": rng.uniform(0.05, 0.95),
                        "groundwater_depth": rng.uniform(4, 45),
                    }
                    r = rech_svc.calculate(payload)
                    grid.append({"id": f"GRID-{i+1:03d}", "latitude": round(lat, 5),
                                 "longitude": round(lon, 5), "score": r["score"], "class": r["class"]})
            _grid_cache_by_belt[cache_key] = grid
        return {"points": points, "grid": _grid_cache_by_belt[cache_key],
                "weights": rech_svc.DEFAULT_WEIGHTS,
                "belt_id": cache_key,
                "disclaimer": "Prototype Decision-Support Estimate"}
    except Exception:
        return {"points": [], "grid": [], **_friendly("recharge map data")}


@router.post("/recharge/calculate")
def recharge_calculate(body: RechargeCalculateRequest):
    try:
        return rech_svc.calculate(body.model_dump())
    except Exception:
        return _friendly("recharge calculation")


@router.get("/recharge/{spring_id}")
def recharge_for_spring(spring_id: str):
    try:
        s = _spring_by_id(spring_id)
        if not s:
            return {"detail": f"Spring {spring_id} not found."}
        calc = rech_svc.calculate({
            "rainfall": s.get("annual_rainfall_mm", 1200),
            "slope": s.get("slope_deg", 12),
            "soil_moisture": s.get("soil_moisture_index", 0.5),
            "land_use": s.get("land_use", "unknown"),
            "geology": s.get("geology", "unknown"),
            "distance_to_stream": s.get("distance_to_stream_m", 300),
            "lineament_density": s.get("lineament_density_index", 0.5),
            "groundwater_depth": s.get("groundwater_depth_m", 15),
        })
        calc["spring_id"] = spring_id
        calc["stored_score"] = float(s.get("recharge_suitability", 0) or 0)
        return calc
    except Exception:
        return _friendly("recharge data")


# ---------------- ML ----------------
@router.post("/ml/predict")
def ml_predict(body: MLPredictRequest):
    try:
        return ml.predict(body.model_dump())
    except Exception as e:
        return {"detail": f"ML prediction unavailable: {e}. Check training data."}


@router.get("/ml/metrics")
def ml_metrics():
    try:
        return ml.metrics()
    except Exception:
        return {"error": "Unable to compute model metrics. Please check the dataset."}


@router.get("/ml/feature-importance")
def ml_importance():
    try:
        return {"features": ml.feature_importance(),
                "model": "RandomForestRegressor",
                "disclaimer": "Prototype Decision-Support Estimate"}
    except Exception:
        return {"features": [], **_friendly("feature importance")}


# ---------------- interventions ----------------
@router.get("/interventions")
def intervention_catalog():
    try:
        return {"count": len(_prov().get_intervention_costs()),
                "interventions": _prov().get_intervention_costs(),
                "source": _prov().source_label}
    except Exception:
        return {"count": 0, "interventions": [], **_friendly("intervention data")}


@router.post("/interventions/simulate")
def intervention_simulate(body: InterventionSimulateRequest):
    try:
        costs = {c.get("type"): c for c in _prov().get_intervention_costs()}
        if body.intervention_type not in costs:
            return {"detail": f"Unknown intervention type '{body.intervention_type}'. "
                              f"Choose from: {', '.join(sorted(costs))}."}
        base = body.base_score
        spring = _spring_by_id(body.spring_id) if body.spring_id else None
        if base is None:
            base = float((spring or {}).get("recharge_suitability", 55) or 55)
        slope = float((spring or {}).get("slope_deg", 12) or 12)
        geo = str((spring or {}).get("geology", "fractured_rock"))
        result = sim_svc.simulate(costs[body.intervention_type], body.quantity, base, slope, geo)
        result["spring_id"] = body.spring_id
        result["location"] = {"latitude": body.latitude, "longitude": body.longitude}
        return result
    except Exception:
        return _friendly("intervention simulation")


# ---------------- priorities + risks ----------------
@router.get("/training-data")
def training_data(limit: int = Query(default=200, le=600)):
    """Paginated sample of the ML datasets (demo data, clearly labelled)."""
    import csv as _csv
    import os as _os
    try:
        base = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "data")
        out: Dict[str, Any] = {}
        for name in ("training_data.csv", "validation_data.csv"):
            path = _os.path.join(base, name)
            rows: List[Dict[str, Any]] = []
            cols: List[str] = []
            try:
                with open(path, newline="", encoding="utf-8") as f:
                    reader = _csv.DictReader(f)
                    cols = list(reader.fieldnames or [])
                    for i, r in enumerate(reader):
                        if i >= limit:
                            break
                        rows.append(r)
            except FileNotFoundError:
                pass
            key = "training" if name.startswith("training") else "validation"
            out[key] = {"columns": cols, "rows": rows, "count": len(rows)}
        out["source"] = _prov().source_label
        out["data_badge"] = DATA_BADGE
        return out
    except Exception:
        return {"training": {"columns": [], "rows": []},
                "validation": {"columns": [], "rows": []},
                **_friendly("training data")}


@router.get("/priorities")
def priorities(state: Optional[str] = Query(default=None), belt_id: Optional[str] = Query(default=None)):
    try:
        springs = _prov().get_springs()
        if state:
            q = state.lower()
            springs = [s for s in springs if q in str(s.get("state","")).lower()]
        if belt_id:
            belt_map = {"jhk":"jharkhand","mp":"madhya pradesh","rj":"rajasthan","ne":"meghalaya","ghats":"kerala","tn":"tamil","mh":"maharashtra"}
            q = belt_map.get(belt_id.lower(), belt_id.lower())
            springs = [s for s in springs if q in str(s.get("state","")).lower()]
        pops = _village_pop_map()
        max_pop = max(pops.values()) if pops else 2200
        out = [prio_svc.compute_priority(s, pops.get(s.get("nearby_village_id", ""), 800), max_pop)
               for s in springs]
        out.sort(key=lambda p: p["priority_score"], reverse=True)
        return {"count": len(out), "priorities": out}
    except Exception:
        return {"count": 0, "priorities": [], **_friendly("priority data")}


@router.get("/risk-flags")
def risk_flags(spring_id: Optional[str] = Query(default=None)):
    try:
        springs = _prov().get_springs()
        if spring_id:
            s = _spring_by_id(spring_id)
            if not s:
                return {"detail": f"Spring {spring_id} not found."}
            return {"spring_id": spring_id, "flags": risk_svc.generate_risk_flags(s)}
        return {"count": len(springs),
                "flags": [{"spring_id": s.get("spring_id"),
                           "flags": risk_svc.generate_risk_flags(s)} for s in springs]}
    except Exception:
        return {"count": 0, "flags": [], **_friendly("risk data")}


# ============ FEATURE 1: groundwater early warning ============
def _thresholds(body: Optional[ThresholdOverride]) -> Optional[Dict[str, float]]:
    if body is None:
        return None
    return {k: v for k, v in body.model_dump().items() if v is not None}


@router.get("/early-warning/status")
def ew_status():
    try:
        return ew_svc.status()
    except Exception:
        return {"available": False, **_friendly("groundwater dataset")}


@router.get("/early-warning/summary")
def ew_summary(min_level: str = Query(default="WATCH"),
               limit: int = Query(default=100, le=500),
               thresholds: Optional[ThresholdOverride] = None):
    try:
        return ew_svc.all_warnings(min_level=min_level, limit=limit,
                                   thresholds=_thresholds(thresholds))
    except Exception:
        return {"count": 0, "warnings": [], **_friendly("early-warning data")}


@router.post("/early-warning/summary")
def ew_summary_cfg(body: ThresholdOverride,
                   min_level: str = Query(default="WATCH"),
                   limit: int = Query(default=100, le=500)):
    return ew_summary(min_level=min_level, limit=limit, thresholds=body)


@router.get("/early-warning/stations")
def ew_stations(risk: Optional[str] = Query(default=None),
                search: Optional[str] = Query(default=None),
                limit: int = Query(default=100, le=500),
                offset: int = Query(default=0, ge=0)):
    try:
        full = ew_svc._summary_cache.get("full")
        if full is None:
            data = ew_svc.all_warnings(min_level="WATCH", limit=100000)
            rows = data.get("warnings", [])
            last = data.get("last_updated")
        else:
            rows = full["out"]
            last = full["last_updated"]
        if risk:
            rows = [w for w in rows if w.get("risk_level") == risk.upper()]
        if search:
            q = search.lower()
            rows = [w for w in rows if q in str(w.get("station_id", "")).lower()]
        total = len(rows)
        return {"count": total, "warnings": rows[offset:offset + limit],
                "last_updated": last,
                "disclaimer": "AI/Prototype Decision Support."}
    except Exception:
        return {"count": 0, "warnings": [], **_friendly("station warnings")}


@router.get("/early-warning/stations/{station_id}")
def ew_station_detail(station_id: str):
    try:
        w = ew_svc.station_warning(station_id)
        if "detail" in w and "risk_level" not in w:
            return w
        w["history"] = ew_svc.history(station_id)
        return w
    except Exception:
        return _friendly("station warning data")


@router.get("/early-warning/lead-time")
def ew_lead_time():
    try:
        return ew_svc.lead_time_validation()
    except Exception:
        return {"possible": False,
                "reason": "Unable to compute lead-time validation. Please check the dataset."}


@router.post("/early-warning/forecast/{station_id}")
def ew_forecast(station_id: str, body: ForecastRequest):
    try:
        return ew_svc.forecast(station_id, horizon_days=body.horizon_days)
    except Exception:
        return {"detail": "Forecast unavailable. Please check the dataset."}


# ============ UNIFIED ANALYSIS (Judge 3-min flow: ONE button) ============
@router.get("/analysis/{spring_id}")
def unified_analysis(spring_id: str):
    """ONE call returns recharge + risk + priority + ML + why + disclaimer + timestamp.
    This is the 'RUN AI ANALYSIS' button."""
    try:
        s = _spring_by_id(spring_id)
        if not s:
            return {"detail": f"Spring {spring_id} not found."}
        s = dict(s)
        score = float(s.get("recharge_suitability", 0) or 0)
        # Recharge via weighted engine (real)
        recharge = rech_svc.calculate({
            "rainfall": s.get("annual_rainfall_mm", 1200),
            "slope": s.get("slope_deg", 12),
            "soil_moisture": s.get("soil_moisture_index", 0.5),
            "land_use": s.get("land_use", "unknown"),
            "geology": s.get("geology", "unknown"),
            "distance_to_stream": s.get("distance_to_stream_m", 300),
            "lineament_density": s.get("lineament_density_index", 0.5),
            "groundwater_depth": s.get("groundwater_depth_m", 15),
        })
        # ML predict via RF
        try:
            ml_pred = ml.predict({
                "elevation_m": s.get("elevation_m", 600),
                "slope_deg": s.get("slope_deg", 12),
                "annual_rainfall_mm": s.get("annual_rainfall_mm", 1200),
                "soil_moisture_index": s.get("soil_moisture_index", 0.5),
                "land_use": s.get("land_use", "forest"),
                "geology": s.get("geology", "fractured_rock"),
                "distance_to_stream_m": s.get("distance_to_stream_m", 250),
                "lineament_density_index": s.get("lineament_density_index", 0.5),
                "groundwater_depth_m": s.get("groundwater_depth_m", 15),
            })
        except Exception as e:
            ml_pred = {"score": score, "class": rech_svc.classify(score), "confidence": 0.7, "error": str(e)}
        # Priority + risks
        pops = _village_pop_map()
        max_pop = max(pops.values()) if pops else 2200
        priority = prio_svc.compute_priority(s, pops.get(s.get("nearby_village_id",""), 800), max_pop)
        risks = risk_svc.generate_risk_flags(s)
        # Recommendation logic: based on geology/slope/rain
        geo = str(s.get("geology","")).lower()
        slope = float(s.get("slope_deg",12) or 12)
        rain = float(s.get("annual_rainfall_mm",1200) or 1200)
        if geo in ("clay","shale") or rain < 600:
            rec_type, rec_why = "check_dam", "Clay/shale or low rainfall — stream barrier more effective than hillside trench"
        elif slope > 22:
            rec_type, rec_why = "contour_trench", "Steep slope — contour trenches reduce runoff"
        elif s.get("land_use")=="forest":
            rec_type, rec_why = "recharge_trench", "Forest cover with good lineament — trench captures runoff"
        elif rain > 2000:
            rec_type, rec_why = "percolation_pond", "Very high rainfall — pond stores monsoon for slow percolation"
        else:
            rec_type, rec_why = "recharge_trench", "Moderate conditions — balanced trench"
        # Why bars: use recharge factors sorted
        why_factors = sorted(recharge.get("factors",{}).items(), key=lambda kv: kv[1], reverse=True)
        # Water stress heuristic
        water_stress = "HIGH" if score < 45 else ("MODERATE" if score < 70 else "LOW")
        spring_risk = "HIGH" if any(f.get("status")=="Risk" for f in risks) else "MODERATE"
        # Model meta
        import time as _t
        return {
            "spring_id": spring_id,
            "state": s.get("state"), "tribal_belt": s.get("tribal_belt"),
            "location": {"latitude": s["latitude"], "longitude": s["longitude"], "village": s.get("nearby_village"), "elevation_m": s.get("elevation_m")},
            "recharge": recharge,
            "ml": ml_pred,
            "priority": priority,
            "risk_flags": risks,
            "recommendation": {"type": rec_type, "why": rec_why},
            "assessment": {
                "recharge_suitability": recharge.get("score"), "recharge_class": recharge.get("class"),
                "water_stress": water_stress, "spring_risk": spring_risk,
                "confidence": ml_pred.get("confidence", recharge.get("confidence")),
            },
            "why": [{"factor": k, "value": v} for k,v in why_factors],
            "model": {"name": "RandomForestRegressor", "n_estimators": 200, "n_train": 800, "n_val": 200, "target": "recharge_suitability"},
            "timestamp": _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime()),
            "data_source": _prov().source_label, "data_badge": DATA_BADGE,
            "disclaimer": "Prototype Decision-Support Estimate — requires field validation.",
            "springshed": {"type":"circle","center":[s["latitude"], s["longitude"]],"radius_m": int(250+score*6), "label":"Estimated Prototype Springshed (not officially delineated)"},
        }
    except Exception as e:
        return {"detail": f"Analysis failed: {e}. Check dataset."}

@router.post("/analysis/{spring_id}/explain")
def analysis_explain(spring_id: str):
    try:
        data = unified_analysis(spring_id)
        if "detail" in data and "recharge" not in data:
            return data
        from services import llm as llm_svc
        txt = llm_svc.explain_analysis(data)
        return {"spring_id": spring_id, "explanation": txt, "provider": llm_svc.provider_name(), "has_key": llm_svc.has_key(), "disclaimer":"Prototype Decision-Support Estimate"}
    except Exception as e:
        return {"detail": f"Explain failed: {e}"}

# ============ FIELD OBSERVATIONS (Field Worker Mode) ============
@router.get("/field-observations")
def fo_list(spring_id: Optional[str] = Query(default=None)):
    try:
        from services import field_observations as fo_svc
        rows = fo_svc.list_observations(spring_id=spring_id)
        return {"count": len(rows), "observations": rows}
    except Exception:
        return {"count":0,"observations":[], **_friendly("field observations")}

@router.post("/field-observations")
def fo_create(body: Dict[str, Any]):
    try:
        from services import field_observations as fo_svc
        # Accept any JSON, validate inside service
        rec = fo_svc.create(body)
        return rec
    except ValueError as ve:
        return {"detail": str(ve)}
    except Exception as e:
        return {"detail": f"Unable to save observation: {e}"}

@router.get("/field-observations/{obs_id}")
def fo_get(obs_id: str):
    try:
        from services import field_observations as fo_svc
        r = fo_svc.get(obs_id)
        if not r:
            return {"detail": f"Observation {obs_id} not found."}
        return r
    except Exception:
        return _friendly("field observation")

# ============ REPORTS (Dynamic PDF) ============
@router.get("/reports/{spring_id}")
def report_generate(spring_id: str):
    try:
        # Build payload from analysis + spring detail
        analysis = unified_analysis(spring_id)
        if "detail" in analysis and "recharge" not in analysis:
            return analysis
        from services import reports as rep_svc
        # Try simulate for recommendation
        rec_type = analysis.get("recommendation",{}).get("type","recharge_trench")
        try:
            costs = {c.get("type"): c for c in _prov().get_intervention_costs()}
            if rec_type in costs:
                from services import interventions as sim_svc
                sim = sim_svc.simulate(costs[rec_type], 1, float(analysis["recharge"]["score"]), float(analysis["location"].get("elevation_m",600) or 12), str(analysis.get("spring",{}).get("geology","fractured_rock")))
                analysis["simulation"] = sim
        except Exception:
            pass
        pdf_bytes, mime = rep_svc.generate_pdf({
            "spring_id": spring_id,
            "spring": _spring_by_id(spring_id) or {},
            "location": analysis.get("location"),
            "recharge": analysis.get("recharge"),
            "priority": analysis.get("priority"),
            "risk_flags": analysis.get("risk_flags"),
            "recommendation": analysis.get("recommendation"),
            "simulation": analysis.get("simulation"),
        })
        if mime == "application/pdf":
            from fastapi.responses import Response
            return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=JAL-RAKSHA-{spring_id}.pdf"})
        else:
            from fastapi.responses import JSONResponse
            return JSONResponse(content={"report_json": json.loads(pdf_bytes.decode("utf-8")), "note":"Install fpdf2 for PDF"})
    except Exception as e:
        return {"detail": f"Report failed: {e}"}

@router.get("/reports/{spring_id}/html")
def report_html(spring_id: str):
    try:
        analysis = unified_analysis(spring_id)
        from services import reports as rep_svc
        html = rep_svc.generate_html_report({"spring_id": spring_id, **analysis})
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html)
    except Exception as e:
        return {"detail": f"Report html failed: {e}"}

# ============ DATA MANAGEMENT (Admin upload) ============
@router.post("/data/upload")
async def data_upload(file: UploadFile = File(...), type: str = "springs"):
    try:
        content = await file.read()
        text = content.decode("utf-8", errors="ignore")
        import csv as _csv, io as _io
        reader = _csv.DictReader(_io.StringIO(text))
        rows = list(reader)
        if not rows:
            return {"valid": False, "errors": ["Empty CSV or missing header"], "filename": file.filename}
        required = {
            "springs": ["spring_id","latitude","longitude","recharge_suitability"],
            "villages": ["village_id","name","latitude","longitude"],
            "wells": ["well_id","latitude","longitude","depth_m"],
        }.get(type.lower(), ["spring_id","latitude","longitude"])
        errors = []
        for i,r in enumerate(rows[:20]):
            for col in required:
                if col not in r or str(r[col] or "").strip()=="":
                    errors.append(f"row {i+1} missing {col}")
            try:
                float(r.get("latitude") or 0); float(r.get("longitude") or 0)
            except:
                errors.append(f"row {i+1} invalid lat/lon")
        preview = rows[:3]
        # Save history even if errors (so admin sees)
        import time as _t, os as _o
        hist_path = _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "data", "import_history.json")
        hist = []
        if _o.path.exists(hist_path):
            try:
                with open(hist_path) as f: hist = _j if False else _json.load(f)
            except: hist=[]
        entry = {"timestamp": _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime()), "type": type, "filename": file.filename, "count": len(rows), "preview": preview, "errors": errors[:10], "valid": len(errors)==0}
        hist.append(entry)
        hist = hist[-20:]
        _o.makedirs(_o.path.dirname(hist_path), exist_ok=True)
        with open(hist_path, "w") as f: _json.dump(hist, f, indent=2)
        if errors:
            return {"valid": False, "errors": errors[:10], "preview": preview, "count": len(rows), "filename": file.filename}
        return {"valid": True, "imported": len(rows), "type": type, "preview": preview, "filename": file.filename, "message": "Validated and logged. Overwrite CSV manually to activate (demo safety)."}
    except Exception as e:
        return {"detail": f"Upload failed: {e}"}

@router.post("/data/upload-csv")
def data_upload_csv(payload: Dict[str, Any]):
    """Admin upload CSV as JSON rows (for demo without multipart).
    payload: {type: 'springs'|'villages'|'wells', rows: [...], validate_only: bool}"""
    try:
        typ = str(payload.get("type") or "").lower()
        rows = payload.get("rows") or []
        validate_only = bool(payload.get("validate_only"))
        if typ not in ("springs","villages","wells"):
            return {"detail": "type must be springs, villages, or wells"}
        if not isinstance(rows, list) or not rows:
            return {"detail": "rows must be non-empty list"}
        # Validate header contract
        required = {
            "springs": ["spring_id","latitude","longitude","recharge_suitability"],
            "villages": ["village_id","name","latitude","longitude"],
            "wells": ["well_id","latitude","longitude","depth_m"],
        }[typ]
        errors = []
        for i,r in enumerate(rows[:20]):
            for col in required:
                if col not in r or r[col] in ("", None):
                    errors.append(f"row {i} missing {col}")
        preview = rows[:3]
        if validate_only:
            return {"valid": len(errors)==0, "errors": errors, "preview": preview, "count": len(rows)}
        if errors:
            return {"valid": False, "errors": errors, "preview": preview}
        # Save preview to history (not overwriting real data in demo - just history log)
        import time as _t, json as _j, os as _o
        hist_path = _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "data", "import_history.json")
        hist = []
        if _o.path.exists(hist_path):
            try:
                with open(hist_path) as f: hist = _j.load(f)
            except: hist=[]
        hist.append({"timestamp": _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime()), "type": typ, "count": len(rows), "preview": preview, "errors": errors})
        hist = hist[-20:]
        _o.makedirs(_o.path.dirname(hist_path), exist_ok=True)
        with open(hist_path, "w") as f: _j.dump(hist, f, indent=2)
        return {"valid": True, "imported": len(rows), "type": typ, "preview": preview, "message": "Validated and logged (demo - real import would overwrite CSV)"}
    except Exception as e:
        return {"detail": f"Upload failed: {e}"}

@router.get("/data/history")
def data_history():
    try:
        import os as _o, json as _j
        hist_path = _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "data", "import_history.json")
        if not _o.path.exists(hist_path):
            return {"count":0, "history":[]}
        with open(hist_path) as f: hist = _j.load(f)
        return {"count": len(hist), "history": hist}
    except Exception:
        return {"count":0,"history":[]}

# ============ REAL IMD + SOIL DATA (Spring_Revival Db) ============
@router.get("/real/summary")
def real_summary():
    try:
        return real_svc.summary()
    except Exception:
        return {"error":"real data unavailable"}

@router.get("/rainfall/normal")
def rainfall_normal(state: Optional[str]=None, district: Optional[str]=None, q: Optional[str]=None, limit: int=Query(default=20, le=100)):
    try:
        rows = real_svc.rainfall_normal(state=state, district=district, q=q, limit=limit)
        return {"count": len(rows), "rows": rows, "source":"IMD district wise normal (1901-2017 avg)", "disclaimer":"Real IMD data from Spring_Revival Db — 641 districts"}
    except Exception:
        return {"count":0,"rows":[], **_friendly("rainfall normal data")}

@router.get("/rainfall/historical")
def rainfall_historical(subdivision: Optional[str]=None, from_year: Optional[int]=None, to_year: Optional[int]=None, limit: int=Query(default=100, le=500)):
    try:
        rows = real_svc.rainfall_historical(subdivision=subdivision, from_year=from_year, to_year=to_year, limit=limit)
        return {"count": len(rows), "rows": rows, "source":"IMD Subdivision 1901-2017", "disclaimer":"Real IMD historical — 4188 records 1901-2017"}
    except Exception:
        return {"count":0,"rows":[], **_friendly("rainfall historical data")}

@router.get("/rainfall/daily")
def rainfall_daily(state: Optional[str]=None, district: Optional[str]=None, month: Optional[int]=None, limit: int=Query(default=50, le=200)):
    try:
        rows = real_svc.rainfall_daily(state=state, district=district, month=month, limit=limit)
        return {"count": len(rows), "rows": rows, "source":"IMD District-wise Daily Measurements", "disclaimer":"Daily per-district — 8790 records"}
    except Exception:
        return {"count":0,"rows":[], **_friendly("rainfall daily data")}

@router.get("/soil")
def soil(district: Optional[str]=None, q: Optional[str]=None, limit: int=Query(default=50, le=100)):
    try:
        rows = real_svc.soil(district=district, q=q, limit=limit)
        return {"count": len(rows), "rows": rows, "source":"Soil micronutrients district-wise (Zn,Fe,Cu,Mn,B,S)", "disclaimer":"Real soil data — 673 districts, % deficiency values"}
    except Exception:
        return {"count":0,"rows":[], **_friendly("soil data")}

@router.get("/tribal-belt/rainfall")
def tribal_belt_rainfall():
    try:
        return {"belts": real_svc.tribal_belt_stats(), "source":"IMD district normal aggregated to 7 tribal belts"}
    except Exception:
        return {"belts":{}, **_friendly("tribal belt rainfall")}

# ============ FEATURE 2: community reporting ============
@router.post("/community-reports")
def cr_create(body: CommunityReportCreate):
    try:
        rep = cr_svc.create(body.model_dump())
        rep["event"] = "NEW_COMMUNITY_REPORT"
        return rep
    except Exception:
        return {"detail": "Unable to submit report. Please check the data and retry."}


@router.get("/community-reports")
def cr_list(status: Optional[str] = Query(default=None),
            severity: Optional[str] = Query(default=None)):
    try:
        rows = cr_svc.list_reports(status=status, severity=severity)
        return {"count": len(rows), "reports": rows,
                "label": "Community reported — pending field verification."}
    except Exception:
        return {"count": 0, "reports": [], **_friendly("community reports")}


@router.get("/community-reports/clusters")
def cr_clusters():
    try:
        return cr_svc.clusters()
    except Exception:
        return {"clusters": [], **_friendly("report clusters")}


@router.get("/community-reports/{report_id}")
def cr_get(report_id: str):
    try:
        r = cr_svc.get(report_id)
        if not r:
            return {"detail": f"Report {report_id} not found."}
        return r
    except Exception:
        return _friendly("community report")


@router.patch("/community-reports/{report_id}")
def cr_status(report_id: str, body: CommunityReportStatusUpdate):
    try:
        r = cr_svc.set_status(report_id, body.status)
        if not r:
            return {"detail": f"Report {report_id} not found or invalid status."}
        return r
    except Exception:
        return _friendly("community report update")


@router.post("/community-reports/{report_id}/reverify")
def cr_reverify(report_id: str):
    try:
        r = cr_svc.refresh_verification(report_id)
        if not r:
            return {"detail": f"Report {report_id} not found."}
        return r
    except Exception:
        return _friendly("report verification")


@router.post("/community-reports/chat")
def cr_chat(body: ChatMessage):
    """Prototype WhatsApp/SMS-style demo (SIMULATION ONLY — no real messaging
    provider connected). Guides villager -> village -> severity -> creates report."""
    try:
        s = dict(body.session or {})
        msg = (body.message or "").strip()
        step = s.get("step", "problem")

        def ask(text: str, next_step: str, patch: Dict[str, Any]):
            ns = {**s, **patch, "step": next_step}
            return {"reply": text, "session": ns, "done": False,
                    "note": "Prototype simulation — no real WhatsApp/SMS connected."}

        if step == "problem":
            if not msg:
                return ask("Namaste! Describe your water problem (e.g. 'Our well went dry').",
                           "problem", {})
            return ask("Thank you. Please share your village name.", "village",
                       {"description": msg[:500]})
        if step == "village":
            if not msg:
                return ask("Please share your village name.", "village", {})
            return ask("Severity? Reply LOW, MEDIUM, HIGH or CRITICAL.", "severity",
                       {"village": msg[:200]})
        if step == "severity":
            sev = msg.upper() if msg.upper() in ("LOW", "MEDIUM", "HIGH", "CRITICAL") else "MEDIUM"
            s2 = {**s, "severity": sev, "step": "location"}
            return {"reply": ("If possible, share location as 'lat,lon' (e.g. 23.46,84.96), "
                              "or reply SKIP."),
                    "session": s2, "done": False,
                    "note": "Prototype simulation — no real WhatsApp/SMS connected."}
        # location step -> create
        lat, lon = 0.0, 0.0
        if msg.upper() != "SKIP" and "," in msg:
            try:
                a, b = msg.split(",", 1)
                lat, lon = float(a.strip()), float(b.strip())
            except (TypeError, ValueError):
                pass
        rep = cr_svc.create({
            "problem_type": "other", "description": s.get("description", ""),
            "village": s.get("village", ""), "latitude": lat, "longitude": lon,
            "severity": s.get("severity", "MEDIUM")})
        return {"reply": (f"Thank you. Your report {rep['report_id']} has been registered. "
                          "Community reported — pending field verification."),
                "session": {}, "done": True, "report_id": rep["report_id"],
                "note": "Prototype simulation — no real WhatsApp/SMS connected."}
    except Exception:
        return {"reply": "Sorry, something went wrong. Please try again.",
                "session": {}, "done": False}
