"""Execute claims against Facts and return a verdict (true, false, undecidable) plus evidence (§5.6).

Pure Python and deterministic: each claim type maps to one lexicon predicate (lexicon/predicates.py), which
reads only the Facts of one model. No LLM. A set of values (D33) goes to the set form of its predicate; the
hedge unsettled(<claim>) (D30) is judged on the verdict of its claim.

The local spot check (D49): given one notice's facts (facts/local.LocalFacts) instead of a model's Facts, the
local claims go to lexicon/local.py, and a global claim goes to the model's Facts the notice carries
(`model_facts`), or is not applicable if it carries none. A local claim on a model's Facts is not applicable.
A hedge in a notice is false whatever it hedges (D68): a notice states the principal reasons for a decision M has
made, on M's exact contributions, and never hedges them.
"""

from collections.abc import Iterable, Mapping

from verifier_gate.dsl.grammar import HEDGE, LOCAL_KINDS, Claim
from verifier_gate.dsl.parse import parse
from verifier_gate.facts.local import LocalFacts
from verifier_gate.facts.schema import Facts
from verifier_gate.lexicon import local as lp
from verifier_gate.lexicon import predicates as p

NOTICE_HEDGE = "a notice states its principal reasons and never hedges them"


def verify(claim: Claim | str, facts: Facts | LocalFacts, lex: p.Lexicon | None = None) -> p.Verdict:
    claim = parse(claim) if isinstance(claim, str) else claim
    lex = lex or p.load()
    t = claim.terms
    if claim.kind == HEDGE and isinstance(facts, LocalFacts):
        inner = verify(claim.inner, facts, lex)
        return p.Verdict(p.FALSE, {"claim": str(claim.inner), "claim verdict": inner.value}, NOTICE_HEDGE)
    if claim.kind == HEDGE:
        verdict = p.unsettled(verify(claim.inner, facts, lex))
        return p.Verdict(verdict.value, {"claim": str(claim.inner)} | verdict.evidence, verdict.reason)
    if isinstance(facts, LocalFacts):
        return _local(claim, facts, lex)
    if claim.kind in LOCAL_KINDS:
        return p.Verdict(p.UNDECIDABLE, {"term": t[0]}, "a claim about one applicant; these facts are about the model", p.NOT_APPLICABLE)
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
        case "threshold" | "drop":
            return p.threshold(facts, t[0], claim.value, lex, sign=1 if claim.kind == "threshold" else -1)
        case "peak":
            return p.peak(facts, t[0], claim.value, lex)
        case "interaction":
            return p.interaction(facts, t[0], t[1], claim.value, lex)
    raise ValueError(f"unknown claim kind {claim.kind}")


def _local(claim: Claim, lf: LocalFacts, lex: p.Lexicon) -> p.Verdict:
    t = claim.terms
    match claim.kind:
        case "reason_rank":
            return lp.reason_rank(lf, t[0], claim.value)
        case "principal_reason":
            return lp.principal_reason(lf, t[0])
        case "higher_than_reference" | "lower_than_reference":
            return lp.compared_to_reference(lf, t[0], higher=claim.kind == "higher_than_reference")
    if lf.model_facts is not None:
        return verify(claim, lf.model_facts, lex)
    return p.Verdict(p.UNDECIDABLE, {"term": t[0]}, "a claim about the whole model; the notice carries no model facts", p.NOT_APPLICABLE)


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
