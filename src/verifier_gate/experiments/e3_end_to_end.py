"""E3: end to end (plan §6, WP3; D36): each draft scored with the gate off and on.

Design (§6, §14.14, D37, D41): 18 synthetic datasets x 2 models x 2 handovers x 5 draws = 360 drafts per naming,
both namings (the outcome of the D41 confirmation), so 720 runs with Claude Haiku 5.5 as writer and extractor; and
the Sonnet subset (D37): draw 0 of each cell with Claude Sonnet 5.5 as the writer, plausible names, 72 runs. The
prompts are the frozen writer v3 and extractor x3. Every call goes through the Batch API in waves (llm/batch.py)
and is cached, so a stopped run resumes and a rerun costs nothing.

Scoring (D36; §14.14 review item 6, option B, decided 15 Oct): what a text tells its reader is read by the
extractor three times, in SCORING readings apart from the gate's own (replicas 3 to 5), so that the gate is not
scored by the readings it acted on. Both arms are scored the same way:
- gate off: the writer's first draft as written (a run whose writer gave no draft has none);
- gate on: the released text (RELEASED, RELEASED_REDUCED or TEMPLATE); ESCALATE releases nothing.
A claim counts if at least two readings find it (gate/roundtrip.py); each is verified against M, the fitted model,
and against T, the planted truth. P_U is the share of texts that state at least one claim false against M;
E_U = 1 - P_U(on) / P_U(off), always next to the exit states and the claim volume (D36). Undecidable claims,
numbers no claim can check, coverage and emphasis are counted apart. An answer that leaves out a sentence is
retried once, as in the gate. The two pilot datasets are reported apart: they shaped the prompts.

The rerun after the 20 Oct review (D66): lexicon v3, writer prompts v4 and extractor x5 (D63-D65; with
VERIFIER_GATE_LEXICON=v2 the code replays E3 as run, v3-x3), `--revised` (M5: H2's statements under the run's own
names, and the round trip's rule on unknown terms; without it, handover and round trip as E3 ran them), and
`--tier both`: the 720 synthetic runs as before and the plasmode tier (M7), 18 datasets x 2 models x 2 handovers x 5
draws = 360 runs, with the TaiwanCredit column codes and their descriptions as names (naming "codes", D54). The
rerun's batch waves have their own folder, so other experiments' batches neither block nor see them.

Run (in a terminal: hours, mostly waiting for batches; stopping is safe, the same command resumes):
  uv run python -m verifier_gate.experiments.e3_end_to_end --dry        # stub writer and extractor, 16 runs, $0
  uv run python -m verifier_gate.experiments.e3_end_to_end --estimate   # runs and cost from the pilot's rates
  uv run python -m verifier_gate.experiments.e3_end_to_end              # the 720 Haiku runs
  uv run python -m verifier_gate.experiments.e3_end_to_end --sonnet     # the 72 Sonnet runs
  uv run python -m verifier_gate.experiments.e3_end_to_end --revised --tier both   # the rerun with D74's fixes: 1,080 runs
  VERIFIER_GATE_D74=0 uv run python -m verifier_gate.experiments.e3_end_to_end --revised --tier both   # D66 as run
Writes results/e3/<writer prompts>-<extractor prompts>[-m5][-d74]/<haiku|sonnet>/: runs/<run id>.json, rows.csv (one row per
run) and summary.csv.
"""

import argparse
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path

import pandas as pd

from verifier_gate.data import dgp, labels, plasmode, tiers
from verifier_gate.experiments.build_facts import load
from verifier_gate.experiments.pilot import NAMINGS, stub_writer
from verifier_gate.gate import gate as g
from verifier_gate.gate import roundtrip as rt
from verifier_gate.gate.template import plasmode_label
from verifier_gate.lexicon.predicates import d74_fixes
from verifier_gate.llm import batch, extract, prompts, settings
from verifier_gate.llm.client import Client, Request, Response
from verifier_gate.llm.handover import handover
from verifier_gate.verifier.certified import certified_plan
from verifier_gate.verifier.verify import verify

