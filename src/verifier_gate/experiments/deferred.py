"""The sizes of the defects D75 deferred to the thesis, measured on D74's E3 run (D75; the review of 20 Oct, minor
issues 2 to 9, 15 and 16, and M2 point 4).

D75 froze the gate for the working paper in D74's configuration and deferred the review items that would change a
verdict, a handover, a template or a prompt: the paper reports the size of each, measured on D74's run
(results/e3/v4-x5-m5-d74/), and the thesis fixes them. This script measures them offline, at $0. It reads the run's
traces (haiku/runs/), rows.csv and claims.csv, the LLM answers behind the traces (cache/llm/<key>.json, read as files:
no request is sent and the call log is not written), the fitted models' Facts (cache/facts/) and E1's verdicts
(results/e1/v3-d74/). It changes no input.

Every count leaves out the two pilot datasets (items 9 and 10 list them in their detail, flagged) and is given per
tier: synthetic (namings plausible and opaque) and plasmode (the column codes). The answers are rebuilt from the
traces, and the script stops if they do not reproduce the run: per run, the writer's answers and the gate's
extractions must be the run's calls; per round trip, the readings and their format errors must be the trace's, and
the digit test its unchecked numbers; per scored text, the readings must be rows.csv's; the ranks recomputed from
the refits' importances must be the stored ones.

1. Stop rules (minor issue 9). How each run ended, from its trace's events and versions (gate.py): released after k
   repair rounds; repairs stopped by no progress, by the repair rounds (2) or by the call budget (16 calls), then the
   drop step (the rest released, or the template: nothing to drop, no sentence left, the reduced text no longer covers
   a required term, the reduced text fails its round trip or has too few readings, no calls left for it); the template
   after a round trip with fewer than two readings, or with no draft after the format-only retry. Also the format-only
   retries by cause, the extraction retries (round trips and answers) and those the budget prevented, and the template
   exits: no template is round-tripped, and some runs never round-tripped any text.
2. Rank ties (minor issue 2). Global ranks break ties by the features' order (facts/build.py). Per fitted model:
   features whose importance in M exactly equals another feature's, and features whose refit rank band differs under
   competition ranks (tied features share the best rank; M's and each refit's ranks recomputed from the stored
   importances, which reproduce the stored ranks). For the rank claims of the released LLM-written texts (plans, the
   gate's final readings, the scoring readings), the templates and the H2 statements: those about a feature tied in M,
   and those whose verdict changes under competition ranks; the texts and handovers affected. Also the handovers whose
   printed rank range, and the H2 handovers whose certified rank statement (verifier/certified.py), would change.
3. DSL robustness (minor issue 3). Every DSL line the writers and readers produced, each LLM answer once (the
   writers' answers, the gate's extractions, the scoring readings): lines with a repeated keyword argument, with a
   non-finite number (a literal such as 1e999 parses to inf; nan or inf written as a word), rank sets that cover every
   rank from 1 to the number of features (always true), and lines whose parse raises an error other than DSLError;
   runs that ended without an exit state (an error escaping DSLError aborts a run).
4. Count steps (minor issue 4). Released template texts and H2 handovers (each distinct handover once, and the runs
   whose writer saw it) with a step (threshold, drop, peak) on a count feature, written "= <value>" instead of by its
   gap. A count feature: M's Facts keep its observed values (at most 128 distinct, D42) and all are whole numbers.
5. Emphasis rule (minor issue 5). Gate round trips that checked it (drafts; a reduced text is not checked) and fired;
   scored texts where it fired (rows.csv).
6. Numbers in words (minor issue 6). In the released LLM-written texts: texts and sentences that state a count or a
   value in words (COUNT_IN_WORDS, case-insensitive), which the digit test (gate/roundtrip.NUMBER) does not see, and
   those of these sentences whose content the gate's final readings put beyond the DSL in words (2 or more readings),
   which then passed unchecked; texts whose only digits sit inside feature codes (the names shown to the writer that
   hold a digit: PAY_0, BILL_AMT1, ...), which the digit test counts as numbers, and, recomputed from the readings, the
   sentences that fail the digit test only through a feature code, in every gate round trip and in the scoring of the
   released LLM-written texts.
7. Unparsed DSL lines (minor issue 7). In the gate's final readings of the released LLM-written texts: DSL lines that
   do not parse (dropped), and lines filed under a sentence id the text does not have (dropped unparsed); the hedges
   among them. The scoring readings of the same texts apart.
8. Reading counts (minor issue 8). The claims of the final round trip of the released LLM-written texts by the number
   of readings that found them: 1, 2 or 3 of 3 (1 or 2 of 2 where an answer was not a reading); hedges apart; planned
   claims no reading found.
9. Spurious share (M2 point 4 and fix 5; minor issue 15). Per fitted model, the share of M's importance on terms T
   does not plant (main terms with no importance in T, pairs T does not have), and M's number of pair terms; per tier
   and model class, mean, min and max.
10. Model multiplicity (minor issue 16). E1's planted claims certified (true) for one model class and refuted (false)
    for the other on the same dataset, per tier and n, with examples.

Writes results/e3/v4-x5-m5-d74/deferred/: summary.csv (one row per quantity: item, tier, quantity, count, denominator,
share, note; share is count / denominator unless the quantity names a statistic) and per item a detail CSV.

Run:
  uv run python -m verifier_gate.experiments.deferred
"""

import argparse
import ast
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import replace
from functools import cache
from pathlib import Path

import numpy as np
import pandas as pd

from verifier_gate.data import labels, tiers
from verifier_gate.dsl.grammar import HEDGE, LOCATED, Claim
from verifier_gate.dsl.parse import DSLError, parse
from verifier_gate.experiments import e3_end_to_end as e3
from verifier_gate.experiments.build_facts import load
from verifier_gate.facts import build
from verifier_gate.facts.schema import Estimate, Facts, FeatureFacts
from verifier_gate.gate import gate as g
from verifier_gate.gate import roundtrip as rt
from verifier_gate.lexicon import predicates as p
from verifier_gate.lexicon import words
from verifier_gate.llm import extract, prompts
from verifier_gate.llm.client import CACHE, Request, Response, interpret
from verifier_gate.verifier import certified
from verifier_gate.verifier.verify import verify

SOURCE = "v4-x5-m5-d74"  # D74's E3 run, the one the paper reports (D75)
WRITER_ARM = "haiku"
TIERS = ("synthetic", "plasmode")
E1 = Path(__file__).parents[3] / "results" / "e1" / "v3-d74"
E1_SETS = ("discovery", "confirmation", "plasmode")
RELEASED_LLM = (g.RELEASED, g.RELEASED_REDUCED)
ITEMS = {1: "1 stop rules", 2: "2 rank ties", 3: "3 DSL robustness", 4: "4 count steps", 5: "5 emphasis rule", 6: "6 numbers in words",
         7: "7 unparsed DSL lines", 8: "8 reading counts", 9: "9 spurious share", 10: "10 model multiplicity"}  # fmt: skip

# Item 6: a count or a value in words, matched case-insensitively in each sentence: a number word (NUMBER_WORDS) with a
# feature's unit, a range of values, a bound, a value reached, or a fraction of something. Left out: "two months before"
# (it names a feature's month, PAY_AMT3), counts of features ("two features"), ranks ("the three most important
# features", "a third or fourth most important feature", "the lower half"), and "one" as a pronoun.
NUMBER_WORDS = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
                "twenty", "thirty", "forty", "fifty", "hundred", "thousand", "single")  # fmt: skip
_NUM = rf"(?:{'|'.join(NUMBER_WORDS)})"
_UNIT = r"(?:delinquenc(?:y|ies)|inquir(?:y|ies)|dependents?|months?(?:'s)?|years?|payments?|units?|points?|percent|dollars?)"
_FRACTION = r"(?:halves|half|thirds?|quarters?|fifths?|tenths?)"
COUNT_IN_WORDS = {
    "number word and unit": rf"\b{_NUM}(?:\s+(?:or|to|and)\s+(?:{_NUM}|more|fewer|less))?(?:[\s-]+(?:past|recent|late|missed|more|additional|log|odds|log-odds))*"
                            rf"[\s-]+{_UNIT}\b(?!\s+before)",
    "range of values": rf"\b(?:from|between|at)\s+(?:(?:roughly|about|around)\s+)?(?:{_NUM}|none|no)(?:\s+{_UNIT})?\s+(?:to|and|versus|or)\s+(?:{_NUM}|more)\b",
    "bound": rf"\b(?:at\s+least|at\s+most|more\s+than|fewer\s+than|less\s+than|up\s+to)\s+{_NUM}\b",
    "value reached": rf"\b(?:reaches|reached|reach|exceeds|exceed|above|below|past|over|under|equals)\s+{_NUM}\b(?!\s+(?:of|most|least|features?|attributes?)\b)"
                     rf"|\bis\s+zero\b",
    "fraction": rf"\b(?:{_NUM}|a)[\s-]+{_FRACTION}\b(?=\s+of\b|\s*[.,;:)]|\s*$|\s+and\s+(?:{_NUM}|a)[\s-]+{_FRACTION}\b)",
}  # fmt: skip
COUNT_PATTERNS = {name: re.compile(pattern, re.IGNORECASE) for name, pattern in COUNT_IN_WORDS.items()}
NON_FINITE_WORD = re.compile(r"\b(?:nan|inf|infinity)\b", re.IGNORECASE)
HEDGE_LINE = re.compile(rf"^\s*{HEDGE}\s*\(")
STATEMENT = re.compile(r"^- (.+?)  \((.+)\)$")  # an H2 statement: "- <DSL>  (<words>)" (llm/handover.py)
H2_HEADER = "Statements the verifier certifies for this model"


