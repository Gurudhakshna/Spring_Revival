"""Synthetic prototype dataset generator for JAL-RAKSHA AI.
DEMO DATA ONLY - replace with validated government/field data.
Deterministic (seeded) so backend ML + frontend are reproducible.
Uses stdlib only.
"""
import csv, json, math, os, random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
B = os.path.join(DATA, "boundary")
R = os.path.join(DATA, "rainfall")
W = os.path.join(DATA, "water")
I = os.path.join(DATA, "interventions")
A = os.path.join(DATA, "ai")
BD = os.path.join(ROOT, "backend", "data")
for d in (B, R, W, I, A, BD):
    os.makedirs(d, exist_ok=True)

rng = random.Random(42)

CENTER_LAT, CENTER_LON = 23.45, 84.95

VILLAGES = [
    ("VIL-001", "Hesatu", 23.512, 84.902, 1450, 285, "Gumla Sadar"),
    ("VIL-002", "Jariya", 23.498, 84.968, 980, 196, "Gumla Sadar"),
    ("VIL-003", "Kulhi", 23.471, 85.012, 1720, 344, "Raidih"),
    ("VIL-004", "Biren", 23.445, 84.891, 640, 128, "Gumla Sadar"),
    ("VIL-005", "Toto", 23.428, 84.945, 2100, 420, "Raidih"),
    ("VIL-006", "Silam", 23.412, 85.005, 870, 174, "Raidih"),
    ("VIL-007", "Ambatoli", 23.486, 84.925, 1230, 246, "Gumla Sadar"),
    ("VIL-008", "Kotam", 23.458, 84.985, 1890, 378, "Raidih"),
    ("VIL-009", "Puto", 23.431, 84.915, 520, 104, "Palkot"),
    ("VIL-010", "Gerda", 23.405, 84.962, 1560, 312, "Palkot"),
    ("VIL-011", "Chirgora", 23.525, 84.955, 760, 152, "Gumla Sadar"),
    ("VIL-012", "Banai", 23.448, 85.035, 1340, 268, "Raidih"),
]

LAND_USES = ["forest", "agroforestry", "agriculture", "grassland", "settlement", "barren"]
GEOLOGIES = ["fractured_rock", "weathered_granite", "sandstone", "shale", "clay"]
LU_SCORE = {"forest": 0.90, "agroforestry": 0.75, "agriculture": 0.55, "grassland": 0.50, "settlement": 0.25, "barren": 0.20}
GEO_SCORE = {"fractured_rock": 0.90, "weathered_granite": 0.75, "sandstone": 0.65, "shale": 0.45, "clay": 0.25}

def suitability(elev, slope, rain, sm, lu, geo, dist, lin, depth):
    rain_n = max(0.0, min(1.0, (rain - 700) / 900.0))
    slope_n = max(0.0, min(1.0, 1.0 - (slope - 2) / 33.0))
    dist_n = math.exp(-dist / 600.0)
    depth_n = max(0.0, min(1.0, 1.0 - (depth - 3) / 47.0))
    s = (0.20 * rain_n + 0.15 * slope_n + 0.15 * sm + 0.10 * LU_SCORE[lu]
         + 0.15 * GEO_SCORE[geo] + 0.10 * dist_n + 0.10 * lin + 0.05 * depth_n)
    return round(max(5.0, min(98.0, s * 100.0)), 1)

def jitter(lat, lon, dlat=0.012, dlon=0.012):
    return round(lat + rng.uniform(-dlat, dlat), 5), round(lon + rng.uniform(-dlon, dlon), 5)

# ---------- villages.geojson ----------
features = []
for vid, name, lat, lon, pop, hh, block in VILLAGES:
    elev = int(rng.uniform(450, 800))
    features.append({
        "type": "Feature",
        "properties": {"village_id": vid, "name": name, "population": pop,
                       "households": hh, "block": block, "elevation_m": elev,
                       "district": "Gumla (prototype)", "state": "Jharkhand (prototype)",
                       "source": "Synthetic Prototype Dataset"},
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
    })
