"""E3 read by another vendor's model and counted by the release rule (experiments/e3_independent.py, D69). No network."""

from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from verifier_gate.experiments import e3_independent as ind
from verifier_gate.gate import gate as g
from verifier_gate.llm import extract, prompts, settings
from verifier_gate.llm.client import Response, sha


def counts(**kw) -> dict:
    return {c: 0 for c in ind.COUNTS} | kw


def test_the_release_rule_counts_an_undecidable_claim_and_refuted_does_not():
    undecidable = counts(**{"undecidable M": 1})
    assert ind.STANDARDS["release rule"](undecidable) and not ind.STANDARDS["refuted"](undecidable)
    assert ind.STANDARDS["release rule or unchecked"](counts(**{"no DSL form": 1}))
    assert not ind.STANDARDS["release rule"](counts(**{"no DSL form": 1, "hedges": 2, "claims": 9}))
    assert ind.STANDARDS["against T"](counts(**{"false T": 1}))


@pytest.fixture
def ctx():
    facts = SimpleNamespace(features=[SimpleNamespace(name="utilization"), SimpleNamespace(name="age")])
    return g.Context(facts, [])


def test_the_other_readers_request_is_e3s_scoring_request_with_only_the_model_changed(ctx):
    text = {"sentences": [[1, "Risk rises with utilization."], [2, "Age hardly matters."]], "draw": 3}
    system = ind.extractor_system("v3-x3")
    haiku = ind.requests_for(text, ctx, settings.EXTRACTOR, system)
    luna = ind.requests_for(text, ctx, settings.CRITIC, system)
    assert [r.replica for r in haiku] == [3, 4, 5] and all(r.draw == 3 for r in haiku)
    for h, lu in zip(haiku, luna):
        assert (lu.model, h.model) == (settings.CRITIC, settings.EXTRACTOR)
        assert (lu.system, lu.messages, lu.schema, lu.effort, lu.replica) == (h.system, h.messages, h.schema, h.effort, h.replica)
        assert lu.key != h.key
    assert haiku[0].key == replace(extract.extractor_request(text["sentences"], extract.features_text(ctx.facts, ctx.names, ctx.descriptions), 3, 3), system=system).key


def test_x3s_prompt_is_checked_against_its_hash():
    assert sha(ind.extractor_system("v3-x3")) == prompts.EXTRACTOR_HISTORY["x3"]["extract_system"]


def test_an_answer_not_received_is_not_retried_and_one_that_is_no_reading_is(ctx):
    text = {"sentences": [[1, "Risk rises with utilization."]], "draw": 0}
    reqs = ind.requests_for(text, ctx, settings.CRITIC, "system")
    good = Response(reqs[0].key, "scorer", settings.CRITIC, "end_turn", "", data={"sentences": [{"id": 1, "claims": ['direction("utilization") == "increasing"'], "unexpressed": []}]})
    bad = Response(reqs[1].key, "scorer", settings.CRITIC, "max_tokens", "truncated")
    readings, retry = ind.usable(text, ctx, reqs, {reqs[0].key: good, reqs[1].key: bad})
    assert len(readings) == 1 and retry == [reqs[1]]
    api = Response(reqs[2].key, "scorer", settings.CRITIC, "", "api")
    assert ind.usable(text, ctx, reqs[2:], {reqs[2].key: api}) == ([], [])


def toy_verdicts() -> pd.DataFrame:
    """Two datasets; off: 3 of 4 texts refuted by haiku, 2 by luna; on: 1 of 4 by luna only."""
    rows = []
    for k, (arm, kind, h, lu) in enumerate([("off", "draft", 1, 1), ("off", "draft", 1, 0), ("off", "draft", 1, 1), ("off", "draft", 0, 0),
                                            ("on", "LLM-written", 0, 1), ("on", "LLM-written", 0, 0), ("on", "template", 0, 0), ("on", "template", 0, 0)]):
        row = {"run": f"r{k}", "arm": arm, "kind": kind, "scenario": f"s{k % 2}", "tier": "synthetic"}
        for name in ind.STANDARDS:
            row |= {f"{name} | haiku": bool(h), f"{name} | luna": bool(lu), f"{name} | either": bool(h or lu), f"{name} | both": bool(h and lu)}
        rows.append(row)
    return pd.DataFrame(rows)


def test_the_residual_table_gives_p_u_per_group_and_e_u_with_intervals():
    table = ind.residual_table(toy_verdicts(), draws=200)
    haiku = table[(table.standard == "refuted") & (table.reader == "haiku")].iloc[0]
    luna = table[(table.standard == "refuted") & (table.reader == "luna")].iloc[0]
    assert (haiku["P_U off"], haiku["P_U on"], haiku["E_U"]) == (0.75, 0.0, 1.0)
    assert (luna["P_U off"], luna["P_U on"], luna["P_U on, LLM-written"], luna["P_U on, template"]) == (0.5, 0.25, 0.5, 0.0)
    assert luna["E_U"] == 0.5 and luna["off lo"] <= 0.5 <= luna["off hi"]
    either = table[(table.standard == "refuted") & (table.reader == "either")].iloc[0]
    assert either["P_U off"] == 0.75 and either["P_U on"] == 0.25


def test_kappa_is_one_for_equal_verdicts_and_zero_for_chance():
    assert ind.kappa(pd.Series([1, 0, 1, 0]), pd.Series([1, 0, 1, 0])) == 1.0
    assert ind.kappa(pd.Series([1, 1, 0, 0]), pd.Series([1, 0, 1, 0])) == 0.0
    assert np.isnan(ind.kappa(pd.Series([1, 1]), pd.Series([1, 1])))


def test_the_agreement_table_counts_claims_found_by_both_readers():
    table = toy_verdicts()
    claims = {"haiku": pd.DataFrame({"run": ["r0", "r0"], "arm": ["off", "off"], "claim": ["a", "b"]}),
              "luna": pd.DataFrame({"run": ["r0"], "arm": ["off"], "claim": ["a"]})}
    luna = table[["run", "arm"]].assign(lines=10, **{"unparsed lines": 1})
    out = ind.agreement(table, luna, claims)
    off = out[(out.group == "off") & (out.standard == "refuted")].iloc[0]
    assert (off["haiku's claims luna finds"], off["luna's claims haiku finds"], off["luna lines unparsed"]) == (0.5, 1.0, 0.1)
    assert (off["both"], off["haiku only"], off["luna only"], off["neither"]) == (2, 1, 0, 1)