MODELS = ("EBM", "XGB2")
VARIANTS = ("H1", "H2")
DRAWS = 5
SCORING_REPLICAS = (3, 4, 5)
PILOT = ("syn-dominant-n50000-s1", "syn-none-n5000-s1")
RESULTS = Path(__file__).parents[3] / "results" / "e3"
RELEASING = (g.RELEASED, g.RELEASED_REDUCED, g.TEMPLATE)
# Rates measured in the round-trip pilot (15 Oct, plan §14.15), synchronous USD per call, and calls per run
RATES = {"haiku writer": 0.00097, "haiku extractor": 0.00038, "sonnet writer": 0.0253}
PER_RUN = {"haiku": {"writer": 2.2, "extractor": 5.6}, "sonnet": {"writer": 1.3, "extractor": 3.5}}
NAMES = {**NAMINGS, "codes": {}}  # "codes": the plasmode tier's column codes, shown as they are (D54)
DESCRIPTIONS = {"synthetic": labels.SYNTHETIC_DESCRIPTIONS, "plasmode": labels.PLASMODE_DESCRIPTIONS}


@dataclass(frozen=True)
class Spec:
    scenario: str
    model: str
    variant: str
    draw: int
    writer: str
    naming: str

    @property
    def run_id(self) -> str:
        writer = self.writer.replace("/", "-").replace(":", "-")  # a local model's tag (ollama/qwen3.8:27b) in a file name
        return f"{self.scenario}_{self.model}_{self.variant}_d{self.draw}_{writer}_{self.naming}"


def writer_folder(writer: str) -> str:
    return writer.removeprefix("ollama/").replace(":", "-")


def plan(sonnet: bool = False, dry: bool = False, writer: str | None = None, tier: str = "synthetic") -> list[Spec]:
    """The runs: synthetic as E3 ran (both namings); plasmode with the column codes (D66); "both": synthetic, then
    plasmode."""
    if sonnet or writer:  # a writer subset (D37, D55): one draw per cell, plausible names
        return [Spec(s.id, m, v, 0, writer or settings.WRITER_SUBSET, "plausible") for s in dgp.SCENARIOS for m in MODELS for v in VARIANTS]
    draws = range(1) if dry else range(DRAWS)
    out = []
    if tier in ("synthetic", "both"):
        scenarios = dgp.SCENARIOS[:2] if dry else dgp.SCENARIOS
        out += [Spec(s.id, m, v, d, settings.WRITER, naming) for naming in NAMINGS for s in scenarios for m in MODELS for v in VARIANTS for d in draws]
    if tier in ("plasmode", "both"):
        scenarios = plasmode.SCENARIOS[:2] if dry else plasmode.SCENARIOS
        out += [Spec(s.id, m, v, d, settings.WRITER, "codes") for s in scenarios for m in MODELS for v in VARIANTS for d in draws]
    return out


def contexts(specs: list[Spec], revised: bool = False) -> tuple[dict[str, g.Context], dict[str, str]]:
    """Per run: the gate's context and the handover text; each handover is built and checked once. revised: H2's
    statements under the run's own names and the round trip's rule on unknown terms (M5); otherwise as E3 ran."""
    data, facts, ctxs, texts, built = {}, {}, {}, {}, {}
    for spec in specs:
        scenario = tiers.scenario(spec.scenario)
        tier = tiers.name(scenario)
        if (spec.scenario, spec.model) not in facts:
            f = load(scenario, spec.model)
            facts[spec.scenario, spec.model] = (f, certified_plan(f))
        f, certified = facts[spec.scenario, spec.model]
        key = (spec.scenario, spec.model, spec.variant, spec.naming)
        if key not in built:
            data.setdefault(spec.scenario, tiers.generate(scenario).X)
            h = handover(f, data[spec.scenario], spec.variant, certified, names=NAMES[spec.naming], descriptions=DESCRIPTIONS[tier],
                         naming_bug=not revised)  # fmt: skip
            if not h.passed:
                raise SystemExit(f"{key}: the readable form failed its check; fix it before any call")
            built[key] = h.text
        label = plasmode_label if tier == "plasmode" else None
        ctxs[spec.run_id] = g.Context(f, certified, NAMES[spec.naming], label=label, descriptions=DESCRIPTIONS[tier], unknown_terms=revised)
        texts[spec.run_id] = built[key]
    return ctxs, texts


