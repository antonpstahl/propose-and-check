"""E3's baselines (M4 of the 20 Oct review, D71): what the gate adds over its own template and over a plain prompt.

Two arms beside E3's gate off and gate on, on the same cells and scored the same way:
- template: the template text from the certified statements (gate/template.py), the text the gate falls back to;
  no LLM. An always-template policy states no claim false on M by construction, so its E_U is 1 as read: what it
  gives up shows in its claims, words and kinds of claims.
- plain: E3's writer (Claude Haiku 5.5, the same settings) with a plain prompt (llm/plain.py, prompts p1): the same
  facts (H1), the writer's role and its rules for the text, and nothing the gate adds: no lexicon words, DSL, plan,
  certified statements, verifier, round trip or repair. An answer that is not a text is retried once.
Cells: E3's Haiku design with the facts-only handover, 18 synthetic datasets x 2 models x 2 namings x 5 draws = 360,
each named by its E3 run id. Gate off and gate on are E3's H1 runs of the same cells (results/e3/v3-x3/haiku); its
H2 runs are kept in rows.csv and compared for reference.

Scoring: E3's (e3_end_to_end.score_texts): three scoring readings by extractor x3 (replicas 3 to 5, at the cell's
draw), a claim counts if two readings find it, each verified against M and T under lexicon v2 (E3_LEXICON); one
retry of an answer that is not a reading. Added for every arm: the claims by kind, and the claims false against T
other than hedges (as e3_truth); for gate off and on from e3_truth's claims.csv and truth_rows.csv. The template's
text is the same at every draw of a cell, and each draw reads it again. The pilot datasets are reported apart: the
plain prompt was tried on them before it was frozen (`--pilot`).

Its batch waves have their own folder (cache/llm/batches/e3_baselines/), so it runs beside another batch experiment.

texts.json is the record of what was scored, as E3's run traces are: once it exists, a rerun scores its texts (every
reading from the cache) and rebuilds none, so a later change to the template's wording or to the handover does not
change these arms.

Run: `uv run python -m verifier_gate.experiments.e3_baselines [--pilot | --estimate | --dry]` (live: minutes to an
hour, mostly waiting for batches; stopping is safe, the same command resumes). Writes
results/e3/v3-x3/baselines/<plain prompts>/: texts.json, rows.csv (one row per cell and arm: template, plain, and
E3's gate off and gate on), summary.csv (per arm and naming, pilot datasets apart) and compare.csv (outside the
pilot datasets, both namings: each arm, and gate on by exit state, with P_U and its 95% interval, E_U against gate
off and against the plain prompt, claims, words, claims by kind, coverage and cost per text).
"""

import argparse
import json
import tempfile
from collections import Counter
from dataclasses import replace
from pathlib import Path

import pandas as pd

from verifier_gate.dsl.parse import parse
from verifier_gate.experiments import e3_end_to_end as e3
from verifier_gate.experiments.e2_false_alarms import wilson
from verifier_gate.experiments.pilot import as_answer
from verifier_gate.gate import gate as g
from verifier_gate.gate import roundtrip as rt
from verifier_gate.gate import template as templates
from verifier_gate.lexicon import predicates as p
from verifier_gate.lexicon.predicates import FALSE
from verifier_gate.llm import batch, plain, prompts, settings
from verifier_gate.llm.client import Client, Request, Response, stub_message
from verifier_gate.llm.extract import faithful_reading
from verifier_gate.verifier.verify import verify

SOURCE = e3.RESULTS / "v3-x3"
E3_LEXICON = "v2"
ARMS = {"template": "template only", "plain": "plain prompt", "off": "gate off (first draft)", "on": "gate on (released)"}
KINDS = ("strength", "negligible", "rank", "share", "comparison", "direction", "threshold", "peak", "interaction", "unsettled")
KIND_GROUPS = {"strength": ("strength", "negligible"), "rank": ("rank",), "share": ("share",), "comparison": ("comparison",),
               "direction": ("direction",), "jump or peak": ("threshold", "peak"), "interaction": ("interaction",), "hedge": ("unsettled",)}  # fmt: skip
