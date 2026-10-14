import urllib.request
import urllib.error
import json

BASE = "http://127.0.0.1:8000/api"

def post(url, data):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

def put(url, data):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="PUT"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

def patch(url, data):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="PATCH"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

def delete(url):
    req = urllib.request.Request(url, method="DELETE")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

def get(url):
    try:
        with urllib.request.urlopen(url) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

def test_phase3_api_suite():
    print("\n--- 1. Testing GET /api/health ---")
    s, health_res = get(f"{BASE}/health")
    assert s == 200, f"Health check failed with HTTP {s}"
    assert health_res["status"] == "healthy"
    assert health_res["database"]["connected"] is True
    print(f"PASS: Health check OK. DB: {health_res['database']['target']}")

    print("\n--- 2. Testing POST /api/listings ---")
    new_crop = {
        "crop_name": "Organic Basmati Rice",
        "farmer_name": "Hardeep Singh",
        "farmer_phone": "9876543210",
        "category": "Grains",
        "quantity_kg": 2000.0,
        "price_per_kg": 65.0,
        "farm_location": "Amritsar, Punjab",
        "harvest_date": "2026-10-12",
        "quality_grade": "Export Quality"
    }
    s, create_res = post(f"{BASE}/listings", new_crop)
    assert s == 201, f"Create listing failed: HTTP {s}, {create_res}"
    listing_id = create_res["id"]
    batch_id = create_res["batch_id"]
    print(f"PASS: Created listing ID={listing_id}, batch_id={batch_id}")

    print("\n--- 3. Testing GET /api/listings/{id} (by numeric ID and batch_id) ---")
    s, get_id_res = get(f"{BASE}/listings/{listing_id}")
    assert s == 200 and get_id_res["batch_id"] == batch_id
    s, get_batch_res = get(f"{BASE}/listings/{batch_id}")
    assert s == 200 and get_batch_res["id"] == listing_id
    print("PASS: Retrieved listing successfully by both numeric ID and batch_id")

    print("\n--- 4. Testing PUT /api/listings/{id} ---")
    s, update_res = put(f"{BASE}/listings/{listing_id}", {"price_per_kg": 68.0})
    assert s == 200 and update_res["price_per_kg"] == 68.0
    print(f"PASS: Updated listing price to Rs {update_res['price_per_kg']}")

    print("\n--- 5. Testing Order Oversell Rejection (Requested > Available) ---")
    s, over_res = post(f"{BASE}/orders", {
        "batch_id": batch_id,
        "buyer_name": "Mega Wholesale Co",
        "quantity_kg": 3000.0,  # Stock is only 2000.0
        "delivery_location": "Delhi"
    })
    assert s == 400, f"Expected 400 rejection, got HTTP {s}"
    print(f"PASS: Overselling rejected with HTTP 400: '{over_res.get('detail')}'")

    print("\n--- 6. Testing Order Zero/Negative Quantity Rejection ---")
    s, zero_res = post(f"{BASE}/orders", {
        "batch_id": batch_id,
        "buyer_name": "Mega Wholesale Co",
        "quantity_kg": 0.0,
        "delivery_location": "Delhi"
    })
    assert s == 400 or s == 422, f"Expected 400 or 422, got HTTP {s}"
    print(f"PASS: Zero quantity rejected with HTTP {s}")

    print("\n--- 7. Testing Successful Order Placement & Single-Transaction Deduction ---")
    s, order_res = post(f"{BASE}/orders", {
        "batch_id": batch_id,
        "buyer_name": "Mega Wholesale Co",
        "quantity_kg": 800.0,
        "delivery_location": "Delhi Azadpur"
    })
    assert s == 201, f"Order placement failed: HTTP {s}, {order_res}"
    order_id = order_res["order_id"]
    expected_total = 800.0 * 68.0
    assert order_res["total_price"] == expected_total
    print(f"PASS: Order {order_id} created. Total Rs {order_res['total_price']}")

    # Verify inventory deduction
    s, refreshed_batch = get(f"{BASE}/listings/{batch_id}")
    assert s == 200
    assert refreshed_batch["available_qty_kg"] == 1200.0, f"Expected 1200.0 kg, got {refreshed_batch['available_qty_kg']}"
    print(f"PASS: Listing stock deducted from 2000.0 to {refreshed_batch['available_qty_kg']} kg")

    print("\n--- 8. Testing PATCH /api/orders/{id}/status ---")
    s, patch_res = patch(f"{BASE}/orders/{order_id}/status", {"status": "In Transit"})
    assert s == 200 and patch_res["status"] == "In Transit"
    print(f"PASS: Order status updated to '{patch_res['status']}'")

    print("\n--- 9. Testing Filtering in GET /api/listings ---")
    s, filter_res = get(f"{BASE}/listings?crop_name=Basmati&category=Grains")
    assert s == 200
    assert any(b["batch_id"] == batch_id for b in filter_res)
    print(f"PASS: Filtered listings returned {len(filter_res)} matching records")

    print("\n--- 10. Testing DELETE /api/listings/{id} ---")
    s, del_res = delete(f"{BASE}/listings/{listing_id}")
    assert s == 200
    s, get_deleted = get(f"{BASE}/listings/{listing_id}")
    assert s == 404
    print(f"PASS: Listing deleted and confirmed 404")

    print("\n=== ALL 10 PHASE 3 INTEGRATION TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    test_phase3_api_suite()
