"""Tabs. 1-4 of the working paper (plan §8), each from its source of truth, as Markdown and CSV in paper/tables/.

- Tab. 1, DSL and lexicon: the claim forms and the words they stand for, from the writers' own DSL tables
  (llm/prompts/system.md, system_local.md), and the lexicon's thresholds (lexicon/lexicon.yaml).
- Tab. 2, the benchmark: per tier the features, their planted role, shape and target share, and the pairs with their
  shares by interaction level (data/dgp.py, data/plasmode.py). The synthetic distributions and shapes are written as
  coded in dgp.sample_features and dgp.MAIN_SHAPES (frozen with the DGP, D11).
- Tab. 3, E1 by tier (D31): decided rate, accuracy among decided and confident-error rate per layer, model and
  sample size; the synthetic tier pooled over its three seeds (discovery and confirmation, recomputed from the
  counts, not averaged), the plasmode tier over its three seeds.
- Tab. 4, survival, control effectiveness and cost (D36): per writer, outside the pilot datasets: exit states,
  repair rounds, P_U before and after the gate and E_U, as run and with human labels where they exist (§14.21), and
  the cost per run; the local spot check (§14.22) as its own row.

Each table is also written as a LaTeX tabular (booktabs) for paper/main.tex, which inputs it: no number of the paper is
typed by hand.

Run: `uv run python -m verifier_gate.experiments.tables`.
"""

from pathlib import Path

import re

import pandas as pd
import yaml

from verifier_gate.data import dgp, plasmode
from verifier_gate.llm import prompts

ROOT = Path(__file__).parents[3]
OUT = ROOT / "paper" / "tables"
RESULTS = ROOT / "results"
SYNTHETIC_DISTRIBUTIONS = {  # dgp.sample_features
    "utilization": "Beta(2, 3)", "n_delinquencies": "min(Poisson(0.8), 6)", "income": "lognormal, median 50,000, σ 0.5",
    "history_months": "uniform 6 to 360", "dti": "uniform 0 to 0.6", "n_inquiries": "Poisson(1.5)",
    "age": "uniform 21 to 75", "noise_1": "N(0, 1)", "noise_2": "N(0, 1)",
}  # fmt: skip
SYNTHETIC_SHAPES = {  # dgp.MAIN_SHAPES
    "utilization": "increasing, steeper above 0.6", "n_delinquencies": "increasing, saturating",
    "income": "decreasing (−log income)", "history_months": "decreasing, with a bump at 36 months (rising on 7% of the data)",
    "dti": "a step up at 0.43", "n_inquiries": "increasing (linear)", "age": "decreasing (linear)",
    "noise_1": "zero", "noise_2": "zero",
}  # fmt: skip
PLASMODE_SHAPES = {  # data/plasmode.py, docstring table
    "PAY_0": "the real-label EBM's, per status value", "LIMIT_BAL": "decreasing, smooth", "BILL_AMT1": "increasing, smooth",
    "PAY_AMT1": "decreasing, smooth", "PAY_AMT2": "a step down at 2,000", "AGE": "increasing, smooth",
    "EDUCATION": "linear in the code, clipped to 1 to 3", "BILL_AMT2": "zero; Spearman 0.91 with BILL_AMT1",
    "PAY_AMT3": "zero",
}  # fmt: skip


def markdown(df: pd.DataFrame) -> str:
    cells = [[str(v) for v in row] for row in df.itertuples(index=False)]
    lines = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    return "\n".join(lines + ["| " + " | ".join(r) + " |" for r in cells]) + "\n"


def _tex(text: str) -> str:
    """Plain text for LaTeX; `code` spans become \texttt."""

    def escape(s: str) -> str:
        s = s.replace("\\", r"\textbackslash{}")
        for ch in "&%$#_{}":
            s = s.replace(ch, "\\" + ch)
        return s.replace("~", r"\textasciitilde{}").replace("^", r"\textasciicircum{}")

    def prose(s: str) -> str:  # curly quotes; P_U and E_U as math
        s = re.sub(r'"([^"]*)"', "\u201c\\1\u201d", escape(s))
        return s.replace(r"P\_U", r"$P_U$").replace(r"E\_U", r"$E_U$")

    parts = re.split(r"`([^`]*)`", str(text))
    return "".join(prose(p) if i % 2 == 0 else r"\texttt{" + escape(p) + "}" for i, p in enumerate(parts))


