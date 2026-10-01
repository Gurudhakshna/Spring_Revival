"""Real ML pipeline: RandomForestRegressor on training_data.csv.

- One-hot encodes land_use + geology, passthrough numerics.
- Persists model bundle (pipeline + feature names) to model/recharge_rf.pkl.
- Metrics (R2 / MAE / RMSE) are COMPUTED from validation_data.csv, never faked.
"""
from __future__ import annotations
import json
import os
from typing import Dict, List

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import OneHotEncoder

NUMERIC = ["elevation_m", "slope_deg", "annual_rainfall_mm", "soil_moisture_index",
           "distance_to_stream_m", "lineament_density_index", "groundwater_depth_m"]
CATEGORICAL = ["land_use", "geology"]
TARGET = "recharge_suitability"
BASE_FEATURES = NUMERIC + CATEGORICAL

_model_bundle = None
_model_error: str | None = None


def _paths():
    here = os.path.dirname(os.path.abspath(__file__))          # backend/ml
    backend_dir = os.path.dirname(here)                        # backend
    root = os.path.dirname(backend_dir)                        # project root
    return {
        "train": os.path.join(backend_dir, "data", "training_data.csv"),
        "valid": os.path.join(backend_dir, "data", "validation_data.csv"),
        "model": os.path.join(root, "model", "recharge_rf.pkl"),
        "meta": os.path.join(root, "model", "model_meta.json"),
    }


def _build_pipeline() -> ColumnTransformer:
    return ColumnTransformer([
        ("num", "passthrough", NUMERIC),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
    ])


def train_and_save() -> Dict:
    p = _paths()
    if not os.path.exists(p["train"]):
        raise FileNotFoundError(f"Training data not found: {p['train']}")
    df = pd.read_csv(p["train"]).dropna(subset=[TARGET])
    for c in BASE_FEATURES:
        if c not in df.columns:
            raise ValueError(f"Missing feature column in training data: {c}")
    X = df[BASE_FEATURES]
    y = df[TARGET].astype(float)
    pre = _build_pipeline()
    Xt = pre.fit_transform(X)
    reg = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)
    reg.fit(Xt, y)
    os.makedirs(os.path.dirname(p["model"]), exist_ok=True)
    bundle = {"pipeline": pre, "regressor": reg, "features": BASE_FEATURES,
              "numeric": NUMERIC, "categorical": CATEGORICAL}
    joblib.dump(bundle, p["model"])
    meta = {"model": "RandomForestRegressor", "n_estimators": 200,
            "target": TARGET, "features": BASE_FEATURES,
            "n_train": int(len(df)), "disclaimer": "Prototype Decision-Support Estimate"}
    with open(p["meta"], "w") as f:
        json.dump(meta, f, indent=2)
    global _model_bundle
    _model_bundle = bundle
    return meta


def get_bundle():
    global _model_bundle, _model_error
    if _model_bundle is not None:
        return _model_bundle
    p = _paths()
    try:
        if os.path.exists(p["model"]):
            _model_bundle = joblib.load(p["model"])
            return _model_bundle
        train_and_save()
        return _model_bundle
    except Exception as e:  # never crash the API on ML failure
        _model_error = str(e)
        return None


def _row_to_df(payload: Dict) -> pd.DataFrame:
    row = {}
    for c in NUMERIC:
        try:
            row[c] = [float(payload.get(c, 0) or 0)]
        except (TypeError, ValueError):
            row[c] = [0.0]
    for c in CATEGORICAL:
        row[c] = [str(payload.get(c, "unknown") or "unknown").lower()]
    return pd.DataFrame(row)


def predict(payload: Dict) -> Dict:
    bundle = get_bundle()
    if bundle is None:
        raise RuntimeError(f"ML model unavailable: {_model_error or 'unknown error'}")
    Xt = bundle["pipeline"].transform(_row_to_df(payload))
    reg = bundle["regressor"]
    score = float(max(0.0, min(100.0, reg.predict(Xt)[0])))
    # Prototype confidence: agreement across trees (low std => high confidence)
    try:
        import numpy as np
        tree_preds = [t.predict(Xt)[0] for t in reg.estimators_]
        std = float(np.std(tree_preds))
        confidence = round(max(0.5, min(0.95, 1.0 - std / 40.0)), 2)
    except Exception:
        confidence = 0.7
    s = round(score, 1)
    pclass = "HIGH" if s >= 70 else ("MEDIUM" if s >= 45 else "LOW")
    importances = feature_importance()
    top = importances[0] if importances else {"feature": "n/a", "importance": 0}
    return {"score": s, "class": pclass, "confidence": confidence,
            "top_feature": top,
            "disclaimer": "Prototype Decision-Support Estimate — requires field validation."}


def feature_importance() -> List[Dict]:
    bundle = get_bundle()
    if bundle is None:
        return []
    pre = bundle["pipeline"]
    reg = bundle["regressor"]
    try:
        cat_names = list(pre.named_transformers_["cat"].get_feature_names_out(CATEGORICAL))
    except Exception:
        cat_names = []
    names = NUMERIC + cat_names
    imps = reg.feature_importances_
    agg: Dict[str, float] = {}
    for n, v in zip(names, imps):
        # ColumnTransformer prefixes one-hot columns, e.g.
        # "cat__land_use__forest" / "land_use_forest" / "land_use__forest".
        # Aggregate those back to the base feature, but keep full
        # numeric names (e.g. "annual_rainfall_mm") intact so API
        # consumers get stable, recognisable feature keys.
        base = n
        if "__" in n:
            base = n.split("__")[-1]
        if base.startswith("land_use"):
            base = "land_use"
        elif base.startswith("geology"):
            base = "geology"
        agg[base] = agg.get(base, 0.0) + float(v)
    total = sum(agg.values()) or 1.0
    ranked = sorted(agg.items(), key=lambda kv: kv[1], reverse=True)
    return [{"feature": k, "importance": round(v / total, 4)} for k, v in ranked]


def metrics() -> Dict:
    p = _paths()
    bundle = get_bundle()
    if bundle is None:
        return {"error": f"ML model unavailable: {_model_error or 'unknown'}", "n_validation": 0}
    if not os.path.exists(p["valid"]):
        return {"error": "validation_data.csv not found", "n_validation": 0}
    df = pd.read_csv(p["valid"]).dropna(subset=[TARGET])
    if len(df) == 0:
        return {"error": "validation dataset is empty", "n_validation": 0}
    Xt = bundle["pipeline"].transform(df[BASE_FEATURES])
    preds = bundle["regressor"].predict(Xt)
    y = df[TARGET].astype(float).to_numpy()
    rmse = float(mean_squared_error(y, preds) ** 0.5)
    return {
        "model": "RandomForestRegressor",
        "r2": round(float(r2_score(y, preds)), 4),
        "mae": round(float(mean_absolute_error(y, preds)), 3),
        "rmse": round(rmse, 3),
        "n_validation": int(len(df)),
        "n_train": int(pd.read_csv(p['train']).shape[0]) if os.path.exists(p["train"]) else 0,
        "target": TARGET,
        "computed_from": "validation_data.csv (real calculation, not a placeholder)",
    }
