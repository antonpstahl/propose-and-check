import numpy as np
import pandas as pd
import pytest
from scipy.special import expit

from verifier_gate.data import dgp
from verifier_gate.experiments.acceptance import STRENGTH


@pytest.fixture(scope="module")
def big():
    return dgp.sample_features(400_000, np.random.default_rng(123))


def conditional_effect(truth, pair, feature, lo, hi, moderator, value):
    """Effect of feature (main + pair) from lo to hi, with the moderator held at value."""
    X = pd.DataFrame({feature: [lo, hi], moderator: [value, value]})
    total = truth.term(feature, X) + truth.term(pair, X)
    return total[1] - total[0]


def test_grid_has_18_scenarios():
    assert len({s.id for s in dgp.SCENARIOS}) == 18
    assert sum(s.is_discovery for s in dgp.SCENARIOS) == 6


def test_generate_is_deterministic():
    scenario = dgp.Scenario("weak", 5_000, 2)
    a, b = dgp.generate(scenario), dgp.generate(scenario)
    pd.testing.assert_frame_equal(a.X, b.X)
    np.testing.assert_array_equal(a.y, b.y)


def test_common_random_numbers_across_n_and_levels():
    small = dgp.generate(dgp.Scenario("none", 5_000, 1))
    large = dgp.generate(dgp.Scenario("none", 50_000, 1))
    dominant = dgp.generate(dgp.Scenario("dominant", 5_000, 1))
    pd.testing.assert_frame_equal(small.X, large.X.iloc[:5_000])
    np.testing.assert_array_equal(small.y, large.y[:5_000])
    pd.testing.assert_frame_equal(small.X, dominant.X)


@pytest.mark.parametrize("interaction", dgp.INTERACTION_LEVELS)
def test_truth_is_centred_and_reproduces_the_planted_logit(interaction):
    data = dgp.generate(dgp.Scenario(interaction, 5_000, 1))
    for values in data.truth.terms(data.X).values():
        assert abs(values.mean()) < 1e-12
    planted = dgp.base_intercept(interaction) + sum(
        dgp._population_term(t, data.X, interaction) for t in dgp.TERMS
    )
    np.testing.assert_allclose(data.truth.logit(data.X), planted, atol=1e-12)


@pytest.mark.parametrize("interaction", dgp.INTERACTION_LEVELS)
def test_shares_and_base_rate_hit_targets(big, interaction):
    truth = dgp.make_truth(big, interaction)
    shares = truth.shares(big)
    pair_shares = dgp.PAIR_SHARES[interaction]
    main_scale = 1.0 - sum(pair_shares.values())
    for feature in dgp.FEATURES:
        assert shares[feature] == pytest.approx(dgp.MAIN_SHARES[feature] * main_scale, abs=0.003)
    for pair, share in pair_shares.items():
        assert shares[pair] == pytest.approx(share, abs=0.003)
    assert expit(truth.logit(big)).mean() == pytest.approx(dgp.BASE_RATE, abs=0.003)


@pytest.mark.parametrize("interaction", dgp.INTERACTION_LEVELS)
def test_strength_classes_and_ranks_hold_at_every_level(big, interaction):
    # lexicon v0 bands: strong >= 15%, moderate 5-15%, weak < 5%, negligible < 2%
    shares = dgp.make_truth(big, interaction).shares(big)
    assert shares["utilization"] >= 0.15 and shares["n_delinquencies"] >= 0.15
    for feature in ("income", "history_months", "dti"):
        assert 0.05 <= shares[feature] < 0.15
    assert 0.02 <= shares["n_inquiries"] < 0.05
    assert shares["age"] < 0.02
    assert shares["noise_1"] == shares["noise_2"] == 0.0
    ordered = ["utilization", "n_delinquencies", "income", "history_months", "dti", "n_inquiries", "age"]
    for higher, lower in zip(ordered, ordered[1:]):
        assert shares[higher] > 1.2 * shares[lower]


@pytest.mark.parametrize("interaction", dgp.INTERACTION_LEVELS)
def test_every_share_sits_inside_its_strength_band(big, interaction):
    # unambiguous truth: about one point or more from the nearest band edge, at every level
    edges = [lower for _, lower in STRENGTH]
    for term, share in dgp.make_truth(big, interaction).shares(big).items():
        if share > 0:
            assert min(abs(share - edge) for edge in edges) > 0.008, (term, share)


@pytest.mark.parametrize("pair", list(dgp.PAIR_FACTORS))
def test_pairs_are_pure_in_the_population(pair):
    ref = dgp._reference()
    (a, b), _ = dgp.PAIR_FACTORS[pair]
    truth = dgp.Truth("dominant", 0.0, dict.fromkeys(dgp.TERMS, 0.0))
    scale = np.abs(truth.term(pair, ref)).mean()
    for fixed, varied in ((a, b), (b, a)):
        for value in np.quantile(ref[fixed], [0.05, 0.5, 0.95]):
            X = {fixed: np.full(len(ref), value), varied: ref[varied]}
            assert abs(truth.term(pair, X).mean()) < 1e-9 * scale


def test_main_shapes():
    truth = dgp.make_truth(dgp._reference(), "none")

    u = np.linspace(0.0, 1.0, 101)
    slopes = np.diff(truth.term("utilization", {"utilization": u}))
    assert np.all(slopes > 0)
    assert slopes[80] == pytest.approx(6.0 * slopes[20])

    h = np.arange(6.0, 361.0)
    history = truth.term("history_months", {"history_months": h})
    assert abs(h[np.argmax(history)] - 36.0) <= 2.0
    assert history.max() - history[0] > 0.25  # the bump clearly beats the left edge (was 0.04 logits)
    rising = np.mean(np.diff(history) > 0)  # history is uniform, so share of months = share of data mass
    assert 0.0 < rising < 0.08  # "mostly decreasing" (threshold 10%) with a margin

    dti = np.linspace(0.0, 0.6, 601)
    jumps = np.flatnonzero(np.abs(np.diff(truth.term("dti", {"dti": dti}))) > 1e-12)
    assert len(jumps) == 1 and dti[jumps[0] + 1] == pytest.approx(0.43)


@pytest.mark.parametrize("interaction", dgp.INTERACTION_LEVELS)
def test_amplification(interaction):
    truth = dgp.make_truth(dgp._reference(), interaction)
    low = conditional_effect(truth, dgp.AMPLIFICATION, "utilization", 0.15, 0.70, "n_delinquencies", 0)
    high = conditional_effect(truth, dgp.AMPLIFICATION, "utilization", 0.15, 0.70, "n_delinquencies", 3)
    assert low > 0 and high > 0
    if interaction == "none":
        assert high == pytest.approx(low)
    else:
        assert high > 1.1 * low


@pytest.mark.parametrize("interaction", dgp.INTERACTION_LEVELS)
def test_sign_flip(interaction):
    truth = dgp.make_truth(dgp._reference(), interaction)
    thin = conditional_effect(truth, dgp.SIGN_FLIP, "n_inquiries", 0, 4, "history_months", 30.0)
    long = conditional_effect(truth, dgp.SIGN_FLIP, "n_inquiries", 0, 4, "history_months", 340.0)
    assert thin > 0
    if interaction == "none":
        assert long == pytest.approx(thin)
    else:
        assert long < -0.45  # about -0.5 logits; a planted -0.15 was not recovered
