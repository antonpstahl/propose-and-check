"""A blind random sample of E3's texts for human labels (D70; the review of 20 Oct, M3, fixes 1 and 4 in a cheap form).

E3's labelled residual (D52) rests on labels of flagged texts only: an AI assistant proposed them, the author
reviewed them, and neither step was recorded. Here a random sample of all of an E3 run's texts, flagged or not, is
labelled sentence by sentence by people who see neither the text's arm nor any checker's verdict. They follow a
guide fixed before the first label (blind_guide.md), and the page keeps every label's author and every change.

Sample (`--build`, seed SEED; fixed before any label, and a second build into the same folder is refused): from the
run's texts outside the pilot datasets (e3_independent.texts, both tiers where the run has both), simple random
samples of SIZES[kind] first drafts, LLM-written releases (RELEASED, RELEASED_REDUCED) and templates. A text drawn
twice (a draft released as written) is shown once. The items are shuffled and numbered in that order (B01, ...);
the first OVERLAP of them, a random subset, go to the second rater as well.

A rater sees each text sentence by sentence, the model's facts as the H1 handover states them (the same for every
text about that model: an H2 writer also saw the certified statements, which would show what the verifier
certifies), and the words table of the run's extractor prompt (the writer's table). Nothing about the text's
source, the gate, the readers or the critic is shown. Templates read like templates, so their source cannot be hidden: a limit, reported.
The sentences are shown numbered 1 to n (D77): a text the gate reduced keeps its sentences' ids, so their gaps
would show the exit state and which sentences failed; the run's ids are kept in key.csv.

Written to results/e3/<source>/blind/:
- protocol.json: seed, populations, sizes, the hashes of the guide, the items and the key, the counting rules;
- guide.md: the guide as fixed;
- items.json: what the page shows;
- key.csv: item to run, arm, kind, tier and exit, and the run's sentence ids in the order shown, not for raters;
- blind_page.html: the page, from blind_page.html with the items and the guide embedded.
The page is published as an artifact whose store keeps each rater's labels under raters/<their id>/, readable by
the page's owner only (so the second rater never sees the first's), with each label's history: who set it, when,
and every change. Labels are set only through the page; Claude only reads the store back.

`--score <folder>` reads the store as read back: one JSON file per rater ({"rater": {...}, "labels": {item: doc}}),
and adjudication.json if the raters settled their disagreements (who decided each label). It writes:
- score.csv: P_U per stratum and standard with 95% Wilson intervals; P_U(on) weighted by the strata's population
  sizes; E_U with a stratified bootstrap interval; open texts counted both ways;
- readers.csv: the readers' verdicts (e3_independent) against the labels: how many labelled errors each reader
  finds;
- raters.csv: the two raters on the overlap, per sentence and per text, with Cohen's kappa;
- provenance.csv: per label, who set it first and when, how often and by whom it was changed, and its final value.

Run:
  uv run python -m verifier_gate.experiments.e3_blind --build [--source v4-x5-m5 --tier synthetic]
  uv run python -m verifier_gate.experiments.e3_blind --score results/e3/<source>/blind/labels
"""

import argparse
import hashlib
import html
import json
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd

from verifier_gate.data import tiers
from verifier_gate.experiments import e2_labels, e2_text
from verifier_gate.experiments import e3_independent as ind
from verifier_gate.experiments.build_facts import load
from verifier_gate.experiments.e2_false_alarms import wilson
from verifier_gate.llm.handover import handover
from verifier_gate.verifier.certified import certified_plan

VERSION = "b1"
SEED = 20261022
SIZES = {"draft": 30, "LLM-written": 40, "template": 10}
OVERLAP = 24  # the first items in the shuffled order also go to the second rater
GUIDE = Path(__file__).with_name("blind_guide.md")
PAGE = Path(__file__).with_name("blind_page.html")
LABELS = ("supported", "false", "unsettled", "misleading", "nothing", "unsure")
WHOLE = ("yes", "no", "unsure")
ERRORS = {"refuted": ("false",), "release rule": ("false", "unsettled"), "broad": ("false", "unsettled", "misleading")}
BOOT = 4000


def folder(source: str = ind.SOURCE) -> Path:
    return ind.out_folder(source).parent / "blind"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --- the sample -------------------------------------------------------------------------------------------


