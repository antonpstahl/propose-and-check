"""What a repair message tells the writer about a failing claim, and when a failure is the same problem again.

Advice (plan §14.14, review item 13; decided 15 Oct): each failing claim gets advice that says why it failed, from
its verdict's evidence: for a strength word, the classes the share band spans, in percentages; for "about x%",
the band and the shares the claim fits; for "jumps at" and "peaks at", either where the jump or peak lies, or that
the curve has none, so that no location (and no hedge of one) can make the claim true. Other claims get the advice
of their reason code (D30). The texts are prompts: they live in llm/prompts/advice.json, frozen with the writer's
prompts.

The same problem (review item 12): the no-progress rule compares failing claims by their DSL line, except a jump
or peak claim on a curve that has no jump or no peak: whatever its location, hedged or not, it is one problem.
"""

from verifier_gate.dsl.grammar import HEDGE, Claim
from verifier_gate.facts.readable import _x
from verifier_gate.lexicon import predicates as p
from verifier_gate.lexicon.predicates import FALSE, STRENGTHS, UNDECIDABLE, Verdict
from verifier_gate.llm import prompts


def _pct(v: float) -> str:
    return f"{v:.1%}".replace(".0%", "%")


def _classes(low: float, high: float, lex: p.Lexicon) -> str:
    """The strength classes a share band [low, high] overlaps, with their ranges in percent."""
    edges = [0.0, *(lex.strength[s] for s in STRENGTHS), float("inf")]
    names = ("negligible", *STRENGTHS)
    spanned = []
    for name, lo, hi in zip(names, edges[:-1], edges[1:]):
        if low < hi and high >= lo:
            span = f"below {_pct(hi)}" if lo == 0 else f"{_pct(lo)} or more" if hi == float("inf") else f"{_pct(lo)} to {_pct(hi)}"
            spanned.append(f"{name} ({span})")
    return spanned[0] if len(spanned) == 1 else ", ".join(spanned[:-1]) + " and " + spanned[-1]


def impossible(kind: str, evidence: dict, lex: p.Lexicon) -> str:
    """For a jump or peak claim: 'jump' or 'peak' if the curve has none, so that no location can make it true;
    else ''. A jump is judged true only if the curve's largest step is significant and at least `jump_fraction` of
    its range; a peak only if the maximum is interior. Neither depends on the location claimed."""
    if kind == "threshold" and "jump significant" in evidence:
        small = evidence["jump / range band"][1] < lex.jump_fraction
        return "jump" if small or not evidence["jump significant"] else ""
    if kind == "peak" and "interior maximum" in evidence:
        return "" if evidence["interior maximum"] else "peak"
    return ""


def explain(claim: Claim, verdict: Verdict, lex: p.Lexicon | None = None) -> str:
    """The advice for a failing claim."""
    lex = lex or p.load()
    text = prompts.advice()
    e = verdict.evidence
    inner = claim.inner if claim.kind == HEDGE else claim
    missing = impossible(inner.kind, e, lex)
    if missing == "jump":
        small = e["jump / range band"][1] < lex.jump_fraction
        why = text["no_jump_small"].format(ratio=_pct(e["jump / range band"][1])) if small else text["no_jump_insignificant"]
        return text["no_jump"].format(at=_x(e["largest jump at"]), why=why)
    if missing == "peak":
        return text["no_peak"]
    if claim.kind == HEDGE and verdict.value == FALSE:
        return text["hedge_settled_true" if e.get("claim verdict") == "true" else "hedge_settled_false"]
    if verdict.code in (p.UNKNOWN_TERM, p.NOT_APPLICABLE):
        return text[verdict.code]
    general = text[verdict.code] if verdict.value == UNDECIDABLE and verdict.code in text else text["false"]
    if inner.kind == "strength" and "share band" in e:
        low, high = e["share band"]
        advice = text["strength"].format(share=_pct(e["share"]), low=_pct(low), high=_pct(high), classes=_classes(low, high, lex))
        return advice + ("" if e.get("detectable", True) else text["strength_undetected"])
    if inner.kind == "share" and "shares the claim fits" in e:
        (low, high), (fit_low, fit_high) = e["share band"], e["shares the claim fits"]
        return text["share"].format(share=_pct(e["share"]), low=_pct(low), high=_pct(high), claimed=_pct(e["claimed"]),
                                    fit_low=_pct(fit_low), fit_high=_pct(fit_high))  # fmt: skip
    if inner.kind == "rank" and "rank band" in e:
        low, high = e["rank band"]
        return text["rank"].format(rank=int(e["rank"]), low=int(low), high=int(high))
    if inner.kind == "threshold" and "location band" in e:
        low, high = e["location band"]
        return text["jump_elsewhere"].format(at=_x(e["largest jump at"]), low=_x(low), high=_x(high))
    if inner.kind == "peak" and "highest steps" in e:
        low, high = e["highest steps"]
        return text["peak_elsewhere"].format(low=_x(low), high=_x(high))
    return general


def problem_key(claim: Claim, verdict: Verdict, lex: p.Lexicon | None = None) -> str:
    """What the no-progress rule compares: the claim's line, or 'no jump in x' / 'no peak in x' for a jump or peak
    claim, hedged or not, on a curve that has none."""
    inner = claim.inner if claim.kind == HEDGE else claim
    missing = impossible(inner.kind, verdict.evidence, lex or p.load())
    return f"no {missing} in {inner.terms[0]}" if missing else str(claim)
