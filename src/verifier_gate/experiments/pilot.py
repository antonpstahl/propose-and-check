"""Pilot of the LLM loop (plan §14.14, step 7), and the checks before it.

Runs on 2 discovery-seed datasets: syn-dominant-n50000-s1 (the worked example) and syn-none-n5000-s1 (small n:
sets and hedges). Traces: both models x H1 and H2 (8), plus 2 more draws of the worked example with XGB2 and H2 =
10, with the writer of settings.WRITER. `--sonnet` adds the two H2 traces of the worked example's first draw with
the Sonnet writer (D37), to check the prompts work for both.

Modes, in the order they are used:
- dry run (default, no network, $0): a stub writer answers with the template text (one run starts with a wrong
  claim, to exercise a repair), so the whole loop runs on real Facts; prints an estimate of the live cost from
  the prompt sizes. Results in a temporary folder unless --keep.
- --smoke: 2 live calls, the worked example's first draft with H1 and H2: the key, the JSON format, the DSL
  parse, caching and the log. Costs well under $0.01.
- --live: the 10 traces, live and synchronous. Every call is cached (cache/llm/), so a rerun costs nothing.

Writes results/pilot/<mode>/<run id>.json (the full run, with every version and verdict) and summary.csv.
Run: `uv run python -m verifier_gate.experiments.pilot [--smoke | --live] [--sonnet]`.
"""

import argparse
import json
import tempfile
from pathlib import Path

import pandas as pd

from verifier_gate.data import dgp, labels
from verifier_gate.dsl.grammar import Claim
from verifier_gate.experiments.build_facts import load
from verifier_gate.gate import gate as g
from verifier_gate.gate.template import template
from verifier_gate.llm import prompts, settings
from verifier_gate.llm.client import Client, Request, stub_message
from verifier_gate.llm.handover import handover
from verifier_gate.verifier.certified import certified_plan

DATASETS = ("syn-dominant-n50000-s1", "syn-none-n5000-s1")
WORKED = ("syn-dominant-n50000-s1", "XGB2", "H2")
RESULTS = Path(__file__).parents[3] / "results" / "pilot"
CHARS_PER_TOKEN = 3.0  # rough, on the safe side (Claude Haiku 5.5's tokenizer counts more tokens than older ones)
OUTPUT_TOKENS = 1_500  # assumed per call for the estimate


def runs(sonnet: bool) -> list[tuple[str, str, str, int, str]]:
    out = [(s, m, v, 0, settings.WRITER) for s in DATASETS for m in ("EBM", "XGB2") for v in ("H1", "H2")]
    out += [(*WORKED, d, settings.WRITER) for d in (1, 2)]
    if sonnet:
        out += [(s, "XGB2", "H2", 0, settings.WRITER_SUBSET) for s in DATASETS]
    return out


def run_id(scenario: str, model: str, variant: str, draw: int, writer: str) -> str:
    return f"{scenario}_{model}_{variant}_d{draw}_{writer}"


def as_answer(draft) -> dict:
    """A draft as the writer's JSON answer, in the writer's names."""
    return {"sentences": [{"id": i, "text": t} for i, t in draft.sentences],
            "claims": [{"sentence_id": c.sentence_id, "dsl": str(labels.external(Claim(c.kind, c.terms, c.value, c.relation, None, c.inner)))}
                       for c in draft.claims]}  # fmt: skip


def stub_writer(contexts: dict[str, g.Context]):
    """Answers with the template of the run's model; the first run's first draft carries a wrong claim."""
    seen = set()

    def respond(request: Request) -> dict:
        run = request.messages[0][1].split("RUN:")[1].split("\n")[0].strip()
        ctx = contexts[run]
        answer = as_answer(template(ctx.facts, ctx.certified))
        if run not in seen and run == next(iter(contexts)):
            answer["sentences"].append({"id": 99, "text": "Income has a strong effect."})
            answer["claims"].append({"sentence_id": 99, "dsl": 'strength("income") == "strong"'})
        seen.add(run)
        chars = len(request.system) + sum(len(m[1]) for m in request.messages)
        return stub_message(answer, usage={"input_tokens": int(chars / CHARS_PER_TOKEN), "output_tokens": OUTPUT_TOKENS})

    return respond


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--smoke", action="store_true")
    mode.add_argument("--live", action="store_true")
    parser.add_argument("--sonnet", action="store_true")
    parser.add_argument("--keep", action="store_true", help="dry run: keep the results")
    args = parser.parse_args()
    name = "smoke" if args.smoke else "live" if args.live else "dry_run"
    plan = runs(args.sonnet)
    if args.smoke:
        plan = [(WORKED[0], WORKED[1], v, 0, settings.WRITER) for v in ("H1", "H2")]

    contexts, handovers = {}, {}
    for scenario_id, model, variant, draw, writer in plan:
        scenario = next(s for s in dgp.SCENARIOS if s.id == scenario_id)
        facts = load(scenario, model)
        certified = certified_plan(facts)
        h = handover(facts, dgp.generate(scenario).X, variant, certified)
        if not h.passed:
            raise SystemExit(f"{scenario_id} {model} {variant}: the readable form failed its check; fix it before any call")
        rid = run_id(scenario_id, model, variant, draw, writer)
        contexts[rid], handovers[rid] = g.Context(facts, certified), h.text

    if name == "dry_run":
        scratch = Path(tempfile.mkdtemp(prefix="pilot_dry_"))
        # the stub needs to know which run a request belongs to; live requests never carry this tag
        client = Client("stub", stub_writer(contexts), cache_dir=scratch / "cache")
        out = RESULTS / name if args.keep else scratch / "results"
    else:
        client = Client("sync")
        out = RESULTS / name
    rows = []
    for (scenario_id, model, variant, draw, writer), rid in zip(plan, contexts):
        text = handovers[rid] if name != "dry_run" else f"RUN: {rid}\n{handovers[rid]}"
        state = g.start(rid, text, writer, draw, budget=1 if args.smoke else g.CALL_BUDGET)  # smoke: one call per run
        state = g.run_sync(state, client, contexts[rid], out / f"{rid}.json")
        rows.append({"run": rid, "exit": state.exit, "reason": state.reason, "calls": state.calls, "rounds": state.rounds,
                     "flagged": state.flagged, "cost": round(state.cost, 5), **{k: state.usage.get(k, 0) for k in ("input_tokens", "output_tokens", "cache_read_input_tokens")}})  # fmt: skip
    table = pd.DataFrame(rows)
    out.mkdir(parents=True, exist_ok=True)
    table.to_csv(out / "summary.csv", index=False)
    pd.set_option("display.width", 220)
    print(f"Pilot ({name}): {len(table)} runs; prompts {json.dumps({k: v[:12] for k, v in prompts.hashes().items()})}")
    print(table.drop(columns=["reason"]).to_string(index=False))
    print("\nExit states:", table.exit.value_counts().to_dict())
    if name == "dry_run":
        per_call = table.input_tokens.sum() / table.calls.sum()
        live = sum(table.calls) * (per_call * settings.PRICES[settings.WRITER][0] + OUTPUT_TOKENS * settings.PRICES[settings.WRITER][1]) / 1e6
        print(f"\nDry run: about {per_call:,.0f} input tokens per call. A live pilot with these {sum(table.calls)} calls would cost "
              f"about ${live:.2f} with {settings.WRITER} (no caching assumed); results in {out}")  # fmt: skip
    else:
        print(f"\nTotal cost: ${table.cost.sum():.4f}; results in {out}")


if __name__ == "__main__":
    main()
