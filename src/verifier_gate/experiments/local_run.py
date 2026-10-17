"""The local spot check (D47, D49, D53): the principal reasons of 54 adverse-action notices, written by Claude Haiku
5.5 from each notice's handover (llm/handover_local.py) and checked by the same gate as E3 (plan check, round trip
with the local extractor, repair, template), then scored like E3.

Sample (experiments/local_facts.py): seed 2 at n = 50,000, the three interaction levels, EBM and XGB2, 9 declined
applicants each. One draw per notice, plausible names (D41), prompts l1 (llm/prompts, LOCAL_NAMES). The pilot
notices (PILOT) shaped the prompts and are reported apart.

Scoring as in E3 (D36; §14.14 review item 6): the first draft (gate off) and the released text (gate on) are each
read three times apart from the gate's readings (replicas 3 to 5); a claim counts if two readings find it, and is
verified against M (the notice's facts with bands) and against T (lexicon/local.truth_view; a global claim against
T's Facts). A hedge gets no verdict against T: it is a statement about the evidence in one sample, not about T
(data/planted.py), and T, without bands, would refute every hedge. P_U = the share of notices with a claim false against M; E_U = 1 - P_U(on) / P_U(off). Also per
notice: the reasons it states (a reason claim, not hedged), how many of them are principal reasons under T, and
T's principal reasons it leaves out; a notice M declines and T does not (T's gap <= 0) has no true principal reason.

Run (cached and resumable, as E3):
  uv run python -m verifier_gate.experiments.local_run --dry        # stub writer and extractor, no network, $0
  uv run python -m verifier_gate.experiments.local_run --estimate   # runs and cost, no network
  uv run python -m verifier_gate.experiments.local_run --pilot      # the 2 pilot notices, synchronous
  uv run python -m verifier_gate.experiments.local_run              # the 54 notices, batched
Writes results/local/<pilot|run>/<prompts>/: runs/<run id>.json, rows.csv and summary.csv.
"""

import argparse
import json
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path

import pandas as pd

from verifier_gate.data import labels
from verifier_gate.dsl.parse import parse
from verifier_gate.experiments import build_facts
from verifier_gate.experiments.e3_end_to_end import PER_RUN, RATES, SCORING_REPLICAS, readings_of, texts_of
from verifier_gate.experiments.local_facts import OUT as FACTS
from verifier_gate.experiments.local_refits import MODELS, SCENARIOS
from verifier_gate.experiments.pilot import stub_writer
from verifier_gate.facts.local import LocalFacts
from verifier_gate.gate import gate as g
from verifier_gate.gate import roundtrip as rt
from verifier_gate.lexicon import local as lp
from verifier_gate.lexicon.predicates import TRUE
from verifier_gate.llm import batch, extract, prompts, settings
from verifier_gate.llm.client import Client, Request
from verifier_gate.llm.handover_local import notice_handover
from verifier_gate.verifier.certified import certified_local
from verifier_gate.verifier.verify import verify

RESULTS = Path(__file__).parents[3] / "results" / "local"
PILOT = (("syn-dominant-n50000-s2", "EBM", 0), ("syn-weak-n50000-s2", "XGB2", 0))  # (scenario, model, notice index)
NAMES = labels.SYNTHETIC_NAMES


@dataclass(frozen=True)
class Spec:
    scenario: str
    model: str
    index: int  # the notice's place in its dataset's sample
    row: int  # the applicant's row in the training sample
    writer: str = settings.WRITER
    draw: int = 0

    @property
    def run_id(self) -> str:
        return f"{self.scenario}_{self.model}_r{self.row}_{self.writer}"

    @property
    def pilot(self) -> bool:
        return (self.scenario, self.model, self.index) in PILOT


@dataclass
class Notice:
    facts: LocalFacts  # with M's global Facts attached
    truth: LocalFacts  # the same notice under T, with T's global Facts attached
    ctx: g.Context
    handover: str


def notices() -> dict[Spec, Notice]:
    out = {}
    for scenario in SCENARIOS:
        truth_facts = build_facts.load(scenario, "T")
        for kind in MODELS:
            path = FACTS / f"{scenario.id}_{kind}.json"
            if not path.exists():
                raise SystemExit(f"{path} is missing: run experiments/local_refits and experiments/local_facts first")
            model_facts = build_facts.load(scenario, kind)
            for i, d in enumerate(json.loads(path.read_text())):
                lf = replace(LocalFacts.from_json(d), model_facts=model_facts)
                spec = Spec(scenario.id, kind, i, lf.model["row"])
                out[spec] = Notice(lf, lp.truth_view(lf, truth_facts), g.Context(lf, certified_local(lf), NAMES), notice_handover(lf, NAMES))
    return out


# --- scoring ----------------------------------------------------------------------------------------------


