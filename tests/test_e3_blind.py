"""The blind sample for human labels (experiments/e3_blind.py, D70): the draw, the counting rules fixed in the guide,
the estimates and the label provenance. No network; the build itself needs the Facts."""

import json

import numpy as np
import pandas as pd
import pytest

from verifier_gate.data import dgp
from verifier_gate.experiments import e3_blind as b
from verifier_gate.experiments.build_facts import path


def population() -> list[dict]:
    out = []
    for kind, n in (("draft", 60), ("LLM-written", 50), ("template", 20)):
        out += [{"run": f"{kind}-{k:03d}", "arm": "off" if kind == "draft" else "on", "kind": kind, "sentences": [[1, f"{kind} {k}"]]} for k in range(n)]
    return out


def test_the_draw_takes_a_fixed_simple_random_sample_per_kind():
    sample = b.draw(population())
    assert pd.Series([t["kind"] for t in sample]).value_counts().to_dict() == b.SIZES
    assert sample == b.draw(population()) and sample != b.draw(population(), seed=1)


def test_a_text_drawn_twice_is_shown_once_and_stands_for_both_entries():
    same = [[1, "Risk rises with utilization."]]
    sample = [{"run": "r1", "arm": "off", "kind": "draft", "sentences": same}, {"run": "r1", "arm": "on", "kind": "LLM-written", "sentences": same},
              {"run": "r2", "arm": "off", "kind": "draft", "sentences": [[1, "Age hardly matters."]]}]
    order, entries = b.shown_texts(sample)
    assert len(order) == 2 and [t["arm"] for t in entries[json.dumps(same)]] == ["off", "on"]


def doc(labels: dict, whole: str = "no") -> dict:
    return {"labels": {str(k): v for k, v in labels.items()}, "whole": whole}


def test_the_counting_rules_are_the_guides():
    ids = [1, 2]
    unsettled = doc({1: "supported", 2: "unsettled"})
    assert b.text_verdict(unsettled, ids, "refuted") == "ok" and b.text_verdict(unsettled, ids, "release rule") == "error"
    misleading = doc({1: "misleading", 2: "nothing"})
    assert b.text_verdict(misleading, ids, "release rule") == "ok" and b.text_verdict(misleading, ids, "broad") == "error"
    assert b.text_verdict(doc({1: "supported", 2: "supported"}, whole="yes"), ids, "broad") == "error"
    assert b.text_verdict(doc({1: "supported", 2: "unsure"}), ids, "refuted") == "open"
    assert b.text_verdict(doc({1: "false", 2: "unsure"}), ids, "refuted") == "error"
    assert b.text_verdict(doc({1: "supported"}), ids, "refuted") == "missing"
    assert b.text_verdict(doc({1: "supported", 2: "supported"}, whole=None), ids, "refuted") == "missing"
    assert b.text_verdict(None, ids, "refuted") == "missing"


def test_p_u_on_weights_the_strata_by_population_and_e_u_follows():
    rows = [{"kind": "draft", "refuted": v} for v in ["error"] * 15 + ["ok"] * 15]
    rows += [{"kind": "LLM-written", "refuted": v} for v in ["error"] * 4 + ["ok"] * 36]
    rows += [{"kind": "template", "refuted": "ok"} for _ in range(10)]
    verdicts = pd.DataFrame(rows)
    for standard in ("release rule", "broad"):
        verdicts[standard] = verdicts["refuted"]
    table = b.stratum_estimates(verdicts, {"draft": 600, "LLM-written": 300, "template": 300}).set_index(["standard", "stratum"])
    assert table.loc[("refuted", "draft"), "P_U"] == 0.5 and table.loc[("refuted", "LLM-written"), "P_U"] == 0.1
    assert table.loc[("refuted", "on (weighted)"), "P_U"] == 0.05 and table.loc[("refuted", "E_U"), "P_U"] == 0.9
    lo, hi = table.loc[("refuted", "E_U"), ["lo", "hi"]]
    assert lo < 0.9 < hi


def event(at: str, field: str, old, new, by: str = "u_1") -> dict:
    return {"at": at, "by": by, "field": field, "from": old, "to": new}


def test_provenance_names_who_set_each_label_and_every_change():
    raters = {"AS": {"rater": {"id": "u_1", "code": "AS", "owner": True},
                     "labels": {"B01": {"labels": {"1": "false"}, "whole": "no", "history": [
                         event("2026-10-21T10:00:00Z", "s1", None, "supported"), event("2026-10-21T10:05:00Z", "s1", "supported", "false"),
                         event("2026-10-21T10:06:00Z", "whole", None, "no")]}}}}  # fmt: skip
    adjudication = {"B01": {"labels": {"1": "unsettled"}, "proposed_by": "AS", "decided_by": "AS, XY", "at": "2026-10-25"}}
    table = b.provenance(raters, adjudication).set_index(["rater", "item", "field"])
    s1 = table.loc[("AS", "B01", "s1")]
    assert (s1["proposed by"], s1["proposed"], s1["changes"], s1["changed by"], s1["final"]) == ("AS", "supported", 1, "AS", "false")
    assert "supported -> false" in s1["changes made"]
    adj = table.loc[("adjudication", "B01", "s1")]
    assert adj["final"] == "unsettled" and adj["source"] == "adjudicated by AS, XY"
    _, docs = b.primary(raters, adjudication)
    assert docs["B01"]["labels"]["1"] == "unsettled" and docs["B01"]["whole"] == "no"


