"""The readable form of a curve for the handover, and its check against the exact model (plan §5.4, §14.8).

The prompt shows each feature's curve in a readable form, not the exact model. Rounding alone can invent a jump
that M lacks (steps at 0.249 and 0.251 become 0.2 and 0.3) or hide one the verifier detects. So the readable
curve is M at the resolution of its simultaneous band, the band the lexicon judges shapes on:

- pieces: constant values, each inside the band of every step it covers, chosen left to right with the fewest
  pieces that fit (greedy, optimal for this one-dimensional problem), each value the shortest decimal inside the
  band nearest M's mass-weighted mean. Every movement between neighbouring pieces is then significant in M's
  band, in the direction shown, and every significant movement of M (two steps whose bands do not overlap) is
  shown in its direction, so every exception the lexicon detects is visible.
- net change only: one piece fits the band everywhere, but the net change from the 5th to the 95th percentile, a
  single contrast with more power than the band, is significant: the curve "rises by d from the 5th to the 95th
  percentile; the shape in between is not resolved at this sample size". Without this case a weak feature at
  n = 5,000 would read as flat while the lexicon certifies its direction (§14.8: a shape the writer could have
  stated, not shown).
- flat: neither.

The check (§5.4) runs on every result anyway, since the construction is what it tests:
1. size: the largest gap between the readable curve and M on the steps that hold training rows, against the
   band's half-width there (inside the band by construction);
2. shape: neighbouring pieces whose movement no pair of their steps shows significantly; pairs of steps with a
   significant movement the readable curve does not show in its direction; a direction the lexicon certifies
   (word or set) that the readable form does not show; and a certified threshold or peak whose readable location
   is not within the window w of the certified one.
Shares and ranks are not recomputed from the readable curves (§5.4 as first written): the handover states them as
numbers from M with their bands, so the curve carries only the shape. Refined 14 Oct, before any handover was built.
"""

from dataclasses import dataclass, field
from decimal import Decimal

import numpy as np

from verifier_gate.dsl.grammar import Claim
from verifier_gate.facts.schema import Facts, FeatureFacts
from verifier_gate.lexicon import predicates as p

MAX_DECIMALS = 6


@dataclass(frozen=True)
class Piece:
    first: int  # step index range [first, last]
    last: int
    value: float
    decimals: int


@dataclass(frozen=True)
class Readable:
    feature: str
    kind: str  # "pieces", "net change only", "flat"
    pieces: tuple[Piece, ...]
    cuts: np.ndarray  # M's cuts (pieces start and end at them)
    count: bool  # integer-valued feature: pieces are described by the values they cover
    net_change: tuple[float, tuple[float, float]]
    low_high: tuple[float, float]

    def on_steps(self, steps: int) -> np.ndarray:
        values = np.empty(steps)
        for piece in self.pieces:
            values[piece.first : piece.last + 1] = piece.value
        return values


def simplest(lo: float, hi: float, target: float) -> tuple[float, int]:
    """The value in [lo, hi] with the fewest decimals, nearest the target among those."""
    target = min(max(target, lo), hi)
    for decimals in range(MAX_DECIMALS + 1):
        unit = 10.0**-decimals
        candidates = np.arange(np.ceil(lo / unit - 1e-9), np.floor(hi / unit + 1e-9) + 1) * unit
        if len(candidates):
            return float(round(candidates[np.argmin(np.abs(candidates - target))], decimals)), decimals
    return float(round(target, MAX_DECIMALS)), MAX_DECIMALS


