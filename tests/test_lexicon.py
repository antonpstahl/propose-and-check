"""Lexicon predicates on hand-built toy shapes with known answers (§5.6): ramp, dip, step, inverted U, flat
noise, an undetected weak effect, and pair grids with amplification and a sign flip.

Toy Facts are built like real ones: M is a step model, each "refit" is M with independent Gaussian noise on
every step score (sd `noise`, or a term's own perturbation), purified and centred on the sample, and read
through M's frame."""

import itertools

import numpy as np
import pandas as pd
import pytest

from verifier_gate.facts.build import Frame, build_facts
from verifier_gate.facts.schema import Draws, Estimate
from verifier_gate.facts.steps import StepModel, StepTerm, purify
from verifier_gate.lexicon import predicates as p
from verifier_gate.verifier.verify import verify

N = 4_000
EDGES = np.linspace(0.05, 0.95, 19)  # 20 steps on [0, 1]
MIDS = np.concatenate([[0.025], (EDGES[:-1] + EDGES[1:]) / 2, [0.975]])


@pytest.fixture(scope="module")
def X():
    rng = np.random.default_rng(0)
    return pd.DataFrame({f: rng.uniform(0, 1, N) for f in ("ramp", "dip", "step", "hump", "flat", "faint", "a", "b")})


def main(feature, values):
    return StepTerm((feature,), (EDGES,), np.asarray(values, dtype=np.float64))


def toy_facts(X, terms, noise=0.01, refits=60, seed=1, perturb=None):
    """Facts for intercept 0 + terms. perturb: {term: f(scores, rng)} for terms with their own refit noise."""
    features = tuple(dict.fromkeys(f for t in terms for f in t.features))
    raw = StepModel(0.0, {t.name: t for t in terms})
    reference = purify(raw, X, feature_order=features)
    frame = Frame.of(reference, X)
    rng = np.random.default_rng(seed)
    default = lambda scores, rng: scores + rng.normal(0, noise, scores.shape)  # noqa: E731
    reads = []
    for _ in range(refits):
        noisy = {t.name: StepTerm(t.features, t.cuts, (perturb or {}).get(t.name, default)(t.scores, rng)) for t in terms}
        reads.append(frame.read(purify(StepModel(0.0, noisy), X, feature_order=features), X))
    return build_facts(reference, X, Draws.stack(reads))


def exact_facts(X, terms):
    """Facts without bands, like T's: the curves are exact."""
    features = tuple(dict.fromkeys(f for t in terms for f in t.features))
    return build_facts(purify(StepModel(0.0, {t.name: t for t in terms}), X, feature_order=features), X)


def per_step(sd):
    return lambda scores, rng: scores + rng.normal(0, sd, scores.shape)


BASE = [main("ramp", np.linspace(0, 2, 20))]  # a large term, so the toy shares are on a familiar scale
V2 = p.load(p.VERSIONS["v2"])  # the rules these tests were written for; tests/test_lexicon_v3.py has v3's
UP, DOWN = ("increasing", "mostly_increasing"), ("decreasing", "mostly_decreasing")


def test_ramp_increases(X):
    facts = toy_facts(X, BASE)
    assert verify('direction("ramp") == "increasing"', facts).value == p.TRUE
    assert verify('direction("ramp") == "decreasing"', facts).value == p.FALSE
    assert verify('strength("ramp") == "strong"', facts).value == p.TRUE
    assert p.direction_in(facts, "ramp", UP).value == p.TRUE  # "generally increases" (D33)
    assert p.direction_in(facts, "ramp", DOWN).value == p.FALSE


