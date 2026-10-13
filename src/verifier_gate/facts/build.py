"""Build Facts from a purified model M and its bootstrap draws.

`Frame` fixes where every quantity is read: M's steps, the training rows in each step, and the 5th and 95th
percentile of each feature. M and every refit are read through the same frame (Frame.read), so M's values
and the draws behind its bands are measured the same way.

Bands (level 95%):
- curves, pointwise: M +- 1.96 sd of the refits, per step.
- curves, simultaneous (sup-t, Montiel Olea and Plagborg-Moller 2019): M +- c sd, where c is the 95th
  percentile over refits of max over steps of |refit - mean of refits| / sd. Steps without training rows
  are left out of the max. Covers the whole curve in 95% of refits, which is what makes "negligible" and
  "increases" safe to judge (§14 D4). Both bands use the same sd, so the simultaneous band contains the
  pointwise one whenever c >= 1.96.
- scalars (importance, share, rank, net change, conditional effects): 2.5th and 97.5th percentile of the
  refits. Shares are bounded and skewed near zero, where a normal band would be wrong.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from importlib.metadata import version

import numpy as np
import pandas as pd

from verifier_gate.facts.schema import ConditionalEffect, Draws, Estimate, Facts, FeatureFacts, PairFacts
from verifier_gate.facts.steps import StepModel

LEVEL = 0.95
QUANTILES = (0.05, 0.95)  # low and high value of a feature, as for direction in the acceptance check
POINTWISE_Z = 1.959963984540054


def _representative(cuts: np.ndarray) -> np.ndarray:
    """A point inside each step: its lower edge, or just below the first cut for the first step."""
    first = np.nextafter(cuts[0], -np.inf) if len(cuts) else 0.0
    return np.concatenate([[first], cuts])


@dataclass(frozen=True, eq=False)
class Frame:
    reference: StepModel
    rows_in_step: Mapping[str, np.ndarray]  # feature -> step index of each training row
    counts: Mapping[str, np.ndarray]  # feature -> training rows per step
    low_high: Mapping[str, tuple[float, float]]  # feature -> 5th, 95th percentile

    @classmethod
    def of(cls, reference: StepModel, X: pd.DataFrame) -> "Frame":
        rows, counts, low_high = {}, {}, {}
        for f in reference.features:
            term = reference.steps[f]
            rows[f] = term.index(X)[0]
            counts[f] = np.bincount(rows[f], minlength=term.scores.size).astype(np.float64)
            low_high[f] = tuple(float(q) for q in np.quantile(X[f], QUANTILES, method="inverted_cdf"))
        return cls(reference, rows, counts, low_high)

    def orderings(self, pair: str) -> tuple[tuple[str, str], tuple[str, str]]:
        a, b = self.reference.steps[pair].features
        return (a, b), (b, a)

    def read(self, model: StepModel, X: pd.DataFrame, w: np.ndarray | None = None) -> dict:
        """Every quantity of the facts, measured on `model` (M or a refit) in this frame.

        Importance, share and rank use the model's own sample (weights w); terms of M that the model lacks
        count as zero, and the total includes the model's terms that M lacks."""
        terms = model.terms(X)
        importance = {n: float(np.average(np.abs(v), weights=w)) for n, v in terms.items()}
        total = sum(importance.values())
        by_features = {frozenset(model.steps[n].features): n for n in model.term_names}
        lookup = {n: by_features.get(frozenset(t.features)) for n, t in self.reference.steps.items()}
        out = {kind: {} for kind in Draws.KINDS}
        for name, own in lookup.items():
            out["importance"][name] = importance[own] if own else 0.0
            out["share"][name] = out["importance"][name] / total
        order = sorted(self.reference.features, key=lambda f: -out["importance"][f])
        for f in self.reference.features:
            out["rank"][f] = float(order.index(f) + 1)
            values = terms[lookup[f]] if lookup[f] else np.zeros(len(X))
            curve = np.bincount(self.rows_in_step[f], weights=values, minlength=len(self.counts[f]))
            empty = self.counts[f] == 0
            curve = np.divide(curve, self.counts[f], out=np.zeros_like(curve), where=~empty)
            if empty.any() and lookup[f]:
                curve[empty] = model.term(lookup[f], {f: _representative(self.reference.steps[f].cuts[0])[empty]})
            out["curves"][f] = curve
            out["net_change"][f] = float(np.diff(self._main(model, lookup, f, {f: np.array(self.low_high[f])}))[0])
        for pair in self.reference.pairs:
            for feature, moderator in self.orderings(pair):
                lo, hi = self.low_high[feature]
                m_lo, m_hi = self.low_high[moderator]
                at = {feature: np.array([lo, hi, lo, hi]), moderator: np.array([m_lo, m_lo, m_hi, m_hi])}
                total_effect = self._main(model, lookup, feature, at)
                if lookup[pair]:
                    total_effect = total_effect + model.term(lookup[pair], at)
                out["conditional"][f"{feature} | {moderator}"] = np.array(
                    [total_effect[1] - total_effect[0], total_effect[3] - total_effect[2]]
                )
        return out

    @staticmethod
    def _main(model: StepModel, lookup: Mapping, feature: str, at: Mapping) -> np.ndarray:
        n = len(next(iter(at.values())))
        return model.term(lookup[feature], at) if lookup[feature] else np.zeros(n)


