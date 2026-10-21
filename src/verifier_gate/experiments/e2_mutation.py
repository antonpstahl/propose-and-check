"""E2 at plan level: mutation test of the verifier and the coverage check (plan §6 E2; D32). No LLM.

Correct plans (source a): verifier/certified.py, the most specific certified statement per term and claim type
for each fitted model. Each operator mutates one claim of a plan; M8's omission drops every claim about a
pair with a share of at least 10%.

| op  | mutation                                                                                          |
|-----|---------------------------------------------------------------------------------------------------|
| M1  | flip the direction: increasing <-> decreasing, also the "mostly" word and the "generally" set      |
| M2  | swap ranks: k -> k +- 1 (adjacent), k +- 2 (non-adjacent); a rank set shifted; a comparison reversed |
| M3  | upgrade strength: every higher class; a strength set shifted up one class (D33)                    |
| M4  | downgrade strength: every lower class; a strength set shifted down one class                       |
| M5  | share x 0.8, 1.2, 0.5, 1.5, and M's share +- 1.5 times the tolerance (D32)                         |
| M6  | location +- 0.5 w (control), +- 2 w, +- 5 w (D32); on a count (D42): the same step named at its other  |
|     | point (control), +- 2 and 5 steps                                                                 |
| M7  | invent an interaction: amplification or sign flip for a pair the plan calls none, or one not in M |
| M8  | swap the pattern (amplification <-> sign flip), deny it (none), or omit a pair with share >= 10%   |
| M9  | the same claim about a term the model does not have                                               |
| M10 | "mostly increases" <-> "increases" (D29; reported by n)                                            |
| M11 | hedge a settled claim: unsettled(<claim>) (D30)                                                    |

Labels. A mutant is caught if it is not released: its verdict on M is false or undecidable, reported apart
(D32); an omission is caught if the coverage check finds the pair missing. Whether a mutant is an error at all
is judged against M itself, without bands: the lexicon applied to M's point estimate, as it is applied to T.
A mutant true there is equivalent (still true of M): excluded from recall and counted. The controls (M5 values
within the tolerance of M's share, M6 at 0.5 w) must not be refuted. In D31's vocabulary a missed error is a
wrong statement released and a refuted control a correct statement blocked. M9 and M11 are errors by
definition. M10 is not labelled: on a point curve without bands every wiggle is an exception, which is not
the "mostly" the lexicon defines (D29), so M10 reports its verdicts by n.

Plan-level recall checks that the verifier implements the lexicon. It is close to 100% by construction, since
the plans and the verdicts come from the same verifier, and it is not the headline (§6 E2). What it measures:
how mutants are caught (false or undecidable), the false-alarm rate on the controls, and the equivalent
mutants each operator produces.

Run: `uv run python -m verifier_gate.experiments.e2_mutation` (the discovery seed, about a minute;
`--seeds 1,2,3` for all). Writes results/e2/plan_<discovery|...>/: mutants.csv, plans.csv, summary tables.
"""

import argparse
import itertools
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from verifier_gate.data import dgp, tiers
from verifier_gate.dsl.grammar import HEDGE, Claim
from verifier_gate.experiments.build_facts import load
from verifier_gate.facts.build import build_facts
from verifier_gate.facts.schema import Facts
from verifier_gate.gate.roundtrip import PAIR_SHARE, claim_terms, coverage
from verifier_gate.lexicon import predicates as p
from verifier_gate.lexicon.predicates import CLASSES, FALSE, TRUE, UNDECIDABLE
from verifier_gate.verifier.certified import certified_plan
from verifier_gate.verifier.verify import verify

MODELS = ("EBM", "XGB2")
OPERATORS = ("M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9", "M10", "M11")
UNKNOWN = "savings_balance"  # M9: a credit feature none of the models has
SHARE_FACTORS = (0.8, 1.2, 0.5, 1.5)
TOLERANCE_SHIFT = 1.5
LOCATION_SHIFTS = (0.5, 2.0, 5.0)  # in units of w; 0.5 w is the control
INVENTED_FROM_TOP = 4  # M7: pairs of the top features by share that the model does not have
OPPOSITE = {"increasing": "decreasing", "decreasing": "increasing"}
BY_DEFINITION = ("M9", "M11")
UNLABELLED = ("M10",)
RESULTS = Path(__file__).parents[3] / "results" / "e2"


@dataclass(frozen=True)
class Mutant:
    operator: str
    variant: str
    original: Claim | None
    claim: Claim | None  # None: an omission
    control: bool = False  # declared control (M6 at 0.5 w); M5's controls follow from the label
    omitted: frozenset | None = None  # M8's omission: the pair dropped
    share_level: str = ""  # M5 only


