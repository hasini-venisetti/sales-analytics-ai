"""Test for Gemini LLM Provider and Lane B text-to-sql generation."""
import os
import pytest
from app.llm.gemini import GeminiProvider
from app.core.guard import SQLGuard


def test_gemini_provider_live_or_skipped():
    """Verify GeminiProvider drafts valid SQL when key is configured."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        pytest.skip("GEMINI_API_KEY not configured, skipping live LLM test.")

    provider = GeminiProvider(model_name="gemini-3.8-flash")
    assert provider.is_available() is True

    # Ask an open-ended question
    question = "Show me keyboard orders in the North region with quantity and net revenue"
    result = provider.draft_sql(question)
    
    assert "sql" in result
    sql = result["sql"]
    assert "SELECT" in sql.upper()
    assert "v_sales_valid" in sql or "sales" in sql

    # Ensure SQLGuard validates the LLM-generated SQL
    sanitized = SQLGuard.validate_and_sanitize(sql)
    assert "LIMIT" in sanitized