def draw(items: list[dict], sizes: dict = SIZES, seed: int = SEED) -> list[dict]:
    """Simple random samples per kind (draft, LLM-written, template), each from the texts in run order."""
    rng, out = np.random.default_rng(seed), []
    for kind, n in sizes.items():
        population = sorted((t for t in items if t["kind"] == kind), key=lambda t: t["run"])
        out += [population[i] for i in sorted(rng.choice(len(population), min(n, len(population)), replace=False))]
    return out


def shown_texts(sample: list[dict], seed: int = SEED) -> tuple[list[list], dict[str, list[dict]]]:
    """The distinct texts of the sample in a random order, and the sampled entries behind each (a draft released as
    written is one text, two entries)."""
    by_text: dict[str, list[dict]] = {}
    for t in sample:
        by_text.setdefault(json.dumps(t["sentences"]), []).append(t)
    keys = sorted(by_text)
    order = np.random.default_rng(seed + 1).permutation(len(keys))
    return [json.loads(keys[i]) for i in order], {keys[i]: by_text[keys[i]] for i in order}


def shown(sentences: list[list]) -> list[list]:
    """A text's sentences as shown: numbered 1 to n in their order (D77), the run's ids dropped."""
    return [[k, text] for k, (_, text) in enumerate(sentences, 1)]


def named(sentences: list[str], shown: list[str]) -> list[str]:
    """The features a text names: the synthetic tier by e2_labels.MENTIONS, other names (column codes) as words."""
    text = " ".join(sentences).lower()
    pattern = lambda f: e2_labels.MENTIONS.get(f) or rf"(?<![\w]){re.escape(f.lower())}(?![\w])"  # noqa: E731
    return [f for f in shown if re.search(pattern(f), text)]


def facts_of(text: dict, cache: dict) -> str:
    """The model's facts as the H1 handover states them, under the text's names, as head and blocks (e2_labels.blocks)."""
    key = f"{text['scenario']}_{text['model']}_{text['naming']}"
    if key not in cache:
        scenario = tiers.scenario(text["scenario"])
        facts = load(scenario, text["model"])
        h = handover(facts, tiers.generate(scenario).X, "H1", certified_plan(facts), names=e2_text.NAMES[text["naming"]],
                     descriptions=e2_text.DESCRIPTIONS[tiers.name(scenario)])  # fmt: skip
        head, blocks = e2_labels.blocks(h.text)
        cache[key] = {"head": head, "blocks": blocks}
    return key


def word_table(source: str) -> list[list[str]]:
    """The words table of the run's extractor prompt (the writer's): words in the text and their meaning."""
    rows = []
    for line in ind.extractor_system(source).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) == 3 and not set(cells[0]) <= set("-: ") and cells[0] != "Words in the text":
            rows.append([cells[0].replace('"', ""), cells[2]])
    if not rows:
        raise ValueError(f"no words table in {source}'s extractor prompt")
    return rows


def guide_html(text: str) -> str:
    """The guide's Markdown (headings, paragraphs, lists, bold) as HTML for the page."""
    out, para, items = [], [], []
    inline = lambda s: re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(s, quote=False))  # noqa: E731

    def flush():
        if para:
            out.append(f"<p>{inline(' '.join(para))}</p>")
            para.clear()
        if items:
            out.append("<ul>" + "".join(f"<li>{inline(i)}</li>" for i in items) + "</ul>")
            items.clear()

    for line in text.splitlines():
        if line.startswith("#"):
            flush()
            level = min(len(line) - len(line.lstrip("#")) + 1, 4)
            out.append(f"<h{level}>{inline(line.lstrip('# '))}</h{level}>")
        elif line.startswith("- "):
            if para:
                flush()
            items.append(line[2:])
        elif line.startswith("  ") and items:
            items[-1] += " " + line.strip()
        elif line.strip():
            if items:
                flush()
            para.append(line.strip())
        else:
            flush()
    flush()
    return "\n".join(out)


