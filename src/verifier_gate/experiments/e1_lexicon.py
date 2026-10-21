"""E1: lexicon verdicts vs the planted truth, with three references (plan §6 E1; D12, D31). No LLM.

Every labelled claim of data/planted.py (169 per dataset; the label set frozen with lexicon v1, tag e1-frozen)
is verified on the oracle O and on both fitted models M (EBM, XGB2). Labels come from T. Layers (D12):
- data: O vs T, what the sample supports
- model: M vs O, scored on the claims O decides (O's verdict as the label); every claim in the 3 x 3 table, where
  a model miss (D24) is the cell O true, M false
- end to end: M vs T. Each confident error is attributed to the data layer if O makes the same error, to the
  model layer otherwise (D14: a stably shrunk effect gives a confident verdict, faithful to M, wrong against T)
Also EBM vs XGB2 on the same claims (3 x 3): where two faithful explanations differ.

Metrics (D31, experiments/metrics.py) by layer, model and n, and within that by claim type, feature role,
interaction level and single value vs set. Confident-error rates come with a one-sided upper bound (claims
treated as independent, optimistic) and a bootstrap interval clustered by dataset (coarse with the 3 datasets
per n of one seed).

Run: `uv run python -m verifier_gate.experiments.e1_lexicon` (the discovery seed, about 30 s);
`--seeds 2,3` for the confirmation (week 7). Writes results/e1/<lexicon version>/<discovery|confirmation>/.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from verifier_gate.data import dgp, tiers
from verifier_gate.data.planted import planted_claims
from verifier_gate.dsl.grammar import Claim
from verifier_gate.experiments import metrics
from verifier_gate.experiments.build_facts import load
from verifier_gate.lexicon import predicates as p
from verifier_gate.lexicon.predicates import UNDECIDABLE
from verifier_gate.verifier.verify import verify

MODELS = ("EBM", "XGB2")
REFERENCES = ("oracle", *MODELS)
ERRORS = (metrics.RELEASED_WRONG, metrics.BLOCKED_CORRECT)
RESULTS = Path(__file__).parents[3] / "results" / "e1"
HEADLINE = ["claims", "decided rate", "accuracy among decided", "released_wrong", "blocked_correct",
            "confident-error rate", "confident-error upper bound", "certified among true claims", "kappa among decided"]  # fmt: skip


def role(claim: Claim, tier=dgp) -> str:
    """The feature role of the claim's term (the tier's FEATURE_ROLES); pairs and comparisons are their own."""
    if claim.kind == "interaction":
        return "pair"
    if claim.kind == "comparison":
        return "comparison"
    return tier.FEATURE_ROLES[claim.terms[0]]


def verdicts(scenarios, lex: p.Lexicon | None = None) -> pd.DataFrame:
    """One row per dataset and labelled claim: the label, and the verdict and reason code of each reference."""
    lex = lex or p.load()
    rows = []
    for s in scenarios:
        facts = {kind: load(s, kind) for kind in REFERENCES}
        for i, (claim, label) in enumerate(planted_claims(tiers.generate(s), lex)):
            row = {
                "scenario": s.id, "seed": s.seed, "n": s.n, "interaction": s.interaction, "claim id": i,
                "claim": str(claim), "kind": claim.kind, "set": isinstance(claim.value, tuple), "role": role(claim, tiers.module(s)),
                "label": label,
            }  # fmt: skip
            for kind in REFERENCES:
                v = verify(claim, facts[kind], lex)
                row |= {kind: v.value, f"{kind} code": v.code}
            rows.append(row)
    return pd.DataFrame(rows)


def layers(table: pd.DataFrame) -> pd.DataFrame:
    """The claims in long form, one row per layer and model, with that layer's label and verdict."""
    keep = ["scenario", "seed", "n", "interaction", "claim id", "claim", "kind", "set", "role"]
    parts = [table[keep].assign(layer="data", model="oracle", label=table.label, verdict=table.oracle)]
    decided = table[table.oracle != UNDECIDABLE]
    for m in MODELS:
        parts.append(decided[keep].assign(layer="model", model=m, label=decided.oracle, verdict=decided[m]))
        parts.append(table[keep].assign(layer="end to end", model=m, label=table.label, verdict=table[m]))
    return pd.concat(parts, ignore_index=True)


def confident_error_rate(claims: pd.DataFrame) -> float:
    return metrics.summary(claims.label.tolist(), claims.verdict.tolist())["confident-error rate"]


def headline(long: pd.DataFrame) -> pd.DataFrame:
    """D31's numbers by layer, model and n, with a confident-error interval clustered by dataset."""
    table = metrics.summarize(long, ["layer", "model", "n"])
    lows, highs = [], []
    for key in table.index:
        group = long[(long.layer == key[0]) & (long.model == key[1]) & (long.n == key[2])]
        lo, hi = metrics.clustered_interval(group, confident_error_rate)
        lows.append(lo)
        highs.append(hi)
    return table.assign(**{"confident-error clustered low": lows, "confident-error clustered high": highs})


def end_to_end_errors(table: pd.DataFrame) -> pd.DataFrame:
    """Every confident error of a model against T, attributed to the data layer if the oracle makes the same
    error, to the model layer otherwise."""
    rows = []
    for m in MODELS:
        for _, r in table.iterrows():
            outcome = metrics.outcome(r.label, r[m])
            if outcome in ERRORS:
                layer = "data" if r.oracle == r[m] else "model"
                rows.append({"model": m, "scenario": r.scenario, "n": r.n, "kind": r.kind, "role": r.role,
                             "claim": r.claim, "label": r.label, "verdict": r[m], "oracle": r.oracle,
                             "outcome": outcome, "layer": layer})  # fmt: skip
    return pd.DataFrame(rows, columns=["model", "scenario", "n", "kind", "role", "claim", "label", "verdict", "oracle", "outcome", "layer"])


