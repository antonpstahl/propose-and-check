"""E2 with an LLM critic beside the gate (D56, plan §14.29): the comparison a model-risk team asks for first.

The critic (llm/critique.py) is another vendor's model with the writer's facts (H1) and rules; it blocks a text if
it names a problem. Both are scored on the same texts, with labels that do not come from an LLM:

- llm: the 100 LLM-written errors with author-reviewed labels (e2_labels; 95 errors, 5 correct sentences);
- script: SCRIPT_SAMPLE errors per text-level operator, drawn with SEED from the script mutants (e2_text), labelled
  by construction against M, and every control mutant (a jump or peak moved inside the tolerance: still true);
- control: the unchanged template texts, every claim certified;
- e3: E3's released texts (LLM-written). What the critic flags there is labelled like the gate's blocks
  (e2_false_alarms): a flag is right (the sentence states something the facts do not support) or a false alarm.

No case comes from the pilot datasets (PILOT), on which the prompt was tried before it was frozen (`--pilot`). The
gate's outcome on each case is the text-level E2 run with extractor x4 (GATE_VERSION), so the comparison is paired;
for e3 it is false_alarms/texts_x4.csv with its labels. Recall is the share of errors blocked; "at the change"
needs a problem at the changed sentence (for an omission: at the whole text). The critic's probability is checked
against the labels: its Brier score, and how often it is confident and wrong (CONFIDENT).

Versions (llm/prompts): c1 got the H1 facts for every text and the writer's rules for choosing words. c2 (M4 of the
20 Oct review) gets what the writer got: the writer's whole set of rules with the DSL table, and the handover each
writer saw, read from its E3 run trace (`writer_handover`): H2, with the certified statements, for an H2 text and
for the LLM mutant of one; a template text, written from the certified statements without a writer, gets the H1 of
its cell. c2 was frozen before its first call, with no pilot: it changes only the inputs. `--compare` sets c2
beside c1 and the gate (compare.csv in c2's folder): blocked shares, recall and specificity with 95% intervals,
balanced accuracy, agreement between the versions, what c2 does with the E3 texts whose c1 flags the author
labelled, and how many flagged sentences state a statement the verifier certifies.

Calls run in parallel (WORKERS), synchronously; every answer is cached and logged like any other. `--estimate`
prices a run from the prompts' length and the pilot's measured output (OUT_TOKENS) before anything is sent, and a
run that would exceed `--budget` does not start; a running one stops calling once its spend reaches the budget.

Run: `uv run python -m verifier_gate.experiments.e2_critic [--pilot | --estimate | --compare] [--critic c1]
[--model openai/gpt-6.1-sol] [--sources llm,control] [--budget 2.0]`. Writes results/e2/<lexicon>/text/critic/<model>/<prompt
version>/: cases.csv, summary.csv. Labels of the e3 flags: `--page` writes critic/labels/ (items.json, key.csv and the
labelling page critic_page.html, from critic_page.html next to this file); `--score labels.json` scores them.
"""

import argparse
import functools
import json
import math
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from verifier_gate.data import dgp
from verifier_gate.dsl.grammar import Claim
from verifier_gate.experiments import e2_labels, e2_text
from verifier_gate.experiments.e2_false_alarms import wilson
from verifier_gate.experiments.e2_text import PILOT, RESULTS, Case
from verifier_gate.lexicon import predicates as p
from verifier_gate.llm import prompts, settings
from verifier_gate.llm.client import Client, Request, Response, stub_message
from verifier_gate.llm.critique import WHOLE_TEXT, critic_request, critique_from
from verifier_gate.llm.handover import handover

SCRIPT_SAMPLE = 30
SEED = 20261020
GATE_VERSION = "x4"
SOURCES = ("llm", "script", "control", "e3")
WORKERS = 16  # a critique takes about a minute (the pilot: 9 calls in 153 s with 6 workers)
CONFIDENT = 0.1  # confident and wrong: an error passed with p_error <= 0.1, or a correct text blocked with p_error >= 0.9
OUT_TOKENS = {settings.CRITIC: 1800, settings.CRITIC_STRONG: 300}  # output per call, reasoning included: about the pilots' means
PAGE = Path(__file__).with_name("critic_page.html")
FA_SAMPLE = 40  # flagged e3 texts to label if there are more