def percentile_band(draws: np.ndarray) -> tuple[float, float]:
    lo, hi = np.quantile(draws, [(1 - LEVEL) / 2, (1 + LEVEL) / 2], axis=0)
    return float(lo), float(hi)


def curve_bands(center: np.ndarray, draws: np.ndarray, counts: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """Pointwise and simultaneous (sup-t) bands, each (2, steps), and the sup-t critical value."""
    sd = draws.std(axis=0, ddof=1)
    used = (counts > 0) & (sd > 0)
    if used.any():
        z = np.abs(draws[:, used] - draws[:, used].mean(axis=0)) / sd[used]
        critical = float(np.quantile(z.max(axis=1), LEVEL))
    else:  # the term is the same in every refit (e.g. a feature no refit uses)
        critical = 0.0
    pointwise = np.stack([center - POINTWISE_Z * sd, center + POINTWISE_Z * sd])
    simultaneous = np.stack([center - critical * sd, center + critical * sd])
    return pointwise, simultaneous, critical


def _estimate(value: float, draws: np.ndarray | None) -> Estimate:
    return Estimate(float(value), None if draws is None else percentile_band(draws))


def build_facts(reference: StepModel, X: pd.DataFrame, draws: Draws | None = None, model: Mapping | None = None) -> Facts:
    """Facts of M (reference) on its training sample X, with bands if draws are given."""
    frame = Frame.of(reference, X)
    own = frame.read(reference, X)
    n = len(X)
    pick = (lambda kind, key: getattr(draws, kind)[key]) if draws is not None else (lambda kind, key: None)  # noqa: E731
    features = []
    for f in reference.features:
        term = reference.steps[f]
        pointwise = simultaneous = critical = None
        if draws is not None:
            pointwise, simultaneous, critical = curve_bands(term.scores, draws.curves[f], frame.counts[f])
        features.append(
            FeatureFacts(
                f, term.cuts[0], term.scores, frame.counts[f] / n, pointwise, simultaneous, critical,
                *(_estimate(own[k][f], pick(k, f)) for k in ("importance", "share", "rank")),
                frame.low_high[f], _estimate(own["net_change"][f], pick("net_change", f)),
            )  # fmt: skip
        )
    pairs = []
    for p in reference.pairs:
        term = reference.steps[p]
        conditional = []
        for feature, moderator in frame.orderings(p):
            key = f"{feature} | {moderator}"
            values, d = own["conditional"][key], pick("conditional", key)
            conditional.append(
                ConditionalEffect(
                    feature, moderator, frame.low_high[feature], frame.low_high[moderator],
                    _estimate(values[0], None if d is None else d[:, 0]),
                    _estimate(values[1], None if d is None else d[:, 1]),
                    _estimate(values[1] - values[0], None if d is None else d[:, 1] - d[:, 0]),
                )  # fmt: skip
            )
        pairs.append(
            PairFacts(
                p, term.features, term.cuts, term.scores, term.weights(X) / n,
                _estimate(own["importance"][p], pick("importance", p)), _estimate(own["share"][p], pick("share", p)),
                tuple(conditional),
            )  # fmt: skip
        )
    bands = {"refits": 0 if draws is None else draws.refits, "level": LEVEL, "quantiles": list(QUANTILES)}
    if draws is not None:
        bands |= {
            "weights": "Poisson(1) counts per row, rows with count 0 left out (D17)",
            "curves": "pointwise: M +- 1.96 sd; simultaneous: M +- c sd, c = sup-t critical value",
            "scalars": "2.5th and 97.5th percentile of the refits",
        }
    software = {p: version(p) for p in ("interpret-core", "xgboost", "numpy", "scikit-learn")}
    return Facts({**(model or {}), "n": n, "software": software}, bands, reference.intercept, tuple(features), tuple(pairs), draws)
