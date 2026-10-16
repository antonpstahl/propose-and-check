"""False alarms of the round trip on LLM-written text (D48, plan §14.19).

A false alarm is the round trip blocking a correct text. Text-level E2 measures it on the template texts only,
whose fixed wording is easy for the extractor, and its labelled LLM mutants are nearly all errors. Here the texts
are E3's released texts (non-pilot, e2_text.released_texts), each read three times apart from the gate: E3's
scoring readings (replicas 3 to 5, the run's draw). For x3 these are on disk (read from the cache only, $0); for
x4 they are new. Each text's round trip is the gate's (gate/roundtrip.compare with the text's plan). A passing
text cannot be a false alarm, so only what a reading blocks is labelled: a blocked statement is either a real
error the gate let through, or a misreading of a correct sentence (labels: experiments/e2_labels, --fa).

x3's system prompt comes from git (X3_COMMIT) and is checked against the hash kept in EXTRACTOR_HISTORY.

Run: `uv run python -m verifier_gate.experiments.e2_false_alarms [--x3 | --x4] [--estimate]`. Batched (x4);
stopping is safe, the same command resumes. Writes results/e2/<lexicon>/text/false_alarms/: texts_<v>.csv,
statements_<v>.csv.

Labels: `--page` groups the blocked statements of all versions on disk by sentence (one item per sentence, one
label per claim; never which extractor blocked it) and writes items.json, key.csv and fa_page.html (the template
fa_page.html next to this file). A claim is labelled error (the sentence says this, and the facts do not support
it: the block is right), misreading (the sentence does not say this: a false alarm) or unsure. `--score
labels.json` writes score.csv: per extractor version, the blocked texts that are real errors, false alarms (every
blocking claim a misreading) or open, and the false-alarm rate per text, blocked-but-correct over correct texts.
"""

import argparse
import hashlib
import json
import subprocess
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from verifier_gate.data import dgp
from verifier_gate.dsl.parse import DSLError, parse
from verifier_gate.experiments import e2_labels, e2_text
from verifier_gate.experiments.build_facts import load
from verifier_gate.experiments.pilot import NAMINGS
from verifier_gate.gate.template import phrase, synthetic_label
from verifier_gate.llm.handover import handover
from verifier_gate.verifier.certified import certified_plan
from verifier_gate.experiments.e3_end_to_end import SCORING_REPLICAS
from verifier_gate.gate import roundtrip as rt
from verifier_gate.lexicon import predicates as p
from verifier_gate.llm import batch, extract, prompts, settings
from verifier_gate.llm.client import Client, Request

X3_COMMIT = "56c77b0a"  # the last commit with extractor x3 (E3 and the first text-level E2 ran with it)
REPO = Path(__file__).parents[3]
PER_CALL = 1.628 / 9084  # USD per extractor call at batch prices, measured on the x4 rerun of the script mutants
PAGE = Path(__file__).with_name("fa_page.html")
SEED = 20261016
OPAQUE = {"noise_1": "feature a", "noise_2": "feature b"}


def x3_system() -> str:
    text = subprocess.run(["git", "show", f"{X3_COMMIT}:src/verifier_gate/llm/prompts/extract_system.md"], cwd=REPO,
                          capture_output=True, text=True, check=True).stdout  # fmt: skip
    system = text.replace("{dsl}", prompts.dsl_reference())
    if hashlib.sha256(system.encode()).hexdigest() != prompts.EXTRACTOR_HISTORY["x3"]["extract_system"]:
        raise ValueError("x3's system prompt from git does not match its frozen hash")
    return system


def requests_for(text: dict, ctx, system: str | None, attempt: int = 0) -> list[Request]:
    """E3's scoring readings of a released text: replicas 3 to 5 at the run's draw."""
    draw = int(text["run"].split("_")[3].lstrip("d"))
    features = extract.features_text(ctx.facts, ctx.names, ctx.descriptions)
    out = [replace(extract.extractor_request(text["sentences"], features, draw, k), attempt=attempt) for k in SCORING_REPLICAS]
    return [replace(r, system=system) for r in out] if system else out


