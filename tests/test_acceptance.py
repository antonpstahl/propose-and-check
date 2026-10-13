from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
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


def test_failures_are_labelled_data_or_model_misses_against_the_oracle(dominant):
    """D10: the oracle misses the peak (data miss); the model misses the peak and the step (step: model miss)."""
    truth = dominant.truth

    def edited(*claims):
        return Edited(truth.interaction, truth.intercept, truth.offsets, {BROKEN[c][0]: BROKEN[c][1] for c in claims})

    models = {"T": truth, "oracle": edited("peak"), "EBM": edited("peak", "step")}
    checks = pd.concat(
        [acceptance.frame(acceptance.check_terms(m, dominant), scenario="s", model=k) for k, m in models.items()],
        ignore_index=True,
    )
    checks["miss"] = acceptance.attribute(checks, checks[checks.model == "oracle"])
    miss = checks.set_index(["model", "claim", "term"]).miss
    assert miss["EBM", "peak", "history_months"] == "data"
    assert miss["EBM", "step", "dti"] == "model"
    assert miss["oracle", "peak", "history_months"] == "data"
    assert (checks.miss[checks.passed] == "").all() and (checks.miss[~checks.passed] != "").all()
    verdicts = acceptance.verdicts(checks)
    assert verdicts.accepted.to_dict() == {"T": True, "oracle": True, "EBM": False}
    assert verdicts.loc["EBM", "data_misses"] >= 1 and verdicts.loc["EBM", "model_misses"] >= 1


def test_a_spurious_pair_the_oracle_lacks_is_a_model_miss():
    row = {"scenario": "s", "planted": 0.0}
    checks = pd.DataFrame(
        [
            {**row, "model": "oracle", "claim": "auc", "term": "", "fitted": 0.76, "passed": True},
            {**row, "model": "EBM", "claim": "auc", "term": None, "fitted": 0.76, "passed": True},  # "" read from CSV
            {**row, "model": "EBM", "claim": "noise", "term": "income & dti", "fitted": 0.03, "passed": False},
        ]
    )
    assert acceptance.attribute(checks, checks[checks.model == "oracle"]).tolist() == ["", "", "model"]
    unmatched = checks.assign(claim="strength")
    with pytest.raises(ValueError, match="no oracle check"):
        acceptance.attribute(unmatched, checks[checks.model == "oracle"])


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


def test_xgb2_gets_every_check_through_its_decomposition():
    """D26: the same checks as the EBM, on XGB2's exact terms; its pair effects agree with the partial-dependence
    cross-check up to the averaging of its other pairs over the rows (purified on the data, so close to zero)."""
    from verifier_gate.facts.xgb2 import purify_xgb2
    from verifier_gate.models.fit_xgb2 import fit_xgb2

    data = dgp.generate(dgp.Scenario("dominant", 5_000, 1))
    model = fit_xgb2(data.X, data.y, seed=1)
    by_terms = acceptance.check_terms(purify_xgb2(model, data.X), data)
    assert {"strength", "noise", "rank", "direction", "peak", "step", "amplification", "sign_flip", "auc"} <= {c.claim for c in by_terms}
    margin = lambda Z: model.predict(Z, output_margin=True)  # noqa: E731
    by_margin = {c.claim: c for c in acceptance.check_margin(margin, data)}
    for check in by_terms:
        if check.claim in ("amplification", "sign_flip"):
            np.testing.assert_allclose(check.fitted, by_margin[check.claim].fitted, atol=0.05)
        if check.claim == "auc":
            assert check.fitted == pytest.approx(by_margin["auc"].fitted, abs=1e-4)
