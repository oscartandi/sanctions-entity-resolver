from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_exact_alias_with_matching_attributes():
    res = client.post("/screen", json={
        "name": "Victor Sokolov",
        "country": "RU",
        "dob": "1974-05-12"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["overall_status"] == "BLOCK_OR_ESCALATE"
    assert data["hits"][0]["watchlist_id"] == "OFAC-1001"


def test_corporate_suffix_normalization():
    res = client.post("/screen", json={
        "name": "Caspian Petrochemical Holdings Limited",
        "country": "IR"
    })
    data = res.json()
    assert data["overall_status"] == "BLOCK_OR_ESCALATE"
    assert data["hits"][0]["watchlist_id"] == "EU-3089"


def test_fuzzy_typo_triggers_manual_review():
    res = client.post("/screen", json={
        "name": "Al Noor Globel Trding",
        "country": "AE"
    })
    data = res.json()
    assert data["overall_status"] in {"REVIEW_REQUIRED", "BLOCK_OR_ESCALATE"}
    assert data["hits"][0]["watchlist_id"] == "UN-2044"


def test_clean_entity_clears():
    res = client.post("/screen", json={
        "name": "Bengaluru Cloud Solutions Pvt Ltd",
        "country": "IN"
    })
    data = res.json()
    assert data["overall_status"] == "CLEAR"
    assert data["total_hits"] == 0
