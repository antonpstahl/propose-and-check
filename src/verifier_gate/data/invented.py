"""The held-out invented features of text-level E2 (review of 20 Oct, M5 fix 3): quantities the models do not have,
named in words extractor x4's development never saw.

Text-level E2 used one invented term, "the savings balance", in every M9 mutant (543 synthetic, 174 plasmode), and
x4 was written after x3 missed it and is scored on the same mutants: its 85% is in-sample. These terms were fixed on
20 Oct, before any extractor read them. Three kinds:

- near-synonym: a different quantity whose words come close to a feature of the tier (`neighbour`). The outcome a
  validator fears most is the extractor writing the claim on the neighbour: the verifier then checks a real
  feature, and a statement about a quantity the model does not have can be certified. On the plasmode tier three
  are TaiwanCredit columns the model leaves out (PAY_2, BILL_AMT3, PAY_AMT4), one month off a column it has.
- unrelated: a plausible application variable close to no feature, as "the savings balance" was.
- paraphrase: the neighbour itself in other words, a control. It must be read as its feature; a rule that blocks
  every unknown term pays here.

Every near-synonym's neighbour also has a paraphrase, placed on the same clauses (experiments/e2_heldout.py), so the
line x4's prompt draws, "the same quantity in other words" against "a related but different quantity", is measured
from both sides.

`seen`: where x4's development met the term; empty for a held-out term. Two are kept as anchors and reported apart:
"the savings balance" (E2's M9 term, and the term of x4's first live check) and "the length of employment" (x4's
prompt gives it as its example of a related but different quantity; notebooks/04_x4_heldout.py). Held-out terms
avoid what x4 saw: employment, savings, open accounts and credit cards, the loan amount, term and purpose, home
ownership, missed payments (tests/test_e2_heldout.py checks the prompts and the probe).

`cue`: a pattern (case-insensitive) that a sentence naming the term matches, longest form first: it checks the
LLM-written rewrites and the held-out property.
"""

from dataclasses import dataclass

KINDS = ("near-synonym", "unrelated", "paraphrase")


@dataclass(frozen=True)
class Term:
    name: str  # snake_case, as x4's rule names a feature the list does not have; a key, never a feature of the tier
    words: str  # how a sentence names it
    tier: str
    kind: str
    neighbour: str | None  # near-synonym: the feature it comes close to; paraphrase: the feature it names (Facts names:
    # noise_1 and noise_2 are shown as months_at_address and num_dependents, D41)
    cue: str
    seen: str = ""
    why: str = ""  # near-synonym: how it differs from its neighbour

    @property
    def held_out(self) -> bool:
        return not self.seen