def latex(df: pd.DataFrame, spec: str) -> str:
    rows = [" & ".join(_tex(v) for v in row) + r" \\" for row in df.itertuples(index=False)]
    head = " & ".join(r"\textbf{" + _tex(c) + "}" for c in df.columns) + r" \\"
    return "\n".join([rf"\begin{{tabular}}{{{spec}}}", r"\toprule", head, r"\midrule", *rows, r"\bottomrule", r"\end{tabular}"]) + "\n"


def write(name: str, title: str, parts: list[tuple[str, pd.DataFrame]], note: str = "", specs: list[str] | None = None) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    text = f"# {title}\n\n" + "\n".join((f"**{caption}**\n\n" if caption else "") + markdown(df) for caption, df in parts)
    (OUT / f"{name}.md").write_text(text + (f"\n{note}\n" if note else ""))
    for k, (_, df) in enumerate(parts):
        stem = f"{name}{'' if len(parts) == 1 else f'_{k + 1}'}"
        df.to_csv(OUT / f"{stem}.csv", index=False)
        (OUT / f"{stem}.tex").write_text(latex(df, specs[k] if specs else "l" * len(df.columns)))


def dsl_rows(source: str) -> pd.DataFrame:
    rows = []
    for line in prompts.dsl_reference(source).splitlines()[2:]:
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) == 3:
            rows.append({"Words in the text": cells[0], "DSL claim": cells[1], "Meaning (judged on the whole 95% band)": cells[2]})
    return pd.DataFrame(rows)


def tab1() -> None:
    lex = yaml.safe_load((ROOT / "src" / "verifier_gate" / "lexicon" / "lexicon.yaml").read_text())
    thresholds = pd.DataFrame([
        {"Threshold": "strength classes (share of importance)", "Value": f"negligible < {lex['strength']['weak']:.0%} ≤ weak < {lex['strength']['moderate']:.0%} ≤ moderate < {lex['strength']['strong']:.0%} ≤ strong"},
        {"Threshold": "detectable effect", "Value": f"simultaneous band excludes 0 on more than {lex['detectable_mass']:.0%} of the data, or a significant net change"},
        {"Threshold": "\"about x%\"", "Value": f"within {lex['share']['absolute']:.0%} points or {lex['share']['relative']:.0%} of the share"},
        {"Threshold": "\"mostly\" (exception mass)", "Value": f"a detected reversal on at most {lex['direction']['exception_mass']:.0%} of the data"},
        {"Threshold": "jump / peak location (window w)", "Value": f"{lex['location']['window']:.0%} of the 5th-95th percentile range; on counts, the gap between observed values (v2)"},
        {"Threshold": "jump size", "Value": f"at least {lex['location']['jump_fraction']:.0%} of the term's range, significant"},
        {"Threshold": "interaction present", "Value": f"pair share band at or above {lex['interaction']['pair_share']:.0%} and a significant interaction contrast"},
        {"Threshold": "band level", "Value": f"{lex['level']:.0%}, from 100 Poisson bootstrap refits; curves: simultaneous (sup-t) bands"},
    ])  # fmt: skip
    write("tab1_dsl_lexicon", f"Tab. 1: the DSL and the lexicon (lexicon {lex['version']}, frozen)",
          [("Claims about the model (global)", dsl_rows("system")), ("Claims about one declined applicant (local spot check)", dsl_rows("system_local")),
           ("The lexicon's thresholds", thresholds)],
          "A claim is true if the whole band lies inside the set its word names, false if it lies outside, undecidable otherwise; "
          "undecidable claims are never released as stated (D30).",
          ["p{3.3cm}p{5.1cm}p{6.4cm}", "p{3.3cm}p{4.5cm}p{7cm}", "p{4.2cm}p{10.8cm}"])  # fmt: skip


