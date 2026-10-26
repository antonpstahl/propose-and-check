"""Tabs. 1-6 of the working paper (plan §8), each from its source of truth, as Markdown and CSV in paper/tables/.

- Tab. 1, DSL and lexicon: the claim forms and the words they stand for, from the writers' own DSL tables
  (llm/prompts/system.md, system_local.md), and the lexicon's thresholds (lexicon/lexicon.yaml). Under lexicon v3
  (D65) the global claims and the thresholds come from the lexicon itself (lexicon/words.py), the source the
  writer's and the extractor's prompts are rendered from, and the table is written as tab1_dsl_lexicon_v3; under
  v2 (VERIFIER_GATE_LEXICON=v2) it is the frozen Tab. 1.
- Tab. 2, the benchmark: per tier the features, their planted role, shape and target share, and the pairs with their
  shares by interaction level (data/dgp.py, data/plasmode.py). The synthetic distributions and shapes are written as
  coded in dgp.sample_features and dgp.MAIN_SHAPES (frozen with the DGP, D11).
- Tab. 3, E1 by tier (D31): decided rate, accuracy among decided and confident-error rate per layer, model and
  sample size, with its 95% interval clustered by dataset (review M8, point 5); the synthetic tier pooled over its
  three seeds (discovery and confirmation, recomputed from the counts, not averaged), the plasmode tier over its
  three seeds. Under lexicon v3 with D74's fixes (D84: the configuration D75 froze); E1 under v2 stays in git.
- Tab. 4, survival, control effectiveness and cost (D36; D84): (1) E3's rerun with D74's fixes per tier, also split
  by handover (H1: the facts only; H2: with the certified statements), and the adverse-action spot check per tier
  (synthetic: l2; plasmode: l2-d74): exit states, repair rounds, P_U before and after the gate as read by E3's
  scoring readings, E_U, cost per run; (2) the residual of D74 by reference and standard: the gate's extractor,
  GPT-6 Luna, either reader (e3_independent) and, on the synthetic tier, the blind labels (e3_blind, D82, D83); (3)
  E3's first run (lexicon v2, prompts v3, extractor x3) for the three writers.
- Tab. 5, the gate and an LLM critic on the same texts (D79; D84): the critic c3 (GPT-6 Luna with the writer's
  inputs, D75's configuration) beside the gate with extractor x5 (D78): recall and blocked correct texts per set of
  texts and label source, balanced accuracy, and on the blind sample how many labelled texts the gate's extractor
  (as a scoring reader) and the critic flag (e3_blind readers.csv); the critic's confident errors and the cost per
  text. c1 and c2 (D56, D72) stay in git and in results/e2/v2/text/critic/.
- Tab. 6, E3's baselines beside D74 (D71, D76): the template-only and plain-prompt arms beside gate off and gate on,
  on the facts-only cells of each tier: P_U with its interval, E_U against gate off and against the plain prompt,
  claims and words per text, claims by kind, hedges, coverage, numbers no claim checks and cost, from e3_baselines'
  compare.csv.

Each table is also written as a LaTeX tabular (booktabs) for the working paper's source, which inputs it: no number of the paper is
typed by hand.

Run: `uv run python -m verifier_gate.experiments.tables` (`--only tab1` for one table).
"""

import argparse
from pathlib import Path

import re

import pandas as pd
import yaml

from verifier_gate.data import dgp, plasmode
from verifier_gate.experiments import e1_lexicon, metrics
from verifier_gate.lexicon import predicates as p
from verifier_gate.lexicon import words
from verifier_gate.llm import prompts

ROOT = Path(__file__).parents[3]
OUT = ROOT / "paper" / "tables"
RESULTS = ROOT / "results"
E1_RUN = "v3-d74"  # D84: the paper's tables report the configuration D75 froze
E3_RUN = "v4-x5-m5-d74"
FIRST_RUN = "v3-x3"  # E3 as first run: lexicon v2, writer prompts v3, extractor x3
LOCAL_RUNS = {"synthetic": RESULTS / "local" / "run" / "l2", "plasmode": RESULTS / "local" / "plasmode" / "run" / "l2-d74"}
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
    current = p.load()
    if words.section(current) is not None:
        return tab1_words(current)
    lex = yaml.safe_load(current.source.read_text())
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