def fit_pieces(scores: np.ndarray, mass: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> list[Piece]:
    """Fewest constant pieces, left to right, each inside the band of every step with rows it covers. Steps
    without rows join the piece they fall in."""
    pieces, first, lo, hi = [], 0, -np.inf, np.inf

    def close(last: int) -> None:
        held = mass[first : last + 1]
        mean = float(np.average(scores[first : last + 1], weights=held)) if held.sum() > 0 else float(scores[first])
        value, decimals = simplest(lo, hi, mean) if np.isfinite(lo) else (mean, MAX_DECIMALS)
        pieces.append(Piece(first, last, value, decimals))

    for i in range(len(scores)):
        if mass[i] <= 0:
            continue
        new_lo, new_hi = max(lo, lower[i]), min(hi, upper[i])
        if new_lo > new_hi:
            close(i - 1)
            first, lo, hi = i, lower[i], upper[i]
        else:
            lo, hi = new_lo, new_hi
    close(len(scores) - 1)
    return pieces


def readable(f: FeatureFacts, count: bool = False) -> Readable:
    if f.simultaneous is None:
        raise ValueError(f"{f.name}: the readable form needs bands (Facts of a fitted model or the oracle)")
    lower, upper = f.simultaneous
    pieces = fit_pieces(f.scores, f.mass, lower, upper)
    net = p.interval(f.net_change)
    if len(pieces) > 1:
        kind = "pieces"
    elif net[0] > 0 or net[1] < 0:
        kind = "net change only"
    else:
        kind = "flat"
    return Readable(f.name, kind, tuple(pieces), f.cuts, count, (f.net_change.value, net), f.low_high)


# --- the check ---------------------------------------------------------------------------------------------


@dataclass
class Check:
    feature: str
    kind: str
    pieces: int
    largest_gap: float  # logits, over steps with rows
    gap_over_half_width: float  # <= 1: inside the band
    shown_not_significant: int
    significant_not_shown: int
    direction_hidden: list[str] = field(default_factory=list)
    location_off: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return (self.gap_over_half_width <= 1 + 1e-9 and not self.shown_not_significant and not self.significant_not_shown
                and not self.direction_hidden and not self.location_off)  # fmt: skip


def _significant(lower: np.ndarray, upper: np.ndarray, held: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Pairs i < j of steps with rows whose bands show a significant rise (up) or fall (down) from i to j."""
    lo, hi = lower[held], upper[held]
    later = np.triu(np.ones((len(lo), len(lo)), dtype=bool), k=1)
    return later & (hi[:, None] < lo[None, :]), later & (lo[:, None] > hi[None, :])


def _shown_direction(r: Readable, f: FeatureFacts) -> int:
    """+1, -1 or 0: the direction the readable form shows from the 5th to the 95th percentile. The pieces decide
    where they move there; where they do not, the net change does if it is significant (the description always
    states it with its band)."""
    values = r.on_steps(len(f.scores))
    low, high = (np.searchsorted(f.cuts, x, side="right") for x in f.low_high)
    pieces = int(np.sign(values[high] - values[low])) if r.kind == "pieces" else 0
    net, band = r.net_change
    significant = band[0] > 0 or band[1] < 0
    return pieces if pieces or not significant else int(np.sign(net))


def _jump_location(r: Readable) -> float | None:
    if len(r.pieces) < 2:
        return None
    jumps = [abs(b.value - a.value) for a, b in zip(r.pieces, r.pieces[1:])]
    k = int(np.argmax(jumps))
    return float(r.cuts[r.pieces[k + 1].first - 1])


def _highest_span(r: Readable, f: FeatureFacts) -> tuple[float, float]:
    top = max(r.pieces, key=lambda piece: piece.value)
    lower_edge = r.cuts[top.first - 1] if top.first > 0 else -np.inf
    upper_edge = r.cuts[top.last] if top.last < len(r.cuts) else np.inf
    return float(lower_edge), float(upper_edge)


def check(r: Readable, facts: Facts, certified: list[Claim], lex: p.Lexicon | None = None) -> Check:
    """certified: what the verifier certifies about the model (verifier/certified.py), for directions, jumps
    and peaks."""
    lex = lex or p.load()
    f = facts.feature(r.feature)
    lower, upper = f.simultaneous
    held = f.mass > 0
    values = r.on_steps(len(f.scores))
    gap = np.abs(values - f.scores)[held]
    half_width = np.maximum((upper - lower)[held] / 2, 1e-12)
    up, down = _significant(lower, upper, held)
    v = values[held]
    significant_not_shown = int((up & ~(v[None, :] > v[:, None])).sum() + (down & ~(v[None, :] < v[:, None])).sum())
    shown_not_significant = 0
    for a, b in zip(r.pieces, r.pieces[1:]):
        left, right = slice(a.first, a.last + 1), slice(b.first, b.last + 1)
        la, ua, lb, ub = (x[s][held[s]] for x, s in ((lower, left), (upper, left), (lower, right), (upper, right)))
        rise = b.value > a.value
        significant = (ua.min() < lb.max()) if rise else (la.max() > ub.min())
        shown_not_significant += 0 if (len(la) and len(lb) and significant) else 1
    result = Check(r.feature, r.kind, len(r.pieces), float(gap.max()), float((gap / half_width).max()),
                   shown_not_significant, significant_not_shown)  # fmt: skip
    mine = [c for c in certified if c.terms == (r.feature,)]
    shown = _shown_direction(r, f)
    for c in mine:
        if c.kind == "direction":
            words = c.value if isinstance(c.value, tuple) else (c.value,)
            sign = p.DIRECTIONS[words[0]][0]
            if shown != sign:
                result.direction_hidden.append(str(c))
    w = lex.window * (f.low_high[1] - f.low_high[0])
    for c in mine:
        if c.kind == "threshold":
            at = _jump_location(r)
            if at is None or abs(at - c.value) > w:
                result.location_off.append(str(c))
        if c.kind == "peak" and r.pieces:
            lo, hi = _highest_span(r, f)
            if max(lo - c.value, c.value - hi, 0.0) > w:
                result.location_off.append(str(c))
    return result


# --- text --------------------------------------------------------------------------------------------------


def _x(value: float) -> str:
    if abs(value) >= 1000:
        return f"{float(f'{value:.3g}'):,.0f}"
    return f"{value:.3g}"


def _value(piece: Piece) -> str:
    if piece.value == 0:
        return "0"
    return f"{Decimal(str(piece.value)):+.{piece.decimals}f}"


def describe(r: Readable) -> str:
    """The readable curve as text for the handover: logit contribution by range of the feature."""
    low, high = r.low_high
    net, band = r.net_change
    net_text = f"net change from the 5th to the 95th percentile {net:+.2f}, 95% band [{band[0]:+.2f}, {band[1]:+.2f}]"
    if r.kind == "flat":
        return (f"no movement resolved at this sample size (net change from the 5th to the 95th percentile "
                f"{net:+.2f}, 95% band [{band[0]:+.2f}, {band[1]:+.2f}])")  # fmt: skip
    if r.kind == "net change only":
        verb = "rises" if net > 0 else "falls"
        return (f"{verb} by {abs(net):.2f} (95% band [{band[0]:+.2f}, {band[1]:+.2f}]) from x = {_x(low)} (5th "
                f"percentile) to x = {_x(high)} (95th percentile); the shape in between is not resolved at this "
                f"sample size")  # fmt: skip
    parts = []
    for k, piece in enumerate(r.pieces):
        start = r.cuts[piece.first - 1] if piece.first > 0 else None
        end = r.cuts[piece.last] if piece.last < len(r.cuts) else None
        if r.count:
            first = None if start is None else int(np.ceil(start - 1e-9))
            last = None if end is None else int(np.ceil(end - 1e-9)) - 1
            if first is None:
                first = 0 if last == 0 else None
            where = (f"{first}" if first == last else f"{first}-{last}") if first is not None and last is not None else (
                f"<= {last}" if first is None else f">= {first}")  # fmt: skip
        else:
            where = f"x < {_x(end)}" if start is None else (f"x >= {_x(start)}" if end is None else f"{_x(start)} <= x < {_x(end)}")
        parts.append(f"{where}: {_value(piece)}")
    return "; ".join(parts) + f" ({net_text})"