S, P = "synthetic", "plasmode"
TERMS = (
    # synthetic: near-synonyms
    Term("revolving_balance", "the revolving balance", S, "near-synonym", "utilization", r"revolving balance",
         why="an amount owed, in dollars; utilization is the share of the limit in use"),
    Term("months_since_last_delinquency", "the months since the last delinquency", S, "near-synonym", "n_delinquencies",
         r"(months|time) since the (last|most recent|latest) delinquen", why="how recent the last delinquency is, not how many"),
    Term("co_applicants_income", "the co-applicant's income", S, "near-synonym", "income",
         r"co-?applicant(?:'s)? (annual |yearly )?income|income of (the|a) co-?applicant|co-?applicant", why="another person's income"),
    Term("age_of_newest_account", "the age of the newest account", S, "near-synonym", "history_months",
         r"age of (the|their|an applicant's) newest account|newest account'?s age|newest account",
         why="the time since the latest account was opened; the credit history runs from the oldest (and its words hold \"age\")"),
    Term("loan_to_value_ratio", "the loan-to-value ratio", S, "near-synonym", "dti", r"loan.to.value",
         why="a loan against the value of the collateral, not debt against income"),
    Term("number_of_declined_credit_applications", "the number of declined credit applications", S, "near-synonym", "n_inquiries",
         r"declined", why="applications turned down; an inquiry counts whether or not credit was granted"),
    Term("months_at_previous_address", "the months at the previous address", S, "near-synonym", "noise_1",
         r"previous address", why="the address before the current one"),
    Term("household_size", "the household size", S, "near-synonym", "noise_2", r"household",
         why="every member, the applicant and other earners included"),
    # synthetic: unrelated
    Term("down_payment", "the down payment", S, "unrelated", None, r"down.?payment"),
    Term("monthly_rent", "the monthly rent", S, "unrelated", None, r"\brent\b"),
    # synthetic: the anchors x4's development saw
    Term("savings_balance", "the savings balance", S, "unrelated", None, r"savings",
         seen="E2's M9 term in every script mutant; x4's first draft was checked live on three E2 texts with it"),
    Term("length_of_employment", "the length of employment", S, "near-synonym", "history_months", r"employ",
         seen="x4's prompt gives it as the example of a related but different quantity; notebooks/04_x4_heldout.py",
         why="time in the current job, not on the credit file"),
    # synthetic: paraphrases, one per neighbour
    Term("fraction_of_the_credit_limit_in_use", "the fraction of the credit limit in use", S, "paraphrase", "utilization",
         r"fraction of the credit limit"),
    Term("number_of_times_the_applicant_was_delinquent", "the number of times the applicant was delinquent", S, "paraphrase",
         "n_delinquencies", r"times the applicant was delinquent"),
    Term("applicants_yearly_earnings", "the applicant's yearly earnings", S, "paraphrase", "income", r"yearly earnings"),
    Term("age_of_the_credit_file", "the age of the credit file", S, "paraphrase", "history_months", r"age of the credit file"),
    Term("ratio_of_debt_payments_to_income", "the ratio of debt payments to income", S, "paraphrase", "dti", r"debt payments to income"),
    Term("number_of_recent_hard_credit_checks", "the number of recent hard credit checks", S, "paraphrase", "n_inquiries",
         r"hard credit checks?"),
    Term("time_lived_at_the_current_address", "the time lived at the current address", S, "paraphrase", "noise_1",
         r"lived at the current address"),
    Term("number_of_people_the_applicant_supports", "the number of people the applicant supports", S, "paraphrase", "noise_2",
         r"people the applicant supports"),
    # plasmode (TaiwanCredit): near-synonyms
    Term("repayment_status_of_the_month_before", "the repayment status of the month before", P, "near-synonym", "PAY_0",
         r"repayment status (of|in) the month before", why="August 2005's status (PAY_2, not in the model); the model has September's"),
    Term("bill_amount_two_months_before", "the bill amount two months before", P, "near-synonym", "BILL_AMT2",
         r"bill amount two months before", why="July 2005's bill (BILL_AMT3, not in the model); the model has August's and September's"),
    Term("payment_three_months_before", "the payment three months before", P, "near-synonym", "PAY_AMT3",
         r"payment three months before", why="June 2005's payment (PAY_AMT4, not in the model); the model has July's to September's"),
    Term("available_credit", "the available credit", P, "near-synonym", "LIMIT_BAL", r"available credit",
         why="the limit minus what is owed; LIMIT_BAL is the limit"),
    Term("minimum_payment_due", "the minimum payment due", P, "near-synonym", "PAY_AMT1", r"minimum payment",
         why="what the bank asks for, not what was paid"),
    # plasmode: unrelated
    Term("number_of_years_with_the_bank", "the number of years with the bank", P, "unrelated", None, r"years with the bank"),
    # plasmode: paraphrases, one per neighbour (the months from the data dictionary, data/labels.py)
    Term("repayment_status_in_september_2005", "the repayment status in September 2005", P, "paraphrase", "PAY_0",
         r"repayment status in september"),
    Term("bill_amount_in_august_2005", "the bill amount in August 2005", P, "paraphrase", "BILL_AMT2", r"bill amount in august"),
    Term("amount_paid_in_july_2005", "the amount paid in July 2005", P, "paraphrase", "PAY_AMT3", r"paid in july"),
    Term("amount_of_credit_given", "the amount of credit given", P, "paraphrase", "LIMIT_BAL", r"credit given"),
    Term("amount_paid_in_september_2005", "the amount paid in September 2005", P, "paraphrase", "PAY_AMT1", r"paid in september"),
)  # fmt: skip


def of(tier: str) -> tuple[Term, ...]:
    return tuple(t for t in TERMS if t.tier == tier)


def term(name: str) -> Term:
    return next(t for t in TERMS if t.name == name)


def table() -> list[dict]:
    """The terms as rows (results/e2/heldout/set/terms.csv)."""
    return [{"tier": t.tier, "term": t.name, "words": t.words, "kind": t.kind, "neighbour": t.neighbour or "", "held out": t.held_out,
             "seen": t.seen, "why": t.why, "cue": t.cue} for t in TERMS]  # fmt: skip
