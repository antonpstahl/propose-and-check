"""The Batch API transport (llm/batch.py): runs advance in waves to the same exits as synchronous calls, at half the
price; a stopped process resumes its open wave; failed requests go into the next wave, then escalate; an invalid
request raises; a rerun is answered from the cache. All in stub mode, on T's exact Facts."""

import json
import re
from types import SimpleNamespace

import pytest

from verifier_gate.data import dgp, labels
from verifier_gate.dsl.grammar import Claim
from verifier_gate.facts.build import build_facts
from verifier_gate.facts.reference import reference_steps
from verifier_gate.gate import gate as g
from verifier_gate.gate.template import template
from verifier_gate.llm import batch
from verifier_gate.llm.client import Client, stub_message
from verifier_gate.llm.extract import faithful_reading
from verifier_gate.verifier.certified import certified_plan

MODEL = "claude-haiku-5-5"


@pytest.fixture(scope="module")
def ctx():
    data = dgp.generate(dgp.Scenario("dominant", 5_000, 1))
    facts = build_facts(reference_steps(data.truth, data.X), data.X)
    return g.Context(facts, certified_plan(facts))


@pytest.fixture(scope="module")
def good(ctx):
    draft = template(ctx.facts, ctx.certified)
    sentences = [{"id": i, "text": t} for i, t in draft.sentences]
    claims = [{"sentence_id": c.sentence_id, "dsl": str(labels.external(Claim(c.kind, c.terms, c.value, c.relation, None, c.inner)))}
              for c in draft.claims]  # fmt: skip
    return {"sentences": sentences, "claims": claims}


@pytest.fixture(scope="module")
def wrong(good):
    """A first draft with one refuted sentence (income's share is about 10%, moderate): one repair round fixes it."""
    return {"sentences": good["sentences"] + [{"id": 99, "text": "Income has a strong effect."}],
            "claims": good["claims"] + [{"sentence_id": 99, "dsl": 'strength("income") == "strong"'}]}  # fmt: skip


def writer(good, wrong, fail=None):
    """Run "a" drafts well; run "b" drafts wrongly first and is right after the repair; the extractor reads each
    text faithfully. `fail` maps a run to what its writer requests get instead (an error type, or a list consumed
    one per submission)."""

    def respond(request):
        if request.role == "extractor":
            return stub_message(faithful_reading(request, [good, wrong]))
        run = "b" if "facts of b" in request.messages[0][1] else "a"
        if fail and run in fail:
            planned = fail[run]
            if not isinstance(planned, list):
                return planned
            if planned:
                return planned.pop(0)
        return stub_message(wrong if run == "b" and request.role == "proposer" else good)

    return respond


def jobs(ctx, folder=None):
    return {name: batch.Job(g.start(name, f"the facts of {name}", MODEL), ctx, folder / f"{name}.json" if folder else None)
            for name in ("a", "b")}  # fmt: skip


def waves(ctx, tmp_path, respond, **kw):
    client, api = Client("batch", cache_dir=tmp_path / "cache"), batch.StubBatchAPI(respond)
    runs = batch.run_waves(jobs(ctx, tmp_path / "runs"), client, api, poll=0, log=lambda *_: None, **kw)
    return runs, api, client


def test_waves_reach_the_exits_of_synchronous_calls_at_half_the_price(ctx, good, wrong, tmp_path):
    runs, api, _ = waves(ctx, tmp_path, writer(good, wrong))
    sync = Client("stub", writer(good, wrong), cache_dir=tmp_path / "sync")
    for name, run in runs.items():
        alone = g.run_sync(g.start(name, f"the facts of {name}", MODEL), sync, ctx)
        assert (run.exit, run.calls, run.rounds) == (alone.exit, alone.calls, alone.rounds)
        assert run.cost == pytest.approx(alone.cost / 2)
    assert runs["a"].exit == g.RELEASED and runs["b"].exit == g.RELEASED and runs["b"].rounds == 1
    assert runs["a"].roundtrip == runs["b"].roundtrip == "passed"
    # both first drafts; a's three extractions with b's repair. b's repaired text is a's text, so its extractions
    # are the same requests: answered from the cache, never sent twice
    assert [len(b["requests"]) for b in api.batches.values()] == [2, 4]
    assert json.loads((tmp_path / "runs" / "b.json").read_text())["exit"] == g.RELEASED


def test_every_answer_is_cached_and_logged_as_batched(ctx, good, wrong, tmp_path):
    _, _, client = waves(ctx, tmp_path, writer(good, wrong))
    log = [json.loads(line) for line in client.log_path.read_text().splitlines()]
    batched = [r for r in log if r["transport"] == "batch" and not r["cached"]]
    assert sum(r["cached"] for r in log) == 3  # b's extractions, answered from the cache
    assert len(batched) == 6 and all(r["request_id"].startswith("msgbatch_") and r["cost"] > 0 for r in batched)
    waves_on_disk = [json.loads(p.read_text()) for p in (tmp_path / "cache" / "batches").glob("*.json")]
    assert all(w["collected"] and not w["failed"] for w in waves_on_disk)
    assert all(isinstance(role, str) for w in waves_on_disk for role in w["requests"].values())  # bodies dropped


