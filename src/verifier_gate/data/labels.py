"""What the writer sees of each feature: its name in the handover and the DSL, and a short description.

The planted noise features must not be called noise in front of the writer: `noise_1` is our label for what we
planted, and it tells the writer the answer. D41 (plan §14.14): they are shown under plausible names of classic weak
application-scorecard variables, fixed before any LLM run (SYNTHETIC_NAMES). Any name brings the writer's priors,
whose direction we cannot control, so the pilot checks whether the names change the writer's behaviour against
opaque names (OPAQUE_NAMES), with a rule fixed in advance. The verifier works on the Facts' names; `internal` maps
the names the writer used back before verification.
"""

from collections.abc import Mapping

from verifier_gate.dsl.grammar import HEDGE, Claim
from verifier_gate.facts.steps import PAIR_SEPARATOR

SYNTHETIC_NAMES = {"noise_1": "months_at_address", "noise_2": "num_dependents"}  # D41
OPAQUE_NAMES = {"noise_1": "feature_a", "noise_2": "feature_b"}  # the pilot's naming check (D41)
SYNTHETIC_DESCRIPTIONS = {
    "utilization": "revolving credit utilization: the share of the credit limit in use (0 to 1)",
    "n_delinquencies": "number of past delinquencies on the credit file (0 to 6)",
    "income": "annual income in US dollars",
    "history_months": "length of the credit history in months",
    "dti": "debt-to-income ratio (0 to 0.6)",
    "n_inquiries": "number of recent credit inquiries",
    "age": "age of the applicant in years",
    "months_at_address": "months at the current address (standardised)",
    "num_dependents": "number of dependents (standardised)",
    "feature_a": "an application attribute (standardised)",
    "feature_b": "an application attribute (standardised)",
}
SYNTHETIC_LABELS = {  # how a sentence refers to the feature
    "utilization": "credit utilization",
    "n_delinquencies": "the number of past delinquencies",
    "income": "income",
    "history_months": "the length of credit history",
    "dti": "the debt-to-income ratio",
    "n_inquiries": "the number of recent inquiries",
    "age": "age",
    "months_at_address": "months at the current address",
    "num_dependents": "the number of dependents",
    "feature_a": "feature a",
    "feature_b": "feature b",
}


def shown(name: str, names: Mapping[str, str] = SYNTHETIC_NAMES) -> str:
    """The name the writer sees for a feature or a pair ("a & b")."""
    parts = [s.strip() for s in name.split(PAIR_SEPARATOR.strip())]
    return PAIR_SEPARATOR.join(names.get(part, part) for part in parts)


def internal(claim: Claim, names: Mapping[str, str] = SYNTHETIC_NAMES) -> Claim:
    """The claim with the writer's names mapped back to the Facts' names."""
    back = {v: k for k, v in names.items()}
    terms = tuple(shown(t, back) for t in claim.terms)
    inner = internal(claim.inner, names) if claim.kind == HEDGE else None
    return Claim(claim.kind, terms, claim.value, claim.relation, claim.sentence_id, inner)


def external(claim: Claim, names: Mapping[str, str] = SYNTHETIC_NAMES) -> Claim:
    """The claim with the Facts' names replaced by the writer's."""
    terms = tuple(shown(t, names) for t in claim.terms)
    inner = external(claim.inner, names) if claim.kind == HEDGE else None
    return Claim(claim.kind, terms, claim.value, claim.relation, claim.sentence_id, inner)
