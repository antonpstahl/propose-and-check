"""E2 at text level (plan §6 E2, the headline number): does the round trip catch an error in the text when the
plan stays correct?

The gate checks a text against its plan with the round trip (gate/roundtrip.py): three readings of the text by the
extractor, compared with the plan. Here one sentence of a correct text is changed and its plan is left as it was,
so the plan still passes; only the round trip can catch the change. Two sources of changed texts:

- Script (synthetic tier, all 36 models): the template text of each model's certified plan (gate/template.py),
  with one claim's clause rewritten by a plan-level operator (experiments/e2_mutation.py, M1 to M11) in the
  template's own fixed words. An invented interaction (M7) replaces the pair's "do not interact" clause or is added
  as a sentence; an omission (M8) drops the pair's clauses; the invented term of M9 is "the savings balance".
  Labels as at plan level, against M without bands: error, control, equivalent, unlabelled (M10).
- LLM (the released texts of E3, non-pilot): Claude Haiku 5.5 gets the facts (H1) and the text, and changes one
  sentence to state a subtle, plausible error (prompt mutate.md, version m1), declaring the DSL claim of its error;
  the declared claim, verified against M without bands, gives the label (error, equivalent, or undeclared if it
  does not parse).

A changed text is caught if its round trip fails, reported as caught at the changed sentence or elsewhere (a
misreading of another sentence), and by how: refuted, undecidable, a number no claim can check, a top term not
covered. Missed: the round trip passes, a wrong statement released. False alarms: the round trip failing on the
unchanged template texts (each claim certified, so any failure is one), and a control mutant refuted (D32: one that
turns undecidable abstains, reported apart). The readings are replicas 0 to 2, as in
the gate; no text here was read before.

The plasmode tier (D54, plan §14.23): `--tier plasmode` builds the script mutants of the plasmode models' template
texts (the LLM mutants start from E3's synthetic texts and are not built), with the TaiwanCredit column codes as
names, their data-dictionary descriptions and plain words in the sentences (data/labels.py); `--seeds` limits the
datasets (D54: seed 1). Results go to results/e2/<lexicon version>/text_plasmode/<extractor version>/.

Under lexicon v3 (D78), E2 runs in D75's configuration: extractor x5, the round trip's rule on unknown terms, and
D74's fixes, into results/e2/v3-d74/ (`-d74` as the other runs with D74's fixes). Under VERIFIER_GATE_LEXICON=v2 it
replays E2 as run, without the rule. `--labelled` reads the 100 labelled LLM mutants (e2_labels: the texts x3 and
x4 read, with the author's labels) with the current extractor and scores them against those labels
(llm_labelled.csv, labelled_score.csv); under v3 the LLM mutants are not built anew, since v3's handover gives the
mutator other requests, so other mutations.

Run: `uv run python -m verifier_gate.experiments.e2_text [--dry | --estimate] [--script | --llm] [--tier plasmode
--seeds 1]`. Batched; stopping is safe, the same command resumes. Writes results/e2/<lexicon version>/text/<extractor version>/: script.csv,
llm.csv, summary.csv. `--compare` puts the summaries of all extractor versions on disk side by side
(text/by_extractor.csv), from the CSVs alone. The LLM mutants always start from E3 as run (E3_SOURCE).
"""

import argparse
import json
import re
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from verifier_gate.data import dgp, labels, tiers
from verifier_gate.dsl.grammar import Claim
from verifier_gate.dsl.parse import DSLError, parse
from verifier_gate.experiments import e2_mutation as e2
from verifier_gate.experiments.build_facts import load
from verifier_gate.experiments.e3_end_to_end import RESULTS as E3_RESULTS
from verifier_gate.experiments.pilot import NAMINGS
from verifier_gate.gate import gate as g
from verifier_gate.gate import roundtrip as rt
from verifier_gate.gate.template import phrase, plasmode_label, sentence, synthetic_label, template
from verifier_gate.lexicon import predicates as p
from verifier_gate.llm import batch, extract, prompts, settings
from verifier_gate.llm.client import Client, Request, Response, stub_message
from verifier_gate.llm.handover import handover
from verifier_gate.verifier.certified import certified_plan
from verifier_gate.verifier.verify import verify

