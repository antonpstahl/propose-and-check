"""Bootstrap refits behind the bands (§5.1, §14.2 D17): Poisson counts as weights, one code path for both models.

Refit b draws a Poisson(1) count for every training row, from a generator seeded by the dataset's seed and b,
so the EBM and the XGB2 refit b see the same bootstrap sample (paired comparisons). The model is fitted on the
rows drawn at least once, with the counts as sample weights (interpret rejects zero weights, and resampled
duplicates would leak into the internal validation split and break early stopping), then purified and
centred on the bootstrap sample. Each refit is read through M's frame (facts/build.py): a term M has and the
refit lacks counts as zero, so a pair found in some refits only gets a band that reaches down to zero.
"""

import time
from collections.abc import Callable

import numpy as np
import pandas as pd

from verifier_gate.facts.build import Frame
from verifier_gate.facts.ebm import purify_ebm
from verifier_gate.facts.schema import Draws
from verifier_gate.facts.steps import StepModel
from verifier_gate.facts.xgb2 import purify_xgb2
from verifier_gate.models.fit_ebm import EBM_PARAMS, fit_ebm
from verifier_gate.models.fit_xgb2 import XGB2_PARAMS, fit_xgb2

REFITS = 100
STREAM = 17  # separates the bootstrap generator from the DGP's, which is seeded by the dataset seed alone
MODELS: dict[str, tuple[Callable, Callable, dict]] = {
    "EBM": (fit_ebm, purify_ebm, EBM_PARAMS),
    "XGB2": (fit_xgb2, purify_xgb2, XGB2_PARAMS),
}


def poisson_weights(n: int, seed: int, refit: int) -> np.ndarray:
    return np.random.default_rng([STREAM, seed, refit]).poisson(1.0, n).astype(np.float64)


def fit_steps(kind: str, X: pd.DataFrame, y: np.ndarray, seed: int, w: np.ndarray | None = None) -> StepModel:
    """Fit the model, purify and centre it on the (bootstrap) sample. w=None: M itself."""
    fitter, provider, _ = MODELS[kind]
    if w is None:
        return provider(fitter(X, y, seed=seed), X)
    drawn = w > 0
    model = fitter(X[drawn].reset_index(drop=True), y[drawn], seed=seed, sample_weight=w[drawn])
    return provider(model, X, w)


def refit_draws(
    kind: str, X: pd.DataFrame, y: np.ndarray, seed: int, frame: Frame, refits: int = REFITS, log: Callable | None = None
) -> Draws:
    """`refits` Poisson refits of the model, each read through M's frame."""
    reads = []
    start = time.perf_counter()
    for b in range(refits):
        w = poisson_weights(len(y), seed, b)
        reads.append(frame.read(fit_steps(kind, X, y, seed=b, w=w), X, w))
        if log and (b + 1) % 10 == 0:
            elapsed = time.perf_counter() - start
            log(f"  {kind} refit {b + 1}/{refits}, {elapsed / (b + 1):.1f}s per refit")
    return Draws.stack(reads)
