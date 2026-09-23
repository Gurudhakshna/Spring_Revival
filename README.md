# JAL-RAKSHA AI — AI-Powered Spring Revival & Recharge Planning Platform

> **SIH26240** — AI-Based Spring Revival and Recharge Planning for Tribal Areas.
> Decision-support prototype. Every prediction is labelled **"Prototype Decision-Support Estimate"** —
> the system never claims a model guarantees groundwater recharge.
>
> **DEMO DATA — Replace with validated government/field data.** All bundled values are
> synthetic/illustrative, never real measurements.

## 1. Project overview

JAL-RAKSHA AI answers four questions for spring-shed management:

1. **Where are the springs?** — Springs, wells, villages on an interactive Leaflet map.
2. **What areas likely feed them?** — Estimated prototype springshed circle per spring (visual aid only, not officially delineated).
3. **Where is recharge more suitable?** — Transparent weighted recharge score (0–100) + Random Forest prediction.
4. **What intervention fits, with what estimated impact?** — Intervention simulator with side-by-side current-vs-proposed comparison.

## 2. SIH problem statement

Tribal habitations in hilly regions depend on springs that are drying or turning seasonal.
Field teams need a simple tool to **locate springs, prioritise revival sites, visualise water-related
GIS layers, and simulate recharge interventions** before committing field resources.

## 3. Architecture

```
Browser (React)  ──fetch /api/*──>  FastAPI (backend/)  ──> DemoDataProvider (backend/data/*.csv/*.geojson)
       ^                                │   ├─ services/recharge.py      (weighted scoring engine)
       │ Vite proxy                     │   ├─ services/interventions.py (simulator)
       │ /api -> :8000                  │   ├─ services/priority.py      (priority score)
                                        │   ├─ services/risks.py         (risk flags)
                                        │   └─ ml/model.py               (RandomForest, trained on training_data.csv)
```

* Frontend never reads data files directly — only via the backend (adapter pattern).
* Backend caches static datasets in memory at startup; ML model loads/trains once (`lifespan`).
* `DataProvider → CSVDatasetProvider → DemoDataProvider / FutureGovernmentDataProvider`
  (see `backend/services/data_provider.py`).

## 4. Technology stack

| Layer    | Choice |
|----------|--------|
| Frontend | React 18, TypeScript, Vite 5, Tailwind CSS, react-leaflet (Leaflet + OSM basemap), Recharts, react-router-dom |
| Backend  | Python, FastAPI, Pydantic v2, pandas, scikit-learn (RandomForestRegressor), joblib |
| Data     | CSV + GeoJSON + JSON (SQLite not needed — flat files suffice for the prototype) |
| Tests    | pytest (backend), `tsc -b && vite build` (frontend typecheck+build) |

## 5. Folder structure

```
jal-raksha/
├── frontend/            # React + Vite app (src/pages, src/components, src/api)
├── backend/             # FastAPI: main.py, api/routes.py, services/, ml/, models/, data/, tests/
├── data/                # Canonical demo dataset (boundary/, rainfall/, water/, interventions/, ai/)
├── model/               # Trained RandomForest bundle (recharge_rf.pkl) + model_meta.json
├── scripts/gen_data.py  # Deterministic synthetic dataset generator (stdlib only)
├── start.sh / start.bat # One-command local startup
└── README.md
```

`backend/data/` is a synced copy of `data/` that the API serves (regenerate with `python scripts/gen_data.py`).

## 6. How the AI works

* `RandomForestRegressor(n_estimators=200, random_state=42)` on 9 features
  (`elevation_m, slope_deg, annual_rainfall_mm, soil_moisture_index, land_use, geology,
  distance_to_stream_m, lineament_density_index, groundwater_depth_m`), target `recharge_suitability`.
* `land_use` + `geology` are one-hot encoded (`handle_unknown="ignore"` — unknown categories never crash).
* Confidence = tree-agreement heuristic (low std across trees ⇒ high confidence), clamped to 0.50–0.95.
* **Metrics (R² / MAE / RMSE) are computed live from `validation_data.csv`** — never hardcoded
  (`GET /api/ml/metrics`). Current demo values: R² ≈ 0.65, MAE ≈ 4.5, RMSE ≈ 5.6 (n=120).
