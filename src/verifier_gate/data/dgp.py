"""Synthetic tier: planted main and pair terms on the logit scale, purification, sampling of y.

The outcome is y ~ Bernoulli(sigmoid(b0 + sum_j f_j(x_j) + sum g_jk(x_j, x_k))). Each planted term is a
unit shape times a coefficient. Coefficients are set so that each term's importance (mean |score|) has a
target share of the total importance, and b0 is set so the default rate hits BASE_RATE. All population
constants are computed once on a fixed reference sample.

Pairs are products of population-centred factors of independent features, so their marginal means are
zero: they are pure in the functional-ANOVA sense by construction and carry no main-effect part.

Design: rows are drawn for the largest sample size and the first n are used, and the uniforms that decide
y are shared across interaction levels. So within one seed, the n = 5,000 data are a subset of the
n = 50,000 data, and the levels differ only through the planted pairs (common random numbers).
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import cache

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.special import expit

FEATURES = (
    "utilization",
    "n_delinquencies",
    "income",
    "history_months",
    "dti",
    "n_inquiries",
    "age",
    "noise_1",
    "noise_2",
)

INTERACTION_LEVELS = ("none", "weak", "dominant")
SAMPLE_SIZES = (5_000, 50_000)
SEEDS = (1, 2, 3)
DISCOVERY_SEED = 1

BASE_RATE = 0.22  # default rate, matches the plasmode tier (TaiwanCredit)
# Sum of main-term importances in logits. 1.6 gives the planted model an AUC of about 0.77 (0.755 at
# "dominant"), close to what good models reach on TaiwanCredit.
TOTAL_MAIN_IMPORTANCE = 1.6
REFERENCE_N = 1_000_000
REFERENCE_SEED = 0

# Target importance shares of the main terms at interaction level "none". Pairs, when present, take
# their share from the total, and the main terms keep their coefficients (so their shares shrink).
MAIN_SHARES = {
    "utilization": 0.41,
    "n_delinquencies": 0.24,
    "income": 0.13,
    "history_months": 0.10,
    "dti": 0.075,
    "n_inquiries": 0.035,
    "age": 0.01,
    "noise_1": 0.0,
    "noise_2": 0.0,
}

AMPLIFICATION = "utilization & n_delinquencies"
SIGN_FLIP = "history_months & n_inquiries"

PAIR_SHARES = {
    "none": {AMPLIFICATION: 0.0, SIGN_FLIP: 0.0},
    "weak": {AMPLIFICATION: 0.03, SIGN_FLIP: 0.025},
    "dominant": {AMPLIFICATION: 0.21, SIGN_FLIP: 0.025},
}

PAIR_PATTERNS = {AMPLIFICATION: "amplification", SIGN_FLIP: "sign_flip"}

FEATURE_ROLES = {
    "utilization": "strong",
    "n_delinquencies": "strong",
    "income": "moderate",
    "history_months": "peak",
    "dti": "threshold",
    "n_inquiries": "weak",
    "age": "near_flat",
    "noise_1": "noise",
    "noise_2": "noise",
}


def _utilization(u):
    return u + 5.0 * np.maximum(u - 0.6, 0.0)


def _delinquencies(d):
    return 1.0 - np.exp(-d / 1.5)


def _income(x):
    return -np.log(x / 50_000.0)


def _history(h):
    return -(h - 6.0) / 354.0 + 0.15 * np.exp(-(((h - 36.0) / 8.0) ** 2))


def _dti(x):
    return (x >= 0.43).astype(np.float64)


def _identity(x):
    return x


def _age(a):
    return -(a - 21.0) / 54.0


def _zero(x):
    return np.zeros_like(x)


def _thin_file(h):
    return -h


MAIN_SHAPES: dict[str, Callable[[np.ndarray], np.ndarray]] = {
    "utilization": _utilization,
    "n_delinquencies": _delinquencies,
    "income": _income,
    "history_months": _history,
    "dti": _dti,
    "n_inquiries": _identity,
    "age": _age,
    "noise_1": _zero,
    "noise_2": _zero,
}

# Pair term = c * (factor_a - E factor_a) * (factor_b - E factor_b). The amplification pair reuses both
# main shapes, so it scales the utilization effect up or down with delinquencies. The sign-flip pair
# multiplies inquiries with a thin-file factor that is positive for short histories.
PAIR_FACTORS: dict[str, tuple[tuple[str, str], tuple[Callable, Callable]]] = {
    AMPLIFICATION: (("utilization", "n_delinquencies"), (_utilization, _delinquencies)),
    SIGN_FLIP: (("history_months", "n_inquiries"), (_thin_file, _identity)),
}

TERMS = FEATURES + tuple(PAIR_FACTORS)


def sample_features(n: int, rng: np.random.Generator) -> pd.DataFrame:
    """Draw n rows of independent features."""
    return pd.DataFrame(
        {
            "utilization": rng.beta(2.0, 3.0, n),
            "n_delinquencies": np.minimum(rng.poisson(0.8, n), 6),
            "income": rng.lognormal(np.log(50_000.0), 0.5, n),
            "history_months": rng.uniform(6.0, 360.0, n),
            "dti": rng.uniform(0.0, 0.6, n),
            "n_inquiries": rng.poisson(1.5, n),
            "age": rng.uniform(21.0, 75.0, n),
            "noise_1": rng.normal(0.0, 1.0, n),
            "noise_2": rng.normal(0.0, 1.0, n),
        }
    )


@cache
def _reference() -> pd.DataFrame:
    return sample_features(REFERENCE_N, np.random.default_rng(REFERENCE_SEED))


def _column(X: Mapping, feature: str) -> np.ndarray:
    return np.asarray(X[feature], dtype=np.float64)


@cache
def _population() -> tuple[dict, dict]:
    """Population means of the unit shapes and pair factors, and importances of the centred unit terms."""
    ref = _reference()
    means: dict[str, float | tuple[float, float]] = {}
    importances: dict[str, float] = {}
    for feature, shape in MAIN_SHAPES.items():
        values = shape(_column(ref, feature))
        means[feature] = float(values.mean())
        importances[feature] = float(np.abs(values - values.mean()).mean())
    for name, ((a, b), (fa, fb)) in PAIR_FACTORS.items():
        va, vb = fa(_column(ref, a)), fb(_column(ref, b))
        means[name] = (float(va.mean()), float(vb.mean()))
        importances[name] = float(np.abs((va - va.mean()) * (vb - vb.mean())).mean())
    return means, importances


@cache
def coefficients(interaction: str) -> dict[str, float]:
    """Coefficient of each term's unit shape at the given interaction level."""
    _, importances = _population()
    coef = {f: MAIN_SHARES[f] * TOTAL_MAIN_IMPORTANCE / importances[f] if MAIN_SHARES[f] else 0.0 for f in FEATURES}
    pair_shares = PAIR_SHARES[interaction]
    total = TOTAL_MAIN_IMPORTANCE / (1.0 - sum(pair_shares.values()))
    for name, share in pair_shares.items():
        coef[name] = share * total / importances[name]
    return coef


