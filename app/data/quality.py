"""Data quality checking and reporting."""
from typing import Any, Dict, List
from pydantic import BaseModel


class QuarantinedRecord(BaseModel):
    transaction_id: str
    reason: str
    details: Dict[str, Any]


class DataQualityReport(BaseModel):
    total_rows_loaded: int
    valid_rows_count: int
    quarantined_rows_count: int
    returned_rows_count: int
    returns_value: float
    date_range_start: str
    date_range_end: str
    quarantined_records: List[QuarantinedRecord]
    data_hygiene_score_pct: float
    notes: List[str]
