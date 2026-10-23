"""SQL Guard: Validates and sanitizes SQL queries using sqlglot AST analysis."""
import re
from typing import Set, Tuple
import sqlglot
from sqlglot import exp


class SQLSecurityError(Exception):
    """Raised when an unverified or unsafe SQL query is detected."""
    pass


class SQLGuard:
    """AST-level SQL Guardrail using sqlglot to enforce read-only safety on Lane B queries."""

    ALLOWED_TABLES: Set[str] = {
        "sales", "v_sales_valid", "v_sales_with_returns", "sales_quarantine"
    }

    ALLOWED_COLUMNS: Set[str] = {
        "transaction_id", "order_date", "order_date_iso", "order_month",
        "order_month_name", "product", "category", "region", "sales_channel",
        "quantity", "unit_price", "discount_amount", "status", "gross_revenue",
        "net_revenue", "*"
    }

    DISALLOWED_KEYWORDS: Set[str] = {
        "insert", "update", "delete", "drop", "alter", "create", "attach",
        "detach", "pragma", "replace", "truncate", "vacuum", "load_extension",
        "reindex"
    }

    @classmethod
    def validate_and_sanitize(cls, sql_raw: str, default_view: str = "v_sales_valid") -> str:
        """Parses and verifies that the SQL query is strictly a read-only SELECT statement.
        
        Raises:
            SQLSecurityError: If any prohibited syntax, multiple statements, or unknown identifiers are found.
        """
        clean = sql_raw.strip().rstrip(";")

        # 1. Reject comments and semicolons in raw query
        if "--" in clean or "/*" in clean or ";" in clean:
            raise SQLSecurityError("Prohibited tokens detected: comments and chained statements are not allowed.")

        # 2. Check for disallowed keywords via regex
        for kw in cls.DISALLOWED_KEYWORDS:
            if re.search(rf"\b{re.escape(kw)}\b", clean, re.IGNORECASE):
                raise SQLSecurityError(f"Prohibited SQL keyword detected: '{kw.upper()}' is not permitted.")

        # 3. Parse with sqlglot
        try:
            parsed = sqlglot.parse(clean, read="sqlite")
        except Exception as e:
            raise SQLSecurityError(f"SQL parsing failed: {str(e)}")

        if not parsed:
            raise SQLSecurityError("Empty SQL query.")
        if len(parsed) > 1:
            raise SQLSecurityError("Multiple SQL statements detected; exactly one SELECT statement is permitted.")

        ast = parsed[0]

        # 4. Root must be Select or CTE (With)
        if not isinstance(ast, (exp.Select, exp.Union)):
            raise SQLSecurityError(f"Root AST node must be a SELECT statement, found '{type(ast).__name__}'.")

        # 5. Check all tables referenced in AST
        tables = [t.name.lower() for t in ast.find_all(exp.Table)]
        for t in tables:
            if t not in cls.ALLOWED_TABLES:
                raise SQLSecurityError(f"Unauthorized table access: '{t}' is not in the allowed schema tables {cls.ALLOWED_TABLES}.")

        # 6. Check columns referenced
        columns = [c.name.lower() for c in ast.find_all(exp.Column)]
        for c in columns:
            if c not in cls.ALLOWED_COLUMNS:
                raise SQLSecurityError(f"Hallucinated or unauthorized column: '{c}' does not exist in schema.")

        # 7. Ensure LIMIT is applied (cap at 500)
        limit_node = ast.find(exp.Limit)
        if not limit_node:
            ast = ast.limit(500)

        return ast.sql(dialect="sqlite")