SCORED = ("claims", "sentences", "words", "false M", "undecidable M", "false T", "false T, no hedges", "hedges", "unchecked numbers",
          "no DSL form", "not covered", "emphasis", "ambiguous")  # fmt: skip


def plan(pilot: bool = False, dry: bool = False) -> list[e3.Spec]:
    """E3's Haiku runs with the facts-only handover (the pilot: draw 0 of the pilot datasets, plausible names)."""
    if pilot:
        return [s for s in e3.plan() if s.variant == "H1" and s.scenario in e3.PILOT and s.draw == 0 and s.naming == "plausible"]
    return [s for s in e3.plan(dry=dry) if s.variant == "H1"]


def template_text(ctx: g.Context) -> list[list]:
    draft = templates.template(ctx.facts, ctx.certified, ctx.label or templates.synthetic_label(ctx.names))
    return [[i, t] for i, t in draft.sentences]


def _text(answer: Response) -> list[list] | None:
    try:
        return plain.sentences_from(answer)
    except (ValueError, KeyError, TypeError):
        return None


def write_plain(specs: list[e3.Spec], handovers: dict[str, str], resolve) -> dict[str, dict]:
    """Per cell: the plain text as [id, text] sentences (None if neither answer was a text), its calls and their cost.
    `resolve` answers a list of requests by key."""
    first = {s.run_id: plain.plain_request(handovers[s.run_id], s.writer, s.draw) for s in specs}
    answers = resolve(list(first.values()))
    again = {rid: replace(r, attempt=1) for rid, r in first.items() if _text(answers[r.key]) is None}
    if again:
        print(f"plain writer: {len(again)} answer(s) not a text, retried once")
        answers |= resolve(list(again.values()))
    out = {}
    for rid, r in first.items():
        used = [answers[r.key]] + ([answers[again[rid].key]] if rid in again else [])
        out[rid] = {"sentences": _text(used[-1]), "calls": len(used), "cost": round(sum(a.cost for a in used), 6)}
    return out


# --- scoring ----------------------------------------------------------------------------------------------


def scorer(sentences: list, readings: list, ctx: g.Context, truth) -> dict:
    """E3's score of a text, with its claims by kind and its claims other than hedges false against T."""
    out = e3.score(sentences, readings, ctx, truth)
    if not out["scored"]:
        return out
    trip = rt.compare(readings, [], [i for i, _ in sentences], ctx.facts, ctx.certified, unknown_terms=ctx.unknown_terms)  # as e3.score
    lines = [line for _, line, *_ in trip.unplanned]
    kinds = Counter(parse(line).kind for line in lines)
    out["false T, no hedges"] = sum(verify(line, truth).value == FALSE for line in lines if not line.startswith("unsettled("))
    return out | {f"kind {k}": kinds.get(k, 0) for k in KINDS}


def cell(spec: e3.Spec) -> dict:
    scenario, model, variant, draw, _, naming = spec.run_id.split("_")
    return {"run": spec.run_id, "scenario": scenario, "model": model, "naming": naming, "draw": int(draw.removeprefix("d")),
            "handover": variant, "pilot dataset": scenario in e3.PILOT}  # fmt: skip


