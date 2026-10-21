"""E3 read by another vendor's model and counted by the release rule (D69; the review of 20 Oct, M3, fixes 2 and 3).

E3 scores both arms with three more calls of the gate's own extractor request (Claude Haiku 5.5, prompt x3,
replicas 3 to 5): a retest of the gate's reader. It cannot find what that reader misses every time, and the repair
loop rewrites a text until that reader passes it, so the gate-on arm is the more exposed to its blind spots. Here
the same texts are read by OpenAI's GPT-6 Luna under the same request (x3's prompts, the features as the writer saw
them, the run's draw, replicas 3 to 5): only the model differs. Its readings are scored by E3's rule (a claim counts
if at least two readings find it, and is verified against M and T), under the lexicon and with the extractor
version the run used, and with the round trip's rule on unknown terms as the run had it (SOURCES: all three are
passed explicitly, so a newer default does not change an old run's scores). A run with both tiers (v4-x5-m5: synthetic and plasmode) is reported per tier.

Standards (residual_by_standard.csv). A text counts if it states
- refuted: a claim false against M (E3's P_U);
- release rule: a claim false or undecidable against M. The gate never releases an undecidable claim as stated
  (D30), and a hedge is never undecidable (lexicon/predicates.unsettled makes it true or false), so an undecidable
  claim is one stated as settled. This is the gate's own criterion, applied to what it released;
- release rule or unchecked: also content no DSL form expresses (in at least two readings) or a number no claim can
  check, so that no reading checked it;
- against T: a claim false against the planted truth.
Each for the gate's reader (haiku), the other vendor's (luna), either of them and both, on the texts both scored;
per tier;
per arm, the gate-on arm also split into LLM-written releases and templates. 95% intervals come from a bootstrap
over the datasets (CLUSTER_DRAWS draws of the non-pilot datasets with replacement), since the texts of one dataset
share its model. Rows "author labels" count the author's labels of the gate's flags (e2_false_alarms, D52) by the
release rule (v3-x3 only): a lower bound, since only flagged texts were labelled. agreement.csv: per arm, how often the two
readers agree on a text's verdict (Cohen's kappa) and on its claims, and how often Luna's DSL lines do not parse.

Haiku's readings are E3's own, from the cache ($0); the scores are recomputed from them and the run stops if one
differs from E3's rows.csv. Luna's are new: synchronous, in parallel, priced first (`--estimate`) and capped
(`--budget`). `--pilot N` first reads N runs of the pilot datasets (written to <out>/luna/pilot/). The setting was
fixed before any reading: x3's prompts unchanged, Luna at the reasoning effort the extractor request carries
(medium, the API's default, as for the critic).

Run:
  uv run python -m verifier_gate.experiments.e3_independent --estimate     # no network
  uv run python -m verifier_gate.experiments.e3_independent --pilot 8      # the pilot datasets
  uv run python -m verifier_gate.experiments.e3_independent --budget 6     # every non-pilot text
  uv run python -m verifier_gate.experiments.e3_independent --tables       # from the cache only, $0
  uv run python -m verifier_gate.experiments.e3_independent --source v4-x5-m5 --tier synthetic   # the rerun's synthetic tier
(v4-x5-m5's plasmode half is rerun apart after a fix, D73, and read when that run exists.)
Writes results/e3/<source>/independent/: <reader>/texts.csv (one row per run and arm), <reader>/claims.csv,
agreement.csv and residual_by_standard.csv.
"""

import argparse
import json
from collections import Counter
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from verifier_gate.data import tiers
from verifier_gate.experiments import e2_text
from verifier_gate.experiments import e3_end_to_end as e3
from verifier_gate.experiments.build_facts import load
from verifier_gate.experiments.e2_critic import resolve
from verifier_gate.gate import gate as g
from verifier_gate.gate import roundtrip as rt
from verifier_gate.lexicon import predicates as p
from verifier_gate.llm import extract, prompts, settings
from verifier_gate.llm.client import Client, Request, log_records, sha
from verifier_gate.verifier.certified import certified_plan
from verifier_gate.verifier.verify import verify

