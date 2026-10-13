# %% [markdown]
# # Root causes of the week-1 acceptance failures (plan §14.1 D7-D9, §14.2)
#
# Change one factor at a time and see which failure disappears:
#
# | Section | Test | Isolates |
# |---|---|---|
# | 1 | oracle coefficients; oracle over 40 fresh seeds | data vs model; the sampling floor (D7) |
# | 2 | noise-free target, pair as the only unknown, interaction constraints | representation, competition, greedy splits (D8) |
# | 3 | XGB2 past early stopping; n = 500,000; XGB2 knobs; EBM pairs as constraints; 10% sign flip | early stopping, shrinkage vs bias (D8, D11, D15) |
# | 4 | Poisson bootstrap on one dataset; 10 fresh seeds | the uncertainty of one sample; systematic model bias (D7, D17) |
# | 5 | null distribution of noise shares, linear model as baseline | flexible model vs the share statistic (D9) |
#
# Sections 2, 4 and 5 are the scratch diagnostics behind §14.2, with the seeds used there, so their numbers
# reproduce. Section 1's 40-seed loop, and the knobs, constraints and 10% sign flip in section 3, were
# re-implemented from the description in §14.1/§14.2 with fixed seeds here; their numbers can differ from the
# plan in the last digit. Section 4 purifies and centres each refit on its bootstrap weights, as
# facts/bootstrap.py does; the scratch run centred on the unweighted sample, so its band edges can differ from
# §14.2 in the fourth decimal.
#
# Run: `uv run python notebooks/02_root_cause.py [sections] [--quick]`, e.g. `... 2 4` (default: all; about
# 1.5 hours, most of it in sections 3 and 4). `--quick` shrinks every loop to check that the code runs (about a
# minute; numbers meaningless).

# %%
import sys
import time

import numpy as np
import pandas as pd
from interpret.glassbox import ExplainableBoostingClassifier, ExplainableBoostingRegressor
from scipy.optimize import brentq
from scipy.special import expit
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from xgboost import DMatrix, XGBClassifier, XGBRegressor

from verifier_gate.data import dgp
from verifier_gate.experiments import acceptance as acc
from verifier_gate.facts.bootstrap import poisson_weights
from verifier_gate.facts.ebm import purify_ebm
from verifier_gate.models.fit_ebm import EBM_PARAMS, fit_ebm
from verifier_gate.models.fit_xgb2 import VALIDATION_SIZE, XGB2_PARAMS, fit_xgb2

QUICK = "--quick" in sys.argv
SECTIONS = {int(a) for a in sys.argv[1:] if a.isdigit()} or {1, 2, 3, 4, 5}
N = 5_000 if QUICK else 50_000  # the size of every "n = 50,000" dataset below
N_LARGE = 20_000 if QUICK else 500_000

SF, AMP = dgp.SIGN_FLIP, dgp.AMPLIFICATION
H, Q = "history_months", "n_inquiries"
FEATURES = list(dgp.FEATURES)
HOLD = dgp.sample_features(20_000, np.random.default_rng(999))
PD_ROWS = HOLD.iloc[:2_000]
pd.set_option("display.width", 250)


def scenario(level, seed, n=N):
    """A benchmark dataset (dgp.generate), or its first n rows in quick mode."""
    data = dgp.generate(dgp.Scenario(level, 50_000, seed))
    if n == 50_000:
        return data
    X, y = data.X.iloc[:n].reset_index(drop=True), data.y[:n]
    return dgp.Dataset(dgp.Scenario(level, n, seed), X, y, dgp.make_truth(X, level))


def draw(level, n, seed):
    rng = np.random.default_rng(seed)
    X = dgp.sample_features(n, rng)
    truth = dgp.make_truth(X, level)
    return X, (rng.uniform(size=n) < expit(truth.logit(X))).astype(int), truth


def slope(m, t):
    m, t = m - m.mean(), t - t.mean()
    return float(m @ t / (t @ t))


def truth_effects(truth):
    return [acc.term_effect(truth, SF, Q, 0.0, 4.0, H, h) for h in (30.0, 340.0)]


def row(label, truth, thin_long, pair_slope, extra=None):
    """pair slope: TreeSHAP or exact pair vs T's pair, row by row; contrast ratio: the stand-in check's
    partial-dependence contrast (thin minus long history) vs T's. 1 = fully recovered."""
    t = truth_effects(truth)
    contrast = (thin_long[0] - thin_long[1]) / (t[0] - t[1])
    out = {"fit": label, "pair slope": pair_slope, "contrast ratio": contrast,
           "thin": thin_long[0], "long": thin_long[1], "T long": t[1]}  # fmt: skip
    return {**out, **(extra or {})}