def scoring_requests(sentences: list, ctx: g.Context, draw: int, attempt: int = 0) -> list[Request]:
    features = extract.features_text(ctx.facts, ctx.names, ctx.descriptions)
    return [replace(extract.extractor_request(sentences, features, draw, k, local=True), attempt=attempt) for k in SCORING_REPLICAS]


def _reason_terms(claims) -> set[frozenset]:
    return {rt.term_key(c.terms[0]) for c in claims if c.kind in rt.REASON_KINDS}


def score(sentences: list, readings: list, notice: Notice) -> dict:
    """What a notice states, by at least two readings, verified against M and T, and its reasons against T's."""
    if len(readings) < rt.EXTRACTED:
        return {"scored": False, "readings": len(readings)}
    ctx = notice.ctx
    trip = rt.compare(readings, [], [i for i, _ in sentences], ctx.facts, ctx.certified)
    lines = [(line, value) for _, line, value, *_ in trip.unplanned]
    on_t = [verify(line, notice.truth).value for line, _ in lines if not line.startswith("unsettled(")]
    stated = _reason_terms(parse(line) for line, _ in lines)  # a hedged reason is no reason stated
    true_reasons = {rt.term_key(r.term) for r in notice.truth.reasons if lp.principal_reason(notice.truth, r.term).value == TRUE}
    return {
        "scored": True, "readings": len(readings), "claims": len(lines), "sentences": len(sentences),
        "words": sum(len(t.split()) for _, t in sentences),
        "false M": sum(v == "false" for _, v in lines), "undecidable M": sum(v == "undecidable" for _, v in lines),
        "false T": sum(v == "false" for v in on_t), "hedges": sum(line.startswith("unsettled(") for line, _ in lines),
        "unchecked numbers": len(trip.numbers), "no DSL form": len(trip.gap), "not covered": len(trip.missing),
        "ambiguous": len(trip.ambiguous), "reasons stated": len(stated), "reasons true vs T": len(stated & true_reasons),
        "true reasons missed": len(true_reasons - stated),
    }  # fmt: skip


def score_runs(runs: dict[str, g.Run], by_id: dict[str, Spec], found: dict[Spec, Notice], answer, log=print) -> dict:
    """Both arms of every run, with one retry of answers that are not readings. answer: requests -> {key: response}."""
    texts = {(rid, arm): s for rid, run in runs.items() for arm, s in zip(("off", "on"), texts_of(run)) if s}
    requests = {key: scoring_requests(s, found[by_id[key[0]]].ctx, by_id[key[0]].draw) for key, s in texts.items()}
    answers = answer([r for rs in requests.values() for r in rs])
    readings, retries = {}, {}
    for key, rs in requests.items():
        readings[key], unusable = readings_of(texts[key], [answers[r.key] for r in rs], found[by_id[key[0]]].ctx)
        retries[key] = [replace(r, attempt=1) for r in rs if r.replica in unusable]
    again = [r for rs in retries.values() for r in rs]
    if again:
        log(f"scoring: {len(again)} answer(s) not a reading, retried once")
        answers |= answer(again)
        for key, rs in retries.items():
            readings[key] += readings_of(texts[key], [answers[r.key] for r in rs], found[by_id[key[0]]].ctx)[0] if rs else []
    return {key: score(sentences, readings[key], found[by_id[key[0]]]) for key, sentences in texts.items()}


# --- the table --------------------------------------------------------------------------------------------


def row(spec: Spec, notice: Notice, run: g.Run, scores: dict) -> dict:
    principal = sum(c.kind == "principal_reason" for c in notice.ctx.certified)
    out = {"run": spec.run_id, "scenario": spec.scenario, "model": spec.model, "row": spec.row, "pilot notice": spec.pilot,
           "declined by M only": notice.truth.model["declined_by_m_only"], "gap": round(notice.facts.gap.value, 4),
           "certified principal reasons": principal, "writer": spec.writer, "exit": run.exit, "rounds": run.rounds,
           "calls": run.calls, "cost": round(run.cost, 6), "spent": round(run.spent, 6)}  # fmt: skip
    for arm in ("off", "on"):
        for k, v in scores.get((spec.run_id, arm), {"scored": False}).items():
            out[f"{arm} {k}"] = v
    return out


