"""The Facts format: one machine-readable summary per fitted model, the only thing the verifier sees (§5.1).

It holds everything the lexicon checks, with its uncertainty, and every number traces back to the model: the
step functions are the model's own terms (purified, centred, facts/steps.py), exactly, so `Facts.steps()`
gives back a model whose logit equals the fitted model's on any row.

Per feature (main term): the curve as steps (cuts, scores), the share of training rows in each step (mass),
pointwise and simultaneous 95% bands, importance (mean |score|) and share of the total importance with
bands, rank among the features with its band, and the net change of the term between the feature's 5th and
95th percentile with its band.

Per pair: the score grid with its cuts and mass, importance and share with bands, and for each of its two
features the conditional effect, main + pair, from the feature's 5th to its 95th percentile, with the other
feature held at its 5th and at its 95th percentile, and the difference of the two, each with a band (§5.3).

Bands come from bootstrap refits (Poisson weights, §14.2 D17; facts/bootstrap.py, facts/build.py). The refit
values themselves (Draws) are saved next to the JSON, so derived quantities the lexicon needs later get joint
bands without refitting.

Steps follow facts/steps.py: a value x is in step i = #{cuts <= x}.
"""

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from verifier_gate.facts.steps import StepModel, StepTerm

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class Estimate:
    value: float
    band: tuple[float, float] | None = None  # 95% percentile interval of the refits; None without refits

    def to_json(self) -> dict:
        return {"value": self.value, "band": None if self.band is None else list(self.band)}

    @classmethod
    def from_json(cls, d: Mapping) -> "Estimate":
        return cls(d["value"], None if d["band"] is None else tuple(d["band"]))


@dataclass(frozen=True, eq=False)
class FeatureFacts:
    name: str
    cuts: np.ndarray  # (k,)
    scores: np.ndarray  # (k + 1,), logits, centred on the training sample
    mass: np.ndarray  # (k + 1,), share of training rows per step
    pointwise: np.ndarray | None  # (2, k + 1): lower, upper; M +- 1.96 sd of the refits
    simultaneous: np.ndarray | None  # (2, k + 1): M +- c sd, c the sup-t critical value
    critical_value: float | None  # c
    importance: Estimate
    share: Estimate
    rank: Estimate  # among the features, 1 = largest importance
    low_high: tuple[float, float]  # 5th and 95th percentile of the feature on the training sample
    net_change: Estimate  # term(high) - term(low)

    def to_json(self) -> dict:
        bands = {k: None if v is None else v.tolist() for k, v in (("pointwise", self.pointwise), ("simultaneous", self.simultaneous))}
        return {
            "name": self.name,
            "cuts": self.cuts.tolist(),
            "scores": self.scores.tolist(),
            "mass": self.mass.tolist(),
            **bands,
            "critical_value": self.critical_value,
            **{k: getattr(self, k).to_json() for k in ("importance", "share", "rank")},
            "low_high": list(self.low_high),
            "net_change": self.net_change.to_json(),
        }

    @classmethod
    def from_json(cls, d: Mapping) -> "FeatureFacts":
        array = lambda v: None if v is None else np.asarray(v, dtype=np.float64)  # noqa: E731
        return cls(
            d["name"], array(d["cuts"]), array(d["scores"]), array(d["mass"]), array(d["pointwise"]),
            array(d["simultaneous"]), d["critical_value"], *(Estimate.from_json(d[k]) for k in ("importance", "share", "rank")),
            tuple(d["low_high"]), Estimate.from_json(d["net_change"]),
        )  # fmt: skip


@dataclass(frozen=True)
class ConditionalEffect:
    """Effect of `feature` from low to high on main(feature) + pair, with `moderator` held at low and high."""

    feature: str
    moderator: str
    feature_values: tuple[float, float]  # 5th, 95th percentile
    moderator_values: tuple[float, float]  # 5th, 95th percentile
    at_low: Estimate
    at_high: Estimate
    difference: Estimate  # at_high - at_low

    @property
    def key(self) -> str:
        return f"{self.feature} | {self.moderator}"

    def to_json(self) -> dict:
        return {
            "feature": self.feature,
            "moderator": self.moderator,
            "feature_values": list(self.feature_values),
            "moderator_values": list(self.moderator_values),
            **{k: getattr(self, k).to_json() for k in ("at_low", "at_high", "difference")},
        }

    @classmethod
    def from_json(cls, d: Mapping) -> "ConditionalEffect":
        return cls(
            d["feature"], d["moderator"], tuple(d["feature_values"]), tuple(d["moderator_values"]),
            *(Estimate.from_json(d[k]) for k in ("at_low", "at_high", "difference")),
        )  # fmt: skip


