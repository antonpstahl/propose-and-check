"""Text-level E2 on held-out invented features (review of 20 Oct, M5 fix 3): is a statement about a quantity the
model does not have caught when the extractor's development never saw its words, and is a near-synonym read as the
real feature it resembles, and so certified?

The terms are data/invented.py, fixed before any reading. Two sources of texts, as in text-level E2
(experiments/e2_text.py):

- Template (both tiers): the template text of a certified plan with one clause about a term instead of its
  feature: E2's M9 operator with only the term changed, so the anchor "the savings balance" on the same clauses
  ties the held-out terms to E2's in-sample number. Placements: "elsewhere", a random sample of E2's M9 clauses,
  spread over the texts and the same for every term of the tier; and "on the neighbour", clauses about a
  near-synonym's neighbour, where the term read as its neighbour gives back the planned claim and the text passes.
  A paraphrase takes its neighbour's clauses: a control, every claim certified, so any failure is a false alarm.
  Synthetic tier, all 36 models; plasmode tier, seed 1 (12 models, D54).
- LLM-written (synthetic tier): E3's released texts (non-pilot, the Haiku writer, as E2's LLM mutants), with one
  sentence rewritten by Claude Haiku 5.5 so that what it says about one feature it says about the term (prompt
  mutate_invented.md, version i1). The script draws the sentence and the feature; the model only rewrites. A
  rewrite that does not name the term (its cue) or still names the feature is not used (`rewrite_problem`).

The set is built and frozen first (`--build`, results/e2/heldout/set/), from the code of E2's run, so the template
texts carry its wording and lexicon. Reading it is a separate step, after the name-normalising rule is fixed (review
M5): the readings are kept, so a deterministic rule on them is scored without new calls.

Each text is read three times by the extractor and compared with its unchanged plan, as in the gate, twice from
the same readings: as E2 ran it, and with the rule on unknown terms (gate/roundtrip.py, `unknown_terms`; review M5;
the rule's version is the hash of its functions' source, in run.json). Per text: caught, caught at the change, and
how at least two readings read the changed sentence (`change_reading`): a claim on a term that is no feature in the
rule's normal form of names, under any name; a claim of a replaced kind on a listed feature that the rest of the
sentence does not account for (mapped onto a real feature: which, and whether it is the neighbour or the replaced
feature; the extractor's mapping, since the normal form maps no synonym); content without a DSL form. A mapped
invention that passes is a statement about a quantity the model does not have, certified.

Run: `uv run python -m verifier_gate.experiments.e2_heldout --build` (the template texts, and 125 batched rewrites:
$0.007 on 20 Oct); `--estimate` counts the reading's calls and prices them; without either it reads the set with
the current extractor, under the lexicon the set was built with (VERIFIER_GATE_LEXICON=v2 once v3 is the default),
and writes results/e2/heldout/<lexicon version>-<extractor version>/: cases.csv,
readings.jsonl, by_term.csv, summary.csv, run.json. `--dry`: stubs and two datasets per tier, in a temporary folder.
"""

import argparse
import hashlib
import inspect
import json
import re
import subprocess
import tempfile
from collections import Counter
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from verifier_gate.data import invented, labels, tiers
from verifier_gate.data.invented import Term
from verifier_gate.dsl.grammar import Claim
from verifier_gate.dsl.parse import parse
from verifier_gate.experiments import e2_mutation as e2
from verifier_gate.experiments import e2_text as text
from verifier_gate.experiments.build_facts import load
from verifier_gate.experiments.pilot import NAMINGS, NOISE
from verifier_gate.gate import roundtrip as rt
from verifier_gate.gate.template import plasmode_label, synthetic_label, template
from verifier_gate.lexicon import predicates as p
from verifier_gate.llm import batch, prompts, settings
from verifier_gate.llm.client import Client, Request, stub_message
from verifier_gate.verifier.certified import certified_plan

