"""The symbolic handover (§5.4): what the writer reads about one fitted model.

H1, the facts: the model and its scale; per feature, in the order of M's shares, its name in the DSL and a short
description, its share of importance and its rank with their 95% bands (numbers from M), and its readable curve
(facts/readable.py, checked against M before use); per pair the model has with a share of at least
PAIR_LISTED, its share and its conditional effects, main + pair, of each feature from its 5th to its 95th
percentile with the other at its 5th and 95th percentile (D22); the remaining pairs in one line.

H2, the facts plus semantic logic: H1 and the statements the verifier certifies about the model
(verifier/certified.py), each as its DSL line and in words (gate/template.py). Interaction claims are listed for
the listed pairs only.

The writer sees plausible names for the planted noise features (data/labels.py, D41 proposed); the claims it
writes are mapped back before verification.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from verifier_gate.data import labels
from verifier_gate.dsl.grammar import HEDGE, Claim
from verifier_gate.facts import readable
from verifier_gate.facts.schema import Facts
from verifier_gate.gate.template import phrase, synthetic_label
from verifier_gate.lexicon import predicates as p

PAIR_LISTED = 0.005
MODEL_NAMES = {
    "EBM": "an explainable boosting machine (EBM)",
    "XGB2": "a gradient-boosted tree model of depth 2 (XGB2)",
    "oracle": "a logistic regression on known shapes (the oracle)",
}


@dataclass
class Handover:
    variant: str
    text: str
    checks: list[readable.Check] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Every readable curve passed its check against M."""
        return all(c.passed for c in self.checks)


def _pct(x: float) -> str:
    return f"{x:.1%}"


def _band(est, fmt: Callable[[float], str] = lambda v: f"{v:+.2f}") -> str:
    lo, hi = p.interval(est)
    return f"{fmt(est.value)} (95% band {fmt(lo)} to {fmt(hi)})"


def _x(value: float) -> str:
    return readable._x(value)


def handover(facts: Facts, X: pd.DataFrame, variant: str = "H1", certified: list[Claim] | None = None,
             names: Mapping[str, str] = labels.SYNTHETIC_NAMES,
             descriptions: Mapping[str, str] = labels.SYNTHETIC_DESCRIPTIONS, naming_bug: bool = False) -> Handover:  # fmt: skip
    """naming_bug: the handover as E3 ran it (results/e3/v3-x3), whose H2 listed the certified statements under the
    plausible names whatever the naming (M5 of the 20 Oct review); only to replay those runs from the cache."""
    if variant not in ("H1", "H2"):
        raise ValueError(f"variant is H1 or H2, not {variant!r}")
    if variant == "H2" and certified is None:
        raise ValueError("H2 needs the certified statements")
    from verifier_gate.verifier.certified import certified_plan

    plan = certified if certified is not None else certified_plan(facts)
    label = synthetic_label(names)
    kind = facts.model.get("kind", "")
    lines = [
        f"Model: {MODEL_NAMES.get(kind, 'a fitted model')}, fitted to predict whether a credit applicant defaults "
        f"({len(X):,} applicants). Effects are on the log-odds scale: positive values raise the risk of default. "
        f"Every band is a 95% band from {facts.bands.get('refits', 0)} refits of the model on resampled data.",
        "",
        "Features, in the order of their share of the model's importance:",
    ]
    checks = []
    for f in sorted(facts.features, key=lambda f: -f.share.value):
        name = labels.shown(f.name, names)
        count = bool(np.all(X[f.name] == np.round(X[f.name])))
        form = readable.readable(f, count)
        checks.append(readable.check(form, facts, plan))
        lo, hi = (int(v) for v in (np.floor(p.interval(f.rank)[0]), np.ceil(p.interval(f.rank)[1])))
        rank = f"rank {lo}" if lo == hi else f"rank {lo} to {hi}"
        lines += [
            f"- `{name}`: {descriptions.get(name, name)}.",
            f"  Share of importance {_band(f.share, _pct)}; {rank} among {len(facts.features)} features.",
            f"  Curve (logit contribution by value): {readable.describe(form)}.",
        ]
    listed = [q for q in sorted(facts.pairs, key=lambda q: -q.share.value) if q.share.value >= PAIR_LISTED]
    rest = [q for q in facts.pairs if q.share.value < PAIR_LISTED]
    lines += ["", f"Interactions: the model has {len(facts.pairs)} pairs." + (" The larger ones:" if listed else "")]
    for q in listed:
        a, b = (labels.shown(x, names) for x in q.features)
        lines.append(f"- `{a} & {b}`: share of importance {_band(q.share, _pct)}.")
        for c in q.conditional:
            fa, fb = labels.shown(c.feature, names), labels.shown(c.moderator, names)
            lines.append(
                f"  Effect of `{fa}` from {_x(c.feature_values[0])} to {_x(c.feature_values[1])}: {_band(c.at_low)} when "
                f"`{fb}` = {_x(c.moderator_values[0])}, {_band(c.at_high)} when `{fb}` = {_x(c.moderator_values[1])}."
            )  # fmt: skip
    if rest:
        lines.append(f"- {len(rest)} further pairs with a share below {PAIR_LISTED:.1%} each, together {_pct(sum(q.share.value for q in rest))}.")
    if variant == "H2":
        listed_pairs = {frozenset(q.features) for q in listed}
        statements = [
            c for c in plan
            if not ((c.kind == "interaction" or (c.kind == HEDGE and c.inner.kind == "interaction")) and frozenset(c.terms) not in listed_pairs)
        ]  # fmt: skip
        lines += ["", "Statements the verifier certifies for this model (true at this sample size), as DSL and in words:"]
        for c in statements:
            lines.append(f"- {labels.external(c, labels.SYNTHETIC_NAMES if naming_bug else names)}  ({phrase(c, label)})")
    return Handover(variant, "\n".join(lines), checks)
