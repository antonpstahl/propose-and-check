"""Lexicon predicates over Facts (§5.3): each word of the lexicon as a condition on the facts of one model.

Every predicate returns a Verdict: true, false or undecidable, with the evidence it used. A band [lo, hi] is
judged against the set S a word claims (D13): true if the band lies inside S, false if it lies outside S,
undecidable otherwise. Facts without bands (T) have degenerate bands, so every rule reduces to the plain
condition on the exact values.

Bands. Stored in the Facts: percentile bands for share, importance, rank, net change and conditional effects,
and the simultaneous (sup-t) band for curves, used by every rule that scans steps (§14 D4). Derived from the
stored refit draws: percentile bands for single derived quantities (importance differences, peak and jump
locations) and a sup-t band for windowed jumps, which are scanned over locations.

Detectable effects (D25, §14.5). A share band cannot show that an effect exists: the share (mean |score|) of a
fitted null term is positive, and the bootstrap of such a statistic is not valid near zero (its band for a
noise feature typically excludes 0). So every word that asserts an effect (weak, moderate, strong, amplifies)
needs a detectable effect besides its share band, and a curve band, which is valid at zero, decides
detectability: for a feature, the simultaneous band excludes 0 on more than `detectable_mass` of the data, or
the net change from the 5th to the 95th percentile is significant; for a pair, its interaction contrast is
significant (facts/build.py).

"Negligible" (D25 as refined, §14.5) is true if the share band lies below the weak class, or if no effect is
detectable, the model's own share is below the weak class and the share band rules out a moderate effect. It is
false if an effect is detectable and the share band lies at or above the weak class. Requiring the band below
2% alone is a valid equivalence test but almost never passes; requiring only a non-significant effect would
certify "hardly matters" for a real 4% effect whose share is estimated at 3.5% (absence of evidence).

"Mostly" (D29, §14.7) asserts an exception, so it needs a detected one: with bands, a curve without a detected
exception leaves "mostly" undecidable, because the bands do not rule a small exception out. The strict word
("increases") is certified when no exception is detected: true at the resolution the sample allows. Without
bands (T) the curve is exact, and no exception means none.

Reason codes (D30). An undecidable verdict says why: the evidence does not settle the claim
(INSUFFICIENT_EVIDENCE), the claim names a term the model does not have (UNKNOWN_TERM), or the claim type does
not apply to the term, e.g. the direction of a pair (NOT_APPLICABLE). Only the first can be hedged:
`unsettled(<claim>)` is true exactly when its claim is undecidable for insufficient evidence.

Sets of values (D33). A claim may name neighbouring values at once: "weak to moderate", "at most weak", "second
or third", "generally decreases". It is judged by the same rule, true if the band lies inside the set, false if
outside. So a set is confidently wrong only on a term where the claim of the term's true value is confidently
wrong too: sets add no new failure cases, they turn abstentions into certified, coarser statements.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

import numpy as np
import yaml

from verifier_gate.facts import build
from verifier_gate.facts.schema import Draws, Estimate, Facts, FeatureFacts, PairFacts
from verifier_gate.facts.steps import PAIR_SEPARATOR

TRUE, FALSE, UNDECIDABLE = "true", "false", "undecidable"
INSUFFICIENT_EVIDENCE, UNKNOWN_TERM, NOT_APPLICABLE = "insufficient_evidence", "unknown_term", "not_applicable"
CODES = (INSUFFICIENT_EVIDENCE, UNKNOWN_TERM, NOT_APPLICABLE)  # why a verdict is undecidable (D30)
LEXICON_PATH = Path(__file__).with_name("lexicon.yaml")
DIRECTIONS = {"increasing": (1, False), "decreasing": (-1, False), "mostly_increasing": (1, True), "mostly_decreasing": (-1, True)}
STRENGTHS = ("weak", "moderate", "strong")
CLASSES = ("negligible", *STRENGTHS)  # the classes of a share, from below; a strength set spans neighbours (D33)
PATTERNS = ("amplification", "sign_flip", "none")
JUMP_GRID = 2_000  # locations at which a windowed jump is evaluated
ZERO_MASS = 1e-9  # exception mass below this counts as none (float sums of step masses)


@dataclass(frozen=True)
class Verdict:
    value: str  # TRUE, FALSE or UNDECIDABLE
    evidence: dict = field(default_factory=dict)
    reason: str = ""
    code: str = ""  # undecidable verdicts only: one of CODES, INSUFFICIENT_EVIDENCE unless given

    def __post_init__(self):
        if self.value == UNDECIDABLE and not self.code:
            object.__setattr__(self, "code", INSUFFICIENT_EVIDENCE)
        if self.value not in (TRUE, FALSE, UNDECIDABLE) or (self.code not in CODES if self.value == UNDECIDABLE else self.code):
            raise ValueError(f"a {self.value!r} verdict cannot have the code {self.code!r}")


@dataclass(frozen=True)
class Lexicon:
    version: str
    level: float
    strength: Mapping[str, float]  # lower edge of each class
    detectable_mass: float
    share_absolute: float
    share_relative: float
    exception_mass: float
    window: float
    search: tuple[float, float]
    jump_fraction: float
    pair_share: float

    def strength_class(self, label: str) -> tuple[float, float]:
        edges = [self.strength[s] for s in STRENGTHS] + [np.inf]
        i = STRENGTHS.index(label)
        return edges[i], edges[i + 1]


@cache
def load(path: Path = LEXICON_PATH) -> Lexicon:
    d = yaml.safe_load(Path(path).read_text())
    if d["level"] != build.LEVEL:
        raise ValueError(f"lexicon level {d['level']} differs from the level of the stored bands, {build.LEVEL}")
    return Lexicon(
        d["version"], d["level"], dict(d["strength"]), d["detectable_mass"], d["share"]["absolute"],
        d["share"]["relative"], d["direction"]["exception_mass"], d["location"]["window"],
        tuple(d["location"]["search"]), d["location"]["jump_fraction"], d["interaction"]["pair_share"],
    )  # fmt: skip


# --- bands -------------------------------------------------------------------------------------------------


def interval(e: Estimate) -> tuple[float, float]:
    return e.band if e.band is not None else (e.value, e.value)


def curve_band(f: FeatureFacts) -> tuple[np.ndarray, np.ndarray]:
    return (f.simultaneous[0], f.simultaneous[1]) if f.simultaneous is not None else (f.scores, f.scores)


def draws_of(facts: Facts) -> Draws | None:
    """The refit draws, or None for Facts without bands (T)."""
    if facts.bands["refits"] == 0:
        return None
    if facts.draws is None:
        raise ValueError("these Facts have bands; load them with draws=True")
    return facts.draws


def _judge(true: bool, false: bool) -> str:
    assert not (true and false), "a verdict cannot be true and false"
    return TRUE if true else FALSE if false else UNDECIDABLE


def _inside(band: tuple[float, float], lo: float, hi: float) -> bool:
    return lo <= band[0] and band[1] <= hi


def _outside(band: tuple[float, float], lo: float, hi: float) -> bool:
    return band[1] < lo or band[0] > hi


# --- terms -------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Term:
    """What the share-based words need of a feature or a pair. A pair of known features that the model does
    not have is a term that is exactly zero: share 0, not detectable."""

    name: str
    is_pair: bool
    present: bool
    share: Estimate
    importance: Estimate
    detectable: bool
    detection: dict


def feature_detection(f: FeatureFacts, lex: Lexicon) -> tuple[bool, dict]:
    lower, upper = curve_band(f)
    excluded = float(f.mass[(lower > 0) | (upper < 0)].sum())
    net = interval(f.net_change)
    detectable = excluded > lex.detectable_mass or net[0] > 0 or net[1] < 0
    return detectable, {"mass where the curve band excludes 0": excluded, "net change": f.net_change.value, "net change band": net}


def pair_detection(p: PairFacts) -> tuple[bool, dict]:
    contrast = p.conditional[0].difference  # the same from either side
    band = interval(contrast)
    return band[0] > 0 or band[1] < 0, {"interaction contrast": contrast.value, "interaction contrast band": band}


def term(facts: Facts, name: str, lex: Lexicon) -> Term | None:
    """The feature or pair called `name` ("a & b" in either order), or None if a feature is unknown."""
    features = {f.name: f for f in facts.features}
    if name in features:
        f = features[name]
        detectable, detection = feature_detection(f, lex)
        return Term(f.name, False, True, f.share, f.importance, detectable, detection)
    parts = tuple(s.strip() for s in name.split(PAIR_SEPARATOR.strip()))
    if len(parts) != 2 or not all(p in features for p in parts) or parts[0] == parts[1]:
        return None
    p = facts.pair(*parts)
    if p is None:
        zero = Estimate(0.0, (0.0, 0.0))
        return Term(PAIR_SEPARATOR.join(parts), True, False, zero, zero, False, {"in the model": False})
    detectable, detection = pair_detection(p)
    return Term(p.name, True, True, p.share, p.importance, detectable, detection)


def _unknown(name: str) -> Verdict:
    return Verdict(UNDECIDABLE, {"term": name}, f"{name} is not a term of this model", UNKNOWN_TERM)


def _feature(facts: Facts, name: str, lex: Lexicon, what: str) -> FeatureFacts | Verdict:
    """The feature `name`, or the verdict on a claim that needs a feature: an unknown name is not a term of the
    model, and for a pair the claim type does not apply."""
    features = {f.name: f for f in facts.features}
    if name in features:
        return features[name]
    if term(facts, name, lex) is None:
        return _unknown(name)
    return Verdict(UNDECIDABLE, {"term": name}, f"{what} are defined for features, not for pairs", NOT_APPLICABLE)


def _share_evidence(t: Term) -> dict:
    return {"term": t.name, "share": t.share.value, "share band": interval(t.share), "detectable": t.detectable, **t.detection}


# --- share-based words: strength, negligible, share, rank, comparison --------------------------------------


def strength(facts: Facts, name: str, label: str, lex: Lexicon | None = None) -> Verdict:
    """weak / moderate / strong: the share band lies in the class, and the effect is detectable."""
    lex = lex or load()
    t = term(facts, name, lex)
    if t is None:
        return _unknown(name)
    lo, hi = lex.strength_class(label)
    band = interval(t.share)
    inside = lo <= band[0] and band[1] < hi
    outside = band[1] < lo or band[0] >= hi
    value = _judge(inside and t.detectable, outside)
    reason = {
        TRUE: f"share band inside [{lo:.0%}, {hi:.0%}) and the effect is detectable",
        FALSE: f"share band outside [{lo:.0%}, {hi:.0%})",
        UNDECIDABLE: "share band straddles a class edge" if not inside else "share band in the class, but no effect is detectable",
    }[value]
    return Verdict(value, _share_evidence(t) | {"class": [lo, hi]}, reason)


def strength_in(facts: Facts, name: str, labels: tuple[str, ...], lex: Lexicon | None = None) -> Verdict:
    """A run of neighbouring classes of CLASSES (D33), judged like one class on the union of their intervals.
    "weak to moderate" asserts an effect: true if the share band lies inside and the effect is detectable, false
    if the band lies outside. "at most weak" (a run from negligible) asserts at most the run's top class: true if
    the band lies below its upper edge, false if the band lies above it and the effect is detectable, the
    condition D25 sets for refuting "negligible"."""
    lex = lex or load()
    t = term(facts, name, lex)
    if t is None:
        return _unknown(name)
    edges = [0.0, *(lex.strength[s] for s in STRENGTHS), np.inf]
    lo, hi = edges[CLASSES.index(labels[0])], edges[CLASSES.index(labels[-1]) + 1]
    band = interval(t.share)
    if labels[0] == "negligible":
        value = _judge(band[1] < hi, band[0] >= hi and t.detectable)
    else:
        value = _judge(lo <= band[0] and band[1] < hi and t.detectable, band[1] < lo or band[0] >= hi)
    span = f"[{lo:.0%}, {hi:.0%})"
    reason = {
        TRUE: f"share band inside {span}" + ("" if labels[0] == "negligible" else " and the effect is detectable"),
        FALSE: f"share band outside {span}" + (" and the effect is detectable" if labels[0] == "negligible" else ""),
        UNDECIDABLE: f"share band not settled against {span}",
    }[value]
    return Verdict(value, _share_evidence(t) | {"classes": list(labels), "interval": [lo, hi]}, reason)


def negligible(facts: Facts, name: str, lex: Lexicon | None = None) -> Verdict:
    """"hardly matters" (D25 as refined, §14.5; see the module docstring)."""
    lex = lex or load()
    t = term(facts, name, lex)
    if t is None:
        return _unknown(name)
    edge, moderate = lex.strength["weak"], lex.strength["moderate"]
    lo, hi = interval(t.share)
    below = hi < edge
    small_and_undetected = not t.detectable and t.share.value < edge and hi < moderate
    value = _judge(below or small_and_undetected, lo >= edge and t.detectable)
    reason = {
        TRUE: "share band below the weak class" if below else "no detectable effect, share below the weak class, a moderate effect ruled out",
        FALSE: "detectable effect with a share band at or above the weak class",
        UNDECIDABLE: "neither a detectable non-negligible effect nor a negligible one is shown",
    }[value]
    return Verdict(value, _share_evidence(t), reason)


def share(facts: Facts, name: str, claimed: float, lex: Lexicon | None = None) -> Verdict:
    """"about v": |v - actual| <= max(absolute, relative * actual) for every value in the share band."""
    lex = lex or load()
    t = term(facts, name, lex)
    if t is None:
        return _unknown(name)
    # the actual shares a that the claim fits form an interval [a_min, a_max]
    a_min = min(claimed - lex.share_absolute, claimed / (1 + lex.share_relative))
    a_max = max(claimed + lex.share_absolute, claimed / (1 - lex.share_relative))
    band = interval(t.share)
    value = _judge(_inside(band, a_min, a_max), _outside(band, a_min, a_max))
    return Verdict(value, _share_evidence(t) | {"claimed": claimed, "shares the claim fits": [a_min, a_max]})


def _rank_band(f: FeatureFacts) -> tuple[float, float]:
    """The refits' rank band, rounded outward to whole ranks (1.475 means "a few refits put it second")."""
    lo, hi = interval(f.rank)
    return float(np.floor(lo)), float(np.ceil(hi))


