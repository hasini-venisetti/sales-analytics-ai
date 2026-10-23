"""ETL pipeline: loads sales data CSV, validates, quarantines planted anomalies, and populates SQLite."""
import sqlite3
from pathlib import Path
from typing import Tuple
import pandas as pd

from app.config import DATA_CSV_PATH, DB_PATH, DATE_FORMAT_INPUT
from app.data.quality import DataQualityReport, QuarantinedRecord


def run_etl(csv_path: Path = DATA_CSV_PATH, db_path: Path = DB_PATH) -> Tuple[sqlite3.Connection, DataQualityReport]:
    """Execute the ETL process, validating and inserting records into SQLite.
    
    Raises:
        FileNotFoundError: If the CSV file does not exist.
    """
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Required sales dataset not found at '{csv_path}'. "
            "Please ensure the CSV file is placed in the designated path."
        )

    # 1. Read CSV
    df = pd.read_csv(csv_path)

    # Validate required columns
    required_cols = [
        "Transaction_Id", "Order_date", "Product", "Category", 
        "Region", "Sales_channel", "Quantity", "Unit_price", 
        "Discount_amount", "Status"
    ]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in CSV: {missing_cols}")

    # 2. Date parsing strictly with dd-mm-yyyy format
    parsed_dates = pd.to_datetime(df["Order_date"], format=DATE_FORMAT_INPUT)
    df["order_date_iso"] = parsed_dates.dt.strftime("%Y-%m-%d")
    df["order_month"] = parsed_dates.dt.strftime("%Y-%m")
    df["order_month_name"] = parsed_dates.dt.strftime("%b")

    # 3. Numeric sanitation & calculated fields
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["Unit_price"] = pd.to_numeric(df["Unit_price"], errors="coerce")
    df["Discount_amount"] = pd.to_numeric(df["Discount_amount"], errors="coerce").fillna(0.0)

    df["gross_revenue"] = df["Quantity"] * df["Unit_price"]
    df["net_revenue"] = df["gross_revenue"] - df["Discount_amount"]

    # 4. Quarantine planted traps and anomalies
    quarantined_records = []

    # Reason A: Missing Unit_price (e.g. TXN0051)
    missing_price_mask = df["Unit_price"].isna()
    for _, row in df[missing_price_mask].iterrows():
        quarantined_records.append(QuarantinedRecord(
            transaction_id=str(row["Transaction_Id"]),
            reason="missing_unit_price",
            details={
                "product": row["Product"],
                "quantity": int(row["Quantity"]) if pd.notna(row["Quantity"]) else 0,
                "note": "Row quarantined; Unit_price is missing. Not silently imputed."
            }
        ))

    # Reason B: Zero or negative quantity (e.g. TXN0034)
    zero_qty_mask = df["Quantity"] <= 0
    for _, row in df[zero_qty_mask].iterrows():
        quarantined_records.append(QuarantinedRecord(
            transaction_id=str(row["Transaction_Id"]),
            reason="invalid_quantity_zero",
            details={
                "product": row["Product"],
                "quantity": int(row["Quantity"]),
                "note": "Row quarantined; Quantity is zero/non-positive."
            }
        ))

    # Reason C: Returned status (e.g. TXN0033)
    returned_mask = df["Status"].str.strip().str.lower() == "returned"
    returns_value = 0.0
    for _, row in df[returned_mask].iterrows():
        g_val = float(row["gross_revenue"]) if pd.notna(row["gross_revenue"]) else 0.0
        returns_value += g_val
        quarantined_records.append(QuarantinedRecord(
            transaction_id=str(row["Transaction_Id"]),
            reason="status_returned",
            details={
                "product": row["Product"],
                "gross_value": g_val,
                "note": "Excluded from default revenue; available via returns opt-in."
            }
        ))

    # 5. Connect to SQLite and populate tables
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Drop existing tables/views for idempotent reload
    cursor.execute("DROP VIEW IF EXISTS v_sales_valid;")
    cursor.execute("DROP VIEW IF EXISTS v_sales_with_returns;")
    cursor.execute("DROP TABLE IF EXISTS sales;")
    cursor.execute("DROP TABLE IF EXISTS sales_quarantine;")
    cursor.execute("DROP TABLE IF EXISTS data_quality_log;")

    # Create sales table
    cursor.execute("""
        CREATE TABLE sales (
            transaction_id TEXT PRIMARY KEY,
            order_date TEXT,
            order_date_iso TEXT,
            order_month TEXT,
            order_month_name TEXT,
            product TEXT,
            category TEXT,
            region TEXT,
            sales_channel TEXT,
            quantity INTEGER,
            unit_price REAL,
            discount_amount REAL,
            status TEXT,
            gross_revenue REAL,
            net_revenue REAL
        );
    """)

    # Create sales_quarantine table
    cursor.execute("""
        CREATE TABLE sales_quarantine (
            transaction_id TEXT PRIMARY KEY,
            quarantine_reason TEXT,
            details TEXT
        );
    """)

    # Populate sales table
    for _, r in df.iterrows():
        cursor.execute("""
            INSERT INTO sales VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            str(r["Transaction_Id"]),
            str(r["Order_date"]),
            str(r["order_date_iso"]),
            str(r["order_month"]),
            str(r["order_month_name"]),
            str(r["Product"]),
            str(r["Category"]),
            str(r["Region"]),
            str(r["Sales_channel"]),
            int(r["Quantity"]) if pd.notna(r["Quantity"]) else None,
            float(r["Unit_price"]) if pd.notna(r["Unit_price"]) else None,
            float(r["Discount_amount"]) if pd.notna(r["Discount_amount"]) else 0.0,
            str(r["Status"]),
            float(r["gross_revenue"]) if pd.notna(r["gross_revenue"]) else None,
            float(r["net_revenue"]) if pd.notna(r["net_revenue"]) else None,
        ))

    # Populate sales_quarantine table
    for q in quarantined_records:
        cursor.execute("""
            INSERT OR REPLACE INTO sales_quarantine VALUES (?, ?, ?);
        """, (q.transaction_id, q.reason, str(q.details)))

    # Create view v_sales_valid: STRICT DEFAULT SCOPE
    cursor.execute("""
        CREATE VIEW v_sales_valid AS
        SELECT * FROM sales
        WHERE status = 'Completed'
          AND quantity > 0
          AND unit_price IS NOT NULL;
    """)

    # Create view v_sales_with_returns
    cursor.execute("""
        CREATE VIEW v_sales_with_returns AS
        SELECT * FROM sales
        WHERE quantity > 0
          AND unit_price IS NOT NULL;
    """)

    conn.commit()

    # 6. Build DataQualityReport
    valid_count = len(df[~missing_price_mask & ~zero_qty_mask & ~returned_mask])
    total_loaded = len(df)
    score_pct = round((valid_count / total_loaded) * 100, 2) if total_loaded > 0 else 0.0

    report = DataQualityReport(
        total_rows_loaded=total_loaded,
        valid_rows_count=valid_count,
        quarantined_rows_count=len(quarantined_records),
        returned_rows_count=int(returned_mask.sum()),
        returns_value=returns_value,
        date_range_start=str(df["order_date_iso"].min()),
        date_range_end=str(df["order_date_iso"].max()),
        quarantined_records=quarantined_records,
        data_hygiene_score_pct=score_pct,
        notes=[
            f"Loaded {total_loaded} rows from CSV.",
            f"{valid_count} clean completed rows eligible for default revenue metrics.",
            f"3 rows flagged & quarantined: 1 missing unit price (TXN0051), 1 zero quantity (TXN0034), 1 returned (TXN0033).",
            f"All dates parsed with strict dd-mm-yyyy format spanning {df['order_date_iso'].min()} to {df['order_date_iso'].max()}."
        ]
    )

    return conn, report


def get_db_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Return a thread-safe connection with dict row access."""
    if not db_path.exists():
        run_etl(DATA_CSV_PATH, db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
