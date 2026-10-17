"""Fig. 1: the propose-and-prove loop as built (plan §5, §8; adapted from panel C of the thesis overview).

Seven steps left to right; grey fill: an LLM step; thick frame: the contribution (verifier, round trip, lexicon,
gate; plan §0). The lexicon feeds the verifier and the round trip; the gate sends failing claims back to the writer
with their evidence (at most two rounds, then the failing sentences are dropped or the template is released); the
released text's every claim is certified on M. The strip below names the two references the evaluation keeps
apart: the fitted model M (is the text faithful?) and the planted truth T (is it true?).

Run: `uv run python -m verifier_gate.experiments.fig1`. Writes paper/figures/fig1_loop.png and .pdf.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

from verifier_gate.experiments.fig2 import GRID, INK, MUTED, SURFACE  # noqa: E402

OUT = Path(__file__).parents[3] / "paper" / "figures"
LLM_FILL = "#e9e8e4"
STEPS = [  # title, body, LLM step, contribution
    ("1  Data", "planted truth T;\nsynthetic and\nplasmode tiers", False, False),
    ("2  Facts", "purified terms of\nthe model M, with\nbands from 100\nrefits", False, False),
    ("3  Handover", "facts in readable\nform, checked\nagainst M", False, False),
    ("4  Writer", "text and a claim\nplan in the DSL", True, False),
    ("5  Verifier", "each claim true,\nfalse or\nundecidable,\nwith evidence", False, True),
    ("6  Round trip", "text read back\nthree times; a\nclaim counts if\ntwo agree", True, True),
    ("7  Gate", "release, repair,\ndrop sentences,\nor template", False, True),
]
W, H, GAP, Y = 0.124, 0.3, 0.018, 0.47  # box width, height, gap, bottom (figure fractions)


def box(ax, x, y, w, h, fill, thick):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.004,rounding_size=0.012", fc=fill, ec=INK,
                                lw=1.8 if thick else 0.8, transform=ax.transAxes))  # fmt: skip


def arrow(ax, start, end, style="-|>", color=INK, lw=0.9, rad=0.0):
    ax.annotate("", xy=end, xytext=start, xycoords="axes fraction",
                arrowprops={"arrowstyle": style, "color": color, "lw": lw, "shrinkA": 0, "shrinkB": 0, "connectionstyle": f"arc3,rad={rad}"})  # fmt: skip


def draw() -> plt.Figure:
    fig = plt.figure(figsize=(7.2, 3.1), facecolor=SURFACE)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_facecolor(SURFACE)
    ax.set_axis_off()
    left = (1 - (len(STEPS) * W + (len(STEPS) - 1) * GAP)) / 2
    xs = [left + i * (W + GAP) for i in range(len(STEPS))]
    for x, (title, body, llm, new) in zip(xs, STEPS):
        box(ax, x, Y, W, H, LLM_FILL if llm else SURFACE, new)
        ax.text(x + 0.009, Y + H - 0.04, title, fontsize=7.2, fontweight="bold", color=INK, va="top", transform=ax.transAxes)
        ax.text(x + 0.009, Y + H - 0.115, body, fontsize=6.3, color=INK, va="top", linespacing=1.35, transform=ax.transAxes)
    mid = Y + H / 2
    for a, b in zip(xs, xs[1:]):
        arrow(ax, (a + W + 0.003, mid), (b - 0.003, mid))
    # the lexicon feeds the verifier and the round trip
    lx, lw_ = xs[4], xs[5] + W - xs[4]
    box(ax, lx, 0.13, lw_, 0.2, SURFACE, True)
    ax.text(lx + 0.009, 0.3, "Lexicon", fontsize=7.2, fontweight="bold", color=INK, va="top", transform=ax.transAxes)
    ax.text(lx + 0.009, 0.235, "a truth condition on the 95% band\nfor every word the text may use", fontsize=6.3, color=INK, va="top",
            linespacing=1.35, transform=ax.transAxes)  # fmt: skip
    for i in (4, 5):
        arrow(ax, (xs[i] + W / 2, 0.33), (xs[i] + W / 2, Y - 0.004))
    # repair loop: gate back to the writer, above the boxes
    top = Y + H
    arrow(ax, (xs[6] + W / 2, top + 0.004), (xs[3] + W / 2, top + 0.004), color=MUTED, lw=0.9, rad=0.25)
    ax.text((xs[3] + xs[6] + W) / 2, top + 0.175, "repair: failing claims go back with their evidence (at most two rounds)",
            fontsize=6.5, color=MUTED, ha="center", transform=ax.transAxes)  # fmt: skip
    # release
    rx = xs[6] + W / 2
    arrow(ax, (rx, Y - 0.004), (rx, 0.3))
    ax.text(rx, 0.28, "released text:\nevery claim\ncertified on M", fontsize=6.5, color=INK, ha="center", va="top", linespacing=1.3,
            transform=ax.transAxes)  # fmt: skip
    # the two references of the evaluation
    ax.plot([xs[0], xs[3] + W], [0.12, 0.12], color=GRID, lw=0.8, transform=ax.transAxes)
    ax.text(xs[0], 0.095, "Evaluation, two references kept apart: the fitted model M (is the text faithful? E2, E3)\n"
            "and the planted truth T (is it true? E1, E3)", fontsize=6.5, color=MUTED, va="top", linespacing=1.3, transform=ax.transAxes)  # fmt: skip
    ax.text(xs[0], 0.36, "grey: an LLM step\nthick frame: the contribution", fontsize=6.3, color=MUTED, va="top", linespacing=1.35,
            transform=ax.transAxes)  # fmt: skip
    return fig


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig = draw()
    for suffix in ("png", "pdf"):
        fig.savefig(OUT / f"fig1_loop.{suffix}", dpi=250, facecolor=SURFACE, bbox_inches="tight", pad_inches=0.04, metadata={"CreationDate": None} if str(suffix).endswith("pdf") else None)
    print(f"written to {OUT / 'fig1_loop.png'}")


if __name__ == "__main__":
    main()