READERS = {"haiku": settings.EXTRACTOR, "luna": settings.CRITIC}  # the gate's own reader; another vendor's
SOURCE = e2_text.E3_SOURCE  # E3 as run: writer prompts v3, extractor x3
SOURCES = {  # each E3 run's lexicon, extractor version and the round trip's rule on unknown terms (gate/roundtrip.py)
    "v3-x3": {"lexicon": "v2", "extractor": "x3", "unknown_terms": False},
    "v4-x5-m5": {"lexicon": "v3", "extractor": "x5", "unknown_terms": True},  # lexicon v3, writer prompts v4 (D63-D67), both tiers; as run: VERIFIER_GATE_D74=0
    "v4-x5-m5-d74": {"lexicon": "v3", "extractor": "x5", "unknown_terms": True},  # the same with D74's fixes
}
WRITER_ARM = "haiku"  # E3's main arm: Claude Haiku 5.5 writes
SEED = 20261021
CLUSTER_DRAWS = 2000
OUT_TOKENS = 2500  # Luna's output per reading, reasoning included, before the pilot measures it
COUNTS = ("claims", "false M", "undecidable M", "false T", "hedges", "no DSL form", "unchecked numbers", "not covered")
STANDARDS = {
    "refuted": lambda r: r["false M"] > 0,
    "release rule": lambda r: r["false M"] + r["undecidable M"] > 0,
    "release rule or unchecked": lambda r: r["false M"] + r["undecidable M"] + r["no DSL form"] + r["unchecked numbers"] > 0,
    "against T": lambda r: r["false T"] > 0,
}
GROUPS = {"off": ("off", None), "on": ("on", None), "on, LLM-written": ("on", "LLM-written"), "on, template": ("on", "template")}


def out_folder(source: str = SOURCE) -> Path:
    return e3.RESULTS / source / "independent"


def lexicon(source: str = SOURCE) -> p.Lexicon:
    """The lexicon an E3 run was scored with: lexicon_<version>.yaml if a newer one has replaced it, else the current file."""
    version = SOURCES[source]["lexicon"]
    kept = p.LEXICON_PATH.with_name(f"lexicon_{version}.yaml")
    lex = p.load(kept if kept.exists() else p.LEXICON_PATH)
    if lex.version != version:
        raise ValueError(f"E3 {source} was scored with lexicon {version}; found {lex.version}")
    return lex


def extractor_system(source: str = SOURCE) -> str:
    """The system prompt of the run's extractor: x3's as kept (prompts.historical_extractor_system, hash-checked; x3's user prompt is today's
    extract.md, checked too), or the current one if the run used the current version."""
    version = SOURCES[source]["extractor"]
    if version == "x3":
        if sha(prompts.load("extract")) != prompts.EXTRACTOR_HISTORY["x3"]["extract"]:
            raise ValueError("extract.md is no longer x3's: the scoring request would differ from E3's")
        return prompts.historical_extractor_system("x3")
    if prompts.EXTRACTOR_VERSION != version:
        raise ValueError(f"E3 {source} ran with extractor {version}; the current one is {prompts.EXTRACTOR_VERSION}")
    return prompts.extractor_system()


# --- the texts and their readings -------------------------------------------------------------------------


def texts(pilot: bool = False, source: str = SOURCE, folder: Path | None = None) -> list[dict]:
    """Both arms of E3's Haiku runs outside the pilot datasets (inside them with `pilot`), as e3_end_to_end.texts_of
    takes them: the writer's first draft (off) and the released text (on: RELEASED, RELEASED_REDUCED or TEMPLATE)."""
    out = []
    for path in sorted((folder or e3.RESULTS / source / WRITER_ARM / "runs").glob("*.json")):
        run = json.loads(path.read_text())
        scenario, model, variant, draw, _, naming = run["run_id"].split("_")
        if (scenario in e2_text.PILOT) != pilot:
            continue
        first = next((v for v in run["versions"] if v["source"] in ("proposer", "format retry")), None)
        released = run["versions"][-1] if run["exit"] in e3.RELEASING and run["versions"] else None
        base = {"run": run["run_id"], "scenario": scenario, "tier": tiers.name(tiers.scenario(scenario)), "model": model,
                "handover": variant, "draw": int(draw.lstrip("d")), "naming": naming, "exit": run["exit"]}  # fmt: skip
        if first:
            out.append(base | {"arm": "off", "kind": "draft", "sentences": first["sentences"]})
        if released:
            out.append(base | {"arm": "on", "kind": "template" if run["exit"] == g.TEMPLATE else "LLM-written", "sentences": released["sentences"]})
    return out


