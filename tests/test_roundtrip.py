"""The round trip (gate/roundtrip.py, §5.7) and the repair advice (gate/advice.py): the comparison of a text's
extractions with its plan, emphasis, the gate's round-trip path, the advice that says why a claim failed, and the
no-progress rule's notion of the same problem. Stub mode, on T's exact Facts."""

import pytest

from verifier_gate.data import dgp, labels
from verifier_gate.dsl.grammar import Claim
from verifier_gate.dsl.parse import parse
from verifier_gate.facts.build import build_facts
from verifier_gate.facts.reference import reference_steps
from verifier_gate.gate import advice
from verifier_gate.gate import gate as g
from verifier_gate.gate import roundtrip as rt
from verifier_gate.gate.template import template
from verifier_gate.lexicon import predicates as p
from verifier_gate.lexicon.predicates import FALSE, TRUE, UNDECIDABLE, Verdict
from verifier_gate.llm.client import Client, stub_message
from verifier_gate.llm.extract import EXTRACTIONS, Extraction, faithful_reading
from verifier_gate.verifier.certified import certified_plan
from verifier_gate.verifier.verify import verify


@pytest.fixture(scope="module")
def ctx():
    data = dgp.generate(dgp.Scenario("dominant", 5_000, 1))
    facts = build_facts(reference_steps(data.truth, data.X), data.X)
    return g.Context(facts, certified_plan(facts))


@pytest.fixture(scope="module")
def draft(ctx):
    return template(ctx.facts, ctx.certified)


def answer(draft, extra=()) -> dict:
    sentences = [{"id": i, "text": t} for i, t in draft.sentences]
    claims = [{"sentence_id": c.sentence_id, "dsl": str(labels.external(Claim(c.kind, c.terms, c.value, c.relation, None, c.inner)))}
              for c in draft.claims]  # fmt: skip
    for sid, text, lines in extra:
        sentences.append({"id": sid, "text": text})
        claims += [{"sentence_id": sid, "dsl": line} for line in lines]
    return {"sentences": sentences, "claims": claims}


def reading(claims, unexpressed=None) -> Extraction:
    return Extraction([parse(line, sentence_id=sid) for sid, line in claims], unexpressed or {})


# --- the comparison ---------------------------------------------------------------------------------------


def test_claims_are_compared_with_pairs_in_a_fixed_order_and_interactions_in_theirs():
    assert rt.canonical(parse('share("b & a") == approx(0.1)')) == rt.canonical(parse('share("a & b") == approx(0.1)'))
    assert rt.canonical(parse('unsettled(negligible("b & a"))')) == 'unsettled(negligible("a & b"))'
    one, other = (parse(f'interaction("{x}", "{y}", pattern="amplification")') for x, y in (("a", "b"), ("b", "a")))
    assert rt.canonical(one) != rt.canonical(other)


def test_a_faithful_reading_passes_and_finds_the_plan(ctx, draft):
    plan = draft.claims
    lines = [(c.sentence_id, str(c)) for c in plan]
    trip = rt.compare([reading(lines)] * EXTRACTIONS, plan, draft.ids(), ctx.facts)
    assert trip.passed and not trip.unplanned and not trip.plan_only and not trip.ambiguous
    assert len(trip.extracted) == len({rt.canonical(c) for c in plan})


def test_a_statement_beyond_the_plan_fails_if_two_readings_find_it_and_is_flagged_if_one(ctx, draft):
    lines = [(c.sentence_id, str(c)) for c in draft.claims]
    extra = (2, 'strength("income") == "strong"')
    assert verify(extra[1], ctx.facts).value != TRUE
    twice = rt.compare([reading(lines + [extra]), reading(lines + [extra]), reading(lines)], draft.claims, draft.ids(), ctx.facts)
    assert not twice.passed and twice.failing_sentences() == {2} and twice.failures() == [extra[1]]
    once = rt.compare([reading(lines + [extra]), reading(lines), reading(lines)], draft.claims, draft.ids(), ctx.facts)
    assert once.passed and once.ambiguous == [[2, extra[1]]]


def test_a_true_statement_beyond_the_plan_passes(ctx, draft):
    lines = [(c.sentence_id, str(c)) for c in draft.claims]
    extra = (1, next(str(c) for c in ctx.certified if c.kind == "direction"))
    trip = rt.compare([reading(lines + [extra])] * 3, [c for c in draft.claims if str(c) != extra[1]], draft.ids(), ctx.facts)
    assert trip.passed


def test_a_plan_claim_the_text_does_not_state_is_flagged(ctx, draft):
    lines = [(c.sentence_id, str(c)) for c in draft.claims]
    dropped = next(line for line in lines if parse(line[1]).kind == "negligible")  # not needed for coverage
    rest = [line for line in lines if line != dropped]
    trip = rt.compare([reading(rest)] * 3, draft.claims, draft.ids(), ctx.facts, ctx.certified)
    assert trip.passed and [dropped[0], rt.canonical(parse(dropped[1]))] in trip.plan_only


