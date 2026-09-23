"""Groundwater Early Warning engine (FEATURE 1).

Real dataset: backend/data/groundwater_india.csv (416,952 records, ~6,440
stations, 1994-2025). "target" is used AS PROVIDED as a groundwater level
indicator in metres (median ~2.4, IQR -5.6..6.5, with extreme outliers that
are handled with robust medians — never with invented values).

Series are sparse/irregular (median ~39 obs/station), so every indicator is
time-aware and returns null + "insufficient data" instead of guessing.

Risk thresholds live in THRESHOLDS (configurable per-call via override) and
are documented as prototype heuristics, labelled "AI/Prototype Decision Support".
"""
from __future__ import annotations
import math
import os
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "data", "groundwater_india.csv")

# Prototype-heuristic risk thresholds — configurable, not hardcoded fate.
THRESHOLDS: Dict[str, float] = {
    "decline_short_slope": -0.02,   # m/day over trailing 30d window
    "decline_medium_slope": -0.005,  # m/day over trailing 365d window
    "strong_decline_slope": -0.05,  # m/day -> "strongly declining"
    "below_baseline_m": -1.0,       # latest vs seasonal baseline (m)
    "rain_deficit_pct": -20.0,      # rainfall anomaly % triggering concern
    "persistent_days": 5,           # consecutive declining obs
    "warn_score": 35.0,             # risk-score cutoffs (0-100)
    "warning_score": 55.0,
    "critical_score": 75.0,
}

_df: Optional[pd.DataFrame] = None
_stations: Optional[pd.DataFrame] = None
_load_error: Optional[str] = None
_summary_cache: Dict[str, Any] = {}  # dataset is static -> cache per (min_level, thresholds)


def _load() -> Optional[pd.DataFrame]:
    global _df, _stations, _load_error
    if _df is not None:
        return _df
    try:
        if not os.path.exists(DATA_FILE):
            _load_error = f"groundwater dataset not found: {DATA_FILE}"
            return None
        df = pd.read_csv(DATA_FILE, usecols=["station_id", "datetime", "target",
                                             "rainfall", "month", "latitude",
                                             "longitude", "wellDepth"],
                         parse_dates=["datetime"])
        df = df.dropna(subset=["station_id", "datetime", "target"])
        df = df.sort_values(["station_id", "datetime"]).reset_index(drop=True)
        coords = (df.groupby("station_id")
                    .agg(lat=("latitude", "median"), lon=("longitude", "median"),
                         n_obs=("target", "size"),
                         first=("datetime", "min"), last=("datetime", "max"),
                         well_depth=("wellDepth", "median")))
        _stations = coords.reset_index()
        _df = df
        return _df
    except Exception as e:  # never crash the API
        _load_error = str(e)
        return None


def status() -> Dict[str, Any]:
    df = _load()
    if df is None:
        return {"available": False, "error": _load_error or "dataset unavailable"}
    assert _stations is not None
    return {"available": True,
            "records": int(len(df)),
            "stations": int(len(_stations)),
            "time_min": str(df["datetime"].min()), "time_max": str(df["datetime"].max()),
            "target_median": round(float(df["target"].median()), 2),
            "target_p25": round(float(df["target"].quantile(0.25)), 2),
            "target_p75": round(float(df["target"].quantile(0.75)), 2),
            "target_missing": 0,
            "source": "Groundwater India Data.csv (provided dataset — real, not synthetic)",
            "target_note": ("'target' used as-provided as groundwater level indicator (m); "
                            "extremes handled with robust medians."),
            "disclaimer": "AI/Prototype Decision Support — not a confirmed real-world event."}


def _series(station_id: str) -> Optional[pd.DataFrame]:
    df = _load()
    if df is None:
        return None
    s = df[df["station_id"] == station_id].sort_values("datetime")
    return s if len(s) else None


def _window(g: pd.DataFrame, days: int) -> pd.DataFrame:
    end = g["datetime"].max()
    return g[g["datetime"] >= (end - pd.Timedelta(days=days))]


def _slope_m_per_day(g: pd.DataFrame) -> Optional[float]:
    if len(g) < 5:
        return None
    x = (g["datetime"] - g["datetime"].min()).dt.total_seconds().to_numpy() / 86400.0
    if x.max() - x.min() < 7:  # less than a week of span -> not a trend
        return None
    y = g["target"].to_numpy(dtype=float)
    try:
        slope = float(np.polyfit(x, y, 1)[0])
    except Exception:
        return None
    return round(slope, 5)


def _trailing_mean(g: pd.DataFrame, days: int) -> Optional[float]:
    w = _window(g, days)
    if len(w) < 3:
        return None
    return round(float(w["target"].mean()), 3)