def test_mostly_needs_a_detected_exception(X):
    """D29 (lexicon v2): no exception detected on a curve with bands leaves "mostly" open, since the bands do not
    rule a small one out; on an exact curve (T) no exception means none, and "mostly" is false."""
    verdict = verify('direction("ramp") == "mostly_increasing"', toy_facts(X, BASE), V2)
    assert verdict.value == p.UNDECIDABLE and verdict.code == p.INSUFFICIENT_EVIDENCE
    assert verdict.evidence["exception mass"] == 0
    exact = exact_facts(X, BASE)
    assert verify('direction("ramp") == "mostly_increasing"', exact, V2).value == p.FALSE
    assert verify('direction("ramp") == "increasing"', exact, V2).value == p.TRUE


def test_a_significant_dip_on_one_step_makes_it_mostly_increasing(X):
    dip = np.linspace(0, 2, 20)
    dip[10] -= 0.6  # one step of 20 (5% of the mass) drops clearly below its left neighbours
    facts = toy_facts(X, BASE + [main("dip", dip)])
    verdict = verify('direction("dip") == "mostly_increasing"', facts)
    assert verdict.value == p.TRUE and 0.04 < verdict.evidence["exception mass"] < 0.06
    assert verify('direction("dip") == "increasing"', facts).value == p.FALSE
    assert p.direction_in(facts, "dip", UP).value == p.TRUE


def test_the_same_dip_inside_wide_bands_is_not_an_exception(X):
    dip = np.linspace(0, 2, 20)
    dip[10] -= 0.6
    facts = toy_facts(X, BASE + [main("dip", dip)], perturb={"dip": per_step(0.3)})
    assert verify('direction("dip") == "increasing"', facts, V2).value == p.TRUE  # v2: net change still clear


def test_step_threshold(X):
    facts = toy_facts(X, BASE + [main("step", np.where(MIDS >= 0.6, 1.0, 0.0))])
    assert verify('threshold("step", at=0.6)', facts).value == p.TRUE
    assert verify('threshold("step", at=0.3)', facts).value == p.FALSE
    assert verify('threshold("ramp", at=0.5)', facts).value == p.FALSE  # even rise: no dominant jump


def test_inverted_u_peak(X):
    facts = toy_facts(X, BASE + [main("hump", -20 * (MIDS - 0.5) ** 2)])
    assert verify('peak("hump", at=0.5)', facts).value == p.TRUE
    assert verify('peak("hump", at=0.85)', facts).value == p.FALSE
    assert verify('peak("ramp", at=0.5)', facts).value == p.FALSE  # maximum at the edge


def test_a_top_flat_within_the_noise_leaves_the_peak_undecidable(X):
    """The top steps differ by 0.02 logits, the refits by 0.01 per step: some refits peak one step over."""
    facts = toy_facts(X, BASE + [main("hump", -4 * (MIDS - 0.5) ** 2)])
    verdict = verify('peak("hump", at=0.5)', facts)
    assert verdict.value == p.UNDECIDABLE and verdict.evidence["distance band"][1] > verdict.evidence["tolerance"]


def test_a_peak_inside_a_wide_step_counts_wherever_in_the_step(X):
    """XGB2 curves have few, wide steps: the maximum is an interval, and a claim inside it is near."""
    coarse = StepTerm(("hump",), (np.array([0.2, 0.6]),), np.array([0.0, 1.0, 0.0]))
    facts = toy_facts(X, BASE + [coarse])
    assert verify('peak("hump", at=0.25)', facts).value == p.TRUE  # the step's midpoint is 0.4
    assert verify('peak("hump", at=0.75)', facts).value == p.FALSE


def test_flat_noise_is_negligible_and_not_weak(X):
    facts = toy_facts(X, BASE + [main("flat", np.zeros(20))])
    verdict = verify('negligible("flat")', facts)
    assert verdict.value == p.TRUE and not verdict.evidence["detectable"]
    assert verify('strength("flat") == "weak"', facts).value == p.FALSE
    assert verify('direction("flat") == "increasing"', facts).value == p.UNDECIDABLE
    assert p.direction_in(facts, "flat", UP).value == p.UNDECIDABLE


