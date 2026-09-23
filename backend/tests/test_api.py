"""Backend tests: recharge, ML, interventions, priorities, risks, health."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_dashboard_dynamic():
    r = client.get("/api/dashboard")
    d = r.json()
    assert d["total_springs"] == 126  # pan-India 7 belts x 18
    assert d["villages_covered"] == 84  # 7 belts x 12
    assert d["total_wells"] == 105  # 7 belts x 15
    assert 0 < d["avg_recharge_suitability"] <= 100
    assert d["high_priority_zones"] >= 0
    assert d["potential_intervention_sites"] >= 0


def test_geo_entities():
    assert client.get("/api/villages").json()["count"] == 84
    sp = client.get("/api/springs").json()
    assert sp["count"] == 126
    assert client.get("/api/wells").json()["count"] == 105
    rain = client.get("/api/rainfall").json()
    assert len(rain["monthly"]) == 12 and len(rain["annual"]) == 10
    det = client.get("/api/springs/SPR-001").json()
    assert det["spring_id"] == "SPR-001"
    assert "estimated_springshed" in det
    assert "priority" in det and "risk_flags" in det


def test_recharge_calculate():
    body = {"rainfall": 1200, "slope": 12, "soil_moisture": 0.7,
            "land_use": "forest", "geology": "fractured_rock",
            "distance_to_stream": 250, "lineament_density": 0.8,
            "groundwater_depth": 15}
    r = client.post("/api/recharge/calculate", json=body).json()
    assert r["class"] == "HIGH"
    assert abs(sum(r["factors"].values()) - r["score"]) < 0.6
    assert 0.5 <= r["confidence"] <= 0.95
    # unknown categories must not crash
    b2 = dict(body, land_use="mystery", geology="mystery")
    r2 = client.post("/api/recharge/calculate", json=b2).json()
    assert 0 <= r2["score"] <= 100
    # custom weights respected
    b3 = dict(body, weights={"rainfall": 50, "slope": 50, "soil_moisture": 0,
                             "land_use": 0, "geology": 0, "distance_to_stream": 0,
                             "lineament_density": 0, "groundwater_depth": 0})
    r3 = client.post("/api/recharge/calculate", json=b3).json()
    assert r3["weights"]["rainfall"] == 50.0


def test_recharge_map_and_detail():
    m = client.get("/api/recharge/map").json()
    assert len(m["points"]) == 126 and len(m["grid"]) == 112  # pan-India 16x7
    d = client.get("/api/recharge/SPR-001").json()
    assert d["spring_id"] == "SPR-001" and "factors" in d


def test_ml_predict_and_metrics():
    body = {"elevation_m": 600, "slope_deg": 12, "annual_rainfall_mm": 1200,
            "soil_moisture_index": 0.6, "land_use": "forest",
            "geology": "fractured_rock", "distance_to_stream_m": 250,
            "lineament_density_index": 0.6, "groundwater_depth_m": 15}
    p = client.post("/api/ml/predict", json=body).json()
    assert 0 <= p["score"] <= 100 and p["class"] in ("HIGH", "MEDIUM", "LOW")
    assert 0.5 <= p["confidence"] <= 0.95
    m = client.get("/api/ml/metrics").json()
    assert m["n_validation"] == 200  # pan-India expanded validation
    assert -1 <= m["r2"] <= 1 and m["mae"] >= 0 and m["rmse"] >= 0
    assert m["r2"] > 0.5, f"model underfit? r2={m['r2']}"
    fi = client.get("/api/ml/feature-importance").json()
    assert len(fi["features"]) >= 5
    assert abs(sum(f["importance"] for f in fi["features"]) - 1.0) < 0.01


def test_intervention_simulate_changes_with_params():
    base = {"intervention_type": "check_dam", "spring_id": "SPR-001", "quantity": 1}
    r1 = client.post("/api/interventions/simulate", json=base).json()
    r2 = client.post("/api/interventions/simulate",
                     json={**base, "quantity": 3}).json()
    assert r2["estimated_cost_inr"] > r1["estimated_cost_inr"]
    assert r2["predicted_score"] >= r1["predicted_score"]
    assert "Prototype scenario estimate" in r1["disclaimer"]
    assert "comparison" in r1
    bad = client.post("/api/interventions/simulate",
                      json={"intervention_type": "nope", "quantity": 1}).json()
    assert "detail" in bad


def test_priorities_and_risks():
    pr = client.get("/api/priorities").json()
    assert pr["count"] == 126
    scores = [p["priority_score"] for p in pr["priorities"]]
    assert scores == sorted(scores, reverse=True)
    assert "formula" in pr["priorities"][0] and "why" in pr["priorities"][0]
    rf = client.get("/api/risk-flags", params={"spring_id": "SPR-001"}).json()
    assert len(rf["flags"]) == 8
    allf = client.get("/api/risk-flags").json()
    assert allf["count"] == 126


def test_early_warning_status():
    s = client.get("/api/early-warning/status").json()
    assert s["available"] is True
    assert s["records"] == 416952
    assert s["stations"] == 6440
    assert s["target_missing"] == 0
    assert "1994" in s["time_min"] and "2025" in s["time_max"]


def test_early_warning_station_and_history():
    summ = client.get("/api/early-warning/summary", params={"limit": 5}).json()
    assert summ["count"] > 0
    assert summ["stations_assessed"] > 1000
    sid = summ["warnings"][0]["station_id"]
    det = client.get(f"/api/early-warning/stations/{sid}").json()
    assert det["station_id"] == sid
    assert det["risk_level"] in ("WATCH", "WARNING", "CRITICAL")
    assert det["latest_value"] is not None and det["trend"] is not None
    assert "reasons" in det and "reason_summary" in det
    assert det["history"]["count"] >= 10
    assert client.get("/api/early-warning/stations/NOPE-NONE").json()["detail"]


def test_early_warning_forecast_and_leadtime():
    summ = client.get("/api/early-warning/summary", params={"limit": 5}).json()
    sid = summ["warnings"][0]["station_id"]
    fc = client.post(f"/api/early-warning/forecast/{sid}",
                     json={"horizon_days": 30}).json()
    assert "forecast_target" in fc and fc["horizon_days"] == 30
    assert fc["validation"]["method"].startswith("chronological")
    lt = client.get("/api/early-warning/lead-time").json()
    assert ("possible" in lt) and ("events" in lt or "mean_days" in lt or "reason" in lt)
    if lt.get("possible"):
        assert lt["mean_days"] > 0 and lt["events"] >= 5
        assert "dry-out" not in lt["label"].lower() or "NOT" in lt["label"]
    else:
        assert "Insufficient" in lt["reason"]


def test_community_report_full_cycle():
    body = {"problem_type": "well_dry", "description": "Our well went dry",
            "village": "Test Village", "latitude": 23.46, "longitude": 84.96,
            "severity": "HIGH"}
    r = client.post("/api/community-reports", json=body).json()
    assert r["report_id"].startswith("JR-")
    assert r["status"] == "NEW"
    assert r["nearest_station_id"] is not None
    assert r["verification"]["station_id"] == r["nearest_station_id"]
    assert "pending field verification" in r["label"]
    rid = r["report_id"]
    assert client.get(f"/api/community-reports/{rid}").json()["report_id"] == rid
    lst = client.get("/api/community-reports").json()
    assert lst["count"] >= 1
    up = client.patch(f"/api/community-reports/{rid}",
                      json={"status": "UNDER_REVIEW"}).json()
    assert up["status"] == "UNDER_REVIEW"
    bad = client.patch(f"/api/community-reports/{rid}",
                       json={"status": "BOGUS"}).json()
    assert "detail" in bad
    cl = client.get("/api/community-reports/clusters").json()
    assert "clusters" in cl and "Prototype prioritization rule" in cl["rule"]
    rv = client.post(f"/api/community-reports/{rid}/reverify").json()
    assert rv["verification"]["station_id"] == r["nearest_station_id"]


def test_community_chat_demo():
    c1 = client.post("/api/community-reports/chat",
                     json={"session": {}, "message": "Our well went dry"}).json()
    assert c1["done"] is False and "village" in c1["reply"].lower()
    c2 = client.post("/api/community-reports/chat",
                     json={"session": c1["session"], "message": "Demo Village"}).json()
    assert "severity" in c2["reply"].lower()
    c3 = client.post("/api/community-reports/chat",
                     json={"session": c2["session"], "message": "HIGH"}).json()
    assert "SKIP" in c3["reply"] or "location" in c3["reply"].lower()
    c4 = client.post("/api/community-reports/chat",
                     json={"session": c3["session"], "message": "SKIP"}).json()
    assert c4["done"] is True and c4["report_id"].startswith("JR-")
    assert "no real whatsapp" in c4["note"].lower()