def summarise(table: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (model, pilot), part in [*table.groupby(["model", "pilot notice"]), (("both", False), table[~table["pilot notice"]])]:
        off = part[part["off scored"] == True]  # noqa: E712
        on = part[part["on scored"] == True]  # noqa: E712
        p_off = float((off["off false M"] > 0).mean()) if len(off) else float("nan")
        p_on = float((on["on false M"] > 0).mean()) if len(on) else float("nan")
        rows.append({
            "model": model, "pilot notices": pilot, "notices": len(part),
            **{f"exit {e}": int((part.exit == e).sum()) for e in (g.RELEASED, g.RELEASED_REDUCED, g.TEMPLATE, g.ESCALATE)},
            "P_U off": round(p_off, 3), "P_U on": round(p_on, 3), "E_U": round(1 - p_on / p_off, 3) if p_off else float("nan"),
            "P_U off vs T": round(float((off["off false T"] > 0).mean()), 3) if len(off) else float("nan"),
            "P_U on vs T": round(float((on["on false T"] > 0).mean()), 3) if len(on) else float("nan"),
            "reasons stated on": int(on["on reasons stated"].sum()) if len(on) else 0,
            "of them true vs T": int(on["on reasons true vs T"].sum()) if len(on) else 0,
            "true reasons missed on": int(on["on true reasons missed"].sum()) if len(on) else 0,
            "declined by M only": int(part["declined by M only"].sum()),
            "cost per notice": round(float(part.cost.mean()), 5),
        })  # fmt: skip
    return pd.DataFrame(rows)


def estimate(specs: list[Spec]) -> float:
    """USD at batch prices, from E3's measured per-call rates (a notice's prompts are about as long as E3's)."""
    writer = PER_RUN["haiku"]["writer"] * RATES["haiku writer"]
    extractor = (PER_RUN["haiku"]["extractor"] + 2 * len(SCORING_REPLICAS)) * RATES["haiku extractor"]
    return len(specs) * (writer + extractor) * settings.BATCH_DISCOUNT


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", action="store_true", help="the pilot notices, synchronous calls")
    parser.add_argument("--dry", action="store_true", help="stub writer and extractor, no network")
    parser.add_argument("--estimate", action="store_true", help="print the runs and the estimated cost, no network")
    args = parser.parse_args()
    found = notices()
    specs = [s for s in found if s.pilot] if args.pilot else list(found)
    if args.estimate:
        sync = estimate(specs) / settings.BATCH_DISCOUNT
        print(f"{len(specs)} notices; estimated cost ${estimate(specs):.2f} batched, ${sync:.2f} synchronous; "
              f"pilot ({len(PILOT)} notices, synchronous) about ${sync * len(PILOT) / len(specs):.3f}")  # fmt: skip
        return
    by_id = {s.run_id: s for s in specs}
    version = f"{prompts.LOCAL_VERSION}"
    texts = {s.run_id: found[s].handover for s in specs}
    if args.dry:
        scratch = Path(tempfile.mkdtemp(prefix="local_dry_"))
        ctxs = {rid: found[by_id[rid]].ctx for rid in by_id}
        texts = {rid: f"RUN: {rid}\n{t}" for rid, t in texts.items()}
        client, api, poll = Client("batch", cache_dir=scratch / "cache"), batch.StubBatchAPI(stub_writer(ctxs)), 0
        out = scratch / "results"
    else:
        client, api, poll = Client("sync" if args.pilot else "batch"), batch.BatchAPI(), batch.POLL_SECONDS
        out = RESULTS / ("pilot" if args.pilot else "run") / version
    print(f"local spot check{' (pilot)' if args.pilot else ''}{' (no network)' if args.dry else ''}: {len(specs)} notices; "
          f"prompts {version}")  # fmt: skip
    if args.pilot:
        runs = {}
        for rid, spec in by_id.items():
            runs[rid] = g.run_sync(g.start(rid, texts[rid], spec.writer, spec.draw, local=True), client, found[spec].ctx,
                                   out / "runs" / f"{rid}.json")  # fmt: skip
        answer = lambda requests: {r.key: client.call(r) for r in requests}  # noqa: E731
    else:
        jobs = {rid: batch.Job(g.start(rid, texts[rid], spec.writer, spec.draw, local=True), found[spec].ctx, out / "runs" / f"{rid}.json")
                for rid, spec in by_id.items()}  # fmt: skip
        runs = batch.run_waves(jobs, client, api, poll=poll)
        answer = lambda requests: batch.resolve(requests, client, api, poll=poll)  # noqa: E731
    scores = score_runs(runs, by_id, found, answer)
    table = pd.DataFrame([row(by_id[rid], found[by_id[rid]], run, scores) for rid, run in runs.items()])
    out.mkdir(parents=True, exist_ok=True)
    table.to_csv(out / "rows.csv", index=False)
    summary = summarise(table)
    summary.to_csv(out / "summary.csv", index=False)
    pd.set_option("display.width", 250)
    print(summary.T.to_string())
    paid = "no network: stub costs" if args.dry else f"paid now ${table.spent.sum():.4f} for the gate runs (scoring calls in the call log)"
    print(f"\n{paid}; results in {out}")


if __name__ == "__main__":
    main()
