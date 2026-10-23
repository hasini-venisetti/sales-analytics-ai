"""Business metrics single source of truth and formatting utilities."""
from typing import Any, Dict


def format_inr(amount: float) -> str:
    """Format a numeric value using Indian currency notation (₹14,39,200)."""
    if amount is None:
        return "₹0"
    is_negative = amount < 0
    amount = abs(amount)
    rounded = round(amount, 2)
    s, *d = f"{rounded:.2f}".split(".")
    cents = f".{d[0]}" if d and d[0] != "00" else ""
    
    if len(s) <= 3:
        formatted = s
    else:
        last3 = s[-3:]
        rest = s[:-3]
        groups = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        formatted = ",".join(groups) + "," + last3
        
    prefix = "-₹" if is_negative else "₹"
    return f"{prefix}{formatted}{cents}"


def format_percentage(value: float, decimal_places: int = 2) -> str:
    """Format a percentage with sign and decimal places (+7.50%)."""
    prefix = "+" if value > 0 else ""
    return f"{prefix}{value:.{decimal_places}f}%"


# Formal Business Definitions (displayed on UI Proof Panels)
METRICS_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "net_revenue": {
        "name": "Net Revenue",
        "formula": "(Quantity * Unit_price) - Discount_amount",
        "description": "Default revenue figure representing actual realized sales after discounts.",
        "default_scope": "Status = 'Completed' AND Quantity > 0 AND Unit_price IS NOT NULL",
    },
    "gross_revenue": {
        "name": "Gross Revenue",
        "formula": "Quantity * Unit_price",
        "description": "Total value of products ordered before discounts.",
        "default_scope": "Status = 'Completed' AND Quantity > 0 AND Unit_price IS NOT NULL",
    },
    "returns_value": {
        "name": "Returns Value",
        "formula": "SUM(gross_revenue) WHERE Status = 'Returned'",
        "description": "Total gross value of returned orders (quarantined from revenue calculations).",
        "default_scope": "Status = 'Returned'",
    },
    "aov": {
        "name": "Average Order Value (AOV)",
        "formula": "SUM(net_revenue) / COUNT(Transaction_Id)",
        "description": "Average net revenue realized per completed order.",
        "default_scope": "Status = 'Completed' AND Quantity > 0 AND Unit_price IS NOT NULL",
    },
    "discount_impact": {
        "name": "Discount Impact",
        "formula": "(SUM(Discount_amount) / SUM(gross_revenue)) * 100",
        "description": "Percentage of total gross merchandise value absorbed by discounts.",
        "default_scope": "Status = 'Completed' AND Quantity > 0 AND Unit_price IS NOT NULL",
    },
}
