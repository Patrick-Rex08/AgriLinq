import urllib.request
import urllib.error
import json
import pytest

BASE = "http://127.0.0.1:8000/api"

def get(path):
    try:
        with urllib.request.urlopen(f"{BASE}{path}") as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

def patch(path, data):
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="PATCH"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

def post(path, data):
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

def delete(path):
    req = urllib.request.Request(f"{BASE}{path}", method="DELETE")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def test_forecast_sufficient_data():
    """1. Test forecast generation when sufficient historical orders exist."""
    s, res = get("/ai/forecast?crop=Wheat&days=14")
    assert s == 200
    assert res["crop_name"] == "Wheat"
    assert res["forecast_period_days"] == 14
    assert res["estimated_demand_kg"] > 0
    assert isinstance(res["timeline"], list)
    assert len(res["timeline"]) > 0
    # In database with seeded wheat orders, data_basis should indicate historical linear fit
    if res["historical_orders_count"] >= 3:
        assert res["is_baseline_estimate"] is False
        assert "Linear Trend" in res["data_basis"]


def test_forecast_insufficient_data():
    """2. Test safe handling of insufficient historical data (uncommon crop)."""
    s, res = get("/ai/forecast?crop=DragonfruitRare&days=7")
    assert s == 200
    assert res["historical_orders_count"] < 3
    assert res["is_baseline_estimate"] is True
    assert "Insufficient" in res["data_basis"]
    assert len(res["timeline"]) > 0


def test_forecast_validation_errors():
    """Test validation errors on forecast horizon parameters."""
    s, res = get("/ai/forecast?crop=Wheat&days=2")  # days < 7 must fail with 422
    assert s == 422

    s, res = get("/ai/forecast?crop=Wheat&days=100")  # days > 60 must fail with 422
    assert s == 422


def test_price_intelligence_msp_available():
    """3. Test price intelligence for MSP-covered commodity (Wheat)."""
    s, res = get("/ai/price-intelligence?crop=Wheat")
    assert s == 200
    assert res["crop_name"] == "Wheat"
    msp_info = res["msp_intelligence"]
    assert msp_info["benchmark_available"] is True
    assert msp_info["msp_price_inr_per_kg"] == 22.75
    assert "CACP" in msp_info["source"]
    assert msp_info["status"] in ["ABOVE_MSP", "NEAR_MSP", "BELOW_MSP"]


def test_price_intelligence_no_msp():
    """4. Test price intelligence for non-MSP commodity (Potato/Tomato)."""
    s, res = get("/ai/price-intelligence?crop=Potato")
    assert s == 200
    msp_info = res["msp_intelligence"]
    assert msp_info["benchmark_available"] is False
    assert msp_info["msp_price_inr_per_kg"] is None
    assert msp_info["status"] == "NO_OFFICIAL_MSP"
    assert "Perishable" in msp_info["source"]


def test_anomaly_detection_and_safety():
    """5. Test anomaly detection flags extreme prices but does not falsely flag normal listings."""
    # Create an intentionally anomalous listing (Wheat at ₹190/kg vs normal ₹25)
    s, bad_listing = post("/listings", {
        "batch_id": "BATCH-ANOM-TEST-HIGH-99",
        "crop_name": "Wheat",
        "farmer_name": "Outlier Farmer",
        "farmer_phone": "9999900000",
        "category": "Grains",
        "quantity_kg": 1500.0,
        "price_per_kg": 190.0,  # 700% above normal median
        "farm_location": "Ambala, Haryana",
        "harvest_date": "2026-10-10",
        "quality_grade": "Grade A"
    })
    assert s == 201

    try:
        # Run anomaly surveillance
        s, anomalies = get("/ai/anomalies")
        assert s == 200
        assert isinstance(anomalies, list)

        # Confirm the anomalous batch was flagged
        flagged = next((a for a in anomalies if a["item_id"] == "BATCH-ANOM-TEST-HIGH-99"), None)
        assert flagged is not None, "Extreme price listing was not caught by anomaly surveillance"
        assert flagged["anomaly_category"] == "PRICING_OUTLIER_HIGH"
        assert flagged["severity"] in ["High", "Medium"]

        # Test dismissal
        aid = flagged["alert_id"]
        s, dismiss_res = patch(f"/ai/anomalies/{aid}/dismiss", {"status": "Dismissed", "notes": "Test verified"})
        assert s == 200
        assert dismiss_res["new_status"] == "Dismissed"

        # Verify status in subsequent retrieval
        s, anomalies_updated = get("/ai/anomalies")
        updated_alert = next((a for a in anomalies_updated if a["alert_id"] == aid), None)
        assert updated_alert is not None
        assert updated_alert["status"] == "Dismissed"

    finally:
        # Clean up test listing
        delete("/listings/BATCH-ANOM-TEST-HIGH-99")


def test_multilingual_advisory():
    """6. Test multilingual post-harvest crop advisory in EN, HI, PA."""
    s_en, res_en = get("/ai/advisory?crop=Wheat&lang=en")
    assert s_en == 200
    assert res_en["language"] == "en"
    assert "moisture" in res_en["advisory"]["optimal_moisture"].lower()

    s_hi, res_hi = get("/ai/advisory?crop=Wheat&lang=hi")
    assert s_hi == 200
    assert res_hi["language"] == "hi"
    assert "नमी" in res_hi["advisory"]["optimal_moisture"]

    s_pa, res_pa = get("/ai/advisory?crop=Wheat&lang=pa")
    assert s_pa == 200
    assert res_pa["language"] == "pa"
    assert "ਨਮੀ" in res_pa["advisory"]["optimal_moisture"]


if __name__ == "__main__":
    pytest.main(["-v", __file__])
