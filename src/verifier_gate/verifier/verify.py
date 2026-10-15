"""Execute claims against Facts and return a verdict (true, false, undecidable) plus evidence (§5.6).

Pure Python and deterministic: each claim type maps to one lexicon predicate (lexicon/predicates.py), which
reads only the Facts of one model. No LLM. A set of values (D33) goes to the set form of its predicate; the
hedge unsettled(<claim>) (D30) is judged on the verdict of its claim.
"""

from collections.abc import Iterable, Mapping

from verifier_gate.dsl.grammar import HEDGE, Claim
from verifier_gate.dsl.parse import parse
from verifier_gate.facts.schema import Facts
from verifier_gate.lexicon import predicates as p


def verify(claim: Claim | str, facts: Facts, lex: p.Lexicon | None = None) -> p.Verdict:
    claim = parse(claim) if isinstance(claim, str) else claim
    lex = lex or p.load()
    t = claim.terms
    if claim.kind == HEDGE:
        verdict = p.unsettled(verify(claim.inner, facts, lex))
        return p.Verdict(verdict.value, {"claim": str(claim.inner)} | verdict.evidence, verdict.reason)
    if isinstance(claim.value, tuple):
        match claim.kind:
            case "rank":
                return p.rank_in(facts, t[0], claim.value, lex)
            case "direction":
                return p.direction_in(facts, t[0], claim.value, lex)
            case "strength":
                return p.strength_in(facts, t[0], claim.value, lex)
        raise ValueError(f"{claim.kind} takes no set of values")
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


def evidence_text(evidence: Mapping) -> str:
    """A verdict's evidence in one line, for the log and the repair message."""

    def fmt(v):
        if isinstance(v, float):
            return f"{v:.3g}"
        if isinstance(v, (tuple, list)) and all(isinstance(x, (int, float)) for x in v):
            return " to ".join(f"{x:.3g}" for x in v)
        return str(v)

    items = [(k, v) for k, v in evidence.items() if k not in ("term", "claim", "claim reason") and not isinstance(v, dict)]
    return "; ".join(f"{k} {fmt(v)}" for k, v in items[:5])