def rank(facts: Facts, name: str, k: int, lex: Lexicon | None = None) -> Verdict:
    """Rank among the features by importance: true if the rank band is {k}, false if it excludes k."""
    lex = lex or load()
    f = _feature(facts, name, lex, "ranks")
    if isinstance(f, Verdict):
        return f
    lo, hi = _rank_band(f)
    value = _judge(lo == hi == k, k < lo or k > hi)
    return Verdict(value, {"term": name, "rank": f.rank.value, "rank band": (lo, hi), "claimed": k})


def rank_in(facts: Facts, name: str, ks: tuple[int, ...], lex: Lexicon | None = None) -> Verdict:
    """One of consecutive ranks (D33), "second or third", "among the top three": true if the rank band lies
    inside them, false if it lies outside."""
    lex = lex or load()
    f = _feature(facts, name, lex, "ranks")
    if isinstance(f, Verdict):
        return f
    lo, hi = _rank_band(f)
    value = _judge(ks[0] <= lo and hi <= ks[-1], hi < ks[0] or lo > ks[-1])
    return Verdict(value, {"term": name, "rank": f.rank.value, "rank band": (lo, hi), "claimed": list(ks)})


def comparison(facts: Facts, a: str, b: str, relation: str, lex: Lexicon | None = None) -> Verdict:
    """effect(a) > effect(b) (or <): on importances, with the band of their difference across refits."""
    lex = lex or load()
    ta, tb = term(facts, a, lex), term(facts, b, lex)
    if ta is None or tb is None:
        return _unknown(a if ta is None else b)
    sign = {">": 1.0, "<": -1.0}[relation]
    point = sign * (ta.importance.value - tb.importance.value)
    draws = draws_of(facts)
    if draws is None:
        band = (point, point)
    else:
        def refit_values(t: Term) -> np.ndarray:
            return draws.importance[t.name] if t.present else np.zeros(draws.refits)

        band = build.percentile_band(sign * (refit_values(ta) - refit_values(tb)))
    value = _judge(band[0] > 0, band[1] <= 0)
    evidence = {"importance": {ta.name: ta.importance.value, tb.name: tb.importance.value}, "difference": point, "difference band": band}
    return Verdict(value, evidence)


