"""Jump and peak locations on count features (D42, lexicon v2): a location is judged against the gap between
neighbouring observed values, so two models that cut the same step at different places (EBM at 0.5, XGB2 at 1.0)
get the same verdict, and fine-grained features are judged as before."""

import numpy as np
import pandas as pd
import pytest

from verifier_gate.facts.build import Frame, build_facts, observed_values
from verifier_gate.facts.schema import Draws, FeatureFacts
from verifier_gate.facts.steps import StepModel, StepTerm, purify
from verifier_gate.lexicon import predicates as p
from verifier_gate.verifier.verify import verify

N = 4_000


def facts_for(X, name, cuts, scores, noise=0.02, refits=40):
    """Facts of a one-feature step model (plus a ramp to give the shares a scale), with noisy refits."""
    terms = [StepTerm((name,), (np.asarray(cuts, dtype=float),), np.asarray(scores, dtype=float)),
             StepTerm(("ramp",), (np.linspace(0.05, 0.95, 19),), np.linspace(0, 2, 20))]  # fmt: skip
    reference = purify(StepModel(0.0, {t.name: t for t in terms}), X, feature_order=(name, "ramp"))
    frame = Frame.of(reference, X)
    rng = np.random.default_rng(1)
    reads = []
    for _ in range(refits):
        noisy = {t.name: StepTerm(t.features, t.cuts, t.scores + rng.normal(0, noise, t.scores.shape)) for t in terms}
        reads.append(frame.read(purify(StepModel(0.0, noisy), X, feature_order=(name, "ramp")), X))
    return build_facts(reference, X, Draws.stack(reads))


@pytest.fixture(scope="module")
def X():
    rng = np.random.default_rng(0)
    return pd.DataFrame({"count": np.minimum(rng.poisson(0.8, N), 4).astype(float), "ramp": rng.uniform(0, 1, N)})


def test_observed_values_are_kept_for_counts_only(X):
    assert list(observed_values(X["count"])) == [0, 1, 2, 3, 4]
    assert observed_values(X["ramp"]) is None


@pytest.mark.parametrize("cuts", [[0.5, 1.5, 2.5, 3.5], [1.0, 2.0, 3.0, 4.0]], ids=["EBM-style", "XGB2-style"])
def test_a_count_step_is_located_the_same_for_any_cut_in_its_gap(X, cuts):
    """The step from 0 to 1 delinquency: "jumps at 1" and "jumps at 0.5" are both right; "at 3" is not."""
    facts = facts_for(X, "count", cuts, [0.0, 1.0, 1.0, 1.0, 1.0])
    assert facts.feature("count").values is not None
    for at in (1.0, 0.5):
        assert verify(f'threshold("count", at={at})', facts).value == p.TRUE, at
    assert verify('threshold("count", at=3.0)', facts).value == p.FALSE


def test_without_observed_values_the_window_decides_as_in_lexicon_v1(X):
    facts = facts_for(X, "count", [0.5, 1.5, 2.5, 3.5], [0.0, 1.0, 1.0, 1.0, 1.0])
    f = facts.feature("count")
    object.__setattr__(f, "values", None)  # as Facts built before D42
    assert verify('threshold("count", at=0.5)', facts).value == p.TRUE
    assert verify('threshold("count", at=1.0)', facts).value == p.FALSE  # the defect D42 fixes


@pytest.mark.parametrize("cuts", [[0.5, 1.5, 2.5, 3.5], [1.0, 2.0, 3.0, 4.0]], ids=["EBM-style", "XGB2-style"])
def test_a_count_peak_is_the_observed_value_it_holds(X, cuts):
    facts = facts_for(X, "count", cuts, [0.0, 0.4, 1.0, 0.4, 0.0])  # highest at 2
    assert verify('peak("count", at=2.0)', facts).value == p.TRUE
    assert verify('peak("count", at=3.0)', facts).value == p.FALSE


def test_the_gap_of_a_location():
    f = FeatureFacts("c", np.array([0.5]), np.zeros(2), np.ones(2) / 2, None, None, None, *([None] * 3), (0.0, 4.0), None,
                     np.array([0.0, 1.0, 2.0]))  # fmt: skip
    assert p._gap(f, 0.5) == (0.0, 1.0) and p._gap(f, 1.0) == (0.0, 1.0) and p._gap(f, 1.5) == (1.0, 2.0)
    object.__setattr__(f, "values", None)
    assert p._gap(f, 0.7) == (0.7, 0.7)
