import urllib.request
import urllib.error
import json
import pytest

BASE = "http://127.0.0.1:8000/api/logistics"

def get(path):
    try:
        with urllib.request.urlopen(f"{BASE}{path}") as resp:
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


def test_hubs_and_fleet_specifications():
    """1. Test agricultural trading hubs and fleet vehicle specifications."""
    s, hubs = get("/hubs")
    assert s == 200
    assert len(hubs) >= 15
    assert any("delhi" in h["key"] for h in hubs)
    assert any("punjab" in h["key"] for h in hubs)

    s, fleet = get("/fleet")
    assert s == 200
    assert len(fleet) == 4
    assert fleet[0]["capacity_kg"] <= 1500
    assert fleet[-1]["capacity_kg"] >= 15000


def test_route_calculation_and_emissions():
    """2. Test route calculation, vehicle matching, and CO2 emissions."""
    s, res = post("/calculate", {
        "origin": "Karnal, Haryana",
        "destination": "Azadpur, Delhi",
        "cargo_weight_kg": 2500.0
    })
    assert s == 200
    assert res["distance_km"] > 0
    assert "Tata 407" in res["vehicle_type"] or "Medium" in res["vehicle_type"]
    assert res["payload_utilization_pct"] > 50.0
    assert res["cost_breakdown"]["total_cost_inr"] > 0
    assert res["emission_metrics"]["total_co2_kg"] > 0
    assert len(res["steps"]) == 4


def test_vehicle_capacity_matching_boundaries():
    """3. Test vehicle matching chooses appropriate truck for cargo size."""
    # Small lot (800 kg) -> Mini Commercial
    s, small_res = post("/calculate", {
        "origin": "Ludhiana, Punjab",
        "destination": "Chandigarh",
        "cargo_weight_kg": 800.0
    })
    assert s == 200
    assert "Tata Ace" in small_res["vehicle_type"] or "Mini" in small_res["vehicle_type"]

    # Heavy lot (12,000 kg) -> Multi-Axle
    s, heavy_res = post("/calculate", {
        "origin": "Ludhiana, Punjab",
        "destination": "Chandigarh",
        "cargo_weight_kg": 12000.0
    })
    assert s == 200
    assert "Multi-Axle" in heavy_res["vehicle_type"]


def test_dispatch_creation_and_milestone_tracking():
    """4. Test creating dispatch and updating tracking milestones."""
    s, disp = post("/dispatch", {
        "origin": "Amritsar, Punjab",
        "destination": "Azadpur, Delhi",
        "cargo_weight_kg": 3200.0,
        "crop_name": "Basmati Rice"
    })
    assert s == 201
    route_id = disp["route_id"]
    assert disp["status"] == "SCHEDULED"

    # Advance milestone to DISPATCHED
    s, updated1 = patch(f"/{route_id}/status", {"status": "DISPATCHED"})
    assert s == 200
    assert updated1["status"] == "DISPATCHED"

    # Advance milestone to IN_TRANSIT
    s, updated2 = patch(f"/{route_id}/status", {"status": "IN_TRANSIT"})
    assert s == 200
    assert updated2["status"] == "IN_TRANSIT"

    # Advance milestone to DELIVERED
    s, updated3 = patch(f"/{route_id}/status", {"status": "DELIVERED"})
    assert s == 200
    assert updated3["status"] == "DELIVERED"


def test_multi_farm_consolidation():
    """5. Test multi-farm consolidation generates verified financial & green savings."""
    # Fetch existing listings to consolidate
    req = urllib.request.Request("http://127.0.0.1:8000/api/listings")
    with urllib.request.urlopen(req) as resp:
        listings = json.loads(resp.read().decode("utf-8"))

    assert len(listings) >= 2, "Need at least 2 listings to test consolidation"
    batch_ids = [listings[0]["batch_id"], listings[1]["batch_id"]]

    s, cons = post("/consolidate", {
        "batch_ids": batch_ids,
        "destination": "Azadpur, Delhi"
    })
    assert s == 200
    assert cons["batches_consolidated"] == 2
    assert cons["total_cargo_weight_kg"] > 0
    assert cons["financial_savings"]["cost_saved_inr"] >= 0
    assert cons["green_emissions_savings"]["co2_saved_kg"] >= 0
    assert len(cons["transit_steps"]) == 4


def test_logistics_validation_errors():
    """6. Test invalid inputs return appropriate HTTP errors."""
    # Negative weight
    s, res = post("/calculate", {
        "origin": "Delhi",
        "destination": "Jaipur",
        "cargo_weight_kg": -50.0
    })
    assert s == 422

    # Non-existent route
    s, res = get("/LOG-DOES-NOT-EXIST-404")
    assert s == 404

    # Invalid status
    s, res = patch("/LOG-DOES-NOT-EXIST-404/status", {"status": "INVALID_STATUS"})
    assert s == 400 or s == 404


if __name__ == "__main__":
    pytest.main(["-v", __file__])