def folder(model: str, version: str = prompts.CRITIC_VERSION) -> Path:
    return RESULTS / p.load().version / "text" / "critic" / model.removeprefix("openai/") / version


# --- cases ------------------------------------------------------------------------------------------------


ROLES = {"error": "error", "ok": "correct"}  # a label on the page; anything else ("unsure") is no role


def llm_cases() -> list[Case]:
    """The labelled LLM mutants, as the labeller saw them (the whole text with the changed sentence), with both label
    passes: the final one (reviewed against the lexicon with the assistant's reading of each sentence) and the
    author's first pass, made alone and without the gate's verdicts, so free of any LLM's or the lexicon's reading."""
    base = RESULTS / p.load().version / "text" / "labels"
    items = json.loads((base / "items.json").read_text())["items"]
    final, first = ({k: v["label"] for k, v in json.loads((base / name).read_text()).items()} for name in ("labels_final.json", "labels_pass1.json"))
    key = pd.read_csv(base / "key.csv").set_index("item")
    out = []
    for it in items:
        scenario, model, naming = it["facts"].rsplit("_", 2)
        out.append(Case(it["id"], "llm", scenario, model, naming, it["sentences"], [], it["changed"],
                        {"role": ROLES.get(final.get(it["id"]), "unsure"), "first pass": ROLES.get(first.get(it["id"]), "unsure"),
                         "gate case": key.at[it["id"], "case"]}))  # fmt: skip
    return out


def script_sample(lex: p.Lexicon | None = None) -> list[Case]:
    """The template texts outside the pilot datasets: every unchanged one, every control mutant, and SCRIPT_SAMPLE
    errors per operator (all of them if fewer)."""
    scenarios = tuple(s for s in dgp.SCENARIOS if s.id not in PILOT)
    cases = e2_text.script_cases(scenarios, lex)
    rng = np.random.default_rng(SEED)
    keep = [c for c in cases if c.source == "control" or c.info.get("role") == "control"]
    for op in sorted({c.info["operator"] for c in cases if c.source == "script"}, key=lambda o: int(o[1:])):
        errors = [c for c in cases if c.source == "script" and c.info["operator"] == op and c.info["role"] == "error"]
        keep += [errors[i] for i in sorted(rng.choice(len(errors), min(SCRIPT_SAMPLE, len(errors)), replace=False))]
    return keep


def e3_cases() -> list[Case]:
    return [Case(t["run"], "e3", t["scenario"], t["model"], t["naming"], t["sentences"], t["plan"], None, {"role": "unlabelled"})
            for t in e2_text.released_texts()]  # fmt: skip


def build(sources: tuple[str, ...]) -> list[Case]:
    lex = p.load()
    out = []
    if "llm" in sources:
        out += llm_cases()
    if "script" in sources or "control" in sources:
        out += [c for c in script_sample(lex) if c.source in sources]
    if "e3" in sources:
        out += e3_cases()
    return out


def pilot_cases() -> list[Case]:
    """The prompt's trial: on the pilot datasets, each unchanged template text and one error of each operator."""
    cases = e2_text.script_cases(tuple(s for s in dgp.SCENARIOS if s.id in PILOT))
    out = [c for c in cases if c.source == "control"]
    for op in ("M1", "M3", "M7", "M9", "M11"):
        out += [c for c in cases if c.source == "script" and c.info["operator"] == op and c.info["role"] == "error"][:1]
    return out


# --- calls ------------------------------------------------------------------------------------------------


@functools.cache
def writer_handover(run_id: str) -> str:
    """The handover in an E3 run's writer request, as the writer read it (propose.md wraps it in one line before and
    one after)."""
    run = json.loads((e2_text.E3_RESULTS / e2_text.E3_SOURCE / "haiku" / "runs" / f"{run_id}.json").read_text())
    user = run["writer"]["messages"][0][1]
    return user[user.index("\n\n") + 2 : user.rindex("\n\nWrite the explanation")]


