"""Facts from a fitted EBM. So far: purified terms. Bins, bootstrap bands and the Facts interface follow.

interpret only centres each pair term, so a fitted pair carries main-effect parts (28% of mean |score| for
the planted pairs in week 1). purify_ebm moves them into the main terms with interpret.utils.purify, the
code path the XGB2 provider will use too, and centres every term on the training sample, as T is centred.
After that, shares and shapes can be compared with T term by term.
"""

import copy
from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
import pandas as pd
from interpret.glassbox import ExplainableBoostingClassifier
from interpret.utils import purify


@dataclass(frozen=True)
class Impurity:
    """Main-effect part of a pair: added to the main term of `feature`, indexed by the pair's bins on `dim`."""

    feature: str
    dim: int
    scores: np.ndarray


@dataclass(frozen=True)
class PurifiedEBM:
    """Purified EBM terms, each centred on the training sample.

    logit(x) = intercept + sum of term(name, x) over term_names equals model.decision_function(x) on any x.
    Same methods as dgp.Truth, so checks can run on T and on the model alike.
    """

    model: ExplainableBoostingClassifier
    intercept: float
    offsets: Mapping[str, float]
    pure_pairs: Mapping[int, np.ndarray]  # term index -> purified score tensor
    impurities: Mapping[int, tuple[Impurity, ...]]  # term index -> parts moved into the main terms
    probe: ExplainableBoostingClassifier  # copy whose pair tensors hold cell codes, see _pair_cells

    @property
    def term_names(self) -> tuple[str, ...]:
        return tuple(self.model.term_names_)

    def terms(self, X: Mapping) -> dict[str, np.ndarray]:
        X = self._frame(X)
        local = self.model.eval_terms(X)
        terms = {name: local[:, i].copy() for i, name in enumerate(self.term_names)}
        for idx, cells in self._pair_cells(X).items():
            terms[self.term_names[idx]] = self.pure_pairs[idx][cells]
            for part in self.impurities[idx]:
                terms[part.feature] += part.scores[cells[part.dim]]
        return {name: values - self.offsets[name] for name, values in terms.items()}

    def term(self, name: str, X: Mapping) -> np.ndarray:
        return self.terms(X)[name]

    def logit(self, X: Mapping) -> np.ndarray:
        return self.intercept + sum(self.terms(X).values())

    def importances(self, X: Mapping) -> dict[str, float]:
        """Mean |score| per term over the rows of X."""
        return {name: float(np.abs(values).mean()) for name, values in self.terms(X).items()}

    def shares(self, X: Mapping) -> dict[str, float]:
        importances = self.importances(X)
        total = sum(importances.values())
        return {name: value / total for name, value in importances.items()}

    def _frame(self, X: Mapping) -> pd.DataFrame:
        """X as a frame with every model feature. Features not in X are set to 0; only terms that use them
        are affected, so evaluate a term only on an X that holds all of its features."""
        n = len(next(iter(X.values()))) if isinstance(X, Mapping) else len(X)
        return pd.DataFrame(
            {f: np.asarray(X[f], dtype=np.float64) if f in X else np.zeros(n) for f in self.model.feature_names_in_}
        )

    def _pair_cells(self, X: pd.DataFrame) -> dict[int, tuple[np.ndarray, ...]]:
        """Per pair term, each row's cell in the pair's score tensor (one eval_terms pass on the probe)."""
        codes = self.probe.eval_terms(X)
        return {
            idx: np.unravel_index(codes[:, idx].astype(np.int64), pure.shape) for idx, pure in self.pure_pairs.items()
        }


def purify_ebm(model: ExplainableBoostingClassifier, X: pd.DataFrame) -> PurifiedEBM:
    """Purify every pair of a fitted binary EBM and centre all terms on X (the training sample)."""
    intercept = float(model.intercept_[0])
    pure_pairs, impurities = {}, {}
    probe = copy.deepcopy(model)
    for idx, features in enumerate(model.term_features_):
        if len(features) != 2:
            continue
        scores = model.term_scores_[idx]
        # is_randomized=False: a fixed processing order, so the facts are reproducible
        pure, parts, pure_intercept = purify(scores, model.bin_weights_[idx], is_randomized=False)
        pure_pairs[idx] = pure
        impurities[idx] = tuple(
            Impurity(model.feature_names_in_[features[dim]], dim, part) for (dim,), part in parts
        )
        intercept += float(pure_intercept[0])
        probe.term_scores_[idx] = np.arange(scores.size, dtype=np.float64).reshape(scores.shape)
    uncentred = PurifiedEBM(model, intercept, dict.fromkeys(model.term_names_, 0.0), pure_pairs, impurities, probe)
    offsets = {name: float(values.mean()) for name, values in uncentred.terms(X).items()}
    return PurifiedEBM(model, intercept + sum(offsets.values()), offsets, pure_pairs, impurities, probe)
