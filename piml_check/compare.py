"""Compare PiML's XGB2 decomposition with ours, and check the invented pair (plan §14.4, D27).

Runs in the project environment after fit_piml.py: `uv run python piml_check/compare.py [scenario id]`.
Loads each booster PiML fitted, decomposes it with our code (facts/xgb2.py), and applies the criteria fixed in the
plan before the run:

- Question 1 (fits defaults and ours_exact): our terms reproduce the booster's own leaves to 1e-9; our data-weighted
  purification vs PiML's true_to_data=True, each term centred on the data: largest difference <= 0.01 logits for
  every term (pairs: those with share >= 0.5% on our measure), and correlation >= 0.999 (main effects) or >= 0.99
  (pairs) for terms with sd >= 0.01 logits. The sd condition was added before the run, on the exploration data:
  for flatter terms PiML's purification tolerance (1e-3) dominates the correlation. Secondary, reported only: ours re-purified with uniform cell weights vs PiML's default.
- Question 2: "PiML shows the pair" = utilization & n_delinquencies has share >= 1% on our measure (mean |score|
  of the data-purified term over the total) and is among the top 3 pairs on PiML's default importance.

Writes results/<scenario>/comparison.json and prints a summary.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from interpret.utils import purify as interpret_purify
from scipy.special import logit
from xgboost import DMatrix, XGBClassifier

from verifier_gate.facts.steps import StepModel, StepTerm, add
from verifier_gate.facts.xgb2 import purify_xgb2, raw_steps
from verifier_gate.models.fit_xgb2 import fit_xgb2

HERE = Path(__file__).parent
PAIR = "utilization & n_delinquencies"
FITS = ("defaults", "ours_exact", "ours_hist")
COMPARED = ("defaults", "ours_exact")  # PiML's own decomposition is wrong for hist trees
MAIN_CORR, PAIR_CORR, MAX_DIFF, PAIR_MIN_SHARE = 0.999, 0.99, 0.01, 0.005
MIN_SD = 0.01  # correlation only for terms with at least this sd (logits); flatter terms sit at PiML's tolerance
SHOWN_SHARE, SHOWN_RANK = 0.01, 3


def load_booster(path: Path, names: list) -> XGBClassifier:
    model = XGBClassifier()
    model.load_model(path)
    model.get_booster().feature_names = names
    return model


def leaf_sum(model: XGBClassifier, X: pd.DataFrame) -> np.ndarray:
    """The margin as the float64 sum of the leaves XGBoost itself reaches, plus logit(base_score)."""
    learner = json.loads(model.get_booster().save_raw(raw_format="json"))["learner"]
    trees = learner["gradient_booster"]["model"]["trees"]
    leaves = model.get_booster().predict(DMatrix(X), pred_leaf=True).astype(int)
    values = np.column_stack([np.asarray(t["split_conditions"], dtype=np.float64)[leaves[:, j]] for j, t in enumerate(trees)])
    return logit(float(json.loads(learner["learner_model_param"]["base_score"])[0])) + values.sum(axis=1)


def uniform_purified(raw: StepModel, X: pd.DataFrame) -> StepModel:
    """Our raw terms purified the way PiML's default does: uniform weights over the grid cells; mains centred on X."""
    mains = {n: t for n, t in raw.steps.items() if len(t.features) == 1}
    pairs = {}
    for name in raw.pairs:
        term = raw.steps[name]
        pure, parts, _ = interpret_purify(term.scores, np.ones_like(term.scores), is_randomized=False)
        pairs[name] = StepTerm(term.features, term.cuts, pure)
        for (dim,), part in parts:
            f = term.features[dim]
            impurity = StepTerm((f,), (term.cuts[dim],), np.asarray(part, dtype=np.float64))
            mains[f] = add(mains[f], impurity) if f in mains else impurity
    return StepModel(0.0, {n: t.shifted(float(t(X).mean())) for n, t in mains.items()} | pairs)


def agreement(ours: dict, theirs: dict, shares: dict, min_share: float = 0.0) -> pd.DataFrame:
    """Per term, both centred on the data: correlation and largest difference."""
    rows = []
    for name in sorted(set(ours) | set(theirs)):
        if " & " in name and shares.get(name, 0.0) < min_share:
            continue
        a = ours.get(name, np.zeros(len(next(iter(ours.values())))))
        b = theirs.get(name, np.zeros_like(a))
        a, b = a - a.mean(), b - b.mean()
        corr = float(np.corrcoef(a, b)[0, 1]) if a.std() > 0 and b.std() > 0 else float(np.allclose(a, b))
        rows.append({"term": name, "pair": " & " in name, "in ours": name in ours, "in PiML": name in theirs,
                     "share (ours)": shares.get(name, 0.0), "sd (ours)": float(a.std()), "corr": corr,
                     "max diff": float(np.abs(a - b).max())})  # fmt: skip
    table = pd.DataFrame(rows)
    threshold = np.where(table["pair"], PAIR_CORR, MAIN_CORR)
    table["passes"] = (table["max diff"] <= MAX_DIFF) & ((table["sd (ours)"] < MIN_SD) | (table["corr"] >= threshold))
    return table


