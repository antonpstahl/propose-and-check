"""The critic's prompts c3 (D79): c2 in D75's configuration, with the rules of writer prompt v4 as D74's writer got
them, the gate's outcomes from D78's run and the texts of D76's blind sample (experiments/e2_critic.py). No network;
the gate's outcomes are fixtures, since D78's run writes them. Nothing of the blind sample's key.csv is printed."""

import hashlib
import json
import sys

import pandas as pd
import pytest

from verifier_gate.experiments import e2_critic, e2_text
from verifier_gate.lexicon import predicates as p
from verifier_gate.lexicon import words
from verifier_gate.llm import client as c
from verifier_gate.llm import critique, prompts, settings

V3 = p.load(p.VERSIONS["v3"])
D74_RUN = "v4-x5-m5-d74"
D74_RUNS = e2_text.E3_RESULTS / D74_RUN / "haiku" / "runs"
CELL = ("syn-dominant-n5000-s2", "EBM", "opaque")
CERTIFIED = "Statements the verifier certifies"  # in an H2 handover only


def run(variant: str, draw: int = 0) -> str:
    scenario, model, naming = CELL
    return f"{scenario}_{model}_{variant}_d{draw}_{settings.WRITER}_{naming}"


@pytest.fixture(autouse=True)
def current(monkeypatch):
    """c3 runs only under lexicon v3 with D74's fixes: these tests lift the pin and D74's switch, whatever the
    environment says."""
    monkeypatch.delenv(p.PIN, raising=False)
    monkeypatch.delenv(p.D74, raising=False)


# --- the prompt -------------------------------------------------------------------------------------------


def test_c3_reads_writer_prompt_v4_exactly_as_d74s_writer_got_it():
    v4 = prompts.writer_system("v4")
    assert hashlib.sha256(v4.encode()).hexdigest() == prompts.frozen(prompts.FROZEN_VERSIONS["v4"])["system"]
    assert v4 == prompts.load("system") == json.loads((D74_RUNS / f"{run('H2', 3)}.json").read_text())["writer"]["system"]
    rules = prompts.writer_rules("v4")
    assert rules.startswith("# The text") and words.rules(V3) in rules and words.table(V3) in rules and "`drop(" in rules
    assert "# The claims" not in rules and "Return one JSON object with two lists" not in rules  # the writer's answer format is not a rule
    system = prompts.critic_system("c3")
    assert system == prompts.load("critic_system_c3").replace("{rules}", rules) and "{rules}" not in system
    assert prompts.writer_rules("v3") not in system and prompts.writer_rules("v3") in prompts.critic_system("c2")


def test_c3_is_c2s_prompt_with_v4s_rules_frozen_before_its_first_call():
    assert prompts.load("critic_system_c3") == prompts.load("critic_system_c2")  # no word of c2's names the writer's version
    frozen = prompts.frozen(prompts.FROZEN_CRITIC["c3"])
    assert frozen is not None and prompts.hashes(prompts.CRITIC_NAMES["c3"]) == frozen
    assert frozen["critic"] == prompts.frozen(prompts.FROZEN_CRITIC["c2"])["critic"]  # critic.md is shared
    c2, c3 = (critique.critic_request("FACTS", [[1, "x"]], version=v) for v in ("c2", "c3"))
    assert c2.messages == c3.messages and c2.key != c3.key
    assert prompts.CRITIC_VERSION == "c2"  # c3 is chosen by name


def test_c3_runs_only_under_lexicon_v3_with_d74s_fixes(monkeypatch):
    e2_critic.configuration("c3")
    for name, value in ((p.PIN, "v2"), (p.D74, "0")):
        monkeypatch.setenv(name, value)
        with pytest.raises(SystemExit, match="critic c3 runs under lexicon v3 with D74's fixes"):
            e2_critic.configuration("c3")
        e2_critic.configuration("c2")  # c1 and c2 run under any lexicon
        monkeypatch.delenv(name)
    monkeypatch.setenv(p.PIN, "v2")
    with pytest.raises(ValueError, match="rendered under lexicon v3"):  # v4's DSL table does not parse under v2
        prompts.writer_system("v4")


# --- folder, sources, gate --------------------------------------------------------------------------------


