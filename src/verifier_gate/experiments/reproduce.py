"""One command that reproduces every number of the working paper from the repository (plan §13), without network.

Inputs, as committed: the code, the frozen prompts and lexicon, the LLM cache (cache/llm: every answer as received),
E3's run traces (results/e3/v3-x3/*/runs: the record of what was paid; E3 ran with extractor x3, which the current
code reads from git where it needs it), and the labels (results/e2/v2/text/labels, .../false_alarms, and the blind
labels in results/e3/v4-x5-m5-d74/blind/labels). Not committed:
the Facts and refits in cache/facts and the TaiwanCredit file in data/raw. Unpacked from the Facts archive
(experiments/facts_archive.py), they make the run offline; otherwise the first steps refit every model from the fixed
seeds (about six hours) and download TaiwanCredit from UCI.

Lexicon versions (D63-D66): every step replays a result run under lexicon v2, with VERIFIER_GATE_LEXICON=v2 set (the
writer's prompts v3, extractor x3 or x4, the template's v2 wording), except the steps in V3_STEPS, which run under
the current lexicon, v3. Of these, the steps in BEFORE_D74 replay results that ran before D74's fixes (E1 under v3,
D66, D67), with VERIFIER_GATE_D74=0; the *-d74 steps make the reruns with them (results/e1/v3-d74, results/e2/v3-d74,
results/e3/v4-x5-m5-d74, results/local/plasmode/run/l2-d74) and the check behind D74 (results/snap_check).

Every step runs with VERIFIER_GATE_OFFLINE set: a request that is not in the LLM cache raises instead of calling the
API, so a reproduction costs $0 or stops. At the end, `git status` over results/ and paper/ lists every output that
differs from the committed one; none should. Differences that are not results are handled: a file that differs only in
bookkeeping is restored, so the record of the run stays: `spent` (what an execution paid: $0 on a rerun from the cache),
the date a replay read its answers (`read`, e2_heldout), and round-trip fields the code writes since a run was made
(ADDED_SINCE: `hedged`, since 21 Oct, absent from E3's first run); a PDF whose PNG is unchanged differs only in
metadata (PDFs written before 17 Oct carry a creation date).

Run: `uv run python -m verifier_gate.experiments.reproduce` (30 steps, about seven minutes with the Facts on disk).
Options: --list, --only <step names, comma-separated>, --from <step name>.
"""

import argparse
import io
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

from verifier_gate.lexicon.predicates import D74, PIN
from verifier_gate.llm.client import OFFLINE

REPO = Path(__file__).parents[3]
LABELS = "results/e2/v2/text/false_alarms/labels.json"
DRAFT_LABELS = "results/e2/v2/text/false_alarms/drafts/labels.json"
CRITIC_LABELS = "results/e2/v2/text/critic/gpt-6-luna/c1/labels/labels.json"
BLIND_LABELS = "results/e3/v4-x5-m5-d74/blind/labels"  # one file per rater, read back from the page's store (D82)
V3_STEPS = {"e1-v3-discovery", "e1-v3-confirmation", "e1-v3-plasmode", "table1-v3", "e3-rerun", "e3-rerun-truth", "e3-text-error",
             "local-refits-plasmode", "local-facts-plasmode", "local-run-plasmode",
             "e1-d74-discovery", "e1-d74-confirmation", "e1-d74-plasmode", "snap-check", "e2-plan-d74-discovery",
             "e2-plan-d74-confirmation", "e2-plan-d74-plasmode", "e3-rerun-d74", "e3-rerun-d74-truth",
             "local-run-plasmode-d74", "e2-text-x5", "e2-text-x5-plasmode", "e2-text-x5-labelled", "e3-baselines-d74", "e3-independent-d74", "e2-critic-c3",
             "e3-blind-score", "deferred", "fig4"}  # under lexicon v3 (D63-D67, D74); every other step replays a result run under v2 (PIN=v2)
