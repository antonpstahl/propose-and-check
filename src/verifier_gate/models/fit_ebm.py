"""Fit an ExplainableBoostingClassifier with one fixed smoothing setting."""

import numpy as np
import pandas as pd
from interpret.glassbox import ExplainableBoostingClassifier

# interpret 0.7.8 defaults, written out so a library upgrade cannot change the paper's setting silently.
# Smoothing and the number of pairs are still to be fixed after the smoothing runs.
EBM_PARAMS = {
    "max_bins": 1024,
    "max_interaction_bins": 64,
    "interactions": "3x",
    "validation_size": 0.15,
    "outer_bags": 14,
    "learning_rate": 0.015,
    "smoothing_rounds": 75,
    "interaction_smoothing_rounds": 75,
    "greedy_ratio": 10.0,
    "cyclic_progress": False,
    "min_samples_leaf": 4,
    "max_rounds": 50_000,
    "early_stopping_rounds": 100,
}


def fit_ebm(X: pd.DataFrame, y: np.ndarray, seed: int, **overrides) -> ExplainableBoostingClassifier:
    params = {**EBM_PARAMS, **overrides, "random_state": seed}
    return ExplainableBoostingClassifier(**params).fit(X, y)
