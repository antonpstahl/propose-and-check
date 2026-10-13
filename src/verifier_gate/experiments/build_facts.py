"""Facts with bootstrap bands for all 36 synthetic models: 18 datasets x {EBM, XGB2} (week 2).

For each dataset and model: fit M, purify and centre it, read REFITS Poisson refits through M's frame, build
the Facts and save cache/facts/<scenario>/<model>.json, with the draws in <model>.npz. Models already in the
cache are skipped, so an interrupted run resumes where it stopped. Small datasets run first, so problems show
early. Progress goes to the terminal and to cache/facts/build.log.

Run: `uv run python -m verifier_gate.experiments.build_facts` (about 3-4 hours at 100 refits: an EBM refit
takes 4-6 s at n = 50,000). Options: --refits N, --models EBM,XGB2, --scenarios <substring>.
Then: `uv run python -m verifier_gate.experiments.null_check`.
"""

import argparse
import time
from pathlib import Path

from verifier_gate.data import dgp
from verifier_gate.facts import bootstrap
from verifier_gate.facts.build import Frame, build_facts
from verifier_gate.facts.schema import Facts

CACHE = Path(__file__).parents[3] / "cache" / "facts"


def path(scenario: dgp.Scenario, kind: str) -> Path:
    return CACHE / scenario.id / kind


def load(scenario: dgp.Scenario, kind: str, draws: bool = True) -> Facts:
    return Facts.load(path(scenario, kind), draws=draws)


def build(scenario: dgp.Scenario, kind: str, refits: int, log=print) -> Facts:
    data = dgp.generate(scenario)
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
    parser.add_argument("--models", default="EBM,XGB2")
    parser.add_argument("--scenarios", default="", help="only scenarios whose id contains this")
    args = parser.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    logfile = (CACHE / "build.log").open("a")

    def log(message: str) -> None:
        stamped = f"{time.strftime('%H:%M:%S')} {message}"
        print(stamped, flush=True)
        logfile.write(stamped + "\n")
        logfile.flush()

    scenarios = sorted((s for s in dgp.SCENARIOS if args.scenarios in s.id), key=lambda s: (s.n, s.seed, s.interaction))
    jobs = [(s, k) for s in scenarios for k in args.models.split(",")]
    log(f"{len(jobs)} models, {args.refits} refits each")
    start = time.perf_counter()
    for i, (scenario, kind) in enumerate(jobs, 1):
        if path(scenario, kind).with_suffix(".json").exists():
            cached = load(scenario, kind, draws=False).bands["refits"]
            if cached != args.refits:
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