def tab1_words(lex: p.Lexicon) -> None:
    """Tab. 1 from the lexicon's words and numbers (D65): the rows of the writer's DSL table as rendered, and the
    thresholds with v3's margins (D63, D64)."""
    n = words.numbers(lex)
    claims = pd.DataFrame([{"Words in the text": w, "DSL claim": d, "Meaning (judged on the whole 95% band)": m} for w, d, m in words.table_rows(lex)])
    thresholds = pd.DataFrame([
        {"Threshold": "strength classes (share of importance)", "Value": f"negligible < {n['weak']} ≤ weak < {n['moderate']} ≤ moderate < {n['strong']} ≤ strong"},
        {"Threshold": "detectable effect", "Value": f"simultaneous band excludes 0 on more than {n['detectable']} of the data, or a significant net change"},
        {"Threshold": "\"hardly matters\", \"no interaction\"", "Value": f"the whole share band (a pair's share band) below {n['weak']} ({n['pair_share']}), or a pair the model lacks (v3)"},
        {"Threshold": "\"about x%\"", "Value": f"within {n['share_points']} points or {n['share_relative']} of the share"},
        {"Threshold": "direction margin", "Value": f"{n['margin']} of the term's range between its 1st and 99th percentile; \"increases\" needs the band to rule out any fall larger than that (v3)"},
        {"Threshold": "\"mostly\" (exception mass)", "Value": f"a fall larger than the margin, detected, on at most {n['exception']} of the data"},
        {"Threshold": "jump / peak location (window w)", "Value": f"{n['window']} of the 5th-95th percentile range; on counts, the gap between observed values (v2)"},
        {"Threshold": "jump size and sign", "Value": f"at least {n['jump']} of the term's range, significant; \"jumps at\" a step up, \"drops at\" a step down (v3)"},
        {"Threshold": "interaction present", "Value": f"pair share band at or above {n['pair_share']} and a significant interaction contrast"},
        {"Threshold": "band level", "Value": f"{n['level']}, from 100 Poisson bootstrap refits; curves: simultaneous (sup-t) bands"},
    ])  # fmt: skip
    write(f"tab1_dsl_lexicon_{lex.version}", f"Tab. 1: the DSL and the lexicon (lexicon {lex.version})",
          [("Claims about the model (global)", claims), ("Claims about one declined applicant (local spot check)", dsl_rows("system_local")),
           ("The lexicon's thresholds", thresholds)],
          "A claim is true if the whole band lies inside the set its word names, false if it lies outside, undecidable otherwise; "
          "undecidable claims are never released as stated (D30). The global rows and the thresholds are generated from the lexicon, "
          "as the writer's and the extractor's prompts are (D65).",
          ["p{4.6cm}p{4.6cm}p{5.6cm}", "p{3.3cm}p{4.5cm}p{7cm}", "p{4.2cm}p{10.8cm}"])  # fmt: skip


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
        base = RESULTS / "e1" / E1_RUN
        h = pd.concat([pd.read_csv(base / f / "headline.csv") for f in folders])
        h["size"] = h.groupby(["layer", "model"]).n.rank(method="dense").map({1.0: "small", 2.0: "large"})
        counts = h.groupby(["layer", "model", "size", "n"])[["claims", "certified", "refuted", "released_wrong", "blocked_correct"]].sum().reset_index()
        verdicts = pd.concat([pd.read_csv(base / f / "verdicts.csv", dtype=str, keep_default_na=False) for f in folders]).astype({"n": int, "seed": int})
        long = e1_lexicon.layers(verdicts)
        bounds = {key: metrics.clustered_interval(group, e1_lexicon.confident_error_rate) for key, group in long.groupby(["layer", "model", "n"])}
        counts["interval"] = [bounds[(r.layer, r.model, r.n)] for r in counts.itertuples()]
        counts.insert(0, "tier", tier)
        frames.append(counts)
    t = pd.concat(frames)
    decided = t.certified + t.refuted + t.released_wrong + t.blocked_correct
    errors = t.released_wrong + t.blocked_correct
    t["decided"] = (decided / t.claims).map("{:.0%}".format)
    t["accuracy among decided"] = ((t.certified + t.refuted) / decided).map("{:.1%}".format)
    t["confident errors"] = (errors / t.claims).map("{:.2%}".format)
    t["95% interval"] = t.interval.map(lambda b: f"{b[0]:.2%}–{b[1]:.2%}")
    order = {"data": 0, "model": 1, "end to end": 2}
    t = t.sort_values(["tier", "layer", "model", "size"], key=lambda s: s.map(order) if s.name == "layer" else s, ascending=[False, True, True, False])
    t["n"] = t.n.map("{:,}".format)
    t = t.rename(columns={"layer": "layer (reference)"})[["tier", "layer (reference)", "model", "n", "claims", "decided", "accuracy among decided", "confident errors", "95% interval"]]
    write("tab3_e1", "Tab. 3: E1, the lexicon's verdicts against the planted truth, by tier (lexicon v3 with D74's fixes)",
          [("", t)],
          "Data layer: the lexicon on the oracle (what the sample supports); model layer: on the fitted model, against the oracle's labels; "
          "end to end: on the fitted model, against the planted labels (D12). Each tier pools its three seeds (synthetic: the discovery "
          "seed and the two confirmation seeds); the model layer counts only the claims the oracle decides. Confident errors: a false claim "
          "certified or a true claim refuted, over all claims (D31), with a 95% percentile interval from a bootstrap over the datasets (9 per cell).",
          ["lllrr" + r">{\raggedleft\arraybackslash}p{1.2cm}" * 3 + r">{\raggedleft\arraybackslash}p{2.1cm}"])  # fmt: skip