def _population_term(name: str, X: Mapping, interaction: str) -> np.ndarray:
    """Planted term centred on the population (not yet on the sample)."""
    means, _ = _population()
    coef = coefficients(interaction)[name]
    if name in MAIN_SHAPES:
        return coef * (MAIN_SHAPES[name](_column(X, name)) - means[name])
    (a, b), (fa, fb) = PAIR_FACTORS[name]
    ma, mb = means[name]
    return coef * (fa(_column(X, a)) - ma) * (fb(_column(X, b)) - mb)


@cache
def base_intercept(interaction: str) -> float:
    """b0 such that the population default rate equals BASE_RATE."""
    ref = _reference()
    eta = sum(_population_term(t, ref, interaction) for t in TERMS)
    return float(brentq(lambda b0: expit(b0 + eta).mean() - BASE_RATE, -20.0, 20.0, xtol=1e-12))


@dataclass(frozen=True)
class Truth:
    """Planted truth T: every term centred on the training sample, as the EBM centres its terms.

    logit(x) = intercept + sum of term(name, x) over TERMS, exactly, on any x.
    """

    interaction: str
    intercept: float
    offsets: Mapping[str, float]

    def term(self, name: str, X: Mapping) -> np.ndarray:
        return _population_term(name, X, self.interaction) - self.offsets[name]

    def terms(self, X: Mapping) -> dict[str, np.ndarray]:
        return {name: self.term(name, X) for name in TERMS}

    def logit(self, X: Mapping) -> np.ndarray:
        return self.intercept + sum(self.terms(X).values())

    def importances(self, X: Mapping) -> dict[str, float]:
        """Mean |score| per term over the rows of X."""
        return {name: float(np.abs(values).mean()) for name, values in self.terms(X).items()}

    def shares(self, X: Mapping) -> dict[str, float]:
        importances = self.importances(X)
        total = sum(importances.values())
        return {name: value / total for name, value in importances.items()}


@dataclass(frozen=True)
class Scenario:
    interaction: str
    n: int
    seed: int

    @property
    def id(self) -> str:
        return f"syn-{self.interaction}-n{self.n}-s{self.seed}"

    @property
    def is_discovery(self) -> bool:
        return self.seed == DISCOVERY_SEED


SCENARIOS = tuple(Scenario(i, n, s) for i in INTERACTION_LEVELS for n in SAMPLE_SIZES for s in SEEDS)


@dataclass(frozen=True)
class Dataset:
    scenario: Scenario
    X: pd.DataFrame
    y: np.ndarray
    truth: Truth


def make_truth(X: Mapping, interaction: str) -> Truth:
    """Planted truth for the sample X: population terms re-centred on X, offsets moved into the intercept."""
    offsets = {name: float(_population_term(name, X, interaction).mean()) for name in TERMS}
    return Truth(interaction, base_intercept(interaction) + sum(offsets.values()), offsets)


def generate(scenario: Scenario) -> Dataset:
    rng = np.random.default_rng(scenario.seed)
    n_max = max(SAMPLE_SIZES)
    X = sample_features(n_max, rng).iloc[: scenario.n].reset_index(drop=True)
    uniforms = rng.uniform(size=n_max)[: scenario.n]
    truth = make_truth(X, scenario.interaction)
    y = (uniforms < expit(truth.logit(X))).astype(np.int64)
    return Dataset(scenario, X, y, truth)
