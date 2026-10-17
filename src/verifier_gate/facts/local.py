"""Local facts for the spot check's adverse-action reasons (D47, D49; plan §14.20).

For one declined applicant x and one model M (EBM or XGB2, both additive):

- Decision rule: declined if M's logit is in the riskiest DECLINE_SHARE of the training sample (approval rate
  80%). The cutoff is M's own quantile, so each model declines its own applicants.
- Reference R: the REFERENCE_SIZE approved applicants closest to the cutoff, i.e. the riskiest approved
  ("comparable passing applicants", Sudjianto 2026), unweighted; leaf-proximity weights stay in the thesis.
- Contribution of term t: c_t = f_t(x) - mean over R of f_t(r), for every main term and pair. Exact for an
  additive model, without SHAP: the contributions sum to the score gap logit(x) - mean over R of logit(r),
  since the intercept cancels.
- Rank: 1 + the number of terms with a strictly larger contribution, so 1 is the term that pushes hardest
  towards the decline, contributions in the applicant's favour rank last, and ties share a rank.
- Fraction: c_t over the score gap. A reason is material from MATERIALITY of the gap, and a notice gives at
  most MAX_REASONS (D49).
- Bands: the same quantities in each refit (facts/refits.py), with x and R held fixed; 2.5th and 97.5th
  percentile, as for the global scalars (facts/build.py). A term of M that a refit lacks counts as zero; a
  refit's terms that M lacks count in its gap but are never a reason; ranks are among M's terms. The draws are
  kept, so claims that combine two quantities (material and among the first four) get joint verdicts.
- Truth: T's terms evaluated the same way, on the same x and R. Terms of M and T are matched by their
  features. A term only T has is listed with M's contribution 0 and no rank under M; T's ranks are over all
  listed terms, with zero for a term T lacks.
- Values: the applicant's value and the reference's median of each feature, for wording against the
  measurement ("high utilization" needs a value above the reference's; Sudjianto 2026 §5.2).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.special import expit

from verifier_gate.facts.build import percentile_band
from verifier_gate.facts.schema import Estimate, Facts
from verifier_gate.facts.steps import StepModel

DECLINE_SHARE = 0.20
REFERENCE_SIZE = 500
MATERIALITY = 0.10
MAX_REASONS = 4
APPLICANTS = 9  # per model and dataset (D49: 3 datasets x 2 models x 9 = 54 notices)
SAMPLE_SEED = 20261016


@dataclass(frozen=True)
class Decision:
    cutoff: float  # logit at the (1 - DECLINE_SHARE) quantile
    declined: np.ndarray  # row indices
    reference: np.ndarray  # row indices of R, sorted


def decide(model: StepModel, X: pd.DataFrame) -> Decision:
    logit = model.logit(X)
    cutoff = float(np.quantile(logit, 1.0 - DECLINE_SHARE))
    declined = np.flatnonzero(logit >= cutoff)
    approved = np.flatnonzero(logit < cutoff)
    closest = approved[np.argsort(-logit[approved], kind="stable")][:REFERENCE_SIZE]
    return Decision(cutoff, declined, np.sort(closest))


def draw_applicants(decision: Decision, key: Sequence[int], k: int = APPLICANTS) -> np.ndarray:
    """k declined applicants at random, from the generator seeded by SAMPLE_SEED and key (dataset seed,
    interaction index, model index)."""
    return np.sort(np.random.default_rng([SAMPLE_SEED, *key]).choice(decision.declined, size=k, replace=False))


def _terms_by_features(model) -> dict[frozenset, str]:
    """Term name by its set of features, for a StepModel or for T (dgp.Truth, plasmode's truth)."""
    if isinstance(model, StepModel):
        return {frozenset(t.features): n for n, t in model.steps.items()}
    return {frozenset(model.term_features(n)): n for n in model.term_names}


def contributions(model, X: pd.DataFrame, rows: np.ndarray, reference: np.ndarray) -> dict[frozenset, np.ndarray]:
    """c_t for each row in rows, by the term's set of features."""
    at, ref = X.iloc[rows], X.iloc[reference]
    return {
        key: np.asarray(model.term(name, at), dtype=np.float64) - float(np.mean(model.term(name, ref)))
        for key, name in _terms_by_features(model).items()
    }


def competition_rank(values: np.ndarray) -> np.ndarray:
    """1 + the number of strictly larger values, along the last axis."""
    return 1 + (values[..., None, :] > values[..., :, None]).sum(axis=-1)


@dataclass(frozen=True)
class Reason:
    """One term's local facts for one applicant."""

    term: str
    contribution: Estimate  # c_t under M, with its band
    fraction: Estimate  # c_t / score gap
    rank: Estimate | None  # among M's terms; None for a term only T has
    truth: float  # c_t under T (0 if T lacks the term)
    truth_fraction: float  # over T's score gap
    truth_rank: int

    def to_json(self) -> dict:
        return {
            "term": self.term,
            **{k: getattr(self, k).to_json() for k in ("contribution", "fraction")},
            "rank": None if self.rank is None else self.rank.to_json(),
            "truth": self.truth,
            "truth_fraction": self.truth_fraction,
            "truth_rank": self.truth_rank,
        }

    @classmethod
    def from_json(cls, d: Mapping) -> "Reason":
        return cls(
            d["term"], Estimate.from_json(d["contribution"]), Estimate.from_json(d["fraction"]),
            None if d["rank"] is None else Estimate.from_json(d["rank"]), d["truth"], d["truth_fraction"], d["truth_rank"],
        )  # fmt: skip


@dataclass(frozen=True)
class Value:
    feature: str
    applicant: float
    reference_median: float


@dataclass(eq=False)
class LocalFacts:
    """The facts of one notice: one declined applicant under one model."""

    model: dict  # kind, scenario, row, decision rule
    risk: float  # M's predicted default probability for the applicant
    reference_risk: float  # mean over R
    gap: Estimate  # logit(x) - mean logit over R, under M, with its band
    truth_gap: float
    reasons: tuple[Reason, ...]  # M's terms by M's contribution, largest first; then the terms only T has
    values: tuple[Value, ...]
    draws: dict[str, np.ndarray] | None = None  # "contribution" (refits, M's terms in the order of reasons), "gap" (refits,)
    model_facts: Facts | None = field(default=None, repr=False)  # M's global Facts, for a global claim in a notice; not saved

    def reason(self, term: str) -> Reason | None:
        key = frozenset(term.split(" & "))
        return next((r for r in self.reasons if frozenset(r.term.split(" & ")) == key), None)

    def value(self, feature: str) -> Value | None:
        return next((v for v in self.values if v.feature == feature), None)

    def to_json(self) -> dict:
        return {
            "model": self.model,
            "risk": self.risk,
            "reference_risk": self.reference_risk,
            "gap": self.gap.to_json(),
            "truth_gap": self.truth_gap,
            "reasons": [r.to_json() for r in self.reasons],
            "values": [vars(v) for v in self.values],
            "draws": None if self.draws is None else {k: v.tolist() for k, v in self.draws.items()},
        }

    @classmethod
    def from_json(cls, d: Mapping) -> "LocalFacts":
        draws = None if d["draws"] is None else {k: np.asarray(v, dtype=np.float64) for k, v in d["draws"].items()}
        return cls(
            d["model"], d["risk"], d["reference_risk"], Estimate.from_json(d["gap"]), d["truth_gap"],
            tuple(Reason.from_json(r) for r in d["reasons"]), tuple(Value(**v) for v in d["values"]), draws,
        )  # fmt: skip


def _estimate(value: float, draws: np.ndarray | None) -> Estimate:
    return Estimate(float(value), None if draws is None else percentile_band(draws))


def local_facts(
    M: StepModel, refits: Sequence[StepModel] | None, truth, X: pd.DataFrame, rows: np.ndarray, decision: Decision,
    model: Mapping | None = None,
) -> list[LocalFacts]:  # fmt: skip
    """LocalFacts for each applicant in rows, under M, with bands from refits (None: no bands)."""
    R = decision.reference
    own = contributions(M, X, rows, R)
    keys = list(own)  # M's terms, in M's order
    names = _terms_by_features(M)
    true = contributions(truth, X, rows, R)
    only_truth = [k for k in true if k not in own]
    truth_names = _terms_by_features(truth)
    listed = keys + only_truth

    values_m = np.stack([own[k] for k in keys], axis=-1)  # (applicants, M's terms)
    gap_m = values_m.sum(axis=-1)
    values_t = np.stack([true.get(k, np.zeros(len(rows))) for k in listed], axis=-1)  # (applicants, listed)
    gap_t = sum(true.values())

    if refits:
        per_refit, gaps = [], []
        for refit in refits:
            c = contributions(refit, X, rows, R)
            per_refit.append(np.stack([c.get(k, np.zeros(len(rows))) for k in keys], axis=-1))
            gaps.append(sum(c.values()))
        draws_c = np.stack(per_refit, axis=1)  # (applicants, refits, M's terms)
        draws_g = np.stack(gaps, axis=1)  # (applicants, refits)
    logit = M.logit(X.iloc[rows])
    reference_risk = float(np.mean(expit(M.logit(X.iloc[R]))))
    ref_medians = {f: float(np.median(X[f].iloc[R])) for f in M.features}

    out = []
    for i, row in enumerate(rows):
        rank_m = competition_rank(values_m[i])
        rank_t = competition_rank(values_t[i])
        d_c = draws_c[i] if refits else None
        d_g = draws_g[i] if refits else None
        d_rank = competition_rank(d_c) if refits else None
        reasons = []
        for j, key in enumerate(keys):
            reasons.append(
                Reason(
                    names[key],
                    _estimate(values_m[i, j], None if d_c is None else d_c[:, j]),
                    _estimate(values_m[i, j] / gap_m[i], None if d_c is None else d_c[:, j] / d_g),
                    _estimate(rank_m[j], None if d_rank is None else d_rank[:, j].astype(np.float64)),
                    float(values_t[i, j]), float(values_t[i, j] / gap_t[i]), int(rank_t[j]),
                )  # fmt: skip
            )
        order = sorted(range(len(reasons)), key=lambda j: -values_m[i, j])
        reasons = [reasons[j] for j in order]
        for j, key in enumerate(only_truth, start=len(keys)):
            reasons.append(
                Reason(
                    truth_names[key], Estimate(0.0, (0.0, 0.0) if refits else None), Estimate(0.0, (0.0, 0.0) if refits else None),
                    None, float(values_t[i, j]), float(values_t[i, j] / gap_t[i]), int(rank_t[j]),
                )  # fmt: skip
            )
        draws = None if not refits else {"contribution": d_c[:, order], "gap": d_g}
        out.append(
            LocalFacts(
                {**(model or {}), "row": int(row), "cutoff": decision.cutoff, "decline_share": DECLINE_SHARE,
                 "reference_size": len(R), "materiality": MATERIALITY, "max_reasons": MAX_REASONS,
                 "refits": len(refits) if refits else 0},
                float(expit(logit[i])), reference_risk, _estimate(gap_m[i], d_g), float(gap_t[i]), tuple(reasons),
                tuple(Value(f, float(X[f].iloc[row]), ref_medians[f]) for f in M.features), draws,
            )  # fmt: skip
        )
    return out
