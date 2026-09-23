# Data contracts — JAL-RAKSHA AI (synthetic prototype dataset)

> **Source: Synthetic Prototype Dataset.** Replace every file here with validated
> government/field data before operational use. Keep the same **column contracts**
> so no code changes are needed.

## Files

| Path | Key columns |
|------|-------------|
| `boundary/villages.geojson` | Feature props: `village_id, name, population, households, block, elevation_m`; Point geometry `[lon, lat]` |
| `boundary/study_area.geojson` | Polygon of the study extent |
| `rainfall/monthly_rainfall.csv` | `month, month_num, rainfall_mm, rainy_days` |
| `rainfall/annual_rainfall.csv` | `year, annual_rainfall_mm` |
| `water/springs.csv` | `spring_id, latitude, longitude, elevation_m, slope_deg, annual_rainfall_mm, soil_moisture_index, land_use, geology, distance_to_stream_m, lineament_density_index, groundwater_depth_m, recharge_suitability, discharge_lpm, seasonality, spring_type, nearby_village_id, nearby_village` |
| `water/wells.csv` | `well_id, latitude, longitude, depth_m, water_level_m, well_type, nearby_village_id, nearby_village` |
| `interventions/intervention_costs.csv` | `type, name, unit, unit_cost_inr, default_qty, min_qty, max_qty, effectiveness, description` |
| `ai/training_data.csv` | ML features + `recharge_suitability` (500 rows) |
| `ai/validation_data.csv` | Same schema, held-out (120 rows) |

## Rules

* Missing coordinates → row skipped (never crashes the map).
* Unknown `land_use`/`geology` → scored as `unknown` (0.40) with a data-uncertainty flag.
* Null numerics → safe defaults (rain 1200, slope 12, soil moisture 0.5, …).
* Regenerate the demo set: `python scripts/gen_data.py` (writes `data/` + `backend/data/`).
* Going live: same headers, real values, then delete `model/recharge_rf.pkl` to force retraining.