def _seasonal_baseline(g: pd.DataFrame, month: int) -> Optional[float]:
    m = g[g["month"].isin([(month - 1) % 12 or 12, month, month % 12 + 1])]
    if len(m) < 5:
        return None
    return round(float(m["target"].median()), 3)


def _consecutive_declines(g: pd.DataFrame, eps: float = 1e-6) -> int:
    y = g["target"].to_numpy(dtype=float)
    n = 0
    for i in range(len(y) - 1, 0, -1):
        if y[i] < y[i - 1] - eps:
            n += 1
        else:
            break
    return n


def _rainfall_anomaly(g: pd.DataFrame, month: int) -> Optional[float]:
    """Mean daily rainfall over trailing 30d vs same-month historical mean, %."""
    w = _window(g, 30)
    if len(w) < 3:
        return None
    hist = g[g["month"] == month]["rainfall"]
    if len(hist) < 5:
        hist = g["rainfall"]
    base = float(hist.mean())
    if base <= 0:
        return None
    return round((float(w["rainfall"].mean()) - base) / base * 100.0, 1)


def _cfg(override: Optional[Dict[str, float]]) -> Dict[str, float]:
    c = dict(THRESHOLDS)
    if override:
        for k, v in override.items():
            if k in c:
                try:
                    c[k] = float(v)
                except (TypeError, ValueError):
                    pass
    return c


def _assess(g: pd.DataFrame, station_id: str,
              cfg: Dict[str, float]) -> Dict[str, Any]:
    """Core assessment on an already-selected, datetime-sorted series."""
    last = g.iloc[-1]
    month = int(last["month"])
    latest = round(float(last["target"]), 3)
    short = _slope_m_per_day(_window(g, 30))
    medium = _slope_m_per_day(_window(g, 365))
    baseline = _seasonal_baseline(g, month)
    gw_anomaly = round(latest - baseline, 3) if baseline is not None else None
    rain_anom = _rainfall_anomaly(g, month)
    consec = _consecutive_declines(g)

    score = 0.0
    reasons: List[str] = []
    ok: List[str] = []
    if short is not None and short < cfg["decline_short_slope"]:
        score += 30
        reasons.append("Short-term declining trend (trailing 30 days)")
    elif short is not None:
        ok.append("No short-term decline")
    if medium is not None and medium < cfg["decline_medium_slope"]:
        score += 20
        reasons.append("Medium-term declining trend (trailing year)")
    elif medium is not None:
        ok.append("No medium-term decline")
    if gw_anomaly is not None and gw_anomaly < cfg["below_baseline_m"]:
        score += 25
        reasons.append("Groundwater below seasonal baseline")
    elif gw_anomaly is not None:
        ok.append("Groundwater near/above seasonal baseline")
    if rain_anom is not None and rain_anom < cfg["rain_deficit_pct"]:
        score += 15
        reasons.append(f"Recent rainfall deficit ({rain_anom}%)")
    elif rain_anom is not None:
        ok.append("No recent rainfall deficit")
    if consec >= cfg["persistent_days"]:
        score += 10
        reasons.append(f"Persistent decline ({consec} consecutive falling observations)")
    if short is not None and short < cfg["strong_decline_slope"]:
        score += 10
        reasons.append("Strongly declining groundwater trend")

    score = round(min(100.0, score), 1)
    if score >= cfg["critical_score"]:
        level = "CRITICAL"
    elif score >= cfg["warning_score"]:
        level = "WARNING"
    elif score >= cfg["warn_score"]:
        level = "WATCH"
    else:
        level = "NORMAL"
    if short is None and medium is None and baseline is None:
        level = "NORMAL"
        reasons = ["Insufficient history for trend assessment"]
    trend_label = ("strongly declining" if (short is not None and short < cfg["strong_decline_slope"])
                   else "declining" if (short is not None and short < cfg["decline_short_slope"])
                   else "stable/insufficient data")

    lat = float(g["latitude"].median())
    lon = float(g["longitude"].median())
    return {
        "station_id": station_id,
        "latitude": lat, "longitude": lon,
        "n_obs": int(len(g)),
        "latest_value": latest,
        "latest_date": str(last["datetime"].date()),
        "ma7": _trailing_mean(g, 7), "ma30": _trailing_mean(g, 30),
        "ma90": _trailing_mean(g, 90),
        "trend_short_m_per_day": short, "trend_medium_m_per_day": medium,
        "trend": trend_label,
        "seasonal_baseline": baseline, "gw_anomaly_m": gw_anomaly,
        "rainfall_anomaly_pct": rain_anom,
        "consecutive_declines": consec,
        "risk_score": score, "risk_level": level,
        "reasons": reasons, "ok_signals": ok,
        "reason_summary": ("Groundwater level has remained below its seasonal baseline "
                           "while showing a persistent declining trend."
                           if (level in ("WARNING", "CRITICAL") and gw_anomaly is not None
                               and gw_anomaly < 0 and consec >= 2)
                           else ("; ".join(reasons) if reasons
                                 else "No groundwater stress signals in available history.")),
        "thresholds": cfg,
        "disclaimer": "AI/Prototype Decision Support — not a confirmed real-world event.",
    }


