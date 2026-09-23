"""JAL-RAKSHA AI — Pan-India Tribal Belt Synthetic Generator (LEVEL 2)
DEMO DATA ONLY — deterministic, stdlib only, seed=42
Generates 7 tribal belts x 18 springs = 126 springs + 84 villages + 105 wells
For SIH Winning: shows national scalability while keeping prototype scoring.
"""
import csv, json, math, os, random, shutil

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

# ========== 7 TRIBAL BELTS ==========
TRIBAL_REGIONS = [
    {
        "id": "jhk", "name": "Jharkhand-Odisha-Chhattisgarh Belt",
        "state": "Jharkhand", "district": "Gumla (prototype)",
        "center": (23.45, 84.95), "area_km2": 185,
        "rain_range": (950, 1450), "slope_range": (4, 28), "elev_range": (480, 860),
        "depth_range": (5, 40), "sm_range": (0.25, 0.90),
        "lu_weights": [30,20,25,10,8,7], "geo_weights": [25,25,20,18,12],
        "villages": [
            ("Hesatu", 23.512, 84.902, 1450, 285, "Gumla Sadar"),
            ("Jariya", 23.498, 84.968, 980, 196, "Gumla Sadar"),
            ("Kulhi", 23.471, 85.012, 1720, 344, "Raidih"),
            ("Biren", 23.445, 84.891, 640, 128, "Gumla Sadar"),
            ("Toto", 23.428, 84.945, 2100, 420, "Raidih"),
            ("Silam", 23.412, 85.005, 870, 174, "Raidih"),
            ("Ambatoli", 23.486, 84.925, 1230, 246, "Gumla Sadar"),
            ("Kotam", 23.458, 84.985, 1890, 378, "Raidih"),
            ("Puto", 23.431, 84.915, 520, 104, "Palkot"),
            ("Gerda", 23.405, 84.962, 1560, 312, "Palkot"),
            ("Chirgora", 23.525, 84.955, 760, 152, "Gumla Sadar"),
            ("Banai", 23.448, 85.035, 1340, 268, "Raidih"),
        ]
    },
    {
        "id": "mp", "name": "Madhya Pradesh Tribal Belt",
        "state": "Madhya Pradesh", "district": "Mandla-Dhar (prototype)",
        "center": (22.90, 78.60), "area_km2": 210,
        "rain_range": (700, 1100), "slope_range": (3, 18), "elev_range": (350, 650),
        "depth_range": (8, 35), "sm_range": (0.20, 0.75),
        "lu_weights": [15,15,40,15,10,5], "geo_weights": [15,20,35,15,15],
        "villages": [
            ("Mandla", 22.92, 78.62, 1650, 330, "Mandla"),
            ("Dindori", 22.88, 78.58, 890, 178, "Dindori"),
            ("Kukshi", 22.95, 78.65, 1320, 264, "Dhar"),
            ("Alirajpur", 22.85, 78.55, 780, 156, "Alirajpur"),
            ("Jhabua", 22.90, 78.70, 2100, 420, "Jhabua"),
            ("Betul", 22.87, 78.50, 560, 112, "Betul"),
            ("Seoni", 22.93, 78.68, 1420, 284, "Seoni"),
            ("Chhindwara", 22.84, 78.62, 980, 196, "Chhindwara"),
            ("Anuppur", 22.96, 78.55, 1120, 224, "Anuppur"),
            ("Umaria", 22.89, 78.72, 760, 152, "Umaria"),
            ("Shahdol", 22.91, 78.48, 1340, 268, "Shahdol"),
            ("Balaghat", 22.86, 78.66, 890, 178, "Balaghat"),
        ]
    },
    {
        "id": "rj", "name": "Rajasthan-Gujarat Bhil Belt",
        "state": "Rajasthan", "district": "Udaipur-Dahod (prototype)",
        "center": (23.80, 73.50), "area_km2": 310,
        "rain_range": (380, 700), "slope_range": (2, 12), "elev_range": (250, 450),
        "depth_range": (20, 50), "sm_range": (0.10, 0.45),
        "lu_weights": [5,5,20,10,15,45], "geo_weights": [5,10,15,20,50],
        "villages": [
            ("Udaipur Bhil", 23.82, 73.52, 1850, 370, "Udaipur"),
            ("Dungarpur", 23.78, 73.48, 920, 184, "Dungarpur"),
            ("Banswara", 23.85, 73.55, 1230, 246, "Banswara"),
            ("Dahod", 23.75, 73.45, 670, 134, "Dahod"),
            ("Jhadol", 23.88, 73.53, 2100, 420, "Jhadol"),
            ("Kotra", 23.77, 73.58, 480, 96, "Kotra"),
            ("Kherwara", 23.83, 73.48, 980, 196, "Kherwara"),
            ("Sagwara", 23.80, 73.60, 1120, 224, "Sagwara"),
            ("Aspur", 23.86, 73.42, 560, 112, "Aspur"),
            ("Sabarkantha", 23.79, 73.62, 780, 156, "Sabarkantha"),
            ("ChhotaUdepur", 23.84, 73.50, 1340, 268, "Chhota Udaipur"),
            ("Panchmahal", 23.76, 73.54, 890, 178, "Panchmahal"),
        ]
    },
    {
        "id": "ne", "name": "Northeast Tribal Belt",
        "state": "Meghalaya-Nagaland", "district": "Shillong-Kohima (prototype)",
        "center": (26.10, 92.90), "area_km2": 280,
        "rain_range": (1600, 2600), "slope_range": (12, 35), "elev_range": (600, 1400),
        "depth_range": (3, 20), "sm_range": (0.60, 0.95),
        "lu_weights": [45,25,10,10,5,5], "geo_weights": [40,30,15,10,5],
        "villages": [
            ("Shillong Khasi", 26.12, 92.92, 1450, 290, "East Khasi Hills"),
            ("Cherrapunji", 26.08, 92.88, 670, 134, "East Khasi Hills"),
            ("Kohima Naga", 26.15, 92.95, 1890, 378, "Kohima"),
            ("Mokokchung", 26.05, 92.85, 920, 184, "Mokokchung"),
            ("Aizawl Mizo", 26.18, 92.98, 2100, 420, "Aizawl"),
            ("Imphal Kuki", 26.02, 92.82, 560, 112, "Ukhrul"),
            ("Tawang Monpa", 26.14, 92.88, 480, 96, "Tawang"),
            ("Dimapur", 26.10, 92.94, 1230, 246, "Dimapur"),
            ("Wokha", 26.06, 92.91, 780, 156, "Wokha"),
            ("Tuensang", 26.16, 92.86, 890, 178, "Tuensang"),
            ("Jowai", 26.11, 92.96, 1120, 224, "West Jaintia"),
            ("Nongpoh", 26.03, 92.89, 1340, 268, "Ri Bhoi"),
        ]
    },
    {
        "id": "ghats", "name": "Western Ghats Tribal Belt",
        "state": "Kerala-Karnataka", "district": "Wayanad-Gadchiroli (prototype)",
        "center": (11.80, 76.10), "area_km2": 250,
        "rain_range": (1800, 3000), "slope_range": (8, 30), "elev_range": (600, 1100),
        "depth_range": (4, 18), "sm_range": (0.65, 0.95),
        "lu_weights": [50,20,10,10,5,5], "geo_weights": [20,40,20,10,10],
        "villages": [
            ("Wayanad Kurichiya", 11.82, 76.12, 1650, 330, "Wayanad"),
            ("Attappadi", 11.78, 76.08, 890, 178, "Palakkad"),
            ("Gadchiroli Madia", 11.85, 76.15, 1320, 264, "Gadchiroli"),
            ("Coorg Jenu", 11.75, 76.05, 780, 156, "Kodagu"),
            ("Banswara Ghat", 11.88, 76.13, 2100, 420, "Wayanad"),
            ("Nilambur", 11.77, 76.18, 560, 112, "Malappuram"),
            ("Sirsi Siddi", 11.83, 76.08, 1420, 284, "Uttara Kannada"),
            ("Dandeli", 11.80, 76.20, 980, 196, "Karwar"),
            ("Munnar Muthuvan", 11.86, 76.05, 1120, 224, "Idukki"),
            ("Agumbe Malekudiya", 11.79, 76.14, 760, 152, "Shivamogga"),
            ("Jawadhu Malayali", 11.81, 76.09, 1340, 268, "Tiruvannamalai"),
            ("Araku Bagata", 11.84, 76.11, 890, 178, "Alluri"),
        ]
    },
    {
        "id": "tn", "name": "Tamil Nadu-Andhra Tribal Belt",
        "state": "Tamil Nadu", "district": "Jawadhu-Araku (prototype)",
        "center": (13.50, 79.00), "area_km2": 190,
        "rain_range": (650, 1050), "slope_range": (5, 22), "elev_range": (300, 700),
        "depth_range": (10, 38), "sm_range": (0.25, 0.70),
        "lu_weights": [15,20,35,15,10,5], "geo_weights": [15,15,20,25,25],
        "villages": [
            ("Jawadhu", 13.52, 79.02, 1450, 290, "Tiruvannamalai"),
            ("Kalrayan", 13.48, 78.98, 670, 134, "Kallakurichi"),
            ("Pachamalai", 13.55, 79.05, 1890, 378, "Tiruchirappalli"),
            ("Araku Valley", 13.45, 78.95, 920, 184, "Alluri Sitharama"),
            ("Paderu", 13.58, 79.08, 2100, 420, "Alluri Sitharama"),
            ("Sittilingi", 13.47, 79.10, 560, 112, "Dharmapuri"),
            ("Kolli Hills", 13.53, 78.92, 1230, 246, "Namakkal"),
            ("Yelagiri", 13.50, 79.04, 980, 196, "Tirupattur"),
            ("Palamalai", 13.46, 79.06, 780, 156, "Coimbatore"),
            ("Chitteri", 13.56, 78.96, 890, 178, "Dharmapuri"),
            ("Shervaroy", 13.51, 79.08, 1120, 224, "Salem"),
            ("BR Hills Soliga", 13.49, 78.99, 1340, 268, "Chamarajanagar"),
        ]
    },
    {
        "id": "mh", "name": "Maharashtra-Chhattisgarh Central Belt",
        "state": "Maharashtra", "district": "Nandurbar-Bastar (prototype)",
        "center": (19.50, 80.20), "area_km2": 230,
        "rain_range": (850, 1350), "slope_range": (5, 25), "elev_range": (300, 650),
        "depth_range": (7, 32), "sm_range": (0.30, 0.80),
        "lu_weights": [25,20,30,10,10,5], "geo_weights": [20,25,25,15,15],
        "villages": [
            ("Nandurbar Bhil", 19.52, 80.22, 1650, 330, "Nandurbar"),
            ("Dhadgaon", 19.48, 80.18, 890, 178, "Nandurbar"),
            ("Toranmal", 19.55, 80.25, 1320, 264, "Nandurbar"),
            ("Bastar Muria", 19.45, 80.15, 780, 156, "Bastar"),
            ("Gadchiroli", 19.58, 80.28, 2100, 420, "Gadchiroli"),
            ("Dantewada", 19.47, 80.30, 560, 112, "Dantewada"),
            ("Sukma", 19.53, 80.18, 1420, 284, "Sukma"),
            ("Bijapur", 19.50, 80.24, 980, 196, "Bijapur"),
            ("Narayanpur", 19.46, 80.22, 1120, 224, "Narayanpur"),
            ("Kanker", 19.56, 80.15, 760, 152, "Kanker"),
            ("Rajura", 19.51, 80.28, 1340, 268, "Chandrapur"),
            ("Melghat Korku", 19.49, 80.19, 890, 178, "Amravati"),
        ]
    },
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

def jitter(lat, lon, dlat=0.018, dlon=0.018):
    return round(lat + rng.uniform(-dlat, dlat), 5), round(lon + rng.uniform(-dlon, dlon), 5)

# ---------- villages.geojson (84 villages) ----------
features = []
village_id_counter = 1
village_coords_map = {}  # vid -> (lat,lon,state,district,block,name)
village_name_map = {}
all_village_ids = []
for region in TRIBAL_REGIONS:
    for name, lat, lon, pop, hh, block in region["villages"]:
        vid = f"VIL-{village_id_counter:03d}"
        village_id_counter += 1
        elev = int(rng.uniform(region["elev_range"][0], region["elev_range"][1]))
        features.append({
            "type": "Feature",
            "properties": {
                "village_id": vid, "name": name, "population": pop,
                "households": hh, "block": block, "elevation_m": elev,
                "district": region["district"], "state": region["state"],
                "tribal_belt": region["name"], "belt_id": region["id"],
                "source": "Synthetic Prototype Dataset — Pan-India Tribal Belts"
            },
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
        })
        village_coords_map[vid] = (lat, lon, region["state"], region["district"], block, name, region)
        village_name_map[vid] = name
        all_village_ids.append(vid)

villages_fc = {
    "type": "FeatureCollection",
    "metadata": {"study_area": "Pan-India Tribal Belts (7 zones)", "note": "DEMO DATA - Synthetic Prototype Dataset - 7 tribal belts", "total_villages": len(features)},
    "features": features
}
with open(os.path.join(B, "villages.geojson"), "w") as f:
    json.dump(villages_fc, f, indent=2)
with open(os.path.join(BD, "villages.geojson"), "w") as f:
    json.dump(villages_fc, f, indent=2)

# ---------- study area boundary (7 polygons) ----------
boundary_features = []
for region in TRIBAL_REGIONS:
    clat, clon = region["center"]
    # ~20km x 20km box per belt (approx 0.18 degree)
    dlat, dlon = 0.09, 0.09
    coords = [[
        [clon - dlon, clat - dlat],
        [clon + dlon, clat - dlat],
        [clon + dlon, clat + dlat],
        [clon - dlon, clat + dlat],
        [clon - dlon, clat - dlat],
    ]]
    boundary_features.append({
        "type": "Feature",
        "properties": {"name": region["name"], "belt_id": region["id"], "state": region["state"], "district": region["district"], "area_km2": region["area_km2"], "source": "Synthetic Prototype Dataset — Pan-India"},
        "geometry": {"type": "Polygon", "coordinates": coords}
    })
boundary = {"type": "FeatureCollection", "features": boundary_features}
with open(os.path.join(B, "study_area.geojson"), "w") as f:
    json.dump(boundary, f, indent=2)
with open(os.path.join(BD, "study_area.geojson"), "w") as f:
    json.dump(boundary, f, indent=2)

# ---------- springs.csv (126 springs) ----------
spring_rows = []
spring_counter = 1
# Distribute villages per region for springs
for region in TRIBAL_REGIONS:
    # Get villages of this region
    region_vids = [vid for vid, (lat, lon, state, dist, block, name, reg) in village_coords_map.items() if reg["id"] == region["id"]]
    for i in range(18):
        sid = f"SPR-{spring_counter:03d}"
        spring_counter += 1
        vid = region_vids[i % len(region_vids)]
        vlat, vlon, vstate, vdist, vblock, vname, _ = village_coords_map[vid]
        lat, lon = jitter(vlat, vlon, dlat=0.015, dlon=0.015)
        elev = int(rng.uniform(region["elev_range"][0], region["elev_range"][1]))
        slope = round(rng.uniform(region["slope_range"][0], region["slope_range"][1]), 1)
        rain = int(rng.uniform(region["rain_range"][0], region["rain_range"][1]))
        sm = round(rng.uniform(region["sm_range"][0], region["sm_range"][1]), 2)
        lu = rng.choices(LAND_USES, weights=region["lu_weights"])[0]
        geo = rng.choices(GEOLOGIES, weights=region["geo_weights"])[0]
        dist = int(rng.uniform(40, 1100))
        lin = round(rng.uniform(0.1, 0.9), 2)
        depth = round(rng.uniform(region["depth_range"][0], region["depth_range"][1]), 1)
        score = suitability(elev, slope, rain, sm, lu, geo, dist, lin, depth)
        score = max(5.0, min(98.0, round(score + rng.gauss(0, 3), 1)))
        dis = round(max(2.0, 46 - score * 0.35 + rng.gauss(0, 4)), 1)
        seas = "Seasonal" if (score < 55 or rng.random() < 0.32) else "Perennial"
        stype = rng.choice(["seep", "fracture spring", "contact spring", "depression spring"])
        spring_rows.append([sid, lat, lon, elev, slope, rain, sm, lu, geo, dist, lin, depth,
                            score, dis, seas, stype, vid, vname, region["state"], region["name"]])

# Shuffle to mix regions in file but keep deterministic
# Do not shuffle - keep grouped by region for readability (JHK first etc)

shead = ["spring_id", "latitude", "longitude", "elevation_m", "slope_deg", "annual_rainfall_mm",
         "soil_moisture_index", "land_use", "geology", "distance_to_stream_m",
         "lineament_density_index", "groundwater_depth_m", "recharge_suitability",
         "discharge_lpm", "seasonality", "spring_type", "nearby_village_id", "nearby_village", "state", "tribal_belt"]
with open(os.path.join(W, "springs.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(shead); w.writerows(spring_rows)
with open(os.path.join(BD, "springs.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(shead); w.writerows(spring_rows)

# ---------- wells.csv (105 wells, 15 per region) ----------
well_rows = []
well_counter = 1
for region in TRIBAL_REGIONS:
    region_vids = [vid for vid, (lat, lon, state, dist, block, name, reg) in village_coords_map.items() if reg["id"] == region["id"]]
    for i in range(15):
        wid = f"WELL-{well_counter:03d}"
        well_counter += 1
        vid = region_vids[(i*2) % len(region_vids)]
        vlat, vlon, vstate, vdist, vblock, vname, _ = village_coords_map[vid]
        lat, lon = jitter(vlat, vlon, dlat=0.012, dlon=0.012)
        depth = round(rng.uniform(max(8, region["depth_range"][0]), min(45, region["depth_range"][1]+5)), 1)
        wl = round(depth * rng.uniform(0.3, 0.8), 1)
        wtype = rng.choice(["open well", "borewell", "handpump"])
        well_rows.append([wid, lat, lon, depth, wl, wtype, vid, vname, region["state"], region["name"]])

whead = ["well_id", "latitude", "longitude", "depth_m", "water_level_m", "well_type",
         "nearby_village_id", "nearby_village", "state", "tribal_belt"]
with open(os.path.join(W, "wells.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(whead); w.writerows(well_rows)
with open(os.path.join(BD, "wells.csv"), "w", newline="") as f:
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

# ---------- training / validation (diverse pan-India) ----------
def gen_rows(n, seed):
    r = random.Random(seed)
    rows = []
    for _ in range(n):
        # Pick a random tribal region to sample realistic distributions
        reg = r.choice(TRIBAL_REGIONS)
        elev = round(r.uniform(reg["elev_range"][0], reg["elev_range"][1]), 1)
        slope = round(r.uniform(reg["slope_range"][0], reg["slope_range"][1]), 1)
        rain = int(r.uniform(reg["rain_range"][0], reg["rain_range"][1]))
        sm = round(r.uniform(reg["sm_range"][0], reg["sm_range"][1]), 2)
        lu = r.choices(LAND_USES, weights=reg["lu_weights"])[0]
        geo = r.choices(GEOLOGIES, weights=reg["geo_weights"])[0]
        dist = int(r.uniform(20, 1500))
        lin = round(r.uniform(0.05, 0.95), 2)
        depth = round(r.uniform(reg["depth_range"][0], reg["depth_range"][1]), 1)
        base = suitability(elev, slope, rain, sm, lu, geo, dist, lin, depth)
        target = max(5.0, min(98.0, round(base + r.gauss(0, 4.5), 1)))
        rows.append([elev, slope, rain, sm, lu, geo, dist, lin, depth, target])
    return rows

thead = ["elevation_m", "slope_deg", "annual_rainfall_mm", "soil_moisture_index", "land_use",
         "geology", "distance_to_stream_m", "lineament_density_index", "groundwater_depth_m",
         "recharge_suitability"]
with open(os.path.join(A, "training_data.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(thead); w.writerows(gen_rows(800, 101))
with open(os.path.join(A, "validation_data.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(thead); w.writerows(gen_rows(200, 202))

# copies for backend/data
for src, dst in [
    (os.path.join(R, "monthly_rainfall.csv"), os.path.join(BD, "monthly_rainfall.csv")),
    (os.path.join(R, "annual_rainfall.csv"), os.path.join(BD, "annual_rainfall.csv")),
    (os.path.join(I, "intervention_costs.csv"), os.path.join(BD, "intervention_costs.csv")),
    (os.path.join(A, "training_data.csv"), os.path.join(BD, "training_data.csv")),
    (os.path.join(A, "validation_data.csv"), os.path.join(BD, "validation_data.csv")),
]:
    shutil.copyfile(src, dst)

print(f"PAN-INDIA DATASET OK: {len(spring_rows)} springs, {len(well_rows)} wells, {len(features)} villages across {len(TRIBAL_REGIONS)} belts")
for reg in TRIBAL_REGIONS:
    print(f"  - {reg['name']} ({reg['state']}): 18 springs, 12 villages")
