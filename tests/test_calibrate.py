"""The calibration rule of plan §14.9 (experiments/calibrate.py), tested on fake evaluations before it runs."""

from dataclasses import fields
from types import SimpleNamespace

import numpy as np
import pandas as pd

from verifier_gate.experiments import calibrate as c
from verifier_gate.experiments import metrics
from verifier_gate.lexicon import predicates as p
from verifier_gate.lexicon.predicates import FALSE, TRUE, UNDECIDABLE

V0 = p.load()


def fake(passes, implicated=("detectable_mass",)):
    """evaluate() for decide(): passes(lex) says whether the lexicon passes; v0's failures implicate `implicated`."""
    tried = []

    def evaluate(lex):
        tried.append(lex)
        return SimpleNamespace(passed=passes(lex), implicated=implicated)

    return evaluate, tried


def test_nothing_moves_when_v0_passes():
    evaluate, tried = fake(lambda lex: True)
    v1, _ = c.decide(V0, evaluate)
    assert v1 == V0 and tried == [V0]


def test_an_implicated_threshold_moves_up_one_grid_step_at_a_time():
    evaluate, tried = fake(lambda lex: lex.detectable_mass >= 0.20)
    v1, _ = c.decide(V0, evaluate)
    assert [lex.detectable_mass for lex in tried] == [V0.detectable_mass, 0.10, 0.20]
    assert v1.detectable_mass == 0.20 and v1.exception_mass == V0.exception_mass


def test_v1_keeps_v0_when_no_grid_value_passes():
    evaluate, tried = fake(lambda lex: False)
    v1, _ = c.decide(V0, evaluate)
    assert v1 == V0 and len(tried) == 1 + len(c.GRID["detectable_mass"])


def test_a_failure_that_implicates_no_threshold_moves_nothing():
    evaluate, tried = fake(lambda lex: lex != V0, implicated=())
    v1, _ = c.decide(V0, evaluate)
    assert v1 == V0 and tried == [V0]


def test_two_implicated_thresholds_take_the_fewest_steps_that_pass():
    evaluate, _ = fake(lambda lex: lex.detectable_mass > V0.detectable_mass and lex.exception_mass > V0.exception_mass,
                       implicated=("detectable_mass", "exception_mass"))  # fmt: skip
    v1, _ = c.decide(V0, evaluate)
    assert (v1.detectable_mass, v1.exception_mass) == (0.10, 0.125)


def test_the_grid_only_moves_up_and_stays_above_t_s_history_exception():
    for name, grid in c.GRID.items():
        assert all(v > getattr(V0, name) for v in grid)
    assert min(c.GRID["exception_mass"]) > 0.0894  # largest on seed 1, measured on T before the rule (§14.9)


def test_the_sweep_covers_every_threshold_but_the_level_and_the_search_region():
    names = {f.name for f in fields(p.Lexicon)} - {"version", "level", "search", "strength"} | set(p.STRENGTHS)
    assert set(c.SWEEP) == names


def test_scaled_changes_one_threshold():
    lex = c.scaled(V0, "weak", 0.5)
    assert lex.strength["weak"] == V0.strength["weak"] * 0.5 and lex.strength["moderate"] == V0.strength["moderate"]
    lex = c.scaled(V0, "exception_mass", 1.5)
    assert lex.exception_mass == V0.exception_mass * 1.5 and lex.detectable_mass == V0.detectable_mass
    for name in c.SWEEP:
        for factor in c.FACTORS:
            changed = {k for k, v in c.thresholds(c.scaled(V0, name, factor)).items() if v != c.thresholds(V0)[k]}
            assert changed == {name}


def evaluation(noise, oracle, label_changes=0, history=0.0894):
    columns = ["n", "claim", "label", "verdict", "exception mass"]
    oracle = pd.DataFrame(oracle, columns=columns)
    oracle["outcome"] = [metrics.outcome(label, verdict) for label, verdict in zip(oracle.label, oracle.verdict)]
    noise = pd.DataFrame(noise, columns=["test", "verdict", "band only"])
    return c.Evaluation(V0, noise, oracle, label_changes, history)


CLEAN_NOISE = [("effect", FALSE, False), ("at most", TRUE, False), ("direction (reported)", TRUE, False)]
CLEAN_ORACLE = [(50_000, 'negligible("noise_1")', TRUE, TRUE, np.nan), (5_000, 'rank("age") == 7', TRUE, FALSE, np.nan)]


def test_criteria_read_the_noise_curves_and_the_oracle_at_n_50000_only():
    e = evaluation(CLEAN_NOISE, CLEAN_ORACLE)  # an error at n = 5,000 and a noise direction are reported only
    assert e.passed and e.implicated == ()
    e = evaluation(CLEAN_NOISE + [("effect", TRUE, True)], CLEAN_ORACLE)
    assert not e.criteria["1 noise never an effect"] and e.implicated == ("detectable_mass",)
    e = evaluation(CLEAN_NOISE + [("at most", FALSE, False)], CLEAN_ORACLE)  # detectable through its net change
    assert not e.criteria["2 noise never refuted as negligible"] and e.implicated == ()
    e = evaluation(CLEAN_NOISE + [("effect", UNDECIDABLE, True)], CLEAN_ORACLE)
    assert e.passed


def test_only_a_mostly_error_above_the_exception_mass_implicates_it():
    error = (50_000, 'direction("history_months") == "mostly_decreasing"', TRUE, FALSE, 0.11)
    e = evaluation(CLEAN_NOISE, CLEAN_ORACLE + [error])
    assert not e.criteria["3 oracle no confident error at n = 50,000"] and e.implicated == ("exception_mass",)
    within = error[:4] + (0.05,)  # refuted for another reason: nothing to move
    assert evaluation(CLEAN_NOISE, CLEAN_ORACLE + [within]).implicated == ()


def test_the_guard_rail():
    assert not evaluation(CLEAN_NOISE, CLEAN_ORACLE, label_changes=1).criteria["guard rail"]
    assert not evaluation(CLEAN_NOISE, CLEAN_ORACLE, history=0.10).criteria["guard rail"]  # not above T's