BEFORE_D74 = {"e1-v3-discovery", "e1-v3-confirmation", "e1-v3-plasmode", "e3-rerun", "e3-rerun-truth", "local-run-plasmode"}  # v3, as run before D74's fixes
STEPS = [  # name, module, arguments
    ("facts", "build_facts", []),
    ("facts-plasmode", "build_facts", ["--tier", "plasmode"]),
    ("e1-discovery", "e1_lexicon", []),
    ("e1-confirmation", "e1_lexicon", ["--seeds", "2,3"]),
    ("e1-plasmode", "e1_lexicon", ["--tier", "plasmode"]),
    ("e1-v3-discovery", "e1_lexicon", []),  # lexicon v3 (D63, D64): results/e1/v3/
    ("e1-v3-confirmation", "e1_lexicon", ["--seeds", "2,3"]),
    ("e1-v3-plasmode", "e1_lexicon", ["--tier", "plasmode"]),
    ("e1-d74-discovery", "e1_lexicon", []),  # lexicon v3 with D74's fixes: results/e1/v3-d74/
    ("e1-d74-confirmation", "e1_lexicon", ["--seeds", "2,3"]),
    ("e1-d74-plasmode", "e1_lexicon", ["--tier", "plasmode"]),
    ("snap-check", "snap_check", []),  # the check behind D74: what the location snap changes, $0
    ("e2-plan-discovery", "e2_mutation", []),
    ("e2-plan-confirmation", "e2_mutation", ["--seeds", "2,3"]),
    ("e2-plan-plasmode", "e2_mutation", ["--tier", "plasmode"]),
    ("e2-plan-d74-discovery", "e2_mutation", []),  # plan-level E2 under v3 with D74's fixes: results/e2/v3-d74/
    ("e2-plan-d74-confirmation", "e2_mutation", ["--seeds", "2,3"]),
    ("e2-plan-d74-plasmode", "e2_mutation", ["--tier", "plasmode"]),
    ("e2-text-script", "e2_text", ["--script"]),  # the two sources as they were run, so each CSV keeps its own columns
    ("e2-text-llm", "e2_text", ["--llm"]),
    ("e2-text-plasmode", "e2_text", ["--tier", "plasmode", "--seeds", "1"]),
    ("e2-text-compare", "e2_text", ["--compare"]),
    ("e2-heldout", "e2_heldout", []),  # the held-out invented features, read as built: lexicon v2, extractor x4 (D76)
    ("e2-text-x5", "e2_text", ["--script"]),  # E2 at text level in D75's configuration (D78): results/e2/v3-d74/
    ("e2-text-x5-plasmode", "e2_text", ["--tier", "plasmode", "--seeds", "1"]),
    ("e2-text-x5-labelled", "e2_text", ["--labelled"]),  # the 100 labelled LLM mutants read by x5 (D78)
    ("e3-haiku", "e3_end_to_end", []),  # E3 as run (extractor x3 pinned), every call from the cache
    ("e3-sonnet", "e3_end_to_end", ["--sonnet"]),
    ("e3-qwen", "e3_end_to_end", ["--writer", "ollama/qwen3.8:27b"]),  # the self-hosted writer subset (D55), every call from the cache ($0)
    ("e3-check-and-truth", "e3_truth", []),
    ("e3-rerun", "e3_end_to_end", ["--revised", "--tier", "both"]),  # the rerun on both tiers (D66), every call from the cache
    ("e3-rerun-truth", "e3_truth", ["--source", "v4-x5-m5"]),
    ("e3-rerun-d74", "e3_end_to_end", ["--revised", "--tier", "both"]),  # the rerun with D74's fixes, every call from the cache
    ("e3-rerun-d74-truth", "e3_truth", ["--source", "v4-x5-m5-d74"]),
    ("e3-text-error", "e3_text_error", []),  # the text-level error against T by claim form, as run and rerun
    ("e3-baselines-d74", "e3_baselines", ["--source", "v4-x5-m5-d74"]),  # the baselines beside D74 (D76), from texts.json and the cache
    ("e3-baselines", "e3_baselines", []),  # the template-only and plain-prompt arms (D71), scored as E3, from texts.json and the cache
    ("false-alarms", "e2_false_alarms", ["--score", LABELS]),
    ("e3-residual", "e2_false_alarms", ["--e3", LABELS]),
    ("e3-effect", "e2_false_alarms", ["--effect", LABELS, DRAFT_LABELS]),
    ("e3-independent-d74", "e3_independent", ["--source", "v4-x5-m5-d74", "--tables"]),  # Luna reading D74 (D76), from the cache
    ("e3-independent", "e3_independent", ["--tables"]),  # E3 read by GPT-6 Luna, the release rule (D69), every call from the cache
    ("e2-critic", "e2_critic", ["--critic", "c1"]),  # the LLM critic (D56), every call from the cache
    ("e2-critic-sol", "e2_critic", ["--critic", "c1", "--model", "openai/gpt-6.1-sol", "--sources", "llm,control"]),
    ("e2-critic-e3-labels", "e2_critic", ["--critic", "c1", "--score", CRITIC_LABELS]),  # the author's labels of Luna's E3 flags
    ("e2-critic-c2", "e2_critic", ["--critic", "c2"]),  # the critic with the writer's inputs (D72), every call from the cache
    ("e2-critic-compare", "e2_critic", ["--compare"]),
    ("e2-critic-c3", "e2_critic", ["--critic", "c3"]),  # c3 in D75's configuration (D79), every call from the cache  # c2 beside c1 and the gate
    ("e3-blind-score", "e3_blind", ["--source", "v4-x5-m5-d74", "--score", BLIND_LABELS]),  # the blind labels of B01-B40 (D82, D83), $0
    ("deferred", "deferred", []),  # the sizes of the defects D75 deferred, on D74's traces and the LLM cache (D85), $0
    ("local-refits", "local_refits", []),
    ("local-facts", "local_facts", []),
    ("local-pilot", "local_run", ["--pilot"]),
    ("local-run", "local_run", []),
    ("local-refits-plasmode", "local_refits", ["--tier", "plasmode"]),  # the spot check on the plasmode tier (D67)
    ("local-facts-plasmode", "local_facts", ["--tier", "plasmode"]),
    ("local-run-plasmode", "local_run", ["--tier", "plasmode"]),
    ("local-run-plasmode-d74", "local_run", ["--tier", "plasmode"]),  # the plasmode notices with D74's fixes
    ("fig1", "fig1", []),
    ("fig2", "fig2", []),
    ("fig3", "fig3", []),
    ("fig4", "fig4", []),
    ("tables", "tables", []),
    ("table1-v3", "tables", ["--only", "tab1"]),  # Tab. 1 from lexicon v3 (D65): tab1_dsl_lexicon_v3
    ("worked-example", "worked_example", []),
    ("spend", "spend", []),  # what the live calls cost, from the call log
]


