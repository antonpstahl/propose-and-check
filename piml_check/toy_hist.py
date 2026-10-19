"""Toy check of PiML's XGB2 decomposition for hist and approx trees (plan §14.4 side finding, D28). PiML's env.

Before the hist/approx finding is reported, it is reproduced on a toy dataset outside our benchmark, with PiML's
own API only for the outcome (no code of ours evaluates PiML's effects there).

Toy data: 3 features uniform on [0, 1], n = 2,000 (seed 0), logit 2 x1 - 1.5 x2 + 4 (x1 - 0.5)(x3 - 0.5), y drawn
from it. For tree_method exact, hist and approx, and PiML's defaults: fit PiML's XGB2Classifier, then rebuild the
margin from PiML's decomposition as users get it, parse_model(): intercept + main effects + interactions, with
PiML's own raw-output functions. Compare it with decision_function on the training rows, on the training rows
that lie away from every split value (at least 1e-4 from each threshold of their feature), and on 2,000 fresh
rows. Purification only moves effect between terms, so the gap does not depend on it.

Secondary, not part of the outcome: PiML's XGBInterpreter has an undocumented option split_calibration (default
False). Its effects are read with fit_piml.py's evaluator (checked against PiML's raw outputs on 13 Oct and again
here, on parse_model()'s effects), with split_calibration off and on: does the option repair hist and approx?

Outcome rule, fixed before the run (14 Oct): the defect is confirmed if the exact fit's largest gap is at most
1e-4 logits and the hist or the approx fit's largest gap on rows away from the splits is at least 0.05 logits.
Otherwise it is not reproduced on the toy data, and the finding is not reported as written.

Run: `piml_check/.venv.nosync/bin/python piml_check/toy_hist.py [label]` (seconds). The label (default: the
xgboost version) names the output, results/toy_hist/<label>.json, so the same script can run in environments
with other xgboost versions.
"""

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import piml
import xgboost
from piml.models import XGB2Classifier
from piml.models.xgb2.interpret import XGBInterpreter

sys.path.insert(0, str(Path(__file__).parent))
from fit_piml import effects_on_rows  # noqa: E402

warnings.filterwarnings("ignore")
HERE = Path(__file__).parent
NAMES = ["x1", "x2", "x3"]
EXACT_LIMIT, DEFECT_SIZE, AWAY = 1e-4, 0.05, 1e-4


def toy(n: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    X = rng.uniform(size=(n, 3))
    logit = 2 * X[:, 0] - 1.5 * X[:, 1] + 4 * (X[:, 0] - 0.5) * (X[:, 2] - 0.5)
    return X, rng.binomial(1, 1 / (1 + np.exp(-logit)))


def rebuilt(interpreter, X: np.ndarray) -> np.ndarray:
    """The margin from parse_model()'s decomposition, with PiML's raw-output functions."""
    pairs = interpreter.get_interaction_raw_output(X)
    pairs = pairs.sum(axis=1) if np.ndim(pairs) == 2 and pairs.shape[1] else 0.0
    return interpreter.intercept_ + interpreter.get_main_effect_raw_output(X).sum(axis=1) + pairs


def evaluated(effects: dict, intercept: float, X: np.ndarray) -> np.ndarray:
    """The margin from an interpreter's effects, read with fit_piml.py's evaluator."""
    rows = effects_on_rows(effects, intercept, X, NAMES)
    return rows["intercept"] + rows["mains"].sum(axis=1) + rows["pairs"].sum(axis=1)


def away_from_splits(model, X: np.ndarray) -> np.ndarray:
    trees = model.estimator_.get_booster().trees_to_dataframe()
    keep = np.ones(len(X), dtype=bool)
    for j, name in enumerate(NAMES):
        splits = trees.loc[trees.Feature.isin([name, f"f{j}"]), "Split"].dropna().to_numpy(dtype=float)
        if len(splits):
            keep &= np.abs(X[:, [j]] - splits[None, :]).min(axis=1) >= AWAY
    return keep


def main() -> None:
    label = sys.argv[1] if len(sys.argv) > 1 else f"xgboost-{xgboost.__version__}"
    X, y = toy(2_000, 0)
    fresh, _ = toy(2_000, 1)
    fits = {"defaults": {}, "exact": {"tree_method": "exact"}, "hist": {"tree_method": "hist"}, "approx": {"tree_method": "approx"}}
    out = {"label": label, "piml": piml.__version__, "xgboost": xgboost.__version__, "python": sys.version.split()[0], "fits": {}}
    for name, params in fits.items():
        model = XGB2Classifier(feature_names=NAMES, random_state=0, **params).fit(X, y)
        away = away_from_splits(model, X)
        margin, margin_fresh = model.decision_function(X), model.decision_function(fresh)
        parsed = model.parse_model()
        gap, gap_fresh = np.abs(rebuilt(parsed, X) - margin), np.abs(rebuilt(parsed, fresh) - margin_fresh)
        row = {
            "tree_method": model.estimator_.get_xgb_params().get("tree_method"), "rows away from splits": int(away.sum()),
            "train": float(gap.max()), "away from splits": float(gap[away].max()), "fresh": float(gap_fresh.max()),
            "mean train": float(gap.mean()),
            "evaluator vs PiML raw output": float(np.abs(evaluated(parsed.effects_, parsed.intercept_, X) - rebuilt(parsed, X)).max()),
        }  # fmt: skip
        for calibration in (False, True):
            interp = XGBInterpreter(model.estimator_, feature_names=NAMES, feature_types=["numerical"] * 3, split_calibration=calibration)
            interp.fit(X)
            row[f"split_calibration={calibration}, train"] = float(np.abs(evaluated(interp.effects_, interp.intercept_, X) - margin).max())
        out["fits"][name] = row
        print(f"{label:>16} {name:>8} ({row['tree_method']}): largest gap train {row['train']:.2e}, away from splits "
              f"{row['away from splits']:.2e} ({row['rows away from splits']} rows), fresh {row['fresh']:.2e}; "
              f"split_calibration off/on {row['split_calibration=False, train']:.2e} / {row['split_calibration=True, train']:.2e}; "
              f"evaluator check {row['evaluator vs PiML raw output']:.1e}")  # fmt: skip

    exact_ok = out["fits"]["exact"]["train"] <= EXACT_LIMIT
    defect = max(out["fits"][m]["away from splits"] for m in ("hist", "approx")) >= DEFECT_SIZE
    out["outcome"] = "confirmed" if exact_ok and defect else "not reproduced"
    print(f"Outcome (rule fixed before the run): {out['outcome']} (exact within {EXACT_LIMIT}: {exact_ok}; "
          f"hist or approx off by >= {DEFECT_SIZE} away from splits: {defect})")  # fmt: skip
    path = HERE / "results" / "toy_hist" / f"{label}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