def out_folder(source: str = SOURCE) -> Path:
    return e3.RESULTS / source / "deferred"


def check_configuration() -> p.Lexicon:
    """D74's configuration (D75): lexicon v3 with D74's fixes, writer prompts v4, extractor x5. Under another, the
    rebuilt requests and verdicts would not be the run's."""
    lex = p.load()
    if lex.version != "v3" or not p.d74_fixes(lex) or prompts.VERSION != "v4" or prompts.extractor_version() != "x5":
        raise SystemExit(f"D74 ran under lexicon v3 with D74's fixes, prompts v4 and extractor x5; found lexicon {lex.version}, "
                         f"fixes {p.d74_fixes(lex)}, prompts {prompts.VERSION}, extractor {prompts.extractor_version()}")  # fmt: skip
    return lex


def row(item: int, tier: str, quantity: str, count, denominator=None, note: str = "", share: float | None = None) -> dict:
    """A line of summary.csv; share is count / denominator unless given (a statistic)."""
    if share is None and denominator:
        share = count / denominator
    return {"item": ITEMS[item], "tier": tier, "quantity": quantity, "count": count, "denominator": denominator,
            "share": None if share is None else round(float(share), 4), "note": note}  # fmt: skip


def counted(counter: Counter) -> str:
    return "; ".join(f"{k}: {v}" for k, v in sorted(counter.items(), key=lambda kv: (-kv[1], str(kv[0]))))


# --- the run and its answers ------------------------------------------------------------------------------------


@cache
def facts_of(scenario: str, kind: str) -> Facts:
    """M (EBM, XGB2) with its refit draws, or T."""
    return load(tiers.scenario(scenario), kind)


def traces(source: str = SOURCE) -> list[dict]:
    """The runs outside the pilot datasets, in run order, each with its cell and its trace."""
    out = []
    for path in sorted((e3.RESULTS / source / WRITER_ARM / "runs").glob("*.json")):
        trace = json.loads(path.read_text())
        scenario, model, variant, draw, _, naming = trace["run_id"].split("_")
        if scenario in e3.PILOT:
            continue
        out.append({"run": trace["run_id"], "scenario": scenario, "tier": tiers.name(tiers.scenario(scenario)), "model": model,
                    "handover": variant, "draw": int(draw.lstrip("d")), "naming": naming, "trace": trace})  # fmt: skip
    return out


def cached(request: Request) -> Response | None:
    """The cached answer to a request, read as a file: Client.lookup would append to the call log."""
    path = CACHE / f"{request.key}.json"
    if not path.exists():
        return None
    stored = json.loads(path.read_text())
    return interpret(request, stored["raw"], stored["latency"], cached=True)


def writer_answers(trace: dict) -> list[Response]:
    """The writer's answers in a run: one per turn of its conversation (the last writer request's messages), and the
    format-only retry of a turn (attempt 1) where one was made."""
    w = trace["writer"]
    messages = tuple(tuple(m) for m in w["messages"])
    out = []
    for end in range(1, len(messages) + 1, 2):
        for attempt in range(3):
            request = Request(w["role"], w["model"], w["system"], messages[:end], w["schema"], w["effort"], w["thinking"], w["max_tokens"], w["draw"], attempt)
            if (answer := cached(request)) is not None:
                out.append(answer)
    return out


def passed(version: dict) -> bool:
    """A version's plan check passed (gate.Version.passed)."""
    return all(c[2] == p.TRUE for c in version["claims"]) and not version["format_errors"] and not version["missing"]


def round_tripped(trace: dict) -> list[int]:
    """The versions the gate sent to the extractor: every version whose plan passed (gate._roundtrip), except the one
    appended before the template when no calls were left. A round trip that could not run left no round trip in its
    version."""
    versions, out = trace["versions"], []
    no_calls = any(e.startswith("no calls left for the round trip") for e in trace["events"])
    for i, v in enumerate(versions):
        if v["source"] == "template" or (no_calls and i == len(versions) - 2):
            continue
        if v["roundtrip"] is not None or passed(v):
            out.append(i)
    return out


def readings(sentences: list, requests: list[Request], names) -> dict:
    """A text's readings as the gate and E3's scoring took them: each replica's answer, or its retry (attempt 1) if
    the answer is not a reading and the retry was made. Also every answer found (each a call), and the answers that
    were not readings and got no retry."""
    ids = {i for i, _ in sentences}
    out = {"readings": [], "used": [], "answers": [], "not retried": 0}
    for request in requests:
        for attempt in (0, 1):
            answer = cached(replace(request, attempt=attempt))
            if answer is None:
                out["not retried"] += attempt == 1
                break
            out["answers"].append((answer.key, answer.data))
            try:
                out["readings"].append(extract.extraction_from(answer, ids, names))
                out["used"].append(answer.data)
                break
            except (ValueError, KeyError, TypeError):
                continue
    return out


def rebuild(entry: dict, rows: pd.DataFrame) -> None:
    """The run's answers from the cache (entry["writer"], ["gate"] by version index, ["scoring"] by arm), checked
    against the trace and rows.csv."""
    trace, facts = entry["trace"], facts_of(entry["scenario"], entry["model"])
    names, descriptions = e3.NAMES[entry["naming"]], e3.DESCRIPTIONS[entry["tier"]]
    features = extract.features_text(facts, names, descriptions)
    entry["writer"] = [(a.key, a.data) for a in writer_answers(trace)]
    entry["gate"] = {}
    for i in round_tripped(trace):
        v = trace["versions"][i]
        requests = [extract.extractor_request(v["sentences"], features, trace["writer"]["draw"], k) for k in range(extract.EXTRACTIONS)]
        entry["gate"][i] = readings(v["sentences"], requests, names)
        trip = v["roundtrip"]
        found = entry["gate"][i]["readings"]
        if trip is not None and (len(found) != trip["readings"] or sum(len(r.format_errors) for r in found) != trip["format_errors"]):
            raise ValueError(f"{entry['run']}, version {i}: the rebuilt readings are not the round trip's")
    calls = len(entry["writer"]) + sum(len(x["answers"]) for x in entry["gate"].values())
    if calls != trace["calls"]:
        raise ValueError(f"{entry['run']}: {calls} answers rebuilt for {trace['calls']} calls")
    ctx = g.Context(facts, [], names, descriptions=descriptions)
    entry["scoring"] = {}
    for arm, sentences in zip(("off", "on"), e3.texts_of(g.Run(**trace))):
        if not sentences:
            continue
        entry["scoring"][arm] = readings(sentences, e3.scoring_requests(sentences, ctx, entry["draw"]), names) | {"sentences": sentences}
        if len(entry["scoring"][arm]["readings"]) != int(rows.loc[entry["run"], f"{arm} readings"]):
            raise ValueError(f"{entry['run']} ({arm}): the rebuilt scoring readings are not rows.csv's")


def released_llm(entries: list[dict]) -> list[dict]:
    return [e for e in entries if e["trace"]["exit"] in RELEASED_LLM]


# --- 1. stop rules ----------------------------------------------------------------------------------------------


def stop_rule(reason: str) -> str:
    """The rule in a "stop repairing: <why>" event (gate._decide, _round_trip_answered, _format_problem)."""
    for marker, rule in (("no progress", "no progress"), ("repair rounds used", "repair rounds exhausted"),
                         ("call budget used", "call budget"), ("format problem after the retry", "format problem after the retry")):  # fmt: skip
        if marker in reason:
            return rule
    return reason