# --- shape words: direction, threshold, peak ---------------------------------------------------------------


def exception_mass(lower: np.ndarray, upper: np.ndarray, mass: np.ndarray, sign: int) -> float:
    """Smallest data mass to leave out so that the rest of the curve shows no significant movement against
    `sign`: for sign +1, no kept steps i < j whose bands show a decrease (upper[j] < lower[i]); for -1, no
    increase. With the simultaneous band, a decrease found this way is real with 95% confidence for the whole
    family of comparisons. Without bands, it is the mass outside the heaviest monotone subsequence.

    Dynamic programme over the steps with data: the state is the largest lower bound among the steps kept so
    far (-inf before any), and step j can be kept iff its upper bound reaches that state."""
    if sign < 0:
        lower, upper = -upper, -lower
    used = mass > 0
    lo, hi, w = lower[used], upper[used], mass[used]
    states = np.concatenate([[-np.inf], lo])  # state 0: nothing kept; state i + 1: largest lower bound lo[i]
    best = np.full(len(states), -np.inf)
    best[0] = 0.0
    for j in range(len(w)):
        allowed = (states <= hi[j]) & np.isfinite(best)
        stay = allowed & (states >= lo[j])  # keeping j leaves the largest lower bound unchanged
        move = allowed & (states < lo[j])  # keeping j raises it to lo[j]
        moved = best[move].max() + w[j] if move.any() else -np.inf
        best[stay] += w[j]
        best[j + 1] = max(best[j + 1], moved)
    return float(max(w.sum() - best.max(), 0.0))


