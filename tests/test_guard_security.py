"""Red-Team Security and Injection Test Suite for SQL Guard."""
import pytest
from app.core.guard import SQLGuard, SQLSecurityError


def test_guard_valid_select_queries():
    """Verify clean SELECT statements pass AST inspection and receive row limits."""
    valid1 = "SELECT product, SUM(net_revenue) AS rev FROM v_sales_valid GROUP BY product"
    sanitized1 = SQLGuard.validate_and_sanitize(valid1)
    assert "LIMIT 500" in sanitized1

    valid2 = "SELECT transaction_id, order_date, region FROM sales WHERE region = 'North' LIMIT 10"
    sanitized2 = SQLGuard.validate_and_sanitize(valid2)
    assert "LIMIT 10" in sanitized2


def test_guard_rejects_destructive_dml_and_ddl():
    """Verify DROP, DELETE, INSERT, UPDATE, ALTER are blocked before execution."""
    attacks = [
        "DROP TABLE sales",
        "DELETE FROM sales WHERE quantity > 0",
        "INSERT INTO sales (transaction_id) VALUES ('HACK')",
        "UPDATE sales SET net_revenue = 0",
        "ALTER TABLE sales ADD COLUMN hacked TEXT",
        "TRUNCATE TABLE sales",
        "ATTACH DATABASE 'hack.db' AS hack",
        "PRAGMA database_list"
    ]
    for attack in attacks:
        with pytest.raises(SQLSecurityError):
            SQLGuard.validate_and_sanitize(attack)


def test_guard_rejects_sql_comments_and_chaining():
    """Verify comment injection and stacked semicolon queries are blocked."""
    attacks = [
        "SELECT * FROM sales -- comment injection",
        "SELECT * FROM sales /* inline comment */ WHERE quantity > 0",
        "SELECT * FROM sales; SELECT * FROM sales_quarantine;",
        "SELECT 1; DROP TABLE sales;"
    ]
    for attack in attacks:
        with pytest.raises(SQLSecurityError):
            SQLGuard.validate_and_sanitize(attack)


def test_guard_rejects_hallucinated_columns_and_tables():
    """Verify unauthorized tables and non-existent columns are blocked."""
    with pytest.raises(SQLSecurityError) as exc_table:
        SQLGuard.validate_and_sanitize("SELECT * FROM passwords")
    assert "Unauthorized table" in str(exc_table.value)

    with pytest.raises(SQLSecurityError) as exc_col:
        SQLGuard.validate_and_sanitize("SELECT fake_column_name FROM v_sales_valid")
    assert "Hallucinated or unauthorized column" in str(exc_col.value)