def ebm_row(label, model, X, truth):
    p = purify_ebm(model, X)  # works for the regressor too
    m = p.term(SF, HOLD) if SF in p.term_names else np.zeros(len(HOLD))
    eff = [acc.term_effect(p, SF, Q, 0.0, 4.0, H, h) for h in (30.0, 340.0)]
    shares = p.shares(X)
    spurious = sum(v for k, v in shares.items() if " & " in k and k not in dgp.TERMS)
    return row(label, truth, eff, slope(m, truth.term(SF, HOLD)),
               {"SF share": shares.get(SF, 0.0), "dti share": shares["dti"], "inq share": shares[Q], "spurious": spurious})  # fmt: skip


def xgb_pair(model, X, ntrees):
    inter = model.get_booster().predict(DMatrix(X), pred_interactions=True, iteration_range=(0, ntrees))
    return 2 * inter[:, FEATURES.index(H), FEATURES.index(Q)]


def xgb_row(label, model, truth, ntrees=None, margin=None, extra=None):
    ntrees = ntrees or model.best_iteration + 1
    margin = margin or (lambda Z: model.predict(Z, output_margin=True, iteration_range=(0, ntrees)))
    eff = [acc.margin_effect(margin, PD_ROWS, SF, Q, 0.0, 4.0, H, h) for h in (30.0, 340.0)]
    return row(label, truth, eff, slope(xgb_pair(model, HOLD, ntrees), truth.term(SF, HOLD)), {"trees": ntrees, **(extra or {})})


def show(rows, title):
    print(f"\n=== {title}")
    print(pd.DataFrame(rows).round(3).to_string(index=False), flush=True)


# %% 1. Data vs model: how much of each planted effect does the sample support? (§14.2, D7)
if 1 in SECTIONS:
    rows = []
    for level in ("weak", "dominant"):
        for seed in dgp.SEEDS:
            data = scenario(level, seed)
            oracle, planted = acc.fit_oracle(data), dgp.coefficients(level)
            rows.append({"dataset": data.scenario.id} | {t: oracle.coef[t] / planted[t] for t in (Q, "dti", AMP, SF)})
    show(rows, "Oracle / planted coefficient (1 = the sample supports the full planted effect)")

    seeds = 3 if QUICK else 40
    rows = []
    for level in dgp.INTERACTION_LEVELS:
        for s in range(seeds):
            X, y, truth = draw(level, N, 9_000 + s)
            data = dgp.Dataset(dgp.Scenario(level, N, 9_000 + s), X, y, truth)
            checks = acc.check_terms(acc.fit_oracle(data), data)
            rows += [{"level": level, "claim": c.claim, "term": c.term, "missed": not c.passed} for c in checks]
    floor = pd.DataFrame(rows).groupby(["level", "claim", "term"]).missed.mean()
    print(f"\n=== D7 sampling floor: share of {seeds} fresh seeds on which even the oracle misses a claim (n = {N:,})")
    print(floor[floor > 0].round(3).to_string(), flush=True)


# %% 2. Sign flip: representation (noise-free), competition (pair alone), greedy splits (constraints) (D8)
if 2 in SECTIONS:
    for level in ("weak", "dominant"):
        data = scenario(level, 2)
        X, y, truth = data.X, data.y, data.truth
        rows = [ebm_row("EBM, as fitted", fit_ebm(X, y, seed=2), X, truth),
                xgb_row("XGB2, as fitted", fit_xgb2(X, y, seed=2), truth)]  # fmt: skip
        # noise-free: regress on the true logit, so no label noise at all
        target = truth.logit(X)
        reg = ExplainableBoostingRegressor(**EBM_PARAMS, random_state=2).fit(X, target)
        rows.append(ebm_row("EBM, noise-free target", reg, X, truth))
        Xf, Xv, tf, tv = train_test_split(X, target, test_size=VALIDATION_SIZE, random_state=2)
        params = {k: v for k, v in XGB2_PARAMS.items() if k != "eval_metric"}
        xr = XGBRegressor(**params, random_state=2).fit(Xf, tf, eval_set=[(Xv, tv)], verbose=False)
        rows.append(xgb_row("XGB2, noise-free target", xr, truth, margin=lambda Z: xr.predict(Z)))
        # isolated: everything but the sign-flip pair given as offset, the model learns the pair alone
        offset = truth.logit(X) - truth.term(SF, X)
        e = ExplainableBoostingClassifier(**EBM_PARAMS, random_state=2).fit(X, y, init_score=offset)
        rows.append(ebm_row("EBM, pair alone (offset)", e, X, truth))
        Xf, Xv, yf, yv, of, ov = train_test_split(X, y, offset, test_size=VALIDATION_SIZE, stratify=y, random_state=2)
        xo = XGBClassifier(**XGB2_PARAMS, random_state=2)
        xo.fit(Xf, yf, base_margin=of, eval_set=[(Xv, yv)], base_margin_eval_set=[ov], verbose=False)
        rows.append(xgb_row("XGB2, pair alone (offset)", xo, truth))
        # greedy split choice: trees may only combine features within a planted pair
        groups = [[H, Q], ["utilization", "n_delinquencies"], ["income"], ["dti"], ["age"], ["noise_1"], ["noise_2"]]
        rows.append(xgb_row("XGB2, interaction constraints", fit_xgb2(X, y, seed=2, interaction_constraints=groups), truth))
        show(rows, f"D8 sign flip, {data.scenario.id} (pair slope / contrast ratio: 1 = fully recovered)")


