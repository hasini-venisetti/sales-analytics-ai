"""Rule-Based Intent Classifier & Parameter Extractor for Zero-Key Execution."""
import re
from typing import Any, Dict, List, Optional
from app.core.vectorless_rag import VectorlessRAG


class RuleBasedProvider:
    """Deterministic natural language classifier that guarantees core queries work with 0 API keys."""

    DESTRUCTIVE_KEYWORDS = [
        "drop", "delete", "insert", "update", "truncate", "alter", 
        "attach", "pragma", "shutdown", "exec", "--", ";", "/*"
    ]

    UNSUPPORTED_KEYWORDS = [
        "predict", "forecast", "future", "next year", "weather", 
        "stock price", "competitor", "ceo", "hire", "salary"
    ]

    def __init__(self, rag: Optional[VectorlessRAG] = None):
        self.rag = rag or VectorlessRAG()

    def classify(self, query: str) -> Dict[str, Any]:
        """Classifies user question into Lane A, Lane B, or Lane C with parameters."""
        q = query.strip()
        q_lower = q.lower()

        # 1. Check for destructive/security attacks -> Lane C
        for kw in self.DESTRUCTIVE_KEYWORDS:
            if kw in ("--", ";", "/*"):
                if kw in q_lower:
                    is_attack = True
                else:
                    is_attack = False
            else:
                is_attack = bool(re.search(rf"\b{re.escape(kw)}\b", q_lower))
            
            if is_attack:
                return {
                    "lane": "C",
                    "intent": "refusal_security",
                    "params": {},
                    "confidence": 1.0,
                    "refusal_reason": "Destructive, administrative, or non-SELECT operations are prohibited for data safety.",
                    "suggestions": [
                        "What is our total net revenue?",
                        "Which product had the highest revenue?",
                        "How did revenue change between March and April?"
                    ]
                }

        # 2. Check for unsupported/future forecasting -> Lane C
        for kw in self.UNSUPPORTED_KEYWORDS:
            if kw in q_lower:
                return {
                    "lane": "C",
                    "intent": "refusal_unsupported",
                    "params": {},
                    "confidence": 0.95,
                    "refusal_reason": f"The query requests speculative forecasting or external data. Our database contains historical sales data from January to June 2026.",
                    "suggestions": [
                        "Show monthly revenue trend for Jan to Jun 2026",
                        "Which month had the peak revenue?",
                        "How did revenue change between March and April?"
                    ]
                }

        # 3. Retrieve domain context via Vectorless RAG
        context = self.rag.retrieve(q)
        entities = context["matched_entities"]

        # Month extraction for comparisons
        months_found = entities.get("months", [])
        # Check explicit month words in text
        month_order = []
        month_words = [
            ("jan", "2026-01"), ("feb", "2026-02"), ("mar", "2026-03"), 
            ("apr", "2026-04"), ("may", "2026-05"), ("jun", "2026-06")
        ]
        for word, iso_m in month_words:
            if re.search(rf"\b{word}", q_lower):
                if iso_m not in month_order:
                    month_order.append(iso_m)

        # 4. Pattern matching for Lane A Intents

        # Q5: Revenue Change between two periods
        if ("change" in q_lower or "difference" in q_lower or "diff" in q_lower or "compare" in q_lower or "growth" in q_lower) and len(month_order) >= 2:
            return {
                "lane": "A",
                "intent": "revenue_change",
                "params": {"month1": month_order[0], "month2": month_order[1]},
                "confidence": 0.98
            }
        
        # Specific driver questions
        if "why did may spike" in q_lower or "may spike" in q_lower or "may peak" in q_lower:
            return {
                "lane": "A",
                "intent": "revenue_change",
                "params": {"month1": "2026-04", "month2": "2026-05", "driver_focus": "May spike"},
                "confidence": 0.99
            }
        if "why did june drop" in q_lower or "june drop" in q_lower or "june fall" in q_lower:
            return {
                "lane": "A",
                "intent": "revenue_change",
                "params": {"month1": "2026-05", "month2": "2026-06", "driver_focus": "June drop"},
                "confidence": 0.99
            }

        # Q1: Total Revenue
        if any(p in q_lower for p in ["total revenue", "total sales", "overall revenue", "overall sales", "total net revenue", "how much revenue", "how much money did we make", "entire revenue"]):
            return {"lane": "A", "intent": "total_revenue", "params": {}, "confidence": 0.99}
        if q_lower in ["revenue", "sales", "total"]:
            return {"lane": "A", "intent": "total_revenue", "params": {}, "confidence": 0.95}

        # Q2: Top Product
        product_top_signals = [
            "product with highest revenue", "top product", "highest revenue product", 
            "best selling product", "highest sales product", "top selling product", 
            "products by revenue", "product ranking", "which product made the most",
            "which product has the highest revenue", "which product generated the most revenue"
        ]
        if any(p in q_lower for p in product_top_signals) or ("highest revenue" in q_lower and "product" in q_lower) or ("top" in q_lower and "product" in q_lower):
            limit = 1 if ("the top" in q_lower or "which product" in q_lower or "highest" in q_lower) else 10
            return {"lane": "A", "intent": "top_product", "params": {"limit": limit}, "confidence": 0.98}

        # Q3: Monthly Trend
        if any(p in q_lower for p in ["monthly revenue", "monthly trend", "revenue trend", "month by month", "revenue over time", "sales by month", "monthly sales", "monthly breakdown"]):
            return {"lane": "A", "intent": "monthly_trend", "params": {}, "confidence": 0.98}

        # Q4: Top Region
        region_top_signals = [
            "region with highest", "top region", "highest sales region", "best region", 
            "regional sales", "revenue by region", "sales by region", "which region",
            "region had highest sales", "region has highest sales"
        ]
        if any(p in q_lower for p in region_top_signals) or ("highest sales" in q_lower and "region" in q_lower) or ("top" in q_lower and "region" in q_lower):
            limit = 1 if ("the top" in q_lower or "which region" in q_lower or "highest" in q_lower) else 10
            return {"lane": "A", "intent": "top_region", "params": {"limit": limit}, "confidence": 0.98}

        # Extra: Category
        if "category" in q_lower or "categories" in q_lower:
            return {"lane": "A", "intent": "revenue_by_category", "params": {}, "confidence": 0.95}

        # Extra: Channel
        if "channel" in q_lower or "online vs retail" in q_lower or "retail vs online" in q_lower:
            return {"lane": "A", "intent": "revenue_by_channel", "params": {}, "confidence": 0.95}

        # Extra: Units / Quantity
        if any(p in q_lower for p in ["units sold", "how many units", "quantity sold", "volume by product"]):
            return {"lane": "A", "intent": "units_sold_product", "params": {}, "confidence": 0.92}
        if "units by region" in q_lower or "quantity by region" in q_lower:
            return {"lane": "A", "intent": "units_sold_region", "params": {}, "confidence": 0.92}

        # Extra: AOV
        if any(p in q_lower for p in ["aov", "average order value", "average order", "order average"]):
            return {"lane": "A", "intent": "average_order_value", "params": {}, "confidence": 0.98}

        # Extra: Discount Impact
        if any(p in q_lower for p in ["discount", "discounts", "discount impact", "total discount"]):
            return {"lane": "A", "intent": "discount_impact", "params": {}, "confidence": 0.95}

        # Extra: Returns Summary
        if any(p in q_lower for p in ["returned", "returns", "return rate", "refunds"]):
            return {"lane": "A", "intent": "returns_summary", "params": {}, "confidence": 0.98}

        # If entities matched a specific single product, region, or month
        if entities.get("products") and len(entities["products"]) == 1:
            prod = entities["products"][0]
            return {
                "lane": "B",
                "intent": "product_specific_query",
                "params": {"product": prod},
                "confidence": 0.85
            }

        # Default fallback to Lane B for general natural language question
        return {
            "lane": "B",
            "intent": "open_question",
            "params": {"raw_query": q},
            "confidence": 0.70
        }