def gate_rows(runs: set[str]) -> list[dict]:
    """E3's gate off and gate on for the given Haiku runs, as rows of the same form: E3's scores, with the claims by
    kind (claims.csv) and the claims other than hedges false against T (truth_rows.csv) from e3_truth."""
    table = pd.read_csv(SOURCE / "haiku" / "rows.csv")
    truth = pd.read_csv(SOURCE / "truth_rows.csv")
    truth = truth[truth.writer == "haiku"].set_index(["run", "arm"])["false T, no hedges"]
    claims = pd.read_csv(SOURCE / "claims.csv")
    claims = claims[claims.writer == "haiku"]
    kinds = claims.assign(kind=claims.dsl.map(lambda line: parse(line).kind)).groupby(["run", "arm", "kind"]).size()
    rows = []
    for r in table[table.run.isin(runs)].to_dict("records"):
        spec = e3.Spec(r["scenario"], r["model"], r["handover"], int(r["draw"]), r["writer"], r["naming"])
        for arm in ("off", "on"):
            row = cell(spec) | {"arm": arm, "exit": r["exit"] if arm == "on" else "", "scored": bool(r[f"{arm} scored"] == True),  # noqa: E712
                                "cost": r["cost"] if arm == "on" else float("nan")}  # fmt: skip
            if row["scored"]:
                row |= {k: r[f"{arm} {k}"] for k in SCORED if k != "false T, no hedges"}
                row["false T, no hedges"] = int(truth.loc[(r["run"], arm)])
                row |= {f"kind {k}": int(kinds.get((r["run"], arm, k), 0)) for k in KINDS}
                if sum(row[f"kind {k}"] for k in KINDS) != row["claims"]:
                    raise ValueError(f"{r['run']} ({arm}): claims.csv does not hold E3's claims")
            rows.append(row)
    return rows


# --- the tables -------------------------------------------------------------------------------------------


def stats(part: pd.DataFrame) -> dict:
    """P_U with its 95% Wilson interval, volume, kinds, coverage and cost of a set of texts."""
    s = part[part.scored == True]  # noqa: E712
    n, k = len(s), int((s["false M"] > 0).sum())
    lo, hi = wilson(k, n) if n else (float("nan"), float("nan"))
    claims = s.claims.sum()
    return {
        "cells": len(part), "texts scored": n, "P_U": round(k / n, 4) if n else float("nan"), "P_U 95% low": round(lo, 4), "P_U 95% high": round(hi, 4),
        "P_U vs T, no hedges": round(float((s["false T, no hedges"] > 0).mean()), 4) if n else float("nan"),
        "claims false vs T, no hedges": round(float(s["false T, no hedges"].sum() / (claims - s.hedges.sum())), 4) if claims else float("nan"),
        "claims per text": round(float(s.claims.mean()), 2), "words per text": round(float(s.words.mean()), 1),
        "sentences per text": round(float(s.sentences.mean()), 2),
        **{f"{name} claims per text": round(float(sum(s[f"kind {k}"].sum() for k in kinds) / n), 2) if n else float("nan") for name, kinds in KIND_GROUPS.items()},
        "hedge share of claims": round(float(s.hedges.sum() / claims), 4) if claims else float("nan"),
        "undecidable claims per text": round(float(s["undecidable M"].mean()), 2),
        "texts covering every required term": round(float((s["not covered"] == 0).mean()), 4) if n else float("nan"),
        "unchecked numbers per text": round(float(s["unchecked numbers"].mean()), 2),
        "cost per text": round(float(part.cost.mean()), 6),
    }  # fmt: skip


def summarise(rows: pd.DataFrame) -> pd.DataFrame:
    """Per arm, handover and naming, the pilot datasets apart."""
    out = []
    for (arm, handover, naming, pilot), part in rows.groupby(["arm", "handover", "naming", "pilot dataset"]):
        out.append({"arm": ARMS[arm], "handover": handover, "naming": naming, "pilot datasets": pilot} | stats(part))
    return pd.DataFrame(out)


