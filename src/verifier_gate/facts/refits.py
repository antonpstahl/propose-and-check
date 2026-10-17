"""The bootstrap refits themselves, kept as step models, for quantities the stored draws do not cover (D49).

The global draws (facts/build.py) keep each refit read through M's frame: curves on M's steps, scalars, and
conditional effects at four points. The local spot check needs each refit's terms at single rows, pairs
included, so the refits are fitted once more, exactly as facts/bootstrap.py fits them (same Poisson weights,
same model seeds), and kept whole: the intercept and every purified, centred term. Each refit is read through
M's frame and must reproduce the stored draws, so the local bands come from the same 100 refits as the global
facts.

File: cache/facts/<scenario>/<kind>_refits.npz, one entry per array: "<refit>/intercept", and per term
"<refit>/<term index>/features", "/scores", "/cuts<axis>".
"""

import time
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd

from verifier_gate.facts import bootstrap
from verifier_gate.facts.build import Frame
from verifier_gate.facts.schema import Draws
from verifier_gate.facts.steps import StepModel, StepTerm

TOLERANCE = 1e-9  # largest difference to the stored draws that counts as the same refit


def save_models(models: list[StepModel], path: Path) -> None:
    arrays = {}
    for b, model in enumerate(models):
        arrays[f"{b}/intercept"] = np.array(model.intercept)
        for i, term in enumerate(model.steps.values()):
            arrays[f"{b}/{i}/features"] = np.array(term.features)
            arrays[f"{b}/{i}/scores"] = term.scores
            for axis, cuts in enumerate(term.cuts):
                arrays[f"{b}/{i}/cuts{axis}"] = cuts
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **arrays)


def load_models(path: Path) -> list[StepModel]:
    with np.load(path) as stored:
        keys = stored.files
        refits = 1 + max(int(k.split("/")[0]) for k in keys)
        models = []
        for b in range(refits):
            n_terms = 1 + max((int(k.split("/")[1]) for k in keys if k.startswith(f"{b}/") and k.count("/") == 2), default=-1)
            steps = {}
            for i in range(n_terms):
                features = tuple(str(f) for f in stored[f"{b}/{i}/features"])
                cuts = tuple(stored[f"{b}/{i}/cuts{axis}"] for axis in range(len(features)))
                term = StepTerm(features, cuts, stored[f"{b}/{i}/scores"])
                steps[term.name] = term
            models.append(StepModel(float(stored[f"{b}/intercept"]), steps))
    return models


def deviation(read: dict, stored: Draws, refit: int) -> float:
    """Largest absolute difference between a refit read through M's frame and its stored draws."""
    worst = 0.0
    for kind in Draws.KINDS:
        for key, value in read[kind].items():
            worst = max(worst, float(np.max(np.abs(np.asarray(value) - getattr(stored, kind)[key][refit]))))
    return worst


def refit_models(
    kind: str, X: pd.DataFrame, y: np.ndarray, seed: int, frame: Frame, stored: Draws, log: Callable | None = None
) -> list[StepModel]:
    """The stored refits of M, fitted again and checked against their draws; raises if one differs."""
    models = []
    start = time.perf_counter()
    for b in range(stored.refits):
        w = bootstrap.poisson_weights(len(y), seed, b)
        model = bootstrap.fit_steps(kind, X, y, seed=b, w=w)
        off = deviation(frame.read(model, X, w), stored, b)
        if off > TOLERANCE:
            raise RuntimeError(f"{kind} refit {b} differs from its stored draws by {off:.3g}")
        models.append(model)
        if log and (b + 1) % 10 == 0:
            log(f"  {kind} refit {b + 1}/{stored.refits}, {(time.perf_counter() - start) / (b + 1):.1f}s per refit, max deviation {off:.1g}")
    return models
