"""The check behind D74 (asked for by D73): what the location snap changes. No API call, $0.

D73 fixed the plasmode rerun's change list and asked first whether the snap (lexicon/predicates._snap: a jump's
estimated location moves to M's nearest cut on a feature with observed values) changes a synthetic verdict. Each
part runs with D74's fixes off and on (VERIFIER_GATE_D74), "A", and with the two alternatives D74 rejected,
patched in for the run: "B", a snap only within one grid spacing of the cut; "C", a snap on every feature, also
those without observed values.

1. Band ends (band_ends.csv): every scenario of both tiers, every reference (oracle, EBM, XGB2, T) and every feature
   with observed values: threshold()'s location estimate and its refit band, and the gap _gap gives each end with
   and without the snap. A location verdict can change only where such a gap changes, since `at` and the window
   do not depend on the snap.
2. Verdicts on the synthetic tier: every planted claim of E1 (all seeds, on the oracle, EBM and XGB2, and T's
   labels; e1_changes.csv), the certified plan of every EBM and XGB2 (H2's statements and the template;
   plan_changes.csv), and every location claim in D66's 720 synthetic run traces (results/e3/v4-x5-m5, plans and
   readings; e3_changes.csv).

Run: `uv run python -m verifier_gate.experiments.snap_check`. Writes results/snap_check/: band_ends.csv,
e1_changes.csv, plan_changes.csv, e3_changes.csv and summary.csv.
"""

import json
import os
import re
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd

from verifier_gate.data import dgp, tiers
from verifier_gate.experiments import e1_lexicon
from verifier_gate.experiments.build_facts import load
from verifier_gate.lexicon import predicates as p
from verifier_gate.verifier.certified import certified_plan
from verifier_gate.verifier.verify import verify

RESULTS = Path(__file__).parents[3] / "results"
OUT = RESULTS / "snap_check"
D66_RUNS = RESULTS / "e3" / "v4-x5-m5" / "haiku" / "runs"
KINDS = ("oracle", "EBM", "XGB2", "T")
VARIANTS = ("A", "B", "C")  # A: D74's snap; B: within one grid spacing; C: on every feature
LOCATION = re.compile(r"(?:threshold|drop)\(")
SNAP = p._snap


def spacing(f, lex: p.Lexicon) -> float:
    """The jump grid's spacing on a feature, as threshold() lays the grid."""
    w, search, x_steps = p._window(f, lex), p._search(f, lex), p._step_x(f)
    lo_x, hi_x = x_steps[search[0]], x_steps[search[-1]]
    x = np.linspace(lo_x + w / 2, max(hi_x - w / 2, lo_x + w / 2), p.JUMP_GRID)
    return float(x[1] - x[0])


def nearest(f, y: float) -> float:
    return float(f.cuts[np.argmin(np.abs(f.cuts - y))])


def snap_within_spacing(lex: p.Lexicon):
    def snap(f, band):
        if f.values is None or len(f.values) < 2 or len(f.cuts) == 0:
            return band
        tol = spacing(f, lex)
        low, high = (nearest(f, y) if abs(nearest(f, y) - y) <= tol else y for y in band)
        return low, high
    return snap


def snap_everywhere(f, band):
    if len(f.cuts) == 0:
        return band
    low, high = (nearest(f, y) for y in band)
    return low, high


@contextmanager
def under(variant: str | None, lex: p.Lexicon):
    """D74's fixes off (None) or a variant of the snap on, for the block."""
    before = os.environ.get(p.D74)
    os.environ[p.D74] = "0" if variant is None else "1"
    p._snap = {"B": snap_within_spacing(lex), "C": snap_everywhere}.get(variant, SNAP)
    try:
        yield
    finally:
        p._snap = SNAP
        if before is None:
            os.environ.pop(p.D74, None)
        else:
            os.environ[p.D74] = before


def facts_of(scenario, kind: str):
    try:
        return load(scenario, kind)
    except Exception:  # T has no refits
        return load(scenario, kind, draws=False)


def band_ends(lex: p.Lexicon) -> pd.DataFrame:
    rows = []
    for s in tiers.SCENARIOS:
        for kind in KINDS:
            try:
                facts = facts_of(s, kind)
            except Exception:
                continue
            for f in facts.features:
                if f.values is None or len(f.values) < 2 or len(f.cuts) == 0:
                    continue
                with under(None, lex):
                    try:
                        evidence = p.threshold(facts, f.name, 0.0, lex).evidence
                    except IndexError:  # no step in the search region
                        continue
                low, high = evidence["location band"]
                snapped = {"A": SNAP(f, (low, high)), "B": snap_within_spacing(lex)(f, (low, high))}
                for i, (end, y) in enumerate((("band low", low), ("band high", high))):
                    gap = p._gap(f, y)
                    row = {"tier": tiers.name(s), "scenario": s.id, "kind": kind, "feature": f.name, "end": end,
                           "estimate": y, "nearest cut": nearest(f, y), "gap": gap}
                    for v, band in snapped.items():
                        row[f"gap {v}"] = p._gap(f, band[i])
                        row[f"changed {v}"] = row[f"gap {v}"] != gap
                    rows.append(row)
    return pd.DataFrame(rows)


