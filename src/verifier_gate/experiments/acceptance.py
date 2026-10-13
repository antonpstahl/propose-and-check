"""Acceptance check (§4.1): does a fitted model recover every planted claim at n = 50,000?

Each claim is measured the same way on T and on the model, then compared. The criteria are stand-ins:
point values against tolerances. These runs are diagnostics; the binding run uses the lexicon's three-valued
verdicts on the frozen lexicon (§14.4 D24, §14.5).

| claim         | stand-in                                                                        |
|---------------|---------------------------------------------------------------------------------|
| strength      | strength class of the share matches T (lexicon v0 bands)                        |
| rank          | rank among the main terms matches T                                             |
| direction     | sign of the net change from the 5th to the 95th percentile matches T            |
| peak          | maximum of history_months within 6 months of T's                                |
| step          | largest rise of dti over one bin (0.01, one bin at 64 bins) within one bin of T's |
| amplification | utilization effect has T's sign at 0 and 3 delinquencies, and grows by at least |
|               | half as much as in T                                                            |
| sign_flip     | inquiries effect has T's sign for thin files and long histories, and at least   |
|               | half T's size on both                                                           |
| noise         | share below 2% for every term T sets to zero (noise, spurious pairs, planted   |
|               | pairs at level "none")                                                          |
| auc           | holdout AUC at most 0.01 below the planted logit's                              |

Every model gets every check on its exact terms: T, the oracle, the purified EBM and, through its exact
decomposition, XGB2 (D26). XGB2's two pair checks on partial dependence of its margin, the only XGB2 checks
before D26, are kept as a cross-check under the model name "XGB2 (PD)"; they are not part of its verdict.

The oracle is a logistic regression on the planted unit shapes, so only the coefficients are estimated:
the best any model can do on the sample. The acceptance rule is relative to it (§14.2 D10): a model has to
recover every claim the oracle recovers on the same dataset. Each failed check is labelled
- "model" (a model miss) if the oracle passes the same claim on the same dataset,
- "data" (a data miss) if the oracle fails it too: the sample does not support the claim. Reported, not fixed.
The oracle knows which terms are zero, so it passes every noise check; a noise failure is always a model miss.

Run: `uv run python -m verifier_gate.experiments.acceptance` (about 1 minute).
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.metrics import roc_auc_score

from verifier_gate.data import dgp
from verifier_gate.facts.ebm import purify_ebm
from verifier_gate.facts.xgb2 import purify_xgb2
from verifier_gate.models import fit_oracle as oracle_model
from verifier_gate.models.fit_ebm import fit_ebm
from verifier_gate.models.fit_xgb2 import fit_xgb2

Oracle = oracle_model.Oracle

SCENARIOS = tuple(s for s in dgp.SCENARIOS if s.n == max(dgp.SAMPLE_SIZES))
MODELS = ("T", "oracle", "EBM", "XGB2")
CROSS_CHECK = "XGB2 (PD)"  # XGB2's pair checks on partial dependence of its margin, as before D26
RESULTS = Path(__file__).parents[3] / "results" / "acceptance"

STRENGTH = (("strong", 0.15), ("moderate", 0.05), ("weak", 0.02))  # lexicon v0, below 2%: negligible
NOISE_SHARE = 0.02
SHAPED = tuple(f for f, role in dgp.FEATURE_ROLES.items() if role not in ("near_flat", "noise"))
NET_CHANGE = (0.05, 0.95)  # quantiles for direction
SEARCH_RANGE = (0.01, 0.99)  # quantiles for peak and step; EBM edge bins can spike
PEAK = ("history_months", 6.0)  # feature, tolerance in months
STEP = ("dti", 0.01)  # feature, bin width = tolerance
GRID_POINTS = 2_000
EFFECT_FRACTION = 0.5
AUC_TOLERANCE = 0.01
HOLDOUT_N = 50_000
PD_ROWS = 2_000

# (pair, feature, low, high, moderator, moderator values): conditional effect of the feature, main + pair
PAIR_EFFECTS = {
    "amplification": (dgp.AMPLIFICATION, "utilization", 0.15, 0.70, "n_delinquencies", (0.0, 3.0)),
    "sign_flip": (dgp.SIGN_FLIP, "n_inquiries", 0.0, 4.0, "history_months", (30.0, 340.0)),
}


@dataclass(frozen=True)
class Check:
    claim: str
    term: str
    planted: float | tuple[float, ...]  # measured on T
    fitted: float | tuple[float, ...]  # measured on the model
    passed: bool


def fit_oracle(data: dgp.Dataset) -> Oracle:
    return oracle_model.fit_oracle(data.X, data.y, interaction=data.scenario.interaction)


def strength(share: float) -> str:
    return next((label for label, lower in STRENGTH if share >= lower), "negligible")


def _ranks(shares: Mapping[str, float]) -> dict[str, int]:
    order = sorted(dgp.FEATURES, key=lambda f: -shares.get(f, 0.0))
    return {f: order.index(f) + 1 for f in dgp.FEATURES}


def _argmax(grid: np.ndarray, values: np.ndarray) -> float:
    """Centre of the first run of grid points where the values reach their maximum."""
    top = np.flatnonzero(values >= values.max() - 1e-12)
    gaps = np.flatnonzero(np.diff(top) > 1)
    return float(grid[top[: gaps[0] + 1] if len(gaps) else top].mean())


def _search_grid(X: pd.DataFrame, feature: str, margin: float = 0.0) -> np.ndarray:
    lo, hi = np.quantile(X[feature], SEARCH_RANGE)
    return np.linspace(lo, hi - margin, GRID_POINTS)


def peak_location(model, X: pd.DataFrame, feature: str) -> float:
    grid = _search_grid(X, feature)
    return _argmax(grid, model.term(feature, {feature: grid}))


def step_location(model, X: pd.DataFrame, feature: str, width: float) -> float:
    grid = _search_grid(X, feature, margin=width)
    rise = model.term(feature, {feature: grid + width}) - model.term(feature, {feature: grid})
    return _argmax(grid + width / 2, rise)


def term_effect(model, pair, feature, low, high, moderator, value) -> float:
    """Change of main(feature) + pair(feature, moderator) from low to high, moderator held at value."""
    X = {feature: np.array([low, high]), moderator: np.full(2, value)}
    total = model.term(feature, X) + (model.term(pair, X) if pair in model.term_names else 0.0)
    return float(total[1] - total[0])


def margin_effect(margin, rows, pair, feature, low, high, moderator, value) -> float:
    """Partial dependence version of term_effect, for models without a decomposition."""
    base = rows.assign(**{moderator: value})
    return float(np.mean(margin(base.assign(**{feature: high})) - margin(base.assign(**{feature: low}))))


def _pair_checks(effect: Callable, truth: dgp.Truth, interaction: str) -> list[Check]:
    if interaction == "none":
        return []  # the planted pairs are zero; the noise check covers them
    checks = []
    for claim, (pair, feature, low, high, moderator, values) in PAIR_EFFECTS.items():
        planted = tuple(term_effect(truth, pair, feature, low, high, moderator, v) for v in values)
        fitted = tuple(effect(pair, feature, low, high, moderator, v) for v in values)
        signs = all(np.sign(f) == np.sign(p) for f, p in zip(fitted, planted))
        if claim == "amplification":
            size = fitted[1] - fitted[0] >= EFFECT_FRACTION * (planted[1] - planted[0])
        else:
            size = all(abs(f) >= EFFECT_FRACTION * abs(p) for f, p in zip(fitted, planted))
        checks.append(Check(claim, pair, planted, fitted, bool(signs and size)))
    return checks


def _holdout(data: dgp.Dataset) -> tuple[pd.DataFrame, np.ndarray]:
    rng = np.random.default_rng(10_000 + data.scenario.seed)
    X = dgp.sample_features(HOLDOUT_N, rng)
    y = (rng.uniform(size=HOLDOUT_N) < expit(data.truth.logit(X))).astype(np.int64)
    return X, y


def _auc_check(margin: Callable, data: dgp.Dataset) -> Check:
    X, y = _holdout(data)
    planted, fitted = roc_auc_score(y, data.truth.logit(X)), roc_auc_score(y, margin(X))
    return Check("auc", "", planted, fitted, bool(fitted >= planted - AUC_TOLERANCE))


def check_terms(model, data: dgp.Dataset) -> list[Check]:
    """Every check, on a model with exact terms (T, the oracle, a purified EBM or XGB2)."""
    X, truth, interaction = data.X, data.truth, data.scenario.interaction
    planted, fitted = truth.shares(X), model.shares(X)
    checks = []
    for name in dict.fromkeys(dgp.TERMS + tuple(model.term_names)):
        share = fitted.get(name, 0.0)
        if planted.get(name, 0.0) > 0:
            checks.append(Check("strength", name, planted[name], share, strength(share) == strength(planted[name])))
        else:
            checks.append(Check("noise", name, 0.0, share, share < NOISE_SHARE))
    planted_ranks, fitted_ranks = _ranks(planted), _ranks(fitted)
    for f in SHAPED:
        checks.append(Check("rank", f, planted_ranks[f], fitted_ranks[f], planted_ranks[f] == fitted_ranks[f]))
    for f in SHAPED:
        ends = {f: np.quantile(X[f], NET_CHANGE)}
        p, m = np.diff(truth.term(f, ends))[0], np.diff(model.term(f, ends))[0]
        checks.append(Check("direction", f, float(p), float(m), bool(np.sign(p) == np.sign(m))))
    feature, tolerance = PEAK
    p, m = peak_location(truth, X, feature), peak_location(model, X, feature)
    checks.append(Check("peak", feature, p, m, abs(m - p) <= tolerance))
    feature, width = STEP
    p, m = step_location(truth, X, feature, width), step_location(model, X, feature, width)
    checks.append(Check("step", feature, p, m, abs(m - p) <= width))
    effect = lambda *args: term_effect(model, *args)  # noqa: E731
    checks += _pair_checks(effect, truth, interaction)
    checks.append(_auc_check(model.logit, data))
    return checks


def check_margin(margin: Callable, data: dgp.Dataset) -> list[Check]:
    """AUC and pair checks on partial dependence of a margin: XGB2's cross-check (D26)."""
    rows = data.X.sample(PD_ROWS, random_state=0)
    effect = lambda *args: margin_effect(margin, rows, *args)  # noqa: E731
    return _pair_checks(effect, data.truth, data.scenario.interaction) + [_auc_check(margin, data)]