def committed(path: str) -> str:
    return subprocess.run(["git", "show", f"HEAD:{path}"], cwd=REPO, capture_output=True, text=True, check=True).stdout


ADDED_SINCE = {"hedged"}  # round-trip fields the code writes since c07a64e9 (21 Oct, D68), absent from traces written before
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def _bookkeeping(old: dict, new: dict) -> tuple[dict, dict]:
    """Both versions without what a replay changes and no result depends on: what the execution paid (`spent`), the
    date a replay read its answers (`read`, e2_heldout), and round-trip fields added after the run was made."""
    drop = lambda d: {k: v for k, v in d.items() if k != "spent" and not (k == "read" and isinstance(v, str) and DATE.fullmatch(v))}  # noqa: E731
    old, new = drop(old), drop(new)
    if isinstance(old.get("versions"), list) and isinstance(new.get("versions"), list) and len(old["versions"]) == len(new["versions"]):
        versions = []
        for o, n in zip(old["versions"], new["versions"]):
            trip_o, trip_n = (o or {}).get("roundtrip"), (n or {}).get("roundtrip")
            if isinstance(trip_o, dict) and isinstance(trip_n, dict):
                n = {**n, "roundtrip": {k: v for k, v in trip_n.items() if k in trip_o or k not in ADDED_SINCE}}
            versions.append(n)
        new = {**new, "versions": versions}
    return old, new


