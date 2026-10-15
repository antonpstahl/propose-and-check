"""E3 (experiments/e3_end_to_end.py): the design, scoring readings apart from the gate's, the score of a text,
and a run end to end in stub mode."""

import pytest

from verifier_gate.dsl.parse import parse
from verifier_gate.experiments import e3_end_to_end as e3
from verifier_gate.gate import gate as g
from verifier_gate.llm import batch, extract
from verifier_gate.llm.client import Client
from verifier_gate.llm.extract import Extraction


def test_the_design_has_720_haiku_runs_and_72_sonnet_runs():
    assert len(e3.plan()) == 720 and len({s.run_id for s in e3.plan()}) == 720
    assert len(e3.plan(sonnet=True)) == 72 and {s.draw for s in e3.plan(sonnet=True)} == {0}
    assert len(e3.plan(dry=True)) == 16


@pytest.fixture(scope="module")
def setup():
    specs = e3.plan(dry=True)[:2]
    ctxs, texts = e3.contexts(specs)
    return specs, ctxs, texts


def test_scoring_readings_are_apart_from_the_gates(setup):
    specs, ctxs, _ = setup
    sentences = [[1, "Utilization is the most important driver."]]
    features = extract.features_text(ctxs[specs[0].run_id].facts)
    gate_keys = {extract.extractor_request(sentences, features, 0, k).key for k in range(extract.EXTRACTIONS)}
    scoring = e3.scoring_requests(sentences, ctxs[specs[0].run_id], 0)
    assert [r.replica for r in scoring] == list(e3.SCORING_REPLICAS) and not gate_keys & {r.key for r in scoring}


def test_a_text_is_scored_on_what_two_readings_find(setup):
    specs, ctxs, _ = setup
    ctx = ctxs[specs[0].run_id]
    sentences = [[1, "Income has a strong effect."], [2, "Utilization is the most important driver."]]
    false = parse('rank("income") == 9', sentence_id=1)
    true = parse('rank("utilization") == 1', sentence_id=2)
    readings = [Extraction([false, true]), Extraction([false, true]), Extraction([true])]
    truth = ctx.facts  # the score's T column is checked on M here; E3 passes T's Facts
    scored = e3.score(sentences, readings, ctx, truth)
    assert scored["scored"] and scored["claims"] == 2 and scored["false M"] == 1
    assert e3.score(sentences, readings[:1], ctx, truth) == {"scored": False, "readings": 1}


def test_runs_end_to_end_in_stub_mode(setup, tmp_path):
    specs, ctxs, texts = setup
    by_id = {s.run_id: s for s in specs}
    client, api = Client("batch", cache_dir=tmp_path), batch.StubBatchAPI(e3.stub_writer(ctxs))
    jobs = {rid: batch.Job(g.start(rid, f"RUN: {rid}\n{texts[rid]}", s.writer, s.draw), ctxs[rid]) for rid, s in by_id.items()}
    runs = batch.run_waves(jobs, client, api, poll=0, log=lambda *_: None)
    scores = e3.score_runs(runs, ctxs, by_id, client, api, 0, log=lambda *_: None)
    table = e3.pd.DataFrame([e3.row(by_id[rid], run, scores) for rid, run in runs.items()])
    assert table["off scored"].all() and table["on scored"].all() and (table.exit == g.RELEASED).all()
    summary = e3.summarise(table)
    assert summary["runs"].sum() == len(specs) and "E_U" in summary
