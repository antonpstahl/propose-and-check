"""Fit the oracle: a logistic regression on the planted unit shapes (§14.2 D10, D12).

Only the coefficients are estimated, so the oracle is the best any model can do on the sample: what the data
support. It knows the shapes of every planted term, including both planted pairs at level "none" (their
coefficients are then estimated near zero), and it knows that the noise features have no effect.
"""

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from verifier_gate.data import dgp


@dataclass(frozen=True)
class Oracle(dgp.Truth):
    """Logistic regression on the planted unit shapes, centred on the sample like T."""

    coef: Mapping[str, float]

    def term(self, name: str, X: Mapping) -> np.ndarray:
        return self.coef[name] * dgp.unit_term(name, X) - self.offsets[name]


def fit_oracle(
    X: pd.DataFrame, y: np.ndarray, seed: int = 0, sample_weight: np.ndarray | None = None, interaction: str = ""
) -> Oracle:
    """seed is unused (the fit is deterministic) and only keeps the fitters' common signature.
    sample_weight: Poisson counts of a bootstrap refit. interaction is a label; the terms do not use it."""
    ref = dgp._reference().iloc[:1_000]
    names = [t for t in dgp.TERMS if np.ptp(dgp.unit_term(t, ref)) > 0]  # noise shapes are zero
    Z = np.column_stack([dgp.unit_term(t, X) for t in names])
    scale = Z.std(axis=0)
    fit = LogisticRegression(C=np.inf, max_iter=10_000).fit(Z / scale, y, sample_weight=sample_weight)
    coef = dict.fromkeys(dgp.TERMS, 0.0) | dict(zip(names, fit.coef_[0] / scale))
    uncentred = Oracle(interaction, 0.0, dict.fromkeys(dgp.TERMS, 0.0), coef)
    offsets = {t: float(uncentred.term(t, X).mean()) for t in dgp.TERMS}
    return Oracle(interaction, float(fit.intercept_[0]) + sum(offsets.values()), offsets, coef)
