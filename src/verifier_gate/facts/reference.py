"""Facts for the two references, T and the oracle (§14.2 D12): their smooth terms read on a fine grid.

E1 needs the lexicon's verdicts on T (the labels, and the scorer test) and on the oracle (what the sample
supports), so both need Facts in the same format as the fitted models. Their terms are smooth functions of
the planted unit shapes, not steps, so each is read on a fine grid of the training sample:

- a feature with at most GRID_POINTS distinct values (the count features) gets one step per value, exactly;
  any other feature gets the union of GRID_POINTS quantiles (dense where the data are, as the EBM's 1024
  bins) and GRID_POINTS evenly spaced points (fine in the sparse tails, where utilization and income are
  steep), both including the sample's minimum and maximum;
- the cuts are the midpoints between neighbouring grid points, and each step takes the term's value at its
  grid point; pairs are read on the product grid.

Measured on `syn-dominant` at n = 5,000 and 50,000: every term is within 0.016 logits of the smooth one on
every training row (median below 0.0003), except the dti step, which lands within half a grid step (about
0.0003) of 0.43, so the few rows in between (about 0.05%) get the other side of the step. Shares agree to 1e-4.

Unlike a fitted model, the references are not purified on the sample. Their pairs are pure in the population
by construction (products of population-centred factors, data/dgp.py), and that is how T is defined; on a grid
this fine, purifying on the sample would only move the sampling noise of the cells (about 50 rows per
utilization bin, spread over seven delinquency counts) into the main terms. Every term is centred on the
sample (weighted by the refit weights, if any), as T is. Terms that are zero everywhere (noise features, the
planted pairs of T at level "none") are left out, as a fitted model leaves out terms it never uses; a feature
without a term gets a zero term.
"""

from collections.abc import Mapping

import numpy as np
import pandas as pd

from verifier_gate.data import dgp
from verifier_gate.facts.steps import StepModel, StepTerm

GRID_POINTS = 1024


def grid_points(values: np.ndarray) -> np.ndarray:
    distinct = np.unique(values)
    if len(distinct) <= GRID_POINTS:
        return distinct
    quantiles = np.quantile(values, np.linspace(0.0, 1.0, GRID_POINTS))  # dense where the data are
    even = np.linspace(distinct[0], distinct[-1], GRID_POINTS)  # and fine in the sparse tails, where terms are steep
    return np.unique(np.concatenate([quantiles, even]))


def _cuts(points: np.ndarray) -> np.ndarray:
    return (points[:-1] + points[1:]) / 2.0


def reference_steps(model: dgp.Truth, X: pd.DataFrame, w: np.ndarray | None = None) -> StepModel:
    """T or an oracle (of either tier) as centred step terms on the grid of X. X is the training sample, w the
    refit weights. The grid depends on X only, so M and every refit share the same steps."""
    tier_features = tuple(model.features)
    points = {f: grid_points(np.asarray(X[f], dtype=np.float64)) for f in tier_features}
    raw: dict[str, StepTerm] = {}
    for name in model.term_names:
        features = model.term_features(name)
        mesh = np.meshgrid(*(points[f] for f in features), indexing="ij")
        scores = np.asarray(model.term(name, {f: m.ravel() for f, m in zip(features, mesh)})).reshape(mesh[0].shape)
        if not scores.any() and not np.any(model.term(name, X)):
            continue  # zero everywhere
        raw[name] = StepTerm(features, tuple(_cuts(points[f]) for f in features), scores.astype(np.float64))
    intercept = model.intercept
    steps: dict[str, StepTerm] = {}
    for name in [f for f in tier_features if f in raw] + [p for p in raw if p not in tier_features]:
        offset = float(np.average(raw[name](X), weights=w))
        steps[name] = raw[name].shifted(offset)
        intercept += offset
    for feature in tier_features:
        steps.setdefault(feature, StepTerm((feature,), (np.empty(0),), np.zeros(1)))
    order = list(tier_features) + [p for p in steps if p not in tier_features]
    return StepModel(intercept, {n: steps[n] for n in order})


def max_error(model: dgp.Truth, steps: StepModel, X: Mapping) -> float:
    """Largest |logit difference| between the smooth reference and its step form on the rows of X."""
    return float(np.max(np.abs(model.logit(X) - steps.logit(X))))