def frame(checks: list[Check], **labels) -> pd.DataFrame:
    return pd.DataFrame([{**labels, **vars(c)} for c in checks])


def run(scenarios=SCENARIOS, **ebm_overrides) -> pd.DataFrame:
    """T, oracle, EBM and XGB2 on each scenario, plus XGB2's partial-dependence cross-check. T must pass
    everything (scorer test)."""
    parts = []
    for scenario in scenarios:
        data = dgp.generate(scenario)
        ebm = purify_ebm(fit_ebm(data.X, data.y, seed=scenario.seed, **ebm_overrides), data.X)
        xgb2 = fit_xgb2(data.X, data.y, seed=scenario.seed)
        models = (("T", data.truth), ("oracle", fit_oracle(data)), ("EBM", ebm), ("XGB2", purify_xgb2(xgb2, data.X)))
        for name, model in models:
            parts.append(frame(check_terms(model, data), scenario=scenario.id, model=name))
        margin = lambda Z: xgb2.predict(Z, output_margin=True)  # noqa: E731
        parts.append(frame(check_margin(margin, data), scenario=scenario.id, model=CROSS_CHECK))
        print(f"{scenario.id} done", flush=True)
    checks = pd.concat(parts, ignore_index=True)
    return checks.assign(miss=attribute(checks, checks[checks.model == "oracle"]))


