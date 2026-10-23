"""Unit tests for Driver Analysis Agent (USP-5)."""
import pytest
from app.data.etl import get_db_connection
from app.core.agent_drivers import DriverAnalysisAgent


@pytest.fixture(scope="module")
def db_conn():
    conn = get_db_connection()
    yield conn
    conn.close()


def test_driver_analysis_march_to_april(db_conn):
    """Verify March to April variance: +16,800 (+7.50%) with Wireless Mouse as top driver."""
    result = DriverAnalysisAgent.analyze(db_conn, "2026-03", "2026-04")
    assert result["rev1"] == 223900.0
    assert result["rev2"] == 240700.0
    assert result["delta"] == 16800.0
    assert result["pct_change"] == 7.50

    # Primary growth driver
    top_pos = [p for p in result["product_deltas"] if p["diff"] > 0]
    assert top_pos[0]["product"] == "Wireless Mouse"
    assert top_pos[0]["diff"] == 22100.0
    assert "Wireless Mouse" in result["narrative"]
    assert "₹16,800" in result["narrative"]


def test_driver_analysis_may_spike(db_conn):
    """Verify April to May spike: +77,800 (+32.32%) driven by Monitor."""
    result = DriverAnalysisAgent.analyze(db_conn, "2026-04", "2026-05")
    assert result["delta"] == 77800.0
    assert result["pct_change"] == 32.32
    assert result["product_deltas"][0]["product"] == "Monitor"
    assert result["product_deltas"][0]["diff"] == 57500.0
    assert "Monitor" in result["narrative"]


def test_driver_analysis_june_drop(db_conn):
    """Verify May to June drop: -107,250 (-33.67%) driven by Monitor pullback."""
    result = DriverAnalysisAgent.analyze(db_conn, "2026-05", "2026-06")
    assert result["delta"] == -107250.0
    assert result["pct_change"] == -33.67
    
    # Largest negative driver
    sorted_neg = sorted(result["product_deltas"], key=lambda x: x["diff"])
    assert sorted_neg[0]["product"] == "Monitor"
    assert sorted_neg[0]["diff"] == -66500.0
    assert "Monitor" in result["narrative"]
