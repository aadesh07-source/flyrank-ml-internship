"""Recommendations endpoints — ranked pages with scores, reason codes, actions."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.services.artifact_loader import load_artifact

router = APIRouter(tags=["recommendations"])


@router.get("/recommendations")
async def recommendations(
    limit: int = Query(25, ge=1, le=200),
    action: str | None = Query(None),
    content_type: str | None = Query(None),
    min_score: int = Query(0, ge=0, le=100),
):
    """Ranked, paginated, filterable pages with opportunity scores."""
    data = load_artifact("recommendations")
    items = data.get("items", [])

    # Server-side filtering
    if action:
        items = [i for i in items if action.upper() in [r.upper() for r in i.get("reason_codes", [])]]
    if content_type:
        items = [i for i in items if i.get("content_type", "").lower() == content_type.lower()]
    if min_score > 0:
        items = [i for i in items if i.get("opportunity_score", 0) >= min_score]

    return {"total": len(items), "items": items[:limit]}


@router.get("/recommendations/{anon_id}")
async def recommendation_detail(anon_id: str):
    """Single page detail (anonymized)."""
    data = load_artifact("recommendations")
    for item in data.get("items", []):
        if item.get("page_id") == anon_id:
            return item
    return {"error": "Not found"}


@router.get("/playbook")
async def playbook():
    """Action definitions and tier rules."""
    return load_artifact("playbook")
