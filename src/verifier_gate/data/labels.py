"""What the writer sees of each feature: its name in the handover and the DSL, and a short description.

The planted noise features must not be called noise in front of the writer: `noise_1` is our label for what we
planted, and it tells the writer the answer. D41 (plan §14.14): they are shown under plausible names of classic weak
application-scorecard variables, fixed before any LLM run (SYNTHETIC_NAMES). Any name brings the writer's priors,
whose direction we cannot control, so the pilot checks whether the names change the writer's behaviour against
opaque names (OPAQUE_NAMES), with a rule fixed in advance. The verifier works on the Facts' names; `internal` maps
the names the writer used back before verification.

The plasmode tier (D54, plan §14.23) keeps the TaiwanCredit column codes as names (`PAY_0`, `BILL_AMT1`, ...), each
with its data-dictionary description (Yeh and Lien 2009, UCI), the month's place added so that a reader can tell
`BILL_AMT1` from `BILL_AMT2`, and plain words in sentences (PLASMODE_LABELS): how a bank's model documentation
names features. None of the names tells which column has no planted effect. Since D74, the codes the data dictionary
does not document (PAY_0's -2 and 0, EDUCATION's 0, 5 and 6) are described as such; D66 and D67 ran with D54's text.
"""

from collections.abc import Mapping

from verifier_gate.dsl.grammar import HEDGE, Claim
from verifier_gate.facts.steps import PAIR_SEPARATOR
from verifier_gate.lexicon.predicates import d74_fixes

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


PLASMODE_DESCRIPTIONS_D54 = {  # D54: the data dictionary of TaiwanCredit, with the month's place (D66 and D67 ran with it)
    "PAY_0": "repayment status in September 2005, the latest month (-2 no consumption, -1 paid in full, 0 revolving credit used, 1 to 9 months of payment delay)",
    "LIMIT_BAL": "amount of the given credit in NT dollars, individual and family (supplementary) credit",
    "BILL_AMT1": "amount of the bill statement in September 2005, the latest month, in NT dollars",
    "BILL_AMT2": "amount of the bill statement in August 2005, the month before, in NT dollars",
    "PAY_AMT1": "amount paid in September 2005, the latest month, in NT dollars",
    "PAY_AMT2": "amount paid in August 2005, the month before, in NT dollars",
    "PAY_AMT3": "amount paid in July 2005, two months before, in NT dollars",
    "AGE": "age in years",
    "EDUCATION": "education (1 graduate school, 2 university, 3 high school, 4 others; 0, 5 and 6 unknown)",
}
PLASMODE_DESCRIPTIONS_D74 = PLASMODE_DESCRIPTIONS_D54 | {  # D74 (review minor issue 36): undocumented codes marked
    "PAY_0": "repayment status in September 2005, the latest month (-1 paid in full, 1 to 9 months of payment delay; "
             "-2 and 0 are not in the data dictionary, commonly read as no consumption and revolving credit used)",
    "EDUCATION": "education (1 graduate school, 2 university, 3 high school, 4 others; 0, 5 and 6 are not in the data dictionary)",
}  # fmt: skip


def plasmode_descriptions() -> dict[str, str]:
    """D74's descriptions, or D54's where D74's fixes are off (a replay of D66 or D67, or the v2 pin)."""
    return PLASMODE_DESCRIPTIONS_D74 if d74_fixes() else PLASMODE_DESCRIPTIONS_D54


PLASMODE_DESCRIPTIONS = plasmode_descriptions()  # read as the process starts: the switches are environment variables
PLASMODE_LABELS = {  # how a sentence refers to the feature
    "PAY_0": "the latest repayment status",
    "LIMIT_BAL": "the credit limit",
    "BILL_AMT1": "the latest bill amount",
    "BILL_AMT2": "the bill amount of the month before",
    "PAY_AMT1": "the latest payment",
    "PAY_AMT2": "the payment of the month before",
    "PAY_AMT3": "the payment two months before",
    "AGE": "age",
    "EDUCATION": "the education level",
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
