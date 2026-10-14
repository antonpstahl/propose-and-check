"""The template (gate/template.py) and the writer's names (data/labels.py)."""

import pytest

from verifier_gate.data import dgp, labels
from verifier_gate.dsl.grammar import HEDGE, Claim
from verifier_gate.dsl.parse import parse
from verifier_gate.facts.build import build_facts
from verifier_gate.facts.reference import reference_steps
from verifier_gate.gate.roundtrip import coverage
from verifier_gate.gate.template import phrase, synthetic_label, template
from verifier_gate.lexicon.predicates import TRUE
from verifier_gate.verifier.certified import certified_plan
from verifier_gate.verifier.verify import verify

LABEL = synthetic_label()

PHRASES = {
    'strength("utilization") == "strong"': "credit utilization has a strong effect on default risk",
    'strength("dti") in ("weak", "moderate")': "the debt-to-income ratio has a weak to moderate effect on default risk",
    'strength("age") in ("negligible", "weak")': "age has at most a weak effect on default risk",
    'negligible("noise_1")': "months at the current address hardly matters for default risk",
    'rank("utilization") == 1': "credit utilization is the most important feature",
    'rank("income") == 3': "income is the third most important feature",
    'rank("income") in (1, 2, 3)': "income is among the 3 most important features",
    'rank("income") in (3, 4)': "income is the third to fourth most important feature",
    'share("utilization") == approx(0.279)': "credit utilization accounts for about 28% of the model's importance",
    'share("n_inquiries") == approx(0.039)': "the number of recent inquiries accounts for about 3.9% of the model's importance",
    'effect("income") > effect("dti")': "income matters more than the debt-to-income ratio",
    'direction("income") == "decreasing"': "default risk decreases with income",
    'direction("history_months") == "mostly_decreasing"': "default risk mostly decreases with the length of credit history",
    'direction("history_months") in ("decreasing", "mostly_decreasing")': "default risk generally decreases with the length of credit history",
    'threshold("dti", at=0.43)': "default risk jumps at the debt-to-income ratio = 0.43",
    'peak("history_months", at=36.0)': "default risk peaks at the length of credit history = 36",
    'interaction("utilization", "n_delinquencies", pattern="amplification")': "the effect of credit utilization grows with the number of past delinquencies",
    'interaction("n_inquiries", "history_months", pattern="sign_flip")': "the effect of the number of recent inquiries reverses its sign as the length of credit history changes",
    'interaction("utilization", "noise_2", pattern="none")': "credit utilization and the number of dependents do not interact",
    'unsettled(strength("n_inquiries") == "weak")': "the data do not settle whether the number of recent inquiries has a weak effect on default risk",
}


@pytest.mark.parametrize("line", PHRASES)
def test_every_claim_form_has_one_fixed_phrase(line):
    assert phrase(parse(line), LABEL) == PHRASES[line]


def test_the_writer_never_sees_the_noise_names_and_its_claims_map_back():
    assert labels.shown("noise_1") == "months_at_address" and labels.shown("utilization & noise_2") == "utilization & num_dependents"
    written = parse('unsettled(strength("months_at_address") == "weak")')
    assert labels.internal(written).inner.terms == ("noise_1",)
    claim = Claim("interaction", ("noise_1", "noise_2"), "none")
    assert labels.internal(labels.external(claim)) == claim


@pytest.fixture(scope="module")
def t_facts():
    data = dgp.generate(dgp.Scenario("dominant", 5_000, 1))
    return build_facts(reference_steps(data.truth, data.X), data.X)


def test_the_template_is_certified_and_covers_what_coverage_asks(t_facts):
    plan = certified_plan(t_facts)
    draft = template(t_facts, plan)
    assert draft.source == "template" and 5 <= len(draft.sentences) <= 20  # T certifies more than a model
    assert all(verify(c, t_facts).value == TRUE for c in draft.claims)
    assert {c.sentence_id for c in draft.claims} == set(draft.ids())  # every sentence carries claims
    assert coverage(draft.claims, t_facts, plan).passed
    assert "noise_1" not in draft.text and "noise" not in draft.text.lower()


def test_a_term_with_nothing_certified_gets_its_hedge(t_facts):
    inner = Claim("strength", ("utilization",), "weak")
    certified = [Claim(HEDGE, inner.terms, inner=inner)]
    draft = template(t_facts, certified)
    assert draft.claims == [Claim(HEDGE, ("utilization",), sentence_id=1, inner=inner)]
    assert draft.sentences[0][1].startswith("The data do not settle whether credit utilization")