SEED = 20261020
TIERS = ("synthetic", "plasmode")
ELSEWHERE = {"synthetic": 24, "plasmode": 12}  # clauses drawn once per tier, shared by its terms
ON_NEIGHBOUR = {"synthetic": 12, "plasmode": 8}  # clauses drawn per neighbour, shared by its near-synonym and paraphrase
LLM_ELSEWHERE, LLM_SITES = 8, 6  # rewrites: sentences drawn for "elsewhere", and used per term and placement
M9_KINDS = ("strength", "negligible", "direction", "rank", "share", "threshold", "peak")  # e2_mutation's M9
SAME_KIND = {"strength": {"strength", "negligible"}, "negligible": {"strength", "negligible"}}  # "hardly matters" either way
MUTATOR_VERSION = "i1"
REWRITE_SCHEMA = json.dumps({"type": "object", "properties": {"sentence": {"type": "string"}}, "required": ["sentence"],
                             "additionalProperties": False}, sort_keys=True)  # fmt: skip
FEATURE_CUES = {  # how an E3 sentence names a synthetic feature, by the name the writer saw: a rewrite must drop it
    "utilization": r"utili[sz]", "n_delinquencies": r"delinquen", "income": r"(?<!to-)income", "history_months": r"history",
    "dti": r"debt.to.income|\bdti\b", "n_inquiries": r"inquir", "age": r"(?<!that )(?<!this )(?<!its )\bage\b|\b(older|younger) (applicants|borrowers|people)",
    "months_at_address": r"address", "num_dependents": r"dependent", "feature_a": r"feature[ _]?a\b", "feature_b": r"feature[ _]?b\b",
}  # fmt: skip
SET = text.RESULTS / "heldout" / "set"
CODE = ("data/invented.py", "data/labels.py", "experiments/e2_heldout.py", "experiments/e2_text.py", "experiments/e2_mutation.py",
        "gate/template.py", "verifier/certified.py", "lexicon/predicates.py", "lexicon/lexicon.yaml", "llm/prompts/mutate_invented.md")  # fmt: skip
SEPARATOR = " | "  # between the replaced claims of an LLM-written case


# --- the template texts ------------------------------------------------------------------------------------


def scenarios(tier: str) -> tuple:
    every = tiers.module(tier).SCENARIOS
    return every if tier == "synthetic" else tuple(s for s in every if s.seed == 1)


def label_of(tier: str):
    return synthetic_label() if tier == "synthetic" else plasmode_label


def spread(sites: list, k: int, rng: np.random.Generator, text_of=lambda s: s[:2]) -> list:
    """k of the sites at random, spread over the texts: in a random order, each pick is the first site whose text
    has been picked least so far."""
    order = [sites[i] for i in rng.permutation(len(sites))]
    used, out = Counter(), []
    while order and len(out) < k:
        best = min(order, key=lambda s: used[text_of(s)])
        order.remove(best)
        used[text_of(best)] += 1
        out.append(best)
    return out


def template_cases(tier: str, lex: p.Lexicon, among: tuple | None = None) -> list[text.Case]:
    rng = np.random.default_rng([SEED, TIERS.index(tier)])
    drafts = {}
    for s in among or scenarios(tier):
        for kind in e2.MODELS:
            facts = load(s, kind)
            drafts[(s.id, kind)] = template(facts, certified_plan(facts, lex), label_of(tier))
    sites = [(scenario, model, c) for (scenario, model), d in drafts.items() for c in d.claims if c.kind in M9_KINDS]
    elsewhere = spread(sites, ELSEWHERE[tier], rng)
    neighbours = sorted({t.neighbour for t in invented.of(tier) if t.neighbour})
    near = {f: spread([s for s in sites if s[2].terms[0] == f], ON_NEIGHBOUR[tier], rng) for f in neighbours}
    cases = []
    for t in invented.of(tier):
        placed = [("on the neighbour", s) for s in near.get(t.neighbour, [])]
        if t.kind != "paraphrase":
            placed = [("elsewhere", s) for s in elsewhere if s[2].terms[0] != t.neighbour] + placed
        words = lambda term, t=t: t.words if term == t.name else label_of(tier)(term)  # noqa: E731
        for placement, (scenario, model, c) in placed:
            draft = drafts[(scenario, model)]
            mutant = Claim(c.kind, (t.name,), c.value, c.relation)
            sentences, changed = text.render(draft, c, mutant, None, tier, label=words)
            cases.append(text.Case(f"{scenario}_{model}_s{c.sentence_id}-{c.kind}-{c.terms[0]}_{t.name}", "template", scenario, model,
                                   text.NAMING[tier], sentences, draft.claims, changed, info(t, tier, placement, c.terms[0], [c]) | {
                                       "mutant": str(mutant), "pilot dataset": scenario in text.PILOT}))  # fmt: skip
    return cases