def tab2() -> None:
    syn = pd.DataFrame([{"Feature": f, "Role": dgp.FEATURE_ROLES[f].replace("_", " "), "Distribution": SYNTHETIC_DISTRIBUTIONS[f],
                         "Planted shape": SYNTHETIC_SHAPES[f], "Share (no interaction)": f"{dgp.MAIN_SHARES[f]:.0%}"} for f in dgp.FEATURES])  # fmt: skip
    pls = pd.DataFrame([{"Feature": f, "Role": plasmode.FEATURE_ROLES[f].replace("_", " "), "Planted shape": PLASMODE_SHAPES[f],
                         "Share (no interaction)": f"{plasmode.MAIN_SHARES[f]:.0%}"} for f in plasmode.FEATURES])  # fmt: skip
    pairs = pd.DataFrame([{"Tier": tier, "Pair": pair, "Pattern": patterns[pair].replace("_", " "),
                           **{f"Share, {level}": f"{shares[level][pair]:.0%}" for level in dgp.INTERACTION_LEVELS}}
                          for tier, patterns, shares in (("synthetic", dgp.PAIR_PATTERNS, dgp.PAIR_SHARES), ("plasmode", plasmode.PAIR_PATTERNS, plasmode.PAIR_SHARES))
                          for pair in patterns])  # fmt: skip
    write("tab2_benchmark", "Tab. 2: the benchmark, synthetic and plasmode tiers",
          [(f"Synthetic tier: n = {', '.join(f'{n:,}' for n in dgp.SAMPLE_SIZES)}; seeds {', '.join(map(str, dgp.SEEDS))}; base rate {dgp.BASE_RATE:.0%}", syn),
           (f"Plasmode tier: TaiwanCredit features (UCI 350), planted outcome; n = {', '.join(f'{n:,}' for n in plasmode.SAMPLE_SIZES)}; seeds {', '.join(map(str, plasmode.SEEDS))}", pls),
           ("Planted pairs (pairs take their share from the total; main terms keep their coefficients)", pairs)],
          "18 datasets per tier: 3 interaction levels × 2 sample sizes × 3 seeds. EBM and XGB2 are fitted on each (36 models per tier).",
          ["llp{3.4cm}p{4.6cm}r", "llp{7cm}r", "lllrrr"])  # fmt: skip


def tab3() -> None:
    frames = []
    for tier, folders in (("synthetic", ("discovery", "confirmation")), ("plasmode", ("plasmode",))):
        h = pd.concat([pd.read_csv(RESULTS / "e1" / "v2" / f / "headline.csv") for f in folders])
        h["size"] = h.groupby(["layer", "model"]).n.rank(method="dense").map({1.0: "small", 2.0: "large"})
        counts = h.groupby(["layer", "model", "size", "n"])[["claims", "certified", "refuted", "released_wrong", "blocked_correct"]].sum().reset_index()
        counts.insert(0, "tier", tier)
        frames.append(counts)
    t = pd.concat(frames)
    decided = t.certified + t.refuted + t.released_wrong + t.blocked_correct
    errors = t.released_wrong + t.blocked_correct
    t["decided"] = (decided / t.claims).map("{:.0%}".format)
    t["accuracy among decided"] = ((t.certified + t.refuted) / decided).map("{:.1%}".format)
    t["confident errors"] = (errors / t.claims).map("{:.1%}".format)
    order = {"data": 0, "model": 1, "end to end": 2}
    t = t.sort_values(["tier", "layer", "model", "size"], key=lambda s: s.map(order) if s.name == "layer" else s, ascending=[False, True, True, False])
    t["n"] = t.n.map("{:,}".format)
    t = t.rename(columns={"layer": "layer (reference)"})[["tier", "layer (reference)", "model", "n", "claims", "decided", "accuracy among decided", "confident errors"]]
    write("tab3_e1", "Tab. 3: E1, the lexicon's verdicts against the planted truth, by tier",
          [("", t)],
          "Data layer: the lexicon on the oracle (what the sample supports); model layer: on the fitted model, against the oracle's labels; "
          "end to end: on the fitted model, against the planted labels (D12). Each tier pools its three seeds (synthetic: the discovery "
          "seed and the two confirmation seeds); the model layer counts only the claims the oracle decides. Confident errors: a false claim certified or a true claim refuted, over all claims (D31).",
          ["lllrrrrr"])  # fmt: skip