def readings(text: dict, ctx, rs: list[Request], answers: dict) -> tuple[list, list[Request]]:
    ids, good, bad = {i for i, _ in text["sentences"]}, [], []
    for r in rs:
        try:
            good.append(extract.extraction_from(answers[r.key], ids, ctx.names))
        except (ValueError, KeyError, TypeError, AttributeError):
            bad.append(r)
    return good, bad


def run(version: str, client: Client, api, poll: float, log=print) -> tuple[pd.DataFrame, pd.DataFrame]:
    texts, ctxs = e2_text.released_texts(), {}
    system = x3_system() if version == "x3" else None
    case = lambda t: e2_text.Case(t["run"], "released", t["scenario"], t["model"], t["naming"], t["sentences"], t["plan"], None, {})  # noqa: E731
    requests = {t["run"]: requests_for(t, e2_text.context(case(t), ctxs), system) for t in texts}
    if version == "x3":  # on disk from E3: read from the cache, never sent
        answers = {r.key: a for rs in requests.values() for r in rs if (a := client.lookup(r)) is not None}
    else:
        answers = batch.resolve([r for rs in requests.values() for r in rs], client, api, poll=poll, log=log)
    got, retry = {}, {}
    for t in texts:
        got[t["run"]], bad = readings(t, e2_text.context(case(t), ctxs), requests[t["run"]], answers)
        retry[t["run"]] = [replace(r, attempt=1) for r in bad]
    again = [r for rs in retry.values() for r in rs]
    if again:
        log(f"{version}: {len(again)} answer(s) not a reading, retried once")
        if version == "x3":
            answers |= {r.key: a for r in again if (a := client.lookup(r)) is not None}
        else:
            answers |= batch.resolve(again, client, api, poll=poll, log=log)
        for t in texts:
            got[t["run"]] += readings(t, e2_text.context(case(t), ctxs), retry[t["run"]], answers)[0]
    rows, statements = [], []
    for t in texts:
        ctx, good = e2_text.context(case(t), ctxs), got[t["run"]]
        base = {"run": t["run"], "scenario": t["scenario"], "model": t["model"], "naming": t["naming"], "extractor": version}
        if len(good) < rt.EXTRACTED:
            rows.append(base | {"readings": len(good), "scored": False})
            continue
        trip = rt.compare(good, t["plan"], [i for i, _ in t["sentences"]], ctx.facts, ctx.certified)
        rows.append(base | {"readings": len(good), "scored": True, "blocked": not trip.passed, "failures": "; ".join(trip.failures())})
        text_of = dict((i, s) for i, s in t["sentences"])
        for sid, line, value, code, reason, evidence in trip.unplanned:
            if value != p.TRUE:
                statements.append(base | {"kind": value, "sentence id": sid, "sentence": text_of.get(sid, ""), "claim": line,
                                          "code": code or "", "reason": reason, "evidence": evidence})  # fmt: skip
        for sid, words in trip.numbers:
            statements.append(base | {"kind": "number", "sentence id": sid, "sentence": text_of.get(sid, ""), "claim": "; ".join(words)})
        for term in trip.missing:
            statements.append(base | {"kind": "not covered", "sentence id": None, "sentence": "", "claim": term})
        for sid, minor, strong in trip.emphasis:
            statements.append(base | {"kind": "emphasis", "sentence id": sid, "sentence": text_of.get(sid, ""),
                                      "claim": f"leads with {', '.join(minor)}; strong: {', '.join(strong)}"})  # fmt: skip
    return pd.DataFrame(rows), pd.DataFrame(statements)


# --- labels ------------------------------------------------------------------------------------------------