def info(t: Term, tier: str, placement: str, replaced: str, claims: list[Claim]) -> dict:
    return {"tier": tier, "term": t.name, "term kind": t.kind, "neighbour": t.neighbour or "", "held out": t.held_out, "placement": placement,
            "replaced": replaced, "replaced kinds": ", ".join(sorted({c.kind for c in claims})), "original": SEPARATOR.join(str(c) for c in claims),
            "role": "control" if t.kind == "paraphrase" else "error"}  # fmt: skip


# --- the LLM-written texts ---------------------------------------------------------------------------------


def _involves(c: Claim, feature: str) -> bool:
    return any(feature in k for k in rt.claim_terms(c))


def llm_sites(texts: list[dict]) -> list[tuple]:
    """(text, sentence id, feature, its claims there): a sentence whose plan states M9 kinds of claim about the
    feature, and nothing else that names it (no pair, comparison or hedge)."""
    out = []
    for t in texts:
        for sid in sorted({c.sentence_id for c in t["plan"]}):
            claims = [c for c in t["plan"] if c.sentence_id == sid]
            for f in sorted({c.terms[0] for c in claims if c.kind in M9_KINDS and rt.PAIR_SEPARATOR.strip() not in c.terms[0]}):
                about = [c for c in claims if _involves(c, f)]
                if all(c.kind in M9_KINDS and c.terms == (f,) for c in about):
                    out.append((t, sid, f, about))
    return out


def llm_jobs(texts: list[dict], rng: np.random.Generator) -> list[tuple]:
    """(term, placement, site): the sentences are drawn by script. "Elsewhere" sentences are drawn once and shared
    by the terms (each skips its neighbour's); "on the neighbour" sentences once per neighbour, under the plausible
    names if the neighbour is a planted noise feature (an opaque name is near nothing)."""
    sites = llm_sites(texts)
    run = lambda s: s[0]["run"]  # noqa: E731
    elsewhere = spread(sites, LLM_ELSEWHERE, rng, run)
    terms = [t for t in invented.of("synthetic") if t.kind != "paraphrase"]
    near = {}
    for f in sorted({t.neighbour for t in terms if t.neighbour}):
        pool = [s for s in sites if s[2] == f and (f not in NOISE or s[0]["naming"] == "plausible")]
        near[f] = spread(pool, LLM_SITES, rng, run)
    jobs = []
    for t in terms:
        jobs += [(t, "elsewhere", s) for s in [s for s in elsewhere if s[2] != t.neighbour][:LLM_SITES]]
        jobs += [(t, "on the neighbour", s) for s in near.get(t.neighbour, [])]
    return jobs


def rewrite_request(t: dict, sid: int, feature: str, term: Term) -> Request:
    shown = labels.shown(feature, NAMINGS[t["naming"]])
    description = labels.SYNTHETIC_DESCRIPTIONS.get(shown, "")
    body = "\n".join(f"{i}. {s}" for i, s in t["sentences"])
    user = (f"The explanation, sentence by sentence:\n\n{body}\n\nRewrite sentence {sid}: what it says about the feature "
            f'"{shown}" ({description}), it now says about {term.words}.')  # fmt: skip
    return Request("mutator", settings.WRITER, prompts.load("mutate_invented"), (("user", user),), REWRITE_SCHEMA)


