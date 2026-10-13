"""Recheck of the EBM setting on fresh seeds 4-6 (§14.2 D18).

The setting was chosen on seeds 1-3 (experiments/smoothing.py), which include the confirmation seeds, and the
best settings differed there by only 2-3 of 278 checks. The five best settings of that run are fitted again
on 18 fresh datasets: seeds 4-6, all three interaction levels, both sample sizes.

Decision rule, fixed before the run (13 Oct):
- Primary: EBM model misses (D10: a failed check the oracle passes) on the nine n = 50,000 datasets.
- Keep the current setting unless another one has at least MIN_GAIN fewer model misses and a mean
  noise-feature share at n = 5,000 at most NOISE_SLACK above the current one (main-term smoothing made the
  noise terms larger on seeds 1-3, §14.1). If several qualify: fewest model misses, then lowest noise share.
- MIN_GAIN = 3 is about 1% of the checks per setting and larger than the gap that decided on seeds 1-3 (2).

Run: `uv run python -m verifier_gate.experiments.recheck` (about 15 minutes). Writes checks.csv, oracle.csv
and summary.csv to results/recheck/ and prints the summary and the decision.
"""

from pathlib import Path

import pandas as pd

from verifier_gate.data import dgp
from verifier_gate.experiments import smoothing
from verifier_gate.experiments.acceptance import attribute, check_terms, fit_oracle, frame

SEEDS = (4, 5, 6)
SCENARIOS = tuple(dgp.Scenario(i, n, s) for i in dgp.INTERACTION_LEVELS for n in dgp.SAMPLE_SIZES for s in SEEDS)
LARGE = max(dgp.SAMPLE_SIZES)

# The five best settings on seeds 1-3 (EBM checks passed at n = 50,000), current one first
CURRENT = {"smoothing_rounds": 0, "interaction_smoothing_rounds": 1000, "max_bins": 1024}  # 269/278
CANDIDATES = [
    CURRENT,
    {"smoothing_rounds": 75, "interaction_smoothing_rounds": 1000, "max_bins": 1024},  # 267/278
    {"smoothing_rounds": 75, "interaction_smoothing_rounds": 500, "max_bins": 1024},  # 266/278
    {"smoothing_rounds": 0, "interaction_smoothing_rounds": 500, "max_bins": 1024},  # 266/278
    {"smoothing_rounds": 1000, "interaction_smoothing_rounds": 1000, "max_bins": 1024},  # 264/279
]
MIN_GAIN = 3
NOISE_SLACK = 0.002
RESULTS = Path(__file__).parents[3] / "results" / "recheck"


def oracle_checks(scenarios=SCENARIOS) -> pd.DataFrame:
    """The oracle's checks on each n = 50,000 dataset: the reference for model vs data misses."""
    parts = []
    for scenario in (s for s in scenarios if s.n == LARGE):
        data = dgp.generate(scenario)
        parts.append(frame(check_terms(fit_oracle(data), data), scenario=scenario.id, model="oracle"))
    return pd.concat(parts, ignore_index=True)


def summarise(checks: pd.DataFrame, oracle: pd.DataFrame) -> pd.DataFrame:
    """One row per setting: checks, passes, model and data misses at n = 50,000, noise at n = 5,000."""
    rows = []
    for setting, group in checks.groupby(smoothing.SETTING_COLUMNS, sort=False):
        large = group[group.n == LARGE]
        miss = attribute(large, oracle)
        noise = group[(group.n == min(dgp.SAMPLE_SIZES)) & group.term.isin(["noise_1", "noise_2"])]
        rows.append(
            dict(zip(smoothing.SETTING_COLUMNS, setting))
            | {
                "checks": len(large),
                "passed": int(large.passed.sum()),
                "model_misses": int((miss == "model").sum()),
                "data_misses": int((miss == "data").sum()),
                "model misses by claim": ", ".join(f"{c} {k}" for c, k in large.claim[miss == "model"].value_counts().items()),
                "noise feat. mean 5k": float(pd.to_numeric(noise.fitted).mean()),
            }
        )
    return pd.DataFrame(rows)


def decide(summary: pd.DataFrame, current=CURRENT) -> dict:
    """The setting to use, by the rule in the module docstring."""
    columns = smoothing.SETTING_COLUMNS
    is_current = (summary[columns] == pd.Series(current)).all(axis=1)
    base = summary[is_current].iloc[0]
    better = summary[
        ~is_current
        & (summary.model_misses <= base.model_misses - MIN_GAIN)
        & (summary["noise feat. mean 5k"] <= base["noise feat. mean 5k"] + NOISE_SLACK)
    ]
    if better.empty:
        return dict(current)
    best = better.sort_values(["model_misses", "noise feat. mean 5k"]).iloc[0]
    return {c: int(best[c]) for c in columns}


def main() -> None:
    checks, ranks = smoothing.run(CANDIDATES, SCENARIOS)
    oracle = oracle_checks()
    RESULTS.mkdir(parents=True, exist_ok=True)
    checks.to_csv(RESULTS / "checks.csv", index=False)
    ranks.to_csv(RESULTS / "pair_ranks.csv", index=False)
    oracle.to_csv(RESULTS / "oracle.csv", index=False)
    table = summarise(checks, oracle)
    table.to_csv(RESULTS / "summary.csv", index=False)
    pd.set_option("display.width", 250, "display.max_colwidth", 100)
    print(table.round(4).to_string(index=False))
    choice = decide(table)
    print(f"\ndecision: {'keep' if choice == CURRENT else 'switch to'} {choice}")


if __name__ == "__main__":
    main()