def context(text: dict, cache: dict, lex: p.Lexicon, unknown_terms: bool = False) -> g.Context:
    """The gate's context of a text (as e2_text.context, either tier), with the certified plan under `lex` and the
    round trip's rule on unknown terms on or off."""
    key = (text["scenario"], text["model"], text["naming"])
    if key not in cache:
        scenario = tiers.scenario(text["scenario"])
        facts = load(scenario, text["model"])
        cache[key] = g.Context(facts, certified_plan(facts, lex), e2_text.NAMES[text["naming"]], descriptions=e2_text.DESCRIPTIONS[tiers.name(scenario)],
                               unknown_terms=unknown_terms)  # fmt: skip
    return cache[key]


def requests_for(text: dict, ctx: g.Context, model: str, system: str, attempt: int = 0) -> list[Request]:
    """E3's scoring request for a text (replicas 3 to 5 at the run's draw, x3's prompts), sent to `model`."""
    features = extract.features_text(ctx.facts, ctx.names, ctx.descriptions)
    base = [extract.extractor_request(text["sentences"], features, text["draw"], k) for k in e3.SCORING_REPLICAS]
    return [replace(r, model=model, system=system, attempt=attempt, role="extractor" if model == settings.EXTRACTOR else "scorer") for r in base]


def fetch(reqs: list[Request], client: Client, budget: float, log=print) -> dict:
    """Answers by key. The gate's reader only from the cache (E3's readings: a missing one is an error); another
    model's from the cache or the API, in parallel, up to `budget` dollars of new calls."""
    if all(r.model == settings.EXTRACTOR for r in reqs):
        answers = {r.key: a for r in reqs if (a := client.lookup(r)) is not None}
        if len(answers) < len({r.key for r in reqs}):
            raise ValueError(f"{len({r.key for r in reqs}) - len(answers)} of E3's scoring readings are not in the cache")
        return answers
    return resolve(reqs, client, budget, log=log)


def usable(text: dict, ctx: g.Context, reqs: list[Request], answers: dict) -> tuple[list, list[Request]]:
    """The readings among the answers, and the requests whose answer came back but is not a reading (an answer
    not received, at the budget or after an API failure, is neither: a rerun asks again)."""
    ids, good, bad = {i for i, _ in text["sentences"]}, [], []
    for r in reqs:
        answer = answers.get(r.key)
        if answer is None or answer.error == "api":
            continue
        try:
            good.append(extract.extraction_from(answer, ids, ctx.names))
        except (ValueError, KeyError, TypeError, AttributeError):
            bad.append(r)
    return good, bad


def read(items: list[dict], model: str, client: Client, budget: float, ctxs: dict, lex: p.Lexicon, system: str, unknown_terms: bool = False,
         log=print) -> dict[tuple, list]:  # fmt: skip
    """The usable readings of each text, with one retry of an answer that is not a reading (as in E3)."""
    reqs = {(t["run"], t["arm"]): requests_for(t, context(t, ctxs, lex, unknown_terms), model, system) for t in items}
    answers = fetch([r for rs in reqs.values() for r in rs], client, budget, log)
    readings, retry = {}, {}
    for t in items:
        key = (t["run"], t["arm"])
        readings[key], bad = usable(t, context(t, ctxs, lex, unknown_terms), reqs[key], answers)
        retry[key] = [replace(r, attempt=1) for r in bad]
    again = [r for rs in retry.values() for r in rs]
    if again:
        log(f"{model}: {len(again)} answer(s) not a reading, retried once")
        answers |= fetch(again, client, max(budget - sum(a.cost for a in answers.values() if not a.cached), 0.0), log)
        for t in items:
            key = (t["run"], t["arm"])
            readings[key] += usable(t, context(t, ctxs, lex, unknown_terms), retry[key], answers)[0]
    return readings


