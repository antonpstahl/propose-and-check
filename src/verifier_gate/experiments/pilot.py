"""Pilot of the LLM loop (plan §14.14, step 7), and the checks before and beside it.

Runs on 2 discovery-seed datasets: syn-dominant-n50000-s1 (the worked example) and syn-none-n5000-s1 (small n:
sets and hedges). Traces: both models x H1 and H2 (8), plus 2 more draws of the worked example with XGB2 and H2 =
10, with the writer of settings.WRITER. `--sonnet` adds the two H2 traces of the first draw with the Sonnet
writer (D37), to check the prompts work for both.

Modes, in the order they are used:
- dry run (default, no network, $0): a stub writer answers with the template text (one run starts with a wrong
  claim, to exercise a repair), so the whole loop runs on real Facts; prints an estimate of the live cost from
  the prompt sizes. Results in a temporary folder unless --keep.
- --smoke: 2 live calls, the worked example's first draft with H1 and H2: the key, the JSON format, the DSL
  parse, caching and the log. Costs well under $0.01.
- --live: the 10 traces, live and synchronous. Every call is cached (cache/llm/), so a rerun costs nothing.
- --naming: the naming check of D41, live. First drafts only (the gate-off case, where priors show), H1, both
  models, both datasets, 5 draws, once with the plausible names of the noise features and once with opaque names:
  40 calls. Counted per naming: drafts with at least one claim about a noise feature that the verifier does not
  certify. Rule, fixed before the run (14 Oct): if the two counts differ by NAMING_DIFFERENCE or more of 20, the
  names change the writer's behaviour and E3 runs both namings, reported apart; otherwise the plausible names stay.
  Add --dry for a no-network rehearsal.
- --batch-smoke: the Batch API transport (llm/batch.py), live. The worked example with H1 and H2 at draw
  BATCH_SMOKE_DRAW (draws 0-4 are cached from the pilot and the naming check, so they would cost nothing and test
  nothing), with the full call budget, in waves: a repair goes into the next wave. About 2-6 calls at the batch
  price, well under $0.01. A wave usually ends within minutes, at most 24 hours; stopping the process is safe, a
  rerun resumes the open wave. Add --dry for a no-network rehearsal with a stub batch.

Writes results/pilot/<prompt version>/<mode>/<run id>.json (the full run, with every version and verdict),
summary.csv and traces.md (the runs as Markdown, for reading).
Run: `uv run python -m verifier_gate.experiments.pilot [--smoke | --live | --naming | --batch-smoke] [--sonnet]`.
"""

import argparse
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from verifier_gate.data import dgp, labels
from verifier_gate.dsl.grammar import Claim
from verifier_gate.experiments.build_facts import load
from verifier_gate.gate import gate as g
from verifier_gate.gate.template import template
from verifier_gate.llm import batch, prompts, settings
from verifier_gate.llm.client import Client, Request, stub_message
from verifier_gate.llm.extract import faithful_reading
from verifier_gate.llm.handover import handover
from verifier_gate.verifier.certified import certified_plan

DATASETS = ("syn-dominant-n50000-s1", "syn-none-n5000-s1")
WORKED = ("syn-dominant-n50000-s1", "XGB2", "H2")
NAMINGS = {"plausible": labels.SYNTHETIC_NAMES, "opaque": labels.OPAQUE_NAMES}
NAMING_DRAWS = 5
NAMING_DIFFERENCE = 3  # of 20 drafts per naming (D41)
BATCH_SMOKE_DRAW = 5  # the first draw of the worked example no earlier run has made
NOISE = ("noise_1", "noise_2")
RESULTS = Path(__file__).parents[3] / "results" / "pilot"
CHARS_PER_TOKEN = 3.0  # rough, on the safe side (Claude Haiku 5.5's tokenizer counts more tokens than older ones)
OUTPUT_TOKENS = 1_500  # assumed per call for the estimate


@dataclass(frozen=True)
class Spec:
    scenario: str
    model: str
    variant: str
    draw: int
    writer: str
    naming: str = "plausible"
    budget: int = g.CALL_BUDGET

    @property
    def run_id(self) -> str:
        return f"{self.scenario}_{self.model}_{self.variant}_d{self.draw}_{self.writer}_{self.naming}"


def plan(mode: str, sonnet: bool) -> list[Spec]:
    if mode == "smoke":
        return [Spec(WORKED[0], WORKED[1], v, 0, settings.WRITER, budget=1) for v in ("H1", "H2")]
    if mode == "batch_smoke":
        return [Spec(WORKED[0], WORKED[1], v, BATCH_SMOKE_DRAW, settings.WRITER) for v in ("H1", "H2")]
    if mode == "naming":
        return [Spec(s, m, "H1", d, settings.WRITER, naming, budget=1)
                for naming in NAMINGS for s in DATASETS for m in ("EBM", "XGB2") for d in range(NAMING_DRAWS)]  # fmt: skip
    out = [Spec(s, m, v, 0, settings.WRITER) for s in DATASETS for m in ("EBM", "XGB2") for v in ("H1", "H2")]
    out += [Spec(*WORKED, d, settings.WRITER) for d in (1, 2)]
    if sonnet:
        out += [Spec(s, "XGB2", "H2", 0, settings.WRITER_SUBSET) for s in DATASETS]
    return out