def cross_tables(table: pd.DataFrame) -> pd.DataFrame:
    """The 3 x 3 tables in long form: oracle vs each model, and EBM vs XGB2, by n."""
    rows = []
    pairs = [("oracle", m) for m in MODELS] + [("EBM", "XGB2")]
    for (a, b), n in ((pair, n) for pair in pairs for n in sorted(table.n.unique())):
        part = table[table.n == n]
        cells = metrics.cross_table(part[a].tolist(), part[b].tolist())
        for ra in cells.index:
            for rb in cells.columns:
                rows.append({"reference": a, "model": b, "n": n, "reference verdict": ra, "model verdict": rb, "claims": int(cells.loc[ra, rb])})
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", default=None, help="comma-separated, e.g. 2,3 (default: the discovery seed; plasmode: all)")
    parser.add_argument("--tier", default="synthetic", choices=tuple(tiers.TIERS), help="plasmode: the out-of-sample tier (plan §4.4)")
    args = parser.parse_args()
    tier = tiers.module(args.tier)
    every = tuple(sorted({s.seed for s in tier.SCENARIOS}))
    seeds = tuple(int(s) for s in args.seeds.split(",")) if args.seeds else every if tier is not dgp else (dgp.DISCOVERY_SEED,)
    if tier is dgp:
        name = "discovery" if seeds == (dgp.DISCOVERY_SEED,) else "confirmation" if dgp.DISCOVERY_SEED not in seeds else "seeds-" + "-".join(map(str, seeds))
    else:
        name = args.tier if seeds == every else f"{args.tier}_seeds-" + "-".join(map(str, seeds))
    scenarios = tuple(s for s in tier.SCENARIOS if s.seed in seeds)
    lex = p.load()
    assert lex.version != "v0", "E1 runs on the frozen lexicon (tag e1-frozen)"

    table = verdicts(scenarios, lex)
    long = layers(table)
    out = RESULTS / (lex.version + ("-d74" if p.d74_fixes(lex) else "")) / name  # D74's fixes: a folder of their own
    out.mkdir(parents=True, exist_ok=True)
    table.to_csv(out / "verdicts.csv", index=False)
    head = headline(long)
    head.to_csv(out / "headline.csv")
    for by in ("kind", "role", "interaction", "set"):
        metrics.summarize(long, ["layer", "model", "n", by]).to_csv(out / f"by_{by}.csv")
    crosses = cross_tables(table)
    crosses.to_csv(out / "cross_tables.csv", index=False)
    errors = end_to_end_errors(table)
    errors.to_csv(out / "end_to_end_errors.csv", index=False)

    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    pd.set_option("display.max_rows", 200)
    print(f"E1 on seeds {seeds}: {len(scenarios)} datasets, {len(table)} labelled claims, lexicon {lex.version}")
    print("\nHeadline (D31): layer, model, n")
    cols = HEADLINE + ["confident-error clustered low", "confident-error clustered high"]
    print(head[cols].round(4).to_string())
    print("\nEnd to end and model layer by claim type (decided rate / confident errors)")
    kinds = metrics.summarize(long[long.layer != "data"], ["layer", "model", "n", "kind"])
    kinds["errors"] = kinds.released_wrong + kinds.blocked_correct
    print(kinds[["claims", "decided rate", "errors", "released_wrong", "blocked_correct"]].unstack("n").round(3).to_string())
    print("\nEnd to end by feature role")
    roles = metrics.summarize(long[long.layer == "end to end"], ["model", "n", "role"])
    roles["errors"] = roles.released_wrong + roles.blocked_correct
    print(roles[["claims", "decided rate", "errors", "certified among true claims"]].unstack("n").round(3).to_string())
    print("\nSingle values vs sets, end to end")
    sets = metrics.summarize(long[long.layer == "end to end"], ["model", "n", "set"])
    print(sets[["claims", "decided rate", "released_wrong", "blocked_correct", "certified among true claims"]].round(3).to_string())
    for (a, b), part in crosses.groupby(["reference", "model"], sort=False):
        print(f"\n3 x 3: {a} (rows) vs {b} (columns)")
        print(part.pivot_table(index=["n", "reference verdict"], columns="model verdict", values="claims").astype(int).to_string())
    print("\nConfident errors against T, by model, n and layer")
    if len(errors):
        print(errors.groupby(["model", "n", "layer", "outcome"]).size().unstack(fill_value=0).to_string())
        print("\nModel-layer errors (the oracle does not make them)")
        model = errors[errors.layer == "model"]
        print(model.groupby(["model", "n", "claim", "label", "verdict", "oracle"]).size().rename("datasets").to_string())
    else:
        print("  none")
    undecidable = {k: int((table[k] == UNDECIDABLE).sum()) for k in REFERENCES}
    codes = {k: table.loc[table[k] == UNDECIDABLE, f"{k} code"].value_counts().to_dict() for k in REFERENCES}
    print(f"\nUndecidable verdicts: {undecidable}; reason codes: {codes}")
    print(f"\nWritten to {out.relative_to(Path.cwd()) if out.is_relative_to(Path.cwd()) else out}")
    assert np.all(table.label.isin([p.TRUE, p.FALSE]))


if __name__ == "__main__":
    main()
