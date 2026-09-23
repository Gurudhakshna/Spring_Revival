"""Villager community reporting (FEATURE 2).

No second database: the prototype has no DB server, so reports persist to
backend/data/community_reports.json (same flat-file approach as the rest of
the app). Swap this module for a real table later without touching routes.

Every report is labelled "Community reported — pending field verification"
and is cross-checked against the nearest groundwater monitoring station —
never auto-assumed correct.
"""
from __future__ import annotations
import json
import math
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from services import early_warning as ew

STORE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "data", "community_reports.json")

PROBLEM_TYPES = ["well_dry", "spring_stopped", "level_falling", "shortage",
                 "quality", "structure_damaged", "flooding", "other"]
SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
STATUSES = ["NEW", "UNDER_REVIEW", "ESCALATED", "RESOLVED"]
STATUS_MARKER = {"NEW": "NEW", "UNDER_REVIEW": "UNDER REVIEW",
                 "ESCALATED": "ESCALATED", "RESOLVED": "RESOLVED"}

_lock = threading.Lock()
_cache: Optional[List[Dict[str, Any]]] = None


def _load() -> List[Dict[str, Any]]:
    global _cache
    if _cache is not None:
        return _cache
    if os.path.exists(STORE):
        try:
            with open(STORE, encoding="utf-8") as f:
                _cache = json.load(f)
                return _cache
        except Exception:
            pass
    _cache = []
    return _cache


def _save() -> None:
    os.makedirs(os.path.dirname(STORE), exist_ok=True)
    with open(STORE, "w", encoding="utf-8") as f:
        json.dump(_cache, f, indent=2)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest_station(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    df_ok = ew._load()
    if df_ok is None or ew._stations is None or not len(ew._stations):
        return None
    st = ew._stations
    best, best_d = None, float("inf")
    for _, r in st.iterrows():
        try:
            d = _haversine_km(lat, lon, float(r["lat"]), float(r["lon"]))
        except (TypeError, ValueError):
            continue
        if d < best_d:
            best_d, best = d, r
    if best is None:
        return None
    return {"station_id": str(best["station_id"]), "latitude": float(best["lat"]),
            "longitude": float(best["lon"]), "distance_km": round(best_d, 2),
            "n_obs": int(best["n_obs"])}


def _next_id() -> str:
    year = datetime.now(timezone.utc).year
    rows = _load()
    n = sum(1 for r in rows if str(r.get("report_id", "")).startswith(f"JR-{year}-"))
    return f"JR-{year}-{n + 1:04d}"


def verify_against_station(report: Dict[str, Any]) -> Dict[str, Any]:
    """Compare a community report with its nearest station's live warning."""
    ns = report.get("nearest_station") or {}
    sid = ns.get("station_id")
    if not sid:
        return {"verdict": "No monitoring station nearby — field verification required.",
                "consistent": None}
    w = ew.station_warning(sid)
    level = w.get("risk_level", "NORMAL")
    stress = level in ("WARNING", "CRITICAL")
    water_problem = report.get("problem_type") in ("well_dry", "spring_stopped",
                                                   "level_falling", "shortage")
    if stress and water_problem:
        verdict = ("Community report is consistent with current groundwater stress "
                   f"at {sid} ({level}).")
        consistent = True
    elif not stress and water_problem:
        verdict = ("Community report does not currently match monitored groundwater "
                   f"conditions at {sid} ({level}) — field verification recommended.")
        consistent = False
    else:
        verdict = (f"Report logged against station {sid} ({level}); "
                   "field verification recommended.")
        consistent = None
    return {"station_id": sid, "station_risk": level,
            "station_trend": w.get("trend"),
            "rainfall_anomaly_pct": w.get("rainfall_anomaly_pct"),
            "verdict": verdict, "consistent": consistent,
            "label": "Community reported — pending field verification."}


def create(payload: Dict[str, Any]) -> Dict[str, Any]:
    with _lock:
        rows = _load()
        rid = _next_id()
        now = datetime.now(timezone.utc).isoformat()
        lat = float(payload.get("latitude", 0) or 0)
        lon = float(payload.get("longitude", 0) or 0)
        ns = nearest_station(lat, lon) if (lat and lon) else None
        rep = {
            "report_id": rid,
            "problem_type": str(payload.get("problem_type", "other")),
            "description": str(payload.get("description", ""))[:1000],
            "village": str(payload.get("village", ""))[:200],
            "latitude": lat, "longitude": lon,
            "severity": str(payload.get("severity", "MEDIUM")).upper(),
            "status": "NEW",
            "created_at": now, "updated_at": now,
            "nearest_station_id": (ns or {}).get("station_id"),
            "nearest_station": ns,
            "risk_level": None,
            "label": "Community reported — pending field verification.",
        }
        if rep["severity"] not in SEVERITIES:
            rep["severity"] = "MEDIUM"
        if rep["problem_type"] not in PROBLEM_TYPES:
            rep["problem_type"] = "other"
        v = verify_against_station(rep)
        rep["risk_level"] = v.get("station_risk")
        rep["verification"] = v
        rows.append(rep)
        _save()
        return rep


def list_reports(status: Optional[str] = None,
                 severity: Optional[str] = None) -> List[Dict[str, Any]]:
    rows = list(_load())
    if status:
        rows = [r for r in rows if r.get("status") == status.upper()]
    if severity:
        rows = [r for r in rows if r.get("severity") == severity.upper()]
    rows.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return rows


def get(report_id: str) -> Optional[Dict[str, Any]]:
    for r in _load():
        if r.get("report_id") == report_id:
            return r
    return None


def set_status(report_id: str, status: str) -> Optional[Dict[str, Any]]:
    if status.upper() not in STATUSES:
        return None
    with _lock:
        r = get(report_id)
        if not r:
            return None
        r["status"] = status.upper()
        r["updated_at"] = datetime.now(timezone.utc).isoformat()
        _save()
        return r


def refresh_verification(report_id: str) -> Optional[Dict[str, Any]]:
    with _lock:
        r = get(report_id)
        if not r:
            return None
        v = verify_against_station(r)
        r["verification"] = v
        r["risk_level"] = v.get("station_risk")
        r["updated_at"] = datetime.now(timezone.utc).isoformat()
        _save()
        return r


def clusters() -> Dict[str, Any]:
    """Prototype prioritization rule (labelled as such): 1=signal,
    2-3=elevated attention, 4+=high-priority investigation near a station."""
    rows = _load()
    by_st: Dict[str, List[str]] = {}
    for r in rows:
        sid = r.get("nearest_station_id") or "unlinked"
        by_st.setdefault(sid, []).append(r["report_id"])
    out = []
    for sid, ids in by_st.items():
        n = len(ids)
        level = ("high_priority_investigation" if n >= 4
                 else "elevated_attention" if n >= 2 else "community_signal")
        out.append({"station_id": sid, "report_count": n,
                    "report_ids": ids, "attention": level})
    out.sort(key=lambda c: -c["report_count"])
    return {"clusters": out,
            "rule": ("Prototype prioritization rule: 1 report = community signal, "
                     "2-3 = elevated attention, 4+ = high-priority investigation. "
                     "Multiple reports do NOT prove groundwater failure."),
            "disclaimer": "Community reported — pending field verification."}
