"""Fig. 3: the gate's recall per mutation operator, plan level against text level (plan §8; E2, §14.11, §14.17,
§14.19, §14.23; D84: in D75's configuration).

One row per operator (e2_mutation.py, M1 to M11 without M10, which has almost no mutants under lexicon v3 and is not
labelled), and a last row for the LLM-written errors with author-reviewed labels. Recall is the share of errors not
released (D32). Plan level: the mutated claim goes straight to the verifier, under lexicon v3 with D74's fixes, pooled
over the synthetic tier (all three seeds) and the plasmode tier; it is 100% for every operator, drawn as a gray
reference mark. Text level: the template text with one clause changed and its plan unchanged, so only the round trip
can catch it, read by extractor x5 on the synthetic tier and on the plasmode tier (seed 1, D54; D78). M2 and M5
(ranks, shares) have no text-level row: the template texts do not state them. The LLM-written errors are the 100
labelled LLM mutants read by x5 (D78). Values below 99% are labelled; the numbers behind every mark are written to
paper/tables/fig3_recall.csv. E2 as run with x3 and x4 under v2 stays in results/e2/v2/ and in git. Colours:
categorical slots 2 and 3 of the dataviz palette (validated all-pairs, light); marker shapes repeat the encoding.

Run: `uv run python -m verifier_gate.experiments.fig3`. Writes paper/figures/fig3_recall.png and .pdf.
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from verifier_gate.experiments.fig2 import GRID, INK, MUTED, SURFACE  # noqa: E402

ROOT = Path(__file__).parents[3]
E2 = ROOT / "results" / "e2" / "v3-d74"
OUT = ROOT / "paper"
OPERATORS = {
    "M1": "direction flipped",
    "M2": "ranks swapped",
    "M3": "strength raised",
    "M4": "strength lowered",
    "M5": "share changed",
    "M6": "jump or peak moved",
    "M7": "interaction invented",
    "M8": "pattern swapped or pair left out",
    "M9": "feature the model lacks",
    "M11": "settled claim hedged",
}
LLM_ROW = "LLM-written errors (author-reviewed labels)"
TEXT = {  # condition: (script.csv, colour, marker)
    "text, synthetic, x5": (E2 / "text" / "x5" / "script.csv", "#2a78d6", "o"),
    "text, plasmode, x5": (E2 / "text_plasmode" / "x5" / "script.csv", "#1baf7a", "^"),
}
PLAN = (E2 / "plan_discovery", E2 / "plan_seeds-2-3", E2 / "plan_plasmode")
OFFSET = {"plan level": 0.25, "text, synthetic, x5": 0, "text, plasmode, x5": -0.25}  # sub-rows


def data() -> pd.DataFrame:
    rows = []
    plan = pd.concat([pd.read_csv(d / "by_operator.csv") for d in PLAN])
    for op in OPERATORS:
        part = plan[plan.operator == op]
        caught = int((part["caught: refuted"] + part["caught: undecidable"]).sum())
        rows.append({"row": op, "condition": "plan level", "errors": int(part.errors.sum()), "caught": caught})
    for condition, (path, *_) in TEXT.items():
        t = pd.read_csv(path)
        t = t[(t.role == "error") & (t.read == True)]  # noqa: E712
        for op, part in t.groupby("operator"):
            rows.append({"row": op, "condition": condition, "errors": len(part), "caught": int(part.caught.sum())})
    labelled = pd.read_csv(E2 / "text" / "x5" / "labelled_score.csv").set_index("labels").loc["final"]
    errors = int(labelled["errors"])
    rows.append({"row": LLM_ROW, "condition": "text, synthetic, x5", "errors": errors, "caught": round(float(labelled["recall"]) * errors)})
    out = pd.DataFrame(rows)
    out["recall"] = out.caught / out.errors
    return out


def draw(table: pd.DataFrame) -> plt.Figure:
    order = list(OPERATORS) + [LLM_ROW]
    labels = [f"{op}  {OPERATORS[op]}" for op in OPERATORS] + [LLM_ROW]
    fig, ax = plt.subplots(figsize=(7.2, 5.8), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    y = {row: len(order) - 1 - i for i, row in enumerate(order)}
    for x in (0, 0.25, 0.5, 0.75, 1.0):
        ax.axvline(x, color=GRID, lw=0.8, zorder=0)
    plan = table[table.condition == "plan level"]
    ax.scatter(plan.recall, [y[r] + OFFSET["plan level"] for r in plan.row], marker="D", s=34, facecolor="none", edgecolor=MUTED, lw=1.1, zorder=2)
    labelled = set()
    for condition, (_, colour, marker) in TEXT.items():
        part = table[table.condition == condition]
        ys = [y[r] + OFFSET[condition] for r in part.row]
        ax.scatter(part.recall, ys, marker=marker, s=40, color=colour, edgecolor=SURFACE, lw=0.8, zorder=3)
        for row, value, yy in zip(part.row, part.recall, ys):
            if value < 0.99 and (row, round(value, 3)) not in labelled:  # equal values in a row are labelled once
                labelled.add((row, round(value, 3)))
                ax.annotate(f"{value:.0%}" if value < 0.95 else f"{value:.1%}", (value, yy), xytext=(-7, 0), textcoords="offset points",
                            ha="right", va="center", fontsize=8, color=INK)  # fmt: skip
    ax.set_yticks([y[r] for r in order], labels, fontsize=8.5, color=INK)
    ax.set_xlim(-0.02, 1.04)
    ax.set_ylim(-0.6, len(order) - 0.4)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0], ["0%", "25%", "50%", "75%", "100%"], fontsize=8.5, color=MUTED)
    ax.set_xlabel("Recall: errors not released", fontsize=9, color=INK)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(axis="both", length=0)
    handles = [Line2D([], [], ls="", marker="D", markerfacecolor="none", markeredgecolor=MUTED, markersize=7, label="plan level (verifier only)")]
    handles += [Line2D([], [], ls="", marker=m, color=c, markersize=7, label=name) for name, (_, c, m) in TEXT.items()]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.42, 1.0), ncol=2, frameon=False, fontsize=8.5, labelcolor=INK)
    fig.tight_layout()
    return fig


def main() -> None:
    table = data()
    (OUT / "tables").mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT / "tables" / "fig3_recall.csv", index=False)
    fig = draw(table)
    for suffix in ("png", "pdf"):
        fig.savefig(OUT / "figures" / f"fig3_recall.{suffix}", dpi=200, facecolor=SURFACE, metadata={"CreationDate": None} if str(suffix).endswith("pdf") else None)
    print(json.dumps({r: round(v, 3) for r, v in table.groupby("condition").apply(lambda p: p.caught.sum() / p.errors.sum(), include_groups=False).items()}))
    print(f"written to {OUT / 'figures'} and {OUT / 'tables' / 'fig3_recall.csv'}")


if __name__ == "__main__":
    main()