MUTATOR_VERSION = "m1"
MUTATION_SCHEMA = json.dumps(
    {"type": "object", "properties": {"sentence_id": {"type": "integer"}, "sentence": {"type": "string"}, "claim": {"type": "string"}},
     "required": ["sentence_id", "sentence", "claim"], "additionalProperties": False}, sort_keys=True)  # fmt: skip
RESULTS = Path(__file__).parents[3] / "results" / "e2"
E3_SOURCE = "v3-x3"  # E3 as run: writer prompts v3, extractor x3 (plan §14.16)
LABELS = Path(__file__).parents[3] / "results" / "e2" / "v2" / "text" / "labels"  # the labelled LLM mutants (e2_labels)
PILOT = ("syn-dominant-n50000-s1", "syn-none-n5000-s1")
COST = {"extractor": 0.00038, "mutator": 0.00097}  # synchronous USD per call, measured in the pilot (§14.15)


@dataclass
class Case:
    """One text to read, with its unchanged plan: a script mutant, an LLM mutant, or an unchanged control."""

    case_id: str
    source: str  # script, llm, control
    scenario: str
    model: str
    naming: str
    sentences: list  # [id, text]
    plan: list[Claim]  # the unchanged plan, with sentence ids
    changed: int | None  # the changed sentence (None: an omission or a control)
    info: dict  # operator, variant, original, mutant, role, ...


# --- script mutants ---------------------------------------------------------------------------------------


NAMES = {**NAMINGS, "codes": {}}  # "codes": the plasmode tier's column codes, shown as they are (D54)
NAMING = {"synthetic": "plausible", "plasmode": "codes"}
DESCRIPTIONS = {"synthetic": labels.SYNTHETIC_DESCRIPTIONS, "plasmode": labels.PLASMODE_DESCRIPTIONS}


def _label(term: str, tier: str = "synthetic") -> str:
    if term == e2.UNKNOWN:
        return "the savings balance"
    return synthetic_label()(term) if tier == "synthetic" else plasmode_label(term)


def _same(a: Claim, b: Claim) -> bool:
    return (a.kind, a.terms, a.value, a.relation, a.inner) == (b.kind, b.terms, b.value, b.relation, b.inner)


def render(draft, original: Claim | None, mutant: Claim | None, omitted: frozenset | None, tier: str = "synthetic",
           label=None) -> tuple[list, int | None]:  # fmt: skip
    """The template text with one claim's clause changed; the changed sentence's id. label: a term's words in a
    sentence (default: the tier's, and "the savings balance" for M9's term)."""
    label = label or (lambda term: _label(term, tier))
    groups = {sid: [c for c in draft.claims if c.sentence_id == sid] for sid in draft.ids()}
    changed = None
    if omitted is not None:  # M8 omission: drop the pair's clauses
        for sid, group in groups.items():
            groups[sid] = [c for c in group if omitted not in rt.claim_terms(c)]
    elif original is not None:
        sid = next(s for s, group in groups.items() if any(_same(c, original) for c in group))
        groups[sid] = [mutant if _same(c, original) else c for c in groups[sid]]
        changed = sid
    else:  # M7: replace the pair's "do not interact" clause, or add a sentence
        pair = frozenset(mutant.terms)
        sid = next((s for s, group in groups.items() for c in group if c.kind == "interaction" and frozenset(c.terms) == pair), None)
        if sid is None:
            sid = max(groups) + 1
            groups[sid] = [mutant]
        else:
            groups[sid] = [mutant if c.kind == "interaction" and frozenset(c.terms) == pair else c for c in groups[sid]]
        changed = sid
    return [[sid, sentence([phrase(c, label) for c in group])] for sid, group in groups.items() if group], changed


