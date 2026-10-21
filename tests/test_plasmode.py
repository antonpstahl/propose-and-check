"""The plasmode tier (data/plasmode.py; plan §4.4), the tiers' common interface (data/tiers.py), and the frozen
synthetic label set. The plasmode tests need the TaiwanCredit file in data/raw/ (`uv run python -m
verifier_gate.data.plasmode` fetches it once); without it they are skipped."""

import hashlib
import json

import numpy as np
import pytest

from verifier_gate.data import dgp, plasmode, tiers
from verifier_gate.data.planted import planted_claims
from verifier_gate.facts.build import build_facts
from verifier_gate.facts.reference import reference_steps
from verifier_gate.lexicon import predicates as p
from verifier_gate.lexicon.predicates import FALSE, TRUE
from verifier_gate.models.fit_oracle import fit_oracle
from verifier_gate.verifier.verify import verify

FROZEN_LABELS = "6cebb0c637e707417f931c354bb3d60c1262112d5e74b974b7a86bcbddea321e"  # 3,042 claims, tag e1-frozen
needs_data = pytest.mark.skipif(not plasmode.XLS.exists(), reason="TaiwanCredit not fetched (data/raw/)")


def test_the_synthetic_label_set_is_still_the_frozen_one():
    v2 = p.load(p.VERSIONS["v2"])  # v3 adds the other sign of the planted step (D64)
    rows = [[s.id, str(c), label] for s in dgp.SCENARIOS for c, label in planted_claims(dgp.generate(s), v2)]
    assert len(rows) == 3042
    assert hashlib.sha256(json.dumps(rows).encode()).hexdigest() == FROZEN_LABELS


def test_tiers_are_found_from_a_scenario_a_sample_or_a_name():
    assert tiers.module(dgp.SCENARIOS[0]) is dgp and tiers.module(plasmode.SCENARIOS[0]) is plasmode
    assert tiers.module(plasmode.FEATURES) is plasmode and tiers.module("synthetic") is dgp
    assert tiers.scenario("pls-weak-n5000-s2") == plasmode.Scenario("weak", 5000, 2)
    assert len(tiers.SCENARIOS) == 36 and not any(s.is_discovery for s in plasmode.SCENARIOS)  # never calibrated on


@needs_data
def test_the_data_match_their_recorded_hash_and_drop_the_protected_attributes():
    assert plasmode._sha256(plasmode.XLS) == plasmode.XLS_SHA256
    data = plasmode.taiwan()
    assert data.shape == (30_000, 10) and "SEX" not in data and "MARRIAGE" not in data
    assert abs(data["default"].mean() - 0.221) < 0.001


@needs_data
def test_the_planted_shapes_have_their_roles():
    def at(feature, values):
        return plasmode.shape(feature)(np.asarray(values, dtype=float))

    grid = lambda f: np.quantile(plasmode.taiwan()[f], np.linspace(0.01, 0.99, 50))  # noqa: E731
    assert np.all(np.diff(at("LIMIT_BAL", grid("LIMIT_BAL"))) <= 1e-12)  # decreasing
    assert np.all(np.diff(at("PAY_AMT1", grid("PAY_AMT1"))) <= 1e-12)
    assert np.all(np.diff(at("BILL_AMT1", grid("BILL_AMT1"))) >= -1e-12)  # increasing
    assert np.all(np.diff(at("AGE", grid("AGE"))) >= -1e-12)
    pay = at("PAY_0", [-2, -1, 0, 1, 2, 8])
    assert pay[2] < pay[1] < pay[3] and pay[0] > pay[2] and np.all(np.diff(pay[2:]) >= 0)  # lowest at 0
    assert list(at("PAY_AMT2", [1999, 2000])) == [0.0, -1.0]
    assert not np.any(at("BILL_AMT2", grid("BILL_AMT2"))) and not np.any(at("PAY_AMT3", grid("PAY_AMT3")))


@needs_data
def test_datasets_share_rows_and_uniforms_like_the_synthetic_tier():
    small, large = plasmode.generate(plasmode.Scenario("none", 5000, 2)), plasmode.generate(plasmode.Scenario("none", 30000, 2))
    assert small.X.equals(large.X.iloc[:5000]) and np.array_equal(small.y, large.y[:5000])
    weak = plasmode.generate(plasmode.Scenario("weak", 5000, 2))
    assert weak.X.equals(small.X) and 0.9 < (weak.y == small.y).mean() < 1  # only the pairs differ
    again = plasmode.generate(plasmode.Scenario("none", 5000, 2))
    assert np.array_equal(again.y, small.y)


@needs_data
def test_shares_and_the_default_rate_are_on_target():
    d = plasmode.generate(plasmode.Scenario("none", 30000, 1))
    shares = d.truth.shares(d.X)
    for feature, target in plasmode.MAIN_SHARES.items():
        assert abs(shares[feature] - target) < 0.005, feature
    assert abs(d.y.mean() - plasmode.BASE_RATE) < 0.01
    assert plasmode.edge_report().near.sum() == 0  # no planted share within half a point of a class edge


@needs_data
@pytest.mark.parametrize("version", ("v2", "v3"))
@pytest.mark.parametrize("scenario", plasmode.SCENARIOS, ids=lambda s: s.id)
def test_scorer_test_lexicon_on_t_reproduces_every_planted_label(scenario, version):
    """Under v3 too (D63, D64): the direction margin keeps PAY_0's dip at codes -2/-1 a reversal, and the step at
    PAY_AMT2 = 2,000 is a drop."""
    lex = p.load(p.VERSIONS[version])
    data = plasmode.generate(scenario)
    facts = build_facts(reference_steps(data.truth, data.X), data.X)
    claims = planted_claims(data, lex)
    wrong = [(str(c), label, verify(c, facts, lex).value) for c, label in claims if verify(c, facts, lex).value != label]
    assert not wrong
    assert len(claims) == 168 + lex.signed_jumps and {label for _, label in claims} == {TRUE, FALSE}
    kinds = {"rank", "share", "direction", "strength", "negligible", "comparison", "threshold", "peak", "interaction"}
    assert {c.kind for c, _ in claims} == kinds | ({"drop"} if lex.signed_jumps else set())


@needs_data
def test_the_oracle_fits_the_plasmode_shapes():
    data = plasmode.generate(plasmode.Scenario("dominant", 5000, 1))
    oracle = fit_oracle(data.X, data.y, interaction="dominant")
    assert oracle.tier == "plasmode" and oracle.term_names == plasmode.TERMS
    steps = reference_steps(oracle, data.X)
    assert set(plasmode.FEATURES) <= set(steps.steps) and plasmode.AMPLIFICATION in steps.steps
    assert oracle.coef["BILL_AMT2"] == 0.0 and oracle.coef["PAY_AMT3"] == 0.0  # the oracle knows the nulls
