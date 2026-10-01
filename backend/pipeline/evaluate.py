"""evaluate.py — Evaluation metrics for baseline vs ML model (SPECS §9).

Both systems are scored on the identical test set.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    ndcg_score,
    precision_recall_curve,
    roc_auc_score,
)

from app.core.config import load_params


def compute_all_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    missed_clicks: np.ndarray | None = None,
    topk_values: list[int] | None = None,
) -> dict:
    """Compute all evaluation metrics.

    Args:
        y_true: binary ground truth labels.
        y_prob: predicted probabilities / scores.
        missed_clicks: regression target for NDCG gain.
        topk_values: K values for P@K, NDCG@K.

    Returns:
        Dictionary of metric names → values.
    """
    params = load_params()
    if topk_values is None:
        topk_values = params["topk"]

    metrics = {}

    # Overall discrimination
    metrics["pr_auc"] = float(average_precision_score(y_true, y_prob))
    metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))

    # Calibration
    metrics["brier_score"] = float(brier_score_loss(y_true, y_prob))

    # Precision@K and Recall@K
    ranked_indices = np.argsort(-y_prob)
    for k in topk_values:
        if k > len(y_true):
            k = len(y_true)
        top_k_true = y_true[ranked_indices[:k]]
        metrics[f"precision_at_{k}"] = float(top_k_true.mean())
        total_pos = y_true.sum()
        metrics[f"recall_at_{k}"] = float(top_k_true.sum() / max(total_pos, 1))

    # Top-10% metrics
    top_10pct_k = max(1, len(y_true) // 10)
    top_10pct_true = y_true[ranked_indices[:top_10pct_k]]
    metrics["lift_top_10pct"] = float(
        top_10pct_true.mean() / max(y_true.mean(), 1e-9)
    )

    # NDCG@K using missed_clicks as gain
    if missed_clicks is not None:
        for k in topk_values:
            if k > len(y_true):
                k = len(y_true)
            metrics[f"ndcg_at_{k}"] = float(
                ndcg_score(
                    missed_clicks.reshape(1, -1),
                    y_prob.reshape(1, -1),
                    k=k,
                )
            )

    # Expected missed clicks captured @ K
    if missed_clicks is not None:
        total_missed = missed_clicks.sum()
        for k in topk_values:
            if k > len(y_true):
                k = len(y_true)
            captured = missed_clicks[ranked_indices[:k]].sum()
            metrics[f"missed_clicks_captured_at_{k}"] = float(
                captured / max(total_missed, 1e-9)
            )

    return metrics


def compute_pr_curve(y_true: np.ndarray, y_prob: np.ndarray) -> dict:
    """Compute precision-recall curve points."""
    precision, recall, thresholds = precision_recall_curve(y_true, y_prob)
    return {
        "precision": precision.tolist(),
        "recall": recall.tolist(),
        "thresholds": thresholds.tolist(),
    }


def compute_calibration_curve(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10,
) -> dict:
    """Compute reliability / calibration curve."""
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins)
    return {
        "fraction_positives": prob_true.tolist(),
        "mean_predicted": prob_pred.tolist(),
    }


def bootstrap_ci(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    metric_fn,
    n_bootstrap: int = 1000,
    ci: float = 0.95,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Bootstrap confidence interval for a metric.

    Returns:
        (point_estimate, lower_bound, upper_bound)
    """
    rng = np.random.RandomState(seed)
    n = len(y_true)
    point = metric_fn(y_true, y_prob)
    scores = []
    for _ in range(n_bootstrap):
        idx = rng.randint(0, n, size=n)
        try:
            scores.append(metric_fn(y_true[idx], y_prob[idx]))
        except Exception:
            continue

    alpha = (1 - ci) / 2
    lower = float(np.percentile(scores, 100 * alpha))
    upper = float(np.percentile(scores, 100 * (1 - alpha)))
    return float(point), lower, upper
