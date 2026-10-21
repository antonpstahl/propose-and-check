"""Local predicates over the facts of one adverse-action notice (D47, D49, D68): the three local claim types.

| claim                                   | true                                                  | false     |
|-----------------------------------------|-------------------------------------------------------|-----------|
| reason_rank("t") == k  (or in (k, k+1)) | M's rank of t is among the ranks, its contribution > 0 | otherwise |
| principal_reason("t")                   | M's fraction of t >= MATERIALITY, M's rank <= MAX_REASONS | otherwise |
| higher_than_reference("f") / lower_...  | applicant's value above (below) the reference median  | otherwise |

Two-valued on M's exact contributions (D68, review M6): M made the decision, and for an additive model its
contributions to this applicant's score gap are exact, so the principal reasons for the decision are M's, not an
estimate of them. The refit bands answer another question (would a model fitted on another sample also decline,
and for the same reasons?); they stay in the facts as an internal flag (`second_look`) and never decide what a
notice states. A reason pushes towards the decline, so a rank claim needs a positive contribution: the seventh
term of a list is not the seventh reason if it speaks for the applicant. Ties share a rank (facts/local.py).

Terms as globally: a feature or a pair "a & b". A pair of known features that M does not have is a term that
is exactly zero, so it is no reason (false); a feature the model does not have is UNKNOWN_TERM. The wording
claims compare data (the applicant and the reference are fixed); they apply to features only.

Truth. `truth_view` gives the same notice under T, and the same predicates then give the label of a claim against
the planted truth (as E1 applies the lexicon to T). Where T's score gap is not positive, T does not see the
applicant as riskier than the comparable approved: no term carries a share of the gap, so no principal reason is
true against T (the notice is flagged `declined_by_m_only`).

Second look. `second_look` gives the internal flag: the reasons a lender's reviewer should look at the case,
from the bands. The gap band reaches zero (a model fitted on another sample might approve), or a principal reason
under M is one the bands leave open or refute (`band_principal_reason`, the rule of l1: the whole fraction band
from MATERIALITY, the whole rank band within MAX_REASONS). The flag goes to the lender, never into the notice.
"""

from dataclasses import replace

import numpy as np

from verifier_gate.facts.local import MATERIALITY, MAX_REASONS, LocalFacts, Reason
from verifier_gate.facts.schema import Estimate
from verifier_gate.facts.steps import PAIR_SEPARATOR
from verifier_gate.lexicon.predicates import FALSE, NOT_APPLICABLE, TRUE, UNDECIDABLE, UNKNOWN_TERM, Verdict, _judge, interval

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


def _is_principal(r: Reason) -> bool:
    return r.fraction.value >= MATERIALITY and r.rank.value <= MAX_REASONS


def reason_rank(lf: LocalFacts, term: str, ks: int | tuple[int, ...]) -> Verdict:
    """The term is the k-th reason (or one of consecutive ranks, D33)."""
    ks = (ks,) if isinstance(ks, int) else ks
    r = _reason(lf, term)
    if isinstance(r, Verdict):
        return r
    if r.rank is None:  # exactly zero: no reason at any rank
        return Verdict(FALSE, {"term": term, "contribution": 0.0, "claimed": list(ks)}, "the model has no such term")
    holds = ks[0] <= r.rank.value <= ks[-1] and r.contribution.value > 0
    return Verdict(_judge(holds, not holds), {"term": term, "rank": r.rank.value, "contribution": r.contribution.value, "claimed": list(ks)})


def principal_reason(lf: LocalFacts, term: str) -> Verdict:
    """The term is a principal reason: material (from MATERIALITY of the score gap) and among the first
    MAX_REASONS, on M's exact contributions."""
    r = _reason(lf, term)
    if isinstance(r, Verdict):
        return r
    if r.rank is None:
        return Verdict(FALSE, {"term": term, "fraction": 0.0}, "the model has no such term")
    holds = _is_principal(r)
    return Verdict(_judge(holds, not holds), {"term": term, "fraction": r.fraction.value, "rank": r.rank.value,
                                              "materiality": MATERIALITY, "max reasons": MAX_REASONS})  # fmt: skip


def principal_reasons(lf: LocalFacts) -> tuple[str, ...]:
    """M's principal reasons for the decision, in the order of M's contributions: what a notice must state."""
    return tuple(r.term for r in lf.reasons if r.rank is not None and _is_principal(r))


def band_principal_reason(lf: LocalFacts, term: str) -> Verdict:
    """The bands' verdict on "principal reason" (l1's rule): true if the whole fraction band lies from MATERIALITY
    and the whole rank band (rounded outward) within MAX_REASONS, false if either lies outside. For the internal
    flag only."""
    r = _reason(lf, term)
    if isinstance(r, Verdict):
        return r
    if r.rank is None:
        return Verdict(FALSE, {"term": term, "fraction": 0.0}, "the model has no such term")
    f = interval(r.fraction)
    lo, hi = interval(r.rank)
    lo, hi = float(np.floor(lo)), float(np.ceil(hi))
    value = _judge(f[0] >= MATERIALITY and hi <= MAX_REASONS, f[1] < MATERIALITY or lo > MAX_REASONS)
    return Verdict(value, {"term": term, "fraction": r.fraction.value, "fraction band": f, "rank band": (lo, hi),
                           "materiality": MATERIALITY, "max reasons": MAX_REASONS})  # fmt: skip


def second_look(lf: LocalFacts) -> list[str]:
    """Why a reviewer should look at this decision, from the refit bands: the internal flag (empty: no flag). Never
    stated in the notice."""
    why = []
    if interval(lf.gap)[0] <= 0:
        why.append("the gap band reaches zero: a model fitted on another sample might approve")
    open_ = [t for t in principal_reasons(lf) if band_principal_reason(lf, t).value != TRUE]
    if open_:
        why.append("principal reasons the bands do not certify: " + ", ".join(open_))
    return why


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