def rewrite_problem(before: str, after: str, feature: str, term: Term) -> str:
    """Why a rewrite is not used, "" if it is: unchanged, the term not named, the feature still named, or another
    feature named more often than before (feature: the name the writer saw)."""
    if not after.strip() or after.strip() == before.strip():
        return "unchanged"
    if not re.search(term.cue, after, re.I):
        return "the term is not named"
    rest = re.sub(term.cue, " ", after, flags=re.I)
    if re.search(FEATURE_CUES[feature], rest, re.I):
        return "the feature is still named"
    if any(len(re.findall(cue, rest, re.I)) > len(re.findall(cue, before, re.I)) for name, cue in FEATURE_CUES.items() if name != feature):
        return "another feature is named"
    return ""


def llm_cases(texts: list[dict], client: Client, api, poll: float, log=print) -> list[text.Case]:
    jobs = llm_jobs(texts, np.random.default_rng([SEED, len(TIERS)]))
    requests = [rewrite_request(s[0], s[1], s[2], t) for t, _, s in jobs]
    answers = batch.resolve(requests, client, api, client.cache_dir / "batches_heldout", poll, log)  # its own lock: others run E3 meanwhile
    cases = []
    for (t, placement, (run, sid, f, about)), r in zip(jobs, requests):
        response = answers.get(r.key)
        data = response.data if response is not None and not response.error else None
        after = str(data.get("sentence", "")).strip() if isinstance(data, dict) else ""
        before = dict((i, s) for i, s in run["sentences"])[sid]
        problem = rewrite_problem(before, after, labels.shown(f, NAMINGS[run["naming"]]), t)
        sentences = [[i, after if i == sid and not problem else s] for i, s in run["sentences"]]
        extra = {"run": run["run"], "writer": run["writer"], "naming": run["naming"], "before": before, "after": after, "problem": problem}
        role = info(t, "synthetic", placement, f, about) | ({"role": "not used"} if problem else {})
        cases.append(text.Case(f"{run['run']}_s{sid}-{f}_{t.name}", "llm", run["scenario"], run["model"], run["naming"], sentences, run["plan"],
                               sid, role | extra | {"pilot dataset": False}))  # fmt: skip
    return cases


# --- the frozen set ----------------------------------------------------------------------------------------


def to_json(case: text.Case) -> dict:
    return {"case": case.case_id, "source": case.source, "scenario": case.scenario, "model": case.model, "naming": case.naming,
            "sentences": case.sentences, "plan": [[c.sentence_id, str(c)] for c in case.plan], "changed": case.changed, "info": case.info}  # fmt: skip


def from_json(d: dict) -> text.Case:
    plan = [parse(line, sentence_id=sid) for sid, line in d["plan"]]
    return text.Case(d["case"], d["source"], d["scenario"], d["model"], d["naming"], d["sentences"], plan, d["changed"], d["info"])


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def code() -> dict:
    """The commit the code is checked out at (empty outside a repository, e.g. an archive of a commit), and the hashes
    of the files the set's texts depend on, which identify the code either way."""
    root = Path(__file__).parents[1]
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True).stdout.strip()
    return {"commit": commit, "sha256": {name: sha256(root / name) for name in CODE}}


def write_set(cases: list[text.Case], folder: Path, lex: p.Lexicon) -> dict:
    folder.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(invented.table()).to_csv(folder / "terms.csv", index=False)
    for source in ("template", "llm"):
        with open(folder / f"{source}.jsonl", "w") as f:
            for case in cases:
                if case.source == source:
                    f.write(json.dumps(to_json(case), sort_keys=True) + "\n")
    rows = pd.DataFrame([{"source": c.source, **c.info} for c in cases])
    counts = rows.groupby(["tier", "source", "term kind", "held out", "placement", "role"]).size().reset_index(name="texts")
    manifest = {
        "built": date.today().isoformat(), "seed": SEED, "lexicon": lex.version, "code": code(),
        "sizes": {"elsewhere": ELSEWHERE, "on the neighbour": ON_NEIGHBOUR, "llm elsewhere drawn": LLM_ELSEWHERE, "llm per term and placement": LLM_SITES},
        "mutator": {"version": MUTATOR_VERSION, "model": settings.WRITER, "prompt sha256": hashlib.sha256(prompts.load("mutate_invented").encode()).hexdigest()},
        "sha256": {name: sha256(folder / name) for name in ("terms.csv", "template.jsonl", "llm.jsonl")},
        "texts": counts.to_dict("records"),
        "rewrites not used": dict(Counter(c.info["problem"] for c in cases if c.source == "llm" and c.info["problem"])),
    }  # fmt: skip
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    return manifest