def _e3_row(name: str, rows: pd.DataFrame) -> dict:
    off = rows[rows["off scored"] == True]  # noqa: E712
    on = rows[rows["on scored"] == True]  # noqa: E712
    p_off, p_on = (off["off false M"] > 0).mean(), (on["on false M"] > 0).mean()
    exits = {e: (rows.exit == e).mean() for e in ("RELEASED", "RELEASED_REDUCED", "TEMPLATE", "ESCALATE")}
    return {"Writer, setting": name, "runs": len(rows), "released / reduced / template / escalate": " / ".join(f"{v:.0%}" for v in exits.values()),
            "repair rounds (mean)": f"{rows.rounds.mean():.2f}", "P_U before": f"{p_off:.1%}", "P_U after": f"{p_on:.1%}",
            "E_U": f"{1 - p_on / p_off:.2f}" if p_off else "–", "cost per run": f"${rows.cost.mean():.4f}"}  # fmt: skip


def _pct(value: float, lo: float, hi: float) -> str:
    return f"{value:.1%} ({lo:.1%}–{hi:.1%})"


def tab4() -> None:
    d74 = pd.read_csv(RESULTS / "e3" / E3_RUN / "haiku" / "rows.csv")
    d74 = d74[~d74["pilot dataset"]]
    tiers = d74.naming.eq("codes").map({True: "plasmode", False: "synthetic"})
    rerun = []
    for tier in ("synthetic", "plasmode"):
        part = d74[tiers == tier]
        rerun += [_e3_row(f"{tier}, global", part), _e3_row(f"{tier}, facts only (H1)", part[part.handover == "H1"]),
                  _e3_row(f"{tier}, with certified statements (H2)", part[part.handover == "H2"])]  # fmt: skip
    for tier, folder in LOCAL_RUNS.items():
        local = pd.read_csv(folder / "rows.csv")
        rerun.append(_e3_row(f"{tier}, adverse-action notices", local[~local["pilot notice"]]))
    rerun = pd.DataFrame(rerun).rename(columns={"Writer, setting": "Tier, texts"})
    residual = pd.read_csv(RESULTS / "e3" / E3_RUN / "independent" / "residual_by_standard.csv")
    score = pd.read_csv(RESULTS / "e3" / E3_RUN / "blind" / "score.csv").set_index(["standard", "stratum"])
    readers = {"haiku": "Claude Haiku 5.5 (the gate's extractor, x5)", "luna": "GPT-6 Luna (another vendor)", "either": "either reader"}
    rows = []
    for tier in ("synthetic", "plasmode"):
        for standard in ("refuted", "release rule"):
            for reader, name in readers.items():
                r = residual[(residual.tier == tier) & (residual.standard == standard) & (residual.reader == reader)].iloc[0]
                rows.append({"Tier, standard": f"{tier}, {standard}", "Read by": name, "P_U before": _pct(r["P_U off"], r["off lo"], r["off hi"]),
                             "P_U after": _pct(r["P_U on"], r["on lo"], r["on hi"]),
                             "of LLM-written texts": _pct(r["P_U on, LLM-written"], r["on, LLM-written lo"], r["on, LLM-written hi"]),
                             "of templates": _pct(r["P_U on, template"], r["on, template lo"], r["on, template hi"]),
                             "E_U": f"{r['E_U']:.2f} ({r['E_U lo']:.2f} to {r['E_U hi']:.2f})"})  # fmt: skip
            if tier == "synthetic":
                b = lambda stratum: score.loc[(standard, stratum)]  # noqa: E731
                rows.append({"Tier, standard": f"{tier}, {standard}", "Read by": "blind labels, one rater (40 texts)",
                             "P_U before": f"{_pct(b('draft').P_U, b('draft').lo, b('draft').hi)}, {int(b('draft').errors)} of {int(b('draft').labelled)}",
                             "P_U after": _pct(b("on (weighted)").P_U, b("on (weighted)").lo, b("on (weighted)").hi),
                             "of LLM-written texts": f"{int(b('LLM-written').errors)} of {int(b('LLM-written').labelled)}",
                             "of templates": f"{int(b('template').errors)} of {int(b('template').labelled)}",
                             "E_U": f"{b('E_U').P_U:.2f} ({b('E_U').lo:.2f} to {b('E_U').hi:.2f})"})  # fmt: skip
    first = {name: pd.read_csv(RESULTS / "e3" / FIRST_RUN / folder / "rows.csv") for name, folder in
             (("Claude Haiku 5.5", "haiku"), ("Claude Sonnet 5.5 (subset)", "sonnet"), ("qwen3.8:27b, self-hosted (subset)", "qwen3.8-27b"))}  # fmt: skip
    first = pd.DataFrame([_e3_row(name, rows_[~rows_["pilot dataset"]]) for name, rows_ in first.items()])
    write("tab4_e3", "Tab. 4: survival, control effectiveness and cost (E3, D36)",
          [("E3 with D74's fixes: Claude Haiku 5.5, lexicon v3, writer prompts v4, extractor x5", rerun),
           ("The residual of D74 by reference and standard", pd.DataFrame(rows)),
           ("E3's first run: lexicon v2, writer prompts v3, extractor x3 (synthetic tier)", first)],
          "Outside the pilot datasets and the pilot notices. P_U: share of texts with a claim false against the fitted model (refuted), or false "
          "or stated as settled where the facts leave it open (release rule); before = the writer's first draft, after = the released text; "
          "E_U = 1 − P_U after / P_U before. In the first and third parts, P_U is as read by E3's three scoring readings (the gate's extractor "
          "request, replicas 3 to 5; a claim counts if two find it). In the second, intervals for the readers come from a bootstrap over the "
          "datasets; for the blind labels, Wilson intervals per stratum, P_U after weighted by the strata's population sizes, and E_U from a "
          "stratified bootstrap. Cost per run: every call of the trace at its price when made (batch prices).",
          ["p{4cm}p{1cm}p{2.3cm}p{1.1cm}p{1.2cm}p{1.2cm}p{1cm}p{1.2cm}", "p{2.2cm}p{3cm}p{2cm}p{2cm}p{1.7cm}p{1.7cm}p{1.9cm}",
           "p{4cm}p{1cm}p{2.3cm}p{1.1cm}p{1.2cm}p{1.2cm}p{1cm}p{1.2cm}"])  # fmt: skip


