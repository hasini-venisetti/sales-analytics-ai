"""FastAPI REST endpoints for Ask-the-Numbers."""
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Depends
import sqlite3

from app.api.schemas import (
    AskRequest, AskResponse, HealthResponse, InsightCard,
    ChallengeRequest, ChallengeResponse, BreakItResponse
)
from app.config import GEMINI_API_KEY, DATA_CSV_PATH
from app.data.etl import get_db_connection, run_etl
from app.data.quality import DataQualityReport
from app.core.orchestrator import Orchestrator
from app.core.challenge_sandbox import ChallengeSandbox
from app.core.break_it import BreakItEngine
from app.core.metrics import format_inr, format_percentage

router = APIRouter(prefix="/api")
orchestrator = Orchestrator()


@router.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    """Processes a natural language business intelligence query with verification."""
    try:
        include_ret = request.options.include_returned if request.options else False
        res = orchestrator.process_question(
            question=request.question,
            session_id=request.session_id,
            include_returned=include_ret
        )
        return AskResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "code": "PROCESSING_ERROR",
            "message": str(e),
            "hint": "Check question syntax or try asking one of the certified Lane A questions."
        })


@router.get("/health", response_model=HealthResponse)
def health_check():
    """Health status and row load metrics."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM sales;")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM v_sales_valid;")
        valid = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM sales_quarantine;")
        quarantined = cur.fetchone()[0]
        mode = "gemini" if orchestrator.gemini_provider.is_available() else "rule-based"
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            mode=mode,
            csv_loaded=DATA_CSV_PATH.exists(),
            total_rows=total,
            valid_rows=valid,
            quarantined_rows=quarantined
        )
    finally:
        conn.close()


@router.get("/data-quality", response_model=DataQualityReport)
def get_data_quality():
    """Returns the comprehensive Data Quality & Quarantine audit report."""
    _, report = run_etl()
    return report


@router.get("/insights", response_model=List[InsightCard])
def get_insights():
    """Generates today's proactive insight cards computed deterministically."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        # 1. Total Net Revenue
        cur.execute("SELECT ROUND(SUM(net_revenue), 2) FROM v_sales_valid;")
        total_rev = cur.fetchone()[0] or 0.0

        # 2. Peak Month
        cur.execute("""
            SELECT order_month_name, ROUND(SUM(net_revenue), 2) AS rev 
            FROM v_sales_valid GROUP BY order_month, order_month_name 
            ORDER BY rev DESC LIMIT 1;
        """)
        peak_m, peak_val = cur.fetchone()

        # 3. Top Product & Concentration Risk
        cur.execute("""
            SELECT product, ROUND(SUM(net_revenue), 2) AS rev 
            FROM v_sales_valid GROUP BY product 
            ORDER BY rev DESC LIMIT 1;
        """)
        top_p, top_p_rev = cur.fetchone()
        concentration_pct = round((top_p_rev / total_rev) * 100, 1) if total_rev > 0 else 0

        # 4. Top Region
        cur.execute("""
            SELECT region, ROUND(SUM(net_revenue), 2) AS rev 
            FROM v_sales_valid GROUP BY region 
            ORDER BY rev DESC LIMIT 1;
        """)
        top_reg, top_reg_rev = cur.fetchone()

        # 5. Returns Value
        cur.execute("SELECT COUNT(*), ROUND(SUM(gross_revenue), 2) FROM sales WHERE status = 'Returned';")
        ret_count, ret_val = cur.fetchone()

        return [
            InsightCard(
                id="peak_month",
                title="Peak Revenue Month",
                value=f"{peak_m} 2026 ({format_inr(peak_val)})",
                subtitle="Highest sales volume across H1",
                badge="Peak",
                badge_color="emerald"
            ),
            InsightCard(
                id="top_product",
                title="Top Product Concentration",
                value=f"{top_p} ({format_inr(top_p_rev)})",
                subtitle=f"Represents {concentration_pct}% of total company revenue",
                badge=f"{concentration_pct}% Share",
                badge_color="indigo"
            ),
            InsightCard(
                id="top_region",
                title="Best Regional Market",
                value=f"{top_reg} ({format_inr(top_reg_rev)})",
                subtitle="Leading market in net collections",
                badge="Top Market",
                badge_color="blue"
            ),
            InsightCard(
                id="returns_alert",
                title="Returns & Quarantine",
                value=f"{format_inr(ret_val or 0.0)} ({ret_count} order)",
                subtitle="Quarantined from default revenue figures",
                badge="Quarantined",
                badge_color="amber"
            )
        ]
    finally:
        conn.close()


@router.get("/schema")
def get_schema():
    """Returns database tables, views, and column definitions."""
    return {
        "tables": {
            "sales": [
                "transaction_id (TEXT, PK)", "order_date (TEXT)", "order_date_iso (TEXT)",
                "order_month (TEXT)", "order_month_name (TEXT)", "product (TEXT)",
                "category (TEXT)", "region (TEXT)", "sales_channel (TEXT)",
                "quantity (INTEGER)", "unit_price (REAL)", "discount_amount (REAL)",
                "status (TEXT)", "gross_revenue (REAL)", "net_revenue (REAL)"
            ],
            "sales_quarantine": ["transaction_id (TEXT)", "quarantine_reason (TEXT)", "details (TEXT)"]
        },
        "views": {
            "v_sales_valid": "SELECT * FROM sales WHERE status = 'Completed' AND quantity > 0 AND unit_price IS NOT NULL;",
            "v_sales_with_returns": "SELECT * FROM sales WHERE quantity > 0 AND unit_price IS NOT NULL;"
        }
    }


@router.get("/glossary")
def get_glossary():
    """Returns the business glossary definitions."""
    return orchestrator.rag.glossary


@router.get("/examples")
def get_examples():
    """Returns categorized example questions for rapid user testing."""
    return {
        "required_5": [
            "What is the total revenue?",
            "Which product has the highest revenue?",
            "Show monthly revenue trend",
            "Which region has the highest sales?",
            "How did revenue change between March and April?"
        ],
        "driver_analysis": [
            "Why did May revenue spike?",
            "Why did June revenue drop?",
            "Compare sales between March and April"
        ],
        "extras": [
            "What is our average order value?",
            "Show revenue breakdown by category",
            "Online vs Retail channel sales",
            "What was our discount impact?",
            "How many orders were returned?"
        ],
        "red_team_safety": [
            "DROP TABLE sales;",
            "SELECT * FROM sales; DELETE FROM sales;",
            "Predict our revenue for next year"
        ]
    }


@router.post("/challenge", response_model=ChallengeResponse)
def challenge_answer(request: ChallengeRequest = None):
    """Evaluates question conclusions across multiple definitions (gross vs net, returns, price imputation)."""
    q = request.question if request else "General Sales Metrics"
    conn = get_db_connection()
    try:
        res = ChallengeSandbox.evaluate_sensitivity(conn, question=q)
        return ChallengeResponse(**res)
    finally:
        conn.close()


@router.post("/break-it", response_model=BreakItResponse)
def run_break_it_battery():
    """Fires a battery of attacks (DROP, injection, stacked DML, shadow columns) to demonstrate live defensive blocking."""
    res = BreakItEngine.run_battery()
    return BreakItResponse(**res)
