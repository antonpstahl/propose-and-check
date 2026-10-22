"""What the pre-study's live LLM calls cost, from the call log (cache/llm/calls/*.jsonl.gz and calls.jsonl, committed; D80).

The client logs every request, also those served from its cache (`cached` true). A request is paid once, so the
spend counts each request key once among the rows with `cached` false and a transport other than the stub (a batch
collected twice logs its answers twice, which a plain sum would count double). Self-hosted calls are logged at $0.

Writes results/spend.csv: requests and dollars by day, model, transport and role, and the total ($10.94 for the
pre-study). `--from` and `--to` (ISO times) total one window instead, without writing: e.g. what the self-hosted
writer's arm paid for its Haiku extractor calls, which its run traces do not record (results/README.md):
`--from 2026-10-17T13:00 --to 2026-10-17T17:00`.

Run: `uv run python -m verifier_gate.experiments.spend` (seconds, $0).
"""

import argparse
from pathlib import Path

import pandas as pd

from verifier_gate.llm.client import log_records

ROOT = Path(__file__).parents[3]
LOG = ROOT / "cache" / "llm" / "calls.jsonl"
OUT = ROOT / "results" / "spend.csv"


def paid() -> pd.DataFrame:
    """One row per paid request: its costliest live answer in the log (D81). A failed attempt costs nothing and a
    batch collected twice logs the same answer twice, so the costliest is the one paid; on a tie, the first."""
    first = {}
    for row in log_records(LOG.parent, LOG.name):  # the closed parts, then the open log (D80)
        if row["cached"] is False and row["transport"] != "stub" and row["cost"] > first.get(row["key"], {"cost": -1})["cost"]:
            first[row["key"]] = row
    frame = pd.DataFrame([{"time": r["time"], "model": r["model"], "transport": r["transport"],
                           "role": r["role"].split()[0], "cost": r["cost"]} for r in first.values()])  # fmt: skip
    frame["day"] = frame.time.str[:10]
    return frame


def summary(frame: pd.DataFrame) -> pd.DataFrame:
    table = frame.groupby(["day", "model", "transport", "role"]).cost.agg(requests="size", dollars="sum").reset_index()
    total = pd.DataFrame([{"day": "all", "model": "all", "transport": "all", "role": "all", "requests": len(frame), "dollars": frame.cost.sum()}])
    out = pd.concat([table, total], ignore_index=True)
    out["dollars"] = out.dollars.round(4)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="start", default="", help="ISO time: total the requests from here (no file written)")
    parser.add_argument("--to", dest="end", default="", help="ISO time: up to here")
    args = parser.parse_args()
    frame = paid()
    if args.start or args.end:
        window = frame[(frame.time >= (args.start or "0")) & (frame.time < (args.end or "9"))]
        print(window.groupby(["model", "transport", "role"]).cost.agg(requests="size", dollars="sum").round(4).to_string())
        print(f"{args.start or 'start'} to {args.end or 'end'}: {len(window)} requests, ${window.cost.sum():.4f}")
        return
    table = summary(frame)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT, index=False)
    print(table.to_string(index=False))
    print(f"all live calls: {len(frame)} requests, ${frame.cost.sum():.2f}; written to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