* Feature importance = aggregated `feature_importances_` (`GET /api/ml/feature-importance`).

## 7. How recharge score is calculated

Weighted sum of 8 normalised factors (weights configurable per request, renormalised to 100):

| Factor | Weight | Normalisation (prototype) |
|--------|--------|---------------------------|
| Rainfall | 20% | (rain − 700)/900, clipped 0–1 |
| Slope | 15% | 1 − (slope − 2)/33 |
| Soil moisture | 15% | index 0–1 directly |
| Land use | 10% | forest .9 … barren .2 |
| Geology | 15% | fractured rock .9 … clay .25 |
| Distance to stream | 10% | exp(−dist/600) |
| Lineament density | 10% | index 0–1 directly |
| Groundwater depth | 5% | 1 − (depth − 3)/47 |

Classes: **HIGH ≥ 70, MEDIUM 45–70, LOW < 45**.
Priority = `0.40·recharge + 0.20·vulnerability + 0.15·population + 0.15·feasibility + 0.10·water_stress`
(formula returned in every response + "Why this location?" reasons).

## 8. API documentation

Base: `http://localhost:8000` · interactive docs: `http://localhost:8000/docs`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | `{"status":"ok"}` |
| GET | `/api/dashboard` | KPI aggregates (dynamic, never hardcoded) |
| GET | `/api/villages?search=` | Villages |
| GET | `/api/springs?search=&suitability_class=&seasonality=` | Springs + class + confidence |
| GET | `/api/springs/{id}` | Spring detail + priority + risk flags + estimated springshed |
| GET | `/api/wells` | Wells |
| GET | `/api/rainfall` | Monthly + annual rainfall |
| GET | `/api/recharge/map` | Spring scores + 110-point suitability grid + weights |
| GET | `/api/recharge/{id}` | Recharge breakdown for one spring |
| POST | `/api/recharge/calculate` | Weighted score (accepts optional `weights` override) |
| POST | `/api/ml/predict` | Random Forest score + class + confidence + top feature |
| GET | `/api/ml/metrics` | R² / MAE / RMSE computed from validation_data.csv |
| GET | `/api/ml/feature-importance` | Ranked feature importances |
| GET | `/api/interventions` | Intervention catalog + unit costs |
| POST | `/api/interventions/simulate` | Scenario estimate (base → predicted, cost, priority, risk, comparison table) |
| GET | `/api/priorities` | Ranked priority list with formula + reasons |
| GET | `/api/risk-flags?spring_id=` | 8 automatic risk/ok flags per spring |
| GET | `/api/training-data?limit=` | Training/validation samples for the Data page |
| GET | `/api/study-areas` | Study-area selector (prototype active, states reserved) |

Errors never leak tracebacks: `{"detail": "Unable to load … Please check the dataset."}`

## 9. Dataset documentation

Synthetic, deterministic (`seed=42`) Gumla-like plateau extent (~23.38–23.55 N, 84.86–85.06 E):

| File | Records | Contents |
|------|---------|----------|
| `villages.geojson` | 12 villages | id, name, population, households, block, elevation |
| `springs.csv` | 18 springs | coords, elevation, slope, rainfall, soil moisture, land use, geology, stream distance, lineament, GW depth, suitability, discharge, seasonality, nearby village |
| `wells.csv` | 15 wells | coords, depth, water level, type, nearby village |
| `monthly_rainfall.csv` | 12 months | month, rainfall_mm, rainy_days |
| `annual_rainfall.csv` | 10 years | year, annual_rainfall_mm |
| `intervention_costs.csv` | 5 types | recharge_trench, check_dam, percolation_pond, contour_trench, vegetation_restoration + unit costs |
| `training_data.csv` | 500 rows | ML features + `recharge_suitability` target |
| `validation_data.csv` | 120 rows | Same schema, held-out for metrics |

Regenerate: `python scripts/gen_data.py` (writes both `data/` and `backend/data/`).

## 10. Demo data disclaimer

* App badge: **"DEMO DATA — Replace with validated government/field data"** + **"DEMO MODE — Synthetic Data"** toggle.
* Recharge/ML outputs: **"Prototype Decision-Support Estimate"**.
* Interventions: **"Prototype scenario estimate — requires field validation"**.
* Springsheds: **"Estimated Prototype Springshed (not officially delineated)"**.

