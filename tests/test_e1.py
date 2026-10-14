"""E1's scorers (experiments/e1_lexicon.py) and the binding acceptance rule (experiments/acceptance_binding.py),
on hand-made verdict tables."""

import pandas as pd

from verifier_gate.dsl.grammar import Claim
from verifier_gate.experiments import acceptance_binding, e1_lexicon
from verifier_gate.lexicon.predicates import FALSE, TRUE, UNDECIDABLE as UND


def table(rows):
    """rows: (label, oracle, EBM, XGB2), one claim each, all in one dataset at n = 50,000."""
    out = pd.DataFrame(rows, columns=["label", "oracle", "EBM", "XGB2"])
    return out.assign(scenario="syn-none-n50000-s1", seed=1, n=50_000, interaction="none", **{"claim id": range(len(out))},
                      claim=[f"c{i}" for i in range(len(out))], kind="strength", set=False, role="weak")  # fmt: skip


def test_roles():
    assert e1_lexicon.role(Claim("strength", ("age",), "weak")) == "near_flat"
    assert e1_lexicon.role(Claim("negligible", ("noise_1",))) == "noise"
    assert e1_lexicon.role(Claim("interaction", ("a", "b"), "none")) == "pair"
    assert e1_lexicon.role(Claim("comparison", ("utilization", "income"), relation=">")) == "comparison"


def test_layers_score_the_model_against_the_oracle_on_claims_the_oracle_decides():
    t = table([(TRUE, TRUE, TRUE, FALSE), (TRUE, UND, TRUE, UND), (FALSE, FALSE, TRUE, FALSE)])
    long = e1_lexicon.layers(t)
    assert len(long[long.layer == "data"]) == 3
    assert len(long[(long.layer == "model") & (long.model == "EBM")]) == 2  # the oracle's undecidable claim is out
    assert len(long[(long.layer == "end to end") & (long.model == "XGB2")]) == 3
    model = long[(long.layer == "model") & (long.model == "EBM")]
    assert model.label.tolist() == [TRUE, FALSE] and model.verdict.tolist() == [TRUE, TRUE]


def test_end_to_end_errors_are_attributed_to_data_or_model():
    t = table([(FALSE, TRUE, TRUE, UND), (TRUE, UND, FALSE, TRUE), (FALSE, FALSE, TRUE, FALSE)])
    errors = e1_lexicon.end_to_end_errors(t)
    by = {(r.model, r.claim): (r.outcome, r.layer) for r in errors.itertuples()}
    assert by == {
        ("EBM", "c0"): ("released_wrong", "data"),  # the oracle makes the same error: the sample
        ("EBM", "c1"): ("blocked_correct", "model"),
        ("EBM", "c2"): ("released_wrong", "model"),  # the oracle refutes it: the model
    }


def test_binding_rule_counts_a_miss_only_where_the_oracle_is_true_and_the_model_false():
    t = table([(TRUE, TRUE, FALSE, TRUE), (TRUE, TRUE, UND, TRUE), (FALSE, FALSE, TRUE, FALSE), (TRUE, FALSE, UND, UND)])
    s = acceptance_binding.summarise(t)
    assert s.loc["EBM", "model misses (oracle true, model false)"] == 1 and not s.loc["EBM", "accepted"]
    assert s.loc["EBM", "model undecidable where the oracle is true"] == 1
    assert s.loc["EBM", "mirror (oracle false, model true), reported only"] == 1
    assert s.loc["XGB2", "accepted"]
    assert s.loc["XGB2", "data misses (label true, oracle false)"] == 1
