"""The sizes of the defects D75 deferred (experiments/deferred.py): how a run's end is classified, ranks with ties,
the checks on DSL lines, steps on counts, numbers in words and digits in feature codes, dropped lines, reading counts,
spurious shares and opposite verdicts. No network; the last test rebuilds a few of D74's runs from the cache and the
Facts, and skips without them."""

from collections import Counter
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from verifier_gate.data import tiers
from verifier_gate.dsl.grammar import Claim
from verifier_gate.experiments import deferred as d
from verifier_gate.experiments import e3_end_to_end as e3
from verifier_gate.experiments.build_facts import path
from verifier_gate.llm.client import CACHE
from verifier_gate.llm.extract import Extraction

TEMPLATE = "TEMPLATE: template text from the certified facts"
STOP = 'stop repairing: no progress: rank("x") == 1 failed before'


def versions(*sources: str, missing: tuple = ()) -> list[dict]:
    """Text versions as a trace keeps them; a reduced one with the required terms it does not cover."""
    return [{"source": s, "missing": list(missing) if s == "reduced" else []} for s in sources]


def test_the_stop_path_names_the_rule_and_the_drop_step():
    events = ["round trip of the draft: 3 extractions", "repair round 1: 2 problem(s) in the text", "round trip of the draft: 3 extractions",
              "RELEASED: passed after 1 repair round(s)"]  # fmt: skip
    released = d.stop_path("RELEASED", 1, events, versions("proposer", "repair 1"))
    assert released == {"stop rule": "", "drop step": "", "path": "released after 1 repair round(s)"}
    dropped = d.stop_path("RELEASED_REDUCED", 1, ["repair round 1: 1 problem(s)", STOP, "round trip of the reduced text: 3 extractions",
                                                  "RELEASED_REDUCED: failing sentences dropped after 1 repair round(s)"], versions("proposer", "repair 1"))  # fmt: skip
    assert dropped == {"stop rule": "no progress", "drop step": "the rest released", "path": "sentences dropped after: no progress"}
    rounds = ["repair round 1: 3 problem(s)", "repair round 2: 1 problem(s)", "stop repairing: 2 repair rounds used", TEMPLATE]
    plain = versions("proposer", "repair 1", "repair 2", "template")
    uncovered = d.stop_path("TEMPLATE", 2, rounds, versions("proposer", "repair 1", "repair 2", "reduced", "template", missing=("income",)))
    assert uncovered["path"] == "template after: repair rounds exhausted; the reduced text no longer covers a required term"
    assert d.stop_path("TEMPLATE", 2, rounds, versions("proposer", "reduced", "template"))["drop step"] == "the reduced plan failed its check"
    assert d.stop_path("TEMPLATE", 2, rounds, plain)["drop step"] == "no sentence left"
    assert d.stop_path("TEMPLATE", 0, [STOP, "nothing to drop", TEMPLATE], versions("proposer", "template"))["drop step"] == "nothing to drop"
    failed = [STOP, "round trip of the reduced text: 3 extractions", "the reduced text failed its round trip", TEMPLATE]
    assert d.stop_path("TEMPLATE", 1, failed, plain)["drop step"] == "the reduced text failed its round trip"
    few = [STOP, "round trip of the reduced text: 3 extractions", "round trip could not run: 1 readable extraction(s)", TEMPLATE]
    assert d.stop_path("TEMPLATE", 1, few, plain)["drop step"] == "too few readings of the reduced text"
    budget = d.stop_path("TEMPLATE", 1, [STOP, "no calls left for the round trip", TEMPLATE], plain)
    assert budget["drop step"] == "no calls left for the reduced text's round trip"
    draft = ["round trip of the draft: 3 extractions", "extraction retry: 2 answer(s) not a reading", "round trip could not run: 1 readable extraction(s)",
             TEMPLATE]  # fmt: skip
    assert d.stop_path("TEMPLATE", 0, draft, versions("proposer", "template"))["path"] == "template: too few readings of a draft"
    no_draft = d.stop_path("TEMPLATE", 0, ["format-only retry: the answer is not a draft", TEMPLATE], versions("template"))
    assert no_draft == {"stop rule": "", "drop step": "", "path": "template: no draft after the format-only retry"}