def _movement(f: FeatureFacts, sign: int) -> tuple[float, bool, bool, dict]:
    """Exception mass against `sign`, whether the net change is significantly with it or (at least weakly)
    against it, and the evidence."""
    lower, upper = curve_band(f)
    exception = exception_mass(lower, upper, f.mass, sign)
    exception = 0.0 if exception < ZERO_MASS else exception
    net = interval(f.net_change)
    net_with = net[0] > 0 if sign > 0 else net[1] < 0
    net_against = net[1] <= 0 if sign > 0 else net[0] >= 0
    evidence = {"term": f.name, "net change": f.net_change.value, "net change band": net, "exception mass": exception}
    return exception, net_with, net_against, evidence


def direction(facts: Facts, name: str, label: str, lex: Lexicon | None = None) -> Verdict:
    """"increases": the net change (5th to 95th percentile) is significantly positive and no significant
    decrease remains anywhere (exception mass 0). "mostly increases": the net change is significantly positive
    and a significant decrease exists, on at most `exception_mass` of the data; with bands and no detected
    decrease it is undecidable (D29). Mirrored for decreases."""
    lex = lex or load()
    f = _feature(facts, name, lex, "directions")
    if isinstance(f, Verdict):
        return f
    sign, mostly = DIRECTIONS[label]
    exception, net_with, net_against, evidence = _movement(f, sign)
    reason = ""
    if mostly:
        exact = f.simultaneous is None  # T: without bands, no exception means none
        true = net_with and 0 < exception <= lex.exception_mass
        value = _judge(true, net_against or exception > lex.exception_mass or (exception == 0 and exact))
        if value == UNDECIDABLE:  # with a significant net change, only D29's case is left open
            reason = "no exception detected, and the bands do not rule a small one out (D29)" if net_with else "no significant net change"
    else:
        value = _judge(net_with and exception == 0, net_against or exception > 0)
    return Verdict(value, evidence, reason)