def as_answer(draft, names) -> dict:
    """A draft as the writer's JSON answer, in the writer's names."""
    return {"sentences": [{"id": i, "text": t} for i, t in draft.sentences],
            "claims": [{"sentence_id": c.sentence_id, "dsl": str(labels.external(Claim(c.kind, c.terms, c.value, c.relation, None, c.inner), names))}
                       for c in draft.claims]}  # fmt: skip


def stub_writer(contexts: dict[str, g.Context]):
    """Answers with the template of the run's model; the first run's first draft carries a wrong claim. The
    extractor reads each text as exactly the writer's claims. Dry runs only: the run id travels in the handover
    text."""
    seen, answers = set(), []

    def respond(request: Request) -> dict:
        if request.role == "extractor":
            return stub_message(faithful_reading(request, answers))
        run = request.messages[0][1].split("RUN:")[1].split("\n")[0].strip()
        ctx = contexts[run]
        answer = as_answer(template(ctx.facts, ctx.certified), ctx.names)
        if run not in seen and run == next(iter(contexts)):
            answer["sentences"].append({"id": 99, "text": "Income has a strong effect."})
            answer["claims"].append({"sentence_id": 99, "dsl": 'strength("income") == "strong"'})
        seen.add(run)
        answers.append(answer)
        chars = len(request.system) + sum(len(m[1]) for m in request.messages)
        return stub_message(answer, usage={"input_tokens": int(chars / CHARS_PER_TOKEN), "output_tokens": OUTPUT_TOKENS})

    return respond


def uncertified_noise_claims(state: g.Run) -> int | None:
    """In the writer's first draft: claims about a noise feature that the verifier does not certify (None if the
    writer gave no draft, e.g. an empty answer with no call left for the format retry: the run's text is the
    template, which is not the writer's)."""
    first = next((v for v in state.versions if v["source"] in ("proposer", "format retry")), None)
    if first is None:
        return None
    return sum(1 for _, line, value, *_ in first["claims"] if value != "true" and any(f'"{n}"' in line for n in NOISE))


def naming_verdict(table: pd.DataFrame) -> str:
    counts = {n: int((table[table.naming == n].noise_uncertified > 0).sum()) for n in NAMINGS}
    drafts = {n: int(table[table.naming == n].noise_uncertified.notna().sum()) for n in NAMINGS}
    differ = abs(counts["plausible"] - counts["opaque"]) >= NAMING_DIFFERENCE
    decision = "the names change the writer's behaviour: E3 runs both namings, reported apart" if differ else "no difference by the rule: the plausible names stay"
    return f"Drafts with an uncertified claim about a noise feature: {counts} of {drafts} drafts. {decision}."


def digest(folder: Path) -> str:
    """The runs of a pilot folder as Markdown, for reading: per text version its sentences, each with its claims
    and verdicts (a failing claim with its reason), then the exit state."""
    out = [f"# Pilot traces: {folder.name}", ""]
    for path in sorted(folder.glob("*.json")):
        run = json.loads(path.read_text())
        out += [f"## {run['run_id']}", "", f"**{run['exit']}**: {run['reason']} ({run['calls']} calls, {run['rounds']} repair rounds)", ""]
        for k, version in enumerate(run["versions"]):
            failing = sum(1 for c in version["claims"] if c[2] != "true")
            out.append(f"### Version {k}: {version['source']} ({len(version['claims'])} claims, {failing} failing"
                       f"{', missing: ' + ', '.join(version['missing']) if version['missing'] else ''})")  # fmt: skip
            for sid, text in version["sentences"]:
                out.append(f"{sid}. {text}")
                for c in (c for c in version["claims"] if c[0] == sid):
                    mark = "ok" if c[2] == "true" else f"**{c[2]}**" + (f" ({c[4]})" if c[4] else "")
                    out.append(f"    - `{c[1]}`: {mark}")
            out += [f"    - format error: {e}" for e in version["format_errors"]]
            out += roundtrip_lines(version.get("roundtrip")) + [""]
    return "\n".join(out)