def _strength_index(claim: Claim) -> int:
    return 0 if claim.kind == "negligible" else CLASSES.index(claim.value)


def _strength_claim(feature: str, i: int) -> Claim:
    return Claim("negligible", (feature,)) if i == 0 else Claim("strength", (feature,), CLASSES[i])


def _opposite(word: str) -> str:
    strict = word.removeprefix("mostly_")
    return f"mostly_{OPPOSITE[strict]}" if word.startswith("mostly_") else OPPOSITE[strict]


def share_level(share: float) -> str:
    return "below 4%" if share < 0.04 else "4-10%" if share < 0.10 else "10% and above"


def tolerance(share: float, lex: p.Lexicon) -> float:
    return max(lex.share_absolute, lex.share_relative * share)


def mutants(plan: list[Claim], facts: Facts, lex: p.Lexicon) -> list[Mutant]:
    out: list[Mutant] = []
    features = [f.name for f in facts.features]
    add = out.append
    for c in plan:
        if c.kind == HEDGE:
            continue
        f = c.terms[0]
        if c.kind == "direction":
            if isinstance(c.value, tuple):
                add(Mutant("M1", "set", c, Claim("direction", c.terms, tuple(_opposite(w) for w in c.value))))
            else:
                add(Mutant("M1", "single", c, Claim("direction", c.terms, _opposite(c.value))))
                strict = c.value.removeprefix("mostly_")
                other = strict if c.value.startswith("mostly_") else f"mostly_{strict}"
                add(Mutant("M10", "mostly to strict" if c.value.startswith("mostly_") else "strict to mostly", c, Claim("direction", c.terms, other)))
        if c.kind == "rank":
            if isinstance(c.value, tuple):
                for d in (-1, 1):
                    shifted = tuple(k + d for k in c.value)
                    if shifted[0] >= 1 and shifted[-1] <= len(features):
                        add(Mutant("M2", "set shifted", c, Claim("rank", c.terms, shifted)))
            else:
                for d in (-2, -1, 1, 2):
                    if 1 <= c.value + d <= len(features):
                        add(Mutant("M2", "adjacent" if abs(d) == 1 else "non-adjacent", c, Claim("rank", c.terms, c.value + d)))
        if c.kind == "comparison":
            add(Mutant("M2", "comparison reversed", c, Claim("comparison", (c.terms[1], c.terms[0]), relation=c.relation)))
        if c.kind == "negligible" or (c.kind == "strength" and not isinstance(c.value, tuple)):
            i = _strength_index(c)
            for j in range(len(CLASSES)):
                if j != i:
                    add(Mutant("M3" if j > i else "M4", f"{j - i:+d} class", c, _strength_claim(f, j)))
        if c.kind == "strength" and isinstance(c.value, tuple):
            lo, hi = CLASSES.index(c.value[0]), CLASSES.index(c.value[-1])
            if hi + 1 < len(CLASSES):
                add(Mutant("M3", "set +1 class", c, Claim("strength", c.terms, CLASSES[lo + 1 : hi + 2])))
            if lo > 0:
                add(Mutant("M4", "set -1 class", c, Claim("strength", c.terms, CLASSES[lo - 1 : hi])))
        if c.kind == "share":
            share = facts.feature(f).share.value
            level = share_level(share)
            for k in SHARE_FACTORS:
                add(Mutant("M5", f"x{k}", c, Claim("share", c.terms, round(c.value * k, 3)), share_level=level))
            for sign in (-1, 1):
                value = share + sign * TOLERANCE_SHIFT * tolerance(share, lex)
                if value > 0:
                    add(Mutant("M5", f"{sign * TOLERANCE_SHIFT:+} tolerance", c, Claim("share", c.terms, round(value, 3)), share_level=level))
        if c.kind in ("threshold", "peak"):
            feature = facts.feature(f)
            values = feature.values
            if values is not None and len(values) > 1:  # D42: on a count, half a step names another step
                unit = float(np.median(np.diff(values)))
                if c.kind == "threshold":  # control: the same step named at its other point (0.5 <-> 1 for a count)
                    lo, hi = p._gap(feature, c.value)
                    other = hi if c.value < hi else (lo + hi) / 2
                    add(Mutant("M6", "same step, other point", c, Claim(c.kind, c.terms, round(other, 4)), control=True))
                for k, sign in itertools.product(LOCATION_SHIFTS[1:], (-1, 1)):
                    add(Mutant("M6", f"{sign * k:+} steps", c, Claim(c.kind, c.terms, round(c.value + sign * k * unit, 4))))
            else:
                low, high = feature.low_high
                w = lex.window * (high - low)
                for k, sign in itertools.product(LOCATION_SHIFTS, (-1, 1)):
                    add(Mutant("M6", f"{sign * k:+} w", c, Claim(c.kind, c.terms, round(c.value + sign * k * w, 4)), control=k < 1))
        if c.kind == "interaction" and c.value != "none":
            other = "sign_flip" if c.value == "amplification" else "amplification"
            add(Mutant("M8", "swap", c, Claim("interaction", c.terms, other)))
            add(Mutant("M8", "deny", c, Claim("interaction", c.terms, "none")))
        if c.kind in ("strength", "negligible", "direction", "rank", "share", "threshold", "peak"):
            add(Mutant("M9", c.kind, c, Claim(c.kind, (UNKNOWN,), c.value)))
        add(Mutant("M11", c.kind, c, Claim(HEDGE, c.terms, inner=c)))
    # M7: invent an interaction where the plan says none, or between top features the model does not pair
    nones = [c for c in plan if c.kind == "interaction" and c.value == "none"]
    top = sorted(features, key=lambda n: -facts.feature(n).share.value)[:INVENTED_FROM_TOP]
    absent = [(a, b) for a, b in itertools.combinations(top, 2) if facts.pair(a, b) is None]
    for terms, variant in [(c.terms, "none in the plan") for c in nones] + [(t, "not in the model") for t in absent]:
        for pattern in ("amplification", "sign_flip"):
            add(Mutant("M7", variant, None, Claim("interaction", terms, pattern)))
    # M8: omit every claim about a pair with share >= 10%
    for q in facts.pairs:
        if q.share.value >= PAIR_SHARE and any(frozenset(q.features) in claim_terms(c) for c in plan):
            add(Mutant("M8", "omit", None, None, omitted=frozenset(q.features)))
    return out