def direction_in(facts: Facts, name: str, labels: tuple[str, str], lex: Lexicon | None = None) -> Verdict:
    """"generally increases": the strict or the "mostly" word of one direction, whichever holds (D33). True if
    the net change is significantly in the direction and the exceptions cover at most `exception_mass` of the
    data; false if the net change is not in the direction or the exceptions cover more."""
    lex = lex or load()
    f = _feature(facts, name, lex, "directions")
    if isinstance(f, Verdict):
        return f
    exception, net_with, net_against, evidence = _movement(f, DIRECTIONS[labels[0]][0])
    value = _judge(net_with and exception <= lex.exception_mass, net_against or exception > lex.exception_mass)
    return Verdict(value, evidence | {"claimed": list(labels)})


def _step_x(f: FeatureFacts) -> np.ndarray:
    """A location for each step: the midpoint of its cuts; the outer steps mirror their neighbour's width."""
    c = f.cuts
    if len(c) == 0:
        return np.zeros(1)
    if len(c) == 1:
        return np.array([c[0], c[0]])
    inner = (c[:-1] + c[1:]) / 2
    return np.concatenate([[c[0] - (c[1] - c[0]) / 2], inner, [c[-1] + (c[-1] - c[-2]) / 2]])


def _search(f: FeatureFacts, lex: Lexicon) -> np.ndarray:
    """Steps whose data mass lies (partly) between the search quantiles."""
    after = np.cumsum(f.mass)
    before = after - f.mass
    return np.flatnonzero((f.mass > 0) & (after > lex.search[0]) & (before < lex.search[1]))


