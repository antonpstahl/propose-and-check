"""What the verifier certifies about a model: per term and claim type, the most specific true statement.

The resolution ladder (D30, D33, §14.7): the single value if it is certified, else the narrowest certified set,
else nothing; a term about which nothing is certified gets its hedge, if the hedge is true. Every statement
returned is true by its verdict, so the list is a correct plan: the source of E2's mutants (plan §6 E2, source
a) and, from week 5, of H2's statements and the template.

Candidates per feature: strength (or negligible), direction, rank, share (M's share to 3 decimals), "jumps at"
(or, under lexicon v3, "drops at", by the sign of M's step; D64) the largest jump and "peaks at" the highest steps
(both located on M, kept only if certified), and the
comparison with the next feature in M's ranking. Per pair of the model: its pattern, for either feature as the
one whose effect changes, and "none". Nothing here reads T or the oracle.

For one notice of the local spot check (`certified_local`, D49, D68): per term of M with a contribution above zero,
that it is a principal reason (on M's exact contributions, lexicon/local.py), its reason rank, and for a feature
that is a principal reason, how its value compares with the reference.
"""

from collections.abc import Iterable

from verifier_gate.dsl.grammar import HEDGE, Claim
from verifier_gate.facts.local import LocalFacts
from verifier_gate.facts.schema import Facts
from verifier_gate.lexicon import predicates as p
from verifier_gate.lexicon.predicates import CLASSES, STRENGTHS, TRUE
from verifier_gate.verifier.verify import verify


def _runs(values: tuple, length: int) -> list[tuple]:
    return [values[i : i + length] for i in range(len(values) - length + 1)]


def strength_ladder(feature: str) -> list[Claim]:
    """Single classes, then sets of 2 and 3 neighbouring classes (never all four)."""
    singles = [Claim("negligible", (feature,))] + [Claim("strength", (feature,), s) for s in STRENGTHS]
    return singles + [Claim("strength", (feature,), run) for k in (2, 3) for run in _runs(CLASSES, k)]


def direction_ladder(feature: str) -> list[Claim]:
    singles = [Claim("direction", (feature,), d) for d in p.DIRECTIONS]
    return singles + [Claim("direction", (feature,), (d, f"mostly_{d}")) for d in ("increasing", "decreasing")]


def rank_ladder(feature: str, features: int) -> list[Claim]:
    ranks = tuple(range(1, features + 1))
    singles = [Claim("rank", (feature,), k) for k in ranks]
    return singles + [Claim("rank", (feature,), run) for k in range(2, features) for run in _runs(ranks, k)]


def first_certified(claims: Iterable[Claim], facts: Facts, lex: p.Lexicon) -> Claim | None:
    return next((c for c in claims if verify(c, facts, lex).value == TRUE), None)


def point_class(facts: Facts, feature: str, lex: p.Lexicon) -> Claim:
    """The strength claim of M's own share (its point estimate): what a hedge is about."""
    share = facts.feature(feature).share.value
    if share < lex.strength["weak"]:
        return Claim("negligible", (feature,))
    return Claim("strength", (feature,), next(s for s in reversed(STRENGTHS) if share >= lex.strength[s]))


def certified_local(lf: LocalFacts, lex: p.Lexicon | None = None) -> list[Claim]:
    lex = lex or p.load()
    plan: list[Claim] = []
    for r in lf.reasons:
        if r.rank is None or r.contribution.value <= 0:
            continue  # no reason at any rank: nothing to certify
        principal = Claim("principal_reason", (r.term,))
        is_principal = verify(principal, lf, lex).value == TRUE
        if is_principal:
            plan.append(principal)
        plan.append(Claim("reason_rank", (r.term,), int(r.rank.value)))  # exact ranks: the single rank is true
        if is_principal and len(r.term.split(" & ")) == 1:
            plan += [c for kind in ("higher_than_reference", "lower_than_reference")
                     if verify(c := Claim(kind, (r.term,)), lf, lex).value == TRUE]  # fmt: skip
    return plan


def certified_plan(facts: Facts, lex: p.Lexicon | None = None) -> list[Claim]:
    lex = lex or p.load()
    names = [f.name for f in facts.features]
    plan: list[Claim] = []

    def keep(claim: Claim | None) -> bool:
        if claim is not None and verify(claim, facts, lex).value == TRUE:
            plan.append(claim)
            return True
        return False

    by_share = sorted(names, key=lambda n: -facts.feature(n).share.value)
    for name in names:
        before = len(plan)
        for ladder in (strength_ladder(name), direction_ladder(name), rank_ladder(name, len(names))):
            keep(first_certified(ladder, facts, lex))
        keep(Claim("share", (name,), round(float(facts.feature(name).share.value), 3)))
        jump = p.threshold(facts, name, 0.0, lex).evidence
        kind = "drop" if lex.signed_jumps and jump["jump"] < 0 else "threshold"
        keep(Claim(kind, (name,), round(float(jump["largest jump at"]), 3)))
        span = p.peak(facts, name, 0.0, lex).evidence["highest steps"]
        keep(Claim("peak", (name,), round(float(sum(span) / 2), 3)))
        if len(plan) == before:  # nothing certified: the hedge of M's own class, if the evidence leaves it open
            inner = point_class(facts, name, lex)
            keep(Claim(HEDGE, inner.terms, inner=inner))
    for a, b in zip(by_share, by_share[1:]):
        keep(Claim("comparison", (a, b), relation=">"))
    for pair in facts.pairs:
        before = len(plan)
        a, b = pair.features
        for x, y in ((a, b), (b, a)):
            for pattern in ("amplification", "sign_flip"):
                keep(Claim("interaction", (x, y), pattern))
        keep(Claim("interaction", (a, b), "none"))
        if len(plan) == before:
            inner = Claim("interaction", (a, b), "none")
            keep(Claim(HEDGE, inner.terms, inner=inner))
    return plan
