import pandas as pd
import pytest

from verifier_gate.experiments import recheck


def _summary(rows):
    """rows: (smoothing_rounds, interaction_smoothing_rounds, model misses, noise-feature share at n = 5,000)"""
    return pd.DataFrame(
        [
            {"smoothing_rounds": r, "interaction_smoothing_rounds": i, "max_bins": 1024, "model_misses": m,
             "noise feat. mean 5k": noise}
            for r, i, m, noise in rows
        ]
    )


@pytest.mark.parametrize(
    "challenger, expected",
    [
        ((75, 1000, 6, 0.018), recheck.CURRENT),  # 2 fewer misses: not clearly better
        ((75, 1000, 5, 0.018), {"smoothing_rounds": 75, "interaction_smoothing_rounds": 1000, "max_bins": 1024}),
        ((1000, 1000, 2, 0.025), recheck.CURRENT),  # fewer misses, but fits more noise
    ],
)
def test_decision_rule(challenger, expected):
    table = _summary([(0, 1000, 8, 0.018), challenger])
    assert recheck.decide(table) == expected


def test_decision_takes_the_fewest_misses_among_qualifying_settings():
    table = _summary([(0, 1000, 8, 0.018), (75, 1000, 5, 0.017), (0, 500, 4, 0.019), (1000, 1000, 1, 0.03)])
    assert recheck.decide(table) == {"smoothing_rounds": 0, "interaction_smoothing_rounds": 500, "max_bins": 1024}


def test_candidates_are_fresh_seeds_and_start_with_the_current_setting():
    from verifier_gate.data import dgp
    from verifier_gate.models.fit_ebm import EBM_PARAMS

    assert not set(recheck.SEEDS) & set(dgp.SEEDS)
    assert recheck.CANDIDATES[0] == recheck.CURRENT
    assert all(EBM_PARAMS[k] == v for k, v in recheck.CURRENT.items())
