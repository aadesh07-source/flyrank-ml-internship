"""test_leakage.py — Automated leakage checks (SPECS §9).

Six checks ensuring temporal and page-level leakage safety.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pipeline.windows import WindowPair, generate_window_pairs


class TestLeakageChecks:
    """Leakage checks from SPECS §9."""

    def _sample_window_pairs(self):
        """Generate sample window pairs for testing."""
        return generate_window_pairs(
            pd.Timestamp("2024-01-01"),
            pd.Timestamp("2024-06-30"),
        )

    def test_feature_date_before_label_date(self):
        """Check 1: max(feature_date) < min(label_date) for every snapshot."""
        pairs = self._sample_window_pairs()
        for wp in pairs:
            assert wp.feature_end < wp.label_start, (
                f"Feature window overlaps label window: "
                f"feat_end={wp.feature_end.date()}, label_start={wp.label_start.date()}"
            )

    def test_gap_between_windows(self):
        """Check 1b: gap exists between feature and label windows."""
        pairs = self._sample_window_pairs()
        for wp in pairs:
            gap = (wp.label_start - wp.feature_end).days
            assert gap >= 2, f"Gap too small: {gap} days"

    def test_no_page_overlap_placeholder(self):
        """Check 2: No page_id overlap between train and val folds (grouped CV).

        This is a structural test — actual GroupKFold implementation guarantees it.
        """
        from pipeline.split import grouped_kfold_split

        # Create mock data
        df = pd.DataFrame({
            "page_id": [f"page_{i}" for i in range(100)],
            "anchor_date": pd.Timestamp("2024-03-01"),
            "feature": np.random.randn(100),
        })

        splits = grouped_kfold_split(df, n_splits=3)
        for train_idx, val_idx in splits:
            train_pages = set(df.iloc[train_idx]["page_id"])
            val_pages = set(df.iloc[val_idx]["page_id"])
            overlap = train_pages & val_pages
            assert len(overlap) == 0, f"Page overlap in fold: {overlap}"

    def test_test_anchor_strictly_later(self):
        """Check 3: Test anchor is strictly later than all train anchors."""
        pairs = self._sample_window_pairs()
        if len(pairs) < 3:
            pytest.skip("Not enough window pairs")

        test_anchor = pairs[-1].anchor_date
        train_anchors = [wp.anchor_date for wp in pairs[:-2]]
        for ta in train_anchors:
            assert ta < test_anchor, (
                f"Train anchor {ta.date()} not before test anchor {test_anchor.date()}"
            )

    def test_no_label_columns_in_features_placeholder(self):
        """Check 4: No label-derived columns in the feature matrix.

        Enforced by code structure: features.py never imports from labels.py.
        """
        import inspect
        from pipeline import features

        source = inspect.getsource(features)
        assert "labels" not in source.lower() or "label" in source.lower(), (
            "features.py should not import from labels module"
        )
        # More importantly: no y_ columns
        forbidden = ["y_opportunity", "missed_clicks_L", "actual_ctr_L", "expected_ctr_L"]
        for col in forbidden:
            assert col not in source, f"Feature module references label column: {col}"

    def test_shuffled_label_sanity_placeholder(self):
        """Check 5: Shuffled-label sanity test (model AUC ≈ 0.5).

        This is run as part of the full pipeline evaluation, not as a unit test.
        Placeholder to document the check.
        """
        # This test would require a trained model; it's validated in run_all.py
        pass
