"""Fig. 2: planted vs fitted main terms with the verifier's bands, all nine features, EBM and XGB2 overlaid.

One panel per feature (3 x 3). Each shows the planted term T (centred on the sample, as the fitted terms are),
the purified fitted terms of the EBM and of XGB2, and each model's simultaneous 95% band from the Poisson
refits: the band the lexicon judges direction, detectability and "negligible" on. Continuous features are drawn
between their 1st and 99th percentile as step curves. Count features are drawn as points at the whole numbers
that occur (the two models side by side, the band as a bar, T as a tick): their step curves would put T's steps
at .5 and XGB2's at whole numbers, which looks like a mismatch but agrees at every value that occurs (§14.4).
Titles give the share of importance of T, the EBM and XGB2. The pointwise band is left out: the verifier
does not use it (§5.3).

Run: `uv run python -m verifier_gate.experiments.fig2 [scenario id]` (default syn-dominant-n50000-s1).
Writes paper/figures/fig2_curves_<scenario>.png and .pdf.
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.legend_handler import HandlerTuple  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from verifier_gate.data import dgp  # noqa: E402
from verifier_gate.experiments.build_facts import load  # noqa: E402

FEATURES = ("utilization", "n_delinquencies", "income", "history_months", "dti", "n_inquiries", "age", "noise_1", "noise_2")
MODELS = {"EBM": "#2a78d6", "XGB2": "#eb6834"}  # categorical slots 1 and 2 (dataviz palette; validated light)
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
RANGE = (0.01, 0.99)
BAND_ALPHA = 0.16
DODGE = 0.14  # count features: the models' points left and right of the whole number
OUT = Path(__file__).parents[3] / "paper" / "figures"


def _at(cuts: np.ndarray, values: np.ndarray, x: np.ndarray) -> np.ndarray:
    """A step curve (values per step) read at x."""
    return values[..., np.searchsorted(cuts, x, side="right")]


def is_count(values) -> bool:
    return bool(np.all(values == np.round(values)))


def _continuous(ax, x, cuts, scores, band, color):
    ax.fill_between(x, *_at(cuts, band, x), color=color, alpha=BAND_ALPHA, lw=0, step="post")
    ax.plot(x, _at(cuts, scores, x), color=color, lw=1.3, drawstyle="steps-post", solid_joinstyle="round")


def _counts(ax, k, cuts, scores, band, color, offset):
    lower, upper = _at(cuts, band, k)
    ax.vlines(k + offset, lower, upper, color=color, alpha=0.55, lw=2.2)
    ax.plot(k + offset, _at(cuts, scores, k), "o", ms=5, color=color, mec=SURFACE, mew=0.8, zorder=3)


def draw(scenario: dgp.Scenario, out: Path = OUT, features: tuple[str, ...] = FEATURES, name: str = "") -> Path:
    """All nine features (Fig. 2), or a subset in one row (the worked example, experiments/worked_example.py)."""
    data = dgp.generate(scenario)
    planted = data.truth.shares(data.X)
    facts = {kind: load(scenario, kind, draws=False) for kind in MODELS}
    plt.rcParams.update({"font.size": 7.5, "axes.edgecolor": MUTED, "axes.labelcolor": MUTED, "xtick.color": MUTED,
                         "ytick.color": MUTED, "axes.titlecolor": INK, "axes.titlesize": 7.5,
                         "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6})  # fmt: skip
    rows = -(-len(features) // 3)
    fig, axes = plt.subplots(rows, 3, figsize=(7.2, 6.6 if rows == 3 else 2.2 * rows + 0.9), facecolor=SURFACE, squeeze=False)
    for ax, feature in zip(axes.flat, features):
        ax.set_facecolor(SURFACE)
        values = np.asarray(data.X[feature])
        lo, hi = np.quantile(values, RANGE)
        if is_count(values):
            k = np.arange(np.ceil(lo), np.floor(hi) + 1)
            for i, (kind, color) in enumerate(MODELS.items()):
                f = facts[kind].feature(feature)
                _counts(ax, k, f.cuts, f.scores, f.simultaneous, color, (2 * i - 1) * DODGE)
            ax.hlines(data.truth.term(feature, {feature: k}), k - 0.32, k + 0.32, color=INK, lw=1.3, zorder=4)
            ax.set_xticks(k)
        else:
            x = np.linspace(lo, hi, 2_000)
            for kind, color in MODELS.items():
                f = facts[kind].feature(feature)
                _continuous(ax, x, f.cuts, f.scores, f.simultaneous, color)
            ax.plot(x, data.truth.term(feature, {feature: x}), color=INK, lw=1.1, ls=(0, (4, 2)), zorder=4)
            if hi >= 10_000:
                ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v / 1000:.0f}k"))
        shares = " · ".join([f"T {planted[feature]:.1%}"] + [f"{k} {facts[k].feature(feature).share.value:.1%}" for k in MODELS])
        ax.set_title(f"{feature}\n{shares}", loc="left", pad=4)
        ax.axhline(0, color=GRID, lw=0.8, zorder=0)
        ax.tick_params(length=2.5, pad=2)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    for ax in axes[:, 0]:
        ax.set_ylabel("logit contribution")
    refits = facts["EBM"].bands["refits"]
    handles = [
        (Line2D([], [], color=INK, lw=1.1, ls=(0, (4, 2))), Line2D([], [], color=INK, lw=1.3)),
        *((Patch(color=c, alpha=BAND_ALPHA, lw=0), Line2D([], [], color=c, lw=1.3), Line2D([], [], marker="o", ms=5, color=c, mec=SURFACE, lw=0))
          for c in MODELS.values()),
    ]  # fmt: skip
    labels = ["planted T (counts: tick)", *(f"{k}, purified" for k in MODELS)]
    fig.legend(handles, labels, handler_map={tuple: HandlerTuple(ndivide=None, pad=0.3)}, loc="lower center",
               ncol=3, frameon=False, bbox_to_anchor=(0.5, 0.0), handlelength=3.2, fontsize=7.5)  # fmt: skip
    fig.suptitle(f"Planted vs fitted terms on {scenario.id}. Shading and bars: each model's simultaneous 95% band from "
                 f"{refits} Poisson refits,\nthe band the verifier uses. Titles: share of importance.",
                 x=0.01, ha="left", color=INK, fontsize=7.5, linespacing=1.4)  # fmt: skip
    if rows == 3:
        fig.tight_layout(rect=(0, 0.035, 1, 0.975), h_pad=1.2, w_pad=0.8)
    else:
        fig.tight_layout(rect=(0, 0.11, 1, 0.97), w_pad=0.8)
    out.mkdir(parents=True, exist_ok=True)
    path = out / (name or f"fig2_curves_{scenario.id}")
    for suffix in (".png", ".pdf"):
        fig.savefig(path.with_suffix(suffix), dpi=300, facecolor=SURFACE, metadata={"CreationDate": None} if str(suffix).endswith("pdf") else None)
    plt.close(fig)
    return path.with_suffix(".png")


def main() -> None:
    scenario_id = sys.argv[1] if len(sys.argv) > 1 else "syn-dominant-n50000-s1"
    scenario = next(s for s in dgp.SCENARIOS if s.id == scenario_id)
    print(draw(scenario))


if __name__ == "__main__":
    main()