villages_fc = {"type": "FeatureCollection",
               "metadata": {"study_area": "Prototype Study Area", "note": "DEMO DATA - Synthetic Prototype Dataset"},
               "features": features}
with open(os.path.join(B, "villages.geojson"), "w") as f:
    json.dump(villages_fc, f, indent=2)

# ---------- study area boundary ----------
boundary = {"type": "FeatureCollection", "features": [{
    "type": "Feature",
    "properties": {"name": "Prototype Study Area", "area_km2": 185, "source": "Synthetic Prototype Dataset"},
    "geometry": {"type": "Polygon", "coordinates": [[
        [84.86, 23.38], [85.06, 23.38], [85.06, 23.55], [84.86, 23.55], [84.86, 23.38]
    ]]}}]}
with open(os.path.join(B, "study_area.geojson"), "w") as f:
    json.dump(boundary, f, indent=2)
with open(os.path.join(BD, "study_area.geojson"), "w") as f:
    json.dump(boundary, f, indent=2)

# ---------- springs.csv ----------
spring_rows = []
vcoords = {v[0]: (v[2], v[3]) for v in VILLAGES}
vnames = {v[0]: v[1] for v in VILLAGES}
vids = list(vcoords.keys())
for i in range(1, 19):
    sid = f"SPR-{i:03d}"
    vid = vids[(i - 1) % len(vids)]
    vlat, vlon = vcoords[vid]
    lat, lon = jitter(vlat, vlon)
    elev = int(rng.uniform(480, 860))
    slope = round(rng.uniform(4, 28), 1)
    rain = int(rng.uniform(950, 1450))
    sm = round(rng.uniform(0.25, 0.9), 2)
    lu = rng.choices(LAND_USES, weights=[30, 20, 25, 10, 8, 7])[0]
    geo = rng.choices(GEOLOGIES, weights=[25, 25, 20, 18, 12])[0]
    dist = int(rng.uniform(40, 1100))
    lin = round(rng.uniform(0.1, 0.9), 2)
    depth = round(rng.uniform(5, 40), 1)
    score = suitability(elev, slope, rain, sm, lu, geo, dist, lin, depth)
    score = max(5.0, min(98.0, round(score + rng.gauss(0, 3), 1)))
    dis = round(max(2.0, 46 - score * 0.35 + rng.gauss(0, 4)), 1)
    seas = "Seasonal" if (score < 55 or rng.random() < 0.35) else "Perennial"
    stype = rng.choice(["seep", "fracture spring", "contact spring", "depression spring"])
    spring_rows.append([sid, lat, lon, elev, slope, rain, sm, lu, geo, dist, lin, depth,
                        score, dis, seas, stype, vid, vnames[vid]])
shead = ["spring_id", "latitude", "longitude", "elevation_m", "slope_deg", "annual_rainfall_mm",
         "soil_moisture_index", "land_use", "geology", "distance_to_stream_m",
         "lineament_density_index", "groundwater_depth_m", "recharge_suitability",
         "discharge_lpm", "seasonality", "spring_type", "nearby_village_id", "nearby_village"]
