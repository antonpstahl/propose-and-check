"""Exact step-function form of an additive model: the common ground of every fact provider.

EBM and XGB2 are both sums of piecewise-constant terms on one or two features. Each provider turns its model
into a StepModel without the purification step (raw terms), and `purify` then does the rest for every model
alike (§14 D2): it moves the main-effect parts of each pair into the main terms with
`interpret.utils.purify` and centres every term on the training sample. So "pure" and "centred" mean the
same for every model, and the result can be compared with T term by term.

Convention: a term on cuts c_1 < ... < c_k has k + 1 steps, and x falls into step i = #{j : c_j <= x}. A value
equal to a cut belongs to the upper step, as in the EBM's binning and in XGBoost's `x < threshold -> left`.
Missing values are not supported (no tier of the benchmark has any); evaluating a row with NaN raises.
"""

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
from interpret.utils import purify as interpret_purify

PAIR_SEPARATOR = " & "  # pair names as in interpret: "utilization & n_delinquencies"


def pair_name(a: str, b: str) -> str:
    return f"{a}{PAIR_SEPARATOR}{b}"


def _column(X: Mapping, feature: str) -> np.ndarray:
    values = np.asarray(X[feature], dtype=np.float64)
    if np.isnan(values).any():
        raise ValueError(f"missing values in {feature}; step terms do not support them")
    return values


def _lower_edges(cuts: np.ndarray) -> np.ndarray:
    """Lower edge of each step; -inf for the first."""
    return np.concatenate([[-np.inf], cuts])


@dataclass(frozen=True, eq=False)
class StepTerm:
    """A piecewise-constant term on one feature (main) or two (pair). scores has one axis per feature."""

    features: tuple[str, ...]
    cuts: tuple[np.ndarray, ...]
    scores: np.ndarray

    def __post_init__(self):
        assert len(self.features) == len(self.cuts) == self.scores.ndim
        assert self.scores.shape == tuple(len(c) + 1 for c in self.cuts), (self.scores.shape, self.features)
        assert all(np.all(np.diff(c) > 0) for c in self.cuts), f"cuts not increasing for {self.features}"

    @property
    def name(self) -> str:
        return PAIR_SEPARATOR.join(self.features)

    def index(self, X: Mapping) -> tuple[np.ndarray, ...]:
        """Step index of each row, per feature."""
        return tuple(np.searchsorted(c, _column(X, f), side="right") for f, c in zip(self.features, self.cuts))

    def __call__(self, X: Mapping) -> np.ndarray:
        return self.scores[self.index(X)]

    def on_cuts(self, cuts: tuple[np.ndarray, ...]) -> "StepTerm":
        """The same function on finer cuts (each a superset of the term's own)."""
        assert all(np.isin(own, new).all() for own, new in zip(self.cuts, cuts)), "cuts must be a superset"
        idx = np.ix_(*(np.searchsorted(own, _lower_edges(new), side="right") for own, new in zip(self.cuts, cuts)))
        return StepTerm(self.features, tuple(cuts), self.scores[idx])

    def shifted(self, offset: float) -> "StepTerm":
        return StepTerm(self.features, self.cuts, self.scores - offset)

    def weights(self, X: Mapping, w: np.ndarray | None = None) -> np.ndarray:
        """Training weight (row count, or sum of w) in each step or cell."""
        counts = np.zeros(self.scores.shape)
        np.add.at(counts, self.index(X), 1.0 if w is None else w)
        return counts


def add(a: StepTerm, b: StepTerm) -> StepTerm:
    """Sum of two terms on the same features, on the union of their cuts."""
    assert a.features == b.features
    cuts = tuple(np.union1d(ca, cb) for ca, cb in zip(a.cuts, b.cuts))
    return StepTerm(a.features, cuts, a.on_cuts(cuts).scores + b.on_cuts(cuts).scores)