def test_content_no_dsl_form_expresses_is_flagged_and_fails_only_with_a_number(ctx, draft):
    """D44 (b) as revised after the round-trip pilot: a number no claim can check is not released as stated; other
    content without a DSL form (an intensity word, a paraphrase) is the expressivity gap, flagged and counted."""
    lines = [(c.sentence_id, str(c)) for c in draft.claims]
    sid = draft.ids()[1]
    words = {sid: ["risk rises steeply"]}
    flagged = rt.compare([reading(lines, words), reading(lines, words), reading(lines)], draft.claims, draft.ids(), ctx.facts, ctx.certified)
    assert flagged.passed and flagged.gap == [[sid, ["risk rises steeply"]]] and not flagged.numbers
    number = {sid: ["the largest drop above about $84,000"]}
    blocked = rt.compare([reading(lines, number), reading(lines, number), reading(lines)], draft.claims, draft.ids(), ctx.facts, ctx.certified)
    assert not blocked.passed and blocked.numbers == [[sid, ["the largest drop above about $84,000"]]] and blocked.failing_sentences() == {sid}
    once = rt.compare([reading(lines, number), reading(lines), reading(lines)], draft.claims, draft.ids(), ctx.facts, ctx.certified)
    assert once.passed


def test_coverage_counts_only_what_the_text_states(ctx, draft):
    """D44 (a): a top term covered only by plan claims the extractor does not find in the text is not covered."""
    top = sorted(rt.required_terms(ctx.facts), key=len)[0]
    lines = [(c.sentence_id, str(c)) for c in draft.claims]
    unstated = [line for line in lines if top & set().union(*rt.claim_terms(parse(line[1])))]
    rest = [line for line in lines if line not in unstated]
    trip = rt.compare([reading(rest)] * 3, draft.claims, draft.ids(), ctx.facts, ctx.certified)
    assert " & ".join(sorted(top)) in trip.missing and not trip.passed and not trip.failing_sentences()


def test_an_opening_sentence_that_leads_with_a_minor_term_fails_emphasis(ctx):
    plan = [parse('negligible("noise_1")', sentence_id=1), parse('rank("utilization") == 1', sentence_id=2)]
    lines = [(c.sentence_id, str(c)) for c in plan]
    trip = rt.compare([reading(lines)] * 3, plan, [1, 2], ctx.facts)
    assert trip.emphasis and trip.emphasis[0][0] == 1 and "noise_1" in trip.emphasis[0][1] and "utilization" in trip.emphasis[0][2]
    assert not rt.compare([reading(lines)] * 3, plan, [1, 2], ctx.facts, check_emphasis=False).emphasis
    both = [parse('rank("utilization") == 1', sentence_id=1), parse('negligible("noise_1")', sentence_id=1)]
    assert not rt.compare([reading([(1, str(c)) for c in both])] * 3, both, [1], ctx.facts).emphasis


# --- unknown terms (M5 of the 20 Oct review) --------------------------------------------------------------


def test_a_feature_name_the_model_lacks_is_compared_in_its_normal_form_or_as_the_feature_it_spells():
    features = {"income", "utilization", "PAY_0"}
    assert rt.normal_name(" The savings-balance ") == rt.normal_name("savings _balance") == "savings_balance"
    assert str(rt.normalised(parse('direction("Income") == "increasing"'), features)) == 'direction("income") == "increasing"'
    assert str(rt.normalised(parse('negligible("pay 0")'), features)) == 'negligible("PAY_0")'
    hedge = parse('unsettled(negligible("Utilization & the Savings Balance"))')
    assert str(rt.normalised(hedge, features)) == 'unsettled(negligible("utilization & savings_balance"))'
    assert rt.unknown(rt.normalised(hedge, features), features) and not rt.unknown(parse('rank("income") == 1'), features)


def test_a_claim_on_a_feature_the_model_lacks_fails_if_one_reading_finds_it(ctx, draft):
    lines = [(c.sentence_id, str(c)) for c in draft.claims]
    invented = (2, 'direction("the savings balance") == "decreasing"')
    readings = [reading(lines + [invented]), reading(lines), reading(lines)]
    trip = rt.compare(readings, draft.claims, draft.ids(), ctx.facts)
    line = 'direction("savings_balance") == "decreasing"'
    assert trip.failures() == [line] and trip.failing_sentences() == {2} and not trip.ambiguous
    assert trip.unplanned[0][:4] == [2, line, UNDECIDABLE, p.UNKNOWN_TERM]
    message = g.text_problems(trip, ctx)
    assert f"Sentence 2 says more than its claims: a reader takes it to state `{line}`" in message and "no such term" in message
    as_run = rt.compare(readings, draft.claims, draft.ids(), ctx.facts, unknown_terms=False)
    assert as_run.passed and as_run.ambiguous == [[2, invented[1]]]