def script_cases(scenarios=dgp.SCENARIOS, lex: p.Lexicon | None = None) -> list[Case]:
    lex = lex or p.load()
    cases = []
    for s in scenarios:
        tier = tiers.name(s)
        X = tiers.generate(s).X
        for kind in e2.MODELS:
            facts = load(s, kind)
            point = e2.point_facts(facts, X)
            draft = template(facts, certified_plan(facts, lex), synthetic_label() if tier == "synthetic" else plasmode_label)
            base = f"{s.id}_{kind}"
            cases.append(Case(f"{base}_control", "control", s.id, kind, NAMING[tier], [list(x) for x in draft.sentences], draft.claims, None,
                              {"role": "control text"}))  # fmt: skip
            for k, m in enumerate(e2.mutants(draft.claims, facts, lex)):
                sentences, changed = render(draft, m.original, m.claim, m.omitted, tier)
                cases.append(Case(f"{base}_{k:03d}", "script", s.id, kind, NAMING[tier], sentences, draft.claims, changed, {
                    "operator": m.operator, "variant": m.variant, "original": str(m.original) if m.original else "",
                    "mutant": str(m.claim) if m.claim else f"omit {' & '.join(sorted(m.omitted))}", "role": e2.label(m, point, lex),
                    "omitted": " & ".join(sorted(m.omitted)) if m.omitted else ""}))  # fmt: skip
    return cases


# --- LLM mutants ------------------------------------------------------------------------------------------


def mutator_system() -> str:
    return prompts.load("mutate").replace("{dsl}", prompts.dsl_reference())


def mutator_request(facts_text: str, sentences: list, draw: int = 0) -> Request:
    text = "\n".join(f"{i}. {t}" for i, t in sentences)
    user = f"The facts about the model:\n\n{facts_text}\n\nThe explanation, sentence by sentence:\n\n{text}\n\nChange one sentence."
    return Request("mutator", settings.WRITER, mutator_system(), (("user", user),), MUTATION_SCHEMA, draw=draw)


def released_texts(arm: str = "haiku") -> list[dict]:
    """E3's texts released by the writer (RELEASED and RELEASED_REDUCED), outside the pilot datasets."""
    out = []
    for path in sorted((E3_RESULTS / E3_SOURCE / arm / "runs").glob("*.json")):
        run = json.loads(path.read_text())
        scenario, model, variant, draw, writer, naming = run["run_id"].split("_")
        if run["exit"] in (g.RELEASED, g.RELEASED_REDUCED) and scenario not in PILOT:
            version = run["versions"][-1]
            out.append({"run": run["run_id"], "scenario": scenario, "model": model, "naming": naming, "writer": writer,
                        "sentences": version["sentences"], "plan": [parse(line, sentence_id=sid) for sid, line, *_ in version["claims"]]})  # fmt: skip
    return out


def llm_cases(texts: list[dict], answers: dict[str, Response], requests: dict[str, Request], lex: p.Lexicon) -> list[Case]:
    cases, points = [], {}
    for t in texts:
        response = answers.get(requests[t["run"]].key)
        data = response.data if response is not None and not response.error else None
        base = {"run": t["run"], "writer": t["writer"]}
        ids = {i for i, _ in t["sentences"]}
        if not isinstance(data, dict) or int(data.get("sentence_id", -1)) not in ids:
            cases.append(Case(t["run"], "llm", t["scenario"], t["model"], t["naming"], t["sentences"], t["plan"], None, base | {"role": "no mutation"}))
            continue
        sid, new = int(data["sentence_id"]), str(data["sentence"]).strip()
        sentences = [[i, new if i == sid else s] for i, s in t["sentences"]]
        scenario = next(s for s in dgp.SCENARIOS if s.id == t["scenario"])
        point = points.setdefault((t["scenario"], t["model"]), e2.point_facts(load(scenario, t["model"]), dgp.generate(scenario).X))
        try:
            claim = labels.internal(parse(str(data["claim"])), NAMINGS[t["naming"]])
            role = {p.TRUE: "equivalent", p.FALSE: "error", p.UNDECIDABLE: "unlabelled"}[verify(claim, point, lex).value]
            declared = str(claim)
        except DSLError:
            role, declared = "undeclared", str(data["claim"])
        before = dict((i, s) for i, s in t["sentences"])[sid]
        cases.append(Case(t["run"], "llm", t["scenario"], t["model"], t["naming"], sentences, t["plan"], sid,
                          base | {"role": role, "mutant": declared, "before": before, "after": new}))  # fmt: skip
    return cases


