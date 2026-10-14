import pytest

from verifier_gate.dsl.grammar import Claim
from verifier_gate.dsl.parse import DSLError, parse

VALID = {
    'rank("utilization") == 1': Claim("rank", ("utilization",), 1),
    'share("utilization") == approx(0.31)': Claim("share", ("utilization",), 0.31),
    'share("utilization & n_delinquencies") == approx(0.2)': Claim("share", ("utilization & n_delinquencies",), 0.2),
    'direction("income") == "mostly_decreasing"': Claim("direction", ("income",), "mostly_decreasing"),
    'strength("age") == "weak"': Claim("strength", ("age",), "weak"),
    'negligible("noise_1")': Claim("negligible", ("noise_1",)),
    'effect("utilization") > effect("income")': Claim("comparison", ("utilization", "income"), relation=">"),
    'effect("age") < effect("dti")': Claim("comparison", ("age", "dti"), relation="<"),
    'threshold("dti", at=0.43)': Claim("threshold", ("dti",), 0.43),
    'peak("history_months", at=36)': Claim("peak", ("history_months",), 36.0),
    'peak("noise_1", at=-1.5)': Claim("peak", ("noise_1",), -1.5),
    'interaction("utilization", "n_delinquencies", pattern="amplification")': Claim(
        "interaction", ("utilization", "n_delinquencies"), "amplification"
    ),
    # sets of values (D33), stored in their canonical order
    'strength("age") in ("negligible", "weak")': Claim("strength", ("age",), ("negligible", "weak")),
    'strength("dti") in ("moderate", "weak")': Claim("strength", ("dti",), ("weak", "moderate")),
    'rank("income") in (3, 2)': Claim("rank", ("income",), (2, 3)),
    'rank("income") in (1, 2, 3)': Claim("rank", ("income",), (1, 2, 3)),
    'direction("history_months") in ("mostly_decreasing", "decreasing")': Claim(
        "direction", ("history_months",), ("decreasing", "mostly_decreasing")
    ),
    # the hedge (D30)
    'unsettled(strength("n_inquiries") == "weak")': Claim(
        "unsettled", ("n_inquiries",), inner=Claim("strength", ("n_inquiries",), "weak")
    ),
    'unsettled(interaction("a", "b", pattern="sign_flip"))': Claim(
        "unsettled", ("a", "b"), inner=Claim("interaction", ("a", "b"), "sign_flip")
    ),
}


@pytest.mark.parametrize("line", list(VALID))
def test_valid_lines_parse_and_round_trip(line):
    claim = parse(line)
    assert claim == VALID[line]
    assert parse(str(claim)) == claim


def test_sentence_id_is_attached():
    assert parse('negligible("age")', sentence_id=3).sentence_id == 3
    hedge = parse('unsettled(negligible("age"))', sentence_id=2)
    assert hedge.sentence_id == 2 and hedge.inner.sentence_id is None


REJECTED = [
    '__import__("os").system("ls")',
    'rank("utilization").real == 1',
    'rank(utilization) == 1',  # a name, not a string
    'rank("utilization") == 0',
    'rank("utilization") == 1.0',
    'rank("utilization") == True',
    'rank("utilization") > 1',
    'share("utilization") == 0.31',  # needs approx()
    'share("utilization") == approx(1.5)',
    'share("utilization") == approx(x=0.3)',
    'direction("income") == "falls"',
    'strength("age") == "negligible"',  # negligible has its own claim
    'negligible("age", "income")',
    'negligible("")',
    'effect("a") == effect("b")',
    'effect("a") > effect("b") > effect("c")',
    'threshold("dti", 0.43)',  # at= is required
    'threshold("dti", at="0.43")',
    'threshold("dti", at=0.43, width=1)',
    'interaction("a", "b", "amplification")',
    'interaction("a", "b", pattern="synergy")',
    'interaction("a", "a", pattern="none")',
    'lambda: 1',
    'rank("a") == 1; negligible("b")',
    'print("x")',
    '[negligible("a")]',
    'negligible(**{"t": "a"})',
    # sets of values (D33)
    'strength("age") in ("weak",)',  # a set holds at least two values
    'strength("age") in ("weak", "strong")',  # not neighbours
    'strength("age") in ("negligible", "weak", "moderate", "strong")',  # every class: says nothing
    'strength("age") in ("weak", "weak")',
    'strength("age") in ("weak", "faint")',
    'strength("age") in ["weak", "moderate"]',  # a set is a tuple
    'strength("age") not in ("weak", "moderate")',
    'rank("income") in (2, 4)',
    'rank("income") in (0, 1)',
    'rank("income") in (2.0, 3.0)',
    'direction("income") in ("decreasing", "increasing")',
    'direction("income") in ("decreasing", "mostly_increasing")',
    'share("income") in (0.1, 0.2)',
    # the hedge (D30)
    'unsettled(unsettled(negligible("age")))',
    'unsettled("age")',
    'unsettled(negligible("age"), negligible("dti"))',
    'unsettled(claim=negligible("age"))',
    'unsettled()',
]


@pytest.mark.parametrize("line", REJECTED)
def test_anything_outside_the_whitelist_is_rejected(line):
    with pytest.raises(DSLError):
        parse(line)
