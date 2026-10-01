"""EDA endpoints — charts data for exploratory analysis sections."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.services.artifact_loader import load_artifact

router = APIRouter(tags=["eda"])


@router.get("/ctr-by-position")
async def ctr_by_position():
    """Observed vs expected CTR curve data."""
    return load_artifact("ctr_by_position")


@router.get("/distributions")
async def distributions(metric: str = Query("impressions")):
    """Histogram bins for impressions / CTR / position / engagement."""
    data = load_artifact("distributions")
    if metric in data:
        return data[metric]
    return data


@router.get("/trends")
async def trends():
    """Aggregated time series (daily/weekly)."""
    return load_artifact("trends")


@router.get("/segments")
async def segments(by: str = Query("content_type")):
    """Segment-level metrics."""
    data = load_artifact("segments")
    if by in data:
        return data[by]
    return data
