"""Facts from a fitted EBM: its terms as exact step terms, purified and centred (facts/steps.py).

interpret only centres each pair term, so a fitted pair carries main-effect parts (28% of mean |score| for
the planted pairs in week 1). purify_ebm moves them into the main terms with the same code path as the XGB2
provider (steps.purify, which calls interpret.utils.purify) and centres every term on the training sample, as
T is centred. After that, shares and shapes can be compared with T term by term.
"""

from collections.abc import Mapping

import numpy as np
from interpret.glassbox import ExplainableBoostingClassifier

from verifier_gate.facts.steps import StepModel, StepTerm, purify


def raw_steps(model: ExplainableBoostingClassifier) -> StepModel:
    """The EBM's own terms as step terms, unpurified. interpret's tensors have a missing bin first and an
    unknown bin last; neither can be reached by complete numeric rows, so both are dropped."""
    steps = {}
    for idx, features in enumerate(model.term_features_):
        cuts = []
        for f in features:
            levels = model.bins_[f]  # cut sets by resolution: mains use the first, pairs the second if any
            level = levels[min(len(features), len(levels)) - 1]
            if not isinstance(level, np.ndarray):
                raise TypeError(f"{model.feature_names_in_[f]} is categorical; only numeric features are supported")
            cuts.append(np.asarray(level, dtype=np.float64))
        scores = np.asarray(model.term_scores_[idx], dtype=np.float64)[(slice(1, -1),) * len(features)]
        names = tuple(model.feature_names_in_[f] for f in features)
        steps[model.term_names_[idx]] = StepTerm(names, tuple(cuts), scores)
    return StepModel(float(np.ravel(model.intercept_)[0]), steps)


def purify_ebm(model: ExplainableBoostingClassifier, X: Mapping, w: np.ndarray | None = None) -> StepModel:
    """Purified, centred terms of a fitted binary EBM. X is the training sample, w the refit weights if any.

    logit(x) = intercept + sum of term(name, x) over term_names equals model.decision_function(x) on any x."""
    return purify(raw_steps(model), X, w, feature_order=tuple(model.feature_names_in_))