CORRECT = ("correct", "control", "control text")
CRITIC = RESULTS / "e2" / "v3-d74" / "text" / "critic" / "gpt-6-luna" / "c3"  # the critic in D75's configuration (D79)


def _share(hits: int, n: int) -> str:
    return f"{hits} of {n} ({hits / n:.0%})" if n else "–"


def tab5() -> None:
    t = pd.read_csv(CRITIC / "cases.csv")
    t = t[(t.critiqued == True) & (t.source != "blind")]  # noqa: E712
    sets = [  # name, rows, label column, what is counted
        ("LLM-written errors caught (final labels)", "llm", "role", "error"),
        ("LLM-written errors caught (author's first pass)", "llm", "first pass", "error"),
        ("LLM-written sentences judged correct, blocked (final labels)", "llm", "role", "correct"),
        ("LLM-written sentences judged correct, blocked (first pass)", "llm", "first pass", "correct"),
        ("Scripted errors caught (30 per operator)", "script", "role", "error"),
        ("Scripted errors caught: a feature the model lacks (M9)", "script M9", "role", "error"),
        ("Template texts, every claim certified, blocked", "control", "role", "correct"),
        ("Control mutants (a step moved inside the tolerance), blocked", "script", "role", "control"),
    ]  # fmt: skip
    columns = {"Gate (x5)": "gate caught", "Critic c3 (GPT-6 Luna)": "blocked"}
    rows = []
    for name, source, column, kind in sets:
        part = t[t.source == source.split()[0]]
        if source.endswith("M9"):
            part = part[part.operator == "M9"]
        part = part[part[column].isin(CORRECT if kind == "correct" else (kind,))]
        rows.append({"Texts": name} | {who: _share(int(part[flag].astype(bool).sum()), len(part)) for who, flag in columns.items()})
    errors, correct = t.role == "error", t.role.isin(CORRECT)
    rows.append({"Texts": "Balanced accuracy: errors (LLM-written, final labels, and scripted); known-correct texts (templates, control mutants, LLM-written sentences judged correct)"}
                | {who: f"{(t[flag].astype(bool)[errors].mean() + (~t[flag].astype(bool))[correct].mean()) / 2:.2f}" for who, flag in columns.items()})  # fmt: skip
    readers = pd.read_csv(RESULTS / "e3" / E3_RUN / "blind" / "readers.csv").set_index(["reader", "standard", "stratum"])
    for standard, labelled_as in (("refuted", "false"), ("release rule", "false or not settled")):
        for kind, label in (("all", "all 42 entries"), ("LLM-written", "LLM-written releases")):
            gate, critic = readers.loc[("haiku", standard, kind)], readers.loc[("critic c3", standard, kind)]
            rows.append({"Texts": f"Blind sample ({label}): texts with a sentence labelled {labelled_as}, flagged",
                         "Gate (x5)": _share(int(gate["flagged by the reader"]), int(gate["labelled errors"])) + ", as a scoring reader",
                         "Critic c3 (GPT-6 Luna)": _share(int(critic["flagged by the reader"]), int(critic["labelled errors"]))})  # fmt: skip
            rows.append({"Texts": "  texts labelled without such a sentence, flagged",
                         "Gate (x5)": _share(int(gate["flagged anyway"]), int(gate["labelled no error"])) + ", as a scoring reader",
                         "Critic c3 (GPT-6 Luna)": _share(int(critic["flagged anyway"]), int(critic["labelled no error"]))})  # fmt: skip
    wrong_block = t[t.role.isin(CORRECT) & t.blocked.astype(bool)]
    wrong_pass = t[(t.role == "error") & ~t.blocked.astype(bool)]
    rows.append({"Texts": "Critic's confident errors: correct text blocked at p ≥ 0.9 / error passed at p ≤ 0.1", "Gate (x5)": "no probability",
                 "Critic c3 (GPT-6 Luna)": f"{int((wrong_block.p_error >= 0.9).sum())} of {len(wrong_block)} / {int((wrong_pass.p_error <= 0.1).sum())} of {len(wrong_pass)}"})  # fmt: skip
    rows.append({"Texts": "Cost per text (USD)", "Gate (x5)": f"{3 * 1.628 / 9084:.4f} (x4's batch price)", "Critic c3 (GPT-6 Luna)": f"{pd.read_csv(CRITIC / 'cases.csv').cost.mean():.4f}"})
    write("tab5_critic", "Tab. 5: the gate and an LLM critic on the same texts (D78, D79, D83)", [("", pd.DataFrame(rows))],
          "Outside the pilot datasets. Blocked: the critic names a problem; the gate does not release the text (a text the extractor could not "
          "read counts as caught, D32). Final labels: the author's labels after a review against the lexicon; first pass: the author's labels "
          "alone, made without any checker's verdict (unsure left out). Template texts and control mutants are correct by construction "
          "(every claim certified on the fitted model). The critic c3 gets the facts each writer saw (H2 with the certified statements for an "
          "H2 text) and the writer's whole set of rules, from writer prompt v4 as D74's writer got it. Blind sample: B01 to B40 of D76's sample, "
          "labelled by the author (D82, D83); the gate's column there is its extractor as one of E3's scoring readings, since the gate itself "
          "released every text of the on arm. The gate's cost is its three readings at batch prices; the critic's one call at synchronous "
          "prices, reasoning included.",
          [r">{\raggedright\arraybackslash}p{7.4cm}>{\raggedright\arraybackslash}p{3.6cm}>{\raggedright\arraybackslash}p{3.4cm}"])  # fmt: skip