def stop_path(exit_state: str, rounds: int, events: list[str], versions: list[dict]) -> dict:
    """How a run ended: the stop rule that ended its repairs (if any), what the drop step did, and the path to its
    exit state, from its trace's events and versions (gate._reduce: a reduced text whose plan fails its check, mostly
    because it no longer covers a required term, goes to the template unannounced)."""
    stop = next((e for e in events if e.startswith("stop repairing: ")), None)
    rule = stop_rule(stop.removeprefix("stop repairing: ")) if stop else ""
    after = events[events.index(stop) + 1 :] if stop else events
    starts = lambda prefix: any(e.startswith(prefix) for e in after)  # noqa: E731
    sources = [v["source"] for v in versions]
    reduced = next((v for v in reversed(versions) if v["source"] == "reduced"), None)
    drop = ""
    if stop:
        if "nothing to drop" in after:
            drop = "nothing to drop"
        elif starts("round trip of the reduced text"):
            drop = ("the rest released" if exit_state == g.RELEASED_REDUCED else "the reduced text failed its round trip"
                    if "the reduced text failed its round trip" in after else "too few readings of the reduced text"
                    if starts("round trip could not run") else "the reduced text: other")  # fmt: skip
        elif starts("no calls left for the round trip"):
            drop = "no calls left for the reduced text's round trip"
        elif exit_state == g.TEMPLATE and reduced is None:
            drop = "no sentence left"
        elif exit_state == g.TEMPLATE:
            drop = "the reduced text no longer covers a required term" if reduced["missing"] else "the reduced plan failed its check"
    if exit_state == g.RELEASED:
        path = f"released after {rounds} repair round(s)"
    elif exit_state == g.RELEASED_REDUCED:
        path = f"sentences dropped after: {rule}"
    elif exit_state == g.TEMPLATE and stop:
        path = f"template after: {rule}; {drop}"
    elif exit_state == g.TEMPLATE and starts("round trip could not run"):
        path = "template: too few readings of a draft"
    elif exit_state == g.TEMPLATE and starts("no calls left for the round trip"):
        path = "template: no calls left for a draft's round trip"
    elif exit_state == g.TEMPLATE and sources == ["template"] and starts("format-only retry"):
        path = "template: no draft after the format-only retry"
    else:
        path = f"{exit_state.lower()}: {events[-1] if events else ''}"
    return {"stop rule": rule, "drop step": drop, "path": path}


def format_retries(events: list[str]) -> Counter:
    """The format-only retries of a run by cause: DSL lines that do not parse (gate._advance), or an answer that is
    not a draft, truncated, or not JSON (gate._format_problem)."""
    prefix = "format-only retry: "
    return Counter("DSL lines do not parse" if "do not parse" in e else e.removeprefix(prefix) for e in events if e.startswith(prefix))


def retries(events: list[str]) -> dict:
    """Format-only retries by cause, and extraction retries: round trips with one, and answers retried."""
    causes = format_retries(events)
    answers = [int(m.group(1)) for e in events if (m := re.match(r"extraction retry: (\d+) answer", e))]
    return {"format-only retries": sum(causes.values()), "format-only retry causes": counted(causes), "extraction retries": len(answers),
            "extraction answers retried": sum(answers)}  # fmt: skip


def item1(entries: list[dict]) -> tuple[pd.DataFrame, list[dict]]:
    table, causes = [], {tier: Counter() for tier in TIERS}
    for e in entries:
        t = e["trace"]
        events = t["events"]
        causes[e["tier"]].update(format_retries(events))
        table.append({"run": e["run"], "tier": e["tier"], "naming": e["naming"], "scenario": e["scenario"], "model": e["model"], "handover": e["handover"],
                      "draw": e["draw"], "exit": t["exit"], "rounds": t["rounds"], "calls": t["calls"]}
                     | stop_path(t["exit"], t["rounds"], events, t["versions"]) | retries(events)
                     | {"round trips": sum(x.startswith("round trip of the") for x in events), "too few readings": any(x.startswith("round trip could not run") for x in events),
                        "extraction answers": sum(len(x["answers"]) for x in e["gate"].values()),
                        "extraction retries prevented by the budget": sum(x["not retried"] for x in e["gate"].values())})  # fmt: skip
    table = pd.DataFrame(table)
    out = []
    for tier in TIERS:
        part = table[table.tier == tier]
        n = len(part)
        out.append(row(1, tier, "runs", n, n))
        for state in (g.RELEASED, g.RELEASED_REDUCED, g.TEMPLATE, g.ESCALATE):
            out.append(row(1, tier, f"exit {state}", int((part.exit == state).sum()), n))
        for path, k in sorted(part.path.value_counts().items()):
            out.append(row(1, tier, f"path: {path}", int(k), n))
        rules = part["stop rule"].value_counts()
        out.append(row(1, tier, "repairs stopped by the no-progress rule", int(rules.get("no progress", 0)), n, "then the drop step"))
        out.append(row(1, tier, "repairs stopped after 2 repair rounds", int(rules.get("repair rounds exhausted", 0)), n, "then the drop step"))
        budget = part.path.str.contains("call budget|no calls left")
        prevented = part[part["extraction retries prevented by the budget"] > 0]
        out.append(row(1, tier, "runs ended by the 16-call budget", int(budget.sum()), n,
                       f"'call budget used' {int(rules.get('call budget', 0))}; 'no calls left for the round trip' "
                       f"{int(part.path.str.contains('no calls left').sum())}; runs at 16 calls {int((part.calls >= g.CALL_BUDGET).sum())}"))  # fmt: skip
        out.append(row(1, tier, "runs in which the call budget prevented an extraction retry", len(prevented), n,
                       f"then too few readings: {int(prevented.path.str.contains('too few readings').sum())} "
                       f"({', '.join(prevented[prevented.path.str.contains('too few readings')].run)})"))  # fmt: skip
        out.append(row(1, tier, "runs with a round trip that could not run (fewer than 2 readings)", int(part["too few readings"].sum()), n))
        out.append(row(1, tier, "format-only retries", int(part["format-only retries"].sum()), n, f"denominator: runs; by cause: {counted(causes[tier])}"))
        out.append(row(1, tier, "runs with a format-only retry", int((part["format-only retries"] > 0).sum()), n))
        out.append(row(1, tier, "extraction retries (round trips with an answer retried)", int(part["extraction retries"].sum()), int(part["round trips"].sum()),
                       "denominator: the gate's round trips"))  # fmt: skip
        out.append(row(1, tier, "extraction answers retried", int(part["extraction answers retried"].sum()), int(part["extraction answers"].sum()),
                       f"denominator: the gate's extraction calls; {int(part['extraction retries prevented by the budget'].sum())} retries the call budget prevented"))  # fmt: skip
        templates = part[part.exit == g.TEMPLATE]
        out.append(row(1, tier, "template exits (a template text is never round-tripped)", len(templates), n))
        out.append(row(1, tier, "template exits of runs that round-tripped no text at all", int((templates["round trips"] == 0).sum()), len(templates),
                       "denominator: template exits"))  # fmt: skip
    return table, out


# --- 2. rank ties -----------------------------------------------------------------------------------------------


def ordinal_ranks(importance: np.ndarray) -> np.ndarray:
    """Ranks as facts/build.py gives them: by importance, ties broken by the features' order (a stable sort). Rows:
    M or the refits; columns: the features in the Facts' order."""
    imp = np.atleast_2d(np.asarray(importance, dtype=np.float64))
    greater = (imp[:, None, :] > imp[:, :, None]).sum(axis=2)
    earlier_equal = np.stack([(imp[:, :i] == imp[:, [i]]).sum(axis=1) for i in range(imp.shape[1])], axis=1)
    return greater + earlier_equal + 1


def competition_ranks(importance: np.ndarray) -> np.ndarray:
    """Competition ranks ("1224"): tied features share the best rank of their group."""
    imp = np.atleast_2d(np.asarray(importance, dtype=np.float64))
    return (imp[:, None, :] > imp[:, :, None]).sum(axis=2) + 1


def tied(importance: np.ndarray) -> np.ndarray:
    """Per row and feature: another feature has exactly the same importance."""
    imp = np.atleast_2d(np.asarray(importance, dtype=np.float64))
    return (imp[:, None, :] == imp[:, :, None]).sum(axis=2) > 1


@cache
def competition_facts(scenario: str, model: str) -> Facts:
    """M's Facts with competition ranks: M's rank, and the refits' rank band as built (2.5th and 97.5th percentile).
    Stops if the ranks recomputed from the stored importances are not the stored ranks and bands."""
    facts = facts_of(scenario, model)
    names = [f.name for f in facts.features]
    own = np.array([f.importance.value for f in facts.features])
    refits = np.stack([facts.draws.importance[n] for n in names], axis=1)
    stored = np.stack([facts.draws.rank[n] for n in names], axis=1)
    bands = [build.percentile_band(stored[:, i]) for i in range(len(names))]
    if not (np.array_equal(ordinal_ranks(refits), stored) and np.array_equal(ordinal_ranks(own)[0], [f.rank.value for f in facts.features])
            and all(tuple(f.rank.band) == b for f, b in zip(facts.features, bands))):  # fmt: skip
        raise ValueError(f"{scenario} {model}: the ranks recomputed from the importances are not the stored ones")
    m_rank, r_rank = competition_ranks(own)[0], competition_ranks(refits)
    features = tuple(replace(f, rank=Estimate(float(m_rank[i]), build.percentile_band(r_rank[:, i].astype(np.float64)))) for i, f in enumerate(facts.features))
    return Facts(facts.model, facts.bands, facts.intercept, features, facts.pairs, facts.draws)


