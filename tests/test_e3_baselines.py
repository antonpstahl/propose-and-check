"""E3's baselines (experiments/e3_baselines.py): the cells, the plain prompt, E3's gate arms as rows, and the tables.
The scorer's test reads the Facts in cache/facts/ (the archive or build_facts) and is skipped without them."""

import json

import pandas as pd
import pytest

from verifier_gate.data import tiers
from verifier_gate.dsl.parse import parse
from verifier_gate.experiments import e3_baselines as b
from verifier_gate.experiments import e3_end_to_end as e3
from verifier_gate.experiments.build_facts import path
from verifier_gate.llm import client as c
from verifier_gate.llm import plain, prompts
from verifier_gate.llm.extract import Extraction


def test_the_cells_are_e3s_facts_only_runs():
    cells = b.plan()
    assert len(cells) == 360 and {s.variant for s in cells} == {"H1"} and {s.run_id for s in cells} <= {s.run_id for s in e3.plan()}
    assert len(b.plan(pilot=True)) == 4 and {s.scenario for s in b.plan(pilot=True)} == set(e3.PILOT)


def test_the_plain_prompt_has_the_facts_and_nothing_the_gate_adds():
    request = plain.plain_request("FACTS HERE", draw=2)
    assert "FACTS HERE" in request.messages[0][1] and request.draw == 2 and request.model == e3.settings.WRITER
    for gate_part in ("# Choosing the words", "DSL", "claim", "certif", "verifier", "| Words in the text |"):
        assert gate_part not in request.system
    assert json.loads(request.schema)["required"] == ["sentences"]
    writer = prompts.writer_system("v3")
    assert request.system.split("\n")[0].split(" You receive")[0] in writer  # the writer's own role


def test_plain_prompt_hashes_are_frozen_after_the_pilot():
    frozen = prompts.frozen(prompts.FROZEN_PLAIN)
    if frozen is None:
        pytest.skip("plain prompts not frozen yet (the pilot freezes them)")
    assert prompts.hashes(prompts.PLAIN_NAMES) == frozen


def answer(data, error: str = "") -> c.Response:
    return c.Response("k", "plain writer", "m", "end_turn", error, json.dumps(data), data if not error else None)


def test_a_plain_answer_is_a_text_or_refused():
    assert plain.sentences_from(answer({"sentences": [{"id": 1, "text": " Risk rises. "}]})) == [[1, "Risk rises."]]
    for bad in ({"sentences": []}, {"sentences": [{"id": 1, "text": ""}]}, {"sentences": [{"id": 1, "text": "a"}, {"id": 1, "text": "b"}]}, {}):
        with pytest.raises(ValueError):
            plain.sentences_from(answer(bad))
    with pytest.raises(ValueError):
        plain.sentences_from(answer({"sentences": [{"id": 1, "text": "a"}]}, error="truncated"))


def test_e3s_gate_arms_come_with_their_claims_by_kind():
    run = "syn-none-n50000-s2_EBM_H1_d0_claude-haiku-5-5_plausible"
    rows = {r["arm"]: r for r in b.gate_rows({run})}  # raises if the kinds do not add up to E3's claims
    assert set(rows) == {"off", "on"} and rows["on"]["exit"] and rows["off"]["exit"] == ""
    for r in rows.values():
        if r["scored"]:
            assert sum(r[f"kind {k}"] for k in b.KINDS) == r["claims"] and r["false T, no hedges"] <= r["false T"]


def frame(arm: str, false_m: list[int], **extra) -> pd.DataFrame:
    n = len(false_m)
    base = {"arm": arm, "handover": "H1", "naming": "plausible", "pilot dataset": False, "exit": "", "scored": True, "false M": false_m,
            "false T, no hedges": [0] * n, "claims": [10] * n, "words": [100] * n, "sentences": [5] * n, "hedges": [1] * n,
            "undecidable M": [0] * n, "not covered": [0] * n, "unchecked numbers": [0] * n, "cost": [0.0] * n,
            **{f"kind {k}": [1] * n for k in b.KINDS}}  # fmt: skip
    return pd.DataFrame(base | extra)


def test_compare_gives_p_u_with_its_interval_and_e_u_against_gate_off_and_the_plain_prompt():
    rows = pd.concat([frame("template", [0, 0, 0, 0]), frame("plain", [1, 1, 1, 0]), frame("off", [1, 1, 0, 0]),
                      frame("on", [1, 0, 0, 0], exit=["TEMPLATE", "RELEASED", "RELEASED", "RELEASED"])])  # fmt: skip
    out = b.compare(rows).set_index("arm")
    assert out.loc["plain prompt", "P_U"] == 0.75 and out.loc["gate on (released)", "E_U vs gate off"] == 0.5
    assert out.loc["gate on (released)", "E_U vs plain prompt"] == pytest.approx(1 - 0.25 / 0.75, abs=1e-3)
    assert out.loc["template only", "E_U vs gate off"] == 1.0 and out.loc["template only", "P_U 95% high"] > 0
    assert out.loc["gate on, exit RELEASED", "cells"] == 3 and out.loc["template only", "claims per text"] == 10
    assert out.loc["plain prompt", "strength claims per text"] == 2  # strength and negligible


@pytest.fixture(scope="module")
def ctx():
    spec = b.plan(dry=True)[0]
    if not path(tiers.scenario(spec.scenario), spec.model).with_suffix(".json").exists():
        pytest.skip("Facts not on disk (cache/facts/, see the README)")
    ctxs, _ = e3.contexts([spec])
    return ctxs[spec.run_id]


def test_the_scorer_adds_the_kinds_and_the_false_claims_against_t_without_hedges(ctx):
    sentences = [[1, "Utilization is the most important driver."], [2, "The data do not settle whether income matters."]]
    claims = [parse('rank("utilization") == 1', sentence_id=1), parse('unsettled(negligible("income"))', sentence_id=2)]
    out = b.scorer(sentences, [Extraction(claims)] * 2, ctx, ctx.facts)
    assert out["claims"] == 2 and out["kind rank"] == 1 and out["kind unsettled"] == 1 and sum(out[f"kind {k}"] for k in b.KINDS) == 2
    assert out["false T, no hedges"] <= out["false T"]
    assert b.template_text(ctx) and all(isinstance(i, int) for i, _ in b.template_text(ctx))
