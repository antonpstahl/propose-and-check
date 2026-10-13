"""Fit XGB2: XGBoost with max_depth=2, early stopping on a validation split."""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

VALIDATION_SIZE = 0.15  # same as the EBM's validation_size

XGB2_PARAMS = {
    "max_depth": 2,
    "learning_rate": 0.05,
    "n_estimators": 3_000,
    "early_stopping_rounds": 100,
    "tree_method": "hist",
    "max_bin": 256,
    "eval_metric": "logloss",
}


def fit_xgb2(
    X: pd.DataFrame, y: np.ndarray, seed: int, sample_weight: np.ndarray | None = None, **overrides
) -> XGBClassifier:
    """sample_weight: Poisson counts of a bootstrap refit. They weight the validation loss too, so early
    stopping sees the bootstrap sample (resampled rows would leak duplicates into the validation split, D17)."""
    w = np.ones(len(y)) if sample_weight is None else np.asarray(sample_weight, dtype=np.float64)
    X_fit, X_val, y_fit, y_val, w_fit, w_val = train_test_split(
        X, y, w, test_size=VALIDATION_SIZE, stratify=y, random_state=seed
    )
    model = XGBClassifier(**{**XGB2_PARAMS, **overrides, "random_state": seed})
    if sample_weight is None:
        model.fit(X_fit, y_fit, eval_set=[(X_val, y_val)], verbose=False)
    else:
        model.fit(X_fit, y_fit, sample_weight=w_fit, eval_set=[(X_val, y_val)], sample_weight_eval_set=[w_val], verbose=False)
    return model