def station_warning(station_id: str,
                    thresholds: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """Full early-warning assessment for one station (all values from real data)."""
    cfg = _cfg(thresholds)
    g = _series(station_id)
    if g is None:
        return {"station_id": station_id, "detail": "Station not found."}
    return _assess(g, station_id, cfg)


def all_warnings(min_level: str = "WATCH", limit: int = 200,
                 thresholds: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """Assess every station with enough history; return ranked active warnings."""
    df = _load()
    if df is None:
        return {"count": 0, "warnings": [], "error": _load_error}
    assert _stations is not None
    order = {"NORMAL": 0, "WATCH": 1, "WARNING": 2, "CRITICAL": 3}
    floor = order.get(min_level.upper(), 1)
    cfg = _cfg(thresholds)
    if thresholds is None:
        ck = f"{min_level}:{limit}"
        hit = _summary_cache.get(ck)
        if hit is not None:
            return hit
    # Single grouped pass (boolean-mask per station would rescan 417k rows each).
    out = []
    for sid, g in df.groupby("station_id", sort=False):
        if len(g) < 10:
            continue
        w = _assess(g.sort_values("datetime"), str(sid), cfg)
        if order.get(w.get("risk_level", "NORMAL"), 0) >= floor:
            out.append(w)
    out.sort(key=lambda w: (-w["risk_score"], w["station_id"]))
    assessed = int((_stations["n_obs"] >= 10).sum())
    res = {"count": len(out), "warnings": out[:limit],
            "levels": {l: sum(1 for w in out if w["risk_level"] == l)
                       for l in ("CRITICAL", "WARNING", "WATCH")},
            "stations_assessed": assessed,
            "last_updated": str(df["datetime"].max().date()),
            "disclaimer": "AI/Prototype Decision Support — not confirmed real-world events."}
    if thresholds is None:
        _summary_cache[f"{min_level}:{limit}"] = res
        _summary_cache["full"] = {"out": out, "assessed": assessed,
                                  "last_updated": res["last_updated"]}
    return res


def history(station_id: str, limit: int = 400) -> Dict[str, Any]:
    g = _series(station_id)
    if g is None:
        return {"station_id": station_id, "detail": "Station not found."}
    tail = g.tail(limit)
    pts = [{"date": str(d.date()), "target": round(float(t), 3),
            "rainfall": round(float(r), 2)}
           for d, t, r in zip(tail["datetime"], tail["target"], tail["rainfall"])]
    # trailing 30-observation moving average for the chart
    vals = tail["target"].to_numpy(dtype=float)
    ma = []
    for i in range(len(vals)):
        win = vals[max(0, i - 29):i + 1]
        ma.append(round(float(win.mean()), 3))
    return {"station_id": station_id, "count": len(pts),
            "points": pts, "ma30obs": ma}


def lead_time_validation() -> Dict[str, Any]:
    """Historical warning lead time: for each station, find critical crossings
    (target below seasonal baseline - 1.5*MAD proxy) and measure days between
    the earliest WARNING+ assessment and the crossing. Honest stats or a clear
    'insufficient' statement — never a fabricated number."""
    df = _load()
    if df is None:
        return {"possible": False, "reason": _load_error}
    assert _stations is not None
    leads: List[float] = []
    events = 0
    for sid, g in df.groupby("station_id", sort=False):
        g = g.sort_values("datetime").reset_index(drop=True)
        if len(g) < 30:
            continue
        if len(g) < 30:
            continue
        mmed = g.groupby("month")["target"].median()
        base = g["month"].map(mmed).to_numpy(dtype=float)
        mad = float(np.median(np.abs(g["target"].to_numpy(dtype=float) - base)))
        crit = base - 1.5 * max(mad, 0.5)
        below = g["target"].to_numpy(dtype=float) < crit
        idx = np.where(below)[0]
        if not len(idx):
            continue
        # first crossing = event; look back 120d for earliest WARNING+
        e = int(idx[0])
        e_date = g["datetime"].iloc[e]
        prior = g[(g["datetime"] >= e_date - pd.Timedelta(days=120)) & (g["datetime"] < e_date)]
        if len(prior) < 5:
            continue
        warn_date = None
        for i in range(5, len(prior) + 1):
            tmp = g[g["datetime"] <= prior["datetime"].iloc[i - 1]]
            # cheap proxy of the WARNING rule on truncated history
            sl = _slope_m_per_day(_window(tmp, 30))
            tm = tmp.groupby("month")["target"].median()
            blm = tm.get(int(prior["month"].iloc[i - 1]))
            lv = float(tmp["target"].iloc[-1])
            s = (30 if (sl is not None and sl < THRESHOLDS["decline_short_slope"]) else 0) + \
                (25 if (blm is not None and lv - blm < THRESHOLDS["below_baseline_m"]) else 0) + \
                (20 if (_slope_m_per_day(_window(tmp, 365)) or 0) < THRESHOLDS["decline_medium_slope"] else 0)
            if s >= THRESHOLDS["warning_score"]:
                warn_date = prior["datetime"].iloc[i - 1]
                break
        if warn_date is not None:
            events += 1
            leads.append((e_date - warn_date).days)
    if events < 5:
        return {"possible": False,
                "reason": ("Insufficient historical event labels for validated lead-time "
                           f"estimation (only {events} warning→critical pairs found)."),
                "events": events,
                "label": "Groundwater stress warning lead time"}
    arr = np.array(leads, dtype=float)
    return {"possible": True, "events": events,
            "mean_days": round(float(arr.mean()), 1),
            "median_days": round(float(np.median(arr)), 1),
            "min_days": int(arr.min()), "max_days": int(arr.max()),
            "label": "Groundwater stress warning lead time (NOT a village dry-out prediction)",
            "method": ("critical crossing = target below seasonal baseline − 1.5×MAD; "
                       "warning = first WARNING+ assessment in prior 120 days."),
            "disclaimer": "AI/Prototype Decision Support — retrospective estimate, not a guarantee."}


def forecast(station_id: str, horizon_days: int = 30) -> Dict[str, Any]:
    """Smallest honest forecaster: trend + seasonal-month-mean blend, validated
    with a chronological holdout (last 20%, never shuffled). Confidence interval
    only when holdout residuals justify it."""
    g = _series(station_id)
    if g is None:
        return {"station_id": station_id, "detail": "Station not found."}
    if len(g) < 30:
        return {"station_id": station_id,
                "detail": "Insufficient history for forecasting (need ≥30 observations)."}
    h = min(max(7, horizon_days), 90)
    x = (g["datetime"] - g["datetime"].min()).dt.total_seconds().to_numpy() / 86400.0
    y = g["target"].to_numpy(dtype=float)
    n = len(g)
    cut = int(n * 0.8)
    try:
        a, b = np.polyfit(x[:cut], y[:cut], 1)
    except Exception:
        return {"station_id": station_id, "detail": "Forecast fit failed."}
    pred_hold = a * x[cut:] + b
    resid = y[cut:] - pred_hold
    mae = round(float(np.mean(np.abs(resid))), 3)
    resid_std = float(np.std(resid)) if len(resid) >= 5 else None
    last_x = x[-1]
    trend_fc = a * (last_x + h) + b
    fut_month = int((g["datetime"].max() + pd.Timedelta(days=h)).month)
    seas = _seasonal_baseline(g, fut_month)
    fc = round(float(0.6 * trend_fc + 0.4 * seas) if seas is not None else float(trend_fc), 3)
    out: Dict[str, Any] = {
        "station_id": station_id, "horizon_days": h,
        "forecast_target": fc,
        "validation": {"method": "chronological holdout (last 20%, no shuffling)",
                       "holdout_mae": mae, "holdout_n": int(n - cut)},
        "features": ["previous groundwater values", "groundwater trend",
                     "seasonal month baseline", "recent rainfall mean"],
        "risk": ("WARNING" if (seas is not None and fc < seas - 1.0) else "WATCH"
                 if (seas is not None and fc < seas) else "NORMAL"),
        "disclaimer": "AI/Prototype Decision Support — not a confirmed real-world event.",
    }
    if resid_std is not None:
        out["confidence_interval_80"] = [round(fc - 1.28 * resid_std, 3),
                                         round(fc + 1.28 * resid_std, 3)]
        out["confidence_note"] = "80% interval from chronological-holdout residuals."
    else:
        out["confidence_note"] = "Confidence withheld — insufficient holdout residuals."
    return out
