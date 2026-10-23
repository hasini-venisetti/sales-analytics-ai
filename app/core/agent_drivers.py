"""Driver Analysis Agent: Multi-step autonomous period-over-period decomposition."""
import sqlite3
from typing import Any, Dict, List, Tuple
from app.core.metrics import format_inr, format_percentage


class DriverAnalysisAgent:
    """Agentic 4-step pipeline: Plan -> Query -> Decompose -> Narrate."""

    @classmethod
    def analyze(
        cls, 
        conn: sqlite3.Connection, 
        m1_iso: str, 
        m2_iso: str, 
        include_returned: bool = False
    ) -> Dict[str, Any]:
        """Runs multi-dimensional variance analysis between two monthly periods."""
        view = "v_sales_with_returns" if include_returned else "v_sales_valid"
        cursor = conn.cursor()

        # Step 1: Query aggregate monthly revenue
        cursor.execute(f"""
            SELECT 
                (SELECT ROUND(COALESCE(SUM(net_revenue), 0), 2) FROM {view} WHERE order_month = :m1) AS rev1,
                (SELECT ROUND(COALESCE(SUM(net_revenue), 0), 2) FROM {view} WHERE order_month = :m2) AS rev2
        """, {"m1": m1_iso, "m2": m2_iso})
        agg_row = cursor.fetchone()
        rev1 = float(agg_row[0] or 0.0)
        rev2 = float(agg_row[1] or 0.0)
        delta = round(rev2 - rev1, 2)
        pct_change = round((delta / rev1) * 100, 2) if rev1 > 0 else 0.0

        # Step 2: Decompose by Product
        cursor.execute(f"""
            WITH p1 AS (
                SELECT product, SUM(net_revenue) AS r1 FROM {view} WHERE order_month = :m1 GROUP BY product
            ),
            p2 AS (
                SELECT product, SUM(net_revenue) AS r2 FROM {view} WHERE order_month = :m2 GROUP BY product
            )
            SELECT 
                COALESCE(p1.product, p2.product) AS product,
                COALESCE(p1.r1, 0) AS rev_m1,
                COALESCE(p2.r2, 0) AS rev_m2,
                ROUND(COALESCE(p2.r2, 0) - COALESCE(p1.r1, 0), 2) AS diff
            FROM p1
            FULL OUTER JOIN p2 ON p1.product = p2.product
            ORDER BY diff DESC;
        """, {"m1": m1_iso, "m2": m2_iso})
        product_deltas = [dict(r) for r in cursor.fetchall()]

        # Fallback if SQLite version lacks FULL OUTER JOIN
        if not product_deltas:
            cursor.execute(f"""
                SELECT 
                    product,
                    ROUND(COALESCE(SUM(CASE WHEN order_month = :m2 THEN net_revenue ELSE 0 END) - 
                          SUM(CASE WHEN order_month = :m1 THEN net_revenue ELSE 0 END), 0), 2) AS diff,
                    ROUND(COALESCE(SUM(CASE WHEN order_month = :m1 THEN net_revenue ELSE 0 END), 0), 2) AS rev_m1,
                    ROUND(COALESCE(SUM(CASE WHEN order_month = :m2 THEN net_revenue ELSE 0 END), 0), 2) AS rev_m2
                FROM {view}
                WHERE order_month IN (:m1, :m2)
                GROUP BY product
                ORDER BY diff DESC;
            """, {"m1": m1_iso, "m2": m2_iso})
            product_deltas = [dict(r) for r in cursor.fetchall()]

        # Step 3: Decompose by Region
        cursor.execute(f"""
            SELECT 
                region,
                ROUND(COALESCE(SUM(CASE WHEN order_month = :m2 THEN net_revenue ELSE 0 END) - 
                      SUM(CASE WHEN order_month = :m1 THEN net_revenue ELSE 0 END), 0), 2) AS diff,
                ROUND(COALESCE(SUM(CASE WHEN order_month = :m1 THEN net_revenue ELSE 0 END), 0), 2) AS rev_m1,
                ROUND(COALESCE(SUM(CASE WHEN order_month = :m2 THEN net_revenue ELSE 0 END), 0), 2) AS rev_m2
            FROM {view}
            WHERE order_month IN (:m1, :m2)
            GROUP BY region
            ORDER BY diff DESC;
        """, {"m1": m1_iso, "m2": m2_iso})
        region_deltas = [dict(r) for r in cursor.fetchall()]

        # Step 4: Decompose by Channel
        cursor.execute(f"""
            SELECT 
                sales_channel,
                ROUND(COALESCE(SUM(CASE WHEN order_month = :m2 THEN net_revenue ELSE 0 END) - 
                      SUM(CASE WHEN order_month = :m1 THEN net_revenue ELSE 0 END), 0), 2) AS diff
            FROM {view}
            WHERE order_month IN (:m1, :m2)
            GROUP BY sales_channel
            ORDER BY diff DESC;
        """, {"m1": m1_iso, "m2": m2_iso})
        channel_deltas = [dict(r) for r in cursor.fetchall()]

        # Identify key drivers
        top_positive_products = [p for p in product_deltas if p["diff"] > 0][:2]
        top_negative_products = [p for p in sorted(product_deltas, key=lambda x: x["diff"]) if p["diff"] < 0][:2]
        top_region = region_deltas[0] if region_deltas else None

        # Build narrative
        direction = "increased" if delta > 0 else "decreased"
        sign = "+" if delta > 0 else ""
        
        narrative_parts = [
            f"Net revenue {direction} by {sign}{format_inr(delta)} ({format_percentage(pct_change)}) "
            f"from {format_inr(rev1)} ({m1_iso}) to {format_inr(rev2)} ({m2_iso})."
        ]

        if top_positive_products:
            top_pos_str = ", ".join([f"{p['product']} (+{format_inr(p['diff'])})" for p in top_positive_products])
            narrative_parts.append(f"Primary growth was driven by {top_pos_str}.")

        if top_negative_products:
            top_neg_str = ", ".join([f"{p['product']} ({format_inr(p['diff'])})" for p in top_negative_products])
            narrative_parts.append(f"Offsetting declines occurred in {top_neg_str}.")

        if top_region and top_region["diff"] != 0:
            reg_sign = "+" if top_region["diff"] > 0 else ""
            narrative_parts.append(f"Top regional shift: {top_region['region']} ({reg_sign}{format_inr(top_region['diff'])}).")

        full_narrative = " ".join(narrative_parts)

        # Build waterfall chart data
        waterfall_labels = [m1_iso] + [p["product"] for p in product_deltas if abs(p["diff"]) > 0] + [m2_iso]
        waterfall_values = [rev1] + [p["diff"] for p in product_deltas if abs(p["diff"]) > 0] + [rev2]

        chart_spec = {
            "type": "bar",
            "title": f"Variance Drivers: {m1_iso} to {m2_iso}",
            "labels": [p["product"] for p in product_deltas],
            "datasets": [{
                "label": "Net Revenue Impact (₹)",
                "data": [p["diff"] for p in product_deltas],
                "backgroundColor": ["#10b981" if p["diff"] >= 0 else "#ef4444" for p in product_deltas]
            }]
        }

        return {
            "m1": m1_iso,
            "m2": m2_iso,
            "rev1": rev1,
            "rev2": rev2,
            "delta": delta,
            "pct_change": pct_change,
            "narrative": full_narrative,
            "product_deltas": product_deltas,
            "region_deltas": region_deltas,
            "channel_deltas": channel_deltas,
            "chart_spec": chart_spec
        }
