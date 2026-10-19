"""Fig. 4: faithfulness before and after the gate, by feature role and interaction level (plan §6 E3, §8; D36).

Faithfulness against M is the share of the claims a text states that are true of the fitted model; false and
undecidable claims are not (D30: never released as stated). Before the gate: the writer's first drafts; after: the
released texts (RELEASED, RELEASED_REDUCED, TEMPLATE). Claude Haiku 5.5 as writer, both namings and both models,
outside the two pilot datasets. What a text states is E3's own scoring readings (x3, replicas 3 to 5, a claim found by
two of three), rebuilt by experiments/e3_truth.py into results/e3/v3-x3/claims.csv. A claim counts for the role of
every feature it names (a comparison for both), a claim about a pair for "pairs", and a claim about a feature the
model does not have for that row. Roles as planted (data/dgp.FEATURE_ROLES). 95% intervals: percentile bootstrap
over the datasets of each interaction level (2,000 draws), the models pooled; an interval reaching below 70% ends in
an arrowhead at the axis.

The released texts are read by the same LLM readings as the drafts, so their misreadings count as false claims:
with author-reviewed labels, 32 of the 43 false claims in released texts are misreadings and 2 are real errors (§14.21), so the
values after the gate are a lower bound.

Run: `uv run python -m verifier_gate.experiments.fig4`. Writes paper/figures/fig4_faithfulness.png and .pdf and
paper/tables/fig4_faithfulness.csv.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from verifier_gate.data import dgp  # noqa: E402
from verifier_gate.dsl.parse import parse  # noqa: E402
from verifier_gate.experiments.fig2 import GRID, INK, MUTED, SURFACE  # noqa: E402

ROOT = Path(__file__).parents[3]
CLAIMS = ROOT / "results" / "e3" / "v3-x3" / "claims.csv"
OUT = ROOT / "paper"
ROLES = {  # role: row label
    "strong": "strong (utilization, delinquencies)",
    "moderate": "moderate (income)",
    "peak": "peak (credit history)",
    "threshold": "threshold (debt-to-income)",
    "weak": "weak (inquiries)",
    "near_flat": "near flat (age)",
    "noise": "no effect (two noise features)",
    "pair": "pairs",
    "not in the model": "a feature the model lacks",
}
LEVELS = ("none", "weak", "dominant")
BEFORE, AFTER = "#86b6ef", "#184f95"  # blue ramp steps 250 and 600 (dataviz palette; validated as an ordinal pair)
DRAWS = 2_000
SEED = 20261017
XMIN = 0.70


def roles(line: str) -> list[str]:
    claim = parse(line)
    inner = claim.inner if claim.kind == "unsettled" else claim
    if inner.kind == "interaction":
        return ["pair"]
    return ["pair" if " & " in t else dgp.FEATURE_ROLES.get(t, "not in the model") for t in inner.terms]


def claims() -> pd.DataFrame:
    c = pd.read_csv(CLAIMS)
    c = c[(c.writer == "haiku") & (~c["pilot dataset"])].copy()
    c["role"] = c.dsl.map(roles)
    c = c.explode("role")
    c["interaction"] = c.scenario.str.split("-").str[1]
    c["true"] = c["verdict M"] == "true"
    return c


def table(c: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    rows = []
    for level in LEVELS:
        part = c[c.interaction == level]
        scenarios = sorted(part.scenario.unique())
        counts = part.groupby(["scenario", "role", "arm"]).true.agg(["sum", "size"])
        draws = rng.integers(0, len(scenarios), size=(DRAWS, len(scenarios)))
        for (role, arm), cell in part.groupby(["role", "arm"]):
            per = counts.xs((role, arm), level=("role", "arm")).reindex(scenarios, fill_value=0)
            k, n = per["sum"].to_numpy(), per["size"].to_numpy()
            shares = k[draws].sum(axis=1) / np.maximum(n[draws].sum(axis=1), 1)
            lo, hi = np.quantile(shares[n[draws].sum(axis=1) > 0], [0.025, 0.975])
            rows.append({"interaction": level, "role": role, "arm": arm, "claims": len(cell), "true": int(cell.true.sum()),
                         "faithfulness": cell.true.mean(), "low": lo, "high": hi, "datasets": len(scenarios)})  # fmt: skip
    return pd.DataFrame(rows)


def draw(t: pd.DataFrame) -> plt.Figure:
    order = list(ROLES)
    y = {role: len(order) - 1 - i for i, role in enumerate(order)}
    fig, axes = plt.subplots(1, 3, figsize=(7.6, 4.4), sharey=True, facecolor=SURFACE)
    for ax, level in zip(axes, LEVELS):
        ax.set_facecolor(SURFACE)
        for x in (0.7, 0.8, 0.9, 1.0):
            ax.axvline(x, color=GRID, lw=0.8, zorder=0)
        part = t[t.interaction == level].set_index(["role", "arm"])
        for role in order:
            yy = y[role]
            before = part.loc[(role, "off")] if (role, "off") in part.index else None
            after = part.loc[(role, "on")] if (role, "on") in part.index else None
            if role == "not in the model":
                if before is not None:
                    note = f"{int(before.claims)} drafted, all false; none released" if after is None else ""
                    ax.text(XMIN + 0.005, yy, note, fontsize=7, color=MUTED, va="center")
                continue
            if before is not None and after is not None:
                ax.plot([before.faithfulness, after.faithfulness], [yy, yy], color=GRID, lw=2, zorder=1, solid_capstyle="round")
            for value, colour, filled, dy in ((before, BEFORE, False, 0.14), (after, AFTER, True, -0.14)):
                if value is None:
                    continue
                ax.plot([max(value.low, XMIN), value.high], [yy + dy, yy + dy], color=colour, lw=1.0, zorder=2)
                if value.low < XMIN:  # the interval continues below the axis: an arrowhead at the cut
                    ax.scatter([XMIN + 0.002], [yy + dy], marker="<", s=14, color=colour, zorder=2, clip_on=False)
                ax.scatter([value.faithfulness], [yy + dy], s=36, zorder=3, color=colour if filled else SURFACE, edgecolor=colour, lw=1.4)
        ax.set_title(f"interaction: {level}", fontsize=9, color=INK)
        ax.set_xlim(XMIN, 1.005)
        ax.set_xticks([0.7, 0.8, 0.9, 1.0], ["70%", "80%", "90%", "100%"], fontsize=8, color=MUTED)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(GRID)
        ax.tick_params(axis="both", length=0)
    axes[0].set_yticks([y[r] for r in order], [ROLES[r] for r in order], fontsize=8, color=INK)
    axes[0].set_ylim(-0.6, len(order) - 0.4)
    handles = [Line2D([], [], ls="", marker="o", markerfacecolor=SURFACE, markeredgecolor=BEFORE, markeredgewidth=1.4, markersize=6.5,
                      label="before the gate (first drafts)"),
               Line2D([], [], ls="", marker="o", color=AFTER, markersize=6.5, label="after the gate (released texts)")]  # fmt: skip
    fig.legend(handles=handles, loc="upper center", ncol=2, frameon=False, fontsize=8.5, labelcolor=INK, bbox_to_anchor=(0.6, 1.0))
    fig.tight_layout(rect=(0, 0.06, 1, 0.94))
    fig.subplots_adjust(wspace=0.3)
    left, bottom = axes[0].get_position().x0, axes[0].get_position().y0
    fig.text((left + axes[-1].get_position().x1) / 2, bottom - 0.07, "Faithfulness: share of stated claims true of the model",
             ha="center", va="top", fontsize=9, color=INK)  # fmt: skip
    return fig


def main() -> None:
    t = table(claims())
    (OUT / "tables").mkdir(parents=True, exist_ok=True)
    t.round(4).to_csv(OUT / "tables" / "fig4_faithfulness.csv", index=False)
    fig = draw(t)
    for suffix in ("png", "pdf"):
        fig.savefig(OUT / "figures" / f"fig4_faithfulness.{suffix}", dpi=200, facecolor=SURFACE, metadata={"CreationDate": None} if str(suffix).endswith("pdf") else None)
    low = t[t.role != "not in the model"].groupby("arm").faithfulness.agg(["min", "max"]).round(3)
    print(low.to_string())
    print(f"written to {OUT / 'figures'} and {OUT / 'tables' / 'fig4_faithfulness.csv'}")


if __name__ == "__main__":
    main()