def _window(f: FeatureFacts, lex: Lexicon) -> float:
    return lex.window * (f.low_high[1] - f.low_high[0])


def _argmax_centre(x: np.ndarray, values: np.ndarray) -> float:
    """Centre of the first run of locations where the values reach their maximum."""
    top = np.flatnonzero(values >= values.max() - 1e-12)
    gaps = np.flatnonzero(np.diff(top) > 1)
    return float(x[top[: gaps[0] + 1] if len(gaps) else top].mean())


def _location_verdict(at: float, w: float, band: tuple[float, float]) -> tuple[bool, bool]:
    return _inside(band, at - w, at + w), _outside(band, at - w, at + w)


def threshold(facts: Facts, name: str, at: float, lex: Lexicon | None = None) -> Verdict:
    """"jumps at x": the largest jump over a window w (a `window` fraction of the 5th-95th percentile range)
    is significant (sup-t band over all locations), lies within w of x across refits, and is at least
    `jump_fraction` of the term's range in the search region across refits."""
    lex = lex or load()
    f = _feature(facts, name, lex, "thresholds")
    if isinstance(f, Verdict):
        return f
    w = _window(f, lex)
    search = _search(f, lex)
    x_steps = _step_x(f)
    lo_x, hi_x = x_steps[search[0]], x_steps[search[-1]]
    x = np.linspace(lo_x + w / 2, max(hi_x - w / 2, lo_x + w / 2), JUMP_GRID)
    below, above = (np.searchsorted(f.cuts, x + d, side="right") for d in (-w / 2, w / 2))

    def jumps(curves: np.ndarray) -> np.ndarray:
        return curves[..., above] - curves[..., below]

    def spread(curves: np.ndarray) -> np.ndarray:
        on = curves[..., search]
        return on.max(axis=-1) - on.min(axis=-1)

    jump = jumps(f.scores)
    at_max = int(np.flatnonzero(np.abs(jump) >= np.abs(jump).max() - 1e-12)[0])
    location = _argmax_centre(x, np.abs(jump))
    ratio = float(np.abs(jump).max() / spread(f.scores)) if spread(f.scores) > 0 else 0.0
    draws = draws_of(facts)
    if draws is None:
        significant = bool(jump[at_max] != 0)
        location_band, ratio_band = (location, location), (ratio, ratio)
    else:
        refit_jumps = jumps(draws.curves[name])
        _, simultaneous, _ = build.curve_bands(jump, refit_jumps, np.ones(len(x)))
        significant = bool(simultaneous[0, at_max] > 0 or simultaneous[1, at_max] < 0)
        location_band = build.percentile_band(np.array([_argmax_centre(x, np.abs(j)) for j in refit_jumps]))
        refit_spread = spread(draws.curves[name])
        ratio_band = build.percentile_band(np.abs(refit_jumps).max(axis=1) / np.where(refit_spread > 0, refit_spread, np.inf))
    near, far = _location_verdict(at, w, location_band)
    large, small = ratio_band[0] >= lex.jump_fraction, ratio_band[1] < lex.jump_fraction
    value = _judge(significant and near and large, far or small or (draws is None and not significant))
    evidence = {
        "term": name, "largest jump at": location, "location band": location_band, "tolerance": w,
        "jump": float(jump[at_max]), "jump significant": significant, "jump / range": ratio, "jump / range band": ratio_band,
    }  # fmt: skip
    return Verdict(value, evidence)


