import json

import numpy as np
import pandas as pd
import pytest
from scipy.special import logit
from xgboost import DMatrix

from verifier_gate.data import dgp
from verifier_gate.facts.xgb2 import float64_cut, purify_xgb2, raw_steps
from verifier_gate.models.fit_xgb2 import fit_xgb2


@pytest.fixture(scope="module")
def fitted():
    data = dgp.generate(dgp.Scenario("dominant", 5_000, 1))
    model = fit_xgb2(data.X, data.y, seed=1)
    return data, model, purify_xgb2(model, data.X)


def _rounds(model):
    return model.best_iteration + 1


def leaf_sum(model, X) -> np.ndarray:
    """Margin as the float64 sum of the leaves XGBoost itself reaches (pred_leaf), plus logit(base_score)."""
    learner = json.loads(model.get_booster().save_raw(raw_format="json"))["learner"]
    trees = learner["gradient_booster"]["model"]["trees"][: _rounds(model)]
    leaves = model.get_booster().predict(DMatrix(X), pred_leaf=True, iteration_range=(0, _rounds(model))).astype(int)
    values = np.column_stack([np.asarray(t["split_conditions"], dtype=np.float64)[leaves[:, j]] for j, t in enumerate(trees)])
    return logit(float(json.loads(learner["learner_model_param"]["base_score"])[0])) + values.sum(axis=1)


def _rows_on_thresholds(model, X: pd.DataFrame) -> pd.DataFrame:
    """Rows whose values sit exactly on a split threshold, or one float64 step either side of its cut."""
    learner = json.loads(model.get_booster().save_raw(raw_format="json"))["learner"]
    rows = []
    rng = np.random.default_rng(5)
    for tree in learner["gradient_booster"]["model"]["trees"][: _rounds(model)][:60]:
        for node, left in enumerate(tree["left_children"]):
            if left == -1:
                continue
            feature = X.columns[tree["split_indices"][node]]
            t = float(np.float32(tree["split_conditions"][node]))
            c = float64_cut(t)
            for value in (t, c, np.nextafter(c, -np.inf), np.nextafter(c, np.inf)):
                row = X.iloc[rng.integers(len(X))].copy()
                row[feature] = value
                rows.append(row)
    return pd.DataFrame(rows).reset_index(drop=True)


def test_float64_cut_agrees_with_float32_comparison():
    rng = np.random.default_rng(0)
    thresholds = np.concatenate([rng.normal(0, 100, 2_000), rng.uniform(0, 1, 2_000), [0.0, -0.0, 1.0, -1.0, 0.43]])
    for t in thresholds.astype(np.float32):
        c = float64_cut(float(t))
        below, above = np.nextafter(np.float32(t), np.float32(-np.inf)), np.nextafter(np.float32(t), np.float32(np.inf))
        mid_low, mid_high = (float(below) + float(t)) / 2, (float(t) + float(above)) / 2
        for x in (float(t), c, np.nextafter(c, -np.inf), np.nextafter(c, np.inf), mid_low, mid_high, float(below)):
            assert (np.float32(x) < t) == (x < c), (t, x, c)


def test_decomposition_equals_xgboost_s_own_leaves_exactly(fitted):
    data, model, purified = fitted
    assert model.get_booster().num_boosted_rounds() > _rounds(model), "the fit should keep patience rounds to skip"
    fresh = dgp.sample_features(5_000, np.random.default_rng(99))
    for X in (data.X, fresh, _rows_on_thresholds(model, data.X)):
        exact = leaf_sum(model, X)
        np.testing.assert_allclose(raw_steps(model).logit(X), exact, rtol=0, atol=1e-9)
        np.testing.assert_allclose(purified.logit(X), exact, rtol=0, atol=1e-9)


def test_decomposition_reproduces_the_margin_up_to_float32_rounding(fitted):
    """XGBoost adds its trees in float32, so its own margin is only accurate to a few 1e-6 (the test above
    shows the decomposition is exact)."""
    data, model, purified = fitted
    margin = model.predict(data.X, output_margin=True).astype(np.float64)
    bound = _rounds(model) * np.finfo(np.float32).eps * np.abs(margin).max()
    assert np.abs(purified.logit(data.X) - margin).max() < bound


def test_terms_are_centred_and_pairs_are_pure(fitted):
    data, _, purified = fitted
    assert purified.features == tuple(dgp.FEATURES)
    for values in purified.terms(data.X).values():
        assert abs(values.mean()) < 1e-9
    for name in purified.pairs:
        term = purified.steps[name]
        weights = term.weights(data.X)
        scale = np.average(np.abs(term.scores), weights=weights)
        for axis in (0, 1):
            marginal = (term.scores * weights).sum(axis=axis) / np.maximum(weights.sum(axis=axis), 1e-12)
            assert np.abs(marginal).max() < 1e-6 * max(scale, 1e-12)


def test_pairs_are_the_interaction_part_of_tree_shap(fitted):
    """2 x TreeSHAP's interaction value = our pure pair + main-effect parts (TreeSHAP centres on hessian
    cover, we on row counts). A pure pair is orthogonal to every function of one feature, so the regression
    slope of SHAP on our pair is exactly 1 if and only if the two agree on the interaction part."""
    data, model, purified = fitted
    interactions = model.get_booster().predict(DMatrix(data.X), pred_interactions=True, iteration_range=(0, _rounds(model)))
    columns = list(data.X.columns)
    shares = purified.shares(data.X)
    for name in sorted(purified.pairs, key=lambda n: -shares[n])[:5]:
        a, b = purified.steps[name].features
        shap = 2 * interactions[:, columns.index(a), columns.index(b)].astype(np.float64)
        ours = purified.term(name, data.X)
        slope = (shap - shap.mean()) @ ours / (ours @ ours)
        assert slope == pytest.approx(1.0, abs=1e-4), name
        assert np.corrcoef(shap, ours)[0, 1] > 0.95, name


def test_planted_amplification_is_the_largest_pair(fitted):
    data, _, purified = fitted
    shares = purified.shares(data.X)
    assert max(purified.pairs, key=shares.get) == dgp.AMPLIFICATION


def test_weighted_purification_is_centred_on_the_weights(fitted):
    data, model, _ = fitted
    w = np.random.default_rng(3).poisson(1.0, len(data.y)).astype(float)
    weighted = purify_xgb2(model, data.X, w)
    np.testing.assert_allclose(weighted.logit(data.X), leaf_sum(model, data.X), rtol=0, atol=1e-9)
    for values in weighted.terms(data.X).values():
        assert abs(np.average(values, weights=w)) < 1e-9
