"""The readable form and its check (facts/readable.py; plan §5.4, §14.8), on hand-built curves with known bands.
The toy cases are the ones §14.8 asks for, built to fail with naive rounding: a pair of steps on a rounding
boundary, a significant one-step dip, and a misplaced jump; plus the case naive significance misses, a direction
resolved only by the net change."""

import numpy as np
import pytest

from verifier_gate.dsl.grammar import Claim
from verifier_gate.facts import readable as r
from verifier_gate.facts import symbolic
from verifier_gate.facts.schema import Estimate, Facts, FeatureFacts

SHARE = Estimate(0.1, (0.05, 0.15))


def feature(scores, half, net_band=None, name="x", cuts=None):
    """A curve with steps on [i, i + 1), equal mass, and a band of half-width `half` around M."""
    scores = np.asarray(scores, dtype=float)
    k = len(scores)
    cuts = np.arange(1, k, dtype=float) if cuts is None else np.asarray(cuts, dtype=float)
    band = np.vstack([scores - half, scores + half])
    net = float(scores[-1] - scores[0])
    net_band = net_band if net_band is not None else (net - 2 * half, net + 2 * half)
    return FeatureFacts(name, cuts, scores, np.full(k, 1 / k), band, band, 3.0, SHARE, SHARE, Estimate(1.0, (1.0, 1.0)),
                        (0.5, k - 0.5), Estimate(net, net_band))  # fmt: skip


def facts(*features):
    return Facts({}, {"refits": 100}, 0.0, tuple(features), ())


def test_steps_on_a_rounding_boundary_stay_one_piece():
    f = feature([0.249] * 5 + [0.251] * 5, half=0.05, net_band=(-0.1, 0.1))
    naive_cuts, naive_values = symbolic._merged(f.cuts, f.scores, 1)  # the readable form as first built (§14.3)
    assert list(naive_values) == [0.2, 0.3]  # rounding invents a jump of 0.1
    form = r.readable(f)
    assert len(form.pieces) == 1 and form.kind == "flat"
    assert 0.2 < form.pieces[0].value < 0.3  # the shortest decimal inside the band: 0.25
    naive = r.Readable("x", "pieces", (r.Piece(0, 4, 0.2, 1), r.Piece(5, 9, 0.3, 1)), f.cuts, False, (0.002, (-0.1, 0.1)), f.low_high)
    assert r.check(naive, facts(f), []).shown_not_significant == 1  # the check catches it
    assert r.check(form, facts(f), []).passed


RAMP = np.linspace(0, 1, 20)


def dipped(depth):
    scores = RAMP.copy()
    scores[10] -= depth
    return scores


def test_a_significant_dip_is_shown():
    f = feature(dipped(0.35), half=0.04)
    form = r.readable(f)
    values = form.on_steps(20)
    assert values[10] < values[9]  # the exception is visible
    result = r.check(form, facts(f), [Claim("direction", ("x",), "mostly_increasing")])
    assert result.passed and result.significant_not_shown == 0


def test_the_same_dip_inside_wide_bands_is_not_shown():
    f = feature(dipped(0.35), half=0.4)
    form = r.readable(f)
    values = form.on_steps(20)
    assert np.all(np.diff(values) >= 0)  # no movement against the direction is shown
    assert r.check(form, facts(f), [Claim("direction", ("x",), "increasing")]).passed


def test_a_dip_shown_by_naive_rounding_is_flagged_and_a_dip_hidden_by_it_too():
    wide = feature(dipped(0.35), half=0.4)
    naive = r.Readable("x", "pieces", tuple(r.Piece(i, i, round(v, 1), 1) for i, v in enumerate(wide.scores)), wide.cuts,
                       False, (1.0, (0.5, 1.5)), wide.low_high)  # fmt: skip
    assert r.check(naive, facts(wide), []).shown_not_significant > 0
    tight = feature(dipped(0.35), half=0.04)
    smoothed = r.Readable("x", "pieces", (r.Piece(0, 9, 0.2, 1), r.Piece(10, 19, 0.8, 1)), tight.cuts, False,
                          (1.0, (0.9, 1.1)), tight.low_high)  # fmt: skip
    assert r.check(smoothed, facts(tight), []).significant_not_shown > 0


def test_a_direction_resolved_only_by_the_net_change_is_kept():
    """Weak at n = 5,000: no two steps differ significantly, but the net change does; the curve must not read as
    flat while the lexicon certifies its direction."""
    f = feature(np.linspace(0, 0.1, 20), half=0.2, net_band=(0.03, 0.17))
    form = r.readable(f)
    assert form.kind == "net change only" and "rises by 0.10" in r.describe(form)
    certified = [Claim("direction", ("x",), "increasing")]
    assert r.check(form, facts(f), certified).passed
    as_flat = r.Readable("x", "flat", form.pieces, f.cuts, False, (0.1, (-0.03, 0.17)), f.low_high)  # net change not significant
    assert r.check(as_flat, facts(f), certified).direction_hidden == ['direction("x") == "increasing"']


def test_a_certified_jump_must_be_where_the_readable_curve_jumps():
    f = feature([0.0] * 10 + [1.0] * 10, half=0.05)
    form = r.readable(f)
    assert len(form.pieces) == 2
    assert r.check(form, facts(f), [Claim("threshold", ("x",), 10.0)]).passed
    off = r.check(form, facts(f), [Claim("threshold", ("x",), 12.0)])  # w = 0.02 x (19.5 - 0.5) = 0.38
    assert off.location_off == ['threshold("x", at=12.0)'] and not off.passed


def test_values_are_the_shortest_decimal_inside_the_band():
    assert r.simplest(0.21, 0.37, 0.33) == (0.3, 1)
    assert r.simplest(0.2401, 0.2499, 0.245) == (0.245, 3)
    assert r.simplest(-0.6, 0.4, 0.1) == (0.0, 0)
    assert r._value(r.Piece(0, 0, -0.0, 0)) == "0"  # no "-0" in the handover


def test_count_features_are_described_by_the_values_they_cover():
    f = feature([-0.4, 0.2, 0.2, 0.6], half=0.05, cuts=[0.5, 1.5, 2.5])
    text = r.describe(r.readable(f, count=True))
    assert text.startswith("0: -0.4; 1-2: +0.2; >= 3: +0.6")
    assert "net change from the 5th to the 95th percentile" in text


def test_facts_without_bands_have_no_readable_form():
    f = feature([0, 1], half=0.1)
    object.__setattr__(f, "simultaneous", None)
    with pytest.raises(ValueError):
        r.readable(f)
