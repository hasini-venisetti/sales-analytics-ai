"""Pydantic schemas for API request and response validation."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AskOptions(BaseModel):
    include_returned: bool = Field(default=False, description="Whether to include returned orders in revenue calculations")


class AskRequest(BaseModel):
    question: str = Field(..., max_length=500, description="Natural language question about sales data")
    session_id: Optional[str] = Field(default=None, description="Client session identifier")
    options: Optional[AskOptions] = Field(default_factory=AskOptions)


class RowCounts(BaseModel):
    used: int
    excluded: int
    returned: int


class ChartSpec(BaseModel):
    type: str
    title: Optional[str] = None
    labels: List[str] = []
    datasets: List[Dict[str, Any]] = []


class TrustFactorSchema(BaseModel):
    name: str
    impact: str
    description: str
    status: str


class TrustScoreSchema(BaseModel):
    score: int
    grade: str
    headline: str
    factors: List[TrustFactorSchema]


class AskResponse(BaseModel):
    answer: str
    lane: str
    intent: str
    params: Dict[str, Any]
    confidence: float
    verified: bool
    verification_message: str
    sql: str
    columns: List[str]
    rows: List[Dict[str, Any]]
    formula: str
    assumptions: List[str]
    row_counts: RowCounts
    chart: ChartSpec
    trust_score: Optional[TrustScoreSchema] = None
    advisor: Optional[Dict[str, Any]] = None
    followups: List[str]
    warnings: List[str]
    mode: str
    latency_ms: float


class HealthResponse(BaseModel):
    status: str
    version: str
    mode: str
    csv_loaded: bool
    total_rows: int
    valid_rows: int
    quarantined_rows: int


class InsightCard(BaseModel):
    id: str
    title: str
    value: str
    subtitle: str
    badge: str
    badge_color: str


class ChallengeRequest(BaseModel):
    question: Optional[str] = "General Sales Metrics"


class ChallengeScenarioSchema(BaseModel):
    name: str
    description: str
    total_revenue: float
    total_revenue_formatted: str
    top_product: str
    top_product_rev_formatted: str
    top_region: str
    top_region_rev_formatted: str
    delta_formatted: str
    pct_formatted: str
    assumptions: str


class ChallengeResponse(BaseModel):
    question: str
    verdict: str
    is_stable: bool
    max_variance_pct: float
    scenarios: List[ChallengeScenarioSchema]
    takeaway: str


class AttackResultSchema(BaseModel):
    id: str
    name: str
    payload: str
    attack_type: str
    expected_defense: str
    blocked: bool
    defense_layer: str
    error_message: str
    latency_ms: float


class BreakItResponse(BaseModel):
    all_blocked: bool
    attacks_tested: int
    attacks_blocked: int
    vulnerability_rate_pct: float
    results: List[AttackResultSchema]
    summary: str