# --- scoring ----------------------------------------------------------------------------------------------


def texts_of(run: g.Run) -> tuple[list | None, list | None]:
    """The writer's first draft and the released text, as [id, text] sentences (None where there is none)."""
    first = next((v for v in run.versions if v["source"] in ("proposer", "format retry")), None)
    released = run.versions[-1] if run.exit in RELEASING and run.versions else None
    return (first["sentences"] if first else None), (released["sentences"] if released else None)


def scoring_requests(sentences: list, ctx: g.Context, draw: int, attempt: int = 0) -> list[Request]:
    features = extract.features_text(ctx.facts, ctx.names, ctx.descriptions)
    return [replace(extract.extractor_request(sentences, features, draw, k), attempt=attempt) for k in SCORING_REPLICAS]


def readings_of(sentences: list, answers: list[Response], ctx: g.Context) -> tuple[list, list[int]]:
    """The usable readings, and the replicas whose answer was not a reading."""
    ids, readings, unusable = {i for i, _ in sentences}, [], []
    for replica, answer in zip(SCORING_REPLICAS, answers):
        try:
            readings.append(extract.extraction_from(answer, ids, ctx.names))
        except (ValueError, KeyError, TypeError):
            unusable.append(replica)
    return readings, unusable


def score(sentences: list, readings: list, ctx: g.Context, truth) -> dict:
    """What a text states, by at least two readings, verified against M and T."""
    if len(readings) < rt.EXTRACTED:
        return {"scored": False, "readings": len(readings)}
    trip = rt.compare(readings, [], [i for i, _ in sentences], ctx.facts, ctx.certified, unknown_terms=ctx.unknown_terms)
    claims = [(line, value) for _, line, value, *_ in trip.unplanned]
    on_t = [verify(line, truth).value for line, _ in claims]
    return {
        "scored": True, "readings": len(readings), "claims": len(claims), "sentences": len(sentences),
        "words": sum(len(t.split()) for _, t in sentences),
        "false M": sum(v == "false" for _, v in claims), "undecidable M": sum(v == "undecidable" for _, v in claims),
        "false T": sum(v == "false" for v in on_t), "hedges": sum(line.startswith("unsettled(") for line, _ in claims),
        "unchecked numbers": len(trip.numbers), "no DSL form": len(trip.gap), "not covered": len(trip.missing),
        "emphasis": len(trip.emphasis), "ambiguous": len(trip.ambiguous),
    }  # fmt: skip


def score_runs(runs: dict[str, g.Run], ctxs: dict[str, g.Context], specs: dict[str, Spec], client: Client, api,
               poll: float, log=print) -> dict[str, dict]:  # fmt: skip
    """Both arms of every run, in one set of waves, with one retry of answers that are not readings."""
    texts = {(rid, arm): s for rid, run in runs.items() for arm, s in zip(("off", "on"), texts_of(run)) if s}
    return score_texts(texts, ctxs, specs, client, api, poll, log)


def score_texts(texts: dict[tuple[str, str], list], ctxs: dict[str, g.Context], specs: dict[str, Spec], client: Client, api,
                poll: float, log=print, scorer=None, folder: Path | None = None) -> dict[tuple[str, str], dict]:  # fmt: skip
    """Texts by (run id, arm), each read at its run's draw; `scorer` (default: score) and `folder` (the batch waves'
    folder, default the client's) serve the baselines' arms too (e3_baselines)."""
    scorer = scorer or score
    requests = {key: scoring_requests(s, ctxs[key[0]], specs[key[0]].draw) for key, s in texts.items()}
    answers = batch.resolve([r for rs in requests.values() for r in rs], client, api, folder, poll=poll, log=log)
    readings, retries = {}, {}
    for key, rs in requests.items():
        readings[key], unusable = readings_of(texts[key], [answers[r.key] for r in rs], ctxs[key[0]])
        retries[key] = [replace(r, attempt=1) for r in rs if r.replica in unusable]
    again = [r for rs in retries.values() for r in rs]
    if again:
        log(f"scoring: {len(again)} answer(s) not a reading, retried once")
        answers |= batch.resolve(again, client, api, folder, poll=poll, log=log)
        for key, rs in retries.items():
            readings[key] += readings_of(texts[key], [answers[r.key] for r in rs], ctxs[key[0]])[0] if rs else []
    truths = {}
    out = {}
    for (rid, arm), sentences in texts.items():
        scenario = tiers.scenario(specs[rid].scenario)
        truth = truths.setdefault(scenario.id, load(scenario, "T"))
        out[rid, arm] = scorer(sentences, readings[rid, arm], ctxs[rid], truth)
    return out


