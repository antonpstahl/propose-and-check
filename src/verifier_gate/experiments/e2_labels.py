"""Human labels for the LLM mutants of text-level E2 (plan §14.17, decided 15 Oct).

The mutator's own labels are unreliable (§14.17): it declared errors without changing the sentence, and it often
declared the claim the sentence made before its change. So recall and false alarms of the round trip on
LLM-written errors rest on labels from the text: a simple random sample of SAMPLE changed sentences, each shown
before and after, with the facts the mutator saw (H1) for the features the sentences name, and never the gate's
verdict or the mutator's declared claim. The labeller answers: error (the new sentence says something false
about the model, or more than the facts support), no error, or unsure.

`--build` draws the sample (seed SEED) and writes results/e2/<lexicon>/text/labels/: items.json (what the
labelling page shows), label_page.html (the page, label_page.html in this folder with the items embedded; its
labels go to the page's own store, writable by its owner only) and key.csv (item to case, mutator label and the
gate's outcome; not for the labeller).
`--score labels.json` (the labels read back from the page's store) writes score.csv: recall and false alarms of
the round trip against the human labels, for each extractor version on disk, and the agreement with the
mutator's labels.
"""

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from verifier_gate.data import dgp
from verifier_gate.experiments import e2_text
from verifier_gate.experiments.build_facts import load
from verifier_gate.experiments.pilot import NAMINGS
from verifier_gate.lexicon import predicates as p
from verifier_gate.llm.handover import handover
from verifier_gate.verifier.certified import certified_plan

SAMPLE = 100
PAGE = Path(__file__).with_name("label_page.html")
SEED = 20261015
OUTCOME = ["caught", "caught at the change", "refuted", "undecidable", "number", "not covered", "failures"]
MENTIONS = {  # how texts name each feature (shown names); a sentence names a feature if its pattern matches
    "utilization": r"utili[sz]ation",
    "n_delinquencies": r"delinquen",
    "income": r"(?<!debt-to-)(?<!debt to )\bincomes?\b",
    "dti": r"debt[- ]to[- ]income|\bdti\b",
    "history_months": r"history",
    "age": r"\bages?\b|\bolder\b|\byounger\b",
    "n_inquiries": r"inquir|enquir",
    "months_at_address": r"address|residence",
    "num_dependents": r"dependent",
    "feature_a": r"feature[ _]a\b",
    "feature_b": r"feature[ _]b\b",
}


def blocks(text: str) -> tuple[str, list[dict]]:
    """The H1 text as its opening paragraph and its blocks: one per feature and one per pair, with their names."""
    head, _, rest = text.partition("\n\nFeatures, in the order")
    out, current = [], None
    for line in rest.splitlines()[1:]:
        m = re.match(r"- `([^`]+)`:", line)
        if m:
            current = {"names": [s.strip() for s in m.group(1).split("&")], "lines": [line[2:]]}
            out.append(current)
        elif line.startswith("  ") and current is not None:
            current["lines"].append(line.strip())
        elif line.strip():
            current = None
            out.append({"names": [], "lines": [line.strip().lstrip("- ")]})
    return head.strip(), out


def named(sentences: list[str], shown: list[str]) -> list[str]:
    text = " ".join(sentences).lower()
    return [f for f in shown if f in MENTIONS and re.search(MENTIONS[f], text)]