def test_a_rerun_is_answered_from_the_cache(ctx, good, wrong, tmp_path):
    first, _, client = waves(ctx, tmp_path, writer(good, wrong))
    api = batch.StubBatchAPI(lambda r: pytest.fail("no request may be sent"))
    again = batch.run_waves(jobs(ctx), client, api, poll=0, log=lambda *_: None)
    assert not api.batches and {n: r.exit for n, r in again.items()} == {n: r.exit for n, r in first.items()}
    assert all(r.cost == 0 for r in again.values())  # cached: nothing paid this time


def test_a_stopped_process_resumes_its_open_wave(ctx, good, tmp_path):
    respond = lambda r: stub_message(faithful_reading(r, [good]) if r.role == "extractor" else good)  # noqa: E731
    client, api = Client("batch", cache_dir=tmp_path / "cache"), batch.StubBatchAPI(respond, polls=3)
    started = jobs(ctx)
    batch.submit([j.run.request() for j in started.values()], tmp_path / "cache" / "batches", api, log=lambda *_: None)
    runs = batch.run_waves(jobs(ctx), client, api, poll=0, log=lambda *_: None)  # a new process, same runs
    assert all(r.exit == g.RELEASED for r in runs.values())
    assert [len(b["requests"]) for b in api.batches.values()] == [2, 3]  # the open wave collected, not sent again;
    # both texts are the same, so one set of extractions serves both runs


def test_a_failed_request_goes_into_the_next_wave(ctx, good, wrong, tmp_path):
    runs, api, _ = waves(ctx, tmp_path, writer(good, wrong, fail={"a": ["api_error", "expired"]}))
    assert runs["a"].exit == g.RELEASED and runs["a"].calls == 1 + 3  # answered on its third submission; its round trip
    assert sum(1 for b in api.batches.values() for r in b["requests"] if r.role == "proposer" and "facts of a" in r.messages[0][1]) == 3


def test_a_request_never_answered_ends_its_run_as_escalate(ctx, good, wrong, tmp_path):
    runs, api, _ = waves(ctx, tmp_path, writer(good, wrong, fail={"a": "overloaded_error"}))
    assert (runs["a"].exit, runs["a"].reason) == (g.ESCALATE, "api")
    assert runs["b"].exit == g.RELEASED
    assert sum(1 for b in api.batches.values() for r in b["requests"] if "facts of a" in r.messages[0][1]) == batch.MAX_SUBMISSIONS


def test_an_invalid_request_raises_after_the_other_answers_are_stored(ctx, good, wrong, tmp_path):
    client = Client("batch", cache_dir=tmp_path / "cache")
    api = batch.StubBatchAPI(writer(good, wrong, fail={"b": "invalid_request_error"}))
    started = jobs(ctx)
    with pytest.raises(RuntimeError, match="invalid request"):
        batch.run_waves(started, client, api, poll=0, log=lambda *_: None)
    assert client.lookup(started["a"].run.request()) is not None


def test_the_custom_id_is_the_cache_key_within_the_api_limit(ctx):
    for job in jobs(ctx).values():
        assert re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", job.run.request().key)


def test_a_batch_client_never_calls_the_api_itself(ctx, tmp_path):
    with pytest.raises(RuntimeError, match="cache only"):
        Client("batch", cache_dir=tmp_path).call(jobs(ctx)["a"].run.request())


def test_the_sdk_adapter_sends_the_request_params_and_reads_every_outcome(ctx):
    sent = {}
    items = [
        SimpleNamespace(custom_id="k1", result=SimpleNamespace(type="succeeded", message=SimpleNamespace(to_dict=lambda: {"id": "m"}))),
        SimpleNamespace(custom_id="k2", result=SimpleNamespace(type="errored", error=SimpleNamespace(error=SimpleNamespace(type="api_error")))),
        SimpleNamespace(custom_id="k3", result=SimpleNamespace(type="expired")),
    ]  # fmt: skip
    batches = SimpleNamespace(create=lambda requests: sent.setdefault("requests", requests) and SimpleNamespace(id="msgbatch_1"),
                              results=lambda batch_id: iter(items))  # fmt: skip
    api = batch.BatchAPI()
    api._sdk = SimpleNamespace(messages=SimpleNamespace(batches=batches))
    request = jobs(ctx)["a"].run.request()
    assert api.create([request]) == "msgbatch_1"
    assert sent["requests"] == [{"custom_id": request.key, "params": request.params()}]
    assert list(api.results("msgbatch_1")) == [batch.Result("k1", "succeeded", {"id": "m"}), batch.Result("k2", "errored", None, "api_error"),
                                               batch.Result("k3", "expired", None)]  # fmt: skip


def test_the_number_of_waves_is_bounded(ctx, good, wrong, tmp_path, monkeypatch):
    """A bug that never collects a wave must stop, not keep submitting paid batches."""
    monkeypatch.setattr(batch, "collect", lambda *a, **k: {})
    monkeypatch.setattr(batch, "MAX_WAVES", 4)
    api = batch.StubBatchAPI(writer(good, wrong))
    with pytest.raises(RuntimeError, match="waves"):
        batch.run_waves(jobs(ctx), Client("batch", cache_dir=tmp_path), api, poll=0, log=lambda *_: None)
    assert len(api.batches) == 4
