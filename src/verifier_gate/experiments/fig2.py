"""Fig. 2 (draft): planted vs fitted main terms with bootstrap bands, both models, one dataset.

Rows: EBM, XGB2. Columns: the six shaped features and one noise feature. Each panel shows the planted term T
(centred on the sample, as the fitted terms are; for count features at whole numbers only), the purified fitted term M, its pointwise 95% band and its
simultaneous 95% band, between the 1st and 99th percentile of the feature. Titles give M's share with its
band and T's share. Reads the cached facts (experiments/build_facts.py).

Run: `uv run python -m verifier_gate.experiments.fig2 [scenario id]` (default syn-dominant-n50000-s1).
Writes paper/figures/fig2_curves_<scenario>.png and .pdf.
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from verifier_gate.data import dgp  # noqa: E402
from verifier_gate.experiments.build_facts import load  # noqa: E402

FEATURES = ("utilization", "n_delinquencies", "income", "history_months", "dti", "n_inquiries", "noise_1")
MODELS = {"EBM": "#2a78d6", "XGB2": "#eb6834"}  # categorical slots 1 and 2, validated (dataviz palette)
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
RANGE = (0.01, 0.99)
OUT = Path(__file__).parents[3] / "paper" / "figures"


def _on_grid(cuts: np.ndarray, values: np.ndarray, grid: np.ndarray) -> np.ndarray:
    return values[..., np.searchsorted(cuts, grid, side="right")]


def draw(scenario: dgp.Scenario, out: Path = OUT) -> Path:
    data = dgp.generate(scenario)
    shares = data.truth.shares(data.X)
    plt.rcParams.update({"font.size": 8, "axes.edgecolor": MUTED, "axes.labelcolor": MUTED, "xtick.color": MUTED,
                         "ytick.color": MUTED, "axes.titlecolor": INK, "axes.titlesize": 8})  # fmt: skip
    fig, axes = plt.subplots(len(MODELS), len(FEATURES), figsize=(14, 4.4), sharex="col", sharey="col", facecolor=SURFACE)
    for row, (kind, color) in enumerate(MODELS.items()):
        facts = load(scenario, kind, draws=False)
        for col, name in enumerate(FEATURES):
            ax = axes[row, col]
            ax.set_facecolor(SURFACE)
            feature = facts.feature(name)
            grid = np.linspace(*np.quantile(data.X[name], RANGE), 2_000)
            simultaneous = _on_grid(feature.cuts, feature.simultaneous, grid)
            pointwise = _on_grid(feature.cuts, feature.pointwise, grid)
            ax.fill_between(grid, *simultaneous, color=color, alpha=0.16, lw=0, step="post")
            ax.fill_between(grid, *pointwise, color=color, alpha=0.32, lw=0, step="post")
            ax.plot(grid, _on_grid(feature.cuts, feature.scores, grid), color=color, lw=1.2, drawstyle="steps-post")
            counts = np.all(data.X[name] == np.round(data.X[name]))  # count feature: T only at whole numbers
            planted_at = np.round(grid) if counts else grid
            ax.plot(grid, data.truth.term(name, {name: planted_at}), color=INK, lw=1.2, ls=(0, (4, 2)))
            if grid[-1] >= 10_000:
                ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v / 1000:.0f}k"))
            ax.axhline(0, color=GRID, lw=0.8, zorder=0)
            lo, hi = feature.share.band
            ax.set_title(f"{name}\n{feature.share.value:.1%} [{lo:.1%}, {hi:.1%}], T {shares[name]:.1%}", loc="left")
            ax.grid(False)
            for side in ("top", "right"):
                ax.spines[side].set_visible(False)
        axes[row, 0].set_ylabel(f"{kind}\nlogit contribution", color=INK)
    handles = [
        Line2D([], [], color=INK, lw=1.2, ls=(0, (4, 2)), label="planted T"),
        *(Line2D([], [], color=c, lw=1.2, label=f"{k} fitted (purified)") for k, c in MODELS.items()),
        Patch(color=MUTED, alpha=0.32, label="pointwise 95% band"),
        Patch(color=MUTED, alpha=0.16, label="simultaneous 95% band"),
    ]
    refits = facts.bands["refits"]
    fig.legend(handles=handles, loc="lower center", ncol=len(handles), frameon=False, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle(f"{scenario.id}: planted vs fitted terms, bands from {refits} Poisson refits; "
                 "titles: share of importance [95% band], planted share", x=0.01, ha="left", color=INK, fontsize=9)  # fmt: skip
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"fig2_curves_{scenario.id}"
    for suffix in (".png", ".pdf"):
        fig.savefig(path.with_suffix(suffix), dpi=200, facecolor=SURFACE)
    plt.close(fig)
    return path.with_suffix(".png")


def main() -> None:
    scenario_id = sys.argv[1] if len(sys.argv) > 1 else "syn-dominant-n50000-s1"
    scenario = next(s for s in dgp.SCENARIOS if s.id == scenario_id)
    print(draw(scenario))


if __name__ == "__main__":
    main()