def _e3_row(name: str, rows: pd.DataFrame) -> dict:
    off = rows[rows["off scored"] == True]  # noqa: E712
    on = rows[rows["on scored"] == True]  # noqa: E712
    p_off, p_on = (off["off false M"] > 0).mean(), (on["on false M"] > 0).mean()
    exits = {e: (rows.exit == e).mean() for e in ("RELEASED", "RELEASED_REDUCED", "TEMPLATE", "ESCALATE")}
    return {"Writer, setting": name, "runs": len(rows), "released / reduced / template / escalate": " / ".join(f"{v:.0%}" for v in exits.values()),
            "repair rounds (mean)": f"{rows.rounds.mean():.2f}", "P_U before": f"{p_off:.1%}", "P_U after": f"{p_on:.1%}",
            "E_U": f"{1 - p_on / p_off:.2f}" if p_off else "–", "cost per run": f"${rows.cost.mean():.4f}"}  # fmt: skip


def tab4() -> None:
    haiku = pd.read_csv(RESULTS / "e3" / "v3-x3" / "haiku" / "rows.csv")
    sonnet = pd.read_csv(RESULTS / "e3" / "v3-x3" / "sonnet" / "rows.csv")
    qwen = pd.read_csv(RESULTS / "e3" / "v3-x3" / "qwen3.8-27b" / "rows.csv")
    local = pd.read_csv(RESULTS / "local" / "run" / "l1" / "rows.csv")
    rows = [_e3_row("Claude Haiku 5.5, global (E3)", haiku[~haiku["pilot dataset"]]),
            _e3_row("Claude Sonnet 5.5, global (E3 subset)", sonnet[~sonnet["pilot dataset"]]),
            _e3_row("Qwen3 27B, self-hosted, global (E3 subset)", qwen[~qwen["pilot dataset"]]),
            _e3_row("Claude Haiku 5.5, adverse-action notices (local spot check)", local[~local["pilot notice"]])]  # fmt: skip
    effect = pd.read_csv(RESULTS / "e2" / "v2" / "text" / "false_alarms" / "e3_effect.csv").set_index("quantity").value
    labelled = {"Writer, setting": "Claude Haiku 5.5, global, with human labels", "runs": "40 drafts, all released texts with a false claim",
                "released / reduced / template / escalate": "", "repair rounds (mean)": "",
                "P_U before": f"{float(effect['P_U off, labelled']):.1%} (95% interval " + "–".join(f"{float(x):.1%}" for x in effect['P_U off, labelled, 95% interval'].split(' to ')) + ")",
                "P_U after": f"{float(effect['P_U on, labelled (open: as errors)'].split()[0]):.2%}",
                "E_U": f"{float(effect['E_U, labelled']):.2f} (worst case {float(effect['E_U, worst case (P_U on with open texts, P_U off at its interval' + chr(39) + 's low end)']):.2f})",
                "cost per run": ""}  # fmt: skip
    rows.insert(1, labelled)
    write("tab4_e3", "Tab. 4: survival, control effectiveness and cost (E3, D36)", [("", pd.DataFrame(rows))],
          "Outside the pilot datasets and the pilot notices. P_U: share of texts with a claim false against the fitted model, as read by three "
          "scoring readings apart from the gate's (a claim counts if two find it); before = the writer's first draft, after = the released "
          "text; E_U = 1 − P_U after / P_U before. With human labels, most false claims in released texts are misreadings by the scoring "
          "readings (§14.21). Cost per run: every call of the trace at its price when made (batch prices for E3).",
          ["p{3.7cm}p{1.7cm}p{2.1cm}p{1.1cm}p{1.9cm}p{1.1cm}p{1.6cm}p{1.1cm}"])  # fmt: skip


def main() -> None:
    for build in (tab1, tab2, tab3, tab4):
        build()
    for path in sorted(OUT.glob("tab*.md")):
        print(f"--- {path.name}\n{path.read_text()}")


if __name__ == "__main__":
    main()
