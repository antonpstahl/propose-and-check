"""Calibration of the lexicon on the discovery seed, and the +-50% sensitivity analysis (plan §14.9, D16).

Rule, fixed before the run (14 Oct, plan §14.9). Data: seed 1 only, 6 datasets. References (D16): the oracle's
verdicts on the labelled claims (data/planted.py) and the noise features of every model (EBM, XGB2, oracle).
The fitted models' Facts are loaded without draws and only their noise features are read: no verdict of a
fitted model on a planted feature is computed before the lexicon is frozen.

Criteria, all must hold:
1. Noise is never an effect: on the 36 noise curves (2 features x 6 datasets x 3 models) no strength class and
   no strength set that leaves out "negligible" is true (EFFECT).
2. Noise is never refuted as negligible: "negligible" and "at most weak" are never false (AT_MOST).
3. The oracle makes no confident error at n = 50,000: of its 507 labelled claims, no false claim is certified
   and no true claim refuted.
Guard rail: T's labels do not change. The lexicon on T reproduces every label of seed 1 (the scorer test), and
`exception_mass` stays above T's exception mass for history on every seed-1 dataset.

Decision rule: run v0; if everything holds, nothing moves. Only the thresholds in GRID may move, only up, and
only when a failure implicates them: `detectable_mass` when a criterion-1 or -2 failure is on a curve that is
detectable through its curve band and not through its net change; `exception_mass` when a criterion-3 failure
is a "mostly" claim whose detected exception mass exceeds it. Candidates are tried by their number of grid
steps, and the first that passes everything gives v1. If none does, or a failure implicates no threshold, v1
keeps v0's values and the failure is reported. No threshold moves to raise the decided rate.

Sensitivity analysis (reported, never used to choose): each threshold in SWEEP at 0.5x and 1.5x its v1 value,
one at a time, the others at v1: criteria 1-3, the guard rail, the oracle's D31 summary at both n, and how many
of T's labels change, the labels recomputed as the perturbed lexicon's verdicts on T (the truth depends on the
thresholds too). Direction verdicts on the noise features are reported, not a criterion: a significant net
change is a 5% event per curve by the band level, not a lexicon threshold.

Run: `uv run python -m verifier_gate.experiments.calibrate` (about two minutes, after build_facts). Writes
results/calibration/: steps.csv (every lexicon the rule tried), noise.csv and oracle.csv (verdicts under v1),
sensitivity.csv.
"""

import itertools
from collections.abc import Callable
from dataclasses import dataclass, replace
from functools import cached_property
from pathlib import Path

import numpy as np
import pandas as pd

from verifier_gate.data import dgp
from verifier_gate.data.planted import planted_claims
from verifier_gate.dsl.grammar import Claim
from verifier_gate.experiments import metrics
from verifier_gate.experiments.build_facts import load
from verifier_gate.facts.schema import Facts
from verifier_gate.lexicon import predicates as p
from verifier_gate.lexicon.predicates import FALSE, STRENGTHS, TRUE, UNDECIDABLE
from verifier_gate.verifier.verify import verify

SCENARIOS = tuple(s for s in dgp.SCENARIOS if s.is_discovery)
LARGE = max(dgp.SAMPLE_SIZES)
NOISE = tuple(f for f, role in dgp.FEATURE_ROLES.items() if role == "noise")
NULL_MODELS = ("EBM", "XGB2", "oracle")
EFFECT = (*((s,) for s in STRENGTHS), ("weak", "moderate"), ("moderate", "strong"), ("weak", "moderate", "strong"))
AT_MOST = (("negligible",), ("negligible", "weak"))
GRID = {"detectable_mass": (0.10, 0.20), "exception_mass": (0.125, 0.15)}  # v0: 0.05 and 0.10; up only
SWEEP = ("weak", "moderate", "strong", "detectable_mass", "share_absolute", "share_relative", "exception_mass",
         "window", "jump_fraction", "pair_share")  # fmt: skip
FACTORS = (0.5, 1.5)
ERRORS = (metrics.RELEASED_WRONG, metrics.BLOCKED_CORRECT)
RESULTS = Path(__file__).parents[3] / "results" / "calibration"


@dataclass(frozen=True)
class Dataset:
    scenario: dgp.Scenario
    claims: tuple[tuple[Claim, str], ...]  # the frozen label set
    facts: dict[str, Facts]  # T, the oracle, and the fitted models without draws
    history_exception: float  # T's exception mass for history


def load_discovery(lex: p.Lexicon) -> list[Dataset]:
    out = []
    for s in SCENARIOS:
        facts = {"T": load(s, "T"), "oracle": load(s, "oracle")} | {k: load(s, k, draws=False) for k in ("EBM", "XGB2")}
        history = facts["T"].feature("history_months")
        lower, upper = p.curve_band(history)
        exception = p.exception_mass(lower, upper, history.mass, -1)
        out.append(Dataset(s, tuple(planted_claims(dgp.generate(s), lex)), facts, exception))
    return out


