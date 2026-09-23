"""Data adapter architecture.

DataProvider (abstract)
├── CSVDatasetProvider  (reads CSV/GeoJSON files from disk)
├── DemoDataProvider    (synthetic prototype dataset, clearly labelled)
└── FutureGovernmentDataProvider (stub: how to plug real APIs later)

The frontend NEVER reads demo files directly - it only talks to FastAPI,
which goes through the provider. Swapping demo -> real data means writing
a new provider subclass + pointing DATA_DIR at validated files.
"""
from __future__ import annotations
import csv
import json
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List

DATA_LABEL = "Synthetic Prototype Dataset"
DATA_BADGE = "DEMO DATA — Replace with validated government/field data"


def _read_csv(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def _to_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None or v == "":
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


class DataProvider(ABC):
    source_label: str = "unknown"

    @abstractmethod
    def get_villages(self) -> List[Dict[str, Any]]: ...
    @abstractmethod
    def get_springs(self) -> List[Dict[str, Any]]: ...
    @abstractmethod
    def get_wells(self) -> List[Dict[str, Any]]: ...
    @abstractmethod
    def get_monthly_rainfall(self) -> List[Dict[str, Any]]: ...
    @abstractmethod
    def get_annual_rainfall(self) -> List[Dict[str, Any]]: ...
    @abstractmethod
    def get_intervention_costs(self) -> List[Dict[str, Any]]: ...
    @abstractmethod
    def get_boundary(self) -> Dict[str, Any]: ...


class CSVDatasetProvider(DataProvider):
    """Generic file-backed provider. Works for demo CSVs today and for
    validated government CSVs tomorrow (same column contract)."""

    def __init__(self, data_dir: str, label: str = DATA_LABEL):
        self.data_dir = data_dir
        self.source_label = label
        self._cache: Dict[str, Any] = {}

    def _csv(self, name: str) -> List[Dict[str, Any]]:
        if name not in self._cache:
            self._cache[name] = _read_csv(os.path.join(self.data_dir, name))
        return self._cache[name]

    def get_villages(self) -> List[Dict[str, Any]]:
        if "villages" not in self._cache:
            path = os.path.join(self.data_dir, "villages.geojson")
            villages: List[Dict[str, Any]] = []
            try:
                if os.path.exists(path):
                    with open(path, encoding="utf-8") as f:
                        fc = json.load(f)
                    for feat in fc.get("features", []):
                        p = dict(feat.get("properties", {}))
                        coords = (feat.get("geometry") or {}).get("coordinates") or [None, None]
                        p["longitude"] = coords[0]
                        p["latitude"] = coords[1]
                        villages.append(p)
            except Exception:
                villages = []
            self._cache["villages"] = villages
        return self._cache["villages"]

    def get_springs(self) -> List[Dict[str, Any]]:
        rows = self._csv("springs.csv")
        out = []
        for r in rows:
            try:
                lat = float(r.get("latitude") or 0)
                lon = float(r.get("longitude") or 0)
            except (TypeError, ValueError):
                continue  # skip rows with missing coordinates
            if not lat or not lon:
                continue
            out.append({
                "spring_id": (r.get("spring_id") or "").strip() or "UNKNOWN",
                "latitude": lat, "longitude": lon,
                "elevation_m": _to_float(r.get("elevation_m"), 600),
                "slope_deg": _to_float(r.get("slope_deg"), 12),
                "annual_rainfall_mm": _to_float(r.get("annual_rainfall_mm"), 1200),
                "soil_moisture_index": _to_float(r.get("soil_moisture_index"), 0.5),
                "land_use": (r.get("land_use") or "unknown").strip().lower() or "unknown",
                "geology": (r.get("geology") or "unknown").strip().lower() or "unknown",
                "distance_to_stream_m": _to_float(r.get("distance_to_stream_m"), 300),
                "lineament_density_index": _to_float(r.get("lineament_density_index"), 0.5),
                "groundwater_depth_m": _to_float(r.get("groundwater_depth_m"), 15),
                "recharge_suitability": _to_float(r.get("recharge_suitability"), 50),
                "discharge_lpm": _to_float(r.get("discharge_lpm"), 10),
                "seasonality": (r.get("seasonality") or "Unknown").strip(),
                "spring_type": (r.get("spring_type") or "spring").strip(),
                "nearby_village_id": (r.get("nearby_village_id") or "").strip(),
                "nearby_village": (r.get("nearby_village") or "").strip(),
                "state": (r.get("state") or "Jharkhand").strip(),
                "tribal_belt": (r.get("tribal_belt") or "Jharkhand-Odisha-Chhattisgarh Belt").strip(),
            })
        return out

    def get_wells(self) -> List[Dict[str, Any]]:
        rows = self._csv("wells.csv")
        out = []
        for r in rows:
            try:
                lat = float(r.get("latitude") or 0)
                lon = float(r.get("longitude") or 0)
            except (TypeError, ValueError):
                continue
            if not lat or not lon:
                continue
            out.append({
                "well_id": (r.get("well_id") or "").strip() or "UNKNOWN",
                "latitude": lat, "longitude": lon,
                "depth_m": _to_float(r.get("depth_m"), 20),
                "water_level_m": _to_float(r.get("water_level_m"), 10),
                "well_type": (r.get("well_type") or "well").strip(),
                "nearby_village_id": (r.get("nearby_village_id") or "").strip(),
                "nearby_village": (r.get("nearby_village") or "").strip(),
                "state": (r.get("state") or "Jharkhand").strip(),
                "tribal_belt": (r.get("tribal_belt") or "Jharkhand-Odisha-Chhattisgarh Belt").strip(),
            })
        return out

    def get_monthly_rainfall(self) -> List[Dict[str, Any]]:
        return self._csv("monthly_rainfall.csv")

    def get_annual_rainfall(self) -> List[Dict[str, Any]]:
        return self._csv("annual_rainfall.csv")

    def get_intervention_costs(self) -> List[Dict[str, Any]]:
        return self._csv("intervention_costs.csv")

    def get_boundary(self) -> Dict[str, Any]:
        for name in ("study_area.geojson", "villages.geojson"):
            path = os.path.join(self.data_dir, name)
            if os.path.exists(path):
                try:
                    with open(path, encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    continue
        return {"type": "FeatureCollection", "features": []}


class DemoDataProvider(CSVDatasetProvider):
    """Prototype provider backed by the synthetic demo dataset."""

    def __init__(self, data_dir: str):
        super().__init__(data_dir, label=DATA_LABEL)


class FutureGovernmentDataProvider(CSVDatasetProvider):
    """STUB for real integration (CGWB / state groundwater / IMD feeds).

    To go live:
      1. Subclass or reuse CSVDatasetProvider with DATA_DIR pointing at
         validated files (same column contract, see README + data/README).
      2. Or override the get_* methods to call a government API and map
         fields to the same dict shapes used below.
      3. Set source_label to the official source, e.g.
         "CGWB + IMD (validated)".
    Nothing in the API layer or frontend needs to change.
    """

    def __init__(self, data_dir: str, label: str = "Government source (validated)"):
        super().__init__(data_dir, label=label)