def roundtrip_lines(trip: dict | None) -> list[str]:
    """A version's round trip, for reading: what the text says beyond its plan, and the flags."""
    if not trip:
        return []
    out = [f"Round trip ({trip['readings']} readings):"]
    for sid, line, value, _, reason, _ in trip["unplanned"]:
        mark = "ok" if value == "true" else f"**{value}**" + (f" ({reason})" if reason else "")
        out.append(f"    - sentence {sid} also states `{line}`: {mark}")
    out += [f"    - **emphasis**: sentence {sid} opens with {', '.join(minor)}, none of {', '.join(strong)}" for sid, minor, strong in trip["emphasis"]]
    out += [f"    - **unchecked number**: sentence {sid}: {'; '.join(words)}" for sid, words in trip.get("numbers", [])]
    out += [f"    - **not covered by the text**: {term}" for term in trip.get("missing", [])]
    out += [f"    - flag, plan claim not in the text: sentence {sid} `{line}`" for sid, line in trip["plan_only"]]
    out += [f"    - flag, one reading only: sentence {sid} `{line}`" for sid, line in trip["ambiguous"]]
    out += [f"    - flag, no DSL form: sentence {sid}: {'; '.join(words)}" for sid, words in trip["gap"]]
    return out if len(out) > 1 else [out[0] + " nothing beyond the plan, no flags"]


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--smoke", action="store_true")
    mode.add_argument("--live", action="store_true")
    mode.add_argument("--naming", action="store_true")
    mode.add_argument("--batch-smoke", action="store_true")
    parser.add_argument("--sonnet", action="store_true")
    parser.add_argument("--dry", action="store_true", help="any mode without network (stub writer and extractor)")
    parser.add_argument("--keep", action="store_true", help="dry runs: keep the results")
    args = parser.parse_args()
    name = "smoke" if args.smoke else "live" if args.live else "naming" if args.naming else "batch_smoke" if args.batch_smoke else "dry_run"
    dry = name == "dry_run" or args.dry
    specs = plan(name, args.sonnet)

    contexts, handovers = {}, {}
    for spec in specs:
        scenario = next(s for s in dgp.SCENARIOS if s.id == spec.scenario)
        facts = load(scenario, spec.model)
        certified = certified_plan(facts)
        names = NAMINGS[spec.naming]
        h = handover(facts, dgp.generate(scenario).X, spec.variant, certified, names=names)
        if not h.passed:
            raise SystemExit(f"{spec.run_id}: the readable form failed its check; fix it before any call")
        contexts[spec.run_id] = g.Context(facts, certified, names, roundtrip=spec.budget > 1)  # first-draft checks: no round trip
        handovers[spec.run_id] = h.text

    scratch = Path(tempfile.mkdtemp(prefix="pilot_dry_")) if dry else None
    out = (RESULTS / prompts.VERSION / f"{name}_dry" if args.keep else scratch / "results") if dry else RESULTS / prompts.VERSION / name
    starts = {spec.run_id: g.start(spec.run_id, f"RUN: {spec.run_id}\n{handovers[spec.run_id]}" if dry else handovers[spec.run_id],
                                   spec.writer, spec.draw, budget=spec.budget) for spec in specs}  # fmt: skip
    if args.batch_smoke:
        client = Client("batch", cache_dir=scratch / "cache") if dry else Client("batch")
        api = batch.StubBatchAPI(stub_writer(contexts)) if dry else batch.BatchAPI()
        jobs = {run_id: batch.Job(run, contexts[run_id], out / f"{run_id}.json") for run_id, run in starts.items()}
        states = batch.run_waves(jobs, client, api, poll=0 if dry else batch.POLL_SECONDS)
    else:
        client = Client("stub", stub_writer(contexts), cache_dir=scratch / "cache") if dry else Client("sync")
        states = {run_id: g.run_sync(run, client, contexts[run_id], out / f"{run_id}.json") for run_id, run in starts.items()}
    rows = []
    for spec in specs:
        state = states[spec.run_id]
        rows.append({"run": spec.run_id, "naming": spec.naming, "exit": state.exit, "reason": state.reason, "calls": state.calls,
                     "rounds": state.rounds, "flagged": state.flagged, "noise_uncertified": uncertified_noise_claims(state),
                     "cost": round(state.cost, 5),
                     **{k: state.usage.get(k, 0) for k in ("input_tokens", "output_tokens", "cache_read_input_tokens")}})  # fmt: skip
    table = pd.DataFrame(rows)
    out.mkdir(parents=True, exist_ok=True)
    table.to_csv(out / "summary.csv", index=False)
    (out / "traces.md").write_text(digest(out))
    pd.set_option("display.width", 240)
    print(f"Pilot ({name}{', no network' if dry else ''}): {len(table)} runs; prompts {json.dumps({k: v[:12] for k, v in prompts.hashes().items()})}")
    print(table.drop(columns=["reason"]).to_string(index=False))
    print("\nExit states:", table.exit.value_counts().to_dict())
    if args.naming:
        print(naming_verdict(table))
    if dry:
        per_call = table.input_tokens.sum() / table.calls.sum()
        live = sum(table.calls) * (per_call * settings.PRICES[settings.WRITER][0] + OUTPUT_TOKENS * settings.PRICES[settings.WRITER][1]) / 1e6
        live *= settings.BATCH_DISCOUNT if args.batch_smoke else 1.0
        print(f"\nNo network: about {per_call:,.0f} input tokens per call. Live, these {sum(table.calls)} calls would cost "
              f"about ${live:.4f} with {settings.WRITER}{' (batch price)' if args.batch_smoke else ''}, no caching assumed; "
              f"results in {out}")  # fmt: skip
    else:
        print(f"\nTotal cost: ${table.cost.sum():.4f}; results in {out}")


if __name__ == "__main__":
    main()