def load_set(folder: Path = SET) -> list[text.Case]:
    return [from_json(json.loads(line)) for source in ("template", "llm") for line in (folder / f"{source}.jsonl").read_text().splitlines()]


# --- reading and scoring -----------------------------------------------------------------------------------


def change_reading(case: text.Case, readings: list, listed: set[str]) -> dict:
    """How at least EXTRACTED readings read the changed sentence: a claim there on a term the model does not have,
    under any name; a claim of a replaced kind on a listed feature that is not one of the sentence's remaining
    planned claims (mapped); content without a DSL form."""
    sid = case.changed
    originals = {rt.canonical(parse(line)) for line in case.info["original"].split(SEPARATOR)}
    rest = {rt.canonical(c) for c in case.plan if c.sentence_id == sid and rt.canonical(c) not in originals}
    kinds = set().union(*(SAME_KIND.get(k, {k}) for k in case.info["replaced kinds"].split(", ")))
    unknown, unexpressed, mapped = 0, 0, Counter()
    for reading in readings:
        claims = [rt.normalised(c, listed) for c in reading.claims if c.sentence_id == sid]  # names as the rule reads them
        unknown += any(name not in listed for c in claims for k in rt.claim_terms(c) for name in k)
        unexpressed += sid in reading.unexpressed
        mapped.update({c.terms[0] for c in claims if c.kind in kinds and c.terms[0] in listed and rt.canonical(c) not in rest})
    onto = sorted(f for f, n in mapped.items() if n >= rt.EXTRACTED)
    return {"read as unknown": unknown >= rt.EXTRACTED, "mapped": bool(onto), "mapped onto": ", ".join(onto),
            "mapped onto the neighbour": case.info["neighbour"] in onto, "mapped onto the replaced feature": case.info["replaced"] in onto,
            "unexpressed": unexpressed >= rt.EXTRACTED, "readings unknown": unknown, "readings": len(readings)}  # fmt: skip


def score(cases: list[text.Case], client: Client, api, poll: float, log=print) -> tuple[pd.DataFrame, list[dict]]:
    ctxs: dict = {}
    readings = text.read(cases, client, api, poll, log, ctxs)
    rows, kept = [], []
    for case in cases:
        ctx = text.context(case, ctxs)
        good = readings.get(case.case_id, [])
        trips = {rule: rt.compare(good, case.plan, [i for i, _ in case.sentences], ctx.facts, ctx.certified, unknown_terms=rule)
                 for rule in (False, True)} if len(good) >= rt.EXTRACTED else {False: None, True: None}  # fmt: skip
        listed = {f.name for f in ctx.facts.features}
        row = {"case": case.case_id, "source": case.source, "scenario": case.scenario, "model": case.model, "naming": case.naming,
               **case.info, **text.outcome(case, trips[False])}  # fmt: skip
        if trips[False] is not None:
            ruled = text.outcome(case, trips[True])
            row |= change_reading(case, good, listed) | {"caught with the rule": ruled["caught"], "caught at the change with the rule": ruled["caught at the change"]}
            row["released and mapped"] = row["mapped"] and not row["caught"]
            row["released and mapped with the rule"] = row["mapped"] and not row["caught with the rule"]
        rows.append(row)
        kept.append({"case": case.case_id, "readings": [{"claims": [[c.sentence_id, str(c)] for c in r.claims],
                                                          "unexpressed": {str(k): v for k, v in r.unexpressed.items()}} for r in good]})  # fmt: skip
    return pd.DataFrame(rows), kept


def rule_version() -> str:
    """The rule on unknown terms as read: a hash of its functions' source (roundtrip.py's own hash moves with
    unrelated edits)."""
    return hashlib.sha256("".join(inspect.getsource(f) for f in (rt.normal_name, rt.normalised, rt.unknown)).encode()).hexdigest()


