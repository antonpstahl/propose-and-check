import numpy as np
import pytest
import sympy

from verifier_gate.data import dgp
from verifier_gate.facts import bootstrap, symbolic
from verifier_gate.facts.build import build_facts


@pytest.fixture(scope="module", params=["EBM", "XGB2"])
def facts(request):
    data = dgp.generate(dgp.Scenario("dominant", 5_000, 1))
    return build_facts(bootstrap.fit_steps(request.param, data.X, data.y, seed=1), data.X)


def test_exact_expression_reproduces_the_model(facts):
    function = sympy.lambdify([symbolic.symbol(f) for f in dgp.FEATURES], symbolic.expression(facts), "numpy")
    X = dgp.sample_features(300, np.random.default_rng(4))
    values = function(*[X[f].to_numpy() for f in dgp.FEATURES])
    np.testing.assert_allclose(values, facts.steps().logit(X), rtol=0, atol=1e-12)


def test_value_on_a_cut_belongs_to_the_upper_step(facts):
    feature = facts.feature("dti")
    term = symbolic.main_term(feature)
    cut = feature.cuts[len(feature.cuts) // 2]
    upper = feature.scores[len(feature.cuts) // 2 + 1]
    assert float(term.subs(symbolic.symbol("dti"), sympy.Float(cut, precision=53))) == upper


def test_readable_form_merges_equal_steps():
    cuts = np.array([1.0, 2.0, 3.0, 4.0])
    scores = np.array([0.101, 0.099, 0.5, 0.504, 0.502])
    merged_cuts, merged_scores = symbolic._merged(cuts, scores, digits=2)
    assert merged_cuts.tolist() == [2.0] and merged_scores.tolist() == [0.1, 0.5]


def test_relations_follow_the_ranking(facts):
    relations = symbolic.relations(facts)
    assert len(relations) == len(facts.features) - 1
    assert all(holds for _, holds, _ in relations)
    assert all(refits is None for _, _, refits in relations)  # no draws in this fixture
