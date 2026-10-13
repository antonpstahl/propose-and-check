# %% [markdown]
# # Week 2: what the bootstrap bands can and cannot decide (plan §14.4)
#
# Reads the cached Facts of all 36 synthetic models (experiments/build_facts.py); no fitting, a few seconds.
#
# 1. Calibration on the noise features: how far M's noise curve strays, relative to the band's half-width.
# 2. Power on the planted features: where the simultaneous band excludes 0, and whether the net change
#    (5th to 95th percentile) is significant.
# 3. Centring: how often M lies outside its own percentile band.
# 4. A preview of three-valued verdicts. Not the lexicon (week 3): strength from the share band against the
#    planted class (D13 logic), the planted interaction patterns from the conditional-effect bands.
# 5. Planted pairs at level "none": does a model fit them anyway?
#
# Run: `uv run python notebooks/03_bands.py`.

# %%
import numpy as np
import pandas as pd

from verifier_gate.data import dgp
from verifier_gate.experiments.build_facts import load

pd.set_option("display.width", 250)
CLASSES = (("negligible", 0.0, 0.02), ("weak", 0.02, 0.05), ("moderate", 0.05, 0.15), ("strong", 0.15, 1.0))


def strength_class(share: float) -> str:
    return next(name for name, lo, hi in CLASSES if lo <= share < hi)


def strength_verdict(band: tuple[float, float], planted: str) -> str:
    """True if the share band lies inside the planted class, false if entirely outside, else undecidable."""
    _, lo, hi = next(c for c in CLASSES if c[0] == planted)
    if lo <= band[0] and band[1] < hi:
        return "true"
    if band[1] < lo or band[0] >= hi:
        return "false"
    return "undecidable"


def sign_flip_verdict(at_low, at_high) -> str:
    """'reverses': the inquiries effect is significantly positive for thin files, negative for long histories."""
    if at_low.band[0] > 0 and at_high.band[1] < 0:
        return "true"
    same_sign = (at_low.band[0] > 0 and at_high.band[0] > 0) or (at_low.band[1] < 0 and at_high.band[1] < 0)
    return "false" if same_sign else "undecidable"


def amplification_verdict(at_low, at_high, difference) -> str:
    """'amplifies': the utilization effect is significantly positive at both, and significantly larger at high."""
    if at_low.band[0] > 0 and at_high.band[0] > 0 and difference.band[0] > 0:
        return "true"
    return "false" if difference.band[1] <= 0 or at_low.band[1] < 0 else "undecidable"


def inside(estimate) -> bool:
    return estimate.band[0] <= estimate.value <= estimate.band[1]


features, centring, pairs = [], [], []
for scenario in dgp.SCENARIOS:
    data = dgp.generate(scenario)
    planted_shares = data.truth.shares(data.X)
    for kind in ("EBM", "XGB2"):
        facts = load(scenario, kind, draws=False)
        labels = {"model": kind, "n": scenario.n, "level": scenario.interaction, "seed": scenario.seed}
        for f in facts.features:
            used = f.mass > 0
            sd = (f.simultaneous[1] - f.scores) / f.critical_value if f.critical_value else np.zeros_like(f.scores)
            z = np.abs(f.scores[used]) / np.where(sd[used] > 0, sd[used], np.inf)
            excludes = lambda band: f.mass[(band[0] > 0) | (band[1] < 0)].sum()  # noqa: E731
            features.append(labels | {
                "feature": f.name, "role": dgp.FEATURE_ROLES[f.name], "c": f.critical_value,
                "deviation / half-width": z.max() / f.critical_value if f.critical_value else np.nan,
                "simultaneous excludes 0": excludes(f.simultaneous), "pointwise excludes 0": excludes(f.pointwise),
                "net change significant": f.net_change.band[0] > 0 or f.net_change.band[1] < 0,
                "share": f.share.value, "share high": f.share.band[1],
                "planted class": strength_class(planted_shares[f.name]),
                "strength verdict": strength_verdict(f.share.band, strength_class(planted_shares[f.name])),
            })  # fmt: skip
            centring += [labels | {"quantity": q, "outside": not inside(e)} for q, e in (("share", f.share), ("net change", f.net_change))]
        for p in facts.pairs:
            for c in p.conditional:
                centring += [labels | {"quantity": "conditional effect", "outside": not inside(e)} for e in (c.at_low, c.at_high)]
                centring.append(labels | {"quantity": "interaction contrast", "outside": not inside(c.difference)})
        for name in dgp.PAIR_FACTORS:
            pair = facts.pair(*name.split(" & "))
            row = labels | {"pair": name, "present": pair is not None}
            if pair is not None:
                key = "n_inquiries | history_months" if name == dgp.SIGN_FLIP else "utilization | n_delinquencies"
                c = next(c for c in pair.conditional if c.key == key)
                verdict = sign_flip_verdict(c.at_low, c.at_high) if name == dgp.SIGN_FLIP else amplification_verdict(c.at_low, c.at_high, c.difference)
                row |= {"share": pair.share.value, "share low": pair.share.band[0], "share high": pair.share.band[1],
                        "at low": c.at_low.value, "at low band": tuple(np.round(c.at_low.band, 2)),
                        "at high": c.at_high.value, "at high band": tuple(np.round(c.at_high.band, 2)), "verdict": verdict}  # fmt: skip
            pairs.append(row)
