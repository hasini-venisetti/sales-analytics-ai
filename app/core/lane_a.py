"""Lane A: Deterministic, Certified Parameterized SQL Metric Registry."""
from typing import Any, Dict, List, Optional, Tuple
import sqlite3

from app.core.metrics import format_inr, format_percentage, METRICS_DEFINITIONS


class LaneAEngine:
    """Certified deterministic metrics engine executing parameterized SQL templates."""

    TEMPLATES = {
        "total_revenue": {
            "sql": """
                SELECT 
                    ROUND(SUM(net_revenue), 2) AS total_net_revenue,
                    ROUND(SUM(gross_revenue), 2) AS total_gross_revenue,
                    ROUND(SUM(discount_amount), 2) AS total_discount,
                    COUNT(*) AS order_count
                FROM {view};
            """,
            "formula": "SUM((Quantity * Unit_price) - Discount_amount)",
            "chart_type": "metric",
        },
        "top_product": {
            "sql": """
                SELECT 
                    product, 
                    ROUND(SUM(net_revenue), 2) AS net_revenue,
                    SUM(quantity) AS total_units,
                    ROUND(SUM(discount_amount), 2) AS total_discount
                FROM {view}
                GROUP BY product
                ORDER BY net_revenue DESC
                LIMIT :limit;
            """,
            "formula": "GROUP BY Product ORDER BY SUM(net_revenue) DESC",
            "chart_type": "bar",
        },
        "monthly_trend": {
            "sql": """
                SELECT 
                    order_month,
                    order_month_name,
                    ROUND(SUM(net_revenue), 2) AS net_revenue,
                    SUM(quantity) AS total_units,
                    COUNT(*) AS order_count
                FROM {view}
                GROUP BY order_month, order_month_name
                ORDER BY order_month ASC;
            """,
            "formula": "GROUP BY order_month ORDER BY order_month ASC",
            "chart_type": "line",
        },
        "top_region": {
            "sql": """
                SELECT 
                    region,
                    ROUND(SUM(net_revenue), 2) AS net_revenue,
                    SUM(quantity) AS total_units,
                    COUNT(*) AS order_count
                FROM {view}
                GROUP BY region
                ORDER BY net_revenue DESC
                LIMIT :limit;
            """,
            "formula": "GROUP BY Region ORDER BY SUM(net_revenue) DESC",
            "chart_type": "bar",
        },
        "revenue_by_category": {
            "sql": """
                SELECT 
                    category,
                    ROUND(SUM(net_revenue), 2) AS net_revenue,
                    SUM(quantity) AS total_units
                FROM {view}
                GROUP BY category
                ORDER BY net_revenue DESC;
            """,
            "formula": "GROUP BY Category ORDER BY SUM(net_revenue) DESC",
            "chart_type": "bar",
        },
        "revenue_by_channel": {
            "sql": """
                SELECT 
                    sales_channel,
                    ROUND(SUM(net_revenue), 2) AS net_revenue,
                    SUM(quantity) AS total_units
                FROM {view}
                GROUP BY sales_channel
                ORDER BY net_revenue DESC;
            """,
            "formula": "GROUP BY Sales_channel ORDER BY SUM(net_revenue) DESC",
            "chart_type": "bar",
        },
        "units_sold_product": {
            "sql": """
                SELECT 
                    product,
                    SUM(quantity) AS total_units,
                    ROUND(SUM(net_revenue), 2) AS net_revenue
                FROM {view}
                GROUP BY product
                ORDER BY total_units DESC;
            """,
            "formula": "GROUP BY Product ORDER BY SUM(quantity) DESC",
            "chart_type": "bar",
        },
        "units_sold_region": {
            "sql": """
                SELECT 
                    region,
                    SUM(quantity) AS total_units,
                    ROUND(SUM(net_revenue), 2) AS net_revenue
                FROM {view}
                GROUP BY region
                ORDER BY total_units DESC;
            """,
            "formula": "GROUP BY Region ORDER BY SUM(quantity) DESC",
            "chart_type": "bar",
        },
        "average_order_value": {
            "sql": """
                SELECT 
                    ROUND(AVG(net_revenue), 2) AS average_order_value,
                    ROUND(SUM(net_revenue), 2) AS total_net_revenue,
                    COUNT(*) AS order_count
                FROM {view};
            """,
            "formula": "SUM(net_revenue) / COUNT(Transaction_Id)",
            "chart_type": "metric",
        },
        "discount_impact": {
            "sql": """
                SELECT 
                    ROUND(SUM(discount_amount), 2) AS total_discount,
                    ROUND(SUM(gross_revenue), 2) AS total_gross_revenue,
                    ROUND((SUM(discount_amount) * 100.0 / SUM(gross_revenue)), 2) AS discount_pct
                FROM {view};
            """,
            "formula": "(SUM(Discount_amount) / SUM(gross_revenue)) * 100",
            "chart_type": "metric",
        },
        "returns_summary": {
            "sql": """
                SELECT 
                    COUNT(*) AS returned_orders_count,
                    ROUND(SUM(gross_revenue), 2) AS returns_gross_value,
                    SUM(quantity) AS returned_units
                FROM sales
                WHERE status = 'Returned';
            """,
            "formula": "COUNT(*) and SUM(gross_revenue) WHERE Status = 'Returned'",
            "chart_type": "metric",
        },
    }

    @classmethod
    def execute(
        cls, 
        conn: sqlite3.Connection, 
        intent: str, 
        params: Dict[str, Any], 
        include_returned: bool = False
    ) -> Tuple[str, List[Dict[str, Any]], str, Dict[str, Any]]:
        """Executes a certified Lane A template with bound parameters.
        
        Returns:
            (executed_sql, rows, formula, chart_spec)
        """
        view = "v_sales_with_returns" if include_returned else "v_sales_valid"

        if intent == "revenue_change":
            # Multi-period comparison
            m1 = params.get("month1", "2026-03")
            m2 = params.get("month2", "2026-04")
            
            # Month normalization (e.g., 'Mar' -> '03' or '2026-03')
            month_map = {
                "jan": "2026-01", "feb": "2026-02", "mar": "2026-03", 
                "apr": "2026-04", "may": "2026-05", "jun": "2026-06",
                "january": "2026-01", "february": "2026-02", "march": "2026-03",
                "april": "2026-04", "june": "2026-06"
            }
            norm_m1 = month_map.get(m1.lower(), m1 if "-" in m1 else f"2026-{m1.zfill(2)}")
            norm_m2 = month_map.get(m2.lower(), m2 if "-" in m2 else f"2026-{m2.zfill(2)}")

            sql = f"""
                WITH m1 AS (
                    SELECT ROUND(COALESCE(SUM(net_revenue), 0), 2) AS rev1, :m1 AS month1 FROM {view} WHERE order_month = :m1
                ),
                m2 AS (
                    SELECT ROUND(COALESCE(SUM(net_revenue), 0), 2) AS rev2, :m2 AS month2 FROM {view} WHERE order_month = :m2
                )
                SELECT 
                    m1.month1, m1.rev1 AS month1_revenue,
                    m2.month2, m2.rev2 AS month2_revenue,
                    ROUND(m2.rev2 - m1.rev1, 2) AS delta_revenue,
                    ROUND(((m2.rev2 - m1.rev1) * 100.0 / NULLIF(m1.rev1, 0)), 2) AS pct_change
                FROM m1, m2;
            """
            cursor = conn.cursor()
            cursor.execute(sql, {"m1": norm_m1, "m2": norm_m2})
            rows = [dict(row) for row in cursor.fetchall()]
            formula = "(Revenue(Month2) - Revenue(Month1)) / Revenue(Month1) * 100"
            chart_spec = {
                "type": "bar",
                "title": f"Revenue Comparison: {norm_m1} vs {norm_m2}",
                "labels": [norm_m1, norm_m2],
                "datasets": [{
                    "label": "Net Revenue (₹)",
                    "data": [rows[0]["month1_revenue"], rows[0]["month2_revenue"]]
                }]
            }
            return sql.strip(), rows, formula, chart_spec

        template = cls.TEMPLATES.get(intent)
        if not template:
            raise ValueError(f"Unknown Lane A metric intent: {intent}")

        sql_raw = template["sql"].format(view=view).strip()
        bind_params = {}
        if ":limit" in sql_raw:
            bind_params["limit"] = int(params.get("limit", 10))

        cursor = conn.cursor()
        cursor.execute(sql_raw, bind_params)
        rows = [dict(row) for row in cursor.fetchall()]

        # Generate chart spec
        chart_type = template["chart_type"]
        chart_spec = cls._build_chart_spec(intent, rows, chart_type)

        return sql_raw, rows, template["formula"], chart_spec

    @classmethod
    def _build_chart_spec(cls, intent: str, rows: List[Dict[str, Any]], chart_type: str) -> Dict[str, Any]:
        """Constructs front-end Chart.js specification."""
        if not rows or chart_type == "metric":
            return {"type": "none", "labels": [], "datasets": []}

        if intent in ("top_product", "units_sold_product"):
            labels = [r.get("product") for r in rows]
            val_key = "net_revenue" if intent == "top_product" else "total_units"
            label = "Net Revenue (₹)" if intent == "top_product" else "Units Sold"
            return {
                "type": "bar",
                "title": "Product Performance",
                "labels": labels,
                "datasets": [{"label": label, "data": [r.get(val_key) for r in rows]}]
            }

        elif intent in ("top_region", "units_sold_region"):
            labels = [r.get("region") for r in rows]
            val_key = "net_revenue" if intent == "top_region" else "total_units"
            label = "Net Revenue (₹)" if intent == "top_region" else "Units Sold"
            return {
                "type": "bar",
                "title": "Regional Performance",
                "labels": labels,
                "datasets": [{"label": label, "data": [r.get(val_key) for r in rows]}]
            }

        elif intent == "monthly_trend":
            labels = [r.get("order_month_name") or r.get("order_month") for r in rows]
            return {
                "type": "line",
                "title": "Monthly Net Revenue Trend (Jan–Jun 2026)",
                "labels": labels,
                "datasets": [{
                    "label": "Net Revenue (₹)",
                    "data": [r.get("net_revenue") for r in rows],
                    "borderColor": "#3b82f6",
                    "fill": False
                }]
            }

        elif intent == "revenue_by_category":
            labels = [r.get("category") for r in rows]
            return {
                "type": "bar",
                "title": "Revenue by Category",
                "labels": labels,
                "datasets": [{"label": "Net Revenue (₹)", "data": [r.get("net_revenue") for r in rows]}]
            }

        elif intent == "revenue_by_channel":
            labels = [r.get("sales_channel") for r in rows]
            return {
                "type": "bar",
                "title": "Revenue by Sales Channel",
                "labels": labels,
                "datasets": [{"label": "Net Revenue (₹)", "data": [r.get("net_revenue") for r in rows]}]
            }

        return {"type": chart_type, "labels": [], "datasets": []}