def only_spent(path: str) -> bool:
    """The file equals its committed version apart from bookkeeping (_bookkeeping): what the execution paid, a
    replay's date, round-trip fields added after the run."""
    if path.endswith(".json"):
        old, new = json.loads(committed(path)), json.loads((REPO / path).read_text())
        if not (isinstance(old, dict) and isinstance(new, dict)):
            return False
        old, new = _bookkeeping(old, new)
        return old == new
    if path.endswith(".csv"):
        old, new = pd.read_csv(io.StringIO(committed(path))), pd.read_csv(REPO / path)
        cols = [c for c in old.columns if c != "spent"]
        return "spent" in old.columns and list(old.columns) == list(new.columns) and old[cols].equals(new[cols])
    return False


def changed() -> list[str]:
    out = subprocess.run(["git", "status", "--porcelain", "--", "results", "paper"], cwd=REPO, capture_output=True, text=True, check=True)
    return [line for line in out.stdout.splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true", help="print the steps and stop")
    parser.add_argument("--only", default="", help="comma-separated step names")
    parser.add_argument("--from", dest="start", default="", help="start at this step")
    args = parser.parse_args()
    names = [name for name, *_ in STEPS]
    if args.list:
        print("\n".join(f"{name}: python -m verifier_gate.experiments.{module} {' '.join(a)}" for name, module, a in STEPS))
        return
    steps = STEPS
    if args.only:
        wanted = args.only.split(",")
        unknown = set(wanted) - set(names)
        if unknown:
            raise SystemExit(f"unknown steps: {sorted(unknown)}")
        steps = [s for s in STEPS if s[0] in wanted]
    elif args.start:
        steps = STEPS[names.index(args.start):]
    before = set(changed())
    env = {**os.environ, OFFLINE: "1"}
    start = time.perf_counter()
    for name, module, arguments in steps:
        t0 = time.perf_counter()
        print(f"[{name}] python -m verifier_gate.experiments.{module} {' '.join(arguments)}", flush=True)
        pinned = {**env, D74: "0"} if name in BEFORE_D74 else env if name in V3_STEPS else {**env, PIN: "v2"}
        result = subprocess.run([sys.executable, "-m", f"verifier_gate.experiments.{module}", *arguments], cwd=REPO, env=pinned,
                                capture_output=True, text=True)  # fmt: skip
        if result.returncode != 0:
            print(result.stdout[-2000:], result.stderr[-4000:], sep="\n")
            raise SystemExit(f"[{name}] failed after {time.perf_counter() - t0:.0f}s")
        print(f"[{name}] done in {time.perf_counter() - t0:.0f}s", flush=True)
    after = [line for line in changed() if line not in before]
    print(f"\n{len(steps)} steps in {(time.perf_counter() - start) / 60:.1f} min, no API call")
    restored = [line for line in after if line.startswith(" M") and only_spent(line[3:])]
    for line in restored:
        subprocess.run(["git", "checkout", "--", line[3:]], cwd=REPO, check=True)
    pngs = {line[3:] for line in changed()}
    metadata = [line for line in after if line[3:].endswith(".pdf") and line[3:].replace(".pdf", ".png") not in pngs]
    after = [line for line in after if line not in restored and line not in metadata]
    if restored:
        print(f"{len(restored)} file(s) differed only in bookkeeping ('spent', paid by the original run and $0 now; a replay's date; round-trip fields added since) and were restored")
    if metadata:
        print(f"{len(metadata)} PDF(s) differ only in metadata (their PNGs are unchanged): " + ", ".join(m[3:] for m in metadata))
    modified, new = [x for x in after if not x.startswith("??")], [x for x in after if x.startswith("??")]
    if new:
        print("new outputs, not in the commit (commit them or remove them):\n" + "\n".join(new))
    if modified:
        print("outputs that differ from the committed ones:\n" + "\n".join(modified))
    if after:
        raise SystemExit(1)
    print("every output under results/ and paper/ equals the committed one" + (" (files already changed before the run were not checked)" if before else ""))


if __name__ == "__main__":
    main()
