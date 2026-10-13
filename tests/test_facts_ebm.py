import numpy as np
import pytest

from verifier_gate.data import dgp
from verifier_gate.facts.ebm import purify_ebm
from verifier_gate.models.fit_ebm import fit_ebm


@pytest.fixture(scope="module")
def fitted():
    data = dgp.generate(dgp.Scenario("dominant", 5_000, 1))
    ebm = fit_ebm(data.X, data.y, seed=1, outer_bags=2)
    return data, ebm, purify_ebm(ebm, data.X)


def test_purified_terms_reproduce_the_margin_on_any_rows(fitted):
    data, ebm, purified = fitted
    fresh = dgp.sample_features(2_000, np.random.default_rng(99))
    for X in (data.X, fresh):
        np.testing.assert_allclose(purified.logit(X), ebm.decision_function(X), atol=1e-9)


def test_terms_are_centred_on_the_training_sample(fitted):
    data, _, purified = fitted
    assert set(purified.terms(data.X)) == set(purified.term_names)
    for values in purified.terms(data.X).values():
        assert abs(values.mean()) < 1e-9


def test_pairs_are_pure(fitted):
    _, ebm, purified = fitted
    assert purified.pure_pairs, "the fit has no pairs"
    for idx, pure in purified.pure_pairs.items():
        weights = ebm.bin_weights_[idx]
        scale = np.average(np.abs(pure), weights=weights)
        for axis in (0, 1):
            marginal = (pure * weights).sum(axis=axis) / np.maximum(weights.sum(axis=axis), 1e-12)
            assert np.abs(marginal).max() < 1e-6 * max(scale, 1e-12)


def test_a_main_term_depends_only_on_its_feature(fitted):
    data, _, purified = fitted
    rows = data.X.iloc[:500]
    full = purified.term("history_months", rows)
    alone = purified.term("history_months", {"history_months": rows["history_months"].to_numpy()})
    np.testing.assert_allclose(full, alone, atol=1e-12)
    pair = dgp.SIGN_FLIP
    if pair in purified.term_names:
        subset = rows[["history_months", "n_inquiries"]]
        np.testing.assert_allclose(purified.term(pair, rows), purified.term(pair, subset), atol=1e-12)


def test_shares_sum_to_one(fitted):
    data, _, purified = fitted
    assert sum(purified.shares(data.X).values()) == pytest.approx(1.0)
