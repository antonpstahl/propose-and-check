"""Facts from XGB2: depth-2 trees split exactly into main and pair terms, then purified and centred like the EBM.

Every leaf of a depth-2 tree is reached through at most two features, so its value times the indicator of its
region is a step function on those features. Summing the leaves by feature set gives raw main and pair terms;
steps.purify then does what it does for the EBM.

Parsing details, all covered by the margin test (terms + intercept reproduce XGBoost's margin):
- Trees come from the model JSON (save_raw). Only the first best_iteration + 1 rounds count: predict stops
  there after early stopping, but the model keeps the trees of the patience rounds.
- XGBoost compares float32(x) < t in float32. Each threshold t becomes the float64 cut c with
  float32(x) < t  <=>  x < c, so the step terms take float64 inputs and agree on every row, including rows
  whose float32 rounding lands on a threshold.
- The intercept is stored as base_score, a probability; the margin starts at logit(base_score).
- Leaf values are the split_conditions of leaf nodes, learning rate already applied.
- Missing values are not supported (steps.py), so the default direction of a split never matters.
"""

import json
from collections import defaultdict
from collections.abc import Mapping

import numpy as np
from scipy.special import logit
from xgboost import XGBClassifier

from verifier_gate.facts.steps import StepModel, StepTerm, _lower_edges, pair_name, purify


def float64_cut(threshold: float) -> float:
    """The float64 c with float32(x) < t <=> x < c (float64 -> float32 rounds to nearest, ties to even)."""
    t = np.float32(threshold)
    below = np.nextafter(t, np.float32(-np.inf))
    mid = (np.float64(below) + np.float64(t)) / 2.0  # exact: one more bit than float32 needs
    t_is_even = (np.array(t).view(np.uint32) & 1) == 0  # a tie at mid rounds to the even neighbour
    return float(mid if t_is_even else np.nextafter(mid, np.inf))


def _leaves(tree: Mapping, node: int = 0, region: Mapping | None = None):
    """(leaf value, {feature index: (lo, hi)}) for each leaf; the leaf is reached iff lo <= x < hi per feature."""
    region = region or {}
    left, right = tree["left_children"][node], tree["right_children"][node]
    if left == -1:
        yield float(tree["split_conditions"][node]), region
        return
    feature, cut = tree["split_indices"][node], float64_cut(tree["split_conditions"][node])
    lo, hi = region.get(feature, (-np.inf, np.inf))
    yield from _leaves(tree, left, {**region, feature: (lo, min(hi, cut))})
    yield from _leaves(tree, right, {**region, feature: (max(lo, cut), hi)})


def _booster_json(model: XGBClassifier) -> dict:
    learner = json.loads(model.get_booster().save_raw(raw_format="json"))["learner"]
    if learner["objective"]["name"] != "binary:logistic":
        raise ValueError(f"only binary:logistic is supported, not {learner['objective']['name']}")
    return learner


def _rounds(model: XGBClassifier) -> int:
    """Boosting rounds predict uses: up to the best iteration after early stopping, otherwise all."""
    try:
        return model.best_iteration + 1
    except AttributeError:
        return model.get_booster().num_boosted_rounds()


def raw_steps(model: XGBClassifier) -> StepModel:
    """Sum of the leaves of the trees predict uses, by feature set; unpurified."""
    learner = _booster_json(model)
    names = learner["feature_names"] or [f"f{i}" for i in range(int(learner["learner_model_param"]["num_feature"]))]
    booster = learner["gradient_booster"]["model"]
    trees = booster["trees"][: booster["iteration_indptr"][_rounds(model)]]
    base_score = float(json.loads(learner["learner_model_param"]["base_score"])[0])
    intercept = float(logit(base_score))
    pieces = defaultdict(list)  # sorted feature indices -> [(value, intervals)]
    for tree in trees:
        for value, region in _leaves(tree):
            features = tuple(sorted(region))
            if len(features) > 2:
                raise ValueError(f"a leaf depends on {len(features)} features; XGB2 must have max_depth=2")
            if features:
                pieces[features].append((value, [region[f] for f in features]))
            else:
                intercept += value  # a tree without a split
    steps = {}
    for features, group in pieces.items():
        cuts = []
        for d in range(len(features)):
            bounds = np.array([b for _, intervals in group for b in intervals[d]])
            cuts.append(np.unique(bounds[np.isfinite(bounds)]))
        edges = [_lower_edges(c) for c in cuts]
        scores = np.zeros(tuple(len(c) + 1 for c in cuts))
        for value, intervals in group:
            masks = [(e >= lo) & (e < hi) for e, (lo, hi) in zip(edges, intervals)]
            scores += value * (masks[0] if len(masks) == 1 else np.outer(masks[0], masks[1]))
        term_features = tuple(names[f] for f in features)
        name = term_features[0] if len(features) == 1 else pair_name(*term_features)
        steps[name] = StepTerm(term_features, tuple(cuts), scores)
    order = {n: i for i, n in enumerate(names)}
    mains = sorted((n for n, t in steps.items() if len(t.features) == 1), key=order.get)
    pairs = sorted((n for n, t in steps.items() if len(t.features) == 2), key=lambda n: [order[f] for f in steps[n].features])
    return StepModel(intercept, {n: steps[n] for n in mains + pairs})


def purify_xgb2(model: XGBClassifier, X: Mapping, w: np.ndarray | None = None) -> StepModel:
    """Purified, centred terms of a fitted XGB2. X is the training sample, w the refit weights if any.

    logit(x) = intercept + sum of term(name, x) over term_names equals the model's margin on any x."""
    raw = raw_steps(model)
    return purify(raw, X, w, feature_order=tuple(model.get_booster().feature_names or raw.features))
