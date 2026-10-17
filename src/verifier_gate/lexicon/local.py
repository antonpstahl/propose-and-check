"""Local predicates over the facts of one adverse-action notice (D47, D49): the three local claim types.

| claim                                   | true                                                  | false                                        |
|-----------------------------------------|-------------------------------------------------------|----------------------------------------------|
| reason_rank("t") == k  (or in (k, k+1)) | rank band inside the ranks, contribution band above 0 | rank band outside, or contribution band <= 0 |
| principal_reason("t")                   | fraction band >= MATERIALITY, rank band <= MAX_REASONS | fraction band < MATERIALITY, or rank band > MAX_REASONS |
| higher_than_reference("f") / lower_...  | applicant's value above (below) the reference median  | otherwise                                    |

A reason pushes towards the decline, so a rank claim needs a positive contribution: the seventh term of a list
is not the seventh reason if it speaks for the applicant. A claim that combines two conditions is true if both
bands lie inside their sets and false if either lies outside, as the global words that need two facts
(lexicon/predicates.py). Rank bands are rounded outward to whole ranks, as globally.

Terms as globally: a feature or a pair "a & b". A pair of known features that M does not have is a term that
is exactly zero, so it is no reason (false); a feature the model does not have is UNKNOWN_TERM. The wording
claims compare data, not estimates (the applicant and the reference are fixed), so they are two-valued; they
apply to features only.

Truth. `truth_view` gives the same notice under T, without bands, and the same predicates then give the label
of a claim against the planted truth (as E1 applies the lexicon to T). Where T's score gap is not positive, T
does not see the applicant as riskier than the comparable approved: no term carries a share of the gap, so no
principal reason is true against T (the notice is flagged `declined_by_m_only`).
"""

from dataclasses import replace

import numpy as np

from verifier_gate.facts.local import MATERIALITY, MAX_REASONS, LocalFacts, Reason
from verifier_gate.facts.schema import Estimate
from verifier_gate.facts.steps import PAIR_SEPARATOR
from verifier_gate.lexicon.predicates import FALSE, NOT_APPLICABLE, UNDECIDABLE, UNKNOWN_TERM, Verdict, _judge, interval

KINDS = ("reason_rank", "principal_reason", "higher_than_reference", "lower_than_reference")


def _features(lf: LocalFacts) -> set[str]:
    return {v.feature for v in lf.values}


def _reason(lf: LocalFacts, term: str) -> Reason | Verdict:
    """The term's local facts; a zero reason for a pair of known features M lacks; a Verdict if unknown."""
    features = term.split(PAIR_SEPARATOR)
    if not set(features) <= _features(lf) or len(features) > 2:
        return Verdict(UNDECIDABLE, {"term": term}, f"the model has no feature {term!r}", UNKNOWN_TERM)
    found = lf.reason(term)
    if found is not None and found.rank is not None:
        return found
    zero = Estimate(0.0, (0.0, 0.0))
    return Reason(term, zero, zero, None, found.truth if found else 0.0, found.truth_fraction if found else 0.0, 0)


def _rank_band(r: Reason) -> tuple[float, float]:
    lo, hi = interval(r.rank)
    return float(np.floor(lo)), float(np.ceil(hi))


def reason_rank(lf: LocalFacts, term: str, ks: int | tuple[int, ...]) -> Verdict:
    """The term is the k-th reason (or one of consecutive ranks, D33)."""
    ks = (ks,) if isinstance(ks, int) else ks
    r = _reason(lf, term)
    if isinstance(r, Verdict):
        return r
    c = interval(r.contribution)
    if r.rank is None:  # exactly zero: no reason at any rank
        return Verdict(FALSE, {"term": term, "contribution": 0.0, "claimed": list(ks)}, "the model has no such term")
    lo, hi = _rank_band(r)
    value = _judge(ks[0] <= lo and hi <= ks[-1] and c[0] > 0, hi < ks[0] or lo > ks[-1] or c[1] <= 0)
    return Verdict(value, {"term": term, "rank": r.rank.value, "rank band": (lo, hi), "contribution band": c, "claimed": list(ks)})


def principal_reason(lf: LocalFacts, term: str) -> Verdict:
    """The term is a principal reason: material (from MATERIALITY of the score gap) and among the first
    MAX_REASONS."""
    r = _reason(lf, term)
    if isinstance(r, Verdict):
        return r
    f = interval(r.fraction)
    if r.rank is None:
        return Verdict(FALSE, {"term": term, "fraction": 0.0}, "the model has no such term")
    lo, hi = _rank_band(r)
    value = _judge(f[0] >= MATERIALITY and hi <= MAX_REASONS, f[1] < MATERIALITY or lo > MAX_REASONS)
    return Verdict(value, {"term": term, "fraction": r.fraction.value, "fraction band": f, "rank band": (lo, hi),
                           "materiality": MATERIALITY, "max reasons": MAX_REASONS})  # fmt: skip


def compared_to_reference(lf: LocalFacts, feature: str, higher: bool) -> Verdict:
    """The applicant's value is above (higher) or below the reference's median: wording against measurement."""
    if PAIR_SEPARATOR in feature:
        return Verdict(UNDECIDABLE, {"term": feature}, "a pair has no single value", NOT_APPLICABLE)
    v = lf.value(feature)
    if v is None:
        return Verdict(UNDECIDABLE, {"term": feature}, f"the model has no feature {feature!r}", UNKNOWN_TERM)
    holds = v.applicant > v.reference_median if higher else v.applicant < v.reference_median
    return Verdict(_judge(holds, not holds), {"term": feature, "applicant": v.applicant, "reference median": v.reference_median})


def truth_view(lf: LocalFacts, truth_facts=None) -> LocalFacts:
    """The notice under T, without bands: the same predicates on it give labels against the planted truth.
    truth_facts: T's global Facts, for a global claim in a notice."""
    positive = lf.truth_gap > 0
    reasons = tuple(
        Reason(r.term, Estimate(r.truth), Estimate(r.truth_fraction if positive else 0.0), Estimate(float(r.truth_rank)),
               r.truth, r.truth_fraction, r.truth_rank)  # fmt: skip
        for r in lf.reasons
    )
    model = {**lf.model, "view": "T", "declined_by_m_only": not positive}
    return replace(lf, model=model, gap=Estimate(lf.truth_gap), reasons=reasons, draws=None, model_facts=truth_facts)