def test_retries_are_counted_by_cause():
    events = ["format-only retry: 2 DSL line(s) do not parse", "round trip of the draft: 3 extractions", "extraction retry: 2 answer(s) not a reading",
              "format-only retry: the answer is not a draft", "extraction retry: 1 answer(s) not a reading"]  # fmt: skip
    assert d.format_retries(events) == Counter({"DSL lines do not parse": 1, "the answer is not a draft": 1})
    out = d.retries(events)
    assert (out["format-only retries"], out["extraction retries"], out["extraction answers retried"]) == (2, 2, 3)


def test_the_round_tripped_versions_are_those_whose_plan_passed():
    def version(source: str, verdict: str = "true", trip: dict | None = None) -> dict:
        return {"source": source, "claims": [[1, 'rank("a") == 1', verdict]], "format_errors": [], "missing": [], "roundtrip": trip}

    trace = {"events": [], "versions": [version("proposer", "false"), version("repair 1", trip={"readings": 3}), version("repair 2"), version("template")]}
    assert d.round_tripped(trace) == [1, 2]  # repair 2 passed its plan check, but its round trip could not run
    trace["events"] = ["no calls left for the round trip"]
    assert d.round_tripped(trace) == [1]


def test_ranks_break_ties_by_the_features_order_unless_they_compete():
    importance = np.array([[0.3, 0.1, 0.1, 0.5], [0.0, 0.0, 0.2, 0.0]])
    assert d.ordinal_ranks(importance).tolist() == [[2, 3, 4, 1], [2, 3, 1, 4]]
    assert d.competition_ranks(importance).tolist() == [[2, 3, 3, 1], [2, 2, 1, 2]]
    assert d.tied(importance).tolist() == [[False, True, True, False], [True, True, False, True]]
    rows = np.random.default_rng(0).integers(0, 3, size=(50, 6)).astype(float)
    for ranks, row in zip(d.ordinal_ranks(rows), rows):  # facts/build.py: a stable sort by importance, rank = position + 1
        order = sorted(range(6), key=lambda i: -row[i])
        assert ranks.tolist() == [order.index(i) + 1 for i in range(6)]


def test_the_line_checks_find_what_the_parser_lets_through():
    repeated = d.line_defects('threshold("x", at=1, at=2)', 9)
    assert repeated["repeated keyword"] and repeated["parse"] == "accepted"
    infinite = d.line_defects('threshold("x", at=1e999)', 9)
    assert infinite["non-finite number"] and infinite["parse"] == "accepted"
    word = d.line_defects('threshold("x", at=nan)', 9)
    assert word["nan or inf as a word"] and not word["non-finite number"] and word["parse"] == "DSLError"
    every = 'rank("x") in (1, 2, 3, 4, 5, 6, 7, 8, 9)'
    assert d.line_defects(every, 9)["vacuous rank set"] and not d.line_defects(every, 10)["vacuous rank set"]
    assert d.line_defects(f"unsettled({every})", 9)["vacuous rank set"]
    some = d.line_defects('rank("x") in (2, 3)', 9)
    assert some["rank set"] and not some["vacuous rank set"]
    plain = d.line_defects('strength("x") == "weak"', 9)
    assert plain["parse"] == "accepted" and not any(plain[k] for k in d.DEFECTS) and not plain["rank set"]


def test_a_parse_error_that_escapes_dslerror_is_named(monkeypatch):
    def overflow(line: str):
        raise RecursionError("maximum recursion depth exceeded")

    monkeypatch.setattr(d, "parse", overflow)
    assert d.line_defects('rank("x") == 1', 9)["parse"] == "RecursionError"


def test_the_dsl_lines_of_an_answer_as_written():
    writer = {"sentences": [{"id": 1, "text": "a"}], "claims": [{"sentence_id": 1, "dsl": ' rank("a") == 1 '}]}
    reader = {"sentences": [{"id": 1, "claims": ['rank("a") == 1', "x"], "unexpressed": []}, {"id": 2, "claims": [], "unexpressed": ["b"]}]}
    assert d.dsl_lines(writer, "writer") == [(1, 'rank("a") == 1')]
    assert d.dsl_lines(reader, "gate reader") == [(1, 'rank("a") == 1'), (1, "x")]
    assert d.dsl_lines(None, "writer") == []


