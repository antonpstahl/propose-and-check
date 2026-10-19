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
blocking claim a misreading) or open, and the false-alarm rate per text, blocked-but-correct over correct texts. `--e3 labels.json` writes e3_residual.csv: E3's P_U(on) re-scored with the
labels.
"""

import argparse
import json
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
from verifier_gate.experiments.e3_end_to_end import RESULTS as E3_RESULTS, SCORING_REPLICAS
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
    return prompts.historical_extractor_system("x3")


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


def e3_residual(out: Path, labels_path: Path) -> pd.DataFrame:
    """E3's P_U(on) re-scored with the labels (plan §14.21). E3 counts a gate-on text if its scoring readings (x3,
    replicas 3 to 5) find a claim false against M in at least two readings; those claims are x3's blocked claims of
    kind "false" here. A text keeps its count if a label calls one of them a real error; open if one is unsure;
    else it was a misreading. Haiku writer, outside the pilot datasets, as in the false-alarm run."""
    labels = json.loads(labels_path.read_text())
    key = pd.read_csv(out / "key.csv")
    key["human"] = [labels.get(r.item, {}).get("labels", {}).get(str(r.claim)) for r in key.itertuples()]
    false = key[(key.x3 == True) & (key.kind == "false")]  # noqa: E712
    verdict = false.groupby("run").human.agg(lambda h: "error" if "error" in set(h) else "open" if "unsure" in set(h) else "misreading")
    rows_ = pd.read_csv(E3_RESULTS / e2_text.E3_SOURCE / "haiku" / "rows.csv")
    on = rows_[(rows_["on scored"] == True) & (~rows_["pilot dataset"])]  # noqa: E712
    if set(on.run[on["on false M"] > 0]) != set(verdict.index):
        raise ValueError("E3's texts with a false claim are not x3's blocked texts with a false claim")
    on = on.assign(verdict=on.run.map(verdict))
    rows = []
    for naming, part in [*on.groupby("naming"), ("both", on)]:
        n, error, open_ = len(part), int((part.verdict == "error").sum()), int((part.verdict == "open").sum())
        rows.append({"naming": naming, "texts scored": n, "with a false claim (E3)": int(part.verdict.notna().sum()),
                     "real error": error, "open": open_, "misreading": int((part.verdict == "misreading").sum()),
                     "P_U on (E3)": round(float(part.verdict.notna().mean()), 4), "P_U on, labelled": round(error / n, 4),
                     "P_U on, open as errors": round((error + open_) / n, 4)})  # fmt: skip
    table = pd.DataFrame(rows)
    table.to_csv(out / "e3_residual.csv", index=False)
    return table


DRAFTS = 40  # first drafts sampled for a labelled P_U(off), fixed before any draft was read (plan §14.21)


def drafts(out: Path, client: Client) -> pd.DataFrame:
    """E3's gate-off arm: the Haiku writer's first drafts outside the pilot datasets, with E3's scoring readings (x3,
    replicas 3 to 5) from the cache ($0) and E3's scoring rule (a claim in at least two readings, no plan). Checks
    each draft's count of claims false against M against E3's rows, then draws DRAFTS of the drafts with one (SEED)
    and writes drafts/items.json (sentences, claims, the facts shown) and drafts/key.csv for labelling."""
    system, ctxs, found = x3_system(), {}, {}
    for path in sorted((E3_RESULTS / e2_text.E3_SOURCE / "haiku" / "runs").glob("*.json")):
        run = json.loads(path.read_text())
        scenario, model, variant, draw, writer, naming = run["run_id"].split("_")
        first = next((v for v in run["versions"] if v["source"] in ("proposer", "format retry")), None)
        if scenario in e2_text.PILOT or first is None:
            continue
        text = {"run": run["run_id"], "sentences": first["sentences"]}
        ctx = e2_text.context(e2_text.Case(run["run_id"], "draft", scenario, model, naming, first["sentences"], [], None, {}), ctxs)
        rs = requests_for(text, ctx, system)
        answers = {r.key: a for r in rs if (a := client.lookup(r)) is not None}
        good, bad = readings(text, ctx, rs, answers)
        again = [replace(r, attempt=1) for r in bad]
        answers |= {r.key: a for r in again if (a := client.lookup(r)) is not None}
        good += readings(text, ctx, again, answers)[0]
        if len(good) < rt.EXTRACTED:
            continue
        trip = rt.compare(good, [], [i for i, _ in first["sentences"]], ctx.facts, ctx.certified)
        found[run["run_id"]] = (scenario, model, naming, first["sentences"], [(sid, line, reason, evidence) for sid, line, value, code, reason, evidence in trip.unplanned if value == p.FALSE])  # fmt: skip
    rows_ = pd.read_csv(E3_RESULTS / e2_text.E3_SOURCE / "haiku" / "rows.csv")
    off = rows_[(rows_["off scored"] == True) & (~rows_["pilot dataset"])].set_index("run")  # noqa: E712
    counts = {run: len(c[4]) for run, c in found.items()}
    if set(counts) != set(off.index) or any(counts[run] != off.at[run, "off false M"] for run in counts):
        raise ValueError("the first drafts' readings do not reproduce E3's gate-off scores")
    with_false = sorted(run for run, n in counts.items() if n)
    sample = sorted(np.random.default_rng(SEED).choice(with_false, DRAFTS, replace=False))
    facts, items, key = {}, [], []
    for k, run in enumerate(sample, 1):
        scenario, model, naming, sentences, claims = found[run]
        ctx_id = f"{scenario}_{model}_{naming}"
        if ctx_id not in facts:
            s = next(x for x in dgp.SCENARIOS if x.id == scenario)
            f = load(s, model)
            head, parts = e2_labels.blocks(handover(f, dgp.generate(s).X, "H1", certified_plan(f), names=NAMINGS[naming]).text)
            facts[ctx_id] = {"head": head, "blocks": parts}
        shown = [n for b in facts[ctx_id]["blocks"] for n in b["names"] if len(b["names"]) == 1]
        listed = []
        for c, (sid, line, reason, evidence) in enumerate(claims):
            listed.append({"sentence_id": sid, "dsl": line, "words": words(line, naming), "why": f"{reason or 'the facts contradict it'} ({evidence})"})
            key.append({"item": f"D{k:03d}", "claim": c, "run": run, "sentence id": sid, "dsl": line})
        mentioned = " ".join([s for _, s in sentences] + [c["words"] for c in listed])
        items.append({"id": f"D{k:03d}", "run": run, "facts": ctx_id, "sentences": sentences,
                      "named": e2_labels.named([mentioned], shown), "claims": listed})  # fmt: skip
    folder = out / "drafts"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "items.json").write_text(json.dumps({"seed": SEED, "drafts with a false claim": len(with_false),
                                                   "drafts scored": len(counts), "facts": facts, "items": items}, indent=1))  # fmt: skip
    pd.DataFrame(key).to_csv(folder / "key.csv", index=False)
    return pd.DataFrame({"drafts scored": [len(counts)], "with a false claim": [len(with_false)], "sampled": [len(sample)], "claims sampled": [len(key)]})


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson interval for a proportion k of n."""
    p, d = k / n, 1 + z**2 / n
    centre, half = (p + z**2 / (2 * n)) / d, z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / d
    return centre - half, centre + half