def piml_terms(arrays, prefix: str, names: list) -> dict:
    terms = {f: arrays[f"{prefix}_mains"][:, j] for j, f in enumerate(names)}
    return terms | dict(zip([str(n) for n in arrays[f"{prefix}_pair_names"]], arrays[f"{prefix}_pairs"].T))


def pair_rank(names: np.ndarray, importance: np.ndarray, pair: str) -> int | None:
    pairs = [(float(v), str(n)) for n, v in zip(names, importance) if " & " in str(n)]
    order = [n for _, n in sorted(pairs, reverse=True)]
    return order.index(pair) + 1 if pair in order else None


def main() -> None:
    scenario = sys.argv[1] if len(sys.argv) > 1 else "syn-none-n50000-s1"
    data = np.load(HERE / "data" / f"{scenario}.npz")
    names = [str(n) for n in data["features"]]
    X = pd.DataFrame(data["X"], columns=names)
    out = HERE / "results" / scenario
    meta = json.loads((out / "piml_meta.json").read_text())
    report = {"scenario": scenario, "piml_environment": {k: meta[k] for k in ("piml", "xgboost", "python")}, "fits": {}}
    pd.set_option("display.width", 200)

    reference = purify_xgb2(fit_xgb2(X, data["y"], seed=int(data["seed"])), X)
    report["our_fit_xgb2_pair_share"] = reference.shares(X).get(PAIR, 0.0)

    for fit in FITS:
        model = load_booster(out / f"{fit}_booster.json", names)
        arrays = np.load(out / f"{fit}.npz")
        raw = raw_steps(model)
        exact = leaf_sum(model, X)
        ours = purify_xgb2(model, X)
        shares = ours.shares(X)
        entry = {
            "trees": meta["fits"][fit]["trees"],
            "ours vs own leaves (max)": float(np.abs(raw.logit(X) - exact).max()),
            "ours vs PiML's margin (max, float32)": float(np.abs(ours.logit(X) - arrays["margin"]).max()),
            "PiML's own effects vs its margin (max)": meta["fits"][fit]["uniform_margin_gap"],
            "pairs (ours)": len(ours.pairs),
            "pair share (ours)": shares.get(PAIR, 0.0),
            "pair rank among pairs (ours)": pair_rank(np.array(list(shares)), np.array(list(shares.values())), PAIR),
        }
        if fit in COMPARED:
            primary = agreement(ours.terms(X), piml_terms(arrays, "data", names), shares, PAIR_MIN_SHARE)
            secondary = agreement(uniform_purified(raw, X).terms(X), piml_terms(arrays, "uniform", names), shares, PAIR_MIN_SHARE)
            entry |= {
                "Q1 leaves to 1e-9": entry["ours vs own leaves (max)"] <= 1e-9,
                "Q1 primary passes": bool(primary.passes.all()),
                "Q1 primary worst": primary.sort_values("corr").head(3)[["term", "sd (ours)", "corr", "max diff"]].round(6).to_dict("records"),
                "Q1 primary largest difference": float(primary["max diff"].max()),
                "Q1 secondary (uniform) passes": bool(secondary.passes.all()),
                "Q1 secondary worst": secondary.sort_values("corr").head(3)[["term", "corr", "max diff"]].round(6).to_dict("records"),
                "pair rank, PiML default importance": pair_rank(arrays["uniform_piml_importance_names"], arrays["uniform_piml_importance"], PAIR),
                "pair variance share, PiML default": float(dict(zip(arrays["uniform_piml_importance_names"], arrays["uniform_piml_importance"])).get(PAIR, 0.0)),
                "pairs, PiML default": int(sum(" & " in str(n) for n in arrays["uniform_piml_importance_names"])),
            }
            entry["Q2 PiML shows the pair"] = bool(
                entry["pair share (ours)"] >= SHOWN_SHARE and (entry["pair rank, PiML default importance"] or 99) <= SHOWN_RANK
            )
            primary.to_csv(out / f"{fit}_agreement_data_weighted.csv", index=False)
            secondary.to_csv(out / f"{fit}_agreement_uniform.csv", index=False)
        report["fits"][fit] = entry
    (out / "comparison.json").write_text(json.dumps(report, indent=1, default=str))
    print(json.dumps(report, indent=1, default=str))


if __name__ == "__main__":
    main()
