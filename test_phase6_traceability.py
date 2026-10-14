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


def test_blockchain_ledger_verification():
    """1. Test full ledger mathematical integrity audit."""
    status, res = get("/blockchain/verify")
    assert status == 200
    assert res["chain_valid"] is True
    assert res["total_blocks"] >= 63
    assert "SHA-256" in res["ledger_type"]
    assert "Proof-of-Work" in res["ledger_type"]
    assert "tip_hash" in res
    assert res["tip_hash"].startswith("00")


def test_blockchain_blocks_pagination():
    """2. Test paginated retrieval of ledger blocks."""
    status, blocks = get("/blockchain/blocks?limit=20")
    assert status == 200
    assert isinstance(blocks, list)
    assert len(blocks) > 0
    assert len(blocks) <= 20

    # Genesis block check
    genesis = blocks[0]
    assert genesis["index"] == 0
    assert genesis["block_hash"].startswith("00")
    assert genesis["prev_hash"] == "0" * 64
    assert genesis["event_type"] == "GENESIS"


def test_batch_traceability_lifecycle():
    """3. Test retrieval of complete soil-to-sale timeline for an existing batch."""
    # First get an existing batch from listings
    status, listings = get("/listings")
    assert status == 200
    assert len(listings) > 0
    target_batch = listings[0]["batch_id"]

    status, res = get(f"/traceability/{target_batch}")
    assert status == 200
    assert res["batch"]["batch_id"] == target_batch
    assert isinstance(res["events"], list)
    assert len(res["events"]) >= 1
    assert "qr_code_payload" in res
    assert target_batch in res["qr_code_payload"]
    assert res["verification_status"] == "CRYPTOGRAPHICALLY_VERIFIED"
    assert res["chain_audit"]["chain_valid"] is True


def test_record_provenance_event_and_mining():
    """4. Test appending a new verifiable provenance block with SHA-256 PoW mining."""
    status, listings = get("/listings")
    assert status == 200
    target_batch = listings[0]["batch_id"]

    # Record a quality inspection event
    event_payload = {
        "batch_id": target_batch,
        "event_type": "QUALITY_INSPECTION",
        "actor": "APMC Central Food Assayer #801",
        "location": "Karnal Mandi Quality Testing Wing",
        "details": {
            "moisture_pct": "11.2%",
            "hectolitre_weight": "79.8 kg/hl",
            "foreign_matter_pct": "0.15%",
            "grade": "Grade A Export Quality",
            "certification_id": "APMC-CERT-2026-QA801"
        }
    }

    status, new_block = post("/traceability/record-event", event_payload)
    assert status == 201
    assert new_block["batch_id"] == target_batch
    assert new_block["event_type"] == "QUALITY_INSPECTION"
    assert new_block["actor"] == "APMC Central Food Assayer #801"
    assert new_block["location"] == "Karnal Mandi Quality Testing Wing"
    assert new_block["block_hash"].startswith("00")
    assert new_block["nonce"] >= 0

    # Ensure the new event appears in the batch's traceability timeline
    status, res = get(f"/traceability/{target_batch}")
    assert status == 200
    matching_events = [e for e in res["events"] if e["index"] == new_block["index"]]
    assert len(matching_events) == 1
    assert matching_events[0]["block_hash"] == new_block["block_hash"]

    # Re-verify ledger integrity after mining
    status, audit = get("/blockchain/verify")
    assert status == 200
    assert audit["chain_valid"] is True


def test_traceability_nonexistent_batch():
    """5. Test proper 404 response for nonexistent batch ID."""
    status, res = get("/traceability/NONEXISTENT-BATCH-999999")
    assert status == 404
    assert "not found" in res["detail"].lower()