def compare(rows: pd.DataFrame) -> pd.DataFrame:
    """The arms on the same cells (H1, outside the pilot datasets, both namings), gate on also by exit state, and
    E3's gate off and on over all its runs (H1 and H2) for reference; E_U against gate off and the plain prompt."""
    main = rows[~rows["pilot dataset"]]
    h1 = main[main.handover == "H1"]
    parts = [(ARMS[arm], "H1 cells", h1[h1.arm == arm]) for arm in ARMS]
    parts += [(f"gate on, exit {e}", "H1 cells", h1[(h1.arm == "on") & (h1.exit == e)]) for e in (g.RELEASED, g.RELEASED_REDUCED, g.TEMPLATE)]
    parts += [(f"{ARMS[arm]}, H1 and H2 runs", "E3 runs", main[main.arm == arm]) for arm in ("off", "on")]
    out = pd.DataFrame([{"arm": name, "set": cells} | stats(part) for name, cells, part in parts if len(part)])
    base = out.set_index("arm").P_U
    at = out.columns.get_loc("P_U 95% high") + 1
    out.insert(at, "E_U vs gate off", (1 - out.P_U / base[ARMS["off"]]).round(3))
    out.insert(at + 1, "E_U vs plain prompt", (1 - out.P_U / base[ARMS["plain"]]).round(3))
    return out


# --- running ----------------------------------------------------------------------------------------------


def stub_responder(ctxs: dict[str, g.Context]):
    """No network: the plain writer answers with the cell's template text and, in the first cell, one wrong
    sentence; the extractor reads each sentence as exactly the claims behind it. The run id travels in the handover."""
    answers = [as_answer(templates.template(c.facts, c.certified, templates.synthetic_label(c.names)), c.names) for c in ctxs.values()]
    wrong = {"id": 99, "text": "Income has a strong effect."}
    answers.append({"sentences": [wrong], "claims": [{"sentence_id": 99, "dsl": 'strength("income") == "strong"'}]})
    first = next(iter(ctxs))

    def respond(request: Request) -> dict:
        if request.role == "extractor":
            return stub_message(faithful_reading(request, answers))
        run = request.messages[0][1].split("RUN:")[1].split("\n")[0].strip()
        sentences = template_text(ctxs[run]) + ([[wrong["id"], wrong["text"]]] if run == first else [])
        return stub_message({"sentences": [{"id": i, "text": t} for i, t in sentences]}, usage={"input_tokens": 3000, "output_tokens": 300})

    return respond