def rank_models(scenarios: list[str]) -> pd.DataFrame:
    """Per fitted model and feature: an exact tie in M, refits with a tie, and the rank band in both rankings."""
    out = []
    for scenario in scenarios:
        for model in e3.MODELS:
            facts, comp = facts_of(scenario, model), competition_facts(scenario, model)
            names = [f.name for f in facts.features]
            own = np.array([f.importance.value for f in facts.features])
            refits = np.stack([facts.draws.importance[n] for n in names], axis=1)
            in_m, in_refits = tied(own)[0], tied(refits).sum(axis=0)
            for i, (f, c) in enumerate(zip(facts.features, comp.features)):
                band, cband = p._rank_band(f), p._rank_band(c)
                out.append({"tier": tiers.name(tiers.scenario(scenario)), "scenario": scenario, "model": model, "feature": f.name, "importance": f.importance.value,
                            "rank": f.rank.value, "competition rank": c.rank.value, "tied in M": bool(in_m[i]), "refits with a tie": int(in_refits[i]),
                            "rank band": f"{band[0]:g} to {band[1]:g}", "competition rank band": f"{cband[0]:g} to {cband[1]:g}", "band differs": band != cband})  # fmt: skip
    return pd.DataFrame(out)


def h2_statements(handover: str) -> list[tuple[str, str]]:
    """The certified statements of an H2 handover as listed: (DSL line in the writer's names, words)."""
    if H2_HEADER not in handover:
        return []
    lines = handover.split(H2_HEADER, 1)[1].splitlines()[1:]
    return [(m.group(1), m.group(2)) for line in lines if (m := STATEMENT.match(line))]


def handovers(entries: list[dict]) -> dict[tuple, dict]:
    """The distinct H2 handovers (dataset, model, naming): their text as the writer saw it and the runs that saw it."""
    out = {}
    for e in entries:
        if e["handover"] != "H2":
            continue
        text = e["trace"]["writer"]["messages"][0][1]
        key = (e["tier"], e["scenario"], e["model"], e["naming"])
        if key in out and out[key]["text"] != text:
            raise ValueError(f"{key}: two runs of one cell saw different handovers")
        out.setdefault(key, {"text": text, "runs": []})["runs"].append(e["run"])
    return out


def rank_claim(line: str) -> Claim | None:
    """The line as a rank claim (or a hedged one), else None."""
    try:
        claim = parse(line)
    except DSLError:
        return None
    inner = claim.inner if claim.kind == HEDGE else claim
    return claim if inner.kind == "rank" else None


def item2(entries: list[dict], source: str = SOURCE) -> tuple[pd.DataFrame, pd.DataFrame, list[dict]]:
    scoring = pd.read_csv(e3.RESULTS / source / "claims.csv")
    scoring = scoring[(scoring.writer == WRITER_ARM) & (scoring.arm == "on")].groupby("run").dsl.agg(list).to_dict()
    claims = []  # (scope, tier, text, scenario, model, line in the Facts' names)
    for e in entries:
        t, last = e["trace"], e["trace"]["versions"][-1] if e["trace"]["versions"] else None
        base = (e["tier"], e["run"], e["scenario"], e["model"])
        if t["exit"] in RELEASED_LLM:
            trip = last["roundtrip"]
            claims += [("plan, released LLM-written", *base, c[1]) for c in last["claims"]]
            claims += [("gate's final readings, released LLM-written", *base, line) for _, line, *_ in trip["extracted"] + trip["ambiguous"]]
            claims += [("scoring readings, released LLM-written", *base, line) for line in scoring.get(e["run"], [])]
        elif t["exit"] == g.TEMPLATE:
            claims += [("template", *base, c[1]) for c in last["claims"]]
    for (tier, scenario, model, naming), h in sorted(handovers(entries).items()):
        cell = f"{scenario}_{model}_H2_{naming}"
        claims += [("H2 statements", tier, cell, scenario, model, str(labels.internal(parse(line), e3.NAMES[naming]))) for line, _ in h2_statements(h["text"])]
    scopes = Counter((c[0], c[1]) for c in claims)
    texts = defaultdict(set)
    for scope, tier, text, *_ in claims:
        texts[scope, tier].add(text)
    detail = []
    for scope, tier, text, scenario, model, line in claims:
        claim = rank_claim(line)
        if claim is None:
            continue
        inner = claim.inner if claim.kind == HEDGE else claim
        facts, comp = facts_of(scenario, model), competition_facts(scenario, model)
        imp = {f.name: f.importance.value for f in facts.features}
        feature = inner.terms[0]
        ties = [f for f, v in imp.items() if f != feature and feature in imp and v == imp[feature]]
        verdict, other = verify(claim, facts).value, verify(claim, comp).value
        detail.append({"scope": scope, "tier": tier, "text": text, "scenario": scenario, "model": model, "claim": line, "feature": feature,
                       "tied in M with": ", ".join(ties), "verdict": verdict, "verdict, competition ranks": other, "changes": verdict != other})  # fmt: skip
    detail = pd.DataFrame(detail)
    models = rank_models(sorted({e["scenario"] for e in entries}))
    lex, changed = p.load(), defaultdict(list)  # (dataset, model): the features whose rank band, and certified rank statement, would change
    for r in models[models["band differs"]].to_dict("records"):
        facts, comp = facts_of(r["scenario"], r["model"]), competition_facts(r["scenario"], r["model"])
        ladder = certified.rank_ladder(r["feature"], len(facts.features))
        changed[r["scenario"], r["model"]].append(r | {"statement": str(certified.first_certified(ladder, facts, lex)),
                                                       "competition statement": str(certified.first_certified(ladder, comp, lex))})  # fmt: skip
    h2 = handovers(entries)
    out = []
    for tier in TIERS:
        m = models[models.tier == tier]
        per_model = m.groupby(["scenario", "model"])
        n_models = per_model.ngroups
        out.append(row(2, tier, "fitted models with an exact importance tie between two features in M", int(per_model["tied in M"].any().sum()), n_models))
        refit_ties = per_model["refits with a tie"].max() > 0
        out.append(row(2, tier, "fitted models with an exact tie in at least one refit", int(refit_ties.sum()), n_models,
                       counted(Counter(k[1] for k, v in refit_ties.items() if v))))  # fmt: skip
        differs = m[m["band differs"]]
        out.append(row(2, tier, "features whose refit rank band differs under competition ranks", len(differs), len(m),
                       "; ".join(f"{r.scenario} {r.model} {r.feature}: {r['rank band']} -> {r['competition rank band']}" for _, r in differs.iterrows())))  # fmt: skip
        d = detail[detail.tier == tier] if len(detail) else detail
        n_rank = len(d)
        all_texts = set().union(*(texts[s, tier] for s, t in texts if t == tier))
        on_tied = d[d["tied in M with"] != ""] if n_rank else d
        out.append(row(2, tier, "rank claims about a feature tied in M", len(on_tied), n_rank,
                       f"texts and handovers affected: {on_tied.text.nunique() if len(on_tied) else 0} of {len(all_texts)}"))  # fmt: skip
        changes = d[d.changes] if n_rank else d
        out.append(row(2, tier, "rank claims whose verdict changes under competition ranks", len(changes), n_rank,
                       f"texts and handovers affected: {changes.text.nunique() if len(changes) else 0} of {len(all_texts)}"
                       + ("; " + "; ".join(f"{r.text}: {r.claim} {r.verdict} -> {r['verdict, competition ranks']}" for _, r in changes.iterrows()) if len(changes) else "")))  # fmt: skip
        runs = [e for e in entries if e["tier"] == tier]
        cells = {(e["scenario"], e["model"], e["handover"], e["naming"]) for e in runs}
        hit = {c for c in cells if c[:2] in changed}
        ranges = "; ".join(f"{s} {m_} {c['feature']}: rank {c['rank band']} -> {c['competition rank band']}" for (s, m_), cs in sorted(changed.items())
                           if tiers.name(tiers.scenario(s)) == tier for c in cs)  # fmt: skip
        out.append(row(2, tier, "handovers (H1 and H2) that print a rank range competition ranks would change", len(hit), len(cells),
                       f"runs whose writer saw one: {sum((e['scenario'], e['model']) in changed for e in runs)} of {len(runs)}; {ranges}"))  # fmt: skip
        listed = {key: {str(labels.internal(parse(line), e3.NAMES[key[3]])) for line, _ in h2_statements(v["text"])} for key, v in h2.items() if key[0] == tier}
        moved = [(key, c) for key in sorted(listed) for c in changed.get(key[1:3], [])
                 if c["statement"] != c["competition statement"] and c["statement"] in listed[key]]  # fmt: skip
        out.append(row(2, tier, "H2 handovers whose certified rank statement competition ranks would change", len({k for k, _ in moved}), len(listed),
                       "; ".join(f"{k[1]} {k[2]} ({k[3]}): {c['statement']} -> {c['competition statement']}" for k, c in moved)))  # fmt: skip
        for scope in sorted({s for s, t in scopes if t == tier}):
            part = d[d.scope == scope] if n_rank else d
            out.append(row(2, tier, f"rank claims in: {scope}", len(part), scopes[scope, tier],
                           f"denominator: all claims there; texts {len(texts[scope, tier])}; verdict changes {int(part.changes.sum()) if len(part) else 0}"))  # fmt: skip
    return detail, models, out