def build(out: Path) -> None:
    x3 = pd.read_csv(out.parent / "x3" / "llm.csv")
    changed = x3[(x3.role != "no mutation") & (x3.before.fillna("").str.strip() != x3.after.fillna("").str.strip())]
    pick = changed.iloc[np.random.default_rng(SEED).choice(len(changed), SAMPLE, replace=False)]
    texts = {t["run"]: t for t in e2_text.released_texts()}
    facts, items, key = {}, [], []
    for k, (_, row) in enumerate(pick.iterrows(), 1):
        t = texts[row.case]
        ctx_id = f"{t['scenario']}_{t['model']}_{t['naming']}"
        if ctx_id not in facts:
            scenario = next(s for s in dgp.SCENARIOS if s.id == t["scenario"])
            f = load(scenario, t["model"])
            head, parts = blocks(handover(f, dgp.generate(scenario).X, "H1", certified_plan(f), names=NAMINGS[t["naming"]]).text)
            facts[ctx_id] = {"head": head, "blocks": parts}
        shown = [n for b in facts[ctx_id]["blocks"] for n in b["names"] if len(b["names"]) == 1]
        before, after = str(row.before), str(row.after)
        sid = next(i for i, s in t["sentences"] if s.strip() == before.strip())
        items.append({"id": f"L{k:03d}", "facts": ctx_id, "named": named([before, after], shown), "changed": sid,
                      "before": before, "after": after, "sentences": [[i, after if i == sid else s] for i, s in t["sentences"]]})  # fmt: skip
        key.append({"item": f"L{k:03d}", "case": row.case, "scenario": t["scenario"], "model": t["model"], "naming": t["naming"],
                    "mutator role": row.role, "mutator claim": row.mutant} | {f"x3 {c}": row[c] for c in OUTCOME})  # fmt: skip
    out.mkdir(parents=True, exist_ok=True)
    (out / "items.json").write_text(json.dumps({"seed": SEED, "population": len(changed), "facts": facts, "items": items}, indent=1))
    pd.DataFrame(key).to_csv(out / "key.csv", index=False)
    page(out)
    print(f"{SAMPLE} of {len(changed)} changed sentences; {len(facts)} fact sets; mutator roles in the sample: "
          f"{pd.DataFrame(key)['mutator role'].value_counts().to_dict()}; written to {out}")  # fmt: skip


def page(out: Path) -> Path:
    """The labelling page with the items embedded (nothing from key.csv)."""
    data = json.dumps(json.loads((out / "items.json").read_text()), separators=(",", ":")).replace("</", "<\\/")
    path = out / "label_page.html"
    path.write_text(PAGE.read_text().replace("__DATA__", data))
    return path


def score(out: Path, labels_path: Path) -> pd.DataFrame:
    """labels.json: {item id: {"label": "error" | "ok" | "unsure", ...}} as read back from the page's store."""
    labels = {k: v["label"] for k, v in json.loads(labels_path.read_text()).items()}
    key = pd.read_csv(out / "key.csv")
    key["human"] = key["item"].map(labels)
    rows = []
    for path in sorted(out.parent.glob("x*/llm.csv")):
        version = path.parent.name
        gate = pd.read_csv(path).set_index("case")
        t = key[key.human.isin(["error", "ok"])].copy()
        t = t[t.case.isin(gate.index)]
        t["caught"] = t.case.map(gate["caught"]).astype(bool)
        t["at change"] = t.case.map(gate["caught at the change"]).astype(bool)
        err, ok = t[t.human == "error"], t[t.human == "ok"]
        rows.append({"extractor": version, "labelled": int(key.human.notna().sum()), "unsure": int((key.human == "unsure").sum()),
                     "errors": len(err), "recall": round(err.caught.mean(), 3), "recall at the change": round(err["at change"].mean(), 3),
                     "no error": len(ok), "false alarms": int(ok.caught.sum()), "false-alarm rate": round(ok.caught.mean(), 3),
                     "mutator agrees (error vs equivalent)": round(((t["mutator role"] == "error") == (t.human == "error"))[t["mutator role"].isin(["error", "equivalent"])].mean(), 3)})  # fmt: skip
    table = pd.DataFrame(rows)
    table.to_csv(out / "score.csv", index=False)
    return table


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--page", action="store_true", help="rebuild only the page from items.json")
    parser.add_argument("--score", type=Path)
    args = parser.parse_args()
    out = e2_text.RESULTS / p.load().version / "text" / "labels"
    if args.build:
        build(out)
    elif args.page:
        print(page(out))
    if args.score:
        print(score(out, args.score).to_string(index=False))


if __name__ == "__main__":
    main()
