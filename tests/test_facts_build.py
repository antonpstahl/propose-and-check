import numpy as np
import pytest
from scipy.stats import norm

from verifier_gate.data import dgp
from verifier_gate.facts import bootstrap
from verifier_gate.facts.build import Frame, build_facts, curve_bands
from verifier_gate.facts.schema import Facts
from verifier_gate.facts.steps import StepModel


@pytest.fixture(scope="module")
def data():
    return dgp.generate(dgp.Scenario("dominant", 5_000, 1))


@pytest.fixture(scope="module", params=["EBM", "XGB2"])
def built(request, data):
    reference = bootstrap.fit_steps(request.param, data.X, data.y, seed=1)
    frame = Frame.of(reference, data.X)
    draws = bootstrap.refit_draws(request.param, data.X, data.y, 1, frame, refits=3)
    return reference, build_facts(reference, data.X, draws, {"kind": request.param})


def test_facts_give_back_the_model_exactly_after_a_json_round_trip(built, tmp_path):
    reference, facts = built
    facts.save(tmp_path / "facts")
    loaded = Facts.load(tmp_path / "facts")
    fresh = dgp.sample_features(3_000, np.random.default_rng(9))
    assert np.array_equal(loaded.steps().logit(fresh), reference.logit(fresh))
    assert loaded.draws.refits == 3
    for kind in loaded.draws.KINDS:
        for key, values in getattr(facts.draws, kind).items():
            np.testing.assert_array_equal(getattr(loaded.draws, kind)[key], values)


def test_m_read_through_its_own_frame_gives_its_own_values(built, data):
    reference, facts = built
    own = Frame.of(reference, data.X).read(reference, data.X)
    for f in facts.features:
        np.testing.assert_allclose(own["curves"][f.name], f.scores, atol=1e-12)
        assert f.mass.sum() == pytest.approx(1.0)
    assert sum(own["share"].values()) == pytest.approx(1.0)
    assert sorted(f.rank.value for f in facts.features) == list(range(1, len(facts.features) + 1))


def test_shapes_and_bands(built):
    _, facts = built
    for f in facts.features:
        assert f.pointwise.shape == f.simultaneous.shape == (2, len(f.scores))
        assert np.all(f.pointwise[0] <= f.scores) and np.all(f.scores <= f.pointwise[1])
        assert f.share.band[0] <= f.share.band[1]
    for p in facts.pairs:
        assert p.scores.shape == p.mass.shape == (len(p.cuts[0]) + 1, len(p.cuts[1]) + 1)


def test_the_interaction_contrast_is_the_same_from_either_side(built):
    """[f(a_hi, b_hi) - f(a_lo, b_hi)] - [f(a_hi, b_lo) - f(a_lo, b_lo)] does not depend on which feature
    is the moderator: the main terms cancel."""
    _, facts = built
    for p in facts.pairs:
        first, second = p.conditional
        assert first.difference.value == pytest.approx(second.difference.value, abs=1e-9)


def test_a_term_the_refit_lacks_counts_as_zero(built, data):
    reference, facts = built
    pair = dgp.AMPLIFICATION
    assert pair in reference.term_names
    without = StepModel(reference.intercept, {n: t for n, t in reference.steps.items() if n != pair})
    read = Frame.of(reference, data.X).read(without, data.X)
    assert read["importance"][pair] == 0.0 and read["share"][pair] == 0.0
    effect = read["conditional"]["utilization | n_delinquencies"]
    assert effect[0] == pytest.approx(effect[1])  # main term only: the same effect at both moderator values


def test_sup_t_band_covers_whole_curves_95_percent_of_the_time():
    """Correlated Gaussian curves on 60 steps: c lies between the pointwise and the Bonferroni value, and the
    band M +- c sd from 300 draws covers 95% of fresh whole curves."""
    rng = np.random.default_rng(0)
    steps = 60
    cov = np.exp(-np.abs(np.subtract.outer(np.arange(steps), np.arange(steps))) / 5.0) * np.linspace(0.5, 2, steps) ** 2
    chol = np.linalg.cholesky(cov)
    draws = rng.standard_normal((300, steps)) @ chol.T
    center = np.zeros(steps)
    pointwise, simultaneous, critical = curve_bands(center, draws, np.ones(steps))
    assert 1.96 < critical < norm.ppf(1 - 0.025 / steps)
    fresh = rng.standard_normal((4_000, steps)) @ chol.T
    inside = np.all((fresh >= simultaneous[0]) & (fresh <= simultaneous[1]), axis=1).mean()
    assert inside == pytest.approx(0.95, abs=0.03)
    pointwise_inside = np.all((fresh >= pointwise[0]) & (fresh <= pointwise[1]), axis=1).mean()
    assert pointwise_inside < 0.8  # the multiple-testing problem the simultaneous band fixes (§14 D4)


def test_steps_without_rows_are_left_out_of_the_sup_t_max():
    rng = np.random.default_rng(1)
    draws = rng.standard_normal((200, 10))
    draws[:, 3] *= 1_000.0  # a wild step without rows must not set c
    counts = np.ones(10)
    counts[3] = 0
    _, _, with_empty = curve_bands(np.zeros(10), draws, counts)
    _, _, without = curve_bands(np.zeros(9), np.delete(draws, 3, axis=1), np.ones(9))
    assert with_empty == pytest.approx(without)


def test_poisson_weights_are_shared_by_both_models_and_differ_by_refit():
    a, b = bootstrap.poisson_weights(1_000, 1, 0), bootstrap.poisson_weights(1_000, 1, 0)
    assert np.array_equal(a, b)
    assert not np.array_equal(a, bootstrap.poisson_weights(1_000, 1, 1))
    assert not np.array_equal(a, bootstrap.poisson_weights(1_000, 2, 0))
    assert a.mean() == pytest.approx(1.0, abs=0.1)