# --- 3. DSL robustness ------------------------------------------------------------------------------------------


def dsl_lines(data, role: str) -> list[tuple]:
    """The DSL lines of an answer as written: (sentence id, line), a writer's claims or an extraction's per sentence."""
    if not isinstance(data, dict):
        return []
    if role == "writer":
        return [(c.get("sentence_id"), str(c.get("dsl", "")).strip()) for c in data.get("claims") or [] if isinstance(c, dict)]
    return [(s.get("id"), str(x).strip()) for s in data.get("sentences") or [] if isinstance(s, dict) for x in s.get("claims") or []]


DEFECTS = ("repeated keyword", "non-finite number", "nan or inf as a word", "vacuous rank set")


def line_defects(line: str, features: int) -> dict:
    """What minor issue 3 names, in one DSL line, and how the parser takes it: a repeated keyword argument, a
    non-finite number (a numeric literal that is inf or nan, such as 1e999; nan or inf as a word), a rank set (or a
    hedged one) and whether it covers every rank from 1 to `features` (always true), and the parse: accepted,
    DSLError, or the name of another error."""
    out = {"repeated keyword": False, "non-finite number": False, "nan or inf as a word": bool(NON_FINITE_WORD.search(line))}
    try:
        tree = ast.parse(line.strip(), mode="eval")
    except (SyntaxError, ValueError, MemoryError, RecursionError):
        tree = None
    for node in ast.walk(tree) if tree is not None else ():
        if isinstance(node, ast.Call):
            keys = [k.arg for k in node.keywords if k.arg is not None]
            out["repeated keyword"] |= len(keys) != len(set(keys))
        if isinstance(node, ast.Constant) and isinstance(node.value, float) and not math.isfinite(node.value):
            out["non-finite number"] = True
    claim = None
    try:
        claim = parse(line)
        out["parse"] = "accepted"
    except DSLError:
        out["parse"] = "DSLError"
    except Exception as e:  # noqa: BLE001  what minor issue 3 is about: an error that escapes DSLError
        out["parse"] = type(e).__name__
    inner = claim.inner if claim is not None and claim.kind == HEDGE else claim
    out["rank set"] = bool(inner is not None and inner.kind == "rank" and isinstance(inner.value, tuple))
    out["vacuous rank set"] = out["rank set"] and set(range(1, features + 1)) <= set(inner.value)
    return out


def counted_lines(entries: list[dict], source: str = SOURCE) -> set[tuple[str, str]]:
    """(run, canonical line) of every claim counted (found by at least 2 readings) in one of the run's round trips or
    scorings."""
    out = {(e["run"], line) for e in entries for v in e["trace"]["versions"] if v["roundtrip"] for _, line, _ in v["roundtrip"]["extracted"]}
    scored = pd.read_csv(e3.RESULTS / source / "claims.csv")
    return out | set(zip(scored.run, scored.dsl))


def canonical_line(line: str, naming: str) -> str:
    """A line in the writer's names as the round trip compares it: in the Facts' names, canonical (gate/roundtrip.py)."""
    return rt.canonical(labels.internal(parse(line), e3.NAMES[naming]))


def item3(entries: list[dict], source: str = SOURCE) -> tuple[pd.DataFrame, pd.DataFrame, list[dict]]:
    answers = {}  # key: (tier, role, run, data), each answer once
    for e in entries:
        for key, data in e["writer"]:
            answers.setdefault(key, (e["tier"], "writer", e["run"], data))
        for x in e["gate"].values():
            for key, data in x["answers"]:
                answers.setdefault(key, (e["tier"], "gate reader", e["run"], data))
        for x in e["scoring"].values():
            for key, data in x["answers"]:
                answers.setdefault(key, (e["tier"], "scoring reader", e["run"], data))
    flagged, counts = [], Counter()
    for key, (tier, role, run, data) in sorted(answers.items()):
        counts[tier, role, "answers"] += 1
        features = len(facts_of(*run.split("_")[:2]).features)
        for sid, line in dsl_lines(data, role):
            d = line_defects(line, features)
            counts[tier, role, "lines"] += 1
            counts[tier, role, "parse: " + (d["parse"] if d["parse"] in ("accepted", "DSLError") else "other error")] += 1
            counts[tier, role, "rank sets"] += d["rank set"]
            for k in DEFECTS:
                counts[tier, role, k] += d[k]
                counts[tier, role, f"{k}, accepted"] += d[k] and d["parse"] == "accepted"
            if any(d[k] for k in DEFECTS) or d["parse"] not in ("accepted", "DSLError"):
                flagged.append({"tier": tier, "reader or writer": role, "run": run, "answer": key, "sentence id": sid, "line": line} | d)
    flagged = pd.DataFrame(flagged, columns=["tier", "reader or writer", "run", "answer", "sentence id", "line", *DEFECTS, "rank set", "parse"])
    roles = ("writer", "gate reader", "scoring reader")
    kinds = ("answers", "lines", "parse: accepted", "parse: DSLError", "parse: other error", "rank sets", *(k for d in DEFECTS for k in (d, f"{d}, accepted")))
    table = pd.DataFrame([{"tier": tier, "reader or writer": role} | {k: counts[tier, role, k] for k in kinds} for tier in TIERS for role in roles])
    in_claims, naming = counted_lines(entries, source), {e["run"]: e["naming"] for e in entries}
    out = []
    for tier in TIERS:
        part = table[table.tier == tier].set_index("reader or writer")
        lines = int(part.lines.sum())
        per_role = "; ".join(f"{r}: {int(part.loc[r, 'lines'])} lines in {int(part.loc[r, 'answers'])} answers" for r in roles)
        out.append(row(3, tier, "DSL lines (each LLM answer once)", lines, lines, per_role))
        for k, quantity in (("repeated keyword", "lines with a repeated keyword argument"), ("non-finite number", "lines with a non-finite number literal (inf, nan)"),
                            ("nan or inf as a word", "lines with nan or inf written as a word")):  # fmt: skip
            out.append(row(3, tier, quantity, int(part[k].sum()), lines, f"accepted by the parser: {int(part[f'{k}, accepted'].sum())}"))
        f = flagged[(flagged.tier == tier) & flagged["vacuous rank set"]]
        counted_in = sorted({r.run for r in f.itertuples() if (r.run, canonical_line(r.line, naming[r.run])) in in_claims})
        out.append(row(3, tier, "rank sets that cover every rank (vacuous: always true)", len(f), int(part["rank sets"].sum()),
                       f"denominator: rank sets (hedged ones included); accepted by the parser: {int(f['parse'].eq('accepted').sum())}; by "
                       f"{counted(Counter(f['reader or writer']))}; hedged: {int(f.line.str.match(HEDGE_LINE.pattern).sum())}; counted as a claim "
                       f"(2 or more readings) in {len(counted_in)} run(s)" + (f": {', '.join(counted_in)}" if counted_in else "")))  # fmt: skip
        out.append(row(3, tier, "lines whose parse raises an error other than DSLError", int(part["parse: other error"].sum()), lines))
        runs = [e for e in entries if e["tier"] == tier]
        out.append(row(3, tier, "runs that ended without an exit state (a parser error escaping DSLError aborts the run)",
                       sum(e["trace"]["exit"] not in (g.RELEASED, g.RELEASED_REDUCED, g.TEMPLATE, g.ESCALATE) for e in runs), len(runs)))  # fmt: skip
    return flagged, table, out


# --- 4. count steps ---------------------------------------------------------------------------------------------


def count_feature(f: FeatureFacts) -> bool:
    """A feature whose location is judged on the gaps between its observed values (D42) and whose values are all
    whole numbers: a count or a code."""
    return f.values is not None and len(f.values) >= 2 and bool(np.all(f.values == np.round(f.values)))


def step_on_count(claim: Claim, facts: Facts) -> dict | None:
    """A step (threshold, drop, peak) on a count feature: the value the phrase prints, whether it is an observed value,
    and the gap the location lies in."""
    if claim.kind not in LOCATED or claim.terms[0] not in {f.name for f in facts.features}:
        return None
    f = facts.feature(claim.terms[0])
    if not count_feature(f):
        return None
    lo, hi = p._gap(f, float(claim.value))
    printed = words.number(float(claim.value))
    return {"feature": f.name, "at": float(claim.value), "printed": f"= {printed}", "printed value observed": bool(np.any(np.isclose(f.values, float(printed.replace(",", ""))))),
            "gap": f"from {lo:g} to {hi:g}"}  # fmt: skip