def test_readings_that_spell_a_feature_name_differently_agree_on_it(ctx, draft):
    lines = [(c.sentence_id, str(c)) for c in draft.claims]
    spelled = [(2, 'direction("Savings Balance") == "decreasing"'), (2, 'direction("savings-balance") == "decreasing"')]
    trip = rt.compare([reading(lines + [spelled[0]]), reading(lines + [spelled[1]]), reading(lines)], draft.claims, draft.ids(), ctx.facts)
    assert [2, 'direction("savings_balance") == "decreasing"', 2] in trip.extracted and not trip.passed
    true = next(c for c in ctx.certified if c.kind == "direction")
    shouted = (1, str(true).replace(f'"{true.terms[0]}"', f'"{true.terms[0].upper()}"'))
    assert rt.compare([reading(lines + [shouted])] * EXTRACTIONS, draft.claims, draft.ids(), ctx.facts).passed
    assert not rt.compare([reading(lines + [shouted])] * EXTRACTIONS, draft.claims, draft.ids(), ctx.facts, unknown_terms=False).passed


# --- the gate's round trip --------------------------------------------------------------------------------


def writer(draft, first_extra=(), faithful=True):
    """The writer answers with the draft (plus `first_extra` in its first answer); the extractor reads the text as
    the writer's claims, and also reads sentence 99, if there, as a strong effect of income (not in its claims)."""
    answers = []

    def respond(request):
        if request.role == "extractor":
            data = faithful_reading(request, answers)
            if not faithful:
                for s in data["sentences"]:
                    if s["id"] == 99:
                        s["claims"].append('strength("income") == "strong"')
            return stub_message(data)
        out = answer(draft, first_extra if not answers else ())
        answers.append(out)
        return stub_message(out)

    return respond


def run(ctx, tmp_path, respond, budget=g.CALL_BUDGET):
    client = Client("stub", respond, cache_dir=tmp_path)
    return g.run_sync(g.start("rt", "the facts", "claude-haiku-5-5", budget=budget), client, ctx)


def test_a_faithful_text_is_released_after_its_round_trip(ctx, draft, tmp_path):
    result = run(ctx, tmp_path, writer(draft))
    assert (result.exit, result.calls, result.roundtrip) == (g.RELEASED, 1 + EXTRACTIONS, "passed")
    assert result.versions[-1]["roundtrip"]["readings"] == EXTRACTIONS


def test_a_sentence_that_says_more_than_its_claims_is_repaired(ctx, draft, tmp_path):
    extra = [(99, "Income has a strong effect.", ['direction("income") == "decreasing"'])]
    result = run(ctx, tmp_path, writer(draft, extra, faithful=False))
    assert result.exit == g.RELEASED and result.rounds == 1 and result.calls == 2 * (1 + EXTRACTIONS)
    failed = result.versions[0]["roundtrip"]
    assert failed["unplanned"][0][:3] == [99, 'strength("income") == "strong"', FALSE]
    assert any("problem(s) in the text" in e for e in result.events)


def test_the_repair_message_for_a_text_names_the_sentence_and_asks_to_change_it(ctx, draft):
    trip = rt.RoundTrip(3, unplanned=[[99, 'strength("income") == "strong"', FALSE, "", "", "share 0.1"]],
                        gap=[[4, ["above about $84,000"]], [5, ["risk rises steeply"]]], numbers=[[4, ["above about $84,000"]]],
                        missing=["noise_1"])  # fmt: skip
    message = g.text_problems(trip, ctx)
    assert "Sentence 99 says more than its claims" in message and "Change the sentence itself" in message
    assert 'Sentence 4 states a number that no claim form can check' in message and "steeply" not in message
    assert "`months_at_address`" in message and "not in the sentences" in message  # in the writer's names


def test_a_failure_in_no_single_sentence_ends_in_the_template_when_repairs_end(ctx, draft, tmp_path):
    """A top term the text never states cannot be fixed by dropping sentences."""
    top = sorted(rt.required_terms(ctx.facts), key=len)[0]
    answers = []

    def respond(request):
        if request.role == "extractor":
            data = faithful_reading(request, answers)
            for sentence in data["sentences"]:
                sentence["claims"] = [line for line in sentence["claims"] if not top & set().union(*rt.claim_terms(labels.internal(parse(line))))]
            return stub_message(data)
        answers.append(answer(draft))
        return stub_message(answers[-1])

    result = run(ctx, tmp_path, respond)
    assert result.exit == g.TEMPLATE and any("no progress" in e for e in result.events) and any("nothing to drop" in e for e in result.events)


