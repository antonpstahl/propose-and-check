"""Which rows PiML's XGB2 decomposition gets wrong for hist and approx trees. Exploratory, formed after the toy
check's result (toy_hist.py: not reproduced as written, because rows away from the split values are right).

Two toys, n = 2,000: the continuous one of toy_hist.py, and the same with x3 replaced by a count (Poisson(1.5),
clipped at 6), the kind of feature credit data are full of. For each tree_method: the share of training rows
whose margin, rebuilt from parse_model() with PiML's raw-output functions, is off by more than 0.05 logits,
the median and largest gap, and the share of the off rows whose value sits exactly on a split value (float32)
of its feature.

Run: `piml_check/.venv.nosync/bin/python piml_check/toy_hist_followup.py [label]` (seconds). Writes
results/toy_hist/followup_<label>.json.
"""

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import xgboost
from piml.models import XGB2Classifier

sys.path.insert(0, str(Path(__file__).parent))
from toy_hist import NAMES, rebuilt, toy  # noqa: E402

warnings.filterwarnings("ignore")
HERE = Path(__file__).parent
OFF = 0.05


def count_toy(n: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    X, _ = toy(n, seed)
    rng = np.random.default_rng(seed + 10)
    X[:, 2] = np.minimum(rng.poisson(1.5, n), 6)
    return X, rng.binomial(1, 1 / (1 + np.exp(-(2 * X[:, 0] - 1.5 * X[:, 1] + 0.4 * X[:, 2]))))


def on_a_split(model, X: np.ndarray) -> np.ndarray:
    trees = model.estimator_.get_booster().trees_to_dataframe()
    on = np.zeros(len(X), dtype=bool)
    for j, name in enumerate(NAMES):
        splits = trees.loc[trees.Feature.isin([name, f"f{j}"]), "Split"].dropna().to_numpy(dtype=float)
        on |= np.isin(X[:, j].astype(np.float32), splits.astype(np.float32))
    return on


def main() -> None:
    label = sys.argv[1] if len(sys.argv) > 1 else f"xgboost-{xgboost.__version__}"
    out = {"label": label, "xgboost": xgboost.__version__, "rows": {}}
    for toy_name, (X, y) in (("continuous", toy(2_000, 0)), ("one count feature", count_toy(2_000, 0))):
        for method in ("exact", "hist", "approx"):
            model = XGB2Classifier(feature_names=NAMES, random_state=0, tree_method=method).fit(X, y)
            gap = np.abs(rebuilt(model.parse_model(), X) - model.decision_function(X))
            off, on = gap > OFF, on_a_split(model, X)
            row = {"rows off": float(off.mean()), "median gap": float(np.median(gap)), "largest gap": float(gap.max()),
                   "rows on a split value": float(on.mean()), "off rows on a split value": float(on[off].mean()) if off.any() else None}  # fmt: skip
            out["rows"][f"{toy_name}, {method}"] = row
            print(f"{label:>14} {toy_name:>17} {method:>6}: rows off by > {OFF}: {row['rows off']:6.1%}, median {row['median gap']:.1e}, "
                  f"largest {row['largest gap']:.2f}; rows on a split value {row['rows on a split value']:.1%}"
                  + (f", of the off rows {row['off rows on a split value']:.0%}" if off.any() else ""))  # fmt: skip
    path = HERE / "results" / "toy_hist" / f"followup_{label}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
