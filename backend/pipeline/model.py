"""model.py — ML model training, calibration, and explainability (SPECS §8).

Candidates: LogisticRegression (interpretable), HistGradientBoostingClassifier (main).
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.core.config import ARTIFACTS_DIR, load_params

# Features to use (numeric and categorical)
NUMERIC_FEATURES = [
    "impressions_sum", "impressions_mean_daily", "log_impressions",
    "pos_mean", "pos_median", "pos_std",
    "ctr_obs", "ctr_smoothed", "ctr_expected", "ctr_gap", "ctr_ratio",
    "impr_slope", "click_slope", "ctr_slope", "pos_slope",
    "impr_wow_change", "ctr_wow_change",
    "ctr_cv", "impr_cv",
    "days_active", "content_age_days",
    "sessions", "engagement_rate", "engagement_time_mean",
    "eng_missing",
]

CATEGORICAL_FEATURES = ["pos_bucket", "content_type"]


def build_pipeline(model_type: str = "hgb") -> Pipeline:
    """Build an sklearn Pipeline with preprocessing + model.

    Args:
        model_type: 'hgb' for HistGradientBoosting, 'lr' for LogisticRegression.
    """
    params = load_params()
    seed = params["seed"]

    numeric_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
        ("scaler", StandardScaler()),
    ])

    categorical_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="unknown")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, NUMERIC_FEATURES),
            ("cat", categorical_transformer, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )

    if model_type == "lr":
        clf = LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=seed,
        )
    else:
        clf = HistGradientBoostingClassifier(
            class_weight="balanced",
            max_iter=300,
            learning_rate=0.05,
            max_depth=6,
            random_state=seed,
        )

    return Pipeline([("preprocessor", preprocessor), ("classifier", clf)])


def train_model(
    pipeline: Pipeline,
    X_train: pd.DataFrame,
    y_train: pd.Series,
) -> Pipeline:
    """Fit the pipeline on training data."""
    # Filter to available columns
    available_num = [c for c in NUMERIC_FEATURES if c in X_train.columns]
    available_cat = [c for c in CATEGORICAL_FEATURES if c in X_train.columns]

    # Update the preprocessor column lists
    pipeline.named_steps["preprocessor"].transformers = [
        ("num", pipeline.named_steps["preprocessor"].transformers[0][1], available_num),
        ("cat", pipeline.named_steps["preprocessor"].transformers[1][1], available_cat),
    ]

    pipeline.fit(X_train, y_train)
    return pipeline


def calibrate_model(
    pipeline: Pipeline,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    method: str = "isotonic",
) -> CalibratedClassifierCV:
    """Calibrate the model on validation data."""
    calibrated = CalibratedClassifierCV(pipeline, method=method, cv="prefit")
    calibrated.fit(X_val, y_val)
    return calibrated


def get_feature_importance(
    pipeline: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    n_repeats: int = 10,
) -> pd.DataFrame:
    """Compute permutation importance on the test set."""
    params = load_params()
    result = permutation_importance(
        pipeline, X_test, y_test,
        n_repeats=n_repeats,
        random_state=params["seed"],
        scoring="average_precision",
    )
    importance_df = pd.DataFrame({
        "feature": X_test.columns,
        "importance_mean": result.importances_mean,
        "importance_std": result.importances_std,
    }).sort_values("importance_mean", ascending=False)
    return importance_df


def save_model(model, name: str = "model") -> Path:
    """Save model to artifacts directory."""
    path = ARTIFACTS_DIR / "raw" / f"{name}.joblib"
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    return path


def load_model(name: str = "model"):
    """Load model from artifacts directory."""
    path = ARTIFACTS_DIR / "raw" / f"{name}.joblib"
    return joblib.load(path)