features, centring, pairs = pd.DataFrame(features), pd.DataFrame(centring), pd.DataFrame(pairs)

# %% 1. Calibration on the noise features
noise = features[features.role == "noise"]
print("=== 1. Noise curves: largest |M| / sd, as a fraction of the sup-t critical value c (calibrated: ~95% <= 1)")
print(noise.groupby(["model", "n"]).agg(
    curves=("feature", "size"), median=("deviation / half-width", "median"),
    p90=("deviation / half-width", lambda x: x.quantile(0.9)), max=("deviation / half-width", "max"),
    c_median=("c", "median"), pointwise_excludes_mean=("pointwise excludes 0", "mean"),
).round(3).to_string())  # fmt: skip
print("(a calibrated pointwise band excludes 0 on about 5% of a null curve's mass)")

# %% 2. Power on the planted features
planted = features[~features.role.isin(["noise"])]
print("\n=== 2. Planted features: median mass where the simultaneous band excludes 0; share of datasets with a significant net change")
print(planted.groupby(["feature", "model", "n"]).agg(
    simultaneous_excludes=("simultaneous excludes 0", "median"), net_significant=("net change significant", "mean"),
).round(2).unstack("n").to_string())  # fmt: skip

# %% 3. Centring of the refits on M
print("\n=== 3. M outside its own 95% percentile band (about 5% or less if the refits are centred on M)")
print(centring.groupby(["quantity", "model", "n"]).outside.mean().round(3).unstack("n").to_string())

# %% 4. Verdict preview
print("\n=== 4a. Strength from the share band vs the planted class (9 datasets per cell)")
print(features.groupby(["feature", "planted class", "model", "n"])["strength verdict"].value_counts().unstack(fill_value=0).to_string())
print("\nNoise features: upper end of the share band (median, max)")
print(noise.groupby(["model", "n"])["share high"].agg(["median", "max"]).round(4).to_string())
print("\n=== 4b. Planted interaction patterns on the conditional-effect bands (levels weak and dominant, 3 seeds each)")
active = pairs[pairs.level != "none"]
print(active.groupby(["pair", "model", "n", "level"]).verdict.value_counts().unstack(fill_value=0).to_string())
columns = ["model", "level", "seed", "share", "at low", "at low band", "at high", "at high band", "verdict"]
print(active[(active.n == 50_000) & (active.pair == dgp.SIGN_FLIP)][columns].round(3).to_string(index=False))

# %% 5. Planted pairs at level "none" (truth: zero)
print("\n=== 5. Planted pairs at level 'none': present in the model, share and its band")
none = pairs[pairs.level == "none"]
print(none.groupby(["pair", "model", "n"]).agg(
    present=("present", "mean"), share_max=("share", "max"), share_low_max=("share low", "max"), share_high_max=("share high", "max"),
).round(4).to_string())  # fmt: skip
