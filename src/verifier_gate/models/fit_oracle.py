"""Fit the oracle: a logistic regression on the planted unit shapes (§14.2 D10, D12).

Only the coefficients are estimated, so the oracle is the best any model can do on the sample: what the data
support. It knows the shapes of every planted term, including both planted pairs at level "none" (their
coefficients are then estimated near zero), and it knows that the noise features have no effect. Either tier
(data/tiers.py): the tier is read from the sample's columns.
"""

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from verifier_gate.data import dgp, tiers


@dataclass(frozen=True)
class Oracle(dgp.Truth):
    """Logistic regression on the planted unit shapes, centred on the sample like T."""

    coef: Mapping[str, float]
    tier: str = "synthetic"

    @property
    def features(self) -> tuple[str, ...]:
        return tiers.module(self.tier).FEATURES

    @property
    def term_names(self) -> tuple[str, ...]:
        return tiers.module(self.tier).TERMS

    def term_features(self, name: str) -> tuple[str, ...]:
        return tiers.module(self.tier).term_features(name)

    def term(self, name: str, X: Mapping) -> np.ndarray:
        return self.coef[name] * tiers.module(self.tier).unit_term(name, X) - self.offsets[name]


def fit_oracle(
    X: pd.DataFrame, y: np.ndarray, seed: int = 0, sample_weight: np.ndarray | None = None, interaction: str = ""
) -> Oracle:
    """seed is unused (the fit is deterministic) and only keeps the fitters' common signature.
    sample_weight: Poisson counts of a bootstrap refit. interaction is a label; the terms do not use it."""
    tier = tiers.module(X)
    ref = tiers.reference_sample(tier)
    names = [t for t in tier.TERMS if np.ptp(tier.unit_term(t, ref)) > 0]  # noise shapes are zero
    Z = np.column_stack([tier.unit_term(t, X) for t in names])
    scale = Z.std(axis=0)
    fit = LogisticRegression(C=np.inf, max_iter=10_000).fit(Z / scale, y, sample_weight=sample_weight)
    coef = dict.fromkeys(tier.TERMS, 0.0) | dict(zip(names, fit.coef_[0] / scale))
    label = tiers.name(tier.FEATURES)
    uncentred = Oracle(interaction, 0.0, dict.fromkeys(tier.TERMS, 0.0), coef, label)
    offsets = {t: float(uncentred.term(t, X).mean()) for t in tier.TERMS}
    return Oracle(interaction, float(fit.intercept_[0]) + sum(offsets.values()), offsets, coef, label)