def _step_edges(f: FeatureFacts) -> tuple[np.ndarray, np.ndarray]:
    """Lower and upper edge of each step; the outer steps end at their mirrored width (_step_x)."""
    x = _step_x(f)
    lower = np.concatenate([[2 * x[0] - f.cuts[0] if len(f.cuts) else x[0]], f.cuts])
    upper = np.concatenate([f.cuts, [2 * x[-1] - f.cuts[-1] if len(f.cuts) else x[-1]]])
    return lower, upper


def peak(facts: Facts, name: str, at: float, lex: Lexicon | None = None) -> Verdict:
    """"peaks at x": x lies within w of the curve's highest step(s) in the search region, in M and across the
    refits, and the maximum is interior: on each side some step lies significantly below it (simultaneous
    band). On a step curve the maximum is an interval, so the claim is judged by its distance to that interval
    in each refit: near if the 97.5th percentile of the distance is at most w, far if the 2.5th exceeds w."""
    lex = lex or load()
    f = _feature(facts, name, lex, "peaks")
    if isinstance(f, Verdict):
        return f
    w = _window(f, lex)
    search = _search(f, lex)
    edge_lo, edge_hi = (e[search] for e in _step_edges(f))

    def distance(values: np.ndarray) -> tuple[float, tuple[float, float]]:
        top = np.flatnonzero(values >= values.max() - 1e-12)
        gaps = np.flatnonzero(np.diff(top) > 1)
        run = top[: gaps[0] + 1] if len(gaps) else top
        span = (float(edge_lo[run[0]]), float(edge_hi[run[-1]]))
        return max(span[0] - at, at - span[1], 0.0), span

    d, span = distance(f.scores[search])
    top = search[int(np.argmax(f.scores[search]))]
    lower, upper = curve_band(f)
    left, right = search[search < top], search[search > top]
    interior = bool(left.size and right.size and lower[top] > upper[left].min() and lower[top] > upper[right].min())
    draws = draws_of(facts)
    if draws is None:
        distance_band = (d, d)
    else:
        distance_band = build.percentile_band(np.array([distance(c[search])[0] for c in draws.curves[name]]))
    near, far = distance_band[1] <= w, distance_band[0] > w
    value = _judge(interior and near, far)
    evidence = {"term": name, "highest steps": span, "distance": d, "distance band": distance_band, "tolerance": w, "interior maximum": interior}
    return Verdict(value, evidence)