# %% 3. XGB2 and early stopping, sample size, knobs, constraints from the EBM, a 10% sign flip (D8, D11, D15)
def holdout_auc(margin, data):
    X, y = acc._holdout(data)
    return roc_auc_score(y, margin(X))


def planted_with_sign_flip(level, share, seed, n=N):
    """A dataset like dgp.generate's, with the sign flip planted at `share` instead of 6% (mains unchanged)."""
    means, importances = dgp._population()
    coef = dict(dgp.coefficients(level))
    pair_shares = dict(dgp.PAIR_SHARES[level]) | {SF: share}
    total = dgp.TOTAL_MAIN_IMPORTANCE / (1.0 - sum(pair_shares.values()))
    coef |= {name: s * total / importances[name] for name, s in pair_shares.items()}
    ref = dgp._reference()
    eta = sum(coef[t] * dgp.unit_term(t, ref) for t in dgp.TERMS)
    b0 = brentq(lambda b: expit(b + eta).mean() - dgp.BASE_RATE, -20.0, 20.0, xtol=1e-12)
    rng = np.random.default_rng(seed)
    X = dgp.sample_features(50_000, rng).iloc[:n].reset_index(drop=True)
    uniforms = rng.uniform(size=50_000)[:n]
    offsets = {t: float((coef[t] * dgp.unit_term(t, X)).mean()) for t in dgp.TERMS}
    truth = acc.Oracle(level, b0 + sum(offsets.values()), offsets, coef)  # a truth with these coefficients
    y = (uniforms < expit(truth.logit(X))).astype(np.int64)
    return dgp.Dataset(dgp.Scenario(level, n, seed), X, y, truth)


def sign_flip_passes(checks):
    return next(c.passed for c in checks if c.claim == "sign_flip")


