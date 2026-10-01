"""score.py — Opportunity Score (0-100), reason codes, and actions (SPECS §10).

Converts model output into an actionable review queue.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.core.config import load_params

# Tier definitions
TIERS = {
    (80, 100): "Review now",
    (60, 79): "Review soon",
    (40, 59): "Monitor",
    (0, 39): "Low priority",
}

# Action playbook
ACTION_MAP = {
    "HIGH_IMPR_LOW_CTR": "Review title / meta description",
    "GOOD_POS_LOW_CTR": "CTR optimization review (snippet, intent match)",
    "HIGH_VIS_LOW_ENG": "Content engagement review",
    "DECLINING_CTR": "Review content / SERP changes",
    "MODERATE": "Monitor",
    "LOW": "No action",
}


def compute_opportunity_score(
    p_opportunity: pd.Series,
    ctr_gap: pd.Series,
    impressions: pd.Series,
) -> pd.Series:
    """Compute the 0-100 Opportunity Score.

    Formula (SPECS §10):
        raw = 0.7 × p_opportunity + 0.3 × norm(expected_missed_clicks)
        score = 100 × percentile_rank(raw)

    Where expected_missed_clicks = p_opportunity × (ctr_gap × impressions).
    """
    params = load_params()
    w_model = params["score"]["model_weight"]
    w_mag = params["score"]["magnitude_weight"]

    expected_missed = p_opportunity * (ctr_gap.clip(lower=0) * impressions)
    # Normalize to [0, 1]
    norm_missed = (expected_missed - expected_missed.min()) / max(
        expected_missed.max() - expected_missed.min(), 1e-9
    )

    raw = w_model * p_opportunity + w_mag * norm_missed
    # Percentile rank within the scoring snapshot
    score = raw.rank(pct=True) * 100
    return score.round().astype(int).clip(0, 100)


def assign_tier(score: int) -> str:
    """Map a score to its priority tier."""
    for (lo, hi), tier in TIERS.items():
        if lo <= score <= hi:
            return tier
    return "Low priority"


def assign_reason_and_action(
    features: pd.DataFrame,
    baseline_codes: list[str],
) -> tuple[list[str], str]:
    """Assign reason codes and a recommended action.

    Combines baseline rule codes with model feature contributions.

    Returns:
        (reason_codes, recommended_action)
    """
    codes = [c for c in baseline_codes if c not in ("LOW",)]

    if not codes:
        codes = ["MODERATE"] if features.get("opportunity_score", 0) >= 40 else ["LOW"]

    primary = codes[0]
    action = ACTION_MAP.get(primary, "Monitor")
    return codes, action


def build_ranked_table(
    features: pd.DataFrame,
    scores: pd.Series,
    baseline_results: pd.DataFrame,
    top_n: int | None = None,
) -> list[dict]:
    """Build the final ranked recommendations table.

    Args:
        features: page features DataFrame.
        scores: opportunity scores (0-100) indexed by page_id.
        baseline_results: baseline output with reason_codes.
        top_n: max pages to include (defaults to params.yaml publish.top_n_recommendations).

    Returns:
        List of recommendation dicts, ranked by score descending.
    """
    params = load_params()
    if top_n is None:
        top_n = params["publish"]["top_n_recommendations"]

    records = []
    for page_id in scores.index:
        score_val = int(scores.loc[page_id])
        tier = assign_tier(score_val)

        bl_codes = baseline_results.loc[page_id, "reason_codes"] if page_id in baseline_results.index else ["LOW"]
        reason_codes, action = assign_reason_and_action(
            features.loc[page_id] if page_id in features.index else pd.Series(),
            bl_codes,
        )

        records.append({
            "page_id": str(page_id),
            "opportunity_score": score_val,
            "content_type": str(features.loc[page_id].get("content_type", "unknown")) if page_id in features.index else "unknown",
            "impressions": int(features.loc[page_id].get("impressions_sum", 0)) if page_id in features.index else 0,
            "ctr": round(float(features.loc[page_id].get("ctr_smoothed", 0)), 4) if page_id in features.index else 0,
            "expected_ctr": round(float(features.loc[page_id].get("ctr_expected", 0)), 4) if page_id in features.index else 0,
            "avg_position": round(float(features.loc[page_id].get("pos_mean", 0)), 1) if page_id in features.index else 0,
            "reason_codes": reason_codes,
            "recommended_action": action,
            "tier": tier,
        })

    # Sort by score descending, assign rank
    records.sort(key=lambda x: x["opportunity_score"], reverse=True)
    for i, rec in enumerate(records[:top_n], 1):
        rec["rank"] = i

    return records[:top_n]
