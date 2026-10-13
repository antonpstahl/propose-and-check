# %% [markdown]
# # Week 1: model recovery on one synthetic dataset
#
# Fits the EBM and XGB2 on one dataset and compares them with the planted truth T:
# holdout AUC, importance shares, which pairs the EBM finds, how impure its pair terms are, and the
# conditional effects behind the amplification and sign-flip patterns. Draws planted vs EBM shapes.
# The pass/fail acceptance check over all n = 50,000 datasets is `verifier_gate.experiments.acceptance`.
#
# Run: `uv run python notebooks/01_recovery_check.py [interaction n seed]`, or cell by cell in VS Code.

# %%
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.metrics import roc_auc_score

from verifier_gate.data import dgp
from verifier_gate.experiments import acceptance
from verifier_gate.facts.ebm import purify_ebm
from verifier_gate.models.fit_ebm import fit_ebm
from verifier_gate.models.fit_xgb2 import fit_xgb2

args = sys.argv[1:] if len(sys.argv) == 4 else ["dominant", "50000", "1"]
scenario = dgp.Scenario(args[0], int(args[1]), int(args[2]))
out_dir = Path(__file__).parent / "out"
out_dir.mkdir(exist_ok=True)

data = dgp.generate(scenario)
X, y, truth = data.X, data.y, data.truth
print(f"{scenario.id}: n={len(y)}, default rate {y.mean():.3f}")

# %% Fit both models
start = time.perf_counter()
ebm = fit_ebm(X, y, seed=scenario.seed)
print(f"EBM fitted in {time.perf_counter() - start:.0f}s, {len(ebm.term_names_)} terms")
purified = purify_ebm(ebm, X)
start = time.perf_counter()
xgb2 = fit_xgb2(X, y, seed=scenario.seed)
print(f"XGB2 fitted in {time.perf_counter() - start:.0f}s, {xgb2.best_iteration + 1} trees")

# %% Holdout AUC against the true logit
rng = np.random.default_rng(10_000 + scenario.seed)
X_test = dgp.sample_features(50_000, rng)
p_test = expit(truth.logit(X_test))
y_test = (rng.uniform(size=len(X_test)) < p_test).astype(int)
print(
    "holdout AUC: true logit {:.3f} | EBM {:.3f} | XGB2 {:.3f}".format(
        roc_auc_score(y_test, p_test),
        roc_auc_score(y_test, ebm.predict_proba(X_test)[:, 1]),
        roc_auc_score(y_test, xgb2.predict_proba(X_test)[:, 1]),
    )
)

# %% Importance shares: T vs EBM (EBM total includes the pairs it found, planted or not)
t_shares = truth.shares(X)
ebm_imp = dict(zip(ebm.term_names_, ebm.term_importances()))
ebm_total = sum(ebm_imp.values())
rows = [(t, t_shares[t], ebm_imp.get(t, 0.0) / ebm_total) for t in dgp.TERMS]
spurious = {t: v / ebm_total for t, v in ebm_imp.items() if " & " in t and t not in dgp.TERMS}
shares = pd.DataFrame(rows, columns=["term", "T", "EBM"]).set_index("term")
print(shares.round(3).to_string())
print(
    f"EBM pairs: {sum(' & ' in t for t in ebm.term_names_)}, of which spurious {len(spurious)} "
    f"with total share {sum(spurious.values()):.3f} (largest {max(spurious.values(), default=0):.3f})"
)
pair_rank = sorted((v, t) for t, v in ebm_imp.items() if " & " in t)[::-1]
for pair in dgp.PAIR_FACTORS:
    rank = [t for _, t in pair_rank].index(pair) + 1 if pair in ebm_imp else None
    print(f"  planted pair {pair}: found={pair in ebm_imp}, rank among EBM pairs={rank}")