def test_two_raters_are_compared_on_the_overlap():
    items = {"B01": {"sentences": [[1, "a"], [2, "b"]]}, "B02": {"sentences": [[1, "c"]]}}
    one = {"B01": doc({1: "false", 2: "supported"}), "B02": doc({1: "supported"})}
    two = {"B01": doc({1: "unsettled", 2: "supported"}), "B02": doc({1: "supported"})}
    raters = {"AS": {"rater": {"code": "AS"}, "labels": one}, "XY": {"rater": {"code": "XY"}, "labels": two}}
    table = b.raters_table(raters, items, ["B01", "B02"]).set_index(["unit", "standard"])
    assert table.loc[("sentence", "all six labels"), "pairs"] == 3 and table.loc[("sentence", "all six labels"), "agreement"] == round(2 / 3, 3)
    assert table.loc[("sentence", "release rule"), "agreement"] == 1.0 and table.loc[("text", "refuted"), "agreement"] == 0.5


def test_a_labelled_released_sentence_is_shown_beside_the_gates_claims_and_readings(tmp_path, monkeypatch):
    """released.csv (D83): a labelled sentence of a released text, found by its run id through the shown number, with
    the claims of the released version on it, their verdicts and how many readings found each."""
    runs = tmp_path / "haiku" / "runs"
    runs.mkdir(parents=True)
    plan = [[3, 'direction("income") in ("decreasing", "mostly_decreasing")', "true", "", "", ""]]
    version = {"sentences": [[1, "Utilization matters most."], [3, "Risk generally decreases with income."]], "claims": plan,
               "roundtrip": {"extracted": [[3, plan[0][1], 3]], "unplanned": []}}  # fmt: skip
    (runs / "r1.json").write_text(json.dumps({"versions": [version]}))
    monkeypatch.setattr(b.ind, "out_folder", lambda source: tmp_path / "independent")
    verdicts = pd.DataFrame([{"item": "B01", "run": "r1", "arm": "on", "kind": "LLM-written", "exit": "RELEASED_REDUCED", "sentence ids": "[1, 3]"},
                             {"item": "B01", "run": "r1", "arm": "off", "kind": "draft", "exit": "RELEASED_REDUCED", "sentence ids": "[1, 3]"}])  # fmt: skip
    docs = {"B01": {"labels": {"1": "supported", "2": "unsettled"}, "notes": {"2": "shape in between not resolved"}}}
    table = b.released(verdicts, docs, "any")
    assert len(table) == 1
    row = table.iloc[0]
    assert (row["sentence"], row["label"], row["generally"], row["all certified"], row["readings"]) == (2, "unsettled", True, True, "3")
    assert row["note"] == "shape in between not resolved" and row["text"] == "Risk generally decreases with income."


def test_a_reduced_text_shows_no_gap_in_its_sentence_numbers():
    """A text the gate reduced keeps the ids of the sentences it kept; shown as they are, the gaps would tell the
    exit state and which sentences failed (D77)."""
    assert b.shown([[1, "a"], [3, "b"], [7, "c"]]) == [[1, "a"], [2, "b"], [3, "c"]]


def test_the_guide_renders_with_its_lists_and_bold_words():
    out = b.guide_html(b.GUIDE.read_text())
    assert "<h2>Labelling guide (b1)</h2>" in out and "<li><b>Supported</b>:" in out and "**" not in out
    assert all(word in b.GUIDE.read_text() for word in ("refuted", "release rule", "broad"))


def test_the_words_table_is_the_runs_writer_table():
    rows = b.word_table("v3-x3")
    assert ["the data do not settle whether ...", "the facts leave that claim open at this sample size"] in rows
    assert all(len(r) == 2 and "`" not in r[0] for r in rows)


def test_the_page_shows_nothing_about_the_source_of_a_text(tmp_path):
    if not all(path(dgp.SCENARIOS[2], kind).with_suffix(".json").exists() for kind in ("EBM", "XGB2")):
        pytest.skip("Facts not on disk (cache/facts/, see the README)")
    out = b.build("v3-x3", tmp_path / "blind")
    data = json.loads((out / "items.json").read_text())
    assert all(set(it) == {"id", "facts", "model", "named", "sentences"} for it in data["items"])
    assert all([s for s, _ in it["sentences"]] == list(range(1, len(it["sentences"]) + 1)) for it in data["items"])  # D77
    text = (out / "blind_page.html").read_text()
    key = pd.read_csv(out / "key.csv")
    assert not any(run in text for run in key.run) and "RELEASED" not in text and "TEMPLATE" not in text
    assert data["overlap"] == [it["id"] for it in data["items"][: b.OVERLAP]]
    with pytest.raises(SystemExit, match="fixed once built"):
        b.build("v3-x3", out)
    protocol = json.loads((out / "protocol.json").read_text())
    assert protocol["sha256"]["guide.md"] == b.digest(out / "guide.md") and np.isclose(sum(b.SIZES.values()), protocol["sampled entries"])