def build(source: str = ind.SOURCE, out: Path | None = None, tier: str | None = None) -> Path:
    out = out or folder(source)
    if (out / "protocol.json").exists():
        raise SystemExit(f"{out} already holds a sample: it is fixed once built (remove the folder to draw again before any label)")
    items = [t for t in ind.texts(source=source) if tier is None or t["tier"] == tier]
    sample = draw(items)
    order, entries = shown_texts(sample)
    facts, texts, key = {}, [], []
    for k, sentences in enumerate(order, 1):
        item, behind = f"B{k:02d}", entries[json.dumps(sentences)]
        fid = facts_of(behind[0], facts)
        names = [n for b in facts[fid]["blocks"] for n in b["names"] if len(b["names"]) == 1]
        texts.append({"id": item, "facts": fid, "model": behind[0]["model"], "named": named([s for _, s in sentences], names), "sentences": shown(sentences)})
        key += [{"item": item, "run": t["run"], "arm": t["arm"], "kind": t["kind"], "tier": t["tier"], "scenario": t["scenario"],
                 "exit": t["exit"], "second rater": k <= OVERLAP, "sentence ids": json.dumps([sid for sid, _ in sentences])} for t in behind]  # fmt: skip
    out.mkdir(parents=True, exist_ok=True)
    guide = GUIDE.read_text()
    (out / "guide.md").write_text(guide)
    data = {"version": VERSION, "source": source, "guide": guide_html(guide), "guide_sha": hashlib.sha256(guide.encode()).hexdigest(),
            "words": word_table(source), "edges": {k: round(v * 100, 3) for k, v in ind.lexicon(source).strength.items()},
            "facts": facts, "items": texts, "overlap": [it["id"] for it in texts[:OVERLAP]]}  # fmt: skip
    (out / "items.json").write_text(json.dumps(data, indent=1))
    pd.DataFrame(key).to_csv(out / "key.csv", index=False)
    page(out)
    population = pd.Series([t["kind"] for t in items]).value_counts().to_dict()
    protocol = {
        "version": VERSION, "source": source, "tier": tier or "all", "built": time.strftime("%Y-%m-%dT%H:%M:%S"), "seed": SEED,
        "population": {"texts outside the pilot datasets, by kind": population,
                       "by tier and kind": {f"{tier} {kind}": n for (tier, kind), n in pd.DataFrame(items).groupby(["tier", "kind"]).size().items()}},
        "sizes": SIZES, "sampled entries": len(key), "texts shown": len(texts), "sentence ids": "shown 1 to n; the run's ids in key.csv (D77)", "second rater": f"the first {OVERLAP} items in the shown order",
        "sha256": {"guide.md": digest(out / "guide.md"), "items.json": digest(out / "items.json"), "key.csv": digest(out / "key.csv")},
        "labels": {"sentence": list(LABELS), "whole text": list(WHOLE), "reads the words differently": "a flag per sentence"},
        "standards": {name: f"a sentence labelled {' or '.join(kinds)}" + (", or the whole text a wrong picture" if name == "broad" else "")
                      for name, kinds in ERRORS.items()},
        "open": "no error but an unsure sentence or whole-text answer: reported as an error and as no error",
        "estimators": "P_U per stratum with 95% Wilson intervals; P_U(on) = the LLM-written and template strata weighted by their "
                      "population sizes; E_U = 1 - P_U(on) / P_U(off), interval from a stratified bootstrap (BOOT draws within strata)",
        "blinding": "raters see the text, the model's facts as the H1 handover states them (the same for every text about the model) "
                    "and the words table; not the arm, exit state, gate verdict, readers' or critic's flags. Templates are "
                    "recognisable by their fixed wording.",
        "raters": {"first": "the author, on every item (the page's owner)", "second": f"to be named before labelling; the first {OVERLAP} items"},
        "provenance": "the page stores each rater's labels under raters/<id>/ with the history of every change (time, field, old and new "
                      "value); labels are set only through the page",
    }  # fmt: skip
    (out / "protocol.json").write_text(json.dumps(protocol, indent=1) + "\n")
    print(f"{len(key)} sampled entries, {len(texts)} texts shown, {OVERLAP} for the second rater; {len(facts)} fact sets; written to {out}")
    return out


def page(out: Path) -> Path:
    """The labelling page with items.json embedded (nothing from key.csv)."""
    data = json.dumps(json.loads((out / "items.json").read_text()), separators=(",", ":")).replace("</", "<\\/")
    path = out / "blind_page.html"
    path.write_text(PAGE.read_text().replace("__DATA__", data))
    return path