def faint_toy(X):
    """A 3-4% effect hidden in wide bands. Refits rescale the whole curve, as real refits move a fitted slope,
    so the band spans both sides of M."""
    rescale = lambda scores, rng: scores * (1 + rng.normal(0, 0.8))  # noqa: E731
    return toy_facts(X, BASE + [main("faint", np.linspace(-0.04, 0.04, 20))], perturb={"faint": rescale})


def test_an_undetected_weak_effect_is_not_certified_negligible(X):
    """D25 as refined: the faint effect is not 'hardly matters' (the proposed rule, lower end of the share
    band below 2%, would have said true), and not 'weak' either: the evidence does not settle it."""
    facts = faint_toy(X)
    f = facts.feature("faint")
    assert 0.02 < f.share.value < 0.05 and f.share.band[0] < 0.02  # the proposed rule's case
    verdict = verify('negligible("faint")', facts)
    assert not verdict.evidence["detectable"] and verdict.value == p.UNDECIDABLE
    assert verify('strength("faint") == "weak"', facts).value == p.UNDECIDABLE


def pair_grid(values):
    return StepTerm(("a", "b"), (EDGES, EDGES), np.asarray(values, dtype=np.float64))


def test_amplification_grid(X):
    a, b = np.meshgrid(MIDS, MIDS, indexing="ij")
    facts = toy_facts(X, BASE + [main("a", MIDS), main("b", np.zeros(20)), pair_grid(2 * a * b)])
    assert verify('interaction("a", "b", pattern="amplification")', facts).value == p.TRUE
    assert verify('interaction("a", "b", pattern="sign_flip")', facts).value == p.FALSE
    assert verify('interaction("a", "b", pattern="none")', facts).value == p.FALSE


def test_sign_flip_grid(X):
    a, b = np.meshgrid(MIDS, MIDS, indexing="ij")
    facts = toy_facts(X, BASE + [main("a", np.zeros(20)), main("b", np.zeros(20)), pair_grid(2 * (a - 0.5) * (0.5 - b) * 2)])
    assert verify('interaction("a", "b", pattern="sign_flip")', facts).value == p.TRUE
    assert verify('interaction("a", "b", pattern="amplification")', facts).value == p.FALSE


def test_a_pair_the_model_lacks_is_none_and_nothing_else(X):
    facts = toy_facts(X, BASE + [main("a", MIDS), main("b", MIDS)])
    assert verify('interaction("a", "b", pattern="none")', facts).value == p.TRUE
    assert verify('interaction("a", "b", pattern="amplification")', facts).value == p.FALSE
    assert verify('negligible("a & b")', facts).value == p.TRUE
    assert verify('strength("b & a") == "weak"', facts).value == p.FALSE


def test_unknown_terms_and_claims_that_do_not_apply_are_undecidable_with_their_code(X):
    """D30: the code tells the gate whether the evidence is short (a hedge is possible) or the claim is wrong
    in kind (a writer error)."""
    facts = toy_facts(X, BASE + [main("a", MIDS)], refits=5)
    unknown = ('strength("income") == "weak"', 'rank("x & ramp") == 1', 'negligible("ramp & ramp")',
               'direction("income") in ("increasing", "mostly_increasing")')  # fmt: skip
    for line in unknown:
        verdict = verify(line, facts)
        assert verdict.value == p.UNDECIDABLE and verdict.code == p.UNKNOWN_TERM, line
    for line in ('rank("ramp & a") == 1', 'direction("a & ramp") == "increasing"', 'peak("ramp & a", at=0.5)'):
        verdict = verify(line, facts)
        assert verdict.value == p.UNDECIDABLE and verdict.code == p.NOT_APPLICABLE, line


def test_undecidable_verdicts_carry_a_code_and_decided_ones_none():
    assert p.Verdict(p.UNDECIDABLE).code == p.INSUFFICIENT_EVIDENCE
    assert p.Verdict(p.TRUE).code == ""
    with pytest.raises(ValueError):
        p.Verdict(p.TRUE, code=p.UNKNOWN_TERM)
    with pytest.raises(ValueError):
        p.Verdict(p.UNDECIDABLE, code="tired")


