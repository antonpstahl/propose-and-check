"""Facts for the references (facts/reference.py) and the scorer test: the lexicon applied to T must reproduce
every planted label, on all 18 datasets (§6 E1, Maat lesson)."""

import numpy as np
import pytest

from verifier_gate.data import dgp
from verifier_gate.data.planted import planted_claims
from verifier_gate.facts import bootstrap
from verifier_gate.facts.build import Frame, build_facts
from verifier_gate.facts.reference import max_error, reference_steps
from verifier_gate.lexicon.predicates import FALSE, TRUE
from verifier_gate.models.fit_oracle import fit_oracle
from verifier_gate.verifier.verify import verify


@pytest.fixture(scope="module")
def dominant():
    return dgp.generate(dgp.Scenario("dominant", 5_000, 1))


def test_t_on_the_grid_is_the_smooth_t_up_to_the_dti_step(dominant):
    data = dominant
    steps = reference_steps(data.truth, data.X)
    fresh = dgp.sample_features(5_000, np.random.default_rng(11))
    for X in (data.X, fresh):
        away = np.abs(np.asarray(X["dti"]) - 0.43) > 0.002
        rows = X[away]
        assert max_error(data.truth, steps, rows) < 0.02
    shares, planted = steps.shares(data.X), data.truth.shares(data.X)
    assert max(abs(shares.get(t, 0.0) - planted[t]) for t in planted) < 1e-4


def test_zero_terms_are_left_out_and_features_keep_a_zero_term():
    data = dgp.generate(dgp.Scenario("none", 5_000, 1))
    steps = reference_steps(data.truth, data.X)
    assert steps.pairs == ()  # T has no pairs at level "none"
    assert steps.features == dgp.FEATURES
    assert not np.any(steps.term("noise_1", data.X))


def test_facts_of_t_read_steps_without_rows(dominant):
    """The even grid leaves steps without training rows in the tails; the frame reads them at their lower edge
    (a bug in Frame.read until 13 Oct, never hit by the fitted models)."""
    data = dominant
    steps = reference_steps(data.truth, data.X)
    facts = build_facts(steps, data.X)
    utilization = facts.feature("utilization")
    assert (utilization.mass == 0).any()
    np.testing.assert_array_equal(utilization.scores, steps.steps["utilization"].scores)
    assert np.array_equal(facts.steps().logit(data.X), steps.logit(data.X))


def test_oracle_refits_share_m_s_grid(dominant):
    data = dominant
    reference = bootstrap.fit_steps("oracle", data.X, data.y, seed=1)
    frame = Frame.of(reference, data.X)
    draws = bootstrap.refit_draws("oracle", data.X, data.y, 1, frame, refits=4)
    facts = build_facts(reference, data.X, draws)
    for f in facts.features:
        assert draws.curves[f.name].shape == (4, len(f.scores))
    assert facts.pair("utilization", "n_delinquencies") is not None
    oracle = fit_oracle(data.X, data.y, interaction="dominant")
    assert max_error(oracle, reference, data.X[np.abs(data.X["dti"] - 0.43) > 0.002]) < 0.02


@pytest.mark.parametrize("scenario", dgp.SCENARIOS, ids=lambda s: s.id)
def test_scorer_test_lexicon_on_t_reproduces_every_planted_label(scenario):
    data = dgp.generate(scenario)
    facts = build_facts(reference_steps(data.truth, data.X), data.X)
    claims = planted_claims(data)
    wrong = [(str(c), label, verify(c, facts).value) for c, label in claims if verify(c, facts).value != label]
    assert not wrong
    kinds = {c.kind for c, _ in claims}
    assert kinds == {"rank", "share", "direction", "strength", "negligible", "comparison", "threshold", "peak", "interaction"}
    assert {label for _, label in claims} == {TRUE, FALSE}