# --- the table --------------------------------------------------------------------------------------------


def row(spec: Spec, run: g.Run, scores: dict) -> dict:
    scenario = tiers.scenario(spec.scenario)
    out = {"run": spec.run_id, "scenario": spec.scenario, "interaction": scenario.interaction, "n": scenario.n, "seed": scenario.seed,
           "pilot dataset": spec.scenario in PILOT, "model": spec.model, "handover": spec.variant, "draw": spec.draw,
           "writer": spec.writer, "naming": spec.naming, "exit": run.exit, "rounds": run.rounds, "calls": run.calls,
           "flagged": run.flagged, "cost": round(run.cost, 6), "spent": round(run.spent, 6)}  # fmt: skip
    for arm in ("off", "on"):
        for k, v in scores.get((spec.run_id, arm), {"scored": False}).items():
            out[f"{arm} {k}"] = v
    return out


def summarise(table: pd.DataFrame) -> pd.DataFrame:
    """Per writer and naming, and for the two pilot datasets apart: exit states, P_U off and on, E_U, volume."""
    rows = []
    for (writer, naming, pilot), part in table.groupby(["writer", "naming", "pilot dataset"]):
        off = part[part["off scored"] == True]  # noqa: E712
        on = part[part["on scored"] == True]  # noqa: E712
        p_off = float((off["off false M"] > 0).mean()) if len(off) else float("nan")
        p_on = float((on["on false M"] > 0).mean()) if len(on) else float("nan")
        rows.append({
            "writer": writer, "naming": naming, "pilot datasets": pilot, "runs": len(part),
            **{f"exit {e}": int((part.exit == e).sum()) for e in (g.RELEASED, g.RELEASED_REDUCED, g.TEMPLATE, g.ESCALATE)},
            "P_U off": round(p_off, 3), "P_U on": round(p_on, 3), "E_U": round(1 - p_on / p_off, 3) if p_off else float("nan"),
            "P_U off vs T": round(float((off["off false T"] > 0).mean()), 3) if len(off) else float("nan"),
            "P_U on vs T": round(float((on["on false T"] > 0).mean()), 3) if len(on) else float("nan"),
            "claims false vs T, off": round(float(off["off false T"].sum() / max(off["off claims"].sum(), 1)), 3) if len(off) else float("nan"),
            "claims false vs T, on": round(float(on["on false T"].sum() / max(on["on claims"].sum(), 1)), 3) if len(on) else float("nan"),
            "claims off": round(float(off["off claims"].mean()), 1) if len(off) else float("nan"),
            "claims on": round(float(on["on claims"].mean()), 1) if len(on) else float("nan"),
            "hedge share on": round(float(on["on hedges"].sum() / max(on["on claims"].sum(), 1)), 3) if len(on) else float("nan"),
            "cost per run": round(float(part.cost.mean()), 5),
        })  # fmt: skip
    return pd.DataFrame(rows)