## 11. How to replace demo data

1. Collect validated springs/wells/villages/rainfall/recharge observations (CGWB, state groundwater, IMD, field surveys).
2. Match the column contracts in §9 (same headers; extra columns ignored).
3. Drop files into `backend/data/` (or point the provider at them) and delete `model/recharge_rf.pkl` — the model retrains automatically on next startup.
4. For live feeds: subclass `FutureGovernmentDataProvider` in `backend/services/data_provider.py` — no frontend changes needed.

## 12. How to run locally

Prerequisites: Python 3.10+ with `pip`, Node.js 18+ with `npm`.

```bash
# Option A — one command (Git Bash / Linux / macOS)
./start.sh

# Option B — Windows
start.bat

# Option C — manual
cd backend && pip install -r requirements.txt && python -m uvicorn main:app --port 8000
cd frontend && npm install && npm run dev
```

* Backend: http://localhost:8000 (docs: http://localhost:8000/docs)
* Frontend: http://localhost:5173 (Vite proxies `/api` → backend)

## 12b. New features (added on top of the prototype — existing UI untouched)

**FEATURE 1 — Groundwater Early Warning** (`/early-warning` page + Dashboard card).
Real dataset `backend/data/groundwater_india.csv` (416,952 records, 6,440 stations,
1994-01-05 → 2025-09-27; `target` used as-provided as groundwater level indicator in
metres, median 2.37, IQR −5.6…6.5, zero missing values). Per station: latest value,
MA7/MA30/MA90 (null when &lt;3 obs in window), 30-day + 365-day trend slopes
(least-squares, ≥5 obs), seasonal baseline (same-month ±1 median, ≥5 obs), rainfall
anomaly %, consecutive declining observations. Risk NORMAL/WATCH/WARNING/CRITICAL
from a configurable score (`backend/services/early_warning.py::THRESHOLDS`, overridable
via POST /api/early-warning/summary). Live results: **453 active warnings**,
lead-time **validated on real history: 69 events, median 10 days, mean 21.7 days**
(GET /api/early-warning/lead-time) — labelled "Groundwater stress warning lead time",
never a dry-out prediction. Forecast = trend + seasonal blend with chronological
holdout MAE; 80% interval shown only when holdout residuals justify it.

**FEATURE 2 — Villager Community Reporting** (`/reports` page, polling every 30s).
"Report Water Problem" form → `JR-YYYY-NNNN` id → stored in
`backend/data/community_reports.json` (no second database — same flat-file approach).
Each report auto-links the nearest monitoring station (haversine) and attaches its
live warning status with an honest consistent/mismatch verdict, always labelled
"Community reported — pending field verification." Status flow
NEW → UNDER_REVIEW → ESCALATED → RESOLVED; clusters (1 = signal, 2–3 = elevated,
4+ = high-priority investigation, labelled prototype rule); report + station markers
on the existing map; "Simulate Intervention" opens the existing planner;
WhatsApp/SMS demo at POST /api/community-reports/chat (simulation only).

Tests:

```bash
cd backend && python -m pytest tests/ -q        # 8 passed
cd frontend && npm run build                     # tsc + vite build
```

## 13. Future real-data integration

* `Study Area` selector already reserves Tamil Nadu, Kerala, Karnataka, Odisha, Jharkhand, Northeast.
* Swap provider label to e.g. `"CGWB + IMD (validated)"`; badges/disclaimers update automatically from `source_label`.
* Add auth/rate-limiting (none needed for local prototype), PostGIS for large extents, background retraining jobs.

## 14. Limitations

* Synthetic magnitudes — illustrative, not measurements.
* Springsheds are visual estimates; recharge grid is a sampled prototype layer.
* Intervention lift is a heuristic (effectiveness × size × site × headroom), not a measured outcome.
* No authentication, no rate limiting, single-process server — fine for local demo, not production.

## 15. Field validation requirements

Before any operational use: hydrogeologist review, spring discharge monitoring across seasons,
geophysical confirmation of recharge zones, community consent, post-monsoon impact review,
and replacement of every synthetic file with validated data.