def written_by(case: Case) -> str:
    """The E3 run whose writer request carries the facts for a case: its own run (an E3 text), the run it was mutated
    from (an LLM mutant), or, for a template text, the H1 run of its cell at draw 0."""
    if case.source == "e3":
        return case.case_id
    if case.source == "llm":
        return case.info["gate case"]
    return f"{case.scenario}_{case.model}_H1_d0_{settings.WRITER}_{case.naming}"


def facts_text(case: Case, cache: dict, version: str = "c1") -> str:
    """c1: the handover H1, built from the Facts; c2: the handover the writer saw (writer_handover)."""
    if version != "c1":
        return writer_handover(written_by(case))
    key = (case.scenario, case.model, case.naming)
    if key not in cache:
        ctx = e2_text.context(case, {})
        scenario = next(s for s in dgp.SCENARIOS if s.id == case.scenario)
        cache[key] = handover(ctx.facts, dgp.generate(scenario).X, "H1", ctx.certified, names=ctx.names).text
    return cache[key]


def requests(cases: list[Case], model: str, version: str) -> dict[str, Request]:
    texts: dict = {}
    return {c.case_id: critic_request(facts_text(c, texts, version), c.sentences, model, version=version) for c in cases}


def estimate(reqs: list[Request], client: Client) -> tuple[int, float]:
    """Uncached calls and their price: input from the prompts' length (4 characters a token, the system prompt
    cached after the first call of a worker), output from OUT_TOKENS."""
    todo = [r for r in reqs if not (client.cache_dir / f"{r.key}.json").exists()]
    if not todo:
        return 0, 0.0
    price_in, price_out, price_read = settings.PRICES[todo[0].model]
    system = len(todo[0].system) / 4
    user = sum(len(r.messages[0][1]) for r in todo) / 4
    dollars = (user * price_in + len(todo) * system * price_read + WORKERS * system * price_in + len(todo) * OUT_TOKENS[todo[0].model] * price_out) / 1e6
    return len(todo), dollars


def resolve(reqs: list[Request], client: Client, budget: float, workers: int = WORKERS, log=print) -> dict[str, Response]:
    """Answers by key, from the cache or in parallel; no new call once the calls made here cost `budget`."""
    answers, spent, lock, done = {}, [0.0], threading.Lock(), [0]

    def one(r: Request) -> None:
        cached = client.lookup(r)
        if cached is None:
            with lock:
                if spent[0] >= budget:
                    return
            cached = client.call(r)
            with lock:
                spent[0] += cached.cost
                done[0] += 1
                if done[0] % 50 == 0:
                    log(f"{done[0]} calls, ${spent[0]:.3f}")
        answers[r.key] = cached

    with ThreadPoolExecutor(workers) as pool:
        list(pool.map(one, list({r.key: r for r in reqs}.values())))
    log(f"{done[0]} new call(s), ${spent[0]:.3f}" + (f"; budget ${budget:.2f} reached, the rest not sent" if spent[0] >= budget else ""))
    return answers


# --- scoring ----------------------------------------------------------------------------------------------


def gate_outcomes() -> dict[str, dict]:
    """The gate's outcome per case: text-level E2 with extractor x4 (script and control cases by case id, the
    labelled LLM mutants by the case they came from). A text with fewer than two readable extractions is not
    released (the gate falls back to the template, gate/gate.py), so it counts as caught (D32), not at the change;
    `gate read` keeps it apart. The labelled LLM mutants' published recall (e2_labels, 93 of 95) counts it the same way."""
    base = RESULTS / p.load().version / "text" / GATE_VERSION
    out = {}
    for name in ("script.csv", "llm.csv"):
        table = pd.read_csv(base / name)
        for case, read, caught, at in zip(table.case, table.read, table.caught, table["caught at the change"]):
            out[case] = {"gate read": bool(read), "gate caught": bool(caught) if read else True, "gate at the change": bool(at) if read else False}
    return out


