# %% [markdown]
# # Week 1: model recovery on one synthetic dataset
#
# Fits the EBM and XGB2 on one dataset and compares them with the planted truth T:
# holdout AUC, importance shares, which pairs the EBM finds, how impure its pair terms are, and the
# conditional effects behind the amplification and sign-flip patterns. Draws planted vs EBM shapes.
#
# Run: `uv run python notebooks/01_recovery_check.py [interaction n seed]`, or cell by cell in VS Code.

# %%
import copy
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from interpret.utils import purify
from scipy.special import expit
from sklearn.metrics import roc_auc_score

from verifier_gate.data import dgp
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
for idx, name in enumerate(ebm.term_names_):
    if " & " not in name:
        continue
    scores, weights = ebm.term_scores_[idx], ebm.bin_weights_[idx]
    pure, _, _ = purify(scores, weights)
    impure = np.average(np.abs(scores - pure), weights=weights) / np.average(np.abs(scores), weights=weights)
    if name in dgp.PAIR_FACTORS or impure > 0.25:
        print(f"  {name}: impure part {impure:.0%} of mean |score|")


# %% Shares after purification: move each pair's main-effect parts back into the main terms (per row)
def pair_bin_indices(model, X):
    """Per pair term, each row's cell in the pair's score tensor (one eval_terms pass with cell codes)."""
    probe = copy.deepcopy(model)
    pairs = [i for i, features in enumerate(model.term_features_) if len(features) == 2]
    for i in pairs:
        shape = model.term_scores_[i].shape
        probe.term_scores_[i] = np.arange(np.prod(shape), dtype=np.float64).reshape(shape)
    codes = probe.eval_terms(X)
    return {i: np.unravel_index(codes[:, i].astype(np.int64), model.term_scores_[i].shape) for i in pairs}


def purified_terms(model, X):
    local = model.eval_terms(X)
    terms = {name: local[:, i].copy() for i, name in enumerate(model.term_names_)}
    intercept = float(model.intercept_[0])
    for idx, cells in pair_bin_indices(model, X).items():
        pure, impurities, pure_intercept = purify(model.term_scores_[idx], model.bin_weights_[idx])
        terms[model.term_names_[idx]] = pure[cells]
        intercept += float(pure_intercept[0])
        for (dim,), part in impurities:
            assert len(part) == pure.shape[dim]
            feature = model.feature_names_in_[model.term_features_[idx][dim]]
            terms[feature] += part[cells[dim]]
    assert np.allclose(intercept + sum(terms.values()), model.decision_function(X))
    return {name: values - values.mean() for name, values in terms.items()}


pure_terms = purified_terms(ebm, X)
pure_imp = {name: np.abs(values).mean() for name, values in pure_terms.items()}
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


# %% Conditional effects (partial dependence over the other features) behind the pair patterns
def conditional_effect(margin, feature, lo, hi, moderator, value, rows):
    base = rows.copy()
    base[moderator] = value
    lo_rows, hi_rows = base.copy(), base.copy()
    lo_rows[feature], hi_rows[feature] = lo, hi
    return float(np.mean(margin(hi_rows) - margin(lo_rows)))


margins = {
    "T": truth.logit,
    "EBM": ebm.decision_function,
    "XGB2": lambda Z: xgb2.predict(Z, output_margin=True),
}
rows = X.sample(2_000, random_state=0)
checks = [
    ("utilization 0.15->0.70", "utilization", 0.15, 0.70, "n_delinquencies", [0, 1, 3]),
    ("n_inquiries 0->4", "n_inquiries", 0, 4, "history_months", [30.0, 183.0, 340.0]),
]
for label, feature, lo, hi, moderator, values in checks:
    print(f"{label}, by {moderator} = {values}")
    for model, margin in margins.items():
        effects = [conditional_effect(margin, feature, lo, hi, moderator, v, rows) for v in values]
        print(f"  {model:5s}" + "".join(f"{e:8.2f}" for e in effects))

# %% Figure: planted vs EBM shapes (EBM band = +-1.96 sd across outer bags)
fig, axes = plt.subplots(3, 3, figsize=(12, 10))
for ax, feature in zip(axes.flat, dgp.FEATURES):
    idx = ebm.term_names_.index(feature)
    cuts = np.asarray(ebm.bins_[list(ebm.feature_names_in_).index(feature)][0])
    lo_x, hi_x = np.quantile(X[feature], [0.005, 0.995])
    edges = np.concatenate([[lo_x], cuts[(cuts > lo_x) & (cuts < hi_x)], [hi_x]])
    first = np.searchsorted(cuts, lo_x)  # index of the bin that contains lo_x (bin 0 is below the first cut)
    scores = ebm.term_scores_[idx][1:-1][first : first + len(edges) - 1]
    sd = ebm.standard_deviations_[idx][1:-1][first : first + len(edges) - 1]
    ax.stairs(scores, edges, baseline=None, color="C0", label="EBM")
    band_lo, band_hi = np.append(scores - 1.96 * sd, 0.0), np.append(scores + 1.96 * sd, 0.0)
    band_lo[-1], band_hi[-1] = band_lo[-2], band_hi[-2]
    ax.fill_between(edges, band_lo, band_hi, step="post", color="C0", alpha=0.25)
    grid = np.linspace(lo_x, hi_x, 400)
    if feature in ("n_delinquencies", "n_inquiries"):
        grid = np.arange(np.floor(lo_x), np.ceil(hi_x) + 1)
    ax.plot(grid, truth.term(feature, {feature: grid}), color="C3", lw=1.5, ls="--", label="planted T")
    ax.set_title(f"{feature}  (T {t_shares[feature]:.1%}, EBM {shares.loc[feature, 'EBM']:.1%})", fontsize=10)
    ax.axhline(0, color="grey", lw=0.5)
axes.flat[0].legend()
fig.suptitle(f"{scenario.id}: planted vs EBM main terms (logit scale)")
fig.tight_layout()
path = out_dir / f"{scenario.id}_ebm_shapes.png"
fig.savefig(path, dpi=120)
print(f"figure: {path}")