def point_facts(facts: Facts, X: pd.DataFrame) -> Facts:
    """M without bands: its own terms read like T's, for labelling mutants against M itself."""
    return build_facts(facts.steps(), X)


def label(m: Mutant, point: Facts, lex: p.Lexicon) -> str:
    """The mutant's role: error (must be caught), control (must not be refuted), equivalent, or unlabelled."""
    if m.claim is None or m.operator in BY_DEFINITION:
        return "error"
    if m.operator in UNLABELLED:
        return "unlabelled"
    truth = verify(m.claim, point, lex).value
    if m.control or (m.operator == "M5" and truth == TRUE):
        return "control"
    return {TRUE: "equivalent", FALSE: "error", UNDECIDABLE: "unlabelled"}[truth]


def outcome(role: str, verdict: str) -> str:
    """D31's vocabulary: for errors caught (refuted or undecidable) or released wrong; for controls certified,
    abstained or blocked (a false alarm)."""
    if role == "error":
        return {FALSE: "caught: refuted", UNDECIDABLE: "caught: undecidable", TRUE: "released wrong"}[verdict]
    if role == "control":
        return {TRUE: "control certified", UNDECIDABLE: "control abstained", FALSE: "control blocked"}[verdict]
    return f"{role}: {verdict}"


def run(scenarios, lex: p.Lexicon) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, plans = [], []
    for s in scenarios:
        X = tiers.generate(s).X
        for kind in MODELS:
            facts = load(s, kind)
            point = point_facts(facts, X)
            plan = certified_plan(facts, lex)
            base = {"scenario": s.id, "n": s.n, "interaction": s.interaction, "model": kind}
            full = coverage(plan, facts, plan)
            plans.append(base | {"claims": len(plan), "hedges": sum(c.kind == HEDGE for c in plan),
                                 "sets": sum(isinstance(c.value, tuple) for c in plan),
                                 "coverage passed": full.passed, "limited-evidence flag": full.flagged})  # fmt: skip
            for m in mutants(plan, facts, lex):
                role = label(m, point, lex)
                if m.claim is None:  # omission: the coverage check must find the pair missing
                    kept = [c for c in plan if m.omitted not in claim_terms(c)]
                    verdict = FALSE if m.omitted in coverage(kept, facts, plan).missing else TRUE
                    claim = f"omit {' & '.join(sorted(m.omitted))}"
                else:
                    verdict, claim = verify(m.claim, facts, lex).value, str(m.claim)
                rows.append(base | {
                    "operator": m.operator, "variant": m.variant, "original": str(m.original) if m.original else "",
                    "mutant": claim, "share level": m.share_level, "role": role, "verdict": verdict,
                    "outcome": outcome(role, verdict),
                })  # fmt: skip
    return pd.DataFrame(rows), pd.DataFrame(plans)