def interval(k: int, n: int, level: float = 0.95) -> tuple[float, float]:
    """Clopper-Pearson."""
    if n == 0:
        return float("nan"), float("nan")
    a = (1 - level) / 2
    return (float(stats.beta.ppf(a, k, n - k + 1)) if k else 0.0, float(stats.beta.ppf(1 - a, k + 1, n - k)) if k < n else 1.0)


def _rates(g: pd.DataFrame) -> dict:
    """The round trip fails: for errors caught (recall), for paraphrases blocked (false alarms); as E2 ran it, and
    with the rule on unknown terms. A paraphrase mapped onto its neighbour is read as the feature it names, which is
    right."""
    n, out, error = len(g), {"texts": len(g)}, (g.role == "error").all()
    for rule, suffix in ((False, ""), (True, " with the rule")):
        fails = int(g[f"caught{suffix}"].sum())
        lo, hi = interval(fails, n)
        out |= {f"round trip fails{suffix}": fails, f"rate{suffix}": round(fails / n, 3) if n else float("nan"),
                f"95% from{suffix}": round(lo, 3), f"95% to{suffix}": round(hi, 3),
                f"released and mapped{suffix}": int(g[f"released and mapped{suffix}"].sum()) if error else float("nan")}  # fmt: skip
    return out | {"fails at the change": int(g["caught at the change"].sum()), "read as unknown": int(g["read as unknown"].sum()),
                  "mapped": int(g.mapped.sum()), "mapped onto the neighbour": int(g["mapped onto the neighbour"].sum()),
                  "unexpressed": int(g.unexpressed.sum())}  # fmt: skip


def by_term(table: pd.DataFrame) -> pd.DataFrame:
    t = table[(table.read == True) & table.role.isin(["error", "control"])]  # noqa: E712
    rows = []
    keys = ["tier", "source", "term", "term kind", "neighbour", "held out"]
    for key, g in t.groupby(keys, sort=False):
        for placement, part in [("all", g)] + list(g.groupby("placement")):
            rows.append(dict(zip(keys, key)) | {"placement": placement} | _rates(part))
    return pd.DataFrame(rows)


def group_of(row) -> str:
    if row["term kind"] == "paraphrase":
        return "paraphrases (controls)"
    if not row["held out"]:
        return f"anchor: {row['term']}"
    return f"held out: {row['term kind']}"


def summarise(table: pd.DataFrame) -> pd.DataFrame:
    t = table[(table.read == True) & table.role.isin(["error", "control"])].copy()  # noqa: E712
    t["group"] = t.apply(group_of, axis=1)
    rows = []
    for (tier, source, group), g in t.groupby(["tier", "source", "group"]):
        for placement, part in [("all", g)] + list(g.groupby("placement")):
            rows.append({"tier": tier, "source": source, "group": group, "placement": placement} | _rates(part))
    return pd.DataFrame(rows)


# --- running -----------------------------------------------------------------------------------------------


def stub_responder(known: dict[str, list[str]]):
    """No network: a rewrite puts the term's words in place of the sentence; the extractor reads a sentence as the
    claims `known` gives it, and nothing for a sentence it does not know."""

    def respond(request: Request):
        message = request.messages[0][1]
        if request.role == "mutator":
            words = re.search(r"it now says about (.*)\.$", message).group(1)
            return stub_message({"sentence": f"Default risk increases with {words}."})
        sentences = re.findall(r"^(\d+)\. (.*)$", message.split("The text, sentence by sentence:")[1], re.M)
        return stub_message({"sentences": [{"id": int(i), "claims": known.get(t.strip(), []), "unexpressed": []} for i, t in sentences]})

    return respond