def score(cases: list[Case], reqs: dict[str, Request], answers: dict[str, Response]) -> pd.DataFrame:
    gate = gate_outcomes()
    rows = []
    for c in cases:
        r = reqs[c.case_id]
        answer = answers.get(r.key)
        row = {"case": c.case_id, "source": c.source, "scenario": c.scenario, "model": c.model, "naming": c.naming,
               "operator": c.info.get("operator", ""), "variant": c.info.get("variant", ""), "role": c.info["role"],
               "first pass": c.info.get("first pass", ""), "changed": c.changed}  # fmt: skip
        try:
            if answer is None or answer.error:
                raise ValueError(answer.error if answer is not None else "not sent")
            critique = critique_from(answer, {i for i, _ in c.sentences})
            at = (WHOLE_TEXT in critique.problems) if c.changed is None else (c.changed in critique.problems)
            row |= {"critiqued": True, "blocked": critique.blocks, "at the change": critique.blocks and at, "p_error": critique.p_error,
                    "flagged": " ".join(str(s) for s in sorted(critique.problems)),
                    "problems": json.dumps({str(k): v for k, v in critique.problems.items()})}  # fmt: skip
        except ValueError as e:
            row |= {"critiqued": False, "error": str(e)}
        if answer is not None:  # a cached answer's cost is what it cost when it was made
            row |= {"input tokens": answer.usage.get("input_tokens", 0) + answer.usage.get("cache_read_input_tokens", 0),
                    "output tokens": answer.usage.get("output_tokens", 0), "reasoning tokens": answer.usage.get("reasoning_tokens", 0),
                    "cost": answer.cost}  # fmt: skip
        if c.source != "e3":  # an e3 text's id is also the id of its LLM mutant in llm.csv; the gate's e3 outcome is in score.csv
            row |= gate.get(c.info.get("gate case", c.case_id), {})
        rows.append(row)
    return pd.DataFrame(rows)


CORRECT = ("correct", "control", "control text")  # a labelled correct sentence, a control mutant, an unchanged template text


def _rates(part: pd.DataFrame, who: str) -> dict:
    blocked = "blocked" if who == "critic" else "gate caught"
    at = "at the change" if who == "critic" else "gate at the change"
    errors, correct = part[part.role == "error"], part[part.role.isin(CORRECT)]
    return {"errors": len(errors), "recall": round(errors[blocked].astype(bool).mean(), 3) if len(errors) else math.nan,
            "recall at the change": round(errors[at].astype(bool).mean(), 3) if len(errors) else math.nan,
            "correct texts": len(correct), "false alarms": int(correct[blocked].astype(bool).sum()) if len(correct) else 0}  # fmt: skip


def summarise(table: pd.DataFrame) -> pd.DataFrame:
    """Critic and gate on the same cases, per source and operator; the critic's confidence against the labels."""
    t = table[(table.critiqued == True) & table["gate caught"].notna()]  # noqa: E712  (both have an outcome)
    t = t[t.source != "e3"]
    llm = t[t.source == "llm"]
    first = llm.assign(role=llm["first pass"]) if "first pass" in llm else llm
    groups = [("LLM-written (author-reviewed labels)", llm), ("LLM-written (author's first pass)", first),
              ("template texts, unchanged", t[t.source == "control"]), ("script, all operators", t[t.source == "script"])]  # fmt: skip
    groups += [(f"script, {op}", part) for op, part in sorted(t[t.source == "script"].groupby("operator"), key=lambda x: int(x[0][1:]))]
    rows = []
    for name, part in groups:
        if len(part):
            for who in ("critic", "gate"):
                rows.append({"cases": name, "checker": who, **_rates(part, who)})
    labelled = t[t.role.isin(("error",) + CORRECT)]
    if len(labelled):
        truth = (labelled.role == "error").astype(float)
        p_error = labelled.p_error.astype(float)
        rows.append({"cases": "all labelled", "checker": "critic", "brier": round(float(((p_error - truth) ** 2).mean()), 4),
                     "errors passed with p_error <= 0.1": int(((truth == 1) & ~labelled.blocked.astype(bool) & (p_error <= CONFIDENT)).sum()),
                     "correct blocked with p_error >= 0.9": int(((truth == 0) & labelled.blocked.astype(bool) & (p_error >= 1 - CONFIDENT)).sum()),
                     "blocked but p_error < 0.5": int((labelled.blocked.astype(bool) & (p_error < 0.5)).sum()),
                     "passed but p_error >= 0.5": int((~labelled.blocked.astype(bool) & (p_error >= 0.5)).sum())})  # fmt: skip
    return pd.DataFrame(rows)