def estimate(specs: list[Spec]) -> float:
    """USD at batch prices, from the pilot's measured rates."""
    total = 0.0
    for spec in specs:
        kind = "sonnet" if "sonnet" in spec.writer else "haiku"
        local = spec.writer.startswith("ollama/")  # a local writer costs nothing; its runs are paced like Haiku's
        writer = 0.0 if local else PER_RUN[kind]["writer"] * RATES[f"{kind} writer"]
        extractor = (PER_RUN[kind]["extractor"] + 2 * len(SCORING_REPLICAS)) * RATES["haiku extractor"]
        total += (writer + extractor) * settings.BATCH_DISCOUNT
    return total


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sonnet", action="store_true", help="the Sonnet writer subset (D37)")
    parser.add_argument("--dry", action="store_true", help="stub writer and extractor on 16 runs, no network")
    parser.add_argument("--estimate", action="store_true", help="print the runs and the estimated cost, no network")
    parser.add_argument("--writer", default=None, help="another writer for a subset as for Sonnet, e.g. ollama/qwen3.8:27b (D55)")
    parser.add_argument("--extractor", default=None, help="the extractor version for the gate and the scoring (E3 ran with x3; "
                        "default: x3, or with --revised the current one)")  # fmt: skip
    parser.add_argument("--limit", type=int, default=0, help="only the first N runs (a pilot of a writer subset)")
    parser.add_argument("--tier", default="synthetic", choices=("synthetic", "plasmode", "both"), help="the tiers (D66)")
    parser.add_argument("--revised", action="store_true", help="H2's statements under the run's names, the rule on unknown terms (M5)")
    parser.add_argument("--pilot", action="store_true", help="the rerun's pilot (D66): draw 0 on the pilot datasets (plausible names) and the "
                        "first plasmode dataset; written to <version>/pilot/")  # fmt: skip
    args = parser.parse_args()
    prompts.pin_extractor(args.extractor or (prompts.EXTRACTOR_VERSION if args.revised else "x3"))
    specs = plan(args.sonnet, args.dry, args.writer, args.tier)
    specs = specs[: args.limit] if args.limit else specs
    if args.pilot:
        first = plasmode.SCENARIOS[0].id
        specs = [s for s in specs if s.draw == 0 and ((s.scenario in PILOT and s.naming == "plausible") or s.scenario == first)]
    if args.estimate:
        print(f"{len(specs)} runs; estimated cost at batch prices, from the pilot's rates: ${estimate(specs):.2f}")
        return
    ctxs, texts = contexts(specs, args.revised)
    waves = None  # the batch waves' folder: the client's, or the rerun's own (D66)
    if args.dry:
        scratch = Path(tempfile.mkdtemp(prefix="e3_dry_"))
        client, api, poll = Client("batch", cache_dir=scratch / "cache"), batch.StubBatchAPI(stub_writer(ctxs)), 0
        out = scratch / "results"
        texts = {rid: f"RUN: {rid}\n{t}" for rid, t in texts.items()}
    else:
        client, api, poll = Client("batch"), batch.BatchAPI(), batch.POLL_SECONDS
        folder = "sonnet" if args.sonnet else writer_folder(args.writer) if args.writer else "haiku"
        version = f"{prompts.VERSION}-{prompts.extractor_version()}" + ("-m5" if args.revised else "") + ("-d74" if args.revised and d74_fixes() else "")
        out = RESULTS / version / ("pilot" if args.pilot else "") / folder
        waves = client.cache_dir / "batches" / f"e3_{version}" if args.revised else None
    by_id = {spec.run_id: spec for spec in specs}
    jobs = {rid: batch.Job(g.start(rid, texts[rid], spec.writer, spec.draw), ctxs[rid], out / "runs" / f"{rid}.json") for rid, spec in by_id.items()}
    label = "Sonnet subset" if args.sonnet else f"{args.writer} subset" if args.writer else "Haiku"
    print(f"E3 ({label}{', no network' if args.dry else ''}): {len(jobs)} runs; "
          f"prompts {prompts.VERSION}, extractor {prompts.extractor_version()}")  # fmt: skip
    runs = batch.run_waves(jobs, client, api, waves, poll=poll)
    texts_scored = {(rid, arm): s for rid, run in runs.items() for arm, s in zip(("off", "on"), texts_of(run)) if s}
    scores = score_texts(texts_scored, ctxs, by_id, client, api, poll, folder=waves)
    table = pd.DataFrame([row(by_id[rid], run, scores) for rid, run in runs.items()])
    out.mkdir(parents=True, exist_ok=True)
    table.to_csv(out / "rows.csv", index=False)
    summary = summarise(table)
    summary.to_csv(out / "summary.csv", index=False)
    pd.set_option("display.width", 250)
    print(summary.T.to_string())
    paid = "no network: stub costs" if args.dry else f"paid now ${table.spent.sum():.4f} for the runs (scoring calls in the call log)"
    print(f"\n{paid}; results in {out}")


if __name__ == "__main__":
    main()