def test_c3_has_its_own_folder_gate_and_sources(monkeypatch):
    folder = e2_critic.RESULTS / "v3-d74" / "text" / "critic" / "gpt-6-luna" / "c3"
    assert e2_critic.folder(settings.CRITIC, "c3") == folder and e2_critic.gate_folder("c3") == e2_critic.RESULTS / "v3-d74" / "text" / "x5"
    assert e2_critic.VERSION_SOURCES["c3"] == ("llm", "script", "control", "blind")
    assert e2_critic.GATE_FILES["c3"] == ("script.csv", "llm_labelled.csv")  # D78, as revised: x5 reads the labelled LLM mutants again
    monkeypatch.setenv(p.PIN, "v2")
    assert e2_critic.folder(settings.CRITIC, "c3") == folder  # it does not follow the pin


def test_e3_is_no_source_of_c3_and_blind_none_of_c2(monkeypatch):
    for critic, source in (("c3", "e3"), ("c2", "blind")):
        monkeypatch.setattr(sys, "argv", ["e2_critic", "--critic", critic, "--sources", source, "--estimate"])
        with pytest.raises(SystemExit, match=f"critic {critic}'s sources are"):
            e2_critic.main()


def cases() -> list:
    Case = e2_critic.Case
    return [Case("syn-x_EBM_001", "script", "syn-x", "EBM", "plausible", [[1, "a"]], [], 1, {"role": "error", "operator": "M1"}),
            Case("syn-x_EBM_control", "control", "syn-x", "EBM", "plausible", [[1, "a"]], [], None, {"role": "control text"}),
            Case("L001", "llm", "syn-x", "EBM", "opaque", [[1, "a"]], [], 1, {"role": "error", "gate case": "run-a"}),
            Case("B01", "blind", "syn-x", "EBM", "opaque", [[1, "a"]], [], None, {"role": "unlabelled", "run": "run-b", "kind": "draft"})]  # fmt: skip


def test_c3_reads_d78s_gate_before_any_call_and_a_run_stops_without_it(tmp_path, monkeypatch):
    monkeypatch.setattr(e2_critic, "RESULTS", tmp_path)
    with pytest.raises(SystemExit, match=r"no script.csv in .*v3-d74/text/x5.*nothing sent"):
        e2_critic.gate_for(cases(), "c3")
    assert e2_critic.gate_for(cases(), "c3", dry=True) == {}  # a dry run goes on without it
    assert e2_critic.gate_for(cases()[3:], "c3") == {}  # the blind texts need none
    base = tmp_path / "v3-d74" / "text" / "x5"
    base.mkdir(parents=True)
    columns = ["case", "read", "caught", "caught at the change"]
    pd.DataFrame([["syn-x_EBM_001", True, True, True], ["syn-x_EBM_control", False, None, None]], columns=columns).to_csv(base / "script.csv", index=False)
    pd.DataFrame([["run-a", True, True, True]], columns=columns).to_csv(base / "llm.csv", index=False)  # D78 builds no LLM mutants
    with pytest.raises(SystemExit, match="no llm_labelled.csv"):
        e2_critic.gate_for(cases(), "c3")
    pd.DataFrame([["run-a", True, False, False]], columns=columns).to_csv(base / "llm_labelled.csv", index=False)  # e2_text --labelled
    gate = e2_critic.gate_for(cases(), "c3")
    assert gate["syn-x_EBM_001"] == {"gate read": True, "gate caught": True, "gate at the change": True}
    assert gate["syn-x_EBM_control"] == {"gate read": False, "gate caught": True, "gate at the change": False}  # not read: caught (D32)
    assert gate["run-a"]["gate caught"] is False  # an LLM mutant by the case it came from, as x5 read it again
    unknown = e2_critic.Case("syn-x_EBM_002", "script", "syn-x", "EBM", "plausible", [[1, "a"]], [], 1, {"role": "error", "operator": "M3"})
    with pytest.raises(SystemExit, match=r"1 case\(s\) without an outcome .* e.g. \['syn-x_EBM_002'\]"):
        e2_critic.gate_for([*cases(), unknown], "c3")


def response(data) -> c.Response:
    return c.Response("k", "critic", settings.CRITIC, "end_turn", "", json.dumps(data), data)


def test_a_blind_text_is_scored_without_a_gate_outcome():
    blind = cases()[3]
    reqs = {blind.case_id: critique.critic_request("FACTS", blind.sentences, version="c3")}
    answers = {reqs["B01"].key: response({"problems": [{"sentence_id": 1, "problem": "too strong"}], "p_error": 0.9})}
    table = e2_critic.score([blind], reqs, answers, {"B01": {"gate caught": True}})  # not even an outcome under its id
    assert bool(table.loc[0, "blocked"]) and table.loc[0, "role"] == "unlabelled" and "gate caught" not in table
    assert e2_critic.summarise(table).empty


