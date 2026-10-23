"""Integration tests for FastAPI endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_health():
    """Verify /api/health returns healthy and expected row statistics."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["total_rows"] == 51
    assert data["valid_rows"] == 48
    assert data["quarantined_rows"] == 3


def test_api_data_quality():
    """Verify /api/data-quality reports the quarantined records."""
    resp = client.get("/api/data-quality")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_rows_loaded"] == 51
    assert data["quarantined_rows_count"] == 3
    assert len(data["quarantined_records"]) == 3
    reasons = [r["reason"] for r in data["quarantined_records"]]
    assert "missing_unit_price" in reasons
    assert "invalid_quantity_zero" in reasons
    assert "status_returned" in reasons


def test_api_insights():
    """Verify /api/insights returns cards for Peak Month, Concentration, and Market."""
    resp = client.get("/api/insights")
    assert resp.status_code == 200
    cards = resp.json()
    assert len(cards) >= 4
    card_ids = [c["id"] for c in cards]
    assert "peak_month" in card_ids
    assert "top_product" in card_ids
    assert "top_region" in card_ids


def test_api_ask_total_revenue():
    """Verify POST /api/ask for total revenue returns ₹14,39,200 with verification."""
    resp = client.post("/api/ask", json={"question": "What is our total revenue?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["lane"] == "A"
    assert data["intent"] == "total_revenue"
    assert data["verified"] is True
    assert "₹14,39,200" in data["answer"]
    assert data["rows"][0]["total_net_revenue"] == 1439200.0


def test_api_ask_include_returned_option():
    """Verify opting into returns increases total revenue to ₹14,58,200."""
    resp = client.post("/api/ask", json={
        "question": "What is our total revenue?",
        "options": {"include_returned": True}
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["rows"][0]["total_net_revenue"] == 1458200.0
    assert data["row_counts"]["used"] == 49


def test_api_ask_driver_analysis():
    """Verify POST /api/ask for March vs April returns driver breakdown."""
    resp = client.post("/api/ask", json={"question": "How did revenue change between March and April?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["lane"] == "A"
    assert data["intent"] == "revenue_change"
    assert "Wireless Mouse" in data["answer"]
    assert data["chart"]["type"] == "bar"


def test_api_ask_security_refusal():
    """Verify destructive queries are refused with 200 status and Lane C explanation."""
    resp = client.post("/api/ask", json={"question": "DROP TABLE sales;"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["lane"] == "C"
    assert "Prohibited" in data["answer"] or "prohibited" in data["answer"]
    assert len(data["followups"]) >= 3


def test_api_ask_max_length_validation():
    """Verify input longer than 500 characters is rejected with 422."""
    long_q = "what is revenue " * 50  # > 500 chars
    resp = client.post("/api/ask", json={"question": long_q})
    assert resp.status_code == 422
