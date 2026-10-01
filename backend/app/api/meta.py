"""Meta & summary endpoints — dataset metadata and headline stats."""

from __future__ import annotations

from fastapi import APIRouter

from app.services.artifact_loader import load_artifact

router = APIRouter(tags=["meta"])


@router.get("/meta")
async def meta():
    """Dataset release label, windows, exclusions, counts (public-safe), model version."""
    return load_artifact("meta")


@router.get("/summary")
async def summary():
    """Headline stats: pages analyzed, % flagged, overall CTR vs expected."""
    return load_artifact("summary")