def strength_claim(feature: str, classes: tuple[str, ...]) -> Claim:
    if classes == ("negligible",):
        return Claim("negligible", (feature,))
    return Claim("strength", (feature,), classes[0] if len(classes) == 1 else classes)


@dataclass
class Evaluation:
    """One lexicon on the discovery seed: the noise verdicts, the oracle's verdicts on the labelled claims (labels
    are T's verdicts under this lexicon), and the guard rail's inputs."""

    lex: p.Lexicon
    noise: pd.DataFrame
    oracle: pd.DataFrame
    label_changes: int  # T's verdicts that differ from the frozen labels
    history_exception: float  # largest on seed 1

    @cached_property
    def criteria(self) -> dict[str, bool]:
        effect, at_most = (self.noise[self.noise.test == t] for t in ("effect", "at most"))
        large = self.oracle[self.oracle.n == LARGE]
        return {
            "1 noise never an effect": not (effect.verdict == TRUE).any(),
            "2 noise never refuted as negligible": not (at_most.verdict == FALSE).any(),
            "3 oracle no confident error at n = 50,000": not large.outcome.isin(ERRORS).any(),
            "guard rail": self.label_changes == 0 and self.lex.exception_mass > self.history_exception,
        }

    @property
    def passed(self) -> bool:
        return all(self.criteria.values())

    @cached_property
    def implicated(self) -> tuple[str, ...]:
        """The thresholds in GRID that the failures implicate (decision rule)."""
        noise = self.noise
        failing = noise[((noise.test == "effect") & (noise.verdict == TRUE)) | ((noise.test == "at most") & (noise.verdict == FALSE))]
        errors = self.oracle[(self.oracle.n == LARGE) & self.oracle.outcome.isin(ERRORS)]
        mostly = errors[errors.claim.str.contains("mostly_") & (errors["exception mass"] > self.lex.exception_mass)]
        return tuple(name for name, hit in (("detectable_mass", failing["band only"].any()), ("exception_mass", len(mostly) > 0)) if hit)


def evaluate(lex: p.Lexicon, datasets: list[Dataset]) -> Evaluation:
    noise, oracle, changes = [], [], 0
    for d in datasets:
        labels = {"scenario": d.scenario.id, "n": d.scenario.n, "interaction": d.scenario.interaction}
        for kind in NULL_MODELS:
            facts = d.facts[kind]
            for feature in NOISE:
                detectable, detection = p.feature_detection(facts.feature(feature), lex)
                net = detection["net change band"]
                band_only = detection["mass where the curve band excludes 0"] > lex.detectable_mass and net[0] <= 0 <= net[1]
                curve = labels | {"model": kind, "feature": feature, "detectable": detectable, "band only": band_only}
                tests = [("effect", strength_claim(feature, c)) for c in EFFECT]
                tests += [("at most", strength_claim(feature, c)) for c in AT_MOST]
                tests += [("direction (reported)", Claim("direction", (feature,), w)) for w in ("increasing", "decreasing")]
                for test, claim in tests:
                    noise.append(curve | {"test": test, "claim": str(claim), "verdict": verify(claim, facts, lex).value})
        for claim, frozen in d.claims:
            label = verify(claim, d.facts["T"], lex).value
            changes += label != frozen
            if label == UNDECIDABLE:  # no label under this lexicon; counted as a change
                continue
            verdict = verify(claim, d.facts["oracle"], lex)
            oracle.append(labels | {
                "claim": str(claim), "kind": claim.kind, "set": isinstance(claim.value, tuple), "frozen label": frozen,
                "label": label, "verdict": verdict.value, "outcome": metrics.outcome(label, verdict.value),
                "exception mass": verdict.evidence.get("exception mass", np.nan),
            })  # fmt: skip
    return Evaluation(lex, pd.DataFrame(noise), pd.DataFrame(oracle), changes, max(d.history_exception for d in datasets))


def decide(base: p.Lexicon, evaluate: Callable[[p.Lexicon], Evaluation]) -> tuple[p.Lexicon, list[Evaluation]]:
    """The decision rule: v1's thresholds, and every lexicon tried, v0 first."""
    for name, grid in GRID.items():
        assert all(v > getattr(base, name) for v in grid), f"{name} may only move up"
    tried = [evaluate(base)]
    if tried[0].passed or not tried[0].implicated:
        return base, tried
    names = tried[0].implicated
    steps = sorted(itertools.product(*(range(len(GRID[n]) + 1) for n in names)), key=sum)[1:]  # fewest steps first
    for step in steps:
        lex = replace(base, **{n: GRID[n][i - 1] for n, i in zip(names, step) if i})
        tried.append(evaluate(lex))
        if tried[-1].passed:
            return lex, tried
    return base, tried


def scaled(lex: p.Lexicon, name: str, factor: float) -> p.Lexicon:
    """lex with one threshold of SWEEP multiplied by factor."""
    if name in STRENGTHS:
        strength = dict(lex.strength) | {name: lex.strength[name] * factor}
        edges = [strength[s] for s in STRENGTHS]
        assert edges == sorted(edges) and len(set(edges)) == len(edges), f"{name} x {factor} reorders the classes"
        return replace(lex, strength=strength)
    return replace(lex, **{name: getattr(lex, name) * factor})