def e1_changes(lex: p.Lexicon) -> pd.DataFrame:
    tables = {}
    for v in (None, *VARIANTS):
        with under(v, lex):
            tables[v] = e1_lexicon.verdicts(dgp.SCENARIOS, lex)
    base, cols = tables[None], [*e1_lexicon.REFERENCES, "label"]
    rows = []
    for v in VARIANTS:
        for c in cols:
            for i in np.flatnonzero((base[c].astype(str) != tables[v][c].astype(str)).to_numpy()):
                rows.append({"variant": v, "reference": c, "scenario": base.iloc[i]["scenario"], "claim": base.iloc[i]["claim"],
                             "before": base.iloc[i][c], "after": tables[v].iloc[i][c]})  # fmt: skip
    print(f"E1, synthetic: {len(base)} planted claims, verdicts of {', '.join(cols)}")
    return pd.DataFrame(rows, columns=["variant", "reference", "scenario", "claim", "before", "after"])


def plan_changes(lex: p.Lexicon) -> pd.DataFrame:
    rows = []
    for s in dgp.SCENARIOS:
        for kind in e1_lexicon.MODELS:
            facts = load(s, kind)
            plans = {}
            for v in (None, *VARIANTS):
                with under(v, lex):
                    plans[v] = {str(c) for c in certified_plan(facts, lex)}
            for v in VARIANTS:
                if plans[v] != plans[None]:
                    rows.append({"variant": v, "scenario": s.id, "kind": kind, "removed": sorted(plans[None] - plans[v]),
                                 "added": sorted(plans[v] - plans[None])})  # fmt: skip
    print(f"certified plans: {len(dgp.SCENARIOS) * len(e1_lexicon.MODELS)} synthetic models")
    return pd.DataFrame(rows, columns=["variant", "scenario", "kind", "removed", "added"])


def strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            yield from strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from strings(value)


def e3_changes(lex: p.Lexicon) -> pd.DataFrame:
    """Every location claim of D66's synthetic runs (plans and readings), verified with each variant."""
    facts, rows, seen, runs = {}, [], 0, 0
    for path in sorted(D66_RUNS.glob("syn-*.json")):
        run = json.loads(path.read_text())
        scenario, kind = run["run_id"].split("_")[:2]
        if (scenario, kind) not in facts:
            facts[(scenario, kind)] = load(tiers.scenario(scenario), kind)
        runs += 1
        for line in sorted({s.strip() for s in strings(run) if LOCATION.search(s) and len(s) < 300}):
            verdicts = {}
            try:
                for v in (None, *VARIANTS):
                    with under(v, lex):
                        verdicts[v] = verify(line, facts[(scenario, kind)], lex).value
            except Exception:  # not a DSL line (a sentence, a reason)
                continue
            seen += 1
            for v in VARIANTS:
                if verdicts[v] != verdicts[None]:
                    rows.append({"variant": v, "run": run["run_id"], "claim": line, "before": verdicts[None], "after": verdicts[v]})
    print(f"E3 as run (D66): {runs} synthetic runs, {seen} location claims (per run)")
    return pd.DataFrame(rows, columns=["variant", "run", "claim", "before", "after"])


def main() -> None:
    lex = p.load()
    assert lex.version == "v3", "the snap is a v3 fix (D74); run without VERIFIER_GATE_LEXICON=v2"
    OUT.mkdir(parents=True, exist_ok=True)
    ends = band_ends(lex)
    ends.to_csv(OUT / "band_ends.csv", index=False)
    parts = {"e1": e1_changes(lex), "plans": plan_changes(lex), "e3": e3_changes(lex)}
    for name, table in parts.items():
        table.to_csv(OUT / f"{'plan' if name == 'plans' else name}_changes.csv", index=False)
    summary = [{"part": "band ends", "tier": t, "variant": v, "changed": int(ends.loc[ends.tier == t, f"changed {v}"].sum())}
               for t in sorted(ends.tier.unique()) for v in ("A", "B")]  # fmt: skip
    summary += [{"part": name, "tier": "synthetic", "variant": v, "changed": int((table.variant == v).sum())}
                for name, table in parts.items() for v in VARIANTS]  # fmt: skip
    summary = pd.DataFrame(summary)
    summary.to_csv(OUT / "summary.csv", index=False)
    print(summary.to_string(index=False))
    for name, table in (("plans", parts["plans"]), ("e3", parts["e3"])):
        for _, r in table[table.variant == "A"].iterrows():
            print(f"  {name}, A: {r.to_dict()}")


if __name__ == "__main__":
    main()