# %% Impurity of EBM pair terms: share of mean |score| that is a main-effect part (moved out by purify)
for idx, pure in purified.pure_pairs.items():
    name, scores, weights = ebm.term_names_[idx], ebm.term_scores_[idx], ebm.bin_weights_[idx]
    impure = np.average(np.abs(scores - pure), weights=weights) / np.average(np.abs(scores), weights=weights)
    if name in dgp.PAIR_FACTORS or impure > 0.25:
        print(f"  {name}: impure part {impure:.0%} of mean |score|")


# %% Shares after purification: each pair's main-effect parts moved back into the main terms (per row)
pure_imp = purified.importances(X)
pure_total = sum(pure_imp.values())
shares["EBM purified"] = [pure_imp.get(t, 0.0) / pure_total for t in shares.index]
spurious_pure = sum(v for t, v in pure_imp.items() if " & " in t and t not in dgp.TERMS) / pure_total
print(shares.round(3).to_string())
print(f"spurious pairs after purification: total share {spurious_pure:.3f}")

# %% How much data mass has a +-1.96 sd band that covers 0 (the "negligible" condition)
for feature in dgp.FEATURES:
    idx = ebm.term_names_.index(feature)
    scores, sd, weights = ebm.term_scores_[idx], ebm.standard_deviations_[idx], ebm.bin_weights_[idx]
    covers = np.abs(scores) <= 1.96 * sd
    print(f"  {feature:16s} band covers 0 on {np.average(covers, weights=weights):.0%} of the data mass")


# %% Conditional effects (main + pair; partial dependence for XGB2) behind the pair patterns
rows = X.sample(acceptance.PD_ROWS, random_state=0)
effects = {
    "T": lambda *args: acceptance.term_effect(truth, *args),
    "EBM": lambda *args: acceptance.term_effect(purified, *args),
    "XGB2": lambda *args: acceptance.margin_effect(lambda Z: xgb2.predict(Z, output_margin=True), rows, *args),
}
for claim, (pair, feature, lo, hi, moderator, values) in acceptance.PAIR_EFFECTS.items():
    print(f"{claim}: {feature} {lo:g}->{hi:g}, by {moderator} = {values}")
    for model, effect in effects.items():
        print(f"  {model:5s}" + "".join(f"{effect(pair, feature, lo, hi, moderator, v):8.2f}" for v in values))

# %% Acceptance check on this dataset (stand-in criteria, see experiments/acceptance.py)
failed = acceptance.failures(acceptance.frame(acceptance.check_terms(purified, data)))
print(failed.to_string(index=False) if len(failed) else "EBM passes every check")


# %% Figure: planted vs purified EBM main terms (no band: the outer-bag spread is too narrow, §14 D3;
# bootstrap bands follow in week 2)
fig, axes = plt.subplots(3, 3, figsize=(12, 10))
for ax, feature in zip(axes.flat, dgp.FEATURES):
    lo_x, hi_x = np.quantile(X[feature], [0.005, 0.995])
    grid = np.linspace(lo_x, hi_x, 2_000)
    if feature in ("n_delinquencies", "n_inquiries"):
        grid = np.arange(np.floor(lo_x), np.ceil(hi_x) + 1)
    ax.plot(grid, purified.term(feature, {feature: grid}), color="C0", lw=1.2, label="EBM purified")
    ax.plot(grid, truth.term(feature, {feature: grid}), color="C3", lw=1.5, ls="--", label="planted T")
    ax.set_title(f"{feature}  (T {t_shares[feature]:.1%}, EBM {shares.loc[feature, 'EBM purified']:.1%})", fontsize=10)
    ax.axhline(0, color="grey", lw=0.5)
axes.flat[0].legend()
fig.suptitle(f"{scenario.id}: planted vs EBM main terms (logit scale)")
fig.tight_layout()
path = out_dir / f"{scenario.id}_ebm_shapes.png"
fig.savefig(path, dpi=120)
print(f"figure: {path}")
