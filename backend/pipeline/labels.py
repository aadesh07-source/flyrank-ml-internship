"""labels.py — Label definition using the label window W_L (SPECS §6).

The label is computed from the label window only. The position curve and
thresholds must be fit on training data and passed in.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.core.config import load_params


def compute_labels(
    search_label: pd.DataFrame,
    position_curve_fn,
    alpha: float | None = None,
    min_missed_threshold: float | None = None,
) -> pd.DataFrame:
    """Compute opportunity labels from label-window search data.

    Args:
        search_label: search data sliced to the label window (W_L).
        position_curve_fn: function mapping avg_position → expected CTR.
                           Must be fit on training data only.
        alpha: Bayesian smoothing alpha (defaults to params.yaml value).
        min_missed_threshold: minimum missed clicks for binary label
                              (if None, will be set to top-quartile on train).

    Returns:
        DataFrame indexed by page_id with label columns:
        - impressions_L, actual_ctr_L, expected_ctr_L
        - missed_clicks_L, missed_clicks_log
        - y_opportunity (binary)
    """
    params = load_params()
    if alpha is None:
        alpha = params["ctr_smoothing_alpha"]
    delta = params["label"]["ctr_shortfall_delta"]
    min_impr_l = params["filters"]["min_impressions_label"]

    grouped = search_label.groupby("page_id")
    impr_l = grouped["impressions"].sum().rename("impressions_L")
    clicks_l = grouped["clicks"].sum()

    # Smoothed actual CTR in label window
    global_prior = search_label["clicks"].sum() / max(search_label["impressions"].sum(), 1)
    actual_ctr_l = ((clicks_l + alpha * global_prior) / (impr_l + alpha)).rename("actual_ctr_L")

    # Impression-weighted average position in label window
    def _weighted_pos(g):
        if g["impressions"].sum() == 0:
            return g["avg_position"].mean()
        return np.average(g["avg_position"], weights=g["impressions"])

    avg_pos_l = grouped.apply(_weighted_pos, include_groups=False).rename("avg_pos_L")

    # Expected CTR from the (training-fit) position curve
    expected_ctr_l = avg_pos_l.apply(position_curve_fn).rename("expected_ctr_L")

    # Missed clicks
    missed_clicks_l = (
        np.maximum(0, expected_ctr_l - actual_ctr_l) * impr_l
    ).rename("missed_clicks_L")
    missed_clicks_log = np.log1p(missed_clicks_l).rename("missed_clicks_log")

    labels = pd.concat(
        [impr_l, actual_ctr_l, expected_ctr_l, missed_clicks_l, missed_clicks_log, avg_pos_l],
        axis=1,
    )

    # Filter: must have minimum impressions in label window
    labels = labels[labels["impressions_L"] >= min_impr_l]

    # Binary label
    if min_missed_threshold is None:
        min_missed_threshold = missed_clicks_l.quantile(
            params["label"]["min_missed_clicks_quantile"]
        )

    labels["y_opportunity"] = (
        (labels["actual_ctr_L"] < labels["expected_ctr_L"] * (1 - delta))
        & (labels["missed_clicks_L"] >= min_missed_threshold)
    ).astype(int)

    return labels
