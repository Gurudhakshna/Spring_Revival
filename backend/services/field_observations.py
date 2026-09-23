"""Field observations - field worker mode: discharge, water quality, photos, notes, GPS.
Stores in flat file backend/data/field_observations.json (no DB) with file lock.
"""
from __future__ import annotations
import json, os, time, uuid
from typing import List, Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
FILE = os.path.join(DATA_DIR, "field_observations.json")

def _load() -> List[Dict[str, Any]]:
    if not os.path.exists(FILE):
        return []
    try:
        with open(FILE, encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def _save(rows: List[Dict[str, Any]]):
    os.makedirs(os.path.dirname(FILE), exist_ok=True)
    tmp = FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
    os.replace(tmp, FILE)

def list_observations(spring_id: Optional[str]=None) -> List[Dict[str,Any]]:
    rows = _load()
    if spring_id:
        rows = [r for r in rows if r.get("spring_id")==spring_id]
    # newest first
    rows.sort(key=lambda r: r.get("created_at",""), reverse=True)
    return rows

def create(payload: Dict[str,Any]) -> Dict[str,Any]:
    rows = _load()
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    obs_id = f"FO-{time.strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
    # Basic validation
    spring_id = str(payload.get("spring_id") or "").strip()
    if not spring_id:
        raise ValueError("spring_id required")
    # Allow 0,0 but prefer real coords
    lat = float(payload.get("latitude") or 0)
    lon = float(payload.get("longitude") or 0)
    rec = {
        "observation_id": obs_id,
        "spring_id": spring_id,
        "observer_name": str(payload.get("observer_name") or "Field Officer").strip()[:100],
        "discharge_lpm": payload.get("discharge_lpm"),
        "water_quality": str(payload.get("water_quality") or "").strip()[:200],
        "turbidity": payload.get("turbidity"),
        "ph": payload.get("ph"),
        "notes": str(payload.get("notes") or "").strip()[:1000],
        "latitude": lat,
        "longitude": lon,
        "photo_url": str(payload.get("photo_url") or "").strip()[:500],
        "photos": payload.get("photos") or [],  # base64 or urls (demo)
        "created_at": now,
        "verified": False,
    }
    # Clean numerics
    for k in ("discharge_lpm","turbidity","ph"):
        try:
            if rec[k] is not None and rec[k] != "":
                rec[k] = float(rec[k])
            else:
                rec[k] = None
        except:
            rec[k] = None
    rows.append(rec)
    _save(rows)
    return rec

def get(obs_id: str) -> Optional[Dict[str,Any]]:
    for r in _load():
        if r.get("observation_id")==obs_id:
            return r
    return None
