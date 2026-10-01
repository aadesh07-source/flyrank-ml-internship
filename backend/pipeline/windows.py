"""windows.py — Time-window management for leakage-safe feature/label splits (SPECS §4).

Generates (feature_window, label_window) snapshot pairs by sliding the anchor date.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

import pandas as pd

from app.core.config import load_params


@dataclass
class WindowPair:
    """A (feature_window, label_window) snapshot anchored at a specific date."""

    anchor_date: pd.Timestamp
    feature_start: pd.Timestamp
    feature_end: pd.Timestamp
    label_start: pd.Timestamp
    label_end: pd.Timestamp

    def __repr__(self) -> str:
        return (
            f"WindowPair(anchor={self.anchor_date.date()}, "
            f"feat=[{self.feature_start.date()}..{self.feature_end.date()}], "
            f"label=[{self.label_start.date()}..{self.label_end.date()}])"
        )


def generate_window_pairs(
    min_date: pd.Timestamp,
    max_date: pd.Timestamp,
) -> list[WindowPair]:
    """Generate rolling (feature, label) window pairs.

    The anchor date is the last day of the feature window.
    Windows slide backwards from max_date using anchor_step_days.
    A gap separates feature and label windows to prevent boundary leakage.
    """
    params = load_params()
    w = params["windows"]
    feat_days = w["feature_days"]
    gap_days = w["gap_days"]
    label_days = w["label_days"]
    step_days = w["anchor_step_days"]

    total_span = feat_days + gap_days + label_days
    pairs: list[WindowPair] = []

    # Start from the latest possible label_end = max_date
    label_end = pd.Timestamp(max_date)

    while True:
        label_start = label_end - timedelta(days=label_days - 1)
        feature_end = label_start - timedelta(days=gap_days + 1)
        feature_start = feature_end - timedelta(days=feat_days - 1)

        if feature_start < min_date:
            break

        pairs.append(
            WindowPair(
                anchor_date=feature_end,
                feature_start=feature_start,
                feature_end=feature_end,
                label_start=label_start,
                label_end=label_end,
            )
        )
        label_end -= timedelta(days=step_days)

    # Return in chronological order (earliest anchor first)
    return list(reversed(pairs))


def slice_to_window(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """Filter a date-indexed DataFrame to rows within [start, end]."""
    mask = (df["date"] >= start) & (df["date"] <= end)
    return df[mask].copy()