if 3 in SECTIONS:
    data = scenario("weak", 2)
    X, y, truth = data.X, data.y, data.truth
    Xf, Xv, yf, yv = train_test_split(X, y, test_size=VALIDATION_SIZE, stratify=y, random_state=2)
    params = {**XGB2_PARAMS, "early_stopping_rounds": None, "n_estimators": 300 if QUICK else 3_000}
    m = XGBClassifier(**params, random_state=2).fit(Xf, yf, eval_set=[(Xv, yv)], verbose=False)
    loss = np.array(m.evals_result()["validation_0"]["logloss"])
    best = int(loss.argmin()) + 1
    rows = [xgb_row(f"{k} trees" + (" (best val. loss)" if k == best else ""), m, truth, ntrees=k, extra={"val. logloss": loss[k - 1]})
            for k in sorted({50, 100, 200, best, 500, 1000, 2000, 3000}) if k <= len(loss)]  # fmt: skip
    show(rows, f"D8 XGB2 boosting curve, {data.scenario.id}")

    rows = []
    for level in ("weak", "dominant"):
        for n in (N, N_LARGE):
            X, y, truth = draw(level, n, 4_000)
            t0 = time.perf_counter()
            rows.append(ebm_row(f"EBM {level} n={n:,}", fit_ebm(X, y, seed=4), X, truth))
            rows.append(xgb_row(f"XGB2 {level} n={n:,}", fit_xgb2(X, y, seed=4), truth))
            print(f"{level} n={n}: {time.perf_counter() - t0:.0f}s", flush=True)
    show(rows, "D8 sample size: shrinkage that fades with n is estimation, what stays is bias")

    knobs = {"as fitted": {}, "early stopping 500": {"early_stopping_rounds": 500}, "learning rate 0.01": {"learning_rate": 0.01},
             "L2 10": {"reg_lambda": 10.0}, "column sampling 0.5": {"colsample_bytree": 0.5}}  # fmt: skip
    for level in ("weak", "dominant"):
        data = scenario(level, 2)
        rows = [xgb_row(label, fit_xgb2(data.X, data.y, seed=2, **k), data.truth) for label, k in knobs.items()]
        show(rows, f"D8 XGB2 knobs, {data.scenario.id}")

    rows = []
    for level in ("weak", "dominant"):
        for seed in dgp.SEEDS:
            data = scenario(level, seed)
            ebm = purify_ebm(fit_ebm(data.X, data.y, seed=seed), data.X)
            detected = [list(ebm.steps[p].features) for p in ebm.pairs]
            singles = [[f] for f in FEATURES if not any(f in g for g in detected)]
            for label, overrides in (("as fitted", {}),
                                     ("EBM pairs as constraints, 3,000 trees", {"interaction_constraints": detected + singles,
                                      "early_stopping_rounds": None, "n_estimators": 300 if QUICK else 3_000})):  # fmt: skip
                model = fit_xgb2(data.X, data.y, seed=seed, **overrides)
                margin = lambda Z, m=model: m.predict(Z, output_margin=True)  # noqa: E731
                rows.append({"dataset": data.scenario.id, "XGB2": label, "sign flip passes": sign_flip_passes(acc.check_margin(margin, data)),
                             "holdout AUC": holdout_auc(margin, data)})  # fmt: skip
    show(rows, "D8/D15 XGB2 with the EBM's detected pairs as interaction constraints (recovery-tuned XGB2)")

    rows = []
    for level in ("weak", "dominant"):
        for seed in dgp.SEEDS:
            data = planted_with_sign_flip(level, 0.10, seed)
            ebm = purify_ebm(fit_ebm(data.X, data.y, seed=seed), data.X)
            xgb = fit_xgb2(data.X, data.y, seed=seed)
            rows.append({"dataset": f"{level} s{seed}, sign flip 10%",
                         "EBM passes": sign_flip_passes(acc._pair_checks(lambda *a: acc.term_effect(ebm, *a), data.truth, level)),
                         "XGB2 passes": sign_flip_passes(acc.check_margin(lambda Z: xgb.predict(Z, output_margin=True), data))})  # fmt: skip
    show(rows, "D11 rejected alternative: a 10% sign flip")


# %% 4. Poisson bootstrap on the failing datasets, and EBM bias over 10 fresh seeds (D7, D17)
def weighted_oracle(data, w):
    names = [t for t in dgp.TERMS if np.ptp(dgp.unit_term(t, data.X.iloc[:1000])) > 0]
    Z = np.column_stack([dgp.unit_term(t, data.X) for t in names])
    scale = Z.std(axis=0)
    fit = LogisticRegression(C=np.inf, max_iter=10_000).fit(Z / scale, data.y, sample_weight=w)
    coef = dict.fromkeys(dgp.TERMS, 0.0) | dict(zip(names, fit.coef_[0] / scale))
    return acc.Oracle(data.scenario.interaction, 0.0, dict.fromkeys(dgp.TERMS, 0.0), coef)


def weighted_shares(model, X, w):
    imp = {k: np.average(np.abs(v), weights=w) for k, v in model.terms(X).items()}
    total = sum(imp.values())
    return {k: v / total for k, v in imp.items()}


