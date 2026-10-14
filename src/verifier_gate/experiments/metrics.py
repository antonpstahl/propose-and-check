"""Outcomes and metrics for three-valued verdicts against true/false labels (D31), shared by E1 to E3.

Each claim ends in one of five outcomes, named for what the gate does with its verdict (D30: only a true
verdict is released as stated):

| label | verdict     | outcome         |                                                          |
|-------|-------------|-----------------|----------------------------------------------------------|
| true  | true        | certified       | released, correct                                        |
| false | false       | refuted         | blocked, correct                                         |
| false | true        | released_wrong  | the error that matters: a wrong statement is released    |
| true  | false       | blocked_correct | the cost: a correct statement is held back               |
| any   | undecidable | abstained       | not released as stated: repaired, dropped or hedged      |

For a group of claims: the decided rate (coverage), the accuracy among decided claims, the confident-error
rate with a one-sided upper bound, and the two errors apart, each among the claims it can happen to:
released_wrong among the false claims, blocked_correct among the true ones. Groups are compared as
risk-coverage pairs (selective prediction): deciding more is better only if it does not err more. Between
two sets of verdicts on the same claims, the oracle's and a model's (the model layer of E1, D12), the 3 x 3
table of verdicts; a model miss (D24) is its cell oracle true, model false.

Claims within one dataset are not independent. The bounds here treat them as if they were, so they are
optimistic; E1 adds bootstrap intervals clustered by dataset.
"""

import math
from collections.abc import Sequence

import pandas as pd
from scipy import stats

from verifier_gate.lexicon.predicates import FALSE, TRUE, UNDECIDABLE

CERTIFIED, REFUTED, RELEASED_WRONG, BLOCKED_CORRECT, ABSTAINED = "certified", "refuted", "released_wrong", "blocked_correct", "abstained"
OUTCOMES = (CERTIFIED, REFUTED, RELEASED_WRONG, BLOCKED_CORRECT, ABSTAINED)
VERDICTS = (TRUE, FALSE, UNDECIDABLE)


def outcome(label: str, verdict: str) -> str:
    if label not in (TRUE, FALSE):
        raise ValueError(f"a label is true or false, not {label!r}")
    if verdict not in VERDICTS:
        raise ValueError(f"not a verdict: {verdict!r}")
    if verdict == UNDECIDABLE:
        return ABSTAINED
    if verdict == label:
        return CERTIFIED if label == TRUE else REFUTED
    return RELEASED_WRONG if verdict == TRUE else BLOCKED_CORRECT


def upper_bound(errors: int, n: int, level: float = 0.95) -> float:
    """One-sided upper confidence bound for a rate seen `errors` times in n (Clopper-Pearson). With no errors
    it is 1 - (1 - level) ** (1 / n), about 3 / n at 95% (the rule of three)."""
    if n == 0:
        return math.nan
    if errors >= n:
        return 1.0
    return float(stats.beta.ppf(level, errors + 1, n - errors))


def _rate(k: int, n: int) -> float:
    return k / n if n else math.nan


def summary(labels: Sequence[str], verdicts: Sequence[str]) -> dict[str, float]:
    """D31's numbers for one group of claims."""
    outcomes = [outcome(label, verdict) for label, verdict in zip(labels, verdicts, strict=True)]
    count = {o: outcomes.count(o) for o in OUTCOMES}
    n = len(outcomes)
    true_claims = sum(label == TRUE for label in labels)
    false_claims = n - true_claims
    decided = n - count[ABSTAINED]
    errors = count[RELEASED_WRONG] + count[BLOCKED_CORRECT]
    return {
        "claims": n, "true claims": true_claims, "false claims": false_claims, **count,
        "decided rate": _rate(decided, n),
        "accuracy among decided": _rate(decided - errors, decided),
        "confident-error rate": _rate(errors, n),
        "confident-error upper bound": upper_bound(errors, n),
        "certified among true claims": _rate(count[CERTIFIED], true_claims),  # what a writer can say
        "released wrong among false claims": _rate(count[RELEASED_WRONG], false_claims),
        "released wrong upper bound": upper_bound(count[RELEASED_WRONG], false_claims),
        "blocked among true claims": _rate(count[BLOCKED_CORRECT], true_claims),
    }  # fmt: skip


def summarize(claims: pd.DataFrame, by: Sequence[str], label: str = "label", verdict: str = "verdict") -> pd.DataFrame:
    """summary() for each group of a table with one row per claim."""
    rows = []
    for key, group in claims.groupby(list(by), sort=True):
        key = key if isinstance(key, tuple) else (key,)
        rows.append(dict(zip(by, key)) | summary(group[label].tolist(), group[verdict].tolist()))
    return pd.DataFrame(rows).set_index(list(by))


def cross_table(reference: Sequence[str], model: Sequence[str]) -> pd.DataFrame:
    """Counts of (reference verdict, model verdict) on the same claims, all nine cells."""
    table = pd.DataFrame(0, index=pd.Index(VERDICTS, name="reference"), columns=pd.Index(VERDICTS, name="model"))
    for r, m in zip(reference, model, strict=True):
        if r not in VERDICTS or m not in VERDICTS:
            raise ValueError(f"not a pair of verdicts: {r!r}, {m!r}")
        table.loc[r, m] += 1
    return table