# --- labels of the e3 flags -------------------------------------------------------------------------------


def page(table: pd.DataFrame, out: Path, version: str = "c1") -> None:
    """One item per flagged sentence of the e3 texts the critic blocks (a sample of FA_SAMPLE texts if there are more),
    with the facts the critic saw; key.csv maps items to texts. The labeller never sees the gate's verdict."""
    flagged = table[(table.source == "e3") & (table.blocked == True)]  # noqa: E712
    if len(flagged) > FA_SAMPLE:
        flagged = flagged.iloc[sorted(np.random.default_rng(SEED).choice(len(flagged), FA_SAMPLE, replace=False))]
    texts = {t["run"]: t for t in e2_text.released_texts()}
    facts, items, key, cache = {}, [], [], {}
    for row in flagged.itertuples():
        t = texts[row.case]
        ctx_id = f"{t['scenario']}_{t['model']}_{t['naming']}"
        if ctx_id not in facts:
            head, parts = e2_labels.blocks(facts_text(Case(row.case, "e3", t["scenario"], t["model"], t["naming"], [], [], None, {}), cache, version))
            facts[ctx_id] = {"head": head, "blocks": parts}
        shown = [n for b in facts[ctx_id]["blocks"] for n in b["names"] if len(b["names"]) == 1]
        for sid, problems in sorted(json.loads(row.problems).items(), key=lambda x: int(x[0])):
            sid = int(sid)
            said = [s for i, s in t["sentences"] if i == sid]
            item = f"C{len(items) + 1:03d}"
            items.append({"id": item, "facts": ctx_id, "named": e2_labels.named(said or [s for _, s in t["sentences"]], shown),
                          "sentence_id": sid if said else None, "sentences": t["sentences"],
                          "claims": [{"words": problem, "dsl": "", "why": ""} for problem in problems]})  # fmt: skip
            key.append({"item": item, "case": row.case, "sentence_id": sid, "problems": len(problems), "p_error": row.p_error})
    out.mkdir(parents=True, exist_ok=True)
    blocked = int(table[table.source == "e3"].blocked.astype(bool).sum())
    (out / "items.json").write_text(json.dumps({"seed": SEED, "blocked texts": blocked, "facts": facts, "items": items}, indent=1))
    pd.DataFrame(key).to_csv(out / "key.csv", index=False)
    data = json.dumps(json.loads((out / "items.json").read_text()), separators=(",", ":")).replace("</", "<\\/")
    (out / "critic_page.html").write_text(PAGE.read_text().replace("__DATA__", data))
    print(f"{len(items)} flagged sentence(s) in {len(flagged)} text(s) to label; written to {out}")


def label_kinds(out: Path, labels_path: Path) -> dict[str, str]:
    """Each labelled blocked text's kind: a real error if a flag is right, a false alarm if every flag is wrong, open
    otherwise."""
    labels = json.loads(labels_path.read_text())
    key = pd.read_csv(out / "key.csv")
    verdicts = {}
    for row in key.itertuples():
        values = list((labels.get(row.item, {}).get("labels") or {}).values())
        verdicts.setdefault(row.case, []).extend(values or ["open"])
    return {case: "real error" if "error" in v else "false alarm" if v and all(x == "misreading" for x in v) else "open" for case, v in verdicts.items()}


