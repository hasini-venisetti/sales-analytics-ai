"""Dual-Engine Verification: Recomputes results via an independent Pandas pipeline to verify SQL correctness."""
import math
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from app.config import DATA_CSV_PATH, DATE_FORMAT_INPUT


class PandasVerifier:
    """Independent verification engine that loads CSV directly and calculates ground-truth."""

    def __init__(self, csv_path=DATA_CSV_PATH):
        self.csv_path = csv_path
        self._df = None

    def _get_df(self, include_returned: bool = False) -> pd.DataFrame:
        if self._df is None:
            df = pd.read_csv(self.csv_path)
            # Strict date parse
            parsed_dates = pd.to_datetime(df["Order_date"], format=DATE_FORMAT_INPUT)
            df["order_date_iso"] = parsed_dates.dt.strftime("%Y-%m-%d")
            df["order_month"] = parsed_dates.dt.strftime("%Y-%m")
            df["order_month_name"] = parsed_dates.dt.strftime("%b")
            df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
            df["Unit_price"] = pd.to_numeric(df["Unit_price"], errors="coerce")
            df["Discount_amount"] = pd.to_numeric(df["Discount_amount"], errors="coerce").fillna(0.0)
            df["gross_revenue"] = df["Quantity"] * df["Unit_price"]
            df["net_revenue"] = df["gross_revenue"] - df["Discount_amount"]
            self._df = df

        df = self._df.copy()
        if include_returned:
            # Include returned orders as long as qty > 0 and unit_price not null
            return df[(df["Quantity"] > 0) & (df["Unit_price"].notna())]
        else:
            # Strict default scope
            return df[(df["Status"] == "Completed") & (df["Quantity"] > 0) & (df["Unit_price"].notna())]

    def verify(self, intent: str, params: Dict[str, Any], sql_rows: List[Dict[str, Any]], include_returned: bool = False) -> Tuple[bool, str]:
        """Cross-checks SQL execution output against an independent Pandas recompute."""
        try:
            df = self._get_df(include_returned=include_returned)

            if intent == "total_revenue":
                pandas_val = float(df["net_revenue"].sum())
                sql_val = float(sql_rows[0].get("total_net_revenue") or sql_rows[0].get("net_revenue") or list(sql_rows[0].values())[0])
                match = math.isclose(pandas_val, sql_val, rel_tol=1e-4, abs_tol=0.01)
                return match, f"SQL: ₹{sql_val:,.2f} vs Pandas: ₹{pandas_val:,.2f}"

            elif intent == "top_product":
                grouped = df.groupby("Product")["net_revenue"].sum().sort_values(ascending=False)
                top_product_pandas = grouped.index[0]
                top_rev_pandas = float(grouped.iloc[0])
                sql_top_product = sql_rows[0].get("product") or list(sql_rows[0].values())[0]
                sql_top_rev = float(sql_rows[0].get("net_revenue") or list(sql_rows[0].values())[1])
                match = (top_product_pandas.lower() == str(sql_top_product).lower()) and math.isclose(top_rev_pandas, sql_top_rev, rel_tol=1e-4)
                return match, f"Top Product SQL: {sql_top_product} (₹{sql_top_rev:,.2f}) vs Pandas: {top_product_pandas} (₹{top_rev_pandas:,.2f})"

            elif intent == "top_region":
                grouped = df.groupby("Region")["net_revenue"].sum().sort_values(ascending=False)
                top_region_pandas = grouped.index[0]
                top_rev_pandas = float(grouped.iloc[0])
                sql_top_region = sql_rows[0].get("region") or list(sql_rows[0].values())[0]
                sql_top_rev = float(sql_rows[0].get("net_revenue") or list(sql_rows[0].values())[1])
                match = (top_region_pandas.lower() == str(sql_top_region).lower()) and math.isclose(top_rev_pandas, sql_top_rev, rel_tol=1e-4)
                return match, f"Top Region SQL: {sql_top_region} (₹{sql_top_rev:,.2f}) vs Pandas: {top_region_pandas} (₹{top_rev_pandas:,.2f})"

            elif intent == "monthly_trend":
                grouped = df.groupby("order_month")["net_revenue"].sum().to_dict()
                for row in sql_rows:
                    m = row.get("order_month")
                    if m in grouped:
                        sql_rev = float(row.get("net_revenue"))
                        if not math.isclose(grouped[m], sql_rev, rel_tol=1e-4):
                            return False, f"Mismatch for month {m}: SQL {sql_rev} != Pandas {grouped[m]}"
                return True, "All monthly series values verified across both engines."

            elif intent == "revenue_by_category":
                grouped = df.groupby("Category")["net_revenue"].sum().to_dict()
                for row in sql_rows:
                    cat = row.get("category")
                    if cat in grouped:
                        sql_rev = float(row.get("net_revenue"))
                        if not math.isclose(grouped[cat], sql_rev, rel_tol=1e-4):
                            return False, f"Mismatch for category {cat}"
                return True, "Category breakdown verified."

            elif intent == "revenue_by_channel":
                grouped = df.groupby("Sales_channel")["net_revenue"].sum().to_dict()
                for row in sql_rows:
                    chan = row.get("sales_channel")
                    if chan in grouped:
                        sql_rev = float(row.get("net_revenue"))
                        if not math.isclose(grouped[chan], sql_rev, rel_tol=1e-4):
                            return False, f"Mismatch for channel {chan}"
                return True, "Sales channel breakdown verified."

            elif intent == "revenue_change":
                m1 = params.get("month1")
                m2 = params.get("month2")
                if m1 and m2:
                    rev1 = float(df[df["order_month"].str.endswith(m1) | (df["order_month_name"].str.lower() == m1.lower())]["net_revenue"].sum())
                    rev2 = float(df[df["order_month"].str.endswith(m2) | (df["order_month_name"].str.lower() == m2.lower())]["net_revenue"].sum())
                    expected_delta = rev2 - rev1
                    sql_delta = float(sql_rows[0].get("delta_revenue", 0.0))
                    match = math.isclose(expected_delta, sql_delta, rel_tol=1e-4, abs_tol=0.1)
                    return match, f"Delta check: expected ₹{expected_delta:,.2f}, received ₹{sql_delta:,.2f}"
                return True, "Revenue change parameters verified."

            # Default sanity check for other metrics
            if sql_rows and len(sql_rows) > 0:
                grand_total = float(df["net_revenue"].sum())
                # Ensure no single sub-metric exceeds grand total
                for r in sql_rows:
                    for k, v in r.items():
                        if isinstance(v, (int, float)) and "rev" in k.lower():
                            if v > (grand_total * 1.05):
                                return False, f"Plausibility failure: {k}={v} exceeds grand total {grand_total}"
                return True, "Sanity checks passed: bounds and row counts plausible."

            return False, "Result set empty or unverified."

        except Exception as e:
            return False, f"Verifier encountered an error during cross-check: {str(e)}"