def item4(entries: list[dict]) -> tuple[pd.DataFrame, list[dict]]:
    detail = []
    for e in entries:
        t = e["trace"]
        if t["exit"] != g.TEMPLATE:
            continue
        version, facts = t["versions"][-1], facts_of(e["scenario"], e["model"])
        text = dict((i, s) for i, s in version["sentences"])
        for sid, line, *_ in version["claims"]:
            step = step_on_count(parse(line), facts)
            if step:
                if step["printed"] not in text[sid]:
                    raise ValueError(f"{e['run']}: the template does not print {step['printed']} for {line}")
                detail.append({"tier": e["tier"], "where": "template", "run or handover": e["run"], "runs": 1, "scenario": e["scenario"], "model": e["model"],
                               "naming": e["naming"], "claim": line} | step | {"wording": text[sid]})  # fmt: skip
    for (tier, scenario, model, naming), h in sorted(handovers(entries).items()):
        facts = facts_of(scenario, model)
        for line, wording in h2_statements(h["text"]):
            claim = labels.internal(parse(line), e3.NAMES[naming])
            step = step_on_count(claim, facts)
            if step:
                if not wording.endswith(step["printed"]):
                    raise ValueError(f"{scenario} {model} {naming}: the H2 statement does not print {step['printed']} for {line}")
                detail.append({"tier": tier, "where": "H2 handover", "run or handover": f"{scenario}_{model}_H2_{naming}", "runs": len(h["runs"]), "scenario": scenario,
                               "model": model, "naming": naming, "claim": str(claim)} | step | {"wording": f"{line}  ({wording})"})  # fmt: skip
    detail = pd.DataFrame(detail)
    out = []
    all_h2 = handovers(entries)
    for tier in TIERS:
        templates = [e for e in entries if e["tier"] == tier and e["trace"]["exit"] == g.TEMPLATE]
        h2 = {k: v for k, v in all_h2.items() if k[0] == tier}
        h2_runs = sum(len(v["runs"]) for v in h2.values())
        for where, total, unit in (("template", len(templates), "released template texts"), ("H2 handover", len(h2), "H2 handovers (distinct)")):
            d = detail[(detail.tier == tier) & (detail["where"] == where)] if len(detail) else detail
            texts = d.groupby("run or handover") if len(d) else None
            n_texts = d["run or handover"].nunique() if len(d) else 0
            values = Counter(d.drop_duplicates(["run or handover", "printed"]).printed) if len(d) else Counter()
            feats = Counter(d.drop_duplicates(["run or handover", "feature"]).feature) if len(d) else Counter()
            out.append(row(4, tier, f"{unit} with a step on a count feature written '= <value>'", n_texts, total,
                           f"by feature: {counted(feats)}; by value: {counted(values)}"))  # fmt: skip
            for value, k in sorted(values.items()):
                observed = bool(d[d.printed == value]["printed value observed"].all())
                gaps = counted(Counter(d[d.printed == value].drop_duplicates(["run or handover", "gap"]).gap))
                out.append(row(4, tier, f"{unit} that write a step '{value}'", k, total,
                               f"{'an observed value' if observed else 'not an observed value'}; the gap: {gaps}"))  # fmt: skip
            if where == "H2 handover":
                runs = int(texts.runs.first().sum()) if texts is not None else 0
                out.append(row(4, tier, "H2 runs whose writer saw such a statement", runs, h2_runs))
    return detail, out


# --- 5. emphasis ------------------------------------------------------------------------------------------------


def strong_term(facts: Facts, lex: p.Lexicon) -> bool:
    """The model has a term at the strong edge or above: without one, the emphasis rule cannot fire (gate/roundtrip.emphasis)."""
    return any(v >= lex.strength["strong"] for v in rt._shares(facts).values())


def item5(entries: list[dict], rows: pd.DataFrame, lex: p.Lexicon) -> tuple[pd.DataFrame, list[dict]]:
    table = []
    for e in entries:
        strong = strong_term(facts_of(e["scenario"], e["model"]), lex)
        for v in e["trace"]["versions"]:
            if v["roundtrip"] is not None:
                draft = v["source"] != "reduced"
                table.append({"tier": e["tier"], "where": "gate round trip, draft" if draft else "gate round trip, reduced text (not checked)",
                              "checked": draft, "model has a strong term": strong, "fired": bool(v["roundtrip"]["emphasis"])})  # fmt: skip
    for arm in ("off", "on"):
        part = rows[rows[f"{arm} scored"] == True]  # noqa: E712
        for tier, exit_state, value in zip(part.tier, part.exit, part[f"{arm} emphasis"]):
            kind = "draft" if arm == "off" else "template" if exit_state == g.TEMPLATE else "LLM-written"
            table.append({"tier": tier, "where": f"scoring, {arm}, {kind}", "checked": True, "model has a strong term": None, "fired": bool(value > 0)})
    table = pd.DataFrame(table)
    counts = table.groupby(["tier", "where"]).agg(texts=("fired", "size"), checked=("checked", "sum"), fired=("fired", "sum")).reset_index()
    out = []
    for tier in TIERS:
        part = table[table.tier == tier]
        gate_checked = part[part["where"] == "gate round trip, draft"]
        out.append(row(5, tier, "gate round trips that checked the emphasis rule (drafts) where it fired", int(gate_checked.fired.sum()), len(gate_checked),
                       f"checks on a model with a strong term (the rule can fire): {int(gate_checked['model has a strong term'].sum())}; "
                       f"reduced texts, not checked: {int((part['where'] == 'gate round trip, reduced text (not checked)').sum())}"))  # fmt: skip
        for where in sorted(w for w in part["where"].unique() if w.startswith("scoring")):
            s = part[part["where"] == where]
            out.append(row(5, tier, f"{where}: scored texts where it fired", int(s.fired.sum()), len(s)))
    return counts, out


# --- 6. numbers in words ----------------------------------------------------------------------------------------


def counts_in_words(sentence: str) -> list[tuple[str, str]]:
    """The counts and values a sentence states in words: (pattern, matched words), by COUNT_IN_WORDS."""
    return [(name, m.group(0)) for name, pattern in COUNT_PATTERNS.items() for m in pattern.finditer(sentence)]


def code_pattern(names: list[str]) -> re.Pattern | None:
    """The feature names shown to the writer that hold a digit (PAY_0, BILL_AMT1, ...), as whole words."""
    codes = sorted((n for n in names if re.search(r"\d", n)), key=len, reverse=True)
    return re.compile(r"\b(?:" + "|".join(re.escape(c) for c in codes) + r")\b") if codes else None


def strip_codes(text: str, codes: re.Pattern | None) -> str:
    return codes.sub(" ", text) if codes is not None else text


def digits(text: str, codes: re.Pattern | None) -> dict:
    """Whether a text has a digit (the digit test, gate/roundtrip.NUMBER), one inside a feature code, and digits only
    inside feature codes."""
    any_digit, outside = bool(rt.NUMBER.search(text)), bool(rt.NUMBER.search(strip_codes(text, codes)))
    in_code = any_digit and codes is not None and bool(codes.search(text))
    return {"digit": any_digit, "digit in a code": in_code, "digits only in codes": any_digit and not outside}


def number_sentences(found: list, order: list[int], codes: re.Pattern | None = None) -> list[int]:
    """The sentences that fail the digit test (gate/roundtrip.compare: a statement no DSL form expresses, with a digit,
    in at least EXTRACTED readings); with `codes`, after the feature codes are taken out of the statements."""
    votes = Counter()
    for reading in found:
        for sid, statements in reading.unexpressed.items():
            votes[sid] += any(rt.NUMBER.search(strip_codes(s, codes)) for s in statements)
    return [sid for sid in order if votes[sid] >= rt.EXTRACTED]


def shown_names(entry: dict) -> list[str]:
    return [labels.shown(f.name, e3.NAMES[entry["naming"]]) for f in facts_of(entry["scenario"], entry["model"]).features]