def attribute(checks: pd.DataFrame, oracle: pd.DataFrame) -> pd.Series:
    """Label each check (D10): "" if passed, else "data" if the oracle fails the same claim on the same
    dataset, else "model". Matches on (scenario, claim, term); the oracle's own failures come out as "data".

    The oracle has no term for a model's spurious pairs. It is zero there, so it passes their noise check."""
    key = ["scenario", "claim", "term"]
    checks, oracle = (frame.assign(term=frame.term.fillna("")) for frame in (checks, oracle))  # "" reads as NaN
    oracle_passed = oracle.set_index(key).passed.reindex(pd.MultiIndex.from_frame(checks[key])).to_numpy()
    unmatched = pd.isna(oracle_passed)
    if not (checks.claim[unmatched] == "noise").all():
        raise ValueError(f"no oracle check for {checks[unmatched & (checks.claim != 'noise')][key].values.tolist()}")
    oracle_passed = np.where(unmatched, True, oracle_passed).astype(bool)
    labels = np.where(checks.passed, "", np.where(oracle_passed, "model", "data"))
    return pd.Series(labels, index=checks.index, name="miss")


def verdicts(checks: pd.DataFrame) -> pd.DataFrame:
    """Per model: checks, passed, model misses, data misses, and the acceptance verdict (no model misses).
    The partial-dependence cross-check is not a model and gets no verdict."""
    table = checks.groupby("model", sort=False).agg(
        checks=("passed", "size"),
        passed=("passed", "sum"),
        model_misses=("miss", lambda m: int((m == "model").sum())),
        data_misses=("miss", lambda m: int((m == "data").sum())),
    )
    table["accepted"] = table.model_misses == 0
    return table.loc[[m for m in MODELS if m in table.index]]


def summary(checks: pd.DataFrame) -> pd.DataFrame:
    """Passed / checked per claim and model; spurious pairs are pooled under term '(spurious pairs)'."""
    checks = checks.assign(term=checks.term.where(checks.term.isin(dgp.TERMS + ("",)), "(spurious pairs)"))
    grouped = checks.groupby(["claim", "term", "model"], sort=False).passed
    table = (grouped.sum().astype(str) + "/" + grouped.size().astype(str)).unstack("model")
    return table[[m for m in (*MODELS, CROSS_CHECK) if m in table.columns]].fillna("")


def failures(checks: pd.DataFrame) -> pd.DataFrame:
    def fmt(value):
        return tuple(round(v, 3) for v in value) if isinstance(value, tuple) else round(value, 3)

    failed = checks[~checks.passed]
    return failed.assign(planted=failed.planted.map(fmt), fitted=failed.fitted.map(fmt)).drop(columns="passed")


def main() -> None:
    checks = run()
    RESULTS.mkdir(parents=True, exist_ok=True)
    checks.to_csv(RESULTS / "checks.csv", index=False)
    pd.set_option("display.width", 200)
    print(summary(checks).to_string())
    print(failures(checks).to_string(index=False) if not checks.passed.all() else "every check passed")
    print("\nAcceptance relative to the oracle (D10): a model is accepted if it has no model misses")
    print(verdicts(checks).to_string())


if __name__ == "__main__":
    main()
