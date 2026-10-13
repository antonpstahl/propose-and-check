"""Fit an ExplainableBoostingClassifier with one fixed smoothing setting."""

import numpy as np
import pandas as pd
from interpret.glassbox import ExplainableBoostingClassifier

# interpret 0.7.8 defaults, written out so a library upgrade cannot change the paper's setting silently,
# except pairs and smoothing, fixed by the smoothing runs (experiments/smoothing.py, plan §14): 5 pairs
# instead of 27; no smoothing rounds for main terms (they made the noise terms larger) and 1000 for pairs
# (they recover the sign flip and keep the noisy marginals of the pairs out of the purified main terms).
# Bins barely mattered.
EBM_PARAMS = {
    "max_bins": 1024,
    "max_interaction_bins": 64,
    "interactions": 5,
    "validation_size": 0.15,
    "outer_bags": 14,
    "learning_rate": 0.015,
    "smoothing_rounds": 0,
    "interaction_smoothing_rounds": 1000,
    "greedy_ratio": 10.0,
    "cyclic_progress": False,
    "min_samples_leaf": 4,
    "max_rounds": 50_000,
    "early_stopping_rounds": 100,
}


def fit_ebm(X: pd.DataFrame, y: np.ndarray, seed: int, **overrides) -> ExplainableBoostingClassifier:
    params = {**EBM_PARAMS, **overrides, "random_state": seed}
    return ExplainableBoostingClassifier(**params).fit(X, y)
