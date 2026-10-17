"""Local facts for the spot check (facts/local.py) and the refit store (facts/refits.py), D49.

The step form of T stands in for a fitted model, so the tests run without fitting: it has main terms and the
planted pairs, as M has."""

from dataclasses import replace

import numpy as np
import pytest

from verifier_gate.data import dgp
from verifier_gate.facts import local, refits
from verifier_gate.facts.reference import reference_steps
from verifier_gate.facts.schema import Estimate
from verifier_gate.facts.steps import StepModel, StepTerm


@pytest.fixture(scope="module")
def data():
    return dgp.generate(dgp.Scenario("dominant", 5_000, 1))


@pytest.fixture(scope="module")
def M(data):
    return reference_steps(data.truth, data.X)


@pytest.fixture(scope="module")
def decision(M, data):
    return local.decide(M, data.X)


def shifted(model: StepModel, term: str, by: float) -> StepModel:
    """The model with one term's scores shifted by `by` on the upper half of its steps (a refit stand-in)."""
    steps = dict(model.steps)
    t = steps[term]
    scores = t.scores.copy()
    scores[scores.shape[0] // 2 :] += by
    steps[term] = StepTerm(t.features, t.cuts, scores)
    return StepModel(model.intercept, steps)


def test_the_decision_declines_the_riskiest_fifth_and_takes_the_closest_approved_as_reference(M, data, decision):
    logit = M.logit(data.X)
    assert abs(len(decision.declined) / len(logit) - local.DECLINE_SHARE) < 0.001
    assert len(decision.reference) == local.REFERENCE_SIZE
    assert np.all(logit[decision.reference] < decision.cutoff)
    approved = logit[logit < decision.cutoff]
    assert np.isclose(logit[decision.reference].min(), np.sort(approved)[-local.REFERENCE_SIZE])


def test_draws_are_declined_fixed_by_the_key_and_differ_between_keys(decision):
    a = local.draw_applicants(decision, (2, 0, 0))
    assert len(a) == local.APPLICANTS and set(a) <= set(decision.declined)
    assert np.array_equal(a, local.draw_applicants(decision, (2, 0, 0)))
    assert not np.array_equal(a, local.draw_applicants(decision, (2, 0, 1)))


def test_contributions_sum_to_the_score_gap_under_m_and_under_t(M, data, decision):
    rows = local.draw_applicants(decision, (1, 0, 0))
    facts = local.local_facts(M, None, data.truth, data.X, rows, decision)
    gap_m = M.logit(data.X.iloc[rows]) - M.logit(data.X.iloc[decision.reference]).mean()
    gap_t = data.truth.logit(data.X.iloc[rows]) - data.truth.logit(data.X.iloc[decision.reference]).mean()
    for f, gm, gt in zip(facts, gap_m, gap_t):
        assert np.isclose(sum(r.contribution.value for r in f.reasons), gm, atol=1e-10)
        assert np.isclose(f.gap.value, gm, atol=1e-10)
        assert np.isclose(sum(r.truth for r in f.reasons), gt, atol=1e-10)
        assert np.isclose(sum(r.fraction.value for r in f.reasons), 1.0)
        assert f.gap.value > 0  # declined against approved


def test_reasons_are_ordered_and_ranked_by_contribution(M, data, decision):
    rows = local.draw_applicants(decision, (1, 0, 0))
    for f in local.local_facts(M, None, data.truth, data.X, rows, decision):
        values = [r.contribution.value for r in f.reasons if r.rank is not None]
        assert values == sorted(values, reverse=True)
        assert f.reasons[0].rank.value == 1


def test_the_step_form_of_t_gives_t_its_own_reasons(M, data, decision):
    """M = T on the grid, so M's contributions are T's up to the grid (the dti step, about 0.05% of rows)."""
    rows = local.draw_applicants(decision, (1, 0, 0))
    for f in local.local_facts(M, None, data.truth, data.X, rows, decision):
        assert max(abs(r.contribution.value - r.truth) for r in f.reasons) < 0.05


def test_competition_rank_shares_ties():
    assert local.competition_rank(np.array([0.5, 0.0, 0.9, 0.0])).tolist() == [2, 3, 1, 3]
    assert local.competition_rank(np.array([[1.0, 2.0], [2.0, 1.0]])).tolist() == [[2, 1], [1, 2]]


def test_bands_come_from_the_refits_and_vanish_for_identical_refits(M, data, decision):
    rows = local.draw_applicants(decision, (1, 0, 0))
    same = local.local_facts(M, [M, M, M], data.truth, data.X, rows, decision)
    for f in same:
        for r in f.reasons:
            assert r.contribution.band == pytest.approx((r.contribution.value, r.contribution.value))
    refit = shifted(M, "utilization", 1.0)
    moved = local.local_facts(M, [M, refit], data.truth, data.X, rows, decision)
    # the refit moves x's contribution by its shift minus the reference's mean shift; two draws span 95% of it
    shift = refit.term("utilization", data.X) - M.term("utilization", data.X)
    expected = 0.95 * np.abs(shift[rows] - shift[decision.reference].mean())
    widths = [f.reason("utilization").contribution.band[1] - f.reason("utilization").contribution.band[0] for f in moved]
    assert widths == pytest.approx(expected)
    assert max(widths) > 0.1
    assert all(f.draws["contribution"].shape == (2, len(M.steps)) for f in moved)


def test_a_term_the_refit_lacks_counts_as_zero(M, data, decision):
    rows = local.draw_applicants(decision, (1, 0, 0))
    pair = M.pairs[0]
    lacking = StepModel(M.intercept, {n: t for n, t in M.steps.items() if n != pair})
    f = local.local_facts(M, [lacking, lacking], data.truth, data.X, rows, decision)[0]
    assert f.reason(pair).contribution.band == (0.0, 0.0)


def test_terms_only_t_has_are_listed_without_a_rank(data, decision):
    M = reference_steps(data.truth, data.X)
    without_pairs = StepModel(M.intercept, {n: M.steps[n] for n in M.features})
    f = local.local_facts(without_pairs, None, data.truth, data.X, local.draw_applicants(decision, (1, 0, 0)), decision)[0]
    only_t = [r for r in f.reasons if r.rank is None]
    assert {r.term for r in only_t} == set(dgp.PAIR_FACTORS)
    assert all(r.contribution.value == 0.0 for r in only_t)


def test_local_facts_survive_a_json_round_trip(M, data, decision):
    rows = local.draw_applicants(decision, (1, 0, 0))
    f = local.local_facts(M, [M, shifted(M, "income", 0.3)], data.truth, data.X, rows, decision, {"kind": "T-steps"})[0]
    back = local.LocalFacts.from_json(f.to_json())
    assert back.to_json() == f.to_json()
    assert np.array_equal(back.draws["contribution"], f.draws["contribution"])
    assert back.value("utilization").applicant == float(data.X["utilization"].iloc[f.model["row"]])


def test_refit_models_survive_the_store(M, data, tmp_path):
    models = [M, shifted(M, "dti", -0.2)]
    refits.save_models(models, tmp_path / "x_refits.npz")
    back = refits.load_models(tmp_path / "x_refits.npz")
    assert len(back) == 2
    for a, b in zip(models, back):
        assert a.term_names == b.term_names
        assert np.array_equal(a.logit(data.X), b.logit(data.X))


# --- local predicates (lexicon/local.py) ---------------------------------------------------------------------

from verifier_gate.lexicon import local as lp  # noqa: E402
from verifier_gate.lexicon.predicates import FALSE, TRUE, UNDECIDABLE, UNKNOWN_TERM  # noqa: E402


@pytest.fixture(scope="module")
def notices(M, data, decision):
    rows = local.draw_applicants(decision, (1, 0, 0))
    return local.local_facts(M, [M, M], data.truth, data.X, rows, decision)


def test_the_first_reason_is_rank_one_and_principal_when_material(notices):
    for f in notices:
        top = f.reasons[0]
        assert lp.reason_rank(f, top.term, 1).value == TRUE
        assert lp.reason_rank(f, top.term, 2).value == FALSE
        assert lp.reason_rank(f, top.term, (1, 2)).value == TRUE
        assert lp.principal_reason(f, top.term).value == (TRUE if top.fraction.value >= local.MATERIALITY else FALSE)


def test_a_term_for_the_applicant_is_no_reason_at_any_rank(notices):
    f = next(f for f in notices if any(r.contribution.value < 0 for r in f.reasons if r.rank is not None))
    favour = next(r for r in f.reasons if r.rank is not None and r.contribution.value < 0)
    assert lp.reason_rank(f, favour.term, int(favour.rank.value)).value == FALSE
    assert lp.principal_reason(f, favour.term).value == FALSE


def test_unknown_features_pairs_the_model_lacks_and_pair_order(notices):
    f = notices[0]
    assert lp.principal_reason(f, "savings_balance").code == UNKNOWN_TERM
    assert lp.reason_rank(f, "income & age", 1).value == FALSE  # known features, no such term
    pair = next(r.term for r in f.reasons if " & " in r.term)
    a, b = pair.split(" & ")
    swapped, own = lp.principal_reason(f, f"{b} & {a}"), lp.principal_reason(f, pair)
    assert swapped.value == own.value
    assert {k: v for k, v in swapped.evidence.items() if k != "term"} == {k: v for k, v in own.evidence.items() if k != "term"}


def test_wording_against_the_reference_is_two_valued_and_for_features_only(notices):
    f = notices[0]
    v = f.value("utilization")
    higher = lp.compared_to_reference(f, "utilization", higher=True).value
    lower = lp.compared_to_reference(f, "utilization", higher=False).value
    assert higher == (TRUE if v.applicant > v.reference_median else FALSE)
    assert {higher, lower} <= {TRUE, FALSE} and not (higher == lower == TRUE)
    assert lp.compared_to_reference(f, "utilization & n_delinquencies", True).value == UNDECIDABLE


def test_the_truth_view_judges_against_t_and_gives_no_principal_reason_without_a_positive_gap(notices):
    f = notices[0]
    t = lp.truth_view(f)
    assert t.gap.band is None and t.draws is None and not t.model["declined_by_m_only"]
    best = min(f.reasons, key=lambda r: r.truth_rank)
    assert lp.reason_rank(t, best.term, 1).value == TRUE
    negative = replace(f, truth_gap=-0.1)
    tn = lp.truth_view(negative)
    assert tn.model["declined_by_m_only"]
    assert all(lp.principal_reason(tn, r.term).value == FALSE for r in f.reasons)


def test_a_band_that_straddles_the_materiality_edge_is_undecidable(notices):
    f = notices[0]
    r = f.reasons[0]
    edge = replace(r, fraction=Estimate(local.MATERIALITY, (local.MATERIALITY / 2, 2 * local.MATERIALITY)))
    g = replace(f, reasons=(edge, *f.reasons[1:]))
    assert lp.principal_reason(g, r.term).value == UNDECIDABLE


# --- the gate on a notice (verifier/verify.py, verifier/certified.py, gate/roundtrip.py, gate/template.py) -------

from verifier_gate.dsl.grammar import Claim  # noqa: E402
from verifier_gate.facts.build import build_facts  # noqa: E402
from verifier_gate.gate import gate as g  # noqa: E402
from verifier_gate.gate import roundtrip as rt  # noqa: E402
from verifier_gate.gate.template import template  # noqa: E402
from verifier_gate.lexicon.predicates import NOT_APPLICABLE  # noqa: E402
from verifier_gate.verifier.certified import certified_local  # noqa: E402
from verifier_gate.verifier.verify import verify  # noqa: E402


@pytest.fixture(scope="module")
def global_facts(M, data):
    return build_facts(M, data.X)


@pytest.fixture(scope="module")
def notice(notices, global_facts):
    """A notice with at least two certified principal reasons, carrying the model's global Facts."""
    found = next(f for f in notices if len(rt.required_terms(f)) >= 2)
    return replace(found, model_facts=global_facts)


def test_local_claims_on_model_facts_and_global_claims_on_a_bare_notice_are_not_applicable(notices, global_facts):
    assert verify('principal_reason("utilization")', global_facts).code == NOT_APPLICABLE
    assert verify('rank("utilization") == 1', notices[0]).code == NOT_APPLICABLE


def test_a_global_claim_in_a_notice_is_verified_on_the_model_facts_it_carries(notice, global_facts):
    for line in ('rank("utilization") == 1', 'negligible("noise_1")', 'direction("income") == "decreasing"'):
        assert verify(line, notice).value == verify(line, global_facts).value


def test_the_hedge_works_on_local_claims(notice):
    top = notice.reasons[0].term
    assert verify(f'unsettled(principal_reason("{top}"))', notice).value == FALSE  # settled: the hedge is refuted


def test_everything_certified_about_a_notice_is_true(notice):
    plan = certified_local(notice)
    assert plan and all(verify(c, notice).value == TRUE for c in plan)
    assert {rt.term_key(c.terms[0]) for c in plan if c.kind == "principal_reason"} == set(rt.required_terms(notice))


def test_a_notice_is_covered_by_its_reasons_not_by_wording_alone(notice):
    required = rt.required_terms(notice)
    reasons = [Claim("principal_reason", (" & ".join(sorted(k)),)) for k in required]
    assert rt.coverage(reasons, notice, certified_local(notice)).passed
    wording = [Claim("higher_than_reference", (next(iter(k)),)) for k in required if len(k) == 1]
    assert set(rt.coverage(wording + reasons[1:], notice, certified_local(notice)).missing) == {required[0]}
    assert rt.emphasis([1], {1: {required[-1]}}, notice, None) == []


def test_the_notice_template_passes_the_plan_check(notice):
    ctx = g.Context(notice, certified_local(notice))
    draft = template(notice, ctx.certified)
    assert len(draft.sentences) == len(rt.required_terms(notice))
    assert g.check(draft, ctx).passed
    assert "principal reason" in draft.text


def test_local_prompt_hashes_are_frozen_after_the_pilot():
    from verifier_gate.llm import prompts

    frozen = prompts.frozen(prompts.FROZEN_LOCAL)
    if frozen is None:
        pytest.skip("local prompts not frozen yet (the local pilot freezes them)")
    assert prompts.hashes(prompts.LOCAL_NAMES) == frozen
