"""Fit PiML's XGB2 and export its own decomposition (plan §14.4, D27). Runs in PiML's environment.

Run: `piml_check/.venv.nosync/bin/python piml_check/fit_piml.py [scenario id]` (Python 3.10, PiML 0.6.0.post2,
xgboost 1.7.6; see README.md). Reads data/<scenario>.npz from export_data.py and writes, for each fit,
results/<scenario>/<fit>_booster.json (the fitted xgboost model) and results/<scenario>/<fit>.npz (PiML's effects per row
under both purifications, its effect importance and its margin), plus results/<scenario>/piml_meta.json.

Fits:
- defaults (a): PiML's XGB2Classifier as shipped (100 trees, learning rate 0.3, reg_lambda 0, max_bin 256,
  tree_method auto, which is exact on xgboost 1.7.6 at this size).
- ours_exact (b): our XGB2 settings inside PiML's API: the rounds our fit_xgb2 keeps on this dataset (PiML has no
  early stopping), learning rate 0.05, max_bin 256, reg_lambda 1 (xgboost's default, which our fit uses), and
  tree_method exact, because PiML's decomposition is only right for exact trees (plan §14.4).
- ours_hist (c): the same with tree_method hist, as our fit; PiML's own effects are wrong for hist trees, so this
  fit is judged only through our decomposition.

Interpreters:
- uniform: model.parse_model(), what PiML users get; pairs purified with uniform weights over the grid cells.
- data: XGBInterpreter(true_to_data=True); pairs purified with the data's weights, as our code does.
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

warnings.filterwarnings("ignore")
HERE = Path(__file__).parent


def steps_on_rows(effect: dict, X: np.ndarray) -> np.ndarray:
    """Evaluate one PiML effect (1D or 2D step function) on the rows of X, with XGBoost's split rule:
    float32(x) < split goes to the lower cell. split_unique_list carries -inf and +inf at both ends."""
    cells = []
    for f, splits in zip(effect["fidx"], effect["split_unique_list"]):
        inner = np.asarray(splits, dtype=np.float64)[1:-1]
        cells.append(np.searchsorted(inner, X[:, f].astype(np.float32).astype(np.float64), side="right"))
    return np.asarray(effect["values"], dtype=np.float64)[tuple(cells)]


def effects_on_rows(effects: dict, intercept: float, X: np.ndarray, names: list) -> dict:
    mains = np.zeros((len(X), len(names)))
    for effect in effects["1D"].values():
        (f,) = effect["fidx"]
        mains[:, f] += steps_on_rows(effect, X)
    pair_names, pairs = [], []
    for effect in effects["2D"].values():
        a, b = effect["fidx"]
        pair_names.append(f"{names[a]} & {names[b]}")
        pairs.append(steps_on_rows(effect, X))
    pairs = np.column_stack(pairs) if pairs else np.zeros((len(X), 0))
    return {"intercept": float(intercept), "mains": mains, "pair_names": np.array(pair_names), "pairs": pairs}


def variance_shares(mains: np.ndarray, pairs: np.ndarray) -> np.ndarray:
    v = np.concatenate([mains.var(axis=0), pairs.var(axis=0)])
    return v / v.sum()


def main() -> None:
    scenario = sys.argv[1] if len(sys.argv) > 1 else "syn-none-n50000-s1"
    data = np.load(HERE / "data" / f"{scenario}.npz")
    X, y, names = data["X"], data["y"], [str(n) for n in data["features"]]
    seed, rounds = int(data["seed"]), int(data["our_rounds"])
    out = HERE / "results" / scenario
    out.mkdir(parents=True, exist_ok=True)
    fits = {
        "defaults": dict(random_state=0),
        "ours_exact": dict(n_estimators=rounds, eta=0.05, max_bin=256, tree_method="exact", reg_lambda=1.0, random_state=seed),
        "ours_hist": dict(n_estimators=rounds, eta=0.05, max_bin=256, tree_method="hist", reg_lambda=1.0, random_state=seed),
    }
    meta = {"scenario": scenario, "piml": piml.__version__, "xgboost": xgboost.__version__, "python": sys.version.split()[0], "fits": {}}
    for fit_name, params in fits.items():
        model = XGB2Classifier(feature_names=names, **params).fit(X, y)
        model.estimator_.save_model(out / f"{fit_name}_booster.json")
        margin = model.decision_function(X)
        arrays = {"margin": margin}
        uniform = model.parse_model()
        data_weighted = XGBInterpreter(model.estimator_, feature_names=names, feature_types=["numerical"] * len(names), true_to_data=True)
        data_weighted.fit(X)
        for label, interp in (("uniform", uniform), ("data", data_weighted)):
            rows = effects_on_rows(interp.effects_, interp.intercept_, X, names)
            gap = rows["intercept"] + rows["mains"].sum(axis=1) + rows["pairs"].sum(axis=1) - margin
            arrays |= {f"{label}_{k}": v for k, v in rows.items()}
            arrays[f"{label}_variance_share"] = variance_shares(rows["mains"], rows["pairs"])
            meta["fits"].setdefault(fit_name, {})[f"{label}_margin_gap"] = float(np.abs(gap).max())
        # our evaluator of PiML's effects against PiML's own raw-output functions (default interpreter), term by term
        own_pairs = uniform.get_interaction_raw_output(X)
        own_names = [f"{names[a]} & {names[b]}" for a, b in uniform.interaction_list_]
        mine = dict(zip(arrays["uniform_pair_names"], arrays["uniform_pairs"].T))
        evaluator_gap = max(
            np.abs(uniform.get_main_effect_raw_output(X) - arrays["uniform_mains"]).max(),
            max((np.abs(own_pairs[:, k] - mine[n]).max() for k, n in enumerate(own_names)), default=0.0),
        )
        ei = uniform.update_effect_importance(X) or uniform.get_ei().value
        arrays["uniform_piml_importance_names"] = np.array([str(n).replace(" x ", " & ") for n in ei["effect_names"]])
        arrays["uniform_piml_importance"] = np.asarray(ei["importance"], dtype=np.float64)
        np.savez(out / f"{fit_name}.npz", **arrays)
        meta["fits"][fit_name] |= {
            "params": model.xgb_params_,
            "trees": int(model.estimator_.get_booster().num_boosted_rounds()),
            "evaluator_vs_piml_raw_output": float(evaluator_gap),
        }
        print(f"{fit_name}: {meta['fits'][fit_name]['trees']} trees, margin gap uniform {meta['fits'][fit_name]['uniform_margin_gap']:.1e}, "
              f"data {meta['fits'][fit_name]['data_margin_gap']:.1e}, evaluator vs PiML {meta['fits'][fit_name]['evaluator_vs_piml_raw_output']}")
    (out / "piml_meta.json").write_text(json.dumps(meta, indent=1, default=str))


if __name__ == "__main__":
    main()