with open(os.path.join(W, "springs.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(shead); w.writerows(spring_rows)
with open(os.path.join(BD, "springs.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(shead); w.writerows(spring_rows)

# ---------- wells.csv ----------
well_rows = []
for i in range(1, 16):
    wid = f"WELL-{i:03d}"
    vid = vids[(i * 2) % len(vids)]
    vlat, vlon = vcoords[vid]
    lat, lon = jitter(vlat, vlon)
    depth = round(rng.uniform(8, 45), 1)
    wl = round(depth * rng.uniform(0.3, 0.8), 1)
    wtype = rng.choice(["open well", "borewell", "handpump"])
    well_rows.append([wid, lat, lon, depth, wl, wtype, vid, vnames[vid]])
whead = ["well_id", "latitude", "longitude", "depth_m", "water_level_m", "well_type",
         "nearby_village_id", "nearby_village"]
with open(os.path.join(W, "wells.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(whead); w.writerows(well_rows)

# ---------- rainfall ----------
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
mvals = [12, 18, 25, 38, 72, 215, 330, 310, 225, 85, 20, 8]
with open(os.path.join(R, "monthly_rainfall.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["month", "month_num", "rainfall_mm", "rainy_days"])
    for i, (m, v) in enumerate(zip(months, mvals), 1):
        w.writerow([m, i, v + rng.randint(-4, 4), max(0, int(v / 22) + rng.randint(-1, 1))])
annual = [(y, int(1210 + rng.gauss(0, 130))) for y in range(2015, 2025)]
with open(os.path.join(R, "annual_rainfall.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["year", "annual_rainfall_mm"])
    w.writerows(annual)

# ---------- intervention_costs.csv ----------
costs = [
    ["recharge_trench", "Recharge Trench", "per structure", 45000, 30, 200, 100, 0.14, "Contour-aligned trench to capture runoff and enhance infiltration."],
    ["check_dam", "Check Dam", "per structure", 280000, 1, 5, 1, 0.20, "Small barrier across seasonal stream to slow flow and recharge downstream springs."],
    ["percolation_pond", "Percolation Pond", "per pond", 180000, 1, 4, 1, 0.17, "Excavated pond that stores monsoon runoff for slow percolation."],
    ["contour_trench", "Contour Trench", "per hectare", 60000, 1, 20, 5, 0.12, "Staggered trenches along contours to reduce runoff on slopes."],
    ["vegetation_restoration", "Vegetation Restoration", "per hectare", 35000, 2, 30, 8, 0.10, "Native species plantation to improve soil moisture and baseflow."],
]
with open(os.path.join(I, "intervention_costs.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["type", "name", "unit", "unit_cost_inr", "min_qty", "max_qty", "default_qty", "effectiveness", "description"])
    w.writerows(costs)

# ---------- training / validation ----------
def gen_rows(n, seed):
    r = random.Random(seed)
    rows = []
    for _ in range(n):
        elev = round(r.uniform(400, 900), 1)
        slope = round(r.uniform(2, 35), 1)
        rain = int(r.uniform(800, 1600))
        sm = round(r.uniform(0.1, 0.95), 2)
        lu = r.choices(LAND_USES, weights=[30, 20, 25, 10, 8, 7])[0]
        geo = r.choices(GEOLOGIES, weights=[25, 25, 20, 18, 12])[0]
        dist = int(r.uniform(20, 1500))
        lin = round(r.uniform(0.05, 0.95), 2)
        depth = round(r.uniform(3, 50), 1)
        base = suitability(elev, slope, rain, sm, lu, geo, dist, lin, depth)
        target = max(5.0, min(98.0, round(base + r.gauss(0, 4.5), 1)))
        rows.append([elev, slope, rain, sm, lu, geo, dist, lin, depth, target])
    return rows

thead = ["elevation_m", "slope_deg", "annual_rainfall_mm", "soil_moisture_index", "land_use",
         "geology", "distance_to_stream_m", "lineament_density_index", "groundwater_depth_m",
         "recharge_suitability"]
with open(os.path.join(A, "training_data.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(thead); w.writerows(gen_rows(500, 101))
with open(os.path.join(A, "validation_data.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(thead); w.writerows(gen_rows(120, 202))

# copies for backend/data
import shutil
for src, dst in [
    (os.path.join(B, "villages.geojson"), os.path.join(BD, "villages.geojson")),
    (os.path.join(R, "monthly_rainfall.csv"), os.path.join(BD, "monthly_rainfall.csv")),
    (os.path.join(R, "annual_rainfall.csv"), os.path.join(BD, "annual_rainfall.csv")),
    (os.path.join(W, "wells.csv"), os.path.join(BD, "wells.csv")),
    (os.path.join(I, "intervention_costs.csv"), os.path.join(BD, "intervention_costs.csv")),
    (os.path.join(A, "training_data.csv"), os.path.join(BD, "training_data.csv")),
    (os.path.join(A, "validation_data.csv"), os.path.join(BD, "validation_data.csv")),
]:
    shutil.copyfile(src, dst)

print("DATASET OK:", len(spring_rows), "springs,", len(well_rows), "wells,", len(VILLAGES), "villages")
