"""clean.py — Data cleaning and exclusion logic (SPECS §3.3).

Applies documented exclusions and returns clean DataFrames.
"""

from __future__ import annotations

import pandas as pd

from app.core.config import load_params


def clean_search(df: pd.DataFrame) -> pd.DataFrame:
    """Clean search performance data.

    Exclusions (documented in paper):
    - Null/invalid position (NaN or ≤ 0)
    - clicks > impressions (invalid)
    - Rows with zero impressions
    """
    params = load_params()
    df = df.copy()

    # Remove invalid rows
    df = df.dropna(subset=["page_id", "date", "impressions", "clicks", "avg_position"])
    df = df[df["impressions"] > 0]
    df = df[df["avg_position"] > 0]
    df = df[df["clicks"] <= df["impressions"]]
    df = df[df["clicks"] >= 0]

    return df.reset_index(drop=True)


def clean_engagement(df: pd.DataFrame) -> pd.DataFrame:
    """Clean engagement data — drop rows with null page_id or date."""
    df = df.copy()
    df = df.dropna(subset=["page_id", "date"])
    return df.reset_index(drop=True)


def apply_page_filters(
    page_stats: pd.DataFrame,
    impressions_col: str = "impressions_sum",
    days_col: str = "days_active",
) -> pd.DataFrame:
    """Filter pages by minimum impressions and minimum active days (SPECS §3.3).

    Args:
        page_stats: page-level aggregated stats with impressions_sum and days_active.
        impressions_col: column name for total impressions.
        days_col: column name for count of active days.

    Returns:
        Filtered DataFrame of pages meeting the thresholds.
    """
    params = load_params()
    min_impr = params["filters"]["min_impressions_feature"]
    min_days = params["filters"]["min_days_active"]

    mask = (page_stats[impressions_col] >= min_impr) & (page_stats[days_col] >= min_days)
    return page_stats[mask].reset_index(drop=True)