def test_an_answer_that_leaves_out_sentences_is_retried_once(ctx, draft, tmp_path):
    """Seen in the round-trip pilot: valid JSON with one empty entry, about 8% of the extractor's answers."""
    answers = []

    def respond(request):
        if request.role == "extractor":
            if request.replica == 0 and request.attempt == 0:
                return stub_message({"sentences": [{"id": 1, "claims": [], "unexpressed": []}]})
            return stub_message(faithful_reading(request, answers))
        answers.append(answer(draft))
        return stub_message(answers[-1])

    result = run(ctx, tmp_path, respond)
    assert result.exit == g.RELEASED and result.calls == 1 + EXTRACTIONS + 1
    assert any("extraction retry: 1" in e for e in result.events) and result.versions[-1]["roundtrip"]["readings"] == EXTRACTIONS


def test_too_few_readable_extractions_end_in_the_template(ctx, draft, tmp_path):
    def respond(request):
        return stub_message("not json") if request.role == "extractor" else stub_message(answer(draft))

    result = run(ctx, tmp_path, respond)
    assert result.exit == g.TEMPLATE and any("round trip could not run" in e for e in result.events)


def test_without_calls_left_for_the_round_trip_the_text_is_not_released(ctx, draft, tmp_path):
    result = run(ctx, tmp_path, writer(draft), budget=2)
    assert result.exit == g.TEMPLATE and any("no calls left" in e for e in result.events)


def test_an_extractor_api_failure_escalates(ctx, draft, tmp_path):
    def respond(request):
        return None if request.role == "extractor" else stub_message(answer(draft))

    client = Client("stub", respond, cache_dir=tmp_path)
    client._send = lambda r: None
    result = g.run_sync(g.start("rt", "the facts", "claude-haiku-5-5"), client, ctx)
    assert (result.exit, result.reason) == (g.ESCALATE, "api") and not result.requests()


# --- the advice and the same problem ----------------------------------------------------------------------


def test_the_strength_advice_names_the_classes_the_band_spans():
    verdict = Verdict(UNDECIDABLE, {"share": 0.163, "share band": (0.109, 0.188), "detectable": True})
    text = advice.explain(parse('strength("income") == "moderate"'), verdict)
    assert "16.3% (95% band 10.9% to 18.8%)" in text and "moderate (5% to 15%) and strong (15% or more)" in text


def test_a_jump_on_a_curve_without_one_is_one_problem_whatever_its_location():
    no_jump = {"largest jump at": 0.735, "location band": (0.67, 0.83), "jump significant": False, "jump / range band": (0.16, 0.37)}
    keys = {advice.problem_key(parse(line), Verdict(FALSE, no_jump))
            for line in ('threshold("utilization", at=0.719)', 'threshold("utilization", at=0.735)', 'unsettled(threshold("utilization", at=0.72))')}  # fmt: skip
    assert keys == {"no jump in utilization"}
    assert "No location makes" in advice.explain(parse('threshold("utilization", at=0.72)'), Verdict(FALSE, no_jump))
    elsewhere = no_jump | {"jump significant": True, "jump / range band": (0.6, 0.8)}
    assert advice.problem_key(parse('threshold("utilization", at=0.5)'), Verdict(FALSE, elsewhere)) == 'threshold("utilization", at=0.5)'
    assert "Name a location in that band" in advice.explain(parse('threshold("utilization", at=0.5)'), Verdict(FALSE, elsewhere))


def test_a_hedge_on_a_settled_claim_is_told_to_state_it():
    verdict = Verdict(FALSE, {"claim verdict": "true"}, "the claim is settled: it is true")
    assert "State it instead of hedging it" in advice.explain(parse('unsettled(negligible("age"))'), verdict)


def test_the_location_loop_stops_after_one_repair(ctx, draft, tmp_path):
    """The pilot's case (none, XGB2, H1): a jump the curve does not have, its location nudged in the repair."""
    feature = next(f.name for f in ctx.facts.features
                   if advice.impossible("threshold", verify(f'threshold("{f.name}", at=0)', ctx.facts).evidence, p.load()))  # fmt: skip
    nudges, answers = iter([0.7, 0.71, 0.72]), []

    def respond(request):
        if request.role == "extractor":
            return stub_message(faithful_reading(request, answers))
        answers.append(answer(draft, [(99, "Risk jumps there.", [f'threshold("{labels.shown(feature)}", at={next(nudges)})'])]))
        return stub_message(answers[-1])

    result = run(ctx, tmp_path, respond)
    assert result.rounds == 1 and any("no progress: no jump in" in e for e in result.events)
    assert result.exit == g.RELEASED_REDUCED and result.roundtrip == "passed"  # sentence 99 dropped, the rest read back