def thresholds(lex: p.Lexicon) -> dict[str, float]:
    return {name: (lex.strength[name] if name in STRENGTHS else getattr(lex, name)) for name in SWEEP}


def summary_row(e: Evaluation) -> dict:
    row = {f"criterion {k}": v for k, v in e.criteria.items()} | {"passed": e.passed, "T labels changed": e.label_changes}
    for n, group in e.oracle.groupby("n"):
        s = metrics.summary(group.label.tolist(), group.verdict.tolist())
        row |= {
            f"oracle n={n} claims": s["claims"], f"oracle n={n} decided rate": s["decided rate"],
            f"oracle n={n} accuracy among decided": s["accuracy among decided"],
            f"oracle n={n} released wrong": s["released_wrong"], f"oracle n={n} blocked correct": s["blocked_correct"],
            f"oracle n={n} certified among true": s["certified among true claims"],
        }  # fmt: skip
    noise = e.noise
    row["noise effect true"] = int(((noise.test == "effect") & (noise.verdict == TRUE)).sum())
    row["noise at most false"] = int(((noise.test == "at most") & (noise.verdict == FALSE)).sum())
    row["noise direction true"] = int(((noise.test == "direction (reported)") & (noise.verdict == TRUE)).sum())
    return row


def sensitivity(v1: p.Lexicon, datasets: list[Dataset], base: Evaluation) -> pd.DataFrame:
    rows = [{"threshold": "(v1)", "factor": 1.0, "value": np.nan} | summary_row(base)]
    for name in SWEEP:
        for factor in FACTORS:
            lex = scaled(v1, name, factor)
            rows.append({"threshold": name, "factor": factor, "value": thresholds(lex)[name]} | summary_row(evaluate(lex, datasets)))
    return pd.DataFrame(rows)


def main() -> None:
    base = p.load()
    datasets = load_discovery(base)
    v1, tried = decide(base, lambda lex: evaluate(lex, datasets))
    RESULTS.mkdir(parents=True, exist_ok=True)
    steps = pd.DataFrame([{n: getattr(e.lex, n) for n in GRID} | summary_row(e) for e in tried])
    steps.to_csv(RESULTS / "steps.csv", index=False)
    final = tried[-1] if tried[-1].lex == v1 else tried[0]
    final.noise.to_csv(RESULTS / "noise.csv", index=False)
    final.oracle.to_csv(RESULTS / "oracle.csv", index=False)
    table = sensitivity(v1, datasets, final)
    table.to_csv(RESULTS / "sensitivity.csv", index=False)

    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    print(f"Discovery seed: {len(datasets)} datasets; T's largest exception mass for history {final.history_exception:.4f}")
    for i, e in enumerate(tried):
        print(f"\nLexicon tried {i}: " + ", ".join(f"{n} = {getattr(e.lex, n)}" for n in GRID))
        for k, v in e.criteria.items():
            print(f"  {'pass' if v else 'FAIL'}  {k}")
        if not e.passed:
            print(f"  implicated: {e.implicated or 'none'}")
    moved = {n: getattr(v1, n) for n in GRID if getattr(v1, n) != getattr(base, n)}
    status = "passed" if final.passed else "FAILED: v1 keeps v0's values, the failure is reported (rule 4)"
    print(f"\nDecision: {status}; moved: {moved or 'nothing'}")

    noise = final.noise
    print("\nNoise curves under v1 (36 curves; verdict counts per test and model)")
    print(noise.groupby(["test", "model", "verdict"]).size().unstack(fill_value=0).to_string())
    print("\nThe oracle under v1, by claim type and n (D31)")
    print(metrics.summarize(final.oracle, ["n", "kind"])[["claims", "decided rate", "accuracy among decided", "released_wrong", "blocked_correct"]].round(3).to_string())
    print("\nThe oracle's confident errors under v1")
    errors = final.oracle[final.oracle.outcome.isin(ERRORS)]
    print(errors[["scenario", "claim", "label", "verdict"]].to_string(index=False) if len(errors) else "  none")
    none = final.oracle[(final.oracle.interaction == "none") & (final.oracle.kind == "interaction")]
    print("\nThe oracle's pattern verdicts on the pairs at level none")
    print(none.groupby(["n", "claim", "verdict"]).size().to_string())
    print("\nSensitivity (+-50%, one threshold at a time; labels recomputed on T)")
    columns = ["threshold", "factor", "value", "passed", "T labels changed", "noise effect true", "noise at most false",
               f"oracle n={min(dgp.SAMPLE_SIZES)} decided rate", f"oracle n={min(dgp.SAMPLE_SIZES)} released wrong",
               f"oracle n={min(dgp.SAMPLE_SIZES)} blocked correct", f"oracle n={LARGE} decided rate",
               f"oracle n={LARGE} released wrong", f"oracle n={LARGE} blocked correct"]  # fmt: skip
    print(table[columns].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
