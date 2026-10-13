from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

import numpy as np
import pytest
from scipy.special import expit

from verifier_gate.data import dgp
from verifier_gate.experiments import acceptance


@dataclass(frozen=True)
class Edited(dgp.Truth):
    """T with some terms replaced, to break one planted claim at a time."""

    replaced: Mapping[str, Callable] = field(default_factory=dict)

    def term(self, name, X):
        return self.replaced[name](X) if name in self.replaced else super().term(name, X)


@pytest.fixture(scope="module")
def dominant():
    return dgp.generate(dgp.Scenario("dominant", 50_000, 1))


@pytest.mark.parametrize("scenario", dgp.SCENARIOS, ids=lambda s: s.id)
def test_truth_passes_every_check(scenario):
    data = dgp.generate(scenario)
    checks = acceptance.check_terms(data.truth, data)
    assert all(c.passed for c in checks), [c for c in checks if not c.passed]
    claims = {c.claim for c in checks}
    assert {"strength", "noise", "rank", "direction", "peak", "step", "auc"} <= claims
    assert ({"amplification", "sign_flip"} <= claims) == (scenario.interaction != "none")


def _zeros(feature):
    return lambda X: np.zeros(len(X[feature]))


BROKEN = {
    "peak": ("history_months", lambda X: -0.7 * (np.asarray(X["history_months"]) - 183.0) / 177.0),
    "step": ("dti", lambda X: 0.35 * (np.asarray(X["dti"]) >= 0.46) - 0.1),
    "direction": ("income", lambda X: np.log(np.asarray(X["income"]) / 50_000.0)),
    "rank": ("income", lambda X: -0.2 * np.log(np.asarray(X["income"]) / 50_000.0)),
    "noise": ("noise_1", lambda X: 0.2 * np.asarray(X["noise_1"])),
    "amplification": (dgp.AMPLIFICATION, _zeros("utilization")),
    "sign_flip": (dgp.SIGN_FLIP, _zeros("n_inquiries")),
    "auc": ("utilization", _zeros("utilization")),
}


@pytest.mark.parametrize("claim", list(BROKEN))
def test_each_check_fails_when_its_claim_is_broken(dominant, claim):
    term, replacement = BROKEN[claim]
    truth = dominant.truth
    model = Edited(truth.interaction, truth.intercept, truth.offsets, {term: replacement})
    failed = {(c.claim, c.term) for c in acceptance.check_terms(model, dominant) if not c.passed}
    assert (claim, "" if claim == "auc" else term) in failed


def test_margin_checks_agree_with_term_checks_on_truth(dominant):
    by_terms = {c.claim: c for c in acceptance.check_terms(dominant.truth, dominant)}
    for check in acceptance.check_margin(dominant.truth.logit, dominant):
        assert check.passed
        np.testing.assert_allclose(check.fitted, by_terms[check.claim].fitted, atol=1e-9)


def test_oracle_reproduces_the_planted_coefficients_on_a_large_sample():
    rng = np.random.default_rng(7)
    X = dgp.sample_features(400_000, rng)
    truth = dgp.make_truth(X, "dominant")
    y = (rng.uniform(size=len(X)) < expit(truth.logit(X))).astype(int)
    data = dgp.Dataset(dgp.Scenario("dominant", len(X), 7), X, y, truth)
    oracle = acceptance.fit_oracle(data)
    planted = dgp.coefficients("dominant")
    for term in ("utilization", "n_delinquencies", "income", dgp.AMPLIFICATION, dgp.SIGN_FLIP):
        assert oracle.coef[term] == pytest.approx(planted[term], rel=0.1)
    np.testing.assert_allclose(oracle.logit(X).mean(), truth.logit(X).mean(), atol=0.05)