@dataclass(frozen=True, eq=False)
class StepModel:
    """intercept + sum of step terms, exactly. Same methods as dgp.Truth, so the acceptance checks and the
    fact builder run on T, the oracle and any fitted model alike."""

    intercept: float
    steps: Mapping[str, StepTerm]  # by term name; main terms first, then pairs

    @property
    def term_names(self) -> tuple[str, ...]:
        return tuple(self.steps)

    @property
    def features(self) -> tuple[str, ...]:
        return tuple(n for n, t in self.steps.items() if len(t.features) == 1)

    @property
    def pairs(self) -> tuple[str, ...]:
        return tuple(n for n, t in self.steps.items() if len(t.features) == 2)

    def term(self, name: str, X: Mapping) -> np.ndarray:
        return self.steps[name](X)

    def terms(self, X: Mapping) -> dict[str, np.ndarray]:
        return {name: term(X) for name, term in self.steps.items()}

    def logit(self, X: Mapping) -> np.ndarray:
        return self.intercept + sum(self.terms(X).values())

    def importances(self, X: Mapping, w: np.ndarray | None = None) -> dict[str, float]:
        """Mean |score| per term over the rows of X, weighted by w if given."""
        return {name: float(np.average(np.abs(values), weights=w)) for name, values in self.terms(X).items()}

    def shares(self, X: Mapping, w: np.ndarray | None = None) -> dict[str, float]:
        importances = self.importances(X, w)
        total = sum(importances.values())
        return {name: value / total for name, value in importances.items()}


def _ordered(steps: Mapping[str, StepTerm], raw_names: tuple[str, ...], feature_order: tuple[str, ...]) -> dict:
    """Main terms in feature order, then the pairs in the raw model's order."""
    rank = {f: i for i, f in enumerate(feature_order)}
    mains = sorted((n for n, t in steps.items() if len(t.features) == 1), key=lambda n: rank.get(n, len(rank)))
    pairs = [n for n in raw_names if n in steps and len(steps[n].features) == 2]
    return {n: steps[n] for n in mains + pairs}


def purify(raw: StepModel, X: Mapping, w: np.ndarray | None = None, feature_order: tuple[str, ...] = ()) -> StepModel:
    """Purify every pair on the training weights and centre every term on the training sample.

    Each pair is split by `interpret.utils.purify` (fixed processing order, so the result is reproducible)
    into a pure part, whose weighted mean over either feature is zero, and one main-effect part per feature,
    which is added to that feature's main term (created if the model has none). Features in feature_order
    without any term get a zero term. w are row weights (the Poisson counts of a bootstrap refit); None means
    every row once. logit(x) is unchanged on any x.
    """
    intercept = raw.intercept
    mains = {n: t for n, t in raw.steps.items() if len(t.features) == 1}
    pairs = {}
    for name, term in raw.steps.items():
        if len(term.features) != 2:
            continue
        pure, parts, pure_intercept = interpret_purify(term.scores, term.weights(X, w), is_randomized=False)
        pairs[name] = StepTerm(term.features, term.cuts, pure)
        intercept += float(pure_intercept[0]) if np.ndim(pure_intercept) else float(pure_intercept)
        for (dim,), part in parts:
            feature = term.features[dim]
            impurity = StepTerm((feature,), (term.cuts[dim],), np.asarray(part, dtype=np.float64))
            mains[feature] = add(mains[feature], impurity) if feature in mains else impurity
    for feature in feature_order:  # a feature the model never uses gets a zero term, so it has facts too
        mains.setdefault(feature, StepTerm((feature,), (np.empty(0),), np.zeros(1)))
    uncentred = _ordered(mains | pairs, raw.term_names, feature_order or raw.features)
    centred = {}
    for name, term in uncentred.items():
        offset = float(np.average(term(X), weights=w))
        centred[name] = term.shifted(offset)
        intercept += offset
    return StepModel(intercept, centred)
