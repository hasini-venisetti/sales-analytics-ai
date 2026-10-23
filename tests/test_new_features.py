"""Unit tests for Trust Meter, Challenge Sandbox, Break-It Battery, and Evidence Advisor."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.trust_meter import TrustMeter
from app.core.challenge_sandbox import ChallengeSandbox
from app.core.break_it import BreakItEngine
from app.core.advisor import EvidenceAdvisor
from app.data.etl import get_db_connection

client = TestClient(app)


def test_trust_meter_evaluation():
    """Verify Trust Meter gives high grade to verified Lane A and 0 to refusal."""
    score_lane_a = TrustMeter.evaluate(
        lane="A",
        verified=True,
        row_counts={"used": 48, "excluded": 3, "returned": 1}
    )
    assert score_lane_a.score >= 90
    assert "A+" in score_lane_a.grade or "A" in score_lane_a.grade
    assert len(score_lane_a.factors) >= 4

    # Unverified penalty test
    score_unverified = TrustMeter.evaluate(
        lane="B",
        verified=False,
        row_counts={"used": 48, "excluded": 3, "returned": 1}
    )
    assert score_unverified.score < 60

    # Refusal test
    score_refusal = TrustMeter.evaluate(
        lane="C",
        verified=False,
        row_counts={"used": 0, "excluded": 0, "returned": 1},
        is_refusal=True
    )
    assert score_refusal.score == 0
    assert score_refusal.grade == "Refused"


def test_challenge_sandbox_multi_definitions():
    """Verify Challenge Sandbox stress-tests conclusions across 4 definitions."""
    conn = get_db_connection()
    try:
        report = ChallengeSandbox.evaluate_sensitivity(conn, "What is our total revenue?")
        assert report["is_stable"] is True
        assert len(report["scenarios"]) == 4

        # Scenario names
        names = [s["name"] for s in report["scenarios"]]
        assert "Default Net Revenue" in names
        assert "Gross Merchandise Value" in names
        assert "Returns Included (Net)" in names
        assert "Imputed Missing Price" in names

        # Confirm Monitor remains #1 product across all scenarios
        for s in report["scenarios"]:
            assert s["top_product"] == "Monitor"
            assert s["top_region"] == "South"

        assert "100% ROBUST" in report["verdict"]
    finally:
        conn.close()


def test_break_it_engine_blocks_all_attacks():
    """Verify live Break-It red-team battery blocks 100% of attack payloads."""
    battery = BreakItEngine.run_battery()
    assert battery["all_blocked"] is True
    assert battery["attacks_tested"] == 5
    assert battery["attacks_blocked"] == 5
    assert battery["vulnerability_rate_pct"] == 0.0

    for res in battery["results"]:
        assert res["blocked"] is True
        assert res["defense_layer"] != "None (Warning)"
        assert res["latency_ms"] < 100  # Sub-100ms defense


def test_advisor_with_evidence():
    """Verify Evidence Advisor separates verified facts from strategic advice."""
    mock_rows = [{"product": "Monitor", "net_revenue": 473000.0, "total_units": 50}]
    briefing = EvidenceAdvisor.advise("top_product", {}, mock_rows)
    
    assert len(briefing["verified_facts"]) >= 2
    assert len(briefing["risk_observations"]) >= 1
    assert len(briefing["actionable_recommendations"]) >= 2
    assert "₹4,73,000" in briefing["verified_facts"][0]
    assert "Monitor" in briefing["headline"]


def test_api_challenge_endpoint():
    """Verify POST /api/challenge returns structured sensitivity matrix."""
    resp = client.post("/api/challenge", json={"question": "Which product has highest revenue?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_stable"] is True
    assert len(data["scenarios"]) == 4


def test_api_break_it_endpoint():
    """Verify POST /api/break-it executes attack battery via API."""
    resp = client.post("/api/break-it")
    assert resp.status_code == 200
    data = resp.json()
    assert data["all_blocked"] is True
    assert data["attacks_blocked"] == 5