# --- interactions ------------------------------------------------------------------------------------------


def interaction(facts: Facts, a: str, b: str, pattern: str, lex: Lexicon | None = None) -> Verdict:
    """How b changes the effect of a: the conditional effect of a (main + pair, 5th to 95th percentile) with b
    at its 5th and its 95th percentile (§5.3, D22).

    amplification: both effects significantly of one sign, the effect significantly larger in size at high b,
                   and a pair share band at or above `pair_share`.
    sign_flip:     the two effects are significant and of opposite signs.
    none:          as "negligible" for the pair (module docstring); a pair the model lacks is none."""
    lex = lex or load()
    t = term(facts, f"{a}{PAIR_SEPARATOR}{b}", lex)
    if t is None:
        return _unknown(f"{a}{PAIR_SEPARATOR}{b}")
    if not t.present:
        value = TRUE if pattern == "none" else FALSE
        return Verdict(value, {"term": t.name, "in the model": False}, "the model has no such pair")
    p = facts.pair(a, b)
    c = next(c for c in p.conditional if c.feature == a)
    low, high, diff = interval(c.at_low), interval(c.at_high), interval(c.difference)
    share_band = interval(t.share)
    if pattern == "amplification":
        positive = low[0] > 0 and high[0] > 0 and diff[0] > 0
        negative = low[1] < 0 and high[1] < 0 and diff[1] < 0
        not_positive = diff[1] <= 0 or low[1] < 0 or high[1] < 0
        not_negative = diff[0] >= 0 or low[0] > 0 or high[0] > 0
        value = _judge((positive or negative) and share_band[0] >= lex.pair_share, share_band[1] < lex.pair_share or (not_positive and not_negative))
    elif pattern == "sign_flip":
        flips = (low[0] > 0 and high[1] < 0) or (low[1] < 0 and high[0] > 0)
        same = (low[0] > 0 and high[0] > 0) or (low[1] < 0 and high[1] < 0)
        value = _judge(flips, same)
    else:
        edge, moderate = lex.pair_share, lex.strength["moderate"]
        small = share_band[1] < edge or (not t.detectable and t.share.value < edge and share_band[1] < moderate)
        value = _judge(small, share_band[0] >= edge and t.detectable)
    evidence = _share_evidence(t) | {
        "effect of": a, "moderator": b, "moderator values": c.moderator_values,
        "effect at low": c.at_low.value, "effect at low band": low, "effect at high": c.at_high.value,
        "effect at high band": high, "difference band": diff,
    }  # fmt: skip
    return Verdict(value, evidence)


# --- the hedge ---------------------------------------------------------------------------------------------


def unsettled(claim: Verdict) -> Verdict:
    """"the data do not settle whether ..." (D30), given the verdict on the claim it hedges: true only if that
    claim is undecidable for insufficient evidence. False if the claim is decided either way, so a settled fact
    cannot be hedged and hedging everything does not pass the gate, and false if the claim names a term the
    model does not have or does not apply to its term, so a hedge cannot cover an invented term."""
    hedged = claim.value == UNDECIDABLE and claim.code == INSUFFICIENT_EVIDENCE
    if hedged:
        reason = "the evidence does not settle the claim"
    elif claim.value == UNDECIDABLE:
        reason = f"nothing to hedge: {claim.reason}"
    else:
        reason = f"the claim is settled: it is {claim.value}"
    evidence = {"claim verdict": claim.value, "claim code": claim.code, "claim reason": claim.reason, **claim.evidence}
    return Verdict(TRUE if hedged else FALSE, evidence, reason)
