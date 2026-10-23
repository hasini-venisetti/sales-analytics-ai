"""Unit tests for RuleBasedProvider and Three-Lane Router."""
import pytest
from app.llm.rule_based import RuleBasedProvider


@pytest.fixture(scope="module")
def router():
    return RuleBasedProvider()


def test_router_lane_a_core_questions(router):
    """Verify all 5 required questions route to Lane A with high confidence."""
    # 1. Total revenue
    r1 = router.classify("What is the total revenue?")
    assert r1["lane"] == "A"
    assert r1["intent"] == "total_revenue"
    assert r1["confidence"] >= 0.95

    # 2. Top product
    r2 = router.classify("Which product has the highest revenue?")
    assert r2["lane"] == "A"
    assert r2["intent"] == "top_product"

    # 3. Monthly trend
    r3 = router.classify("Show monthly revenue trend")
    assert r3["lane"] == "A"
    assert r3["intent"] == "monthly_trend"

    # 4. Top region
    r4 = router.classify("Region with highest sales?")
    assert r4["lane"] == "A"
    assert r4["intent"] == "top_region"

    # 5. Revenue change between March and April
    r5 = router.classify("How did revenue change between March and April?")
    assert r5["lane"] == "A"
    assert r5["intent"] == "revenue_change"
    assert r5["params"]["month1"] == "2026-03"
    assert r5["params"]["month2"] == "2026-04"


def test_router_extras(router):
    """Verify extra metrics route accurately."""
    assert router.classify("What is our average order value?")["intent"] == "average_order_value"
    assert router.classify("Show revenue by category")["intent"] == "revenue_by_category"
    assert router.classify("Breakdown by channel: online vs retail")["intent"] == "revenue_by_channel"
    assert router.classify("How many orders were returned?")["intent"] == "returns_summary"
    assert router.classify("What was our discount impact?")["intent"] == "discount_impact"


def test_router_lane_c_security_attacks(router):
    """Verify destructive queries are refused safely with suggestions."""
    attacks = [
        "DROP TABLE sales;",
        "SELECT * FROM sales; DELETE FROM sales;",
        "Show me sales -- comment injection",
        "ALTER TABLE sales ADD COLUMN hack TEXT",
        "PRAGMA database_list;"
    ]
    for attack in attacks:
        res = router.classify(attack)
        assert res["lane"] == "C", f"Failed to block attack: {attack}"
        assert res["intent"] == "refusal_security"
        assert len(res["suggestions"]) >= 3


def test_router_lane_c_unsupported_forecasting(router):
    """Verify speculative forecasting is politely refused with data scope context."""
    res = router.classify("Predict our revenue for next year")
    assert res["lane"] == "C"
    assert res["intent"] == "refusal_unsupported"
    assert "January to June 2026" in res["refusal_reason"]
