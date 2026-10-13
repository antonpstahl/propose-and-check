"""Null check of the bootstrap bands before they are trusted (week 2; §14 D3, D4).

The planted noise features have a true term of exactly zero. A calibrated simultaneous 95% band covers the
whole true curve in 95% of datasets, so it must cover 0 on almost all of the data mass in about 95% of the
noise-feature fits. The EBM's own outer-bag bands failed exactly this (D3: 0 covered on 28-76% of the mass).

Criterion, fixed before the run (13 Oct): for each model, over the 36 noise-feature curves (noise_1 and
noise_2 in 18 datasets), count the curves whose simultaneous band covers 0 on at least 95% of the data mass
(the mass part of the lexicon's "negligible"). The bands pass if the count is at least MIN_COVERED = 32. With a
true rate of 95%, a count of 31 or fewer has probability 3.2% (binomial), so a failure means miscalibration.

Also reported, not part of the criterion: coverage of 0 on all steps (the band's nominal property), the same
for the pointwise band (expected to fail, D4), the share bands of the noise features, the sup-t critical
values, and how often M's own share lies inside its percentile band.

Run: `uv run python -m verifier_gate.experiments.null_check` after build_facts. Writes results/facts/null_check.csv.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from verifier_gate.data import dgp
from verifier_gate.experiments.build_facts import load

NOISE = tuple(f for f, role in dgp.FEATURE_ROLES.items() if role == "noise")
MASS = 0.95
MIN_COVERED = 32
RESULTS = Path(__file__).parents[3] / "results" / "facts"


def covered_mass(band: np.ndarray, mass: np.ndarray) -> float:
    return float(mass[(band[0] <= 0) & (band[1] >= 0)].sum())


def rows(models=("EBM", "XGB2"), scenarios=dgp.SCENARIOS) -> pd.DataFrame:
    out = []
    for scenario in scenarios:
        for kind in models:
            facts = load(scenario, kind, draws=False)
            for feature in facts.features:
                labels = {"scenario": scenario.id, "n": scenario.n, "model": kind, "feature": feature.name}
                out.append(
                    labels
                    | {
                        "role": dgp.FEATURE_ROLES[feature.name],
                        "simultaneous mass": covered_mass(feature.simultaneous, feature.mass),
                        "pointwise mass": covered_mass(feature.pointwise, feature.mass),
                        "simultaneous everywhere": covered_mass(feature.simultaneous, feature.mass > 0) == (feature.mass > 0).sum(),
                        "critical value": feature.critical_value,
                        "share": feature.share.value,
                        "share low": feature.share.band[0],
                        "share high": feature.share.band[1],
                        "share inside band": feature.share.band[0] <= feature.share.value <= feature.share.band[1],
                    }
                )
    return pd.DataFrame(out)


def verdict(table: pd.DataFrame) -> pd.DataFrame:
    noise = table[table.feature.isin(NOISE)]
    summary = noise.groupby("model").agg(
        curves=("feature", "size"),
        covered=("simultaneous mass", lambda m: int((m >= MASS).sum())),
        everywhere=("simultaneous everywhere", "sum"),
        pointwise_covered=("pointwise mass", lambda m: int((m >= MASS).sum())),
        median_critical=("critical value", "median"),
        share_high_max=("share high", "max"),
    )
    summary["passed"] = summary.covered >= MIN_COVERED
    return summary


def main() -> None:
    table = rows()
    RESULTS.mkdir(parents=True, exist_ok=True)
    table.to_csv(RESULTS / "null_check.csv", index=False)
    pd.set_option("display.width", 200)
    print(f"Noise features: simultaneous band covers 0 on >= {MASS:.0%} of the mass; pass if >= {MIN_COVERED} of 36")
    print(verdict(table).to_string())
    print("\nBy sample size (noise features)")
    noise = table[table.feature.isin(NOISE)]
    print(noise.groupby(["model", "n"])[["simultaneous mass", "pointwise mass", "share high"]].median().round(3).to_string())
    print("\nM's share inside its own percentile band, all features:")
    print(table.groupby("model")["share inside band"].mean().round(3).to_string())


if __name__ == "__main__":
    main()