def score_e3(table: pd.DataFrame, out: Path, labels_path: Path, gate_score: Path | None = None) -> pd.DataFrame:
    """The critic's flags on E3's released texts against the labels, beside the gate's (false_alarms/score.csv): a
    blocked text is a real error if a flag is right, a false alarm if every flag is wrong, open otherwise; the
    false-alarm rate is per correct text, as for the gate."""
    kinds = label_kinds(out, labels_path)
    e3 = table[(table.source == "e3") & (table.critiqued == True)]  # noqa: E712
    blocked = int(e3.blocked.astype(bool).sum())
    labelled = len(kinds)
    share = {k: sum(1 for v in kinds.values() if v == k) / labelled for k in ("real error", "false alarm", "open")} if labelled else {}
    estimated = {k: blocked * share.get(k, 0.0) for k in ("real error", "false alarm", "open")}  # the labelled texts are a sample of the blocked ones
    correct = len(e3) - estimated["real error"] - estimated["open"]
    gate_score = gate_score or RESULTS / p.load().version / "text" / "false_alarms" / "score.csv"
    gate = pd.read_csv(gate_score).set_index("extractor").loc[GATE_VERSION]
    result = pd.DataFrame([
        {"checker": "critic", "texts": len(e3), "blocked": blocked, "labelled blocked texts": labelled,
         **{f"{k} (labelled)": sum(1 for v in kinds.values() if v == k) for k in ("real error", "false alarm", "open")},
         "false-alarm rate (per correct text)": round(estimated["false alarm"] / correct, 3) if correct else math.nan},
        {"checker": f"gate ({GATE_VERSION} readings)", "texts": int(gate["texts scored"]), "blocked": int(gate["blocked"]), "labelled blocked texts": int(gate["blocked"]),
         "real error (labelled)": int(gate["real errors"]), "false alarm (labelled)": int(gate["false alarms"]), "open (labelled)": int(gate["open"]),
         "false-alarm rate (per correct text)": float(gate["false-alarm rate (per correct text)"])},
    ])  # fmt: skip
    result.to_csv(out / "score.csv", index=False)
    return result


# --- c2 beside c1 and the gate ----------------------------------------------------------------------------


def kappa(a: pd.Series, b: pd.Series) -> float:
    """Cohen's kappa of two checkers' blocks on the same texts."""
    a, b = a.astype(bool).to_numpy(), b.astype(bool).to_numpy()
    po, pe = float((a == b).mean()), float(a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean()))
    return round((po - pe) / (1 - pe), 3) if pe < 1 else math.nan


def _share(rows: list, set_: str, measure: str, checker: str, k: int, n: int) -> None:
    lo, hi = wilson(k, n) if n else (math.nan, math.nan)
    rows.append({"set": set_, "measure": measure, "checker": checker, "k": k, "n": n, "value": round(k / n, 4) if n else math.nan,
                 "95% low": round(lo, 4), "95% high": round(hi, 4)})  # fmt: skip


def certified_flags(table: pd.DataFrame) -> pd.DataFrame:
    """Per flagged sentence of an E3 text: whether it states a statement the verifier certifies (a claim of its plan
    is in the certified plan, verbatim); sentence 0 (the whole text) left out."""
    texts, cache, rows = {t["run"]: t for t in e2_text.released_texts()}, {}, []
    for row in table[(table.source == "e3") & (table.blocked == True)].itertuples():  # noqa: E712
        t = texts[row.case]
        ctx = e2_text.context(Case(row.case, "e3", t["scenario"], t["model"], t["naming"], [], [], None, {}), cache)
        certified = {str(c) for c in ctx.certified}
        for sid in (int(x) for x in str(row.flagged).split() if int(x) != WHOLE_TEXT):
            stated = [str(Claim(c.kind, c.terms, c.value, c.relation, None, c.inner)) for c in t["plan"] if c.sentence_id == sid]
            rows.append({"case": row.case, "handover": row.case.split("_")[2], "sentence": sid, "certified": any(c in certified for c in stated)})
    return pd.DataFrame(rows, columns=["case", "handover", "sentence", "certified"])


