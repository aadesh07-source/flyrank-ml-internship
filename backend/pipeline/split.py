"""split.py — Time-aware, grouped train/val/test splitting (SPECS §4, §9).

- Train on earlier anchors, validate on a middle anchor, test on the latest anchor(s).
- Within train/validation, use GroupKFold by page_id.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

from app.core.config import load_params
from pipeline.windows import WindowPair


def time_aware_split(
    dataset: pd.DataFrame,
    window_pairs: list[WindowPair],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split dataset by anchor time: earlier → train, latest → test.

    Args:
        dataset: full dataset with an 'anchor_date' column and 'page_id'.
        window_pairs: list of WindowPair objects (chronological order).

    Returns:
        (train_df, val_df, test_df)
    """
    params = load_params()
    n_test = params["split"]["test_anchors"]

    anchors = sorted(dataset["anchor_date"].unique())
    if len(anchors) < 3:
        raise ValueError(f"Need at least 3 anchor dates for train/val/test, got {len(anchors)}")

    test_anchors = set(anchors[-n_test:])
    val_anchor = {anchors[-(n_test + 1)]}
    train_anchors = set(anchors[: -(n_test + 1)])

    train = dataset[dataset["anchor_date"].isin(train_anchors)].copy()
    val = dataset[dataset["anchor_date"].isin(val_anchor)].copy()
    test = dataset[dataset["anchor_date"].isin(test_anchors)].copy()

    return train, val, test


def grouped_kfold_split(
    train_df: pd.DataFrame,
    n_splits: int | None = None,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Generate GroupKFold splits by page_id within training data.

    Ensures no page appears on both sides of a fold.

    Returns:
        List of (train_indices, val_indices) tuples.
    """
    params = load_params()
    if n_splits is None:
        n_splits = params["split"]["cv_folds"]

    gkf = GroupKFold(n_splits=n_splits)
    groups = train_df["page_id"].values
    X_dummy = np.zeros(len(train_df))

    return list(gkf.split(X_dummy, groups=groups))
