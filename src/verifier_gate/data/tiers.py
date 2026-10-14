"""The tiers with a planted truth behind one interface: synthetic (data/dgp.py) and plasmode (data/plasmode.py).

A tier module exposes FEATURES, TERMS, FEATURE_ROLES, PAIR_PATTERNS, AMPLIFICATION, SIGN_FLIP, SCENARIOS,
term_features(name), unit_term(name, X) and generate(scenario). `module` finds the tier of a scenario (by its id),
of a sample (by its columns) or of a tier name.
"""

from collections.abc import Mapping
from types import ModuleType

import pandas as pd

from verifier_gate.data import dgp, plasmode

TIERS = {"synthetic": dgp, "plasmode": plasmode}
PREFIX = {"syn": dgp, "pls": plasmode}
SCENARIOS = dgp.SCENARIOS + plasmode.SCENARIOS


def module(of) -> ModuleType:
    if isinstance(of, str):
        return TIERS.get(of) or PREFIX[of.split("-")[0]]
    if hasattr(of, "id"):
        return PREFIX[of.id.split("-")[0]]
    columns = set(of.columns if isinstance(of, pd.DataFrame) else of)
    for tier in TIERS.values():
        if columns >= set(tier.FEATURES):
            return tier
    raise ValueError(f"no tier has the features {sorted(columns)}")


def name(of) -> str:
    return next(k for k, v in TIERS.items() if v is module(of))


def generate(scenario):
    return module(scenario).generate(scenario)


def scenario(scenario_id: str):
    return next(s for s in SCENARIOS if s.id == scenario_id)


def reference_sample(tier: ModuleType, n: int = 1_000) -> Mapping:
    """A sample of the tier's population, to tell zero shapes from the others."""
    return dgp._reference().iloc[:n] if tier is dgp else plasmode.taiwan().iloc[:n]