def test_unsettled_is_true_only_for_a_claim_the_evidence_does_not_settle(X):
    """D30: a writer can hedge what the data leave open, but not a settled fact and not an invented term."""
    facts = faint_toy(X)
    assert verify('strength("faint") == "weak"', facts).code == p.INSUFFICIENT_EVIDENCE
    assert verify('unsettled(strength("faint") == "weak")', facts).value == p.TRUE
    assert verify('unsettled(strength("ramp") == "strong")', facts).value == p.FALSE  # settled: true
    assert verify('unsettled(strength("ramp") == "weak")', facts).value == p.FALSE  # settled: false
    assert verify('unsettled(strength("income") == "weak")', facts).value == p.FALSE  # not a term of the model


def shell(values):
    """Facts without bands for a feature x (detectable unless flat) next to a ramp y; tests set x's share or
    rank."""
    X = pd.DataFrame({"x": np.linspace(0, 1, 100), "y": np.linspace(0, 1, 100)})
    return build_facts(StepModel(0.0, {"x": main("x", values), "y": main("y", MIDS)}), X)


def test_strength_sets_judge_the_share_band_on_the_union_of_the_classes():
    """D33: "weak to moderate" is certified where the band straddles 5% and neither class alone is; "at most
    weak" needs no effect, but refuting it asserts one, so that needs a detectable effect (as for negligible)."""

    def judge(classes, band, values=MIDS):
        facts = shell(values)
        object.__setattr__(facts.feature("x"), "share", Estimate(sum(band) / 2, band))
        if len(classes) == 1:
            return p.strength(facts, "x", classes[0]).value
        return p.strength_in(facts, "x", classes).value

    assert judge(("weak",), (0.03, 0.08)) == judge(("moderate",), (0.03, 0.08)) == p.UNDECIDABLE
    assert judge(("weak", "moderate"), (0.03, 0.08)) == p.TRUE
    assert judge(("weak", "moderate"), (0.01, 0.08)) == p.UNDECIDABLE
    assert judge(("weak", "moderate"), (0.16, 0.20)) == p.FALSE
    assert judge(("negligible", "weak"), (0.01, 0.045)) == p.TRUE
    assert judge(("negligible", "weak"), (0.03, 0.06)) == p.UNDECIDABLE
    assert judge(("negligible", "weak"), (0.05, 0.07)) == p.FALSE
    flat = np.zeros(20)  # no detectable effect
    assert judge(("weak", "moderate"), (0.03, 0.08), flat) == p.UNDECIDABLE
    assert judge(("negligible", "weak"), (0.01, 0.045), flat) == p.TRUE
    assert judge(("negligible", "weak"), (0.05, 0.07), flat) == p.UNDECIDABLE


def test_rank_sets_judge_the_rounded_rank_band():
    facts = shell(MIDS)
    object.__setattr__(facts.feature("x"), "rank", Estimate(2.0, (1.6, 3.0)))  # rounded outward: 1 to 3
    assert p.rank(facts, "x", 2).value == p.UNDECIDABLE
    assert p.rank_in(facts, "x", (1, 2, 3)).value == p.TRUE  # "among the top three"
    assert p.rank_in(facts, "x", (2, 3)).value == p.UNDECIDABLE
    assert p.rank_in(facts, "x", (4, 5)).value == p.FALSE


