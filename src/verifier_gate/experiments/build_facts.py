"""Facts with bootstrap bands for all 18 synthetic datasets: the 36 models (EBM, XGB2; week 2) and the two
references E1 needs (D12; week 3): the oracle, with bands like a model, and T, without bands (it has no
sampling error).

For each dataset and kind: fit M, purify and centre it (references: read on a fine grid and centre,
facts/reference.py), read REFITS Poisson refits through M's frame, build the Facts and save
cache/facts/<scenario>/<kind>.json, with the draws in <kind>.npz. Models already in the
cache are skipped, so an interrupted run resumes where it stopped. Small datasets run first, so problems show
early. Progress goes to the terminal and to cache/facts/build.log.

Run: `uv run python -m verifier_gate.experiments.build_facts` (about 3-4 hours at 100 refits from an empty
cache: an EBM refit takes 4-6 s at n = 50,000; the oracle and T take minutes in all). Options: --refits N,
--models EBM,XGB2,oracle,T, --scenarios <substring>, --tier synthetic|plasmode (the plasmode tier, plan §4.4:
18 more datasets on TaiwanCredit features, for E1 and E2 in week 7; about 2-3 hours).
Then: `uv run python -m verifier_gate.experiments.null_check`.
"""

import argparse
import time
from pathlib import Path

from verifier_gate.data import dgp, tiers
from verifier_gate.facts import bootstrap
from verifier_gate.facts.build import Frame, build_facts
from verifier_gate.facts.reference import GRID_POINTS, reference_steps
from verifier_gate.facts.schema import Facts

CACHE = Path(__file__).parents[3] / "cache" / "facts"
KINDS = ("EBM", "XGB2", "oracle", "T")


def path(scenario: dgp.Scenario, kind: str) -> Path:
    return CACHE / scenario.id / kind


def load(scenario: dgp.Scenario, kind: str, draws: bool = True) -> Facts:
    return Facts.load(path(scenario, kind), draws=draws)


def refits_of(kind: str, refits: int) -> int:
    return 0 if kind == "T" else refits


def build(scenario: dgp.Scenario, kind: str, refits: int, log=print) -> Facts:
    data = tiers.generate(scenario)
    if kind == "T":
        model = {"kind": kind, "scenario": scenario.id, "interaction": scenario.interaction, "seed": scenario.seed,
                 "parameters": {"grid_points": GRID_POINTS}}  # fmt: skip
        return build_facts(reference_steps(data.truth, data.X), data.X, None, model)
    reference = bootstrap.fit_steps(kind, data.X, data.y, seed=scenario.seed)
    frame = Frame.of(reference, data.X)
    draws = bootstrap.refit_draws(kind, data.X, data.y, scenario.seed, frame, refits=refits, log=log)
    _, _, params = bootstrap.MODELS[kind]
    model = {
        "kind": kind,
        "scenario": scenario.id,
        "interaction": scenario.interaction,
        "seed": scenario.seed,
        "parameters": params,
        "refit_seeds": "model random_state = refit index; weights from default_rng([17, seed, refit])",
    }
    return build_facts(reference, data.X, draws, model)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refits", type=int, default=bootstrap.REFITS)
    parser.add_argument("--models", default=",".join(KINDS))
    parser.add_argument("--scenarios", default="", help="only scenarios whose id contains this")
    parser.add_argument("--tier", default="synthetic", choices=tuple(tiers.TIERS))
    args = parser.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    logfile = (CACHE / "build.log").open("a")

    def log(message: str) -> None:
        stamped = f"{time.strftime('%H:%M:%S')} {message}"
        print(stamped, flush=True)
        logfile.write(stamped + "\n")
        logfile.flush()

    tier_scenarios = tiers.module(args.tier).SCENARIOS
    scenarios = sorted((s for s in tier_scenarios if args.scenarios in s.id), key=lambda s: (s.n, s.seed, s.interaction))
    jobs = [(s, k) for s in scenarios for k in args.models.split(",")]
    log(f"{len(jobs)} models, {args.refits} refits each")
    start = time.perf_counter()
    for i, (scenario, kind) in enumerate(jobs, 1):
        if path(scenario, kind).with_suffix(".json").exists():
            cached = load(scenario, kind, draws=False).bands["refits"]
            if cached != refits_of(kind, args.refits):
                raise SystemExit(f"{path(scenario, kind)} has {cached} refits, not {args.refits}: delete it first")
            log(f"[{i}/{len(jobs)}] {scenario.id} {kind}: cached, skipped")
            continue
        t0 = time.perf_counter()
        facts = build(scenario, kind, args.refits, log)
        facts.save(path(scenario, kind))
        log(f"[{i}/{len(jobs)}] {scenario.id} {kind}: {time.perf_counter() - t0:.0f}s, total {(time.perf_counter() - start) / 60:.0f} min")
    log("done")


if __name__ == "__main__":
    main()