def words(claim_line: str, naming: str) -> str:
    """A blocked claim in plain words, in the names the text uses (the template's phrasing)."""
    base = synthetic_label()
    one = lambda t: OPAQUE.get(t, base(t)) if naming == "opaque" else base(t)  # noqa: E731
    label = lambda t: " and ".join(one(x.strip()) for x in t.split("&"))  # noqa: E731
    try:
        return phrase(parse(claim_line), label)
    except (DSLError, ValueError, KeyError, TypeError):
        return claim_line


def build_page(out: Path) -> Path:
    statements = pd.concat([pd.read_csv(f) for f in sorted(out.glob("statements_x*.csv"))], ignore_index=True)
    texts = {t["run"]: t for t in e2_text.released_texts()}
    facts, groups = {}, {}
    for _, r in statements.iterrows():
        sid = None if pd.isna(r["sentence id"]) else int(r["sentence id"])
        g = groups.setdefault((r.run, sid), {"claims": {}, "versions": set()})
        g["versions"].add(r.extractor)
        c = g["claims"].setdefault((r.kind, r.claim), {"versions": set(), "reason": r.get("reason"), "evidence": r.get("evidence")})
        c["versions"].add(r.extractor)
    order = np.random.default_rng(SEED).permutation(len(groups))
    keys = list(groups)
    items, key = [], []
    for k, idx in enumerate(order, 1):
        run, sid = keys[idx]
        t, g = texts[run], groups[keys[idx]]
        ctx_id = f"{t['scenario']}_{t['model']}_{t['naming']}"
        if ctx_id not in facts:
            scenario = next(x for x in dgp.SCENARIOS if x.id == t["scenario"])
            f = load(scenario, t["model"])
            head, parts = e2_labels.blocks(handover(f, dgp.generate(scenario).X, "H1", certified_plan(f), names=NAMINGS[t["naming"]]).text)
            facts[ctx_id] = {"head": head, "blocks": parts}
        shown = [n for b in facts[ctx_id]["blocks"] for n in b["names"] if len(b["names"]) == 1]
        claims = []
        for (kind, line), c in sorted(g["claims"].items(), key=lambda kv: (kv[0][0], str(kv[0][1]))):
            if kind in ("false", "undecidable"):
                reason = c["reason"] if isinstance(c["reason"], str) and c["reason"] else {"false": "the facts contradict it", "undecidable": "the facts do not settle it"}[kind]
                text, why = words(line, t["naming"]), reason + (f" ({c['evidence']})" if isinstance(c["evidence"], str) and c["evidence"] else "")
            elif kind == "number":
                text, why = f"states a number no claim can check: {line}", "a precise number the DSL cannot express is blocked (D44 b)"
            elif kind == "not covered":
                text, why = f"the text says nothing checkable about {line}", "each of the top terms must be covered by a supported claim"
            else:
                text, why = line, "the opening sentence must not lead with a minor term"
            claims.append({"kind": kind, "dsl": line, "words": text, "why": why})
            key.append({"item": f"F{k:03d}", "claim": len(claims) - 1, "run": run, "sentence id": sid, "kind": kind, "dsl": line,
                        "x3": "x3" in c["versions"], "x4": "x4" in c["versions"]})  # fmt: skip
        mentioned = " ".join([dict(t["sentences"]).get(sid, "")] + [c["words"] for c in claims])
        items.append({"id": f"F{k:03d}", "facts": ctx_id, "sentence_id": sid, "sentences": t["sentences"],
                      "named": e2_labels.named([mentioned], shown), "claims": claims})  # fmt: skip
    (out / "items.json").write_text(json.dumps({"seed": SEED, "facts": facts, "items": items}, indent=1))
    pd.DataFrame(key).to_csv(out / "key.csv", index=False)
    data = json.dumps({"facts": facts, "items": items}, separators=(",", ":")).replace("</", "<\\/")
    path = out / "fa_page.html"
    path.write_text(PAGE.read_text().replace("__DATA__", data))
    print(f"{len(items)} sentences, {len(key)} claims to label; written to {path}")
    return path