def score_text(sentences: list, readings: list, ctx: g.Context, truth, lex: p.Lexicon) -> tuple[dict, list[dict]]:
    """E3's score of a text (e3_end_to_end.score, with the lexicon passed), the undecidable claims by reason code, the
    readings' DSL lines that did not parse, and the claims themselves."""
    lines = {"lines": sum(len(r.claims) + len(r.format_errors) for r in readings), "unparsed lines": sum(len(r.format_errors) for r in readings)}
    if len(readings) < rt.EXTRACTED:
        return {"scored": False, "readings": len(readings)} | lines, []
    trip = rt.compare(readings, [], [i for i, _ in sentences], ctx.facts, ctx.certified, lex=lex, unknown_terms=ctx.unknown_terms)
    claims = [{"sentence id": sid, "claim": line, "verdict": value, "code": code} for sid, line, value, code, *_ in trip.unplanned]
    on_t = [verify(c["claim"], truth, lex).value for c in claims]
    codes = Counter(c["code"] for c in claims if c["verdict"] == p.UNDECIDABLE)
    out = {
        "scored": True, "readings": len(readings), "claims": len(claims), "sentences": len(sentences),
        "words": sum(len(t.split()) for _, t in sentences),
        "false M": sum(c["verdict"] == p.FALSE for c in claims), "undecidable M": sum(c["verdict"] == p.UNDECIDABLE for c in claims),
        "false T": sum(v == p.FALSE for v in on_t), "hedges": sum(c["claim"].startswith("unsettled(") for c in claims),
        "unchecked numbers": len(trip.numbers), "no DSL form": len(trip.gap), "not covered": len(trip.missing),
        "emphasis": len(trip.emphasis), "ambiguous": len(trip.ambiguous),
    }  # fmt: skip
    return out | {f"undecidable M, {code}": codes.get(code, 0) for code in p.CODES} | lines, claims


def score_all(items: list[dict], model: str, client: Client, budget: float, lex: p.Lexicon, system: str, unknown_terms: bool = False,
              log=print) -> tuple[pd.DataFrame, pd.DataFrame]:  # fmt: skip
    ctxs, truths = {}, {}
    readings = read(items, model, client, budget, ctxs, lex, system, unknown_terms, log)
    rows, claims = [], []
    for t in items:
        truth = truths.setdefault(t["scenario"], load(tiers.scenario(t["scenario"]), "T"))
        out, listed = score_text(t["sentences"], readings[t["run"], t["arm"]], context(t, ctxs, lex, unknown_terms), truth, lex)
        rows.append({k: v for k, v in t.items() if k != "sentences"} | {"reader": model} | out)
        claims += [{"run": t["run"], "arm": t["arm"]} | c for c in listed]
    return pd.DataFrame(rows), pd.DataFrame(claims, columns=["run", "arm", "sentence id", "claim", "verdict", "code"])


def check_against_e3(table: pd.DataFrame, source: str = SOURCE) -> None:
    """The gate's reader's scores, recomputed here, must be E3's (rows.csv), field by field."""
    rows = pd.read_csv(e3.RESULTS / source / WRITER_ARM / "rows.csv").set_index("run")
    wrong = []
    for _, r in table.iterrows():
        e3_row = rows.loc[r["run"]]
        if bool(r["scored"]) != bool(e3_row[f"{r['arm']} scored"]):
            wrong.append((r["run"], r["arm"], "scored"))
        elif r["scored"]:
            wrong += [(r["run"], r["arm"], c) for c in COUNTS if int(r[c]) != int(e3_row[f"{r['arm']} {c}"])]
    if wrong:
        raise ValueError(f"{len(wrong)} score(s) differ from E3's rows.csv, e.g. {wrong[:3]}")


# --- the tables -------------------------------------------------------------------------------------------


def verdicts(haiku: pd.DataFrame, luna: pd.DataFrame) -> pd.DataFrame:
    """One row per text both readers scored: its group and, per standard, each reader's verdict and the two combined."""
    keys = ["run", "arm"]
    both = haiku[haiku.scored == True].merge(luna[luna.scored == True], on=keys, suffixes=(" haiku", " luna"))  # noqa: E712
    out = both[keys].copy()
    out["scenario"], out["tier"], out["kind"] = both["scenario haiku"], both["tier haiku"], both["kind haiku"]
    for name, rule in STANDARDS.items():
        for reader in ("haiku", "luna"):
            out[f"{name} | {reader}"] = rule({c: both[f"{c} {reader}"] for c in COUNTS}).astype(bool)
        out[f"{name} | either"] = out[f"{name} | haiku"] | out[f"{name} | luna"]
        out[f"{name} | both"] = out[f"{name} | haiku"] & out[f"{name} | luna"]
    return out