def known_readings(cases: list[text.Case]) -> dict[str, list[str]]:
    """What each template sentence states, for the stub extractor: the plan's claims, and the mutant's in place of
    the original (a paraphrase read as its feature, an invented term under its own name)."""
    known: dict[str, list[str]] = {}
    for c in cases:
        for sid, sentence in c.sentences:
            if sid == c.changed and c.source == "llm":
                continue
            claims = [x for x in c.plan if x.sentence_id == sid and not (sid == c.changed and str(x) == c.info["original"])]
            if sid == c.changed and c.source == "template" and c.info["role"] == "error":
                claims.append(parse(c.info["mutant"]))
            elif sid == c.changed and c.source == "template":
                claims.append(parse(c.info["original"]))
            known.setdefault(sentence.strip(), [str(labels.external(x)) for x in claims])
    return known


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true", help="build and freeze the set: the template texts and the LLM rewrites")
    parser.add_argument("--estimate", action="store_true", help="count the set's texts and price their reading, no network")
    parser.add_argument("--dry", action="store_true", help="build and read with stubs, two datasets per tier, in a temporary folder")
    args = parser.parse_args()
    lex = p.load()
    if args.dry:
        scratch = Path(tempfile.mkdtemp(prefix="e2_heldout_dry_"))
        among = {tier: scenarios(tier)[:2] for tier in TIERS}
        cases = [c for tier in TIERS for c in template_cases(tier, lex, among[tier])]
        texts = [t for t in text.released_texts() if t["scenario"] in {s.id for s in among["synthetic"]}]
        client, api = Client("batch", cache_dir=scratch / "cache"), batch.StubBatchAPI(stub_responder({}))
        cases += llm_cases(texts, client, api, 0)
        write_set(cases, scratch / "set", lex)
        cases = load_set(scratch / "set")
        api = batch.StubBatchAPI(stub_responder(known_readings(cases)))
        table, kept = score([c for c in cases if c.info["role"] != "not used"], client, api, 0)
        out = scratch / "read"
    elif args.build:
        cases = [c for tier in TIERS for c in template_cases(tier, lex)]
        cases += llm_cases(text.released_texts(), Client("batch"), batch.BatchAPI(), batch.POLL_SECONDS)
        manifest = write_set(cases, SET, lex)
        print(pd.DataFrame(manifest["texts"]).to_string(index=False))
        print(f"\nrewrites not used: {manifest['rewrites not used']}; set in {SET}")
        return
    else:
        built = json.loads((SET / "manifest.json").read_text())["lexicon"]
        if lex.version != built:  # the set's plans and wording are certified under that lexicon
            raise SystemExit(f"the set was built under lexicon {built}: read it under the same (VERIFIER_GATE_LEXICON={built})")
        cases = [c for c in load_set() if c.info["role"] != "not used"]
        if args.estimate:
            calls = 3 * len(cases)
            print(f"{len(cases)} texts ({sum(c.source == 'template' for c in cases)} template, {sum(c.source == 'llm' for c in cases)} LLM-written); "
                  f"{calls} extractor calls; about ${text.COST['extractor'] * calls * settings.BATCH_DISCOUNT:.2f} at batch prices before retries")  # fmt: skip
            return
        table, kept = score(cases, Client("batch"), batch.BatchAPI(), batch.POLL_SECONDS)
        out = text.RESULTS / "heldout" / f"{lex.version}-{prompts.extractor_version()}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "run.json").write_text(json.dumps({
        "read": date.today().isoformat(), "extractor": prompts.extractor_version(), "lexicon": lex.version,
        "rule on unknown terms sha256": rule_version(), "set sha256": json.loads((SET / "manifest.json").read_text())["sha256"] if not args.dry else {},
    }, indent=1) + "\n")  # fmt: skip
    table.to_csv(out / "cases.csv", index=False)
    with open(out / "readings.jsonl", "w") as f:
        f.writelines(json.dumps(k) + "\n" for k in kept)
    terms, summary = by_term(table), summarise(table)
    terms.to_csv(out / "by_term.csv", index=False)
    summary.to_csv(out / "summary.csv", index=False)
    pd.set_option("display.width", 250)
    print(summary.to_string(index=False))
    print(f"\nextractor {prompts.extractor_version()}, lexicon {lex.version}; results in {out}")


if __name__ == "__main__":
    main()