def score(out: Path, labels_path: Path) -> pd.DataFrame:
    """labels.json: {item id: {"labels": {claim index: "error" | "misreading" | "unsure"}}}."""
    labels = json.loads(labels_path.read_text())
    key = pd.read_csv(out / "key.csv")
    key["human"] = [labels.get(r.item, {}).get("labels", {}).get(str(r.claim)) for r in key.itertuples()]
    rows = []
    for version in ("x3", "x4"):
        path = out / f"texts_{version}.csv"
        if not path.exists():
            continue
        texts = pd.read_csv(path)
        scored = texts[texts.scored == True]  # noqa: E712
        blocked = scored[scored.blocked == True]  # noqa: E712
        mine = key[key[version] == True]  # noqa: E712
        verdict = {}
        for run in blocked.run:
            h = mine[mine.run == run].human.tolist()
            verdict[run] = "error" if "error" in h else ("false alarm" if h and all(x == "misreading" for x in h) else "open")
        counts = pd.Series(verdict).value_counts().to_dict()
        real, false_alarm = counts.get("error", 0), counts.get("false alarm", 0)
        correct = len(scored) - real - counts.get("open", 0)
        rows.append({"extractor": version, "texts scored": len(scored), "blocked": len(blocked), "real errors": real,
                     "false alarms": false_alarm, "open": counts.get("open", 0),
                     "false-alarm rate (per correct text)": round(false_alarm / correct, 3) if correct else float("nan"),
                     "claims": len(mine), "claims misread": int((mine.human == "misreading").sum()),
                     "claims right": int((mine.human == "error").sum()), "claims unsure": int((mine.human == "unsure").sum())})  # fmt: skip
    table = pd.DataFrame(rows)
    table.to_csv(out / "score.csv", index=False)
    return table


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--x3", action="store_true", help="x3 only: E3's scoring readings from the cache, $0")
    parser.add_argument("--x4", action="store_true", help="x4 only: new readings, batched")
    parser.add_argument("--estimate", action="store_true", help="count the calls and estimate the cost, no network")
    parser.add_argument("--page", action="store_true", help="the labelling page from the statements on disk, no network")
    parser.add_argument("--score", type=Path, help="labels read back from the page's store")
    args = parser.parse_args()
    versions = [v for v, on in (("x3", args.x3), ("x4", args.x4)) if on] or ["x3", "x4"]
    out = e2_text.RESULTS / p.load().version / "text" / "false_alarms"
    if args.page:
        build_page(out)
        return
    if args.score:
        pd.set_option("display.width", 250)
        print(score(out, args.score).to_string(index=False))
        return
    if args.estimate:
        n = len(e2_text.released_texts())
        calls = 3 * n * 1.14  # 14% of x4's answers were retried in the script rerun
        print(f"{n} released texts; x3: {3 * n} readings from the cache, $0; x4: about {calls:.0f} calls, about ${calls * PER_CALL:.2f}")
        return
    client, api = Client("batch"), batch.BatchAPI()
    out.mkdir(parents=True, exist_ok=True)
    for version in versions:
        if version != prompts.EXTRACTOR_VERSION and version != "x3":
            raise ValueError(f"no prompt for {version}")
        texts, statements = run(version, client, api, batch.POLL_SECONDS)
        texts.to_csv(out / f"texts_{version}.csv", index=False)
        statements.to_csv(out / f"statements_{version}.csv", index=False)
        scored = texts[texts.scored == True]  # noqa: E712
        print(f"{version}: {len(scored)} of {len(texts)} texts scored; blocked {int(scored.blocked.sum())} "
              f"({scored.blocked.mean():.1%}); {len(statements)} blocked statements; by kind "
              f"{statements.kind.value_counts().to_dict() if len(statements) else {}}")  # fmt: skip
    print(f"results in {out}; extractor model {settings.EXTRACTOR}")


if __name__ == "__main__":
    main()
