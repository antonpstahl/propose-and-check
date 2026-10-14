"""Planted claims: what T says about a synthetic dataset, as DSL claims with their labels (§6 E1).

Labels come from the DGP's specification (shapes, interaction level) and from T's shares on the sample, never
from a fitted model. True and false claims are both listed, so E1 can measure agreement on both, and the
scorer test (lexicon applied to T must reproduce every label) covers every claim type in both directions.

The false claims are near misses where a writer could plausibly go wrong: the neighbouring strength class,
the next rank, the reversed comparison, the opposite direction and the "mostly" variant, a shifted location,
the other interaction pattern.

Sets of values (D33) get the same treatment: the sets around T's value ("weak to moderate", "second or
third", "generally decreases") are true, and a neighbouring set that leaves T's value out is false. The hedge
unsettled(<claim>) (D30) has no label here: it is a statement about the evidence in one sample, not about T,
and E2 and E3 test it.
"""

import numpy as np

from verifier_gate.data import dgp
from verifier_gate.dsl.grammar import Claim
from verifier_gate.lexicon import predicates
from verifier_gate.lexicon.predicates import CLASSES, FALSE, STRENGTHS, TRUE

DIRECTION = {  # the planted shapes (dgp.MAIN_SHAPES)
    "utilization": "increasing",
    "n_delinquencies": "increasing",
    "income": "decreasing",
    "history_months": "mostly_decreasing",  # rising on 7% of the data mass before the bump at 36 months
    "dti": "increasing",  # a step, flat elsewhere
    "n_inquiries": "increasing",  # the main term; the sign flip lives in the pair
    "age": "decreasing",
}
OPPOSITE = {"increasing": "decreasing", "decreasing": "increasing"}
THRESHOLD = ("dti", 0.43)  # dgp._dti
PEAK = ("history_months", 36.0)  # dgp._history: centre of the bump
PATTERN_CLAIMS = {dgp.AMPLIFICATION: ("utilization", "n_delinquencies"), dgp.SIGN_FLIP: ("n_inquiries", "history_months")}


def _strength_label(share: float, lex: predicates.Lexicon) -> str | None:
    """The class of a planted share, None below the weak class (negligible)."""
    inside = [s for s in STRENGTHS if lex.strength_class(s)[0] <= share < lex.strength_class(s)[1]]
    return inside[0] if inside else None


def planted_claims(data: dgp.Dataset, lex: predicates.Lexicon | None = None) -> list[tuple[Claim, str]]:
    lex = lex or predicates.load()
    shares = data.truth.shares(data.X)
    out: list[tuple[Claim, str]] = []

    def add(claim: Claim, label: str) -> None:
        out.append((claim, label))

    for f in dgp.FEATURES:
        label = _strength_label(shares[f], lex)
        add(Claim("negligible", (f,)), TRUE if label is None else FALSE)
        if label is None:
            add(Claim("strength", (f,), "weak"), FALSE)
        else:
            add(Claim("strength", (f,), label), TRUE)
            for other in STRENGTHS:
                if other != label and abs(STRENGTHS.index(other) - STRENGTHS.index(label)) == 1:
                    add(Claim("strength", (f,), other), FALSE)
        add(Claim("share", (f,), round(shares[f], 3)), TRUE)
        add(Claim("share", (f,), round(shares[f] + max(0.05, 0.3 * shares[f]), 3)), FALSE)

    ranked = sorted((f for f in dgp.FEATURES if shares[f] > 0), key=lambda f: -shares[f])
    for k, f in enumerate(ranked, 1):
        add(Claim("rank", (f,), k), TRUE)
        add(Claim("rank", (f,), k + 1 if k < len(ranked) else k - 1), FALSE)
    for a, b in zip(ranked, ranked[1:]):
        add(Claim("comparison", (a, b), relation=">"), TRUE)
        add(Claim("comparison", (b, a), relation=">"), FALSE)

    for f, d in DIRECTION.items():
        strict = d.removeprefix("mostly_")
        add(Claim("direction", (f,), d), TRUE)
        add(Claim("direction", (f,), strict if d.startswith("mostly_") else f"mostly_{d}"), FALSE)
        add(Claim("direction", (f,), OPPOSITE[strict]), FALSE)
        add(Claim("direction", (f,), f"mostly_{OPPOSITE[strict]}"), FALSE)
    for f in (f for f in dgp.FEATURES if shares[f] == 0):  # flat: neither direction
        add(Claim("direction", (f,), "increasing"), FALSE)
        add(Claim("direction", (f,), "decreasing"), FALSE)

    feature, at = THRESHOLD
    add(Claim("threshold", (feature,), at), TRUE)
    add(Claim("threshold", (feature,), 0.25), FALSE)
    add(Claim("threshold", ("income",), float(np.median(data.X["income"]))), FALSE)
    feature, at = PEAK
    add(Claim("peak", (feature,), at), TRUE)
    add(Claim("peak", (feature,), 200.0), FALSE)
    add(Claim("peak", ("income",), float(np.median(data.X["income"]))), FALSE)

    planted = data.scenario.interaction != "none"
    for pair, (a, b) in PATTERN_CLAIMS.items():
        pattern = dgp.PAIR_PATTERNS[pair]
        other = next(p for p in ("amplification", "sign_flip") if p != pattern)
        add(Claim("interaction", (a, b), pattern), TRUE if planted else FALSE)
        add(Claim("interaction", (a, b), other), FALSE)
        add(Claim("interaction", (a, b), "none"), FALSE if planted else TRUE)

    # sets of values (D33): the sets around T's value, and a neighbouring set that leaves it out
    for f in dgp.FEATURES:
        i = CLASSES.index(_strength_label(shares[f], lex) or "negligible")
        for j in (i - 1, i + 1):
            if 0 <= j < len(CLASSES):
                add(Claim("strength", (f,), CLASSES[min(i, j) : max(i, j) + 1]), TRUE)
        miss = (i + 1, i + 2) if i + 2 < len(CLASSES) else (i - 2, i - 1)
        add(Claim("strength", (f,), CLASSES[miss[0] : miss[1] + 1]), FALSE)
    for k, f in enumerate(ranked, 1):
        add(Claim("rank", (f,), (k, k + 1) if k < len(ranked) else (k - 1, k)), TRUE)
        add(Claim("rank", (f,), (k + 1, k + 2) if k + 2 <= len(ranked) else (k - 2, k - 1)), FALSE)
    for f, d in DIRECTION.items():
        strict = d.removeprefix("mostly_")
        add(Claim("direction", (f,), (strict, f"mostly_{strict}")), TRUE)
        add(Claim("direction", (f,), (OPPOSITE[strict], f"mostly_{OPPOSITE[strict]}")), FALSE)
    for f in (f for f in dgp.FEATURES if shares[f] == 0):  # flat: neither direction
        for d in ("increasing", "decreasing"):
            add(Claim("direction", (f,), (d, f"mostly_{d}")), FALSE)
    return out
