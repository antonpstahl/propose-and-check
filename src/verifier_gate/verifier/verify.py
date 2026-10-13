"""Execute claims against Facts and return a verdict (true, false, undecidable) plus evidence (§5.6).

Pure Python and deterministic: each claim type maps to one lexicon predicate (lexicon/predicates.py), which
reads only the Facts of one model. No LLM.
"""

from collections.abc import Iterable

from verifier_gate.dsl.grammar import Claim
from verifier_gate.dsl.parse import parse
from verifier_gate.facts.schema import Facts
from verifier_gate.lexicon import predicates as p


def verify(claim: Claim | str, facts: Facts, lex: p.Lexicon | None = None) -> p.Verdict:
    claim = parse(claim) if isinstance(claim, str) else claim
    lex = lex or p.load()
    t = claim.terms
    match claim.kind:
        case "rank":
            return p.rank(facts, t[0], claim.value, lex)
        case "share":
            return p.share(facts, t[0], claim.value, lex)
        case "direction":
            return p.direction(facts, t[0], claim.value, lex)
        case "strength":
            return p.strength(facts, t[0], claim.value, lex)
        case "negligible":
            return p.negligible(facts, t[0], lex)
        case "comparison":
            return p.comparison(facts, t[0], t[1], claim.relation, lex)
        case "threshold":
            return p.threshold(facts, t[0], claim.value, lex)
        case "peak":
            return p.peak(facts, t[0], claim.value, lex)
        case "interaction":
            return p.interaction(facts, t[0], t[1], claim.value, lex)
    raise ValueError(f"unknown claim kind {claim.kind}")


def verify_all(claims: Iterable[Claim | str], facts: Facts, lex: p.Lexicon | None = None) -> list[tuple[Claim, p.Verdict]]:
    parsed = [parse(c) if isinstance(c, str) else c for c in claims]
    return [(c, verify(c, facts, lex)) for c in parsed]