def estimate(specs: list[e3.Spec], ctxs: dict[str, g.Context], client: Client, record: dict | None) -> float:
    """USD at batch prices: the plain writer's uncached calls (E3's measured writer rate), and three scoring
    readings per text not yet read (for a plain text not yet written, all three)."""
    rates, dollars = e3.RATES, 0.0
    for s in specs:
        texts = record["cells"][s.run_id] if record else {"template": template_text(ctxs[s.run_id]), "plain": None}
        for sentences in (texts["template"], texts["plain"]):
            reqs = e3.scoring_requests(sentences, ctxs[s.run_id], s.draw) if sentences else [None] * len(e3.SCORING_REPLICAS)
            dollars += sum(r is None or not (client.cache_dir / f"{r.key}.json").exists() for r in reqs) * rates["haiku extractor"]
        if not record:
            dollars += rates["haiku writer"]
    return dollars * settings.BATCH_DISCOUNT


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", action="store_true", help="the plain prompt's trial on the pilot datasets: 4 synchronous calls, texts only")
    parser.add_argument("--estimate", action="store_true", help="the cost at batch prices, no network")
    parser.add_argument("--dry", action="store_true", help="stub writer and extractor on E3's dry cells, no network")
    args = parser.parse_args()
    if p.load().version != E3_LEXICON:
        raise SystemExit(f"E3 was scored under lexicon {E3_LEXICON}, not {p.load().version}: pin it (VERIFIER_GATE_LEXICON={E3_LEXICON})")
    prompts.pin_extractor("x3")  # E3's scoring readings
    if not args.pilot and not args.dry and prompts.frozen(prompts.FROZEN_PLAIN) != prompts.hashes(prompts.PLAIN_NAMES):
        raise SystemExit("the plain prompts are not frozen as they are now: run --pilot, then freeze them (prompts.freeze)")
    specs = plan(args.pilot, args.dry)
    by_id = {s.run_id: s for s in specs}
    ctxs, handovers = e3.contexts(specs)
    out = SOURCE / "baselines" / prompts.PLAIN_VERSION
    if args.dry:
        scratch = Path(tempfile.mkdtemp(prefix="e3_baselines_dry_"))
        client, api, poll, out = Client("batch", cache_dir=scratch / "cache"), batch.StubBatchAPI(stub_responder(ctxs)), 0, scratch / "results"
        handovers = {rid: f"RUN: {rid}\n{t}" for rid, t in handovers.items()}
    else:
        client, api, poll = Client("sync" if args.pilot else "batch"), batch.BatchAPI(), batch.POLL_SECONDS
    if args.pilot:
        texts = write_plain(specs, handovers, lambda reqs: {r.key: client.call(r) for r in reqs})
        target = out / "pilot" / f"r{len(list((out / 'pilot').glob('r*'))) + 1}"
        target.mkdir(parents=True, exist_ok=True)
        (target / "texts.json").write_text(json.dumps({"prompts": prompts.hashes(prompts.PLAIN_NAMES), "cells": texts}, indent=1))
        for rid, t in texts.items():
            words = sum(len(s.split()) for _, s in t["sentences"] or [])
            print(f"\n{rid}: {len(t['sentences'] or [])} sentences, {words} words, ${t['cost']:.5f}")
            print("\n".join(f"  {i}. {s}" for i, s in t["sentences"] or []))
        print(f"\nwritten to {target}")
        return
    record_path = out / "texts.json"
    record = json.loads(record_path.read_text()) if record_path.exists() else None
    if record and set(record["cells"]) != set(by_id):
        raise SystemExit(f"{record_path} holds other cells than the plan")
    print(f"E3 baselines{' (no network)' if args.dry else ''}: {len(specs)} cells; plain prompts {prompts.PLAIN_VERSION}, extractor "
          f"{prompts.extractor_version()}; texts {'from ' + str(record_path) if record else 'to be written'}")  # fmt: skip
    if args.estimate:
        print(f"estimated cost at batch prices: ${estimate(specs, ctxs, client, record):.2f}")
        return
    waves = client.cache_dir / "batches" / "e3_baselines"
    if record is None:
        written = write_plain(specs, handovers, lambda reqs: batch.resolve(reqs, client, api, waves, poll=poll))
        record = {"plain prompts": prompts.PLAIN_VERSION, "prompts": prompts.hashes(prompts.PLAIN_NAMES), "writer": settings.WRITER,
                  "cells": {rid: {"template": template_text(ctxs[rid]), "plain": w["sentences"], "plain calls": w["calls"], "plain cost": w["cost"]}
                            for rid, w in written.items()}}  # fmt: skip
        out.mkdir(parents=True, exist_ok=True)
        record_path.write_text(json.dumps(record, indent=1))
    texts = {(rid, arm): c[arm] for rid, c in record["cells"].items() for arm in ("template", "plain") if c[arm]}
    scores = e3.score_texts(texts, ctxs, by_id, client, api, poll, scorer=scorer, folder=waves)
    rows = []
    for rid, c in record["cells"].items():
        for arm in ("template", "plain"):
            cost = 0.0 if arm == "template" else c["plain cost"]
            rows.append(cell(by_id[rid]) | {"arm": arm, "exit": "", "cost": cost} | scores.get((rid, arm), {"scored": False}))
    rows += gate_rows({rid for rid in by_id} | {rid.replace("_H1_", "_H2_") for rid in by_id})
    table = pd.DataFrame(rows).drop(columns=["readings"], errors="ignore")
    out.mkdir(parents=True, exist_ok=True)
    table.to_csv(out / "rows.csv", index=False)
    summarise(table).to_csv(out / "summary.csv", index=False)
    result = compare(table)
    result.to_csv(out / "compare.csv", index=False)
    pd.set_option("display.width", 250)
    print(result.set_index("arm").T.to_string())
    print(f"\nresults in {out}")


if __name__ == "__main__":
    main()
