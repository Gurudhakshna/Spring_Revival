"""Real IMD + Soil datasets from Spring_Revival Db.
Loaded from backend/data/real/*.csv — 641 districts normal, 4188 historical 1901-2017, 673 soil, 8790 daily.
All cached in memory, never hits disk per request. Fallback to empty if files missing.
"""
from __future__ import annotations
import os, csv, json
from typing import List, Dict, Any, Optional
from functools import lru_cache

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "real")

def _load_csv(name: str) -> List[Dict[str,Any]]:
    path = os.path.join(BASE, name)
    if not os.path.exists(path):
        return []
    try:
        with open(path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []

# Cache
_cache: Dict[str, List[Dict[str,Any]]] = {}

def _get(name: str) -> List[Dict[str,Any]]:
    if name not in _cache:
        _cache[name] = _load_csv(name)
    return _cache[name]

def summary() -> Dict[str,Any]:
    p = os.path.join(BASE, "real_data_summary.json")
    if os.path.exists(p):
        try:
            with open(p) as f: return json.load(f)
        except: pass
    return {
        "district_normal": {"rows": len(_get("rainfall_district_normal.csv"))},
        "historical": {"rows": len(_get("rainfall_historical_1901_2017.csv"))},
        "soil": {"rows": len(_get("soil_district.csv"))},
        "daily": {"rows": len(_get("rainfall_daily_district.csv"))},
    }

def rainfall_normal(state: Optional[str]=None, district: Optional[str]=None, q: Optional[str]=None, limit: int=50) -> List[Dict[str,Any]]:
    rows = _get("rainfall_district_normal.csv")
    if state:
        qs = state.lower()
        rows = [r for r in rows if qs in str(r.get("STATE_UT_NAME","")).lower()]
    if district:
        qd = district.lower()
        rows = [r for r in rows if qd in str(r.get("DISTRICT","")).lower()]
    if q:
        ql = q.lower()
        rows = [r for r in rows if ql in str(r.get("DISTRICT","")).lower() or ql in str(r.get("STATE_UT_NAME","")).lower()]
    return rows[:limit]

def rainfall_historical(subdivision: Optional[str]=None, from_year: Optional[int]=None, to_year: Optional[int]=None, limit: int=100) -> List[Dict[str,Any]]:
    rows = _get("rainfall_historical_1901_2017.csv")
    if subdivision:
        qs = subdivision.lower()
        rows = [r for r in rows if qs in str(r.get("SUBDIVISION","")).lower()]
    if from_year is not None:
        try:
            fy = int(from_year)
            rows = [r for r in rows if int(float(r.get("YEAR") or 0)) >= fy]
        except: pass
    if to_year is not None:
        try:
            ty = int(to_year)
            rows = [r for r in rows if int(float(r.get("YEAR") or 0)) <= ty]
        except: pass
    # sort by year asc
    try:
        rows = sorted(rows, key=lambda r: int(float(r.get("YEAR") or 0)))
    except: pass
    return rows[:limit]

def soil(district: Optional[str]=None, q: Optional[str]=None, limit: int=50) -> List[Dict[str,Any]]:
    rows = _get("soil_district.csv")
    if district:
        qd = district.lower()
        rows = [r for r in rows if qd == str(r.get("district","")).lower()]
        if rows: return rows[:limit]
        # fallback contains
        rows2 = _get("soil_district.csv")
        rows = [r for r in rows2 if qd in str(r.get("district","")).lower()]
    if q:
        ql = q.lower()
        rows = [r for r in rows if ql in str(r.get("district","")).lower()]
    return rows[:limit]

def rainfall_daily(state: Optional[str]=None, district: Optional[str]=None, month: Optional[int]=None, limit: int=100) -> List[Dict[str,Any]]:
    rows = _get("rainfall_daily_district.csv")
    if state:
        qs = state.lower()
        rows = [r for r in rows if qs in str(r.get("state","")).lower()]
    if district:
        qd = district.lower()
        rows = [r for r in rows if qd in str(r.get("district","")).lower()]
    if month is not None:
        try:
            m = str(int(month))
            rows = [r for r in rows if str(r.get("month","")).strip() == m]
        except: pass
    return rows[:limit]

def tribal_belt_stats():
    """Aggregate district normals for 7 tribal belts (for dashboard enrichment)."""
    # Map belt to states/districts keywords
    belts = {
        "jhk": ["jharkhand","odisha","chhattisgarh"],
        "mp": ["madhya pradesh"],
        "rj": ["rajasthan","gujarat"],
        "ne": ["assam","meghalaya","nagaland","mizoram","manipur","arunachal"],
        "ghats": ["kerala","karnataka","maharashtra", "goa"],
        "tn": ["tamil nadu","andhra pradesh"],
        "mh": ["maharashtra","chhattisgarh"],
    }
    rows = _get("rainfall_district_normal.csv")
    out = {}
    for belt, kws in belts.items():
        matched = [r for r in rows if any(kw in str(r.get("STATE_UT_NAME","")).lower() for kw in kws)]
        if matched:
            try:
                avg_annual = sum(float(r.get("ANNUAL") or 0) for r in matched) / len(matched)
                avg_jun_sep = sum(float(r.get("JUN-SEP") or r.get("JUN_SEP") or 0) for r in matched) / len(matched)
            except:
                avg_annual = 0
                avg_jun_sep = 0
            out[belt] = {"districts": len(matched), "avg_annual_mm": round(avg_annual,1), "avg_monsoon_mm": round(avg_jun_sep,1)}
    return out
