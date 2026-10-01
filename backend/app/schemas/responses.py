"""Pydantic v2 response schemas for API endpoints (SPECS §12)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class MetaResponse(BaseModel):
    dataset_label: str = Field(..., description="HF dataset release label")
    feature_window: str = Field(..., description="Feature window date range")
    label_window: str = Field(..., description="Label window date range")
    gap_days: int
    pages_before_exclusion: int
    pages_after_exclusion: int
    model_version: str


class SummaryResponse(BaseModel):
    pages_analyzed: int
    pct_flagged: float = Field(..., description="Percentage of pages flagged as opportunities")
    overall_ctr: float
    overall_expected_ctr: float
    total_missed_clicks: float


class RecommendationItem(BaseModel):
    rank: int
    page_id: str = Field(..., description="Anonymized page identifier (P-xxxxxxxx)")
    opportunity_score: int = Field(..., ge=0, le=100)
    content_type: str
    impressions: int
    ctr: float
    expected_ctr: float
    avg_position: float
    reason_codes: list[str]
    recommended_action: str
    tier: str


class RecommendationsResponse(BaseModel):
    total: int
    items: list[RecommendationItem]


class PlaybookEntry(BaseModel):
    reason_code: str
    trigger_summary: str
    recommended_action: str
    tier_range: str