def item6(entries: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[dict]]:
    texts, sentences, digit_test = [], [], []
    for e in released_llm(entries):
        codes = code_pattern(shown_names(e))
        final = e["trace"]["versions"][-1]
        gap = {sid: statements for sid, statements in final["roundtrip"]["gap"]}  # content no DSL form expresses, in 2 or more readings
        found = [(sid, s, counts_in_words(s)) for sid, s in final["sentences"]]
        for sid, s, matches in found:
            if matches:
                beyond = [x for x in gap.get(sid, []) if counts_in_words(x)]
                sentences.append({"tier": e["tier"], "run": e["run"], "sentence id": sid, "patterns": ", ".join(sorted({n for n, _ in matches})),
                                  "matched": " | ".join(m for _, m in matches), "digit in the sentence": bool(rt.NUMBER.search(s)),
                                  "digit outside feature codes": bool(rt.NUMBER.search(strip_codes(s, codes))),
                                  "readers' statements beyond the DSL with a count in words": " | ".join(beyond), "sentence": s})  # fmt: skip
        text = " ".join(s for _, s in final["sentences"])
        texts.append({"tier": e["tier"], "run": e["run"], "sentences": len(final["sentences"]), "sentences with a count in words": sum(bool(m) for *_, m in found)}
                     | digits(text, codes))  # fmt: skip
    for e in entries:
        codes = code_pattern(shown_names(e))
        for i, x in e["gate"].items():
            v = e["trace"]["versions"][i]
            if v["roundtrip"] is None:
                continue
            order = [sid for sid, _ in v["sentences"]]
            plain = number_sentences(x["readings"], order)
            if plain != [sid for sid, _ in v["roundtrip"]["numbers"]]:
                raise ValueError(f"{e['run']}, version {i}: the digit test does not reproduce the round trip's unchecked numbers")
            without = number_sentences(x["readings"], order, codes)
            digit_test.append({"tier": e["tier"], "where": "gate round trip", "run": e["run"], "version": i, "source": v["source"], "sentences failing the digit test": len(plain),
                               "failing only through a feature code": len(set(plain) - set(without))})  # fmt: skip
        if e["trace"]["exit"] in RELEASED_LLM and "on" in e["scoring"]:
            s = e["scoring"]["on"]
            if len(s["readings"]) >= rt.EXTRACTED:
                order = [sid for sid, _ in s["sentences"]]
                plain, without = number_sentences(s["readings"], order), number_sentences(s["readings"], order, codes)
                digit_test.append({"tier": e["tier"], "where": "scoring, on, LLM-written", "run": e["run"], "version": None, "source": "released",
                                   "sentences failing the digit test": len(plain), "failing only through a feature code": len(set(plain) - set(without))})  # fmt: skip
    texts, sentences, digit_test = pd.DataFrame(texts), pd.DataFrame(sentences), pd.DataFrame(digit_test)
    out = []
    for tier in TIERS:
        t = texts[texts.tier == tier]
        s = sentences[sentences.tier == tier] if len(sentences) else sentences
        with_words = t[t["sentences with a count in words"] > 0]
        patterns = Counter(p_ for ps in s.patterns for p_ in ps.split(", ")) if len(s) else Counter()
        out.append(row(6, tier, "released LLM-written texts that state a count or value in words", len(with_words), len(t),
                       f"sentences: {len(s)} of {int(t.sentences.sum())}; {int((~s['digit outside feature codes']).sum()) if len(s) else 0} of them with no digit "
                       f"outside feature codes; sentences by pattern: {counted(patterns)}"))  # fmt: skip
        strict = s[s.patterns.str.contains("number word and unit|range of values")] if len(s) else s
        out.append(row(6, tier, "released LLM-written texts with a count in words in the narrow sense (a number word and a unit, or a range of values)",
                       strict.run.nunique() if len(strict) else 0, len(t), f"sentences: {len(strict)}"))  # fmt: skip
        beyond = s[s["readers' statements beyond the DSL with a count in words"].fillna("") != ""] if len(s) else s
        out.append(row(6, tier, "sentences with a count in words that the gate's final readings put beyond the DSL, in words (released unchecked)", len(beyond), len(s),
                       f"denominator: sentences with a count in words; the readers' statements no DSL form expresses (2 or more readings) state the count "
                       f"in words, so the digit test passed them; texts: {beyond.run.nunique() if len(beyond) else 0}"))  # fmt: skip
        out.append(row(6, tier, "released LLM-written texts whose only digits sit inside feature codes", int(t["digits only in codes"].sum()), len(t),
                       f"texts with a digit: {int(t.digit.sum())}; with a digit inside a feature code: {int(t['digit in a code'].sum())}"))  # fmt: skip
        d = digit_test[digit_test.tier == tier]
        for where in ("gate round trip", "scoring, on, LLM-written"):
            part = d[d["where"] == where]
            failing = part[part["sentences failing the digit test"] > 0]
            through_codes = part[part["failing only through a feature code"] > 0]
            unit = "gate round trips (all versions)" if where == "gate round trip" else "scored released LLM-written texts"
            out.append(row(6, tier, f"{unit} with a sentence failing the digit test only through a feature code", len(through_codes), len(failing),
                           f"denominator: those with a sentence failing the digit test (of {len(part)}); sentences: "
                           f"{int(part['failing only through a feature code'].sum())} of {int(part['sentences failing the digit test'].sum())}; "
                           f"runs: {through_codes.run.nunique()}"))  # fmt: skip
    return texts, sentences, digit_test, out


# --- 7. unparsed lines ------------------------------------------------------------------------------------------


def dropped_lines(data: dict, sentence_ids: set[int]) -> list[dict]:
    """The DSL lines of a reading that extract.extraction_from drops: lines that do not parse, and every line filed
    under a sentence id the text does not have."""
    out = []
    for item in data.get("sentences", []):
        sid = int(item["id"])
        for line in (str(x).strip() for x in item.get("claims", [])):
            why = "no sentence with this id" if sid not in sentence_ids else None
            if why is None:
                try:
                    parse(line)
                    continue
                except DSLError as e:
                    why = str(e)
            out.append({"sentence id": sid, "line": line, "hedge": bool(HEDGE_LINE.match(line)), "why": why})
    return out


def item7(entries: list[dict]) -> tuple[pd.DataFrame, list[dict]]:
    detail, totals = [], Counter()
    for e in released_llm(entries):
        t = e["trace"]
        last = len(t["versions"]) - 1
        final = t["versions"][last]
        ids = {i for i, _ in final["sentences"]}
        for where, x in (("gate's final readings", e["gate"][last]), ("scoring readings", e["scoring"].get("on"))):
            if x is None:
                continue
            totals[e["tier"], where, "texts"] += 1
            totals[e["tier"], where, "readings"] += len(x["used"])
            totals[e["tier"], where, "error entries"] += sum(len(r.format_errors) for r in x["readings"])
            dropped_any = False
            for k, data in enumerate(x["used"]):
                totals[e["tier"], where, "lines"] += len(dsl_lines(data, "reader"))
                for d in dropped_lines(data, ids):
                    detail.append({"tier": e["tier"], "readings": where, "run": e["run"], "reading": k} | d)
                    dropped_any = True
            totals[e["tier"], where, "texts with a dropped line"] += dropped_any
        if sum(len(r.format_errors) for r in e["gate"][last]["readings"]) != final["roundtrip"]["format_errors"]:
            raise ValueError(f"{e['run']}: the final readings' format errors are not the round trip's")
    detail = pd.DataFrame(detail, columns=["tier", "readings", "run", "reading", "sentence id", "line", "hedge", "why"])
    out = []
    for tier in TIERS:
        for where in ("gate's final readings", "scoring readings"):
            d = detail[(detail.tier == tier) & (detail.readings == where)]
            lines = totals[tier, where, "lines"]
            unparsed, misfiled = d[d.why != "no sentence with this id"], d[d.why == "no sentence with this id"]
            note = (f"{totals[tier, where, 'texts']} texts, {totals[tier, where, 'readings']} readings; texts with a dropped line: "
                    f"{totals[tier, where, 'texts with a dropped line']}; format errors as the readings count them: {totals[tier, where, 'error entries']} "
                    f"(one per unparsed line, and one per sentence entry under an id the text does not have, with or without lines)")  # fmt: skip
            out.append(row(7, tier, f"{where}, released LLM-written texts: DSL lines that do not parse (dropped)", len(unparsed), lines, note))
            out.append(row(7, tier, f"{where}: of these, hedges (unsettled(...))", int(unparsed.hedge.sum()), len(unparsed), "denominator: the dropped lines"))
            out.append(row(7, tier, f"{where}: lines under a sentence id the text does not have (dropped unparsed)", len(misfiled), lines,
                           f"hedges among them: {int(misfiled.hedge.sum())}"))  # fmt: skip
    return detail, out


# --- 8. reading counts ------------------------------------------------------------------------------------------


def reading_counts(trip: dict) -> list[dict]:
    """The claims of a round trip with the number of readings that found each: extracted (2 or more), ambiguous (1),
    and planned claims no reading found (0)."""
    out = [{"sentence id": sid, "claim": line, "found": n} for sid, line, n in trip["extracted"]]
    out += [{"sentence id": sid, "claim": line, "found": 1} for sid, line in trip["ambiguous"]]
    seen = {line for _, line in trip["ambiguous"]}
    out += [{"sentence id": sid, "claim": line, "found": 0} for sid, line in trip["plan_only"] if line not in seen]
    return [c | {"readings": trip["readings"], "hedge": c["claim"].startswith(f"{HEDGE}(")} for c in out]


def item8(entries: list[dict]) -> tuple[pd.DataFrame, list[dict]]:
    trips = [(e, e["trace"]["versions"][-1]["roundtrip"]) for e in released_llm(entries)]
    detail = pd.DataFrame([{"tier": e["tier"], "run": e["run"]} | c for e, trip in trips for c in reading_counts(trip)])
    out = []
    for tier in TIERS:
        d = detail[detail.tier == tier]
        for n in (3, 2):
            part = d[(d.readings == n) & (d.found > 0)]
            texts, hedges = d[d.readings == n].run.nunique(), part[part.hedge]
            for k in range(1, n + 1):
                out.append(row(8, tier, f"claims found by {k} of {n} readings", int((part.found == k).sum()), len(part),
                               f"texts with {n} readings: {texts}; hedges found by {k} of {n}: {int((hedges.found == k).sum())} of {len(hedges)}"
                               + ("; found once: logged, not blocking" if k == 1 else "")))  # fmt: skip
        planned = d[d.found == 0]
        out.append(row(8, tier, "planned claims no reading found", len(planned), len(d), "denominator: all claims listed (found or planned)"))
    return detail, out


