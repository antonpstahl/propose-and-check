"""The certified plan (verifier/certified.py), the coverage check (gate/roundtrip.py) and E2's mutation operators
(experiments/e2_mutation.py), on T's Facts: exact, so every verdict is decided and the labels are the verdicts."""

import pytest

from verifier_gate.data import dgp
from verifier_gate.dsl.grammar import HEDGE, Claim
from verifier_gate.dsl.parse import parse
from verifier_gate.experiments import e2_mutation as e2
from verifier_gate.facts.build import build_facts
from verifier_gate.facts.reference import reference_steps
from verifier_gate.gate.roundtrip import coverage, required_terms, term_key
from verifier_gate.lexicon import predicates as p
from verifier_gate.lexicon.predicates import FALSE, TRUE, UNDECIDABLE
from verifier_gate.verifier.certified import certified_plan
from verifier_gate.verifier.verify import verify

LEX = p.load()


@pytest.fixture(scope="module")
def t_facts():
    data = dgp.generate(dgp.Scenario("dominant", 5_000, 1))
    return build_facts(reference_steps(data.truth, data.X), data.X)


@pytest.fixture(scope="module")
def plan(t_facts):
    return certified_plan(t_facts, LEX)


def test_the_certified_plan_is_true_parses_back_and_says_the_most_specific_thing(t_facts, plan):
    assert all(verify(c, t_facts, LEX).value == TRUE for c in plan)
    assert all(parse(str(c)) == c for c in plan)
    assert not any(isinstance(c.value, tuple) for c in plan)  # T is exact: every single value is decided
    assert not any(c.kind == HEDGE for c in plan)
    stated = {str(c) for c in plan}
    assert 'strength("utilization") == "strong"' in stated and 'direction("history_months") == "mostly_decreasing"' in stated
    assert 'interaction("utilization", "n_delinquencies", pattern="amplification")' in stated
    assert any(c.kind == "threshold" and c.terms == ("dti",) and abs(c.value - 0.43) < 0.02 for c in plan)
    assert any(c.kind == "peak" and c.terms == ("history_months",) for c in plan)


def test_coverage_needs_the_top_terms_and_dominant_pairs(t_facts, plan):
    required = required_terms(t_facts)
    assert term_key("utilization & n_delinquencies") in required  # dominant: a top-3 term
    assert coverage(plan, t_facts, plan).passed
    pair = term_key("utilization & n_delinquencies")
    dropped = [c for c in plan if pair not in e2.claim_terms(c)]
    assert coverage(dropped, t_facts, plan).missing == (pair,)


def test_a_hedge_covers_a_term_only_if_nothing_about_it_is_certified(t_facts, plan):
    inner = Claim("strength", ("utilization",), "weak")
    hedge = Claim(HEDGE, inner.terms, inner=inner)
    others = [c for c in plan if term_key("utilization") not in e2.claim_terms(c)]
    assert term_key("utilization") in coverage(others + [hedge], t_facts, plan).missing  # utilization is settled
    result = coverage(others + [hedge], t_facts, others)  # as if nothing about utilization were certified
    assert result.passed and result.hedged_only == (term_key("utilization"),) and result.flagged


def test_operators_on_one_claim_each(t_facts):
    f = "income"
    by = lambda claim: {(m.operator, str(m.claim)) for m in e2.mutants([claim], t_facts, LEX)}  # noqa: E731
    direction = by(Claim("direction", (f,), "decreasing"))
    assert ("M1", 'direction("income") == "increasing"') in direction
    assert ("M10", 'direction("income") == "mostly_decreasing"') in direction
    assert ("M9", 'direction("savings_balance") == "decreasing"') in direction
    assert ("M11", 'unsettled(direction("income") == "decreasing")') in direction
    strength = by(Claim("strength", (f,), "moderate"))
    assert {("M3", 'strength("income") == "strong"'), ("M4", 'strength("income") == "weak"'), ("M4", 'negligible("income")')} <= strength
    sets = by(Claim("strength", (f,), ("weak", "moderate")))
    assert {("M3", 'strength("income") in ("moderate", "strong")'), ("M4", 'strength("income") in ("negligible", "weak")')} <= sets
    ranks = by(Claim("rank", (f,), 1))
    assert {("M2", 'rank("income") == 2'), ("M2", 'rank("income") == 3')} <= ranks and not any("== 0" in m for _, m in ranks)
    flip = by(Claim("interaction", ("utilization", "n_delinquencies"), "amplification"))
    assert {("M8", 'interaction("utilization", "n_delinquencies", pattern="sign_flip")'),
            ("M8", 'interaction("utilization", "n_delinquencies", pattern="none")')} <= flip  # fmt: skip


def test_share_and_location_shifts_are_in_the_lexicon_s_units(t_facts):
    share = t_facts.feature("utilization").share.value
    out = e2.mutants([Claim("share", ("utilization",), round(share, 3))], t_facts, LEX)
    shifted = [m.claim.value for m in out if m.operator == "M5" and "tolerance" in m.variant]
    assert shifted == pytest.approx([share - 1.5 * e2.tolerance(share, LEX), share + 1.5 * e2.tolerance(share, LEX)], abs=1e-3)
    low, high = t_facts.feature("dti").low_high
    out = e2.mutants([Claim("threshold", ("dti",), 0.43)], t_facts, LEX)
    m6 = {m.variant: (m.claim.value, m.control) for m in out if m.operator == "M6"}
    assert m6["+2.0 w"][0] == pytest.approx(0.43 + 2 * LEX.window * (high - low), abs=1e-4)
    assert m6["+0.5 w"][1] and not m6["+2.0 w"][1]


def test_on_exact_facts_every_error_is_caught_and_no_control_is_blocked(t_facts, plan):
    """The scorer test of E2: on T, M's point estimate is the Facts themselves, so the labels are the verdicts.
    Errors are refuted (M9: undecidable, an unknown term); controls are certified; nothing is released wrong."""
    rows = []
    for m in e2.mutants(plan, t_facts, LEX):
        if m.claim is None:
            continue
        role = e2.label(m, t_facts, LEX)
        rows.append((m.operator, role, verify(m.claim, t_facts, LEX).value))
    assert rows
    for operator, role, verdict in rows:
        if role == "error":
            assert verdict == (UNDECIDABLE if operator == "M9" else FALSE), operator
        if role == "control":
            assert verdict == TRUE, operator
    assert {op for op, _, _ in rows} >= set(e2.OPERATORS)


def test_outcomes_use_d31_s_vocabulary():
    assert e2.outcome("error", TRUE) == "released wrong"
    assert e2.outcome("error", UNDECIDABLE) == "caught: undecidable"
    assert e2.outcome("control", FALSE) == "control blocked"