def e3_effect(out: Path, on_labels: Path, off_labels: Path) -> pd.DataFrame:
    """E3's P_U off and on and E_U = 1 - P_U(on) / P_U(off) with human labels (Haiku, outside the pilot datasets,
    both namings). On: every gate-on text with a false claim is labelled (e3_residual). Off: a random sample of the
    first drafts with a false claim (drafts); P_U(off) = the share of drafts with a false claim x the sampled share
    with a real error, with its 95% Wilson interval. Open texts (an unsure claim, no error) give the upper bounds."""
    on = e3_residual(out, on_labels).set_index("naming").loc["both"]
    labels = json.loads(off_labels.read_text())
    folder = out / "drafts"
    meta = json.loads((folder / "items.json").read_text())
    key = pd.read_csv(folder / "key.csv")
    key["human"] = [labels.get(r.item, {}).get("labels", {}).get(str(r.claim)) for r in key.itertuples()]
    verdict = key.groupby("item").human.agg(lambda h: "error" if "error" in set(h) else "open" if "unsure" in set(h) else "misreading")
    n, error, open_ = len(verdict), int((verdict == "error").sum()), int((verdict == "open").sum())
    share = meta["drafts with a false claim"] / meta["drafts scored"]
    lo, hi = wilson(error, n)
    p_on, p_on_hi = on["P_U on, labelled"], on["P_U on, open as errors"]
    p_off, p_off_lo, p_off_open = share * error / n, share * lo, share * (error + open_) / n
    rows = [
        {"quantity": "P_U off, E3 (unlabelled)", "value": round(share, 4)},
        {"quantity": "sampled drafts: real error / open / misreading", "value": f"{error} / {open_} / {n - error - open_} of {n}"},
        {"quantity": "P_U off, labelled", "value": round(p_off, 4)},
        {"quantity": "P_U off, labelled, 95% interval", "value": f"{share * lo:.4f} to {share * hi:.4f}"},
        {"quantity": "P_U off, open drafts counted as errors", "value": round(p_off_open, 4)},
        {"quantity": "P_U on, E3 (unlabelled)", "value": on["P_U on (E3)"]},
        {"quantity": "P_U on, labelled (open: as errors)", "value": f"{p_on} ({p_on_hi})"},
        {"quantity": "E_U, E3 (unlabelled)", "value": round(1 - on["P_U on (E3)"] / share, 3)},
        {"quantity": "E_U, labelled", "value": round(1 - p_on / p_off, 3)},
        {"quantity": "E_U, worst case (P_U on with open texts, P_U off at its interval's low end)", "value": round(1 - p_on_hi / p_off_lo, 3)},
    ]
    table = pd.DataFrame(rows)
    table.to_csv(out / "e3_effect.csv", index=False)
    return table


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--x3", action="store_true", help="x3 only: E3's scoring readings from the cache, $0")
    parser.add_argument("--x4", action="store_true", help="x4 only: new readings, batched")
    parser.add_argument("--estimate", action="store_true", help="count the calls and estimate the cost, no network")
    parser.add_argument("--page", action="store_true", help="the labelling page from the statements on disk, no network")
    parser.add_argument("--score", type=Path, help="labels read back from the page's store")
    parser.add_argument("--e3", type=Path, help="labels: E3's residual P_U(on) re-scored with them")
    parser.add_argument("--drafts", action="store_true", help="sample E3's first drafts with a false claim for labels, $0")
    parser.add_argument("--effect", type=Path, nargs=2, metavar=("ON_LABELS", "OFF_LABELS"), help="E3's P_U and E_U with human labels")
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
    if args.e3:
        print(e3_residual(out, args.e3).to_string(index=False))
        return
    if args.drafts:
        print(drafts(out, Client("batch")).to_string(index=False))
        return
    if args.effect:
        print(e3_effect(out, *args.effect).to_string(index=False))
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