# --- the labels -------------------------------------------------------------------------------------------


def read_raters(labels_dir: Path) -> dict[str, dict]:
    """One file per rater, as read back from the store: {"rater": {"id", "code", "owner", ...}, "labels": {item: doc}}."""
    out = {}
    for path in sorted(labels_dir.glob("*.json")):
        if path.name == "adjudication.json":
            continue
        record = json.loads(path.read_text())
        out[record["rater"]["code"]] = record
    if not out:
        raise SystemExit(f"no rater files in {labels_dir}")
    return out


def text_verdict(doc: dict | None, sentence_ids: list[int], standard: str) -> str:
    """error, open or ok under a standard; missing if a sentence or the whole-text answer has no label."""
    if not doc:
        return "missing"
    labels = doc.get("labels", {})
    values = [labels.get(str(s)) for s in sentence_ids]
    whole = doc.get("whole")
    if any(v is None for v in values) or whole is None:
        return "missing"
    if any(v in ERRORS[standard] for v in values) or (standard == "broad" and whole == "yes"):
        return "error"
    return "open" if "unsure" in values or whole == "unsure" else "ok"


def primary(raters: dict[str, dict], adjudication: dict | None) -> tuple[str, dict]:
    """The first rater's labels (the page's owner), with adjudicated items replacing theirs."""
    code = next((c for c, r in raters.items() if r["rater"].get("owner")), next(iter(raters)))
    docs = dict(raters[code]["labels"])
    for item, decided in (adjudication or {}).items():
        docs[item] = {**docs.get(item, {}), "labels": {**docs.get(item, {}).get("labels", {}), **decided.get("labels", {})},
                      **({"whole": decided["whole"]} if "whole" in decided else {})}  # fmt: skip
    return code, docs


def stratum_estimates(verdicts: pd.DataFrame, population: dict[str, int]) -> pd.DataFrame:
    """Per standard and stratum: P_U (open texts as no error, and as errors) with Wilson intervals; P_U(on) weighted
    by population; E_U with a stratified bootstrap interval."""
    rng, rows = np.random.default_rng(SEED), []
    on_weights = {k: population.get(k, 0) for k in ("LLM-written", "template")}
    total_on = sum(on_weights.values())
    for standard in ERRORS:
        boot = {}
        for kind in SIZES:
            v = verdicts[(verdicts.kind == kind) & (verdicts[standard] != "missing")][standard]
            n, k, k_open = len(v), int((v == "error").sum()), int(v.isin(["error", "open"]).sum())
            lo, hi = wilson(k, n) if n else (np.nan, np.nan)
            rows.append({"standard": standard, "stratum": kind, "labelled": n, "errors": k, "open": k_open - k,
                         "P_U": round(k / n, 4) if n else np.nan, "lo": round(lo, 4), "hi": round(hi, 4),
                         "P_U, open as errors": round(k_open / n, 4) if n else np.nan})  # fmt: skip
            errors = (v == "error").to_numpy(float)
            boot[kind] = rng.choice(errors, (BOOT, n)).mean(1) if n else np.full(BOOT, np.nan)
        point = {r["stratum"]: r["P_U"] for r in rows if r["standard"] == standard}
        p_on = sum(on_weights[k] * point[k] for k in on_weights) / total_on if total_on else np.nan
        on_boot = sum(on_weights[k] * boot[k] for k in on_weights) / total_on if total_on else np.full(BOOT, np.nan)
        with np.errstate(divide="ignore", invalid="ignore"):
            e_boot = 1 - on_boot / boot["draft"]
        e_lo, e_hi = ind.interval(e_boot)
        on_lo, on_hi = ind.interval(on_boot)
        rows.append({"standard": standard, "stratum": "on (weighted)", "P_U": round(p_on, 4), "lo": on_lo, "hi": on_hi})
        rows.append({"standard": standard, "stratum": "E_U", "P_U": round(1 - p_on / point["draft"], 4) if point["draft"] else np.nan,
                     "lo": e_lo, "hi": e_hi})  # fmt: skip
    return pd.DataFrame(rows)