def in_group(table: pd.DataFrame, group: str) -> pd.Series:
    arm, kind = GROUPS[group]
    return (table.arm == arm) & ((table.kind == kind) if kind else True)


def cluster_draws(n: int, draws: int = CLUSTER_DRAWS, seed: int = SEED) -> np.ndarray:
    """Bootstrap draws of the datasets (rows: draws; columns: dataset indices), one set shared by every quantity."""
    return np.random.default_rng(seed).integers(0, n, size=(draws, n))


def by_dataset(table: pd.DataFrame, column: str, mask: pd.Series, scenarios: list[str]) -> tuple[np.ndarray, np.ndarray]:
    part = table[mask]
    k = part.groupby("scenario")[column].sum().reindex(scenarios, fill_value=0).to_numpy(float)
    n = part.groupby("scenario")[column].size().reindex(scenarios, fill_value=0).to_numpy(float)
    return k, n


def interval(values: np.ndarray) -> tuple[float, float]:
    values = values[np.isfinite(values)]
    return (round(float(np.percentile(values, 2.5)), 4), round(float(np.percentile(values, 97.5)), 4)) if len(values) else (np.nan, np.nan)


def residual_table(table: pd.DataFrame, draws: int = CLUSTER_DRAWS) -> pd.DataFrame:
    """P_U per tier (and over both, if there are two), standard, reader and group with 95% dataset-bootstrap
    intervals, and E_U = 1 - P_U(on) / P_U(off)."""
    parts = [(tier, table[table.tier == tier]) for tier in sorted(table.tier.unique())]
    parts += [("both tiers", table)] if len(parts) > 1 else []
    return pd.concat([residual_part(part, draws).assign(tier=tier) for tier, part in parts], ignore_index=True)


def residual_part(table: pd.DataFrame, draws: int) -> pd.DataFrame:
    scenarios = sorted(table.scenario.unique())
    idx = cluster_draws(len(scenarios), draws)
    rows = []
    for name in STANDARDS:
        for reader in ("haiku", "luna", "either", "both"):
            column, row, boot = f"{name} | {reader}", {"standard": name, "reader": reader}, {}
            for group in GROUPS:
                k, n = by_dataset(table, column, in_group(table, group), scenarios)
                with np.errstate(divide="ignore", invalid="ignore"):
                    boot[group] = k[idx].sum(1) / n[idx].sum(1)
                lo, hi = interval(boot[group])
                row |= {f"texts {group}": int(n.sum()), f"P_U {group}": round(k.sum() / n.sum(), 4) if n.sum() else np.nan,
                        f"{group} lo": lo, f"{group} hi": hi}  # fmt: skip
            with np.errstate(divide="ignore", invalid="ignore"):
                e_u = 1 - boot["on"] / boot["off"]
            row["E_U"] = round(1 - row["P_U on"] / row["P_U off"], 4) if row["P_U off"] else np.nan
            row["E_U lo"], row["E_U hi"] = interval(e_u)
            rows.append(row)
    return pd.DataFrame(rows)


def labelled_rows(n_on: int, n_llm: int, source: str = SOURCE) -> pd.DataFrame:
    """The author's labels of the gate's flags (e2_false_alarms, D52) counted by the release rule: a gate-on text
    counts if a flagged claim false (refuted), or false or undecidable (release rule), against M is labelled a real
    error. The flags of x3's scoring readings (the set behind the paper's 0.16%), and of x3's and x4's. A lower
    bound: only flagged texts were labelled, and only LLM-written releases were read."""
    folder = e2_text.RESULTS / SOURCES[source]["lexicon"] / "text" / "false_alarms"
    labels_ = json.loads((folder / "labels.json").read_text())
    key = pd.read_csv(folder / "key.csv")
    key["human"] = [labels_.get(r.item, {}).get("labels", {}).get(str(r.claim)) for r in key.itertuples()]
    rows = []
    for name, flags in (("x3 flags", key.x3 == True), ("x3 and x4 flags", (key.x3 == True) | (key.x4 == True))):  # noqa: E712
        for standard, kinds in (("refuted", ("false",)), ("release rule", ("false", "undecidable"))):
            part = key[flags & key.kind.isin(kinds)]
            errors = set(part[part.human == "error"].run)
            opened = set(part[part.human == "unsure"].run) - errors
            rows.append({"standard": standard, "reader": f"author labels, {name} only", "tier": "synthetic", "texts on": n_on, "P_U on": round(len(errors) / n_on, 4),
                         "texts on, LLM-written": n_llm, "P_U on, LLM-written": round(len(errors) / n_llm, 4),
                         "note": f"{len(errors)} text(s) with a labelled error ({', '.join(sorted(part[part.run.isin(errors) & (part.human == 'error')].item.unique()))}), "
                                 f"{len(opened)} more open; flagged texts only, a lower bound"})  # fmt: skip
    return pd.DataFrame(rows)