if 4 in SECTIONS:
    ebm_refits, oracle_refits = (2, 5) if QUICK else (15, 200)
    rng = np.random.default_rng(0)  # the scratch run's weights; facts/bootstrap.py seeds per dataset and refit
    for level, seed, terms in (("weak", 2, [AMP]), ("dominant", 1, [Q]), ("dominant", 2, [SF, "dti"])):
        data = scenario(level, seed)
        n = len(data.X)
        fits = {"oracle": [], "EBM": []}
        for b in range(oracle_refits):
            w = rng.poisson(1.0, n).astype(float)
            fits["oracle"].append(weighted_shares(weighted_oracle(data, w), data.X, w))
            if b < ebm_refits:
                t0 = time.perf_counter()
                drawn = w > 0  # interpret rejects zero weights; rows drawn at least once, weighted by count
                e = ExplainableBoostingClassifier(**EBM_PARAMS, random_state=b).fit(data.X[drawn], data.y[drawn], sample_weight=w[drawn])
                fits["EBM"].append(weighted_shares(purify_ebm(e, data.X, w), data.X, w))  # as facts/bootstrap.py
                if b == 0:
                    print(f"{data.scenario.id}: one weighted EBM refit takes {time.perf_counter() - t0:.0f}s", flush=True)
        full = {"oracle": acc.fit_oracle(data).shares(data.X), "EBM": purify_ebm(fit_ebm(data.X, data.y, seed=seed), data.X).shares(data.X)}
        for term in terms:
            t = data.truth.shares(data.X)[term]
            for model, shares in fits.items():
                b = np.array([s.get(term, 0.0) for s in shares])
                print(f"{data.scenario.id} {term:30s} T {t:.4f} | {model:6s} estimate {full[model].get(term, 0):.4f}, "
                      f"bootstrap 95% [{np.quantile(b, 0.025):.4f}, {np.quantile(b, 0.975):.4f}] ({len(b)} refits)", flush=True)  # fmt: skip
    print("\n=== EBM bias over 10 fresh seeds: mean share vs T", flush=True)
    for level, terms in (("weak", [AMP, SF]), ("dominant", [Q, "dti", SF])):
        rows = []
        for seed in range(2 if QUICK else 10):
            X, y, truth = draw(level, N, 7_000 + seed)
            data = dgp.Dataset(dgp.Scenario(level, N, seed), X, y, truth)
            e, o, t = purify_ebm(fit_ebm(X, y, seed=seed), X).shares(X), acc.fit_oracle(data).shares(X), truth.shares(X)
            rows += [{"term": k, "T": t[k], "oracle": o[k], "EBM": e.get(k, 0.0)} for k in terms]
        print(level)
        print(pd.DataFrame(rows).groupby("term").agg(["mean", "std"]).round(4).to_string(), flush=True)
    assert poisson_weights  # the week-2 bands use facts/bootstrap.py, same scheme, seeded per dataset


# %% 5. Null distribution of noise shares: the model or the share statistic? (D9)
def linear_noise_shares(X, y):
    """Oracle plus the two noise features as linear terms: the least flexible model that can fit noise."""
    names = [t for t in dgp.TERMS if np.ptp(dgp.unit_term(t, X.iloc[:1000])) > 0]
    Z = np.column_stack([dgp.unit_term(t, X) for t in names] + [X["noise_1"], X["noise_2"]])
    scale = Z.std(axis=0)
    coef = LogisticRegression(C=np.inf, max_iter=10_000).fit(Z / scale, y).coef_[0] / scale
    imp = np.abs((Z - Z.mean(axis=0)) * coef).mean(axis=0)
    return dict(zip(names + ["noise_1", "noise_2"], imp / imp.sum()))


if 5 in SECTIONS:
    rows = []
    for n, seeds in ((5_000, range(2 if QUICK else 20)), (N, range(1 if QUICK else 6))):
        for seed in seeds:
            X, y, truth = draw("none", n, 5_000 + seed)
            ebm = purify_ebm(fit_ebm(X, y, seed=seed), X).shares(X)
            x = fit_xgb2(X, y, seed=seed)
            contrib = x.get_booster().predict(DMatrix(X), pred_contribs=True, iteration_range=(0, x.best_iteration + 1))
            imp = np.abs(contrib[:, :-1]).mean(axis=0)
            xgb = dict(zip(FEATURES, imp / imp.sum()))
            lin = linear_noise_shares(X, y)
            for model, sh in (("EBM", ebm), ("XGB2 (TreeSHAP)", xgb), ("linear", lin)):
                rows += [{"n": n, "model": model, "term": t, "share": sh[t]} for t in ("noise_1", "noise_2", "age")]
            spurious = max((v for k, v in ebm.items() if " & " in k), default=0.0)
            rows.append({"n": n, "model": "EBM", "term": "largest spurious pair", "share": spurious})
    df = pd.DataFrame(rows)
    df["term"] = df.term.replace({"noise_1": "noise", "noise_2": "noise"})
    summary = df.groupby(["term", "n", "model"]).share.agg(
        median="median", p95=lambda s: s.quantile(0.95), at_least_2pct=lambda s: (s >= 0.02).mean(), draws="size")
    print("\n=== D9 null distribution of shares (level none; age has a planted 1% share)")
    print(summary.round(4).to_string(), flush=True)

    rows = []
    for level, seed in (("none", 2), ("weak", 1)):  # the two noise failures at n = 50,000 (§14.1)
        data = scenario(level, seed)
        ebm = purify_ebm(fit_ebm(data.X, data.y, seed=seed), data.X).shares(data.X)
        lin = linear_noise_shares(data.X, data.y)
        rows += [{"dataset": data.scenario.id, "feature": f, "EBM": ebm[f], "linear": lin[f]} for f in ("noise_1", "noise_2")]
    show(rows, "Noise at n = 50,000: a chance trend in the data (linear model fits it too) or EBM wiggles?")
