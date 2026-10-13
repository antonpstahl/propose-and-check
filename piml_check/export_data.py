"""Export one synthetic dataset so the PiML environment reads exactly the same X and y (plan §14.4, D27).

Runs in the project environment (Python 3.13): `uv run python piml_check/export_data.py [scenario id]`.
Writes piml_check/data/<scenario>.npz with X (float64, column order of dgp.FEATURES), y, the feature names, the
scenario seed, and the number of boosting rounds our fit_xgb2 keeps on this dataset after early stopping (PiML has
no early stopping, so fit (b) in fit_piml.py uses this number).
"""

import sys
from pathlib import Path

import numpy as np

from verifier_gate.data import dgp
from verifier_gate.models.fit_xgb2 import fit_xgb2

DATA = Path(__file__).parent / "data"


def main() -> None:
    scenario_id = sys.argv[1] if len(sys.argv) > 1 else "syn-none-n50000-s1"
    scenario = next(s for s in dgp.SCENARIOS if s.id == scenario_id)
    data = dgp.generate(scenario)
    DATA.mkdir(exist_ok=True)
    path = DATA / f"{scenario.id}.npz"
    rounds = fit_xgb2(data.X, data.y, seed=scenario.seed).best_iteration + 1
    X = data.X[list(dgp.FEATURES)].to_numpy(np.float64)
    np.savez(path, X=X, y=data.y, features=np.array(dgp.FEATURES), seed=scenario.seed, our_rounds=rounds)
    print(f"{path}: {len(data.y)} rows, default rate {data.y.mean():.3f}, our XGB2 keeps {rounds} rounds")


if __name__ == "__main__":
    main()
