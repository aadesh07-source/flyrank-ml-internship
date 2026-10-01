"""baseline.py — Rule-based baseline scoring (SPECS §7).

Transparent thresholds computed from training-set quantiles.
Evaluated on the same test set as the ML model.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_baseline(
    features: pd.DataFrame,
    train_features: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Apply rule-based baseline and produce scores + reason codes.

    Args:
        features: feature DataFrame for the pages to score.
        train_features: training features for computing quantile thresholds.
                        If None, thresholds are computed from `features` itself
                        (only acceptable during EDA; for evaluation, always pass train).

    Returns:
        DataFrame with columns: baseline_score, reason_codes, rules_fired.
    """
    ref = train_features if train_features is not None else features

    # Compute thresholds from reference (training) data
    impr_p75 = ref["impressions_sum"].quantile(0.75)
    impr_p50 = ref["impressions_sum"].quantile(0.50)
    ctr_p25 = ref["ctr_smoothed"].quantile(0.25)
    eng_p25 = ref.get("engagement_rate", pd.Series(dtype=float)).quantile(0.25)

    # Slope threshold: mean - 1 std of ctr_slope (or a fixed negative value)
    ctr_slope_threshold = ref["ctr_slope"].mean() - ref["ctr_slope"].std()

    results = []
    for page_id, row in features.iterrows():
        codes = []
        score = 0

        # R1: High impressions, low CTR
        if row.get("impressions_sum", 0) >= impr_p75 and row.get("ctr_smoothed", 1) <= ctr_p25:
            codes.append("HIGH_IMPR_LOW_CTR")
            score += 3

        # R2: Good position (≤10), low CTR ratio
        if row.get("pos_mean", 99) <= 10 and row.get("ctr_ratio", 1) < 0.75:
            codes.append("GOOD_POS_LOW_CTR")
            score += 3

        # R3: High visibility, low engagement
        if (
            row.get("impressions_sum", 0) >= impr_p50
            and not pd.isna(row.get("engagement_rate"))
            and row.get("engagement_rate", 1) <= eng_p25
        ):
            codes.append("HIGH_VIS_LOW_ENG")
            score += 2

        # R4: Declining CTR with stable impressions
        if row.get("ctr_slope", 0) < ctr_slope_threshold and abs(row.get("impr_slope", 0)) < 0.1:
            codes.append("DECLINING_CTR")
            score += 2

        if not codes:
            codes.append("LOW")

        results.append(
            {
                "page_id": page_id,
                "baseline_score": score,
                "reason_codes": codes,
                "rules_fired": len(codes) - (1 if codes == ["LOW"] else 0),
            }
        )

    result_df = pd.DataFrame(results).set_index("page_id")
    # Tie-break by impressions
    result_df["baseline_rank_score"] = (
        result_df["baseline_score"] * 1e8 + features["impressions_sum"]
    )
    return result_df