def kappa(a: pd.Series, b: pd.Series) -> float:
    a, b = a.astype(bool).to_numpy(), b.astype(bool).to_numpy()
    observed = float((a == b).mean())
    expected = float(a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean()))
    return round((observed - expected) / (1 - expected), 3) if expected < 1 else np.nan


def agreement(table: pd.DataFrame, luna: pd.DataFrame, claims: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Per group and standard: the readers' verdicts side by side, raw agreement and Cohen's kappa; per group: how
    much of one reader's claims the other finds (texts both scored), and how often Luna's lines did not parse."""
    sets = {reader: c.groupby(["run", "arm"]).claim.agg(set).to_dict() for reader, c in claims.items()}
    rows = []
    for group in GROUPS:
        part = table[in_group(table, group)]
        keys = list(zip(part.run, part.arm))
        h, lu = [sets["haiku"].get(k, set()) for k in keys], [sets["luna"].get(k, set()) for k in keys]
        found = lambda xs, ys: round(sum(len(x & y) for x, y in zip(xs, ys)) / max(sum(len(x) for x in xs), 1), 3)  # noqa: E731
        jaccard = float(np.mean([len(x & y) / len(x | y) if x | y else 1.0 for x, y in zip(h, lu)])) if keys else np.nan
        lines = luna.set_index(["run", "arm"]).loc[keys] if keys else luna.iloc[:0]
        common = {"group": group, "texts": len(part), "claims haiku": sum(map(len, h)), "claims luna": sum(map(len, lu)),
                  "haiku's claims luna finds": found(h, lu), "luna's claims haiku finds": found(lu, h), "mean jaccard": round(jaccard, 3),
                  "luna lines unparsed": round(float(lines["unparsed lines"].sum() / max(lines["lines"].sum(), 1)), 4)}  # fmt: skip
        for name in STANDARDS:
            a, b = part[f"{name} | haiku"], part[f"{name} | luna"]
            rows.append(common | {"standard": name, "both": int((a & b).sum()), "haiku only": int((a & ~b).sum()), "luna only": int((~a & b).sum()),
                                  "neither": int((~a & ~b).sum()), "agreement": round(float((a == b).mean()), 3) if len(part) else np.nan,
                                  "kappa": kappa(a, b) if len(part) else np.nan})  # fmt: skip
    first = ["group", "standard", "texts", "both", "haiku only", "luna only", "neither", "agreement", "kappa"]
    frame = pd.DataFrame(rows)
    return frame[first + [c for c in frame.columns if c not in first]]


def tables(out: Path | None = None, source: str = SOURCE) -> tuple[pd.DataFrame, pd.DataFrame]:
    out = out or out_folder(source)
    haiku, luna = (pd.read_csv(out / reader / "texts.csv") for reader in READERS)
    for frame in (haiku, luna):  # texts.csv written before the tier column
        if "tier" not in frame:
            frame["tier"] = [tiers.name(tiers.scenario(s)) for s in frame.scenario]
    claims = {reader: pd.read_csv(out / reader / "claims.csv") for reader in READERS}
    table = verdicts(haiku, luna)
    residual = residual_table(table)
    if source == "v3-x3":  # the author's labels of the gate's flags exist for this run only
        on = table[table.arm == "on"]
        residual = pd.concat([residual, labelled_rows(len(on), int((on.kind == "LLM-written").sum()), source)], ignore_index=True)
    first = ["tier", "standard", "reader"]
    residual = residual[first + [c for c in residual.columns if c not in first]]
    residual.to_csv(out / "residual_by_standard.csv", index=False)
    agree = agreement(table, luna, claims)
    agree.to_csv(out / "agreement.csv", index=False)
    return residual, agree


# --- the run ----------------------------------------------------------------------------------------------


def estimate(items: list[dict], model: str, client: Client, lex: p.Lexicon, system: str) -> tuple[int, float]:
    """Uncached readings and their price: the mean cost of the paid scorer calls of `model` in the call log (the
    pilot's), else input from the prompts' length (4 characters a token) and output from OUT_TOKENS."""
    ctxs = {}
    reqs = list({r.key: r for t in items for r in requests_for(t, context(t, ctxs, lex), model, system)}.values())
    todo = [r for r in reqs if not (client.cache_dir / f"{r.key}.json").exists()]
    paid = [c["cost"] for c in log_records(client.cache_dir)  # the call log's closed parts and open file (D80)
            if c["model"] == model and c["role"] == "scorer" and not c["cached"] and not c["error"]]  # fmt: skip
    if paid:
        return len(todo), len(todo) * float(np.mean(paid))
    price_in, price_out, _ = settings.PRICES[model]
    tokens_in = sum(len(r.system) + len(r.messages[0][1]) for r in todo) / 4
    return len(todo), (tokens_in * price_in + len(todo) * OUT_TOKENS * price_out) / 1e6


def pilot_items(n: int, source: str = SOURCE) -> list[dict]:
    items = texts(pilot=True, source=source)
    chosen = set(np.random.default_rng(SEED).choice(sorted({t["run"] for t in items}), n, replace=False))
    return [t for t in items if t["run"] in chosen]


def write(frame: pd.DataFrame, claims: pd.DataFrame, folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    frame.to_csv(folder / "texts.csv", index=False)
    claims.to_csv(folder / "claims.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=SOURCE, choices=sorted(SOURCES), help="the E3 run to read")
    parser.add_argument("--estimate", action="store_true", help="count and price Luna's uncached readings, no network")
    parser.add_argument("--pilot", type=int, default=0, help="read N runs of the pilot datasets with Luna first")
    parser.add_argument("--budget", type=float, default=6.0, help="USD of new calls: a run priced above it does not start, and stops at it")
    parser.add_argument("--tables", action="store_true", help="both readers from the cache only and the tables, $0")
    parser.add_argument("--tier", choices=("synthetic", "plasmode"), help="one tier only (a tier rerun apart is read when it exists)")
    args = parser.parse_args()
    client, lex, system, out = Client("sync"), lexicon(args.source), extractor_system(args.source), out_folder(args.source)
    pd.set_option("display.width", 250)
    items = pilot_items(args.pilot, args.source) if args.pilot else texts(source=args.source)
    items = [t for t in items if t["tier"] == args.tier] if args.tier else items
    calls, dollars = estimate(items, READERS["luna"], client, lex, system)
    print(f"{'pilot: ' if args.pilot else ''}{len(items)} texts; {calls} uncached Luna readings, about ${dollars:.2f}")
    if args.estimate:
        return
    budget = 0.0 if args.tables else args.budget
    if dollars > budget and not args.tables:
        raise SystemExit(f"the estimate ${dollars:.2f} is above the budget ${budget:.2f}: nothing sent")
    unknown = SOURCES[args.source]["unknown_terms"]
    haiku, haiku_claims = score_all(items, READERS["haiku"], client, 0.0, lex, system, unknown)
    check_against_e3(haiku, args.source)
    luna, luna_claims = score_all(items, READERS["luna"], client, budget, lex, system, unknown)
    if args.pilot:
        write(luna, luna_claims, out / "luna" / "pilot")
        merged = luna.merge(haiku, on=["run", "arm"], suffixes=(" luna", " haiku"))
        print(merged[["run", "arm", "kind luna", "readings luna", "lines luna", "unparsed lines luna", "claims luna", "claims haiku",
                      "false M luna", "false M haiku", "undecidable M luna", "undecidable M haiku"]].to_string(index=False))  # fmt: skip
        return
    write(haiku, haiku_claims, out / "haiku")
    write(luna, luna_claims, out / "luna")
    print(f"scored: haiku {int(haiku.scored.sum())} of {len(haiku)}, luna {int(luna.scored.sum())} of {len(luna)} texts")
    residual, agree = tables(out, args.source)
    print(residual.to_string(index=False))
    print(agree.to_string(index=False))
    print(f"results in {out}")


if __name__ == "__main__":
    main()
