"""The refits behind the local spot check's bands (D49): EBM and XGB2 on the three synthetic datasets of seed 2
at n = 50,000, 100 refits each, fitted again and kept whole (facts/refits.py). No LLM, $0.

For each dataset and model: M is rebuilt from its Facts and checked against a fresh fit on the regenerated data
(same logit on every row), then every refit is fitted again and checked against its stored draws before it is
kept. Models already done are skipped. Progress goes to the terminal and to cache/facts/local_refits.log.

Run: `uv run python -m verifier_gate.experiments.local_refits` (about 26 minutes: an EBM refit takes about 4.6 s
and an XGB2 refit about 0.6 s at n = 50,000). Options: --refits N (a quick check on the first N refits, not
saved), --models EBM,XGB2, --scenarios <substring>, --tier plasmode (D67: the plasmode datasets of seed 2 at
n = 30,000, the largest plasmode n).
"""

import argparse
import time

import numpy as np

from verifier_gate.data import dgp, plasmode, tiers
from verifier_gate.experiments import build_facts
from verifier_gate.facts import bootstrap, refits
from verifier_gate.facts.build import Frame
from verifier_gate.facts.schema import Draws

SEED = 2  # the confirmation seed of D49
N = 50_000
SCENARIOS = tuple(s for s in dgp.SCENARIOS if s.seed == SEED and s.n == N)
PLASMODE_SCENARIOS = tuple(s for s in plasmode.SCENARIOS if s.seed == SEED and s.n == max(plasmode.SAMPLE_SIZES))  # D67
TIER_SCENARIOS = {"synthetic": SCENARIOS, "plasmode": PLASMODE_SCENARIOS}
MODELS = ("EBM", "XGB2")
LOG = build_facts.CACHE / "local_refits.log"


def path(scenario: dgp.Scenario, kind: str):
    return build_facts.path(scenario, kind).with_name(f"{kind}_refits.npz")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refits", type=int, default=0, help="check only the first N refits, save nothing")
    parser.add_argument("--models", default=",".join(MODELS))
    parser.add_argument("--scenarios", default="", help="only scenarios whose id contains this")
    parser.add_argument("--tier", default="synthetic", choices=tuple(TIER_SCENARIOS), help="plasmode: D67's datasets")
    args = parser.parse_args()
    logfile = LOG.open("a")

    def log(message: str) -> None:
        stamped = f"{time.strftime('%H:%M:%S')} {message}"
        print(stamped, flush=True)
        logfile.write(stamped + "\n")
        logfile.flush()

    jobs = [(s, k) for s in TIER_SCENARIOS[args.tier] if args.scenarios in s.id for k in args.models.split(",")]
    log(f"{len(jobs)} models" + (f", check of the first {args.refits} refits only" if args.refits else ""))
    start = time.perf_counter()
    for i, (scenario, kind) in enumerate(jobs, 1):
        target = path(scenario, kind)
        if target.exists() and not args.refits:
            log(f"[{i}/{len(jobs)}] {scenario.id} {kind}: done, skipped")
            continue
        t0 = time.perf_counter()
        data = tiers.generate(scenario)
        facts = build_facts.load(scenario, kind)
        M = facts.steps()
        fresh = bootstrap.fit_steps(kind, data.X, data.y, seed=scenario.seed)
        gap = float(np.max(np.abs(M.logit(data.X) - fresh.logit(data.X))))
        if gap > refits.TOLERANCE:
            raise SystemExit(f"{scenario.id} {kind}: M from its Facts differs from a fresh fit by {gap:.3g}")
        stored = facts.draws
        if args.refits:
            stored = Draws(**{kind_: {k: v[: args.refits] for k, v in getattr(stored, kind_).items()} for kind_ in Draws.KINDS})
        models = refits.refit_models(kind, data.X, data.y, scenario.seed, Frame.of(M, data.X), stored, log)
        if not args.refits:
            refits.save_models(models, target)
        log(f"[{i}/{len(jobs)}] {scenario.id} {kind}: M reproduced ({gap:.1g}), {len(models)} refits match their draws, "
            f"{time.perf_counter() - t0:.0f}s, total {(time.perf_counter() - start) / 60:.0f} min")  # fmt: skip
    log("done")


if __name__ == "__main__":
    main()
