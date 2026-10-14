"""Outcomes and metrics for three-valued verdicts (D31, experiments/metrics.py)."""

import math

import pandas as pd
import pytest

from verifier_gate.experiments import metrics as m
from verifier_gate.lexicon.predicates import FALSE, TRUE, UNDECIDABLE


def test_outcomes_follow_what_the_gate_does_with_the_verdict():
    assert m.outcome(TRUE, TRUE) == m.CERTIFIED
    assert m.outcome(FALSE, FALSE) == m.REFUTED
    assert m.outcome(FALSE, TRUE) == m.RELEASED_WRONG
    assert m.outcome(TRUE, FALSE) == m.BLOCKED_CORRECT
    assert m.outcome(TRUE, UNDECIDABLE) == m.outcome(FALSE, UNDECIDABLE) == m.ABSTAINED
    with pytest.raises(ValueError):
        m.outcome(UNDECIDABLE, TRUE)  # labels are two-valued
    with pytest.raises(ValueError):
        m.outcome(TRUE, "maybe")


def test_summary_counts_and_rates():
    labels = [TRUE] * 6 + [FALSE] * 4
    verdicts = [TRUE, TRUE, TRUE, FALSE, UNDECIDABLE, UNDECIDABLE] + [FALSE, FALSE, TRUE, UNDECIDABLE]
    s = m.summary(labels, verdicts)
    assert (s["certified"], s["blocked_correct"], s["refuted"], s["released_wrong"], s["abstained"]) == (3, 1, 2, 1, 3)
    assert s["decided rate"] == pytest.approx(0.7)
    assert s["accuracy among decided"] == pytest.approx(5 / 7)
    assert s["confident-error rate"] == pytest.approx(0.2)
    assert s["certified among true claims"] == pytest.approx(0.5)
    assert s["released wrong among false claims"] == pytest.approx(0.25)
    assert s["blocked among true claims"] == pytest.approx(1 / 6)


def test_upper_bound_without_errors_is_the_rule_of_three():
    assert m.upper_bound(0, 1035) == pytest.approx(1 - 0.05 ** (1 / 1035))
    assert m.upper_bound(0, 1035) == pytest.approx(3 / 1035, rel=0.01)
    assert m.upper_bound(5, 100) > 0.05
    assert m.upper_bound(100, 100) == 1.0
    assert math.isnan(m.upper_bound(0, 0))


def test_summarize_by_group():
    claims = pd.DataFrame({"n": [5000, 5000, 50000], "label": [TRUE, FALSE, TRUE], "verdict": [TRUE, UNDECIDABLE, TRUE]})
    table = m.summarize(claims, ["n"])
    assert table.loc[5000, "decided rate"] == 0.5
    assert table.loc[50000, "certified"] == 1


def test_cross_table_has_all_nine_cells():
    table = m.cross_table([TRUE, TRUE, UNDECIDABLE], [FALSE, TRUE, TRUE])
    assert table.shape == (3, 3) and table.to_numpy().sum() == 3
    assert table.loc[TRUE, FALSE] == 1  # a model miss (D24): oracle true, model false
    with pytest.raises(ValueError):
        m.cross_table([TRUE], ["maybe"])