# --- 9. spurious share ------------------------------------------------------------------------------------------


def spurious(m: Facts, t: Facts) -> dict:
    """The shares of M's importance on terms T does not plant: main terms with no importance in T (noise features;
    plasmode's BILL_AMT2 and PAY_AMT3) and pairs T does not have; and M's number of pairs. Shares sum to 1 over M's
    terms."""
    mains = {f.name for f in t.features if f.importance.value > 0}
    pairs = {frozenset(q.features) for q in t.pairs if q.importance.value > 0}
    spurious_mains = sum(f.share.value for f in m.features if f.name not in mains)
    spurious_pairs = sum(q.share.value for q in m.pairs if frozenset(q.features) not in pairs)
    return {"pairs": len(m.pairs), "planted pairs fitted": sum(frozenset(q.features) in pairs for q in m.pairs),
            "share on spurious mains": spurious_mains, "share on spurious pairs": spurious_pairs, "share on terms not planted": spurious_mains + spurious_pairs,
            "share on planted pairs": sum(q.share.value for q in m.pairs if frozenset(q.features) in pairs),
            "shares sum": sum(f.share.value for f in m.features) + sum(q.share.value for q in m.pairs),
            "spurious mains": ", ".join(f.name for f in m.features if f.name not in mains)}  # fmt: skip


def item9() -> tuple[pd.DataFrame, list[dict]]:
    """Every fitted model; the pilot datasets' are listed in the detail, flagged, and left out of the summary."""
    detail = []
    for s in tiers.SCENARIOS:
        for model in e3.MODELS:
            detail.append({"tier": tiers.name(s), "scenario": s.id, "pilot dataset": s.id in e3.PILOT, "interaction": s.interaction, "n": s.n, "seed": s.seed,
                           "model": model} | spurious(facts_of(s.id, model), facts_of(s.id, "T")))  # fmt: skip
    detail = pd.DataFrame(detail)
    if not np.allclose(detail["shares sum"], 1.0):
        raise ValueError("M's shares do not sum to 1")
    out = []
    for tier in TIERS:
        for model in e3.MODELS:
            d = detail[(detail.tier == tier) & (detail.model == model) & ~detail["pilot dataset"]]
            for k in ("share on terms not planted", "share on spurious pairs", "share on spurious mains"):
                for stat in ("mean", "min", "max"):
                    out.append(row(9, tier, f"{model}: {k}, {stat}", len(d), None, f"over {len(d)} fitted models", share=getattr(d[k], stat)()))
            out.append(row(9, tier, f"{model}: pair terms per model (mean)", int(d.pairs.sum()), len(d), f"min {d.pairs.min()}, max {d.pairs.max()}"))
            for level in ("none", "weak", "dominant"):
                part = d[d.interaction == level]
                out.append(row(9, tier, f"{model}: share on terms not planted, interaction {level}, mean", len(part), None,
                               f"min {part['share on terms not planted'].min():.4f}, max {part['share on terms not planted'].max():.4f}",
                               share=part["share on terms not planted"].mean()))  # fmt: skip
    return detail, out


# --- 10. model multiplicity -------------------------------------------------------------------------------------


def opposite_verdicts(verdicts: pd.DataFrame) -> pd.DataFrame:
    """E1's claims with both model classes' verdicts: decided by both (true or false), and opposite (certified for
    one, refuted for the other)."""
    decided = verdicts.EBM.isin([p.TRUE, p.FALSE]) & verdicts.XGB2.isin([p.TRUE, p.FALSE])
    return verdicts.assign(**{"decided by both": decided, "opposite": decided & (verdicts.EBM != verdicts.XGB2)})


def item10(e1: Path = E1) -> tuple[pd.DataFrame, list[dict]]:
    """E1's claims on every dataset; the pilot datasets' opposite verdicts are listed in the detail, flagged, and left
    out of the counts (the note gives them)."""
    verdicts = pd.concat([pd.read_csv(e1 / name / "verdicts.csv").assign(set=name) for name in E1_SETS], ignore_index=True)
    verdicts["tier"] = [tiers.name(tiers.scenario(s)) for s in verdicts.scenario]
    verdicts["pilot dataset"] = verdicts.scenario.isin(e3.PILOT)
    every = opposite_verdicts(verdicts)
    table = every[~every["pilot dataset"]]
    out = []
    for tier in TIERS:
        part, pilots = table[table.tier == tier], every[(every.tier == tier) & every["pilot dataset"]]
        for n in sorted(part.n.unique()):
            d = part[part.n == n]
            opp = d[d.opposite]
            examples = "; ".join(f"{r.scenario}: {r.claim} EBM {r.EBM}, XGB2 {r.XGB2} (T: {str(r.label).lower()})" for r in opp.head(3).itertuples())
            out.append(row(10, tier, f"n = {n}: claims certified for one model class and refuted for the other", int(d.opposite.sum()), int(d["decided by both"].sum()),
                           f"denominator: claims decided by both; of all {len(d)} claims {d.opposite.mean():.4f}; datasets {d.scenario.nunique()}; "
                           f"by kind: {counted(Counter(opp.kind))}; e.g. {examples}"))  # fmt: skip
        opp = part[part.opposite]
        out.append(row(10, tier, "all n: claims certified for one model class and refuted for the other", int(part.opposite.sum()), int(part["decided by both"].sum()),
                       f"denominator: claims decided by both; of all {len(part)} claims {part.opposite.mean():.4f}; EBM true and XGB2 false: "
                       f"{int((opp.EBM == p.TRUE).sum())}; XGB2 true and EBM false: {int((opp.XGB2 == p.TRUE).sum())}; by kind: {counted(Counter(opp.kind))}; "
                       f"false against T (label): {int((~opp.label.astype(bool)).sum())}; the pilot datasets add {int(pilots.opposite.sum())} of "
                       f"{int(pilots['decided by both'].sum())}"))  # fmt: skip
    columns = ["tier", "set", "scenario", "pilot dataset", "seed", "n", "interaction", "claim id", "claim", "kind", "role", "label", "EBM", "XGB2", "oracle"]
    return every[every.opposite][columns].sort_values(["tier", "n", "scenario", "claim id"]), out


# --- the run ----------------------------------------------------------------------------------------------------


def measure(source: str = SOURCE, out: Path | None = None) -> pd.DataFrame:
    lex = check_configuration()
    out = out or out_folder(source)
    rows = pd.read_csv(e3.RESULTS / source / WRITER_ARM / "rows.csv").set_index("run")
    rows["tier"] = [tiers.name(tiers.scenario(s)) for s in rows.scenario]
    entries = traces(source)
    for e in entries:
        rebuild(e, rows)
    print(f"{len(entries)} runs outside the pilot datasets: every writer answer, extraction and scoring reading rebuilt from the cache and checked")
    out.mkdir(parents=True, exist_ok=True)
    summary = []
    stop, part = item1(entries)
    stop.to_csv(out / "item1_stop_rules.csv", index=False)
    summary += part
    claims, models, part = item2(entries, source)
    claims.to_csv(out / "item2_rank_claims.csv", index=False)
    models.to_csv(out / "item2_rank_ties_by_model.csv", index=False)
    summary += part
    flagged, table, part = item3(entries, source)
    flagged.to_csv(out / "item3_flagged_lines.csv", index=False)
    table.to_csv(out / "item3_lines.csv", index=False)
    summary += part
    steps, part = item4(entries)
    steps.to_csv(out / "item4_count_steps.csv", index=False)
    summary += part
    emphasis, part = item5(entries, rows[~rows["pilot dataset"]], lex)
    emphasis.to_csv(out / "item5_emphasis.csv", index=False)
    summary += part
    texts, sentences, digit_test, part = item6(entries)
    texts.to_csv(out / "item6_texts.csv", index=False)
    sentences.to_csv(out / "item6_counts_in_words.csv", index=False)
    digit_test.to_csv(out / "item6_digit_test.csv", index=False)
    summary += part
    unparsed, part = item7(entries)
    unparsed.to_csv(out / "item7_unparsed_lines.csv", index=False)
    summary += part
    counts, part = item8(entries)
    counts.to_csv(out / "item8_reading_counts.csv", index=False)
    summary += part
    shares, part = item9()
    shares.to_csv(out / "item9_spurious_share.csv", index=False)
    summary += part
    multiplicity, part = item10()
    multiplicity.to_csv(out / "item10_multiplicity.csv", index=False)
    summary += part
    summary = pd.DataFrame(summary, columns=["item", "tier", "quantity", "count", "denominator", "share", "note"]).astype({"denominator": "Int64"})
    summary.to_csv(out / "summary.csv", index=False)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=SOURCE, choices=(SOURCE,), help="the E3 run: D74's (D75), whose requests today's prompts and Facts rebuild")
    args = parser.parse_args()
    summary = measure(args.source)
    pd.set_option("display.width", 250, "display.max_colwidth", 80, "display.max_rows", 500)
    print(summary.drop(columns="note").to_string(index=False))
    print(f"results in {out_folder(args.source)}")


if __name__ == "__main__":
    main()
