"""Prototype intervention simulator.

Labeled everywhere as "Prototype scenario estimate — requires field validation".
Never claims measured groundwater increase.
"""
from __future__ import annotations
import math
from typing import Dict, List


def _to_float(v, default=0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def simulate(cost_row: Dict, quantity: float, base_score: float,
             slope: float = 12, geology: str = "fractured_rock") -> Dict:
    qty = max(0.1, float(quantity or 1))
    unit_cost = _to_float(cost_row.get("unit_cost_inr"), 50000)
    effectiveness = _to_float(cost_row.get("effectiveness"), 0.12)
    default_qty = _to_float(cost_row.get("default_qty"), 1) or 1

    size_factor = max(0.4, min(1.6, qty / default_qty))
    # Site factor: moderate slopes + permeable geology respond best (prototype assumption)
    slope_factor = 1.0 - max(0.0, min(0.35, (max(0.0, slope - 15)) / 60.0))
    geo_factor = {"fractured_rock": 1.0, "weathered_granite": 0.95, "sandstone": 0.9,
                  "shale": 0.75, "clay": 0.6}.get((geology or "").lower(), 0.8)
    # Diminishing returns near the top of the scale
    headroom = max(0.15, 1.0 - base_score / 110.0)

    lift = effectiveness * 100.0 * size_factor * slope_factor * geo_factor * headroom
    lift = round(max(1.0, min(30.0, lift)), 1)
    after = round(max(0.0, min(97.0, base_score + lift)), 1)
    cost = int(unit_cost * qty)

    improvement = round(after - base_score, 1)
    if after >= 70:
        priority = "HIGH"
    elif after >= 50:
        priority = "MEDIUM"
    else:
        priority = "LOW"
    warn_count = (1 if slope > 25 else 0) + (1 if base_score < 40 else 0)
    risk = "HIGH" if warn_count >= 2 else ("MEDIUM" if warn_count == 1 else "LOW")
    confidence = round(max(0.55, min(0.88, 0.60 + effectiveness + improvement / 200.0)), 2)

    runoff_before = "High" if slope > 25 else ("Medium" if slope > 15 else "Low")
    runoff_after = "High" if (slope > 25 and lift < 8) else ("Medium" if slope > 15 else "Low")
    veg_before = round(max(5.0, min(90.0, 30 + base_score * 0.25)), 1)
    veg_after = round(max(5.0, min(95.0, veg_before + lift * 0.9)), 1)

    return {
        "intervention": cost_row.get("type"),
        "intervention_name": cost_row.get("name"),
        "quantity": qty,
        "unit": cost_row.get("unit"),
        "base_score": round(base_score, 1),
        "predicted_score": after,
        "improvement": improvement,
        "estimated_cost_inr": cost,
        "priority": priority,
        "risk": risk,
        "confidence": confidence,
        "comparison": {
            "headers": ["Metric", "Current", "Proposed"],
            "rows": [
                ["Recharge score", round(base_score, 1), after],
                ["Runoff risk", runoff_before, runoff_after],
                ["Vegetation cover", f"{veg_before}%", f"{veg_after}%"],
                ["Intervention cost", "₹0", f"₹{cost:,}"],
                ["Priority", "Medium" if 40 <= base_score < 65 else ("High" if base_score >= 65 else "Low"), priority.title()],
            ],
        },
        "disclaimer": "Prototype scenario estimate — requires field validation. Not a measured groundwater outcome.",
    }