def recall(table: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Per group: errors, caught (refuted / undecidable), released wrong, recall; controls and their false
    alarms; equivalent mutants."""
    rows = []
    for key, g in table.groupby(by, sort=False):
        key = key if isinstance(key, tuple) else (key,)
        errors, controls = g[g.role == "error"], g[g.role == "control"]
        caught = errors.verdict != TRUE
        rows.append(dict(zip(by, key)) | {
            "mutants": len(g), "errors": len(errors), "caught: refuted": int((errors.verdict == FALSE).sum()),
            "caught: undecidable": int((errors.verdict == UNDECIDABLE).sum()), "released wrong": int((~caught).sum()),
            "recall": caught.mean() if len(errors) else float("nan"), "controls": len(controls),
            "controls blocked": int((controls.verdict == FALSE).sum()),
            "controls certified": int((controls.verdict == TRUE).sum()),
            "equivalent": int((g.role == "equivalent").sum()), "unlabelled": int((g.role == "unlabelled").sum()),
        })  # fmt: skip
    return pd.DataFrame(rows).set_index(by)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", default=None, help="comma-separated, e.g. 1,2,3 (default: the discovery seed; plasmode: all)")
    parser.add_argument("--tier", default="synthetic", choices=tuple(tiers.TIERS), help="plasmode: the out-of-sample tier (plan §4.4)")
    args = parser.parse_args()
    tier = tiers.module(args.tier)
    every = tuple(sorted({s.seed for s in tier.SCENARIOS}))
    seeds = tuple(int(s) for s in args.seeds.split(",")) if args.seeds else every if tier is not dgp else (dgp.DISCOVERY_SEED,)
    if tier is dgp:
        name = "plan_discovery" if seeds == (dgp.DISCOVERY_SEED,) else "plan_seeds-" + "-".join(map(str, seeds))
    else:
        name = f"plan_{args.tier}" if seeds == every else f"plan_{args.tier}_seeds-" + "-".join(map(str, seeds))
    scenarios = tuple(s for s in tier.SCENARIOS if s.seed in seeds)
    lex = p.load()
    assert lex.version != "v0", "E2 runs on the frozen lexicon (tag e1-frozen)"

    table, plans = run(scenarios, lex)
    out = RESULTS / (lex.version + ("-d74" if p.d74_fixes(lex) else "")) / name  # D74's fixes: a folder of their own
    out.mkdir(parents=True, exist_ok=True)
    table.to_csv(out / "mutants.csv", index=False)
    plans.to_csv(out / "plans.csv", index=False)
    by_operator = recall(table, ["operator"]).reindex(OPERATORS)
    by_operator.to_csv(out / "by_operator.csv")
    detail = recall(table, ["operator", "variant", "model", "n"])
    detail.to_csv(out / "by_variant_model_n.csv")
    shares = recall(table[table.operator == "M5"], ["variant", "share level"])
    shares.to_csv(out / "m5_by_share_level.csv")
    m10 = table[table.operator == "M10"].groupby(["model", "n", "variant", "verdict"]).size().unstack(fill_value=0)
    m10.to_csv(out / "m10_by_n.csv")

    pd.set_option("display.width", 250)
    pd.set_option("display.max_rows", 300)
    pd.set_option("display.max_columns", 30)
    print(f"Plan-level E2 on seeds {seeds}: {len(plans)} plans ({len(scenarios)} datasets x {len(MODELS)} models), {len(table)} mutants, lexicon {lex.version}")
    print(f"Plans: {plans.claims.sum()} certified claims ({plans.sets.sum()} sets, {plans.hedges.sum()} hedges); "
          f"coverage passed {plans['coverage passed'].sum()} of {len(plans)}, limited-evidence flag {plans['limited-evidence flag'].sum()}")  # fmt: skip
    print("\nBy operator")
    print(by_operator.round(3).to_string())
    print("\nBy operator and variant")
    print(recall(table, ["operator", "variant"]).round(3).to_string())
    print("\nM5 by share level")
    print(shares.round(3).to_string())
    print("\nM10 verdicts by model and n (not labelled, D29)")
    print(m10.to_string())
    missed = table[table.outcome == "released wrong"]
    print(f"\nReleased wrong (missed errors): {len(missed)}")
    if len(missed):
        print(missed[["scenario", "model", "operator", "variant", "original", "mutant"]].to_string(index=False))
    blocked = table[table.outcome == "control blocked"]
    print(f"\nControls blocked (false alarms): {len(blocked)}")
    if len(blocked):
        print(blocked[["scenario", "model", "operator", "variant", "original", "mutant"]].to_string(index=False))


if __name__ == "__main__":
    main()
