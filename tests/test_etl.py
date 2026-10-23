"""Unit tests for ETL pipeline and data quality verification."""
from pathlib import Path
import pytest
import sqlite3

from app.data.etl import run_etl
from app.config import DATA_CSV_PATH


def test_etl_missing_file_raises_error(tmp_path: Path):
    """Ensure missing CSV raises FileNotFoundError without generating mock data."""
    missing_csv = tmp_path / "non_existent.csv"
    test_db = tmp_path / "test.db"
    with pytest.raises(FileNotFoundError) as exc_info:
        run_etl(csv_path=missing_csv, db_path=test_db)
    assert "Required sales dataset not found" in str(exc_info.value)


def test_etl_row_counts_and_quarantine(tmp_path: Path):
    """Verify exactly 51 rows loaded, 48 valid completed, and 3 quarantined."""
    test_db = tmp_path / "test_sales.db"
    conn, report = run_etl(csv_path=DATA_CSV_PATH, db_path=test_db)
    
    assert report.total_rows_loaded == 51
    assert report.valid_rows_count == 48
    assert report.quarantined_rows_count == 3
    assert report.returned_rows_count == 1
    assert report.returns_value == 19000.0  # TXN0033: 2 * 9500 = 19000

    # Verify SQLite tables
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sales;")
    assert cursor.fetchone()[0] == 51

    cursor.execute("SELECT COUNT(*) FROM sales_quarantine;")
    assert cursor.fetchone()[0] == 3

    # Verify valid view has 48 rows
    cursor.execute("SELECT COUNT(*) FROM v_sales_valid;")
    assert cursor.fetchone()[0] == 48

    # Verify view with returns has 49 rows (48 completed + 1 returned)
    cursor.execute("SELECT COUNT(*) FROM v_sales_with_returns;")
    assert cursor.fetchone()[0] == 49


def test_date_parsing_dd_mm_yyyy(tmp_path: Path):
    """Verify dd-mm-yyyy parsing: TXN0001 (03-01-2026) is Jan 3, 2026."""
    test_db = tmp_path / "test_dates.db"
    conn, _ = run_etl(csv_path=DATA_CSV_PATH, db_path=test_db)
    
    cursor = conn.cursor()
    cursor.execute("SELECT order_date, order_date_iso, order_month FROM sales WHERE transaction_id = 'TXN0001';")
    row = cursor.fetchone()
    assert row[0] == "03-01-2026"
    assert row[1] == "2026-01-03"
    assert row[2] == "2026-01"