def compare_versions(model: str = settings.CRITIC, old: str = "c1", new: str = "c2") -> pd.DataFrame:
    """The critic before (c1) and after (c2) its inputs were matched, beside the gate (x4), in one long table:
    - recall on the errors (the labelled LLM-written ones, final and first-pass labels, and the scripted ones),
      specificity on the known-correct texts (the unchanged templates, the control mutants and the LLM-written
      sentences judged correct, final labels) and the balanced accuracy of the two (errors pooled: LLM-written with
      final labels and scripted), with 95% Wilson intervals;
    - on E3's released texts, the blocked share by handover, and what c2 does with the texts whose c1 flags the
      author labelled (by kind);
    - agreement (Cohen's kappa) of c1 and c2 per set of texts, and of each with the gate on E3's texts;
    - flagged sentences of E3 texts that state a certified statement, by handover."""
    a, b = (pd.read_csv(folder(model, v) / "cases.csv") for v in (old, new))
    t = a.merge(b, on=["case", "source"], suffixes=(" " + old, " " + new))
    t = t[(t[f"critiqued {old}"] == True) & (t[f"critiqued {new}"] == True)]  # noqa: E712
    rows: list = []
    checkers = {"gate (x4)": f"gate caught {old}", f"critic {old}": f"blocked {old}", f"critic {new}": f"blocked {new}"}
    labelled = t[t.source != "e3"]
    errors = {"LLM-written errors (final labels)": labelled[(labelled.source == "llm") & (labelled[f"role {old}"] == "error")],
              "LLM-written errors (author's first pass)": labelled[(labelled.source == "llm") & (labelled[f"first pass {old}"] == "error")],
              "scripted errors": labelled[(labelled.source == "script") & (labelled[f"role {old}"] == "error")]}  # fmt: skip
    pooled = pd.concat([errors["LLM-written errors (final labels)"], errors["scripted errors"]])
    correct = labelled[labelled[f"role {old}"].isin(CORRECT)]
    for checker, column in checkers.items():
        for name, part in [*errors.items(), ("LLM-written and scripted errors", pooled)]:
            _share(rows, name, "recall", checker, int(part[column].astype(bool).sum()), len(part))
        _share(rows, "known-correct texts", "specificity", checker, int((~correct[column].astype(bool)).sum()), len(correct))
        recall, specificity = pooled[column].astype(bool).mean(), (~correct[column].astype(bool)).mean()
        rows.append({"set": "LLM-written and scripted errors; known-correct texts", "measure": "balanced accuracy", "checker": checker,
                     "value": round((recall + specificity) / 2, 4)})  # fmt: skip
    e3 = t[t.source == "e3"].assign(handover=lambda d: d.case.str.split("_").str[2])
    gate = pd.read_csv(RESULTS / p.load().version / "text" / "false_alarms" / f"texts_{GATE_VERSION}.csv")
    gate = gate[gate.scored == True].set_index("run").blocked  # noqa: E712
    for variant, part in [("H1 and H2", e3)] + list(e3.groupby("handover")):
        for v in (old, new):
            _share(rows, f"E3's released texts, {variant}", "blocked", f"critic {v}", int(part[f"blocked {v}"].astype(bool).sum()), len(part))
        g = gate.reindex(part.case).dropna().astype(bool)
        _share(rows, f"E3's released texts, {variant}", "blocked", "gate (x4)", int(g.sum()), len(g))
    kinds = label_kinds(folder(model, old) / "labels", folder(model, old) / "labels" / "labels.json")
    for kind in ("real error", "open", "false alarm"):
        cases = [c for c, k in kinds.items() if k == kind]
        part = e3[e3.case.isin(cases)]
        if len(part):
            _share(rows, f"E3 texts {old} blocked, labelled {kind} by the author", "blocked", f"critic {new}", int(part[f"blocked {new}"].astype(bool).sum()), len(part))
    for source, part in t.groupby("source"):
        rows.append({"set": f"{source} texts", "measure": "kappa", "checker": f"critic {old} vs critic {new}", "n": len(part),
                     "value": kappa(part[f"blocked {old}"], part[f"blocked {new}"])})  # fmt: skip
    for v in (old, new):
        both = e3[e3.case.isin(gate.index)]
        rows.append({"set": "e3 texts", "measure": "kappa", "checker": f"gate (x4) vs critic {v}", "n": len(both),
                     "value": kappa(gate.loc[both.case], both[f"blocked {v}"])})  # fmt: skip
    for v in (old, new):
        flags = certified_flags(pd.read_csv(folder(model, v) / "cases.csv"))
        for variant, part in flags.groupby("handover"):
            _share(rows, f"flagged sentences of E3 texts, {variant}", "state a certified statement", f"critic {v}", int(part.certified.sum()), len(part))
    return pd.DataFrame(rows)


# --- running ----------------------------------------------------------------------------------------------


