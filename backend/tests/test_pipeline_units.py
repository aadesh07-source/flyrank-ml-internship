"""test_pipeline_units.py — Unit tests for pipeline functions (SPECS §16)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pipeline.anonymize import anonymize_page_id


class TestCTRSmoothing:
    """Test Bayesian CTR smoothing logic."""

    def test_smoothing_shrinks_toward_prior(self):
        """With very few impressions, smoothed CTR should be close to prior."""
        from pipeline.features import _search_features

        df = pd.DataFrame({
            "page_id": ["A"] * 5 + ["B"] * 5,
            "date": list(pd.date_range("2024-01-01", periods=5)) * 2,
            "impressions": [2, 3, 1, 2, 1] + [200, 200, 200, 200, 200],
            "clicks": [2, 3, 1, 2, 1] + [10, 10, 10, 10, 10],  # page B has 5% CTR
            "avg_position": [5.0] * 10,
        })
        result = _search_features(df, alpha=50)
        # With alpha=50, page A's 100% CTR should be pulled significantly toward prior (~5.8%)
        assert float(result.loc["A", "ctr_smoothed"]) < 0.50

    def test_high_impressions_less_shrinkage(self):
        """With many impressions, smoothed CTR should be close to observed."""
        from pipeline.features import _search_features

        df = pd.DataFrame({
            "page_id": ["B"] * 30,
            "date": pd.date_range("2024-01-01", periods=30),
            "impressions": [1000] * 30,
            "clicks": [50] * 30,
            "avg_position": [3.0] * 30,
        })
        result = _search_features(df, alpha=50)
        assert abs(float(result.loc["B", "ctr_smoothed"]) - 0.05) < 0.01


class TestScoreComputation:
    """Test opportunity score computation."""

    def test_scores_in_range(self):
        """Scores must be between 0 and 100."""
        from pipeline.score import compute_opportunity_score

        p_opp = pd.Series([0.1, 0.5, 0.9, 0.3, 0.7])
        ctr_gap = pd.Series([0.01, 0.03, 0.05, 0.02, 0.04])
        impressions = pd.Series([100, 500, 1000, 200, 800])
        scores = compute_opportunity_score(p_opp, ctr_gap, impressions)
        assert (scores >= 0).all() and (scores <= 100).all()


class TestAnonymization:
    """Test page ID anonymization."""

    def test_format(self):
        """Anonymized ID should match expected format."""
        anon_id = anonymize_page_id("test-page-123")
        assert anon_id.startswith("P-")
        assert len(anon_id) >= 4

    def test_deterministic(self):
        """Same input should produce same output."""
        id1 = anonymize_page_id("page-abc")
        id2 = anonymize_page_id("page-abc")
        assert id1 == id2

    def test_different_inputs_different_outputs(self):
        """Different inputs should produce different outputs."""
        id1 = anonymize_page_id("page-1")
        id2 = anonymize_page_id("page-2")
        assert id1 != id2


class TestConfig:
    """Test configuration and schema loading."""

    def test_load_params(self):
        """Verify params.yaml loads correctly with all required sections."""
        from app.core.config import load_params

        params = load_params()
        assert "seed" in params
        assert "windows" in params
        assert "filters" in params
        assert "label" in params

    def test_load_schema(self):
        """Verify schema.yaml loads correctly with all confirmed HF tables."""
        from app.core.config import load_schema

        schema = load_schema()
        assert "tables" in schema
        tables = schema["tables"]
        assert "dim_content" in tables
        assert "fact_content_daily_performance" in tables
        assert "fact_content_query_90d" in tables