def test_comparison_uses_the_joint_draws(X):
    """Two terms whose marginal share bands overlap, but whose refits move together: the band of the
    difference decides. Common noise: the same perturbation hits both terms in each refit."""
    terms = [main("a", 1.0 * MIDS), main("b", 0.95 * MIDS)]
    reference = StepModel(0.0, {t.name: t for t in terms})
    frame = Frame.of(reference, X)
    rng = np.random.default_rng(3)
    reads = []
    for _ in range(80):
        scale = 1 + rng.normal(0, 0.1)
        refit = StepModel(0.0, {t.name: StepTerm(t.features, t.cuts, t.scores * scale + rng.normal(0, 0.002, 20)) for t in terms})
        reads.append(frame.read(refit, X))
    facts = build_facts(reference, X, Draws.stack(reads))
    a, b = facts.feature("a").importance.band, facts.feature("b").importance.band
    assert a[0] < b[1]  # marginal bands overlap
    assert verify('effect("a") > effect("b")', facts).value == p.TRUE
    assert verify('effect("b") > effect("a")', facts).value == p.FALSE
    assert verify('effect("a") < effect("b")', facts).value == p.FALSE


def test_facts_with_bands_need_their_draws(X):
    facts = toy_facts(X, BASE + [main("a", MIDS)], refits=5)
    facts.draws = None
    with pytest.raises(ValueError, match="draws"):
        verify('effect("ramp") > effect("a")', facts)


@pytest.mark.parametrize("seed", range(40))
def test_exception_mass_matches_brute_force(seed):
    """The dynamic programme against all subsets, with and without bands, both signs."""
    rng = np.random.default_rng(seed)
    k = 8
    center = np.cumsum(rng.normal(0.2, 1.0, k))
    half = rng.uniform(0, 0.8, k) * (seed % 2)  # odd seeds have bands
    mass = rng.dirichlet(np.ones(k))
    mass[rng.integers(k)] = 0.0  # a step without data is ignored
    lower, upper = center - half, center + half
    for sign in (1, -1):
        best = 0.0
        for keep in itertools.product((False, True), repeat=k):
            idx = [i for i in range(k) if keep[i] and mass[i] > 0]
            ok = all((upper[j] >= lower[i]) if sign > 0 else (lower[j] <= upper[i]) for i, j in itertools.combinations(idx, 2))
            if ok:
                best = max(best, mass[idx].sum())
        assert p.exception_mass(lower, upper, mass, sign) == pytest.approx(mass.sum() - best, abs=1e-12)


def test_share_tolerance_edges():
    """about v fits actual shares a with |v - a| <= max(0.02, 0.1 a)."""
    lex = p.load()
    reference = StepModel(0.0, {"x": main("x", MIDS)})  # only for a Facts shell
    X = pd.DataFrame({"x": np.linspace(0, 1, 100)})
    facts = build_facts(reference, X)

    def judge(actual, claimed, band=None):
        f = facts.features[0]
        object.__setattr__(f, "share", Estimate(actual, band))
        return p.share(facts, "x", claimed, lex).value

    assert judge(0.30, 0.329) == p.TRUE and judge(0.30, 0.335) == p.FALSE  # relative: about 10%
    assert judge(0.05, 0.0695) == p.TRUE and judge(0.05, 0.0705) == p.FALSE  # absolute: 0.02
    assert judge(0.30, 0.31, (0.25, 0.35)) == p.UNDECIDABLE
    assert judge(0.30, 0.31, (0.29, 0.33)) == p.TRUE


def test_rank_band_is_rounded_outward():
    reference = StepModel(0.0, {"x": main("x", MIDS)})
    facts = build_facts(reference, pd.DataFrame({"x": np.linspace(0, 1, 100)}))
    f = facts.features[0]
    object.__setattr__(f, "rank", Estimate(1.0, (1.0, 1.475)))  # a few refits put it second
    assert p.rank(facts, "x", 1).value == p.UNDECIDABLE
    assert p.rank(facts, "x", 2).value == p.UNDECIDABLE
    assert p.rank(facts, "x", 3).value == p.FALSE
    object.__setattr__(f, "rank", Estimate(1.0, (1.0, 1.0)))
    assert p.rank(facts, "x", 1).value == p.TRUE