def labelled_cases() -> list[Case]:
    """The labelled LLM mutants as the labeller saw them (e2_labels' items: the E3 text with its changed sentence),
    each with the plan of the E3 text it came from, for another extractor to read (D78)."""
    items = json.loads((LABELS / "items.json").read_text())["items"]
    key = pd.read_csv(LABELS / "key.csv").set_index("item")
    texts = {t["run"]: t for t in released_texts()}
    out = []
    for it in items:
        t = texts[key.at[it["id"], "case"]]
        out.append(Case(t["run"], "llm", t["scenario"], t["model"], t["naming"], it["sentences"], t["plan"], it["changed"],
                        {"run": t["run"], "writer": t["writer"], "item": it["id"], "role": key.at[it["id"], "mutator role"],
                         "mutant": key.at[it["id"], "mutator claim"], "before": it["before"], "after": it["after"]}))  # fmt: skip
    return out


def labelled_score(table: pd.DataFrame, version: str) -> pd.DataFrame:
    """Recall and false alarms on the labelled LLM mutants against the author's final labels and first pass, in the
    columns of e2_labels' score_final.csv and score_pass1.csv. A text with fewer than two readable extractions is
    not released (D32): caught, not at the change, and counted apart (unread)."""
    rows = []
    for name in ("final", "pass1"):
        labels = {k: v["label"] for k, v in json.loads((LABELS / f"labels_{name}.json").read_text()).items()}
        human = table["item"].map(labels)
        t = table[human.isin(["error", "ok"])].assign(human=human)
        read = t["read"].astype(bool)
        caught = t["caught"].where(read, True).astype(bool)
        at = t["caught at the change"].where(read, False).astype(bool)
        err, ok = t.human == "error", t.human == "ok"
        rows.append({"labels": name, "extractor": version, "labelled": int(human.notna().sum()), "unsure": int((human == "unsure").sum()),
                     "errors": int(err.sum()), "recall": round(caught[err].mean(), 3), "recall at the change": round(at[err].mean(), 3),
                     "no error": int(ok.sum()), "false alarms": int(caught[ok].sum()), "false-alarm rate": round(caught[ok].mean(), 3),
                     "unread": int((~read).sum())})  # fmt: skip
    return pd.DataFrame(rows)


# --- reading and scoring ----------------------------------------------------------------------------------


def context(case: Case, cache: dict) -> g.Context:
    key = (case.scenario, case.model, case.naming)
    if key not in cache:
        scenario = tiers.scenario(case.scenario)
        facts = load(scenario, case.model)
        cache[key] = g.Context(facts, certified_plan(facts), NAMES[case.naming], descriptions=DESCRIPTIONS[tiers.name(scenario)],
                               unknown_terms=p.load().version != "v2")  # D78: the rule under v3 (D75); E2 as run (v2) without it
    return cache[key]


def reading_requests(case: Case, ctx: g.Context, attempt: int = 0) -> list[Request]:
    features = extract.features_text(ctx.facts, ctx.names, ctx.descriptions)
    return [Request(**{**extract.extractor_request(case.sentences, features, 0, k).__dict__, "attempt": attempt}) for k in range(extract.EXTRACTIONS)]