def kappa_labels(a: list, b: list) -> float:
    """Cohen's kappa for two raters' categorical labels."""
    if not a:
        return np.nan
    cats = sorted(set(a) | set(b))
    observed = np.mean([x == y for x, y in zip(a, b)])
    expected = sum((a.count(c) / len(a)) * (b.count(c) / len(b)) for c in cats)
    return round((observed - expected) / (1 - expected), 3) if expected < 1 else np.nan


def raters_table(raters: dict[str, dict], items: dict[str, dict], overlap: list[str]) -> pd.DataFrame:
    """The first two raters on the overlap: sentence labels (all six, and error vs not by each standard) and text verdicts."""
    if len(raters) < 2:
        return pd.DataFrame()
    (c1, r1), (c2, r2) = list(raters.items())[:2]
    rows = []
    pairs = [(r1["labels"].get(i, {}), r2["labels"].get(i, {}), items[i]) for i in overlap if i in r1["labels"] and i in r2["labels"]]
    s1 = [d1.get("labels", {}).get(str(s)) for d1, d2, it in pairs for s, _ in it["sentences"]]
    s2 = [d2.get("labels", {}).get(str(s)) for d1, d2, it in pairs for s, _ in it["sentences"]]
    both = [(x, y) for x, y in zip(s1, s2) if x and y]
    a, b = [x for x, _ in both], [y for _, y in both]
    rows.append({"unit": "sentence", "standard": "all six labels", "pairs": len(both), "agreement": round(np.mean([x == y for x, y in both]), 3) if both else np.nan,
                 "kappa": kappa_labels(a, b), "raters": f"{c1}, {c2}"})  # fmt: skip
    for standard, kinds in ERRORS.items():
        ea, eb = [x in kinds for x in a], [y in kinds for y in b]
        rows.append({"unit": "sentence", "standard": standard, "pairs": len(both), "agreement": round(np.mean([x == y for x, y in zip(ea, eb)]), 3) if both else np.nan,
                     "kappa": kappa_labels(ea, eb), "raters": f"{c1}, {c2}"})  # fmt: skip
        ids = lambda it: [s for s, _ in it["sentences"]]  # noqa: E731
        v = [(text_verdict(d1, ids(it), standard), text_verdict(d2, ids(it), standard)) for d1, d2, it in pairs]
        v = [(x == "error", y == "error") for x, y in v if "missing" not in (x, y)]
        rows.append({"unit": "text", "standard": standard, "pairs": len(v), "agreement": round(np.mean([x == y for x, y in v]), 3) if v else np.nan,
                     "kappa": kappa_labels([x for x, _ in v], [y for _, y in v]), "raters": f"{c1}, {c2}"})  # fmt: skip
    return pd.DataFrame(rows)


def provenance(raters: dict[str, dict], adjudication: dict | None) -> pd.DataFrame:
    """Per rater, item and field (a sentence's label, its "reads differently" flag, the whole-text answer): who set it
    first and when, the changes and who made them, and the final value; adjudicated labels with who decided them."""
    rows = []
    for code, record in raters.items():
        for item, doc in record["labels"].items():
            events = {}
            for e in doc.get("history", []):
                events.setdefault(e["field"], []).append(e)
            for field, history in sorted(events.items()):
                history = sorted(history, key=lambda e: e["at"])
                rows.append({"item": item, "field": field, "rater": code, "proposed by": code if history[0].get("by") == record["rater"]["id"] else history[0].get("by"),
                             "proposed": history[0]["to"], "proposed at": history[0]["at"], "changes": len(history) - 1,
                             "changed by": ", ".join(sorted({code if e.get("by") == record["rater"]["id"] else str(e.get("by")) for e in history[1:]})),
                             "changes made": "; ".join(f"{e['at']}: {e['from']} -> {e['to']}" for e in history[1:]),
                             "final": history[-1]["to"], "final at": history[-1]["at"], "source": "page"})  # fmt: skip
    for item, decided in (adjudication or {}).items():
        for field, value in [*((f"s{s}", v) for s, v in decided.get("labels", {}).items()), *((("whole", decided["whole"]),) if "whole" in decided else ())]:
            rows.append({"item": item, "field": field, "rater": "adjudication", "proposed by": decided.get("proposed_by", ""), "proposed": value,
                         "proposed at": decided.get("at", ""), "changes": 0, "changed by": "", "changes made": "", "final": value,
                         "final at": decided.get("at", ""), "source": f"adjudicated by {decided.get('decided_by', '')}"})  # fmt: skip
    return pd.DataFrame(rows)


