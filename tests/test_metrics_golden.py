"""Golden metric verification tests re-computed independently with Pandas and SQL."""
import pytest
from app.data.etl import get_db_connection
from app.core.lane_a import LaneAEngine
from app.core.verifier import PandasVerifier


@pytest.fixture(scope="module")
def db_conn():
    conn = get_db_connection()
    yield conn
    conn.close()


@pytest.fixture(scope="module")
def verifier():
    return PandasVerifier()


def test_golden_total_revenue(db_conn, verifier):
    """Verify total net revenue matches exactly ₹14,39,200 (₹14,58,200 if returned included)."""
    # Default scope
    sql, rows, formula, _ = LaneAEngine.execute(db_conn, "total_revenue", {}, include_returned=False)
    assert rows[0]["total_net_revenue"] == 1439200.0
    valid, msg = verifier.verify("total_revenue", {}, rows, include_returned=False)
    assert valid is True

    # Returned included scope
    sql_ret, rows_ret, _, _ = LaneAEngine.execute(db_conn, "total_revenue", {}, include_returned=True)
    assert rows_ret[0]["total_net_revenue"] == 1458200.0
    valid_ret, msg_ret = verifier.verify("total_revenue", {}, rows_ret, include_returned=True)
    assert valid_ret is True


def test_golden_top_product(db_conn, verifier):
    """Verify Monitor is top product with ₹4,73,000 net revenue."""
    sql, rows, formula, chart = LaneAEngine.execute(db_conn, "top_product", {"limit": 10})
    assert rows[0]["product"] == "Monitor"
    assert rows[0]["net_revenue"] == 473000.0
    
    # Check runner-ups
    product_dict = {r["product"]: r["net_revenue"] for r in rows}
    assert product_dict["Desk"] == 222500.0
    assert product_dict["Office Chair"] == 210600.0
    assert product_dict["USB-C Hub"] == 163800.0
    assert product_dict["Wireless Mouse"] == 148200.0
    assert product_dict["Keyboard"] == 125100.0
    assert product_dict["Laptop Stand"] == 96000.0

    valid, _ = verifier.verify("top_product", {}, rows)
    assert valid is True


def test_golden_top_region(db_conn, verifier):
    """Verify South is top region with ₹4,11,200."""
    sql, rows, formula, chart = LaneAEngine.execute(db_conn, "top_region", {"limit": 10})
    assert rows[0]["region"] == "South"
    assert rows[0]["net_revenue"] == 411200.0

    region_dict = {r["region"]: r["net_revenue"] for r in rows}
    assert region_dict["North"] == 384450.0
    assert region_dict["East"] == 346700.0
    assert region_dict["West"] == 296850.0

    valid, _ = verifier.verify("top_region", {}, rows)
    assert valid is True


def test_golden_category_and_channel(db_conn, verifier):
    """Verify Category and Sales Channel breakdowns."""
    _, cat_rows, _, _ = LaneAEngine.execute(db_conn, "revenue_by_category", {})
    cat_dict = {r["category"]: r["net_revenue"] for r in cat_rows}
    assert cat_dict["Accessories"] == 533100.0
    assert cat_dict["Electronics"] == 473000.0
    assert cat_dict["Furniture"] == 433100.0

    _, chan_rows, _, _ = LaneAEngine.execute(db_conn, "revenue_by_channel", {})
    chan_dict = {r["sales_channel"]: r["net_revenue"] for r in chan_rows}
    assert chan_dict["Online"] == 746750.0
    assert chan_dict["Retail"] == 692450.0


def test_golden_monthly_trend(db_conn, verifier):
    """Verify monthly net revenue trend from Jan to Jun 2026."""
    _, rows, _, _ = LaneAEngine.execute(db_conn, "monthly_trend", {})
    month_dict = {r["order_month"]: r["net_revenue"] for r in rows}
    assert month_dict["2026-01"] == 210250.0
    assert month_dict["2026-02"] == 234600.0
    assert month_dict["2026-03"] == 223900.0
    assert month_dict["2026-04"] == 240700.0
    assert month_dict["2026-05"] == 318500.0  # Peak
    assert month_dict["2026-06"] == 211250.0

    valid, _ = verifier.verify("monthly_trend", {}, rows)
    assert valid is True


def test_golden_revenue_change_march_april(db_conn, verifier):
    """Verify revenue change between March and April (+16,800, +7.50%)."""
    _, rows, _, _ = LaneAEngine.execute(db_conn, "revenue_change", {"month1": "03", "month2": "04"})
    assert rows[0]["month1_revenue"] == 223900.0
    assert rows[0]["month2_revenue"] == 240700.0
    assert rows[0]["delta_revenue"] == 16800.0
    assert rows[0]["pct_change"] == 7.50

    valid, _ = verifier.verify("revenue_change", {"month1": "03", "month2": "04"}, rows)
    assert valid is True


def test_verifier_blocks_corrupted_result(verifier):
    """Deliberately corrupt a result and confirm the Dual-Engine Verifier blocks it."""
    corrupted_rows = [{"total_net_revenue": 9999999.0}]
    valid, msg = verifier.verify("total_revenue", {}, corrupted_rows)
    assert valid is False
    assert "SQL: ₹9,999,999.00 vs Pandas: ₹1,439,200.00" in msg