def outcome(case: Case, trip: rt.RoundTrip | None) -> dict:
    if trip is None:
        return {"read": False}
    failing = trip.failing_sentences()
    at = case.changed in failing if case.changed is not None else bool(case.info.get("omitted") and case.info["omitted"] in trip.missing)
    how = Counter()
    for sid, _, value, *_ in trip.unplanned:
        if value != p.TRUE and (case.changed is None or sid == case.changed):
            how[value] += 1
    how["number"] += sum(1 for sid, _ in trip.numbers if sid == case.changed)
    how["not covered"] += len(trip.missing)
    return {"read": True, "caught": not trip.passed, "caught at the change": at, "refuted": how["false"] > 0, "undecidable": how["undecidable"] > 0,
            "number": how["number"] > 0, "not covered": how["not covered"] > 0, "failures": "; ".join(trip.failures())}  # fmt: skip


def read(cases: list[Case], client: Client, api, poll: float, log=print, ctxs: dict | None = None) -> dict[str, list]:
    """Each case's readings that could be read (llm/extract.Extraction), by case id; an answer that is not a reading
    is retried once. A case without a mutation is not read."""
    ctxs = {} if ctxs is None else ctxs
    requests = {c.case_id: reading_requests(c, context(c, ctxs)) for c in cases if c.info.get("role") != "no mutation"}
    answers = batch.resolve([r for rs in requests.values() for r in rs], client, api, poll=poll, log=log)
    readings, retry = {}, {}
    for case in cases:
        if case.case_id not in requests:
            continue
        ids = {i for i, _ in case.sentences}
        good, bad = [], []
        for r in requests[case.case_id]:
            try:
                good.append(extract.extraction_from(answers[r.key], ids, context(case, ctxs).names))
            except (ValueError, KeyError, TypeError):
                bad.append(Request(**{**r.__dict__, "attempt": 1}))
        readings[case.case_id], retry[case.case_id] = good, bad
    again = [r for rs in retry.values() for r in rs]
    if again:
        log(f"{len(again)} answer(s) not a reading, retried once")
        answers |= batch.resolve(again, client, api, poll=poll, log=log)
        for case in cases:
            for r in retry.get(case.case_id, []):
                try:
                    readings[case.case_id].append(extract.extraction_from(answers[r.key], {i for i, _ in case.sentences}, context(case, ctxs).names))
                except (ValueError, KeyError, TypeError):
                    pass
    return readings


def score(cases: list[Case], client: Client, api, poll: float, log=print) -> pd.DataFrame:
    ctxs: dict = {}
    readings = read(cases, client, api, poll, log, ctxs)
    rows = []
    for case in cases:
        ctx = context(case, ctxs)
        good = readings.get(case.case_id, [])
        trip = rt.compare(good, case.plan, [i for i, _ in case.sentences], ctx.facts, ctx.certified, unknown_terms=ctx.unknown_terms) if len(good) >= rt.EXTRACTED else None
        scenario = tiers.scenario(case.scenario)
        rows.append({"case": case.case_id, "source": case.source, "scenario": case.scenario, "n": scenario.n, "interaction": scenario.interaction,
                     "pilot dataset": case.scenario in PILOT, "model": case.model, **case.info, **outcome(case, trip)})  # fmt: skip
    return pd.DataFrame(rows)


def summarise(table: pd.DataFrame) -> pd.DataFrame:
    """Recall on errors (caught, and caught at the change), by source and operator; false alarms on controls."""
    rows = []
    t = table[table["read"] == True]  # noqa: E712
    for source, part in t.groupby("source"):
        if source == "control":
            rows.append({"source": "control texts", "group": "all", "texts": len(part), "false alarms": int(part.caught.sum()),
                         "false-alarm rate": round(float(part.caught.mean()), 3)})  # fmt: skip
            continue
        groups = [("all", part)] + list(part.groupby("operator" if source == "script" else "writer"))
        if source == "script":  # M9 by the kind of claim the invented feature takes over
            groups += [(f"M9 {v}", sub) for v, sub in part[part.operator == "M9"].groupby("variant")]
        for key, sub in groups:
            errors, controls = sub[sub.role == "error"], sub[sub.role == "control"]
            rows.append({"source": source, "group": key, "errors": len(errors),
                         "recall": round(float(errors.caught.mean()), 3) if len(errors) else float("nan"),
                         "recall at the change": round(float(errors["caught at the change"].mean()), 3) if len(errors) else float("nan"),
                         "missed": int((~errors.caught.astype(bool)).sum()) if len(errors) else 0,
                         "controls": len(controls), "controls refuted": int(controls.refuted.sum()) if len(controls) else 0,
                         "controls abstained": int((controls.undecidable & ~controls.refuted).sum()) if len(controls) else 0,
                         "equivalent": int((sub.role == "equivalent").sum()), "other": int((~sub.role.isin(["error", "control", "equivalent"])).sum())})  # fmt: skip
    return pd.DataFrame(rows)


