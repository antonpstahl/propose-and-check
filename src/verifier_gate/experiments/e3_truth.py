"""E3's claims against T without hedges (plan §12 item 42, §14.22). No API call, $0.

E3 verified every claim a text states against T, hedges included (experiments/e3_end_to_end.score). T has no
bands, so it settles nearly every claim and refutes its hedge; but a hedge is a statement about the evidence in one
sample, not about T, and the planted labels give it none (data/planted.py). This script rebuilds E3's scoring
readings of both arms of every run from the cache (extractor x3, replicas 3 to 5 at the run's draw, one retry of an
answer that is not a reading, as in E3), checks that they reproduce E3's rows (per text: scored or not, claims,
claims false against M and against T, hedges), and scores against T without hedges: the share of claims other
than hedges that are false against T, and P_U against T (a text with such a claim). P_U and E_U against M are not
affected.

Run: `uv run python -m verifier_gate.experiments.e3_truth`. Writes results/e3/v3-x3/truth_without_hedges.csv
(per writer, naming and pilot datasets apart, as E3's summary) and truth_rows.csv (per run and arm).
"""

import json
import tempfile
from collections import Counter
from pathlib import Path

import pandas as pd

from verifier_gate.data import dgp
from verifier_gate.experiments import e2_text
from verifier_gate.experiments.build_facts import load
from verifier_gate.experiments.e2_false_alarms import readings, requests_for, x3_system
from verifier_gate.experiments.e3_end_to_end import RESULTS, texts_of
from verifier_gate.experiments.pilot import NAMINGS
from verifier_gate.gate import gate as g
from verifier_gate.gate import roundtrip as rt
from verifier_gate.lexicon.predicates import FALSE
from verifier_gate.llm.client import Client
from verifier_gate.verifier.certified import certified_plan
from verifier_gate.verifier.verify import verify

SOURCE = RESULTS / e2_text.E3_SOURCE
WRITERS = ("haiku", "sonnet")
CHECKED = ("claims", "false M", "false T", "hedges")


def score_text(sentences: list, ctx: g.Context, truth, run_id: str, system: str, client: Client) -> dict:
    text = {"run": run_id, "sentences": sentences}
    rs = requests_for(text, ctx, system)
    answers = {r.key: a for r in rs if (a := client.lookup(r)) is not None}
    good, bad = readings(text, ctx, rs, answers)
    again = [r.__class__(**{**r.__dict__, "attempt": 1}) for r in bad]
    answers |= {r.key: a for r in again if (a := client.lookup(r)) is not None}
    good += readings(text, ctx, again, answers)[0]
    if len(good) < rt.EXTRACTED:
        return {"scored": False}
    trip = rt.compare(good, [], [i for i, _ in sentences], ctx.facts, ctx.certified)
    lines = [(line, value) for _, line, value, *_ in trip.unplanned]
    hedge = [line.startswith("unsettled(") for line, _ in lines]
    on_t = [verify(line, truth).value for line, _ in lines]
    return {
        "scored": True, "claims": len(lines), "false M": sum(v == FALSE for _, v in lines), "hedges": sum(hedge),
        "false T": sum(v == FALSE for v in on_t),
        "false T, no hedges": sum(v == FALSE and not h for v, h in zip(on_t, hedge)),
        "hedges false T": sum(v == FALSE and h for v, h in zip(on_t, hedge)),
    }  # fmt: skip


def rescore(client: Client) -> pd.DataFrame:
    system, ctxs, truths, out = x3_system(), {}, {}, []
    for writer in WRITERS:
        rows = pd.read_csv(SOURCE / writer / "rows.csv").set_index("run")
        for path in sorted((SOURCE / writer / "runs").glob("*.json")):
            run = g.Run(**json.loads(path.read_text()))
            scenario, model, _, _, _, naming = run.run_id.split("_")
            key = (scenario, model, naming)
            if key not in ctxs:
                s = next(x for x in dgp.SCENARIOS if x.id == scenario)
                f = load(s, model)
                ctxs[key] = g.Context(f, certified_plan(f), NAMINGS[naming])
                truths.setdefault(scenario, load(s, "T"))
            for arm, sentences in zip(("off", "on"), texts_of(run)):
                if not sentences:
                    continue
                found = score_text(sentences, ctxs[key], truths[scenario], run.run_id, system, client)
                e3 = rows.loc[run.run_id]
                if bool(found["scored"]) != bool(e3[f"{arm} scored"]) or (found["scored"] and any(found[k] != e3[f"{arm} {k}"] for k in CHECKED)):
                    raise ValueError(f"{run.run_id} ({arm}): the rebuilt readings do not reproduce E3's row")
                out.append({"writer": writer, "naming": naming, "pilot dataset": scenario in e2_text.PILOT, "run": run.run_id, "arm": arm, **found})
    return pd.DataFrame(out)


def summarise(table: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (writer, naming, pilot), part in table[table.scored == True].groupby(["writer", "naming", "pilot dataset"]):  # noqa: E712
        row = {"writer": writer, "naming": naming, "pilot datasets": pilot}
        for arm in ("off", "on"):
            a = part[part.arm == arm]
            non_hedge = int(a.claims.sum() - a.hedges.sum())
            row |= {
                f"texts {arm}": len(a),
                f"claims false vs T, {arm} (E3)": round(float(a["false T"].sum() / max(a.claims.sum(), 1)), 3),
                f"claims false vs T, {arm}, no hedges": round(float(a["false T, no hedges"].sum() / max(non_hedge, 1)), 3),
                f"P_U {arm} vs T (E3)": round(float((a["false T"] > 0).mean()), 3),
                f"P_U {arm} vs T, no hedges": round(float((a["false T, no hedges"] > 0).mean()), 3),
                f"hedges {arm}": int(a.hedges.sum()), f"hedges refuted by T, {arm}": int(a["hedges false T"].sum()),
            }  # fmt: skip
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    log = Path(tempfile.mkdtemp(prefix="e3_truth_")) / "lookups.jsonl"  # cache lookups only: not the call log
    table = rescore(Client("batch", log_path=log))
    table.to_csv(SOURCE / "truth_rows.csv", index=False)
    summary = summarise(table)
    summary.to_csv(SOURCE / "truth_without_hedges.csv", index=False)
    print(f"{len(table)} texts rebuilt from the cache; every scored text reproduces E3's counts ({', '.join(CHECKED)})")
    print(Counter(zip(table.writer, table.arm, table.scored)))
    pd.set_option("display.width", 250)
    print(summary.T.to_string())


if __name__ == "__main__":
    main()
