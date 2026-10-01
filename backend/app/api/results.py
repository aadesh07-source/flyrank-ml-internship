"""Results endpoints — model vs baseline metrics, curves, feature importance."""

from __future__ import annotations

from fastapi import APIRouter

from app.services.artifact_loader import load_artifact

router = APIRouter(tags=["results"])


@router.get("/metrics")
async def metrics():
    """Baseline vs ML metrics with bootstrap CIs."""
    return load_artifact("metrics")


@router.get("/pr-curve")
async def pr_curve():
    """Precision-Recall curve points for both baseline and ML model."""
    return load_artifact("pr_curve")


@router.get("/precision-at-k")
async def precision_at_k():
    """P@K and NDCG@K curves."""
    return load_artifact("precision_at_k")


@router.get("/calibration")
async def calibration():
    """Reliability / calibration data."""
    return load_artifact("calibration")


@router.get("/feature-importance")
async def feature_importance():
    """Feature importance values (permutation / model-native)."""
    return load_artifact("feature_importance")
