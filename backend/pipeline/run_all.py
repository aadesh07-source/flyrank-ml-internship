"""run_all.py — Orchestrate the full pipeline end-to-end (SPECS §18).

Usage:
    python -m pipeline.run_all
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from app.core.config import ARTIFACTS_DIR, PUBLIC_ARTIFACTS_DIR, RAW_ARTIFACTS_DIR, load_params
from pipeline.anonymize import anonymize_page_id
from pipeline.baseline import compute_baseline
from pipeline.clean import apply_page_filters, clean_engagement, clean_search
from pipeline.evaluate import (
    bootstrap_ci,
    compute_all_metrics,
    compute_calibration_curve,
    compute_pr_curve,
)
from pipeline.features import add_expected_ctr, compute_page_features
from pipeline.labels import compute_labels
from pipeline.load import load_content_metadata, load_engagement, load_search_performance
from pipeline.model import (
    build_pipeline,
    calibrate_model,
    get_feature_importance,
    save_model,
    train_model,
)
from pipeline.score import build_ranked_table, compute_opportunity_score
from pipeline.split import grouped_kfold_split, time_aware_split
from pipeline.windows import generate_window_pairs, slice_to_window

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger(__name__)


def _ensure_dirs():
    """Create artifact directories if they don't exist."""
    for d in [ARTIFACTS_DIR, PUBLIC_ARTIFACTS_DIR, RAW_ARTIFACTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def _save_json(data: dict | list, name: str, public: bool = True):
    """Save a dict/list as JSON to the artifacts directory."""
    target = PUBLIC_ARTIFACTS_DIR if public else RAW_ARTIFACTS_DIR
    path = target / f"{name}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    log.info(f"Saved {'public' if public else 'raw'} artifact: {path.name}")


def _fit_position_curve(train_features: pd.DataFrame):
    """Fit a simple position → expected CTR curve from training data.

    Returns a callable: position → expected_ctr.
    """
    from scipy.optimize import curve_fit

    def _ctr_model(pos, a, b, c):
        return a * np.exp(-b * pos) + c

    pos = train_features["pos_mean"].values
    ctr = train_features["ctr_smoothed"].values

    mask = np.isfinite(pos) & np.isfinite(ctr) & (pos > 0)
    pos, ctr = pos[mask], ctr[mask]

    try:
        popt, _ = curve_fit(_ctr_model, pos, ctr, p0=[0.3, 0.2, 0.01], maxfev=5000)
        log.info(f"Position curve fit: a={popt[0]:.4f}, b={popt[1]:.4f}, c={popt[2]:.4f}")
        return lambda p: float(_ctr_model(p, *popt))
    except Exception as e:
        log.warning(f"Position curve fit failed ({e}); falling back to median-based lookup")
        # Fallback: binned median CTR by position bucket
        bins = pd.cut(pos, bins=[0, 3, 10, 20, 50, 100], labels=False)
        medians = pd.Series(ctr).groupby(bins).median().to_dict()
        def _fallback(p):
            if p <= 3:
                return medians.get(0, 0.05)
            elif p <= 10:
                return medians.get(1, 0.03)
            elif p <= 20:
                return medians.get(2, 0.015)
            elif p <= 50:
                return medians.get(3, 0.005)
            return medians.get(4, 0.002)
        return _fallback


def main():
    """Run the full pipeline."""
    _ensure_dirs()
    params = load_params()
    seed = params["seed"]
    np.random.seed(seed)

    # ── Step 1: Load ──────────────────────────────────────────────────────────
    log.info("Step 1: Loading data from Hugging Face...")
    search_df = load_search_performance()
    log.info(f"  Search performance: {len(search_df):,} rows")

    try:
        engagement_df = load_engagement()
        log.info(f"  Engagement: {len(engagement_df):,} rows")
    except Exception as e:
        log.warning(f"  Engagement data not available: {e}")
        engagement_df = None

    try:
        content_meta = load_content_metadata()
        log.info(f"  Content metadata: {len(content_meta):,} rows")
    except Exception as e:
        log.warning(f"  Content metadata not available: {e}")
        content_meta = None

    # ── Step 2: Clean ─────────────────────────────────────────────────────────
    log.info("Step 2: Cleaning data...")
    search_df = clean_search(search_df)
    if engagement_df is not None:
        engagement_df = clean_engagement(engagement_df)
    log.info(f"  After cleaning: {len(search_df):,} search rows")

    # ── Step 3: Generate windows ──────────────────────────────────────────────
    log.info("Step 3: Generating time windows...")
    min_date = search_df["date"].min()
    max_date = search_df["date"].max()
    window_pairs = generate_window_pairs(min_date, max_date)
    log.info(f"  Generated {len(window_pairs)} window pairs from {min_date.date()} to {max_date.date()}")

    if len(window_pairs) < 3:
        log.error("Not enough window pairs for train/val/test. Check date range and window config.")
        return

    # ── Step 4: Build feature + label snapshots ──────────────────────────────
    log.info("Step 4: Building feature and label snapshots...")
    all_snapshots = []
    for wp in window_pairs:
        feat_data = slice_to_window(search_df, wp.feature_start, wp.feature_end)
        eng_data = slice_to_window(engagement_df, wp.feature_start, wp.feature_end) if engagement_df is not None else None

        features = compute_page_features(feat_data, eng_data, content_meta, wp.anchor_date)

        # Page-level filtering
        features = apply_page_filters(features.reset_index().rename(columns={"index": "page_id"}).set_index("page_id"))

        features["anchor_date"] = wp.anchor_date
        all_snapshots.append(features)

    dataset = pd.concat(all_snapshots)
    dataset = dataset.reset_index()
    log.info(f"  Total snapshots: {len(dataset):,} (page × anchor)")

    # ── Step 5: Train/val/test split ──────────────────────────────────────────
    log.info("Step 5: Time-aware split...")
    train_df, val_df, test_df = time_aware_split(dataset, window_pairs)
    log.info(f"  Train: {len(train_df):,} | Val: {len(val_df):,} | Test: {len(test_df):,}")

    # ── Step 6: Fit position curve on training data ──────────────────────────
    log.info("Step 6: Fitting position curve (train only)...")
    pos_curve = _fit_position_curve(train_df)

    # Add expected CTR to all splits
    for split_name, split_df in [("train", train_df), ("val", val_df), ("test", test_df)]:
        split_df_updated = add_expected_ctr(split_df.set_index("page_id"), pos_curve)
        if split_name == "train":
            train_df = split_df_updated.reset_index()
        elif split_name == "val":
            val_df = split_df_updated.reset_index()
        else:
            test_df = split_df_updated.reset_index()

    # ── Step 7: Compute labels ────────────────────────────────────────────────
    log.info("Step 7: Computing labels...")
    # For each split, compute labels from the corresponding label window
    # (We use the latest anchor's label window for the test set)
    test_wp = window_pairs[-1]
    label_search = slice_to_window(search_df, test_wp.label_start, test_wp.label_end)
    test_labels = compute_labels(label_search, pos_curve)
    log.info(f"  Label distribution: {test_labels['y_opportunity'].value_counts().to_dict()}")

    # ── Step 8: Baseline ──────────────────────────────────────────────────────
    log.info("Step 8: Computing baseline...")
    test_features = test_df.set_index("page_id")
    train_features = train_df.set_index("page_id")
    baseline_results = compute_baseline(test_features, train_features)

    # ── Step 9: ML Model ──────────────────────────────────────────────────────
    log.info("Step 9: Training ML model...")
    # Prepare labels for training
    train_wp_labels = {}
    for wp in window_pairs[:-2]:  # train window pairs
        lbl_data = slice_to_window(search_df, wp.label_start, wp.label_end)
        lbl = compute_labels(lbl_data, pos_curve)
        train_wp_labels[wp.anchor_date] = lbl

    # Merge train features with labels
    train_with_labels = train_df.set_index("page_id").copy()
    y_parts = []
    for anchor, lbls in train_wp_labels.items():
        anchor_mask = train_with_labels["anchor_date"] == anchor
        anchor_pages = train_with_labels[anchor_mask]
        common = anchor_pages.index.intersection(lbls.index)
        y_parts.append(lbls.loc[common, "y_opportunity"])

    if y_parts:
        y_train = pd.concat(y_parts)
        X_train = train_with_labels.loc[y_train.index]

        pipeline = build_pipeline("hgb")
        pipeline = train_model(pipeline, X_train, y_train)
        save_model(pipeline, "opportunity_model")
        log.info("  Model trained and saved.")

        # Calibrate on validation
        val_wp = window_pairs[-2]
        val_label_data = slice_to_window(search_df, val_wp.label_start, val_wp.label_end)
        val_labels = compute_labels(val_label_data, pos_curve)
        val_features = val_df.set_index("page_id")
        val_common = val_features.index.intersection(val_labels.index)
        if len(val_common) > 10:
            calibrated = calibrate_model(pipeline, val_features.loc[val_common], val_labels.loc[val_common, "y_opportunity"])
            save_model(calibrated, "opportunity_model_calibrated")
            log.info("  Model calibrated.")
            model_to_eval = calibrated
        else:
            model_to_eval = pipeline

        # ── Step 10: Evaluate ─────────────────────────────────────────────────
        log.info("Step 10: Evaluating...")
        test_common = test_features.index.intersection(test_labels.index)
        X_test = test_features.loc[test_common]
        y_test = test_labels.loc[test_common, "y_opportunity"].values
        missed_test = test_labels.loc[test_common, "missed_clicks_L"].values

        # ML predictions
        y_prob_ml = model_to_eval.predict_proba(X_test)[:, 1]
        ml_metrics = compute_all_metrics(y_test, y_prob_ml, missed_test)

        # Baseline predictions (normalized score as probability proxy)
        bl_scores = baseline_results.loc[test_common, "baseline_rank_score"].values
        bl_norm = (bl_scores - bl_scores.min()) / max(bl_scores.max() - bl_scores.min(), 1e-9)
        baseline_metrics = compute_all_metrics(y_test, bl_norm, missed_test)

        log.info(f"  ML PR-AUC: {ml_metrics['pr_auc']:.4f} | Baseline PR-AUC: {baseline_metrics['pr_auc']:.4f}")

        # PR curves
        ml_pr = compute_pr_curve(y_test, y_prob_ml)
        bl_pr = compute_pr_curve(y_test, bl_norm)

        # Calibration
        ml_cal = compute_calibration_curve(y_test, y_prob_ml)

        # Feature importance
        importance = get_feature_importance(pipeline, X_test, y_test)

        # ── Step 11: Score ────────────────────────────────────────────────────
        log.info("Step 11: Computing opportunity scores...")
        opp_scores = compute_opportunity_score(
            pd.Series(y_prob_ml, index=test_common),
            test_features.loc[test_common, "ctr_gap"],
            test_features.loc[test_common, "impressions_sum"],
        )

        # ── Step 12: Build recommendations ────────────────────────────────────
        log.info("Step 12: Building ranked recommendations...")
        recs = build_ranked_table(test_features, opp_scores, baseline_results)

        # Anonymize page IDs in recommendations
        for rec in recs:
            rec["page_id"] = anonymize_page_id(rec["page_id"])

        # ── Step 13: Save public artifacts ────────────────────────────────────
        log.info("Step 13: Saving public artifacts...")

        _save_json({
            "dataset_label": "FlyRank ML Internship Dataset",
            "feature_window": f"{window_pairs[-1].feature_start.date()} to {window_pairs[-1].feature_end.date()}",
            "label_window": f"{window_pairs[-1].label_start.date()} to {window_pairs[-1].label_end.date()}",
            "gap_days": params["windows"]["gap_days"],
            "pages_before_exclusion": len(search_df["page_id"].unique()),
            "pages_after_exclusion": len(test_common),
            "model_version": "0.1.0",
        }, "meta")

        _save_json({
            "pages_analyzed": len(test_common),
            "pct_flagged": round(float(y_test.mean()) * 100, 1),
            "overall_ctr": round(float(test_features.loc[test_common, "ctr_smoothed"].mean()), 4),
            "overall_expected_ctr": round(float(test_features.loc[test_common, "ctr_expected"].mean()), 4),
            "total_missed_clicks": round(float(missed_test.sum()), 0),
        }, "summary")

        _save_json({
            "baseline": baseline_metrics,
            "ml_model": ml_metrics,
        }, "metrics")

        _save_json({"ml": ml_pr, "baseline": bl_pr}, "pr_curve")

        _save_json(ml_cal, "calibration")

        _save_json(importance.to_dict("records"), "feature_importance")

        _save_json({"total": len(recs), "items": recs}, "recommendations")

        # CTR by position data
        pos_bins = pd.cut(test_features.loc[test_common, "pos_mean"], bins=[0, 3, 10, 20, 50, 100])
        ctr_by_pos = test_features.loc[test_common].groupby(pos_bins, observed=True).agg(
            observed_ctr=("ctr_smoothed", "mean"),
            expected_ctr=("ctr_expected", "mean"),
            page_count=("ctr_smoothed", "count"),
        ).reset_index()
        ctr_by_pos["position_range"] = ctr_by_pos["pos_mean"].astype(str)
        _save_json(ctr_by_pos[["position_range", "observed_ctr", "expected_ctr", "page_count"]].to_dict("records"), "ctr_by_position")

        # P@K curves
        pak_data = {"topk": params["topk"]}
        for k in params["topk"]:
            pak_data[f"ml_precision_at_{k}"] = ml_metrics.get(f"precision_at_{k}", 0)
            pak_data[f"baseline_precision_at_{k}"] = baseline_metrics.get(f"precision_at_{k}", 0)
            pak_data[f"ml_ndcg_at_{k}"] = ml_metrics.get(f"ndcg_at_{k}", 0)
        _save_json(pak_data, "precision_at_k")

        # Playbook
        _save_json({
            "tiers": [
                {"range": "80-100", "label": "Review now", "description": "High-confidence opportunity"},
                {"range": "60-79", "label": "Review soon", "description": "Moderate opportunity"},
                {"range": "40-59", "label": "Monitor", "description": "Worth watching"},
                {"range": "0-39", "label": "Low priority", "description": "Low opportunity signal"},
            ],
            "actions": [
                {"reason_code": k, "recommended_action": v}
                for k, v in {
                    "HIGH_IMPR_LOW_CTR": "Review title / meta description",
                    "GOOD_POS_LOW_CTR": "CTR optimization review (snippet, intent match)",
                    "HIGH_VIS_LOW_ENG": "Content engagement review",
                    "DECLINING_CTR": "Review content / SERP changes",
                }.items()
            ],
        }, "playbook")

        log.info("✅ Pipeline complete! All artifacts saved.")
    else:
        log.error("No training labels could be computed. Check data and window config.")


if __name__ == "__main__":
    main()