def test_a_step_on_a_count_is_written_as_a_value_not_by_its_gap():
    f = SimpleNamespace(name="n_delinquencies", values=np.array([0.0, 1.0, 2.0, 3.0]))
    facts = SimpleNamespace(features=[f], feature=lambda name: f)
    half = d.step_on_count(Claim("threshold", ("n_delinquencies",), 0.5), facts)
    assert (half["printed"], half["printed value observed"], half["gap"]) == ("= 0.5", False, "from 0 to 1")
    assert d.step_on_count(Claim("threshold", ("n_delinquencies",), 0.999), facts)["printed"] == "= 0.999"
    one = d.step_on_count(Claim("threshold", ("n_delinquencies",), 1.0), facts)
    assert (one["printed"], one["printed value observed"], one["gap"]) == ("= 1", True, "from 0 to 1")
    assert d.step_on_count(Claim("direction", ("n_delinquencies",), "increasing"), facts) is None
    smooth = SimpleNamespace(name="income", values=None)
    assert d.step_on_count(Claim("threshold", ("income",), 40200.0), SimpleNamespace(features=[smooth], feature=lambda name: smooth)) is None
    assert not d.count_feature(SimpleNamespace(values=np.array([0.5, 1.5, 2.5])))


def test_h2_statements_are_read_as_listed():
    text = ("Interactions: the model has 5 pairs.\n\nStatements the verifier certifies for this model (true at this sample size), as DSL and in words:\n"
            "- rank(\"utilization\") == 1  (credit utilization is the model's most important feature)\n"
            "- threshold(\"n_delinquencies\", at=0.5)  (the model's predicted default risk jumps at the number of past delinquencies = 0.5)")  # fmt: skip
    assert d.h2_statements(text) == [('rank("utilization") == 1', "credit utilization is the model's most important feature"),
                                     ('threshold("n_delinquencies", at=0.5)', "the model's predicted default risk jumps at the number of past delinquencies = 0.5")]  # fmt: skip
    assert d.h2_statements("Interactions: the model has 5 pairs.") == []


@pytest.mark.parametrize("sentence", [
    "The model's predicted default risk jumps when the count moves from zero to one.",
    "Risk rises once an applicant has at least one delinquency.",
    "Applicants with two or more months of payment delay receive a much higher predicted risk.",
    "Utilization is the most important feature, with about a third of its importance.",
    "A net increase of about three units in log-odds from low to high utilization.",
    "A share the data place somewhere between roughly one fifth and one quarter",
    "The risk steps up once the count moves above zero.",
])  # fmt: skip
def test_counts_in_words_are_found(sentence):
    assert d.counts_in_words(sentence)


@pytest.mark.parametrize("sentence", [
    "The two features interact in the model.",
    "Income is among the model's three most important features.",
    "The length of credit history is a third or fourth most important feature.",
    "PAY_AMT3, the amount paid two months before, hardly matters to the model's predictions.",
    "The pair is one of the model's larger interactions.",
    "Both rank in the lower half of the features.",
    "The model's predicted default risk jumps at PAY_0 = 2.",
    "Risk rises in a single sharp step.",
])  # fmt: skip
def test_counts_of_features_ranks_and_digits_are_not_counts_in_words(sentence):
    assert not d.counts_in_words(sentence)


def test_digits_inside_feature_codes_are_told_apart():
    codes = d.code_pattern(["PAY_0", "LIMIT_BAL", "BILL_AMT1", "BILL_AMT2", "AGE"])
    assert d.digits("PAY_0 matters more to the model than BILL_AMT1.", codes) == {"digit": True, "digit in a code": True, "digits only in codes": True}
    assert d.digits("Risk jumps at PAY_0 = 2.", codes)["digits only in codes"] is False
    assert d.code_pattern(["utilization", "feature_a"]) is None
    assert d.digits("Risk jumps at 0.43.", None) == {"digit": True, "digit in a code": False, "digits only in codes": False}


def test_the_digit_test_with_and_without_feature_codes():
    readings = [Extraction([], {1: ["the effect of PAY_0 is larger"], 2: ["a delay of 2 months"]}), Extraction([], {1: ["PAY_0 matters"], 2: ["2 months"]}),
                Extraction([], {3: ["a delay of 2 months"]})]  # fmt: skip
    assert d.number_sentences(readings, [1, 2, 3]) == [1, 2]  # sentence 3: one reading only
    assert d.number_sentences(readings, [1, 2, 3], d.code_pattern(["PAY_0", "AGE"])) == [2]


