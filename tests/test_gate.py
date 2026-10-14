"""The gate (gate/gate.py): every exit state and every stop rule of §5.8, with scripted writer answers in stub mode,
on T's exact Facts so that every verdict is known."""

import json

import pytest

from verifier_gate.data import dgp, labels
from verifier_gate.dsl.grammar import Claim
from verifier_gate.facts.build import build_facts
from verifier_gate.facts.reference import reference_steps
from verifier_gate.gate import gate as g
from verifier_gate.gate.draft import Draft
from verifier_gate.gate.roundtrip import Coverage
from verifier_gate.gate.template import template
from verifier_gate.llm.client import Client, stub_message
from verifier_gate.verifier.certified import certified_plan


@pytest.fixture(scope="module")
def ctx():
    data = dgp.generate(dgp.Scenario("dominant", 5_000, 1))
    facts = build_facts(reference_steps(data.truth, data.X), data.X)
    return g.Context(facts, certified_plan(facts))


@pytest.fixture(scope="module")
def good(ctx):
    return template(ctx.facts, ctx.certified)


def answer(draft: Draft, extra: list[tuple[int, str, list[str]]] = (), replace: dict[int, list[str]] | None = None) -> dict:
    """A writer's JSON answer for a draft (in the writer's names), plus extra sentences and claim lines."""
    sentences = [{"id": i, "text": t} for i, t in draft.sentences]
    claims = [{"sentence_id": c.sentence_id, "dsl": str(labels.external(Claim(c.kind, c.terms, c.value, c.relation, None, c.inner)))}
              for c in draft.claims if not (replace and c.sentence_id in replace)]  # fmt: skip
    for sid, lines in (replace or {}).items():
        claims += [{"sentence_id": sid, "dsl": line} for line in lines]
    for sid, text, lines in extra:
        sentences.append({"id": sid, "text": text})
        claims += [{"sentence_id": sid, "dsl": line} for line in lines]
    return {"sentences": sentences, "claims": claims}


def scripted(*messages):
    requests = []

    def respond(request):
        requests.append(request)
        return messages[len(requests) - 1]

    return respond, requests


def run(ctx, tmp_path, *messages, budget=g.CALL_BUDGET):
    respond, requests = scripted(*messages)
    client = Client("stub", respond, cache_dir=tmp_path)
    result = g.run_sync(g.start("test", "the facts", "claude-haiku-5-5", budget=budget), client, ctx)
    return result, requests


WRONG = (99, "Income has a weak effect.", ['strength("income") == "weak"'])  # income is moderate in T


def test_a_correct_draft_is_released_at_once(ctx, good, tmp_path):
    result, requests = run(ctx, tmp_path, stub_message(answer(good)))
    assert (result.exit, result.calls, result.rounds) == (g.RELEASED, 1, 0)
    assert result.roundtrip == "not run (week 6)" and not result.flagged


def test_a_false_claim_is_repaired(ctx, good, tmp_path):
    result, requests = run(ctx, tmp_path, stub_message(answer(good, [WRONG])), stub_message(answer(good)))
    assert (result.exit, result.calls, result.rounds) == (g.RELEASED, 2, 1)
    repair = requests[1]
    assert repair.role == "repair 1" and [m[0] for m in repair.messages] == ["user", "assistant", "user"]
    assert 'Sentence 99: `strength("income") == "weak"` is false' in repair.messages[-1][1]


def test_no_progress_stops_repairing_and_drops_the_sentence(ctx, good, tmp_path):
    result, _ = run(ctx, tmp_path, stub_message(answer(good, [WRONG])), stub_message(answer(good, [WRONG])))
    assert (result.exit, result.calls, result.rounds) == (g.RELEASED_REDUCED, 2, 1)
    assert any("no progress" in e for e in result.events)
    final = result.versions[-1]
    assert 99 not in [s[0] for s in final["sentences"]]


def test_two_repair_rounds_at_most(ctx, good, tmp_path):
    wrong = [(99, "Income has a weak effect.", ['strength("income") == "weak"']),
             (99, "Income has a strong effect.", ['strength("income") == "strong"']),
             (99, "Dti has a strong effect.", ['strength("dti") == "strong"'])]  # fmt: skip
    result, _ = run(ctx, tmp_path, *(stub_message(answer(good, [w])) for w in wrong))
    assert (result.exit, result.calls, result.rounds) == (g.RELEASED_REDUCED, 3, 2)
    assert any("2 repair rounds used" in e for e in result.events)


