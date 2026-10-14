"""Round-trip check: three extractions, plan-text comparison, coverage and emphasis (§5.7).

Built so far: coverage (§5.7, item 3), which needs no LLM and also runs on plans (E2's omission mutants). The
top 3 terms by M's share and every pair with a share of at least 10% must be mentioned. A set covers its term
(D33); a hedge unsettled(<claim>) covers a term only if nothing about the term is certified, and then it raises
the limited-evidence flag (D30): released, but marked for a reviewer.
"""

from collections.abc import Iterable
from dataclasses import dataclass

from verifier_gate.dsl.grammar import HEDGE, Claim
from verifier_gate.facts.schema import Facts
from verifier_gate.facts.steps import PAIR_SEPARATOR

TOP_TERMS = 3
PAIR_SHARE = 0.10


@dataclass(frozen=True)
class Coverage:
    required: tuple[frozenset, ...]
    missing: tuple[frozenset, ...]
    hedged_only: tuple[frozenset, ...]  # covered by hedges alone: the limited-evidence flag

    @property
    def passed(self) -> bool:
        return not self.missing

    @property
    def flagged(self) -> bool:
        return bool(self.hedged_only)


def term_key(name: str) -> frozenset:
    """A feature or a pair ("a & b", either order) as the set of its features."""
    return frozenset(s.strip() for s in name.split(PAIR_SEPARATOR.strip()))


def claim_terms(claim: Claim) -> set[frozenset]:
    """The terms a claim is about: an interaction is about its pair, a comparison about both features."""
    if claim.kind == HEDGE:
        return claim_terms(claim.inner)
    if claim.kind == "interaction":
        return {frozenset(claim.terms)}
    return {term_key(t) for t in claim.terms}


def required_terms(facts: Facts) -> tuple[frozenset, ...]:
    shares = {frozenset([f.name]): f.share.value for f in facts.features}
    shares |= {frozenset(q.features): q.share.value for q in facts.pairs}
    top = sorted(shares, key=lambda k: -shares[k])[:TOP_TERMS]
    pairs = [k for k, s in shares.items() if len(k) == 2 and s >= PAIR_SHARE and k not in top]
    return tuple(top + sorted(pairs, key=lambda k: -shares[k]))


def coverage(claims: Iterable[Claim], facts: Facts, certified: Iterable[Claim]) -> Coverage:
    """certified: what the verifier certifies about the model (verifier/certified.py), to decide whether a hedge
    may cover a term."""
    claims = list(claims)
    stated = set().union(*(claim_terms(c) for c in claims if c.kind != HEDGE))
    hedged = set().union(*(claim_terms(c) for c in claims if c.kind == HEDGE))
    settled = set().union(*(claim_terms(c) for c in certified if c.kind != HEDGE))
    required = required_terms(facts)
    hedge_covers = {k for k in hedged if k not in settled}
    missing = tuple(k for k in required if k not in stated and k not in hedge_covers)
    hedged_only = tuple(k for k in required if k not in stated and k in hedge_covers)
    return Coverage(required, missing, hedged_only)