@dataclass(frozen=True, eq=False)
class PairFacts:
    name: str
    features: tuple[str, str]
    cuts: tuple[np.ndarray, np.ndarray]
    scores: np.ndarray  # (k_a + 1, k_b + 1), purified, logits
    mass: np.ndarray  # same shape, share of training rows per cell
    importance: Estimate
    share: Estimate
    conditional: tuple[ConditionalEffect, ConditionalEffect]  # feature = features[0], then features[1]

    def to_json(self) -> dict:
        return {
            "name": self.name,
            "features": list(self.features),
            "cuts": [c.tolist() for c in self.cuts],
            "scores": self.scores.tolist(),
            "mass": self.mass.tolist(),
            "importance": self.importance.to_json(),
            "share": self.share.to_json(),
            "conditional": [c.to_json() for c in self.conditional],
        }

    @classmethod
    def from_json(cls, d: Mapping) -> "PairFacts":
        return cls(
            d["name"], tuple(d["features"]), tuple(np.asarray(c, dtype=np.float64) for c in d["cuts"]),
            np.asarray(d["scores"], dtype=np.float64), np.asarray(d["mass"], dtype=np.float64),
            Estimate.from_json(d["importance"]), Estimate.from_json(d["share"]),
            tuple(ConditionalEffect.from_json(c) for c in d["conditional"]),
        )  # fmt: skip


@dataclass(eq=False)
class Draws:
    """Refit values on M's grid, one row per refit (facts/bootstrap.py)."""

    curves: dict[str, np.ndarray] = field(default_factory=dict)  # feature -> (refits, steps)
    importance: dict[str, np.ndarray] = field(default_factory=dict)  # term -> (refits,)
    share: dict[str, np.ndarray] = field(default_factory=dict)
    rank: dict[str, np.ndarray] = field(default_factory=dict)  # feature -> (refits,)
    net_change: dict[str, np.ndarray] = field(default_factory=dict)
    conditional: dict[str, np.ndarray] = field(default_factory=dict)  # "feature | moderator" -> (refits, 2)

    KINDS = ("curves", "importance", "share", "rank", "net_change", "conditional")

    @property
    def refits(self) -> int:
        return len(next(iter(self.importance.values())))

    @classmethod
    def stack(cls, reads: list[dict]) -> "Draws":
        """From one `Frame.read` per refit."""
        return cls(**{kind: {k: np.stack([r[kind][k] for r in reads]) for k in reads[0][kind]} for kind in cls.KINDS})

    def save(self, path: Path) -> None:
        np.savez_compressed(path, **{f"{kind}/{k}": v for kind in self.KINDS for k, v in getattr(self, kind).items()})

    @classmethod
    def load(cls, path: Path) -> "Draws":
        draws = cls()
        with np.load(path) as stored:
            for key in stored.files:
                kind, name = key.split("/", 1)
                getattr(draws, kind)[name] = stored[key]
        return draws


@dataclass(eq=False)
class Facts:
    model: dict  # kind, scenario, n, seed, parameters, software versions
    bands: dict  # refits, level, weights, methods
    intercept: float
    features: tuple[FeatureFacts, ...]
    pairs: tuple[PairFacts, ...]
    draws: Draws | None = None  # not part of the JSON; saved next to it

    def feature(self, name: str) -> FeatureFacts:
        return next(f for f in self.features if f.name == name)

    def pair(self, a: str, b: str) -> PairFacts | None:
        """The pair on features a and b, in either order; None if the model has no such pair."""
        return next((p for p in self.pairs if set(p.features) == {a, b}), None)

    def steps(self) -> StepModel:
        """The model back from its facts: logit(x) equals the fitted model's margin on any x."""
        terms = {f.name: StepTerm((f.name,), (f.cuts,), f.scores) for f in self.features}
        terms |= {p.name: StepTerm(p.features, p.cuts, p.scores) for p in self.pairs}
        return StepModel(self.intercept, terms)

    def to_json(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "model": self.model,
            "bands": self.bands,
            "intercept": self.intercept,
            "features": [f.to_json() for f in self.features],
            "pairs": [p.to_json() for p in self.pairs],
        }

    @classmethod
    def from_json(cls, d: Mapping) -> "Facts":
        if d["schema_version"] != SCHEMA_VERSION:
            raise ValueError(f"schema version {d['schema_version']}, expected {SCHEMA_VERSION}")
        return cls(
            d["model"], d["bands"], d["intercept"],
            tuple(FeatureFacts.from_json(f) for f in d["features"]), tuple(PairFacts.from_json(p) for p in d["pairs"]),
        )  # fmt: skip

    def save(self, path: Path) -> None:
        """path.json, and path.npz with the draws if any."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.with_suffix(".json").write_text(json.dumps(self.to_json()))
        if self.draws is not None:
            self.draws.save(path.with_suffix(".npz"))

    @classmethod
    def load(cls, path: Path, draws: bool = True) -> "Facts":
        path = Path(path)
        facts = cls.from_json(json.loads(path.with_suffix(".json").read_text()))
        if draws and path.with_suffix(".npz").exists():
            facts.draws = Draws.load(path.with_suffix(".npz"))
        return facts