def stub_responder(request: Request) -> dict:
    """No network: the critic flags sentence 1 when a sentence says "strong", otherwise nothing."""
    text = request.messages[0][1].split("sentence by sentence:")[1]
    flagged = "strong effect" in text
    return stub_message({"problems": [{"sentence_id": 1, "problem": "too strong"}] if flagged else [], "p_error": 0.8 if flagged else 0.2},
                        usage={"input_tokens": 4000, "output_tokens": 600})  # fmt: skip


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=settings.CRITIC)
    parser.add_argument("--critic", default=prompts.CRITIC_VERSION, choices=sorted(prompts.CRITIC_NAMES), help="the critic's prompt version")
    parser.add_argument("--compare", action="store_true", help="c2 beside c1 and the gate, from both versions' cases.csv (no calls)")
    parser.add_argument("--sources", default=",".join(SOURCES), help=f"comma-separated, of {SOURCES}")
    parser.add_argument("--pilot", action="store_true", help="the prompt's trial on the pilot datasets (each round written to <out>/pilot/r<n>)")
    parser.add_argument("--estimate", action="store_true", help="count and price the uncached calls, no network")
    parser.add_argument("--dry", action="store_true", help="stubs, no network, a few cases")
    parser.add_argument("--budget", type=float, default=2.0, help="USD: a run priced above it does not start, and stops calling at it")
    parser.add_argument("--page", action="store_true", help="the labelling page for the critic's e3 flags")
    parser.add_argument("--score", type=Path, help="labels.json of the e3 flags")
    args = parser.parse_args()
    out = folder(args.model, args.critic)
    labels_dir = out / "labels"
    if args.compare:
        table = compare_versions(args.model)
        table.to_csv(folder(args.model, "c2") / "compare.csv", index=False)
        pd.set_option("display.width", 250)
        print(table.to_string(index=False))
        return
    if args.page or args.score:
        table = pd.read_csv(out / "cases.csv")
        if args.page:
            page(table, labels_dir, args.critic)
        if args.score:
            pd.set_option("display.width", 250)
            print(score_e3(table, labels_dir, args.score).to_string(index=False))
        return
    names = prompts.CRITIC_NAMES[args.critic]
    if not args.pilot and prompts.frozen(prompts.FROZEN_CRITIC[args.critic]) != prompts.hashes(names):
        raise SystemExit(f"the critic's prompts {args.critic} are not frozen as they are now: run --pilot, then freeze them (prompts.freeze)")
    cases = pilot_cases() if args.pilot else build(tuple(args.sources.split(",")))
    if args.dry:
        cases = cases[:6]
    reqs = requests(cases, args.model, args.critic)
    client = Client("stub", stub_responder, cache_dir=Path(tempfile.mkdtemp(prefix="e2_critic_dry_"))) if args.dry else Client("sync")
    calls, dollars = estimate(list(reqs.values()), client)
    print(f"{len(cases)} case(s) ({pd.Series([c.source for c in cases]).value_counts().to_dict()}); {calls} uncached call(s) to {args.model}, "
          f"about ${dollars:.2f}")  # fmt: skip
    if args.estimate:
        return
    if dollars > args.budget:
        raise SystemExit(f"the estimate ${dollars:.2f} is above the budget ${args.budget:.2f}: nothing sent")
    start = time.time()
    answers = resolve(list(reqs.values()), client, args.budget)
    table = score(cases, reqs, answers)
    target = out / "pilot" / f"r{len(list((out / 'pilot').glob('r*'))) + 1}" if args.pilot else out  # each pilot round kept
    if args.dry:
        target = Path(tempfile.mkdtemp(prefix="e2_critic_dry_out_"))
    target.mkdir(parents=True, exist_ok=True)
    if not args.pilot and (target / "cases.csv").exists():  # a run on some sources keeps the others' rows
        old = pd.read_csv(target / "cases.csv")
        table = pd.concat([old[~old.case.isin(table.case)], table], ignore_index=True)
    table.to_csv(target / "cases.csv", index=False)
    (target / "prompts.json").write_text(json.dumps(prompts.hashes(names), indent=1) + "\n")  # which prompt answered
    summary = summarise(table)
    summary.to_csv(target / "summary.csv", index=False)
    pd.set_option("display.width", 250)
    print(summary.to_string(index=False))
    spent = table["cost"].sum() if "cost" in table else 0.0
    print(f"\ncritic {args.model}, prompts {args.critic}; {time.time() - start:.0f}s; cases' cost ${spent:.3f}; results in {target}")


if __name__ == "__main__":
    main()