def readers_table(verdicts: pd.DataFrame, source: str) -> pd.DataFrame:
    """Each reader's verdict (e3_independent, release rule and refuted) against the labels, on the sampled entries."""
    rows = []
    texts = {r: pd.read_csv(ind.out_folder(source) / r / "texts.csv").set_index(["run", "arm"]) for r in ind.READERS if (ind.out_folder(source) / r / "texts.csv").exists()}
    for reader, table in texts.items():
        for standard, human in (("refuted", "refuted"), ("release rule", "release rule")):
            rule = ind.STANDARDS[standard]
            flagged = [bool(rule(table.loc[(run, arm)])) if (run, arm) in table.index and table.loc[(run, arm)]["scored"] else None
                       for run, arm in zip(verdicts.run, verdicts.arm)]  # fmt: skip
            v = verdicts.assign(flagged=flagged)
            v = v[v.flagged.notna() & v[human].isin(["error", "ok"])]
            err, ok = v[v[human] == "error"], v[v[human] == "ok"]
            for kind, part_err, part_ok in [("all", err, ok), *((k, err[err.kind == k], ok[ok.kind == k]) for k in SIZES)]:
                rows.append({"reader": reader, "standard": standard, "stratum": kind, "labelled errors": len(part_err),
                             "flagged by the reader": int(part_err.flagged.astype(bool).sum()), "missed": int((~part_err.flagged.astype(bool)).sum()),
                             "labelled no error": len(part_ok), "flagged anyway": int(part_ok.flagged.astype(bool).sum())})  # fmt: skip
    return pd.DataFrame(rows)


def score(out: Path, labels_dir: Path) -> pd.DataFrame:
    protocol = json.loads((out / "protocol.json").read_text())
    if digest(out / "guide.md") != protocol["sha256"]["guide.md"] or digest(out / "items.json") != protocol["sha256"]["items.json"]:
        raise ValueError("the guide or the items changed after the sample was fixed")
    data = json.loads((out / "items.json").read_text())
    items = {it["id"]: it for it in data["items"]}
    raters = read_raters(labels_dir)
    stale = [c for c, r in raters.items() if r["rater"].get("guide") not in (None, data["guide_sha"])]
    if stale:
        raise ValueError(f"rater(s) {stale} labelled under another guide")
    adjudication = json.loads((labels_dir / "adjudication.json").read_text()) if (labels_dir / "adjudication.json").exists() else None
    _, docs = primary(raters, adjudication)
    key = pd.read_csv(out / "key.csv")
    for standard in ERRORS:
        key[standard] = [text_verdict(docs.get(r.item), [s for s, _ in items[r.item]["sentences"]], standard) for r in key.itertuples()]
    population = protocol["population"]["texts outside the pilot datasets, by kind"]
    table = stratum_estimates(key, population)
    table.to_csv(out / "score.csv", index=False)
    key.to_csv(out / "verdicts.csv", index=False)
    readers_table(key, protocol["source"]).to_csv(out / "readers.csv", index=False)
    raters_table(raters, items, data["overlap"]).to_csv(out / "raters.csv", index=False)
    provenance(raters, adjudication).to_csv(out / "provenance.csv", index=False)
    return table


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=ind.SOURCE, choices=sorted(ind.SOURCES), help="the E3 run to sample")
    parser.add_argument("--build", action="store_true", help="draw the sample and write the page (refused if one exists)")
    parser.add_argument("--tier", choices=("synthetic", "plasmode"), help="draw from one tier only")
    parser.add_argument("--page", action="store_true", help="rebuild only the page from items.json")
    parser.add_argument("--score", type=Path, help="the folder with the labels read back, one JSON file per rater")
    args = parser.parse_args()
    out = folder(args.source)
    if args.build:
        build(args.source, out, args.tier)
    elif args.page:
        print(page(out))
    if args.score:
        pd.set_option("display.width", 250)
        print(score(out, args.score).to_string(index=False))


if __name__ == "__main__":
    main()