def test_dropping_a_needed_sentence_falls_back_to_the_template(ctx, good, tmp_path):
    first = good.sentences[0][0]  # the sentence about the most important feature
    broken = answer(good, replace={first: ['direction("utilization") == "decreasing"']})
    result, _ = run(ctx, tmp_path, stub_message(broken), stub_message(broken))
    assert result.exit == g.TEMPLATE and result.versions[-1]["source"] == "template"


def test_a_broken_answer_gets_one_format_only_retry(ctx, good, tmp_path):
    result, requests = run(ctx, tmp_path, stub_message("not json"), stub_message(answer(good)))
    assert (result.exit, result.calls) == (g.RELEASED, 2)
    assert requests[1].attempt == 1 and requests[1].messages == requests[0].messages


def test_two_broken_answers_at_the_start_give_the_template(ctx, tmp_path):
    result, _ = run(ctx, tmp_path, stub_message("not json"), stub_message('{"x": 1', stop_reason="max_tokens"))
    assert result.exit == g.TEMPLATE


def test_dsl_lines_that_do_not_parse_get_a_format_only_retry(ctx, good, tmp_path):
    bad = answer(good, [(98, "Income matters.", ['strength("income") is "moderate"'])])
    fixed = answer(good, [(98, "Income matters.", ['strength("income") == "moderate"'])])
    result, requests = run(ctx, tmp_path, stub_message(bad), stub_message(fixed))
    assert (result.exit, result.calls, result.rounds) == (g.RELEASED, 2, 0)
    assert requests[1].role == "format retry" and "not valid DSL" in requests[1].messages[-1][1]


def test_an_api_failure_and_a_refusal_escalate(ctx, tmp_path):
    result, _ = run(ctx, tmp_path / "a", None)
    assert (result.exit, result.reason) == (g.ESCALATE, "api")
    refused = stub_message(None, stop_reason="refusal")
    refused["stop_details"] = {"category": "general_harms"}
    result, _ = run(ctx, tmp_path / "b", refused)
    assert (result.exit, result.reason) == (g.ESCALATE, "refusal (general_harms)")


def test_the_call_budget_stops_repairs(ctx, good, tmp_path):
    result, _ = run(ctx, tmp_path, stub_message(answer(good, [WRONG])), budget=1)
    assert (result.exit, result.calls) == (g.RELEASED_REDUCED, 1)
    assert any("call budget" in e for e in result.events)


def test_a_template_that_fails_escalates(ctx, tmp_path, monkeypatch):
    monkeypatch.setattr(g.templates, "template", lambda *a: Draft([(1, "Wrong.")], [Claim("strength", ("income",), "weak", sentence_id=1)], [], "template"))
    result, _ = run(ctx, tmp_path, stub_message("not json"), stub_message("not json"))
    assert result.exit == g.ESCALATE and "template" in result.reason


def test_unknown_terms_get_their_own_advice(ctx, good):
    version = g.check(Draft(good.sentences, good.claims + [Claim("strength", ("savings",), "weak", sentence_id=1)]), ctx)
    message = g.problems(version, ctx)
    assert "The model has no such term" in message and '`strength("savings") == "weak"` is undecidable' in message


def test_a_run_resumes_from_its_saved_state(ctx, good, tmp_path):
    respond, _ = scripted(stub_message(answer(good, [WRONG])), stub_message(answer(good)))
    client = Client("stub", respond, cache_dir=tmp_path / "cache")
    state = g.start("resume", "the facts", "claude-haiku-5-5")
    path = tmp_path / "run.json"
    while state.pending is not None:
        state = g.advance(state, client.call(state.request()), ctx)
        state.save(path)
        state = g.Run.load(path)  # as after an interruption
    assert (state.exit, state.calls) == (g.RELEASED, 2)
    assert json.loads(path.read_text())["exit"] == g.RELEASED


def test_a_term_covered_only_by_a_hedge_is_released_with_the_flag(ctx, good, tmp_path, monkeypatch):
    flagged = Coverage((frozenset({"utilization"}),), (), (frozenset({"utilization"}),))
    monkeypatch.setattr(g, "coverage", lambda *a: flagged)
    result, _ = run(ctx, tmp_path, stub_message(answer(good)))
    assert result.exit == g.RELEASED and result.flagged


def test_an_empty_draft_is_a_format_problem_not_a_repair_round(ctx, good, tmp_path):
    """Seen in the pilot: {"claims": [], "sentences": []}, valid JSON with nothing in it."""
    result, requests = run(ctx, tmp_path, stub_message({"claims": [], "sentences": []}), stub_message(answer(good)))
    assert (result.exit, result.calls, result.rounds) == (g.RELEASED, 2, 0)
    assert requests[1].attempt == 1 and any("format-only retry" in e for e in result.events)