def _interval(row: pd.Series) -> str:
    return f"{row['P_U']:.1%} ({max(row['P_U 95% low'], 0.0) + 0.0:.1%}–{row['P_U 95% high']:.1%})"  # a Wilson bound of -0.0 prints as 0.0%


def tab6() -> None:
    """What the gate adds over its template and a plain prompt (D71), beside D74 (D76), on the facts-only cells of each
    tier outside the pilot datasets."""
    path = RESULTS / "e3" / E3_RUN / "baselines" / prompts.PLAIN_VERSION / "compare.csv"
    if not path.exists():
        return
    t = pd.read_csv(path)
    t = t[t.set == "H1 cells"]
    names = {"template only": "Template only (no LLM)", "plain prompt": "Plain prompt (no gate)", "gate off (first draft)": "Gate off (first draft)",
             "gate on (released)": "Gate on (released text)", "gate on, exit RELEASED": "  gate on: released as written",
             "gate on, exit RELEASED_REDUCED": "  gate on: released reduced", "gate on, exit TEMPLATE": "  gate on: template"}  # fmt: skip
    t = t[t.arm.isin(names)].assign(arm=lambda d: d.arm.map(names))
    control = pd.DataFrame({
        "Tier": t.tier, "Arm": t.arm, "texts": t["texts scored"], "P_U (95% interval)": t.apply(_interval, axis=1),
        "E_U vs gate off": t["E_U vs gate off"].map(lambda v: f"{v:.2f}"), "E_U vs plain prompt": t["E_U vs plain prompt"].map(lambda v: f"{v:.2f}"),
        "claims per text": t["claims per text"].map(lambda v: f"{v:.1f}"), "words per text": t["words per text"].map(lambda v: f"{v:.0f}"),
        "claims false vs planted truth": t["claims false vs T, no hedges"].map(lambda v: f"{v:.1%}"),
        "cost per text": t["cost per text"].map(lambda v: "–" if pd.isna(v) else f"${v:.4f}"),
    })  # fmt: skip
    kinds = pd.DataFrame({
        "Tier": t.tier, "Arm": t.arm,
        **{name: t[f"{name} claims per text"].map(lambda v: f"{v:.1f}") for name in ("strength", "direction", "rank", "share", "comparison", "interaction", "jump or peak")},
        "hedges (share of claims)": t["hedge share of claims"].map(lambda v: f"{v:.1%}"),
        "every required term covered": t["texts covering every required term"].map(lambda v: f"{v:.0%}"),
        "numbers no claim checks": t["unchecked numbers per text"].map(lambda v: f"{v:.1f}"),
    })  # fmt: skip
    cells = t.drop_duplicates("tier").set_index("tier").cells
    write("tab6_baselines", "Tab. 6: what the gate adds over its template and over a plain prompt (facts-only cells; D71, D76)",
          [("Control effectiveness and volume", control), ("Claims per text by kind, hedges, coverage and numbers", kinds)],
          f"Claude Haiku 5.5 on the facts-only (H1) cells of D74 outside the pilot datasets ({int(cells['synthetic'])} synthetic: 16 datasets × 2 models × "
          f"2 namings × 5 draws; {int(cells['plasmode'])} plasmode: 18 datasets × 2 models × 5 draws), every arm scored by E3's three scoring "
          "readings (extractor x5; a claim counts if two find it) and verified on the fitted model under lexicon v3 with D74's fixes. Template "
          "only: the gate's fallback text from the certified statements, without an LLM. Plain prompt: the same writer and facts with the "
          "writer's role and rules for the text, but no lexicon words, DSL, plan, verifier or repair (prompts p1). Gate off: the first draft "
          "under the gate's prompt; gate on: the released text, and by exit state. P_U: share of texts with a claim false against the fitted "
          "model, as read; 95% Wilson interval. E_U = 1 − P_U / P_U of the reference arm. Claims false vs planted truth: the share of claims "
          "other than hedges that are false against T (a hedge is about the sample, not T). Required terms: the three most important features "
          "and every pair with a share of at least 10%. Numbers no claim checks: statements with a number that no DSL form expresses (the "
          "gate's round trip fails them). Cost per text: the writer's and the gate's calls at batch prices, scoring readings not included.",
          ["lp{3cm}r" + r">{\raggedleft\arraybackslash}p{2.1cm}" + r">{\raggedleft\arraybackslash}p{1.05cm}" * 6,
           "lp{3cm}" + r">{\raggedleft\arraybackslash}p{0.95cm}" * 7 + r">{\raggedleft\arraybackslash}p{1.25cm}" * 3])  # fmt: skip


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default="", help="comma-separated tables, e.g. tab1")
    only = parser.parse_args().only.split(",") if parser.parse_args().only else None
    for build in (tab1, tab2, tab3, tab4, tab5, tab6):
        if only is None or build.__name__ in only:
            build()
    for path in sorted(OUT.glob("tab*.md")):
        print(f"--- {path.name}\n{path.read_text()}")


if __name__ == "__main__":
    main()
