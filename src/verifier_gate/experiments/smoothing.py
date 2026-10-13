"""Smoothing runs (§14 D3, D6): which EBM setting recovers every planted claim and keeps noise flat?

Grid: smoothing rounds (main and pair terms alike) x max_bins, pairs capped at 5, every other parameter as
in EBM_PARAMS. The tied grid showed that main-term smoothing makes the noise terms worse while pair
smoothing helps the sign flip, so four settings with the two decoupled follow (at max_bins 1024).

Each setting is fitted on all 18 datasets. The acceptance check counts at n = 50,000; at n = 5,000 the
noise terms are read too (D3: the EBM fitted noise there). The planted pairs' ranks among the fitted
pairs are recorded for every fit (D6).

Run: `uv run python -m verifier_gate.experiments.smoothing` (about 25 minutes). Writes checks.csv and
pair_ranks.csv to results/smoothing/ and prints one summary row per setting.
"""

import time
from itertools import product
from pathlib import Path

import pandas as pd

from verifier_gate.data import dgp
from verifier_gate.experiments.acceptance import check_terms, frame
from verifier_gate.facts.ebm import purify_ebm
from verifier_gate.models.fit_ebm import fit_ebm

SMOOTHING_ROUNDS = (0, 75, 200, 500, 1000)
MAX_BINS = (32, 64, 256, 1024)
DECOUPLED = ((0, 500), (0, 1000), (75, 500), (75, 1000))  # (main, pair) smoothing rounds
SETTINGS = [
    {"smoothing_rounds": r, "interaction_smoothing_rounds": r, "max_bins": b}
    for r, b in product(SMOOTHING_ROUNDS, MAX_BINS)
] + [{"smoothing_rounds": r, "interaction_smoothing_rounds": i, "max_bins": 1024} for r, i in DECOUPLED]
INTERACTIONS = 5
SETTING_COLUMNS = ["smoothing_rounds", "interaction_smoothing_rounds", "max_bins"]
RESULTS = Path(__file__).parents[3] / "results" / "smoothing"


def pair_ranks(ebm, X) -> list[dict]:
    """Rank of each planted pair among the fitted pairs by purified share (None if not fitted)."""
    shares = ebm.shares(X)
    pairs = sorted((n for n in ebm.term_names if " & " in n), key=lambda n: -shares[n])
    return [
        {"pair": p, "rank": pairs.index(p) + 1 if p in pairs else None, "share": shares.get(p, 0.0)}
        for p in dgp.PAIR_FACTORS
    ]


def summarise(checks: pd.DataFrame) -> pd.DataFrame:
    """One row per setting: EBM checks passed at n = 50,000, failures by claim, largest noise shares."""
    rows = []
    for (rounds, pair_rounds, bins), group in checks.groupby(SETTING_COLUMNS):
        large = group[group.n == max(dgp.SAMPLE_SIZES)]
        failed = large[~large.passed]
        noise = group[group.claim == "noise"]
        noise = noise.assign(fitted=pd.to_numeric(noise.fitted))  # mixed column when read from CSV
        features = noise[noise.term.isin(["noise_1", "noise_2"])]
        rows.append(
            {
                "smoothing_rounds": rounds,
                "interaction_smoothing_rounds": pair_rounds,
                "max_bins": bins,
                "passed": f"{large.passed.sum()}/{len(large)}",
                "failed": ", ".join(f"{c} {k}" for c, k in failed.claim.value_counts().items()),
                "noise max 50k": noise[noise.n == 50_000].fitted.max(),
                "noise max 5k": noise[noise.n == 5_000].fitted.max(),
                "noise feat. mean 5k": features[features.n == 5_000].fitted.mean(),
            }
        )
    return pd.DataFrame(rows)


def run(settings=SETTINGS, scenarios=dgp.SCENARIOS) -> tuple[pd.DataFrame, pd.DataFrame]:
    datasets = [dgp.generate(s) for s in scenarios]
    checks, ranks = [], []
    for setting in settings:
        start = time.perf_counter()
        for data in datasets:
            s = data.scenario
            ebm = purify_ebm(fit_ebm(data.X, data.y, seed=s.seed, interactions=INTERACTIONS, **setting), data.X)
            labels = {"scenario": s.id, "interaction": s.interaction, "n": s.n, "seed": s.seed, **setting}
            checks.append(frame(check_terms(ebm, data), **labels))
            ranks += [{**labels, **row} for row in pair_ranks(ebm, data.X)]
        print(f"{setting}: {time.perf_counter() - start:.0f}s", flush=True)
    return pd.concat(checks, ignore_index=True), pd.DataFrame(ranks)


def main() -> None:
    checks, ranks = run()
    RESULTS.mkdir(parents=True, exist_ok=True)
    checks.to_csv(RESULTS / "checks.csv", index=False)
    ranks.to_csv(RESULTS / "pair_ranks.csv", index=False)
    pd.set_option("display.width", 250, "display.max_colwidth", 120)
    print(summarise(checks).round(4).to_string(index=False))


if __name__ == "__main__":
    main()
