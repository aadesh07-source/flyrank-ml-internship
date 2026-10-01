"""features.py — Feature engineering per (page_id, anchor_date) using only W_F data (SPECS §5).

All features are computed strictly within the feature window.
The position-curve for ctr_expected is fit externally (train-only) and passed in.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.core.config import load_params


def compute_page_features(
    search_df: pd.DataFrame,
    engagement_df: pd.DataFrame | None,
    content_meta: pd.DataFrame | None,
    anchor_date: pd.Timestamp,
) -> pd.DataFrame:
    """Compute all features for pages in the feature window.

    Args:
        search_df: search performance data already sliced to the feature window.
        engagement_df: engagement data sliced to feature window (may be None).
        content_meta: page-level content metadata (may be None).
        anchor_date: the anchor date for age calculations.

    Returns:
        DataFrame indexed by page_id with all feature columns.
    """
    params = load_params()
    alpha = params["ctr_smoothing_alpha"]

    features = _search_features(search_df, alpha)

    if engagement_df is not None and not engagement_df.empty:
        eng = _engagement_features(engagement_df)
        features = features.join(eng, how="left")
        features["eng_missing"] = features["sessions"].isna().astype(int)
    else:
        features["eng_missing"] = 1

    if content_meta is not None and not content_meta.empty:
        meta = _content_features(content_meta, anchor_date)
        features = features.join(meta, how="left")

    return features


def _search_features(df: pd.DataFrame, alpha: float) -> pd.DataFrame:
    """Visibility, position, CTR, trend, and volatility features."""
    grouped = df.groupby("page_id")

    # --- Visibility ---
    impr_sum = grouped["impressions"].sum().rename("impressions_sum")
    impr_mean = grouped["impressions"].mean().rename("impressions_mean_daily")
    log_impr = np.log1p(impr_sum).rename("log_impressions")

    # --- Position (impression-weighted) ---
    def _weighted_pos(g):
        if g["impressions"].sum() == 0:
            return g["avg_position"].mean()
        return np.average(g["avg_position"], weights=g["impressions"])

    pos_mean = grouped.apply(_weighted_pos, include_groups=False).rename("pos_mean")
    pos_median = grouped["avg_position"].median().rename("pos_median")
    pos_std = grouped["avg_position"].std().rename("pos_std")

    def _pos_bucket(p):
        if p <= 3:
            return "1-3"
        elif p <= 10:
            return "4-10"
        elif p <= 20:
            return "11-20"
        return "21+"

    pos_bucket = pos_mean.apply(_pos_bucket).rename("pos_bucket")

    # --- CTR ---
    clicks_sum = grouped["clicks"].sum()
    ctr_obs = (clicks_sum / impr_sum).rename("ctr_obs")

    # Bayesian shrinkage: (clicks + α·prior) / (impressions + α)
    global_prior = df["clicks"].sum() / max(df["impressions"].sum(), 1)
    ctr_smoothed = ((clicks_sum + alpha * global_prior) / (impr_sum + alpha)).rename("ctr_smoothed")

    # --- Trends (linear slope over window, normalized) ---
    impr_slope = grouped.apply(
        lambda g: _linear_slope(g, "impressions"), include_groups=False
    ).rename("impr_slope")
    click_slope = grouped.apply(
        lambda g: _linear_slope(g, "clicks"), include_groups=False
    ).rename("click_slope")
    ctr_daily = df.assign(ctr_daily=df["clicks"] / df["impressions"].clip(lower=1))
    ctr_slope = ctr_daily.groupby("page_id").apply(
        lambda g: _linear_slope(g, "ctr_daily"), include_groups=False
    ).rename("ctr_slope")
    pos_slope = grouped.apply(
        lambda g: _linear_slope(g, "avg_position"), include_groups=False
    ).rename("pos_slope")

    # --- Week-over-week change (last 7d vs previous 7d) ---
    impr_wow = grouped.apply(
        lambda g: _wow_change(g, "impressions"), include_groups=False
    ).rename("impr_wow_change")
    ctr_wow = ctr_daily.groupby("page_id").apply(
        lambda g: _wow_change(g, "ctr_daily"), include_groups=False
    ).rename("ctr_wow_change")

    # --- Volatility ---
    ctr_cv = ctr_daily.groupby("page_id")["ctr_daily"].apply(
        lambda s: s.std() / max(s.mean(), 1e-9)
    ).rename("ctr_cv")
    impr_cv = grouped["impressions"].apply(
        lambda s: s.std() / max(s.mean(), 1e-9)
    ).rename("impr_cv")

    # --- Days active ---
    days_active = grouped.size().rename("days_active")

    result = pd.concat(
        [
            impr_sum, impr_mean, log_impr,
            pos_mean, pos_median, pos_std, pos_bucket,
            ctr_obs, ctr_smoothed,
            impr_slope, click_slope, ctr_slope, pos_slope,
            impr_wow, ctr_wow,
            ctr_cv, impr_cv,
            days_active,
        ],
        axis=1,
    )
    return result


def _engagement_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engagement features from the engagement table."""
    grouped = df.groupby("page_id")
    sessions = grouped["sessions"].sum().rename("sessions")
    eng_rate = grouped["engagement_rate"].mean().rename("engagement_rate")
    eng_time = grouped["avg_engagement_time"].mean().rename("engagement_time_mean")
    return pd.concat([sessions, eng_rate, eng_time], axis=1)


def _content_features(meta: pd.DataFrame, anchor_date: pd.Timestamp) -> pd.DataFrame:
    """Content metadata features."""
    meta = meta.set_index("page_id")
    if "publish_date" in meta.columns:
        meta["content_age_days"] = (anchor_date - meta["publish_date"]).dt.days
    else:
        meta["content_age_days"] = np.nan
    return meta[["content_type", "content_age_days"]].copy()


def _linear_slope(group: pd.DataFrame, col: str) -> float:
    """Compute normalized linear slope of a column over time."""
    if len(group) < 2:
        return 0.0
    y = group[col].values.astype(float)
    x = np.arange(len(y), dtype=float)
    mean_y = np.mean(y)
    if mean_y == 0:
        return 0.0
    slope = np.polyfit(x, y, 1)[0]
    return slope / max(abs(mean_y), 1e-9)


def _wow_change(group: pd.DataFrame, col: str) -> float:
    """Week-over-week change: mean of last 7 days vs previous 7 days."""
    if len(group) < 14:
        return 0.0
    sorted_g = group.sort_values("date")
    recent = sorted_g[col].iloc[-7:].mean()
    previous = sorted_g[col].iloc[-14:-7].mean()
    if previous == 0:
        return 0.0
    return (recent - previous) / abs(previous)


def add_expected_ctr(
    features: pd.DataFrame,
    position_curve_fn,
) -> pd.DataFrame:
    """Add ctr_expected, ctr_gap, and ctr_ratio using a pre-fit position curve.

    The position_curve_fn must be fit on training data only to avoid leakage.
    """
    features = features.copy()
    features["ctr_expected"] = features["pos_mean"].apply(position_curve_fn)
    features["ctr_gap"] = features["ctr_expected"] - features["ctr_smoothed"]
    features["ctr_ratio"] = features["ctr_smoothed"] / features["ctr_expected"].clip(lower=1e-9)
    return features