# --- the cases and their handovers ------------------------------------------------------------------------


def test_c3_reads_the_labelled_llm_mutants_where_they_were_made_with_the_handover_of_their_run():
    llm = e2_critic.build(("llm",), "c3")  # under v3, from results/e2/v2/text/labels
    assert len(llm) == 100 and {x.source for x in llm} == {"llm"} and sum(x.info["role"] == "error" for x in llm) == 95
    first = llm[0]
    assert e2_critic.facts_text(first, {}, "c3") == e2_critic.writer_handover(first.info["gate case"], e2_text.E3_SOURCE) == e2_critic.facts_text(first, {}, "c2")


def test_c3_gives_a_template_text_the_h1_of_its_cell_in_d74s_run():
    scenario, model, naming = CELL
    control = e2_critic.Case(f"{scenario}_{model}_control", "control", scenario, model, naming, [], [], None, {"role": "control text"})
    assert e2_critic.written_by(control) == run("H1")
    text = e2_critic.facts_text(control, {}, "c3")
    assert text == e2_critic.writer_handover(run("H1"), D74_RUN) and CERTIFIED not in text


def test_c3_builds_the_blind_texts_from_items_json_with_the_handover_of_each_items_run(tmp_path):
    facts = "_".join(CELL)
    items = [{"id": "B01", "facts": facts, "model": CELL[1], "named": [], "sentences": [[1, "First."], [2, "Second."]]},
             {"id": "B02", "facts": facts, "model": CELL[1], "named": [], "sentences": [[1, "A template."]]}]  # fmt: skip
    (tmp_path / "items.json").write_text(json.dumps({"items": items}))
    key = [{"item": "B01", "run": run("H2", 3), "kind": "draft"}, {"item": "B01", "run": run("H1", 1), "kind": "LLM-written"},
           {"item": "B02", "run": run("H2", 2), "kind": "template"}, {"item": "B02", "run": run("H1", 4), "kind": "template"}]  # fmt: skip
    pd.DataFrame(key).to_csv(tmp_path / "key.csv", index=False)
    blind = e2_critic.blind_cases(tmp_path)
    assert [x.case_id for x in blind] == ["B01", "B02"] and {x.source for x in blind} == {"blind"}
    assert [x.sentences for x in blind] == [it["sentences"] for it in items] and all(x.info["role"] == "unlabelled" for x in blind)
    assert all((x.scenario, x.model, x.naming) == CELL for x in blind)
    assert [e2_critic.written_by(x) for x in blind] == [run("H2", 3), run("H1")]  # the first entry's run; a template: the H1 of its cell at draw 0
    texts = [e2_critic.facts_text(x, {}, "c3") for x in blind]
    assert texts[0] == e2_critic.writer_handover(run("H2", 3), D74_RUN) and CERTIFIED in texts[0]
    assert texts[1] == e2_critic.writer_handover(run("H1"), D74_RUN) and CERTIFIED not in texts[1]
    pd.DataFrame([{**key[0], "run": run("H2", 3).replace("_EBM_", "_XGB2_")}, *key[1:]]).to_csv(tmp_path / "key.csv", index=False)
    with pytest.raises(ValueError, match="B01: its entry in key.csv is about another model"):
        e2_critic.blind_cases(tmp_path)


def test_c3_reads_d76s_blind_sample_as_shown():
    """The 78 texts as items.json shows them, sentences numbered 1 to n (D77), each with a handover from a run of
    D74's; the assertions print nothing of key.csv."""
    items = json.loads((e2_critic.BLIND / "items.json").read_text())["items"]
    blind = e2_critic.blind_cases()
    assert len(blind) == len(items) == 78 and [x.case_id for x in blind] == [it["id"] for it in items]
    assert [x.sentences for x in blind] == [it["sentences"] for it in items]
    assert all([k for k, _ in x.sentences] == list(range(1, len(x.sentences) + 1)) for x in blind)
    assert all((D74_RUNS / f"{e2_critic.written_by(x)}.json").exists() for x in blind)
    assert all(e2_critic.facts_text(x, {}, "c3").startswith("Model: ") for x in blind)