def compare_versions(base: Path) -> pd.DataFrame:
    """The script mutants' recall and the control texts' false alarms for every extractor version under `base`,
    recomputed from each version's script.csv."""
    rows = []
    for path in sorted(base.glob("x*/script.csv")):
        summary = summarise(pd.read_csv(path))
        summary.insert(0, "extractor", path.parent.name)
        rows.append(summary)
    return pd.concat(rows, ignore_index=True)


# --- running ----------------------------------------------------------------------------------------------


def stub_responder(cases_by_text: dict[str, list[str]], texts: list[dict]):
    """No network: the mutator raises the strength of the first claim of sentence 1 by a word; the extractor reads
    each sentence as the claims its text states (known for the script's texts and the stub's changes)."""

    def respond(request: Request):
        if request.role == "mutator":
            text = request.messages[0][1].split("sentence by sentence:")[1]
            first = re.findall(r"^1\. (.*)$", text, re.M)[0]
            return stub_message({"sentence_id": 1, "sentence": first.replace("a moderate", "a strong"), "claim": "rank(\"utilization\") == 9"})
        text = request.messages[0][1].split("The text, sentence by sentence:")[1]
        sentences = re.findall(r"^(\d+)\. (.*)$", text, re.M)
        return stub_message({"sentences": [{"id": int(i), "claims": cases_by_text.get(t.strip(), []), "unexpressed": []} for i, t in sentences]})

    return respond


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry", action="store_true", help="stubs, no network, two datasets")
    parser.add_argument("--estimate", action="store_true", help="count the texts and estimate the cost, no network")
    parser.add_argument("--script", action="store_true", help="only the script mutants")
    parser.add_argument("--llm", action="store_true", help="only the LLM mutants")
    parser.add_argument("--compare", action="store_true", help="the extractor versions on disk side by side, no network")
    parser.add_argument("--tier", default="synthetic", choices=tuple(tiers.TIERS), help="plasmode: script mutants only (D54)")
    parser.add_argument("--seeds", default=None, help="comma-separated, e.g. 1 (default: all)")
    parser.add_argument("--labelled", action="store_true", help="the 100 labelled LLM mutants, read by the current extractor (D78)")
    args = parser.parse_args()
    lex = p.load()
    version = lex.version + ("-d74" if p.d74_fixes(lex) else "")  # D74's fixes: a folder of their own
    folder = "text" if args.tier == "synthetic" else f"text_{args.tier}"
    if args.compare:
        table = compare_versions(RESULTS / version / folder)
        table.to_csv(RESULTS / version / folder / "by_extractor.csv", index=False)
        pd.set_option("display.width", 250)
        print(table[table.source != "llm"].to_string(index=False))
        return
    if args.labelled:
        cases = labelled_cases()
        if args.estimate:
            print(f"{len(cases)} labelled LLM mutants; {3 * len(cases)} extractor calls; about ${3 * len(cases) * COST['extractor'] * settings.BATCH_DISCOUNT:.2f}")
            return
        out = RESULTS / version / folder / prompts.EXTRACTOR_VERSION
        table = score(cases, Client("batch"), batch.BatchAPI(), batch.POLL_SECONDS)
        out.mkdir(parents=True, exist_ok=True)
        table.to_csv(out / "llm_labelled.csv", index=False)
        result = labelled_score(table, prompts.EXTRACTOR_VERSION)
        result.to_csv(out / "labelled_score.csv", index=False)
        print(result.to_string(index=False))
        print(f"\nextractor {prompts.EXTRACTOR_VERSION}; results in {out}")
        return
    if args.tier != "synthetic":  # the LLM mutants start from E3's synthetic texts
        args.script, args.llm = True, False
    both = not (args.script or args.llm)
    scenarios = tiers.module(args.tier).SCENARIOS
    if args.seeds:
        scenarios = tuple(s for s in scenarios if s.seed in {int(x) for x in args.seeds.split(",")})
    scenarios = scenarios[:2] if args.dry else scenarios
    script = script_cases(scenarios, lex) if (both or args.script) else []
    texts = released_texts() if (both or args.llm) and not args.dry else []
    if args.dry and (both or args.llm):
        texts = [t for t in released_texts() if t["scenario"] in {s.id for s in scenarios}][:6]
    if args.estimate:
        calls = {"extractor": 3 * (len(script) + len(texts)), "mutator": len(texts)}
        cost = sum(COST[k] * n for k, n in calls.items()) * settings.BATCH_DISCOUNT
        print(f"{len(script)} script texts ({sum(c.source == 'control' for c in script)} unchanged controls), {len(texts)} released texts to mutate; "
              f"{calls} calls; about ${cost:.2f} at batch prices")  # fmt: skip
        return
    known: dict[str, list[str]] = {}
    for c in script:  # what each script sentence states, for the stub extractor
        mutated = {"original": c.info.get("original"), "mutant": c.info.get("mutant")}
        for sid, text in c.sentences:
            claims = [str(labels.external(x)) for x in c.plan if x.sentence_id == sid and str(x) != mutated["original"]]
            if sid == c.changed and mutated["mutant"] and not mutated["mutant"].startswith("omit"):
                claims.append(str(labels.external(parse(mutated["mutant"]))))
            known.setdefault(text.strip(), claims)
    if args.dry:
        scratch = Path(tempfile.mkdtemp(prefix="e2_text_dry_"))
        client, api, poll = Client("batch", cache_dir=scratch / "cache"), batch.StubBatchAPI(stub_responder(known, texts)), 0
        out = scratch / "results"
    else:
        client, api, poll = Client("batch"), batch.BatchAPI(), batch.POLL_SECONDS
        out = RESULTS / version / folder / prompts.EXTRACTOR_VERSION
    cases = list(script)
    if texts:
        ctxs: dict = {}
        facts_text = {}
        requests = {}
        for t in texts:
            ctx = context(Case(t["run"], "llm", t["scenario"], t["model"], t["naming"], [], [], None, {}), ctxs)
            key = (t["scenario"], t["model"], t["naming"])
            if key not in facts_text:
                scenario = next(s for s in dgp.SCENARIOS if s.id == t["scenario"])
                facts_text[key] = handover(ctx.facts, dgp.generate(scenario).X, "H1", ctx.certified, names=ctx.names).text
            requests[t["run"]] = mutator_request(facts_text[key], t["sentences"])
        answers = batch.resolve(list(requests.values()), client, api, poll=poll)
        cases += llm_cases(texts, answers, requests, lex)
    table = score(cases, client, api, poll)
    out.mkdir(parents=True, exist_ok=True)
    for source in ("script", "llm"):
        part = table[table.source.isin([source, "control"] if source == "script" else [source])]
        if len(part):
            part.to_csv(out / f"{source}.csv", index=False)
    on_disk = [pd.read_csv(out / f"{source}.csv") for source in ("script", "llm") if (out / f"{source}.csv").exists()]
    summary = summarise(pd.concat(on_disk, ignore_index=True))  # both sources, whichever this run read
    summary.to_csv(out / "summary.csv", index=False)
    pd.set_option("display.width", 250)
    print(summary.to_string(index=False))
    print(f"\nprompts: extractor {prompts.EXTRACTOR_VERSION}, mutator {MUTATOR_VERSION}; results in {out}")


if __name__ == "__main__":
    main()