def test_dropped_lines_are_the_unparsed_and_the_misfiled():
    data = {"sentences": [{"id": 1, "claims": ['rank("x") == 1', 'unsettled(strength("x") != "weak")'], "unexpressed": []},
                          {"id": 7, "claims": ['rank("x") == 2'], "unexpressed": []}]}  # fmt: skip
    out = d.dropped_lines(data, {1, 2})
    assert [(x["sentence id"], x["line"], x["hedge"]) for x in out] == [(1, 'unsettled(strength("x") != "weak")', True), (7, 'rank("x") == 2', False)]
    assert "compared with" in out[0]["why"] and out[1]["why"] == "no sentence with this id"


def test_reading_counts_list_each_claim_once():
    trip = {"readings": 3, "extracted": [[1, 'rank("a") == 1', 3], [2, 'unsettled(strength("b") == "weak")', 2]], "ambiguous": [[2, 'negligible("c")']],
            "plan_only": [[2, 'negligible("c")'], [3, 'rank("d") == 4']]}  # fmt: skip
    found = {c["claim"]: (c["found"], c["hedge"], c["readings"]) for c in d.reading_counts(trip)}
    assert found == {'rank("a") == 1': (3, False, 3), 'unsettled(strength("b") == "weak")': (2, True, 3), 'negligible("c")': (1, False, 3),
                     'rank("d") == 4': (0, False, 3)}  # fmt: skip


def test_the_spurious_share_is_what_t_does_not_plant():
    def term(name: str, share: float, importance: float | None = None):
        return SimpleNamespace(name=name, share=SimpleNamespace(value=share), importance=SimpleNamespace(value=share if importance is None else importance))

    def pair(a: str, b: str, share: float):
        return SimpleNamespace(features=(a, b), share=SimpleNamespace(value=share), importance=SimpleNamespace(value=share))

    t = SimpleNamespace(features=[term("a", 0.6), term("b", 0.3), term("noise", 0.0)], pairs=[pair("a", "b", 0.1)])
    m = SimpleNamespace(features=[term("a", 0.5), term("b", 0.2), term("noise", 0.05)], pairs=[pair("b", "a", 0.15), pair("a", "noise", 0.1)])
    out = d.spurious(m, t)
    assert (out["pairs"], out["planted pairs fitted"], out["spurious mains"]) == (2, 1, "noise")
    assert np.isclose(out["share on spurious mains"], 0.05) and np.isclose(out["share on spurious pairs"], 0.1)
    assert np.isclose(out["share on terms not planted"], 0.15) and np.isclose(out["share on planted pairs"], 0.15) and np.isclose(out["shares sum"], 1.0)


def test_opposite_verdicts_need_a_decision_from_both_models():
    verdicts = pd.DataFrame({"EBM": ["true", "false", "true", "undecidable", "true"], "XGB2": ["false", "true", "true", "false", "undecidable"]})
    out = d.opposite_verdicts(verdicts)
    assert out["decided by both"].tolist() == [True, True, True, False, False]
    assert out.opposite.tolist() == [True, True, False, False, False]


def test_d74s_runs_are_rebuilt_from_the_cache():
    """Each kind of exit: the writer's answers and the gate's extractions found are the run's calls, the readings the
    round trips' and rows.csv's (deferred.rebuild raises otherwise)."""
    runs = e3.RESULTS / d.SOURCE / d.WRITER_ARM / "runs"
    if not runs.exists() or not CACHE.exists() or not all(path(s, "XGB2").with_suffix(".npz").exists() for s in tiers.SCENARIOS):
        pytest.skip("D74's runs, the LLM cache or the Facts are not on disk (see the README)")
    d.check_configuration()
    rows = pd.read_csv(runs.parent / "rows.csv").set_index("run")
    entries = d.traces()
    picked = {}
    for e in entries:
        picked.setdefault((e["tier"], e["trace"]["exit"]), e)
    for e in picked.values():
        d.rebuild(e, rows)
        assert len(e["writer"]) + sum(len(x["answers"]) for x in e["gate"].values()) == e["trace"]["calls"]
    assert {exit_state for _, exit_state in picked} == {"RELEASED", "RELEASED_REDUCED", "TEMPLATE"}
