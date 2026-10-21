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
  sample size; the synthetic tier pooled over its three seeds (discovery and confirmation, recomputed from the
  counts, not averaged), the plasmode tier over its three seeds.
- Tab. 4, survival, control effectiveness and cost (D36): per writer, outside the pilot datasets: exit states,
  repair rounds, P_U before and after the gate and E_U, as run and with author-reviewed labels where they exist
  (§14.21), Haiku also split by handover (H1: the facts only; H2: with the certified statements; WP3's handover
  question), and the cost per run; the local spot check (§14.22) as its own row.
- Tab. 5, the gate and an LLM critic on the same texts (D56, §14.29; D72): recall and blocked correct texts per set
  of texts and label source, balanced accuracy, E3's released texts blocked by handover, the critic's confident
  errors, and the cost per text, from e2_critic's cases.csv per critic and prompt version (c1; c2 with the inputs
  matched to the writer's), which carries the gate's x4 outcome per case, and, for E3's released texts, the labels
  of the critic's flags.
- Tab. 6, E3's baselines (D71): the template-only and plain-prompt arms beside gate off and gate on, on E3's
  facts-only cells: P_U with its interval, E_U against gate off and against the plain prompt, claims and words per
  text, claims by kind, hedges, coverage, numbers no claim checks and cost, from e3_baselines' compare.csv.

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
from verifier_gate.lexicon import predicates as p
from verifier_gate.lexicon import words
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
    local = pd.read_csv(RESULTS / "local" / "run" / prompts.LOCAL_VERSION / "rows.csv")
    haiku = haiku[~haiku["pilot dataset"]]
    rows = [_e3_row("Claude Haiku 5.5, global (E3)", haiku),
            _e3_row("Claude Haiku 5.5, global, facts only (H1)", haiku[haiku.handover == "H1"]),
            _e3_row("Claude Haiku 5.5, global, with certified statements (H2)", haiku[haiku.handover == "H2"]),
            _e3_row("Claude Sonnet 5.5, global (E3 subset)", sonnet[~sonnet["pilot dataset"]]),
            _e3_row("qwen3.8:27b (NVFP4), self-hosted, global (E3 subset)", qwen[~qwen["pilot dataset"]]),
            _e3_row("Claude Haiku 5.5, adverse-action notices (local spot check)", local[~local["pilot notice"]])]  # fmt: skip
    effect = pd.read_csv(RESULTS / "e2" / "v2" / "text" / "false_alarms" / "e3_effect.csv").set_index("quantity").value
    labelled = {"Writer, setting": "Claude Haiku 5.5, global, with author-reviewed labels", "runs": "40 drafts, all released texts with a false claim",
                "released / reduced / template / escalate": "", "repair rounds (mean)": "",
                "P_U before": f"{float(effect['P_U off, labelled']):.1%} (95% interval " + "–".join(f"{float(x):.1%}" for x in effect['P_U off, labelled, 95% interval'].split(' to ')) + ")",
                "P_U after": f"{float(effect['P_U on, labelled (open: as errors)'].split()[0]):.2%}",
                "E_U": f"{float(effect['E_U, labelled']):.2f} (worst case {float(effect['E_U, worst case (P_U on with open texts, P_U off at its interval' + chr(39) + 's low end)']):.2f})",
                "cost per run": ""}  # fmt: skip
    rows.insert(1, labelled)
    write("tab4_e3", "Tab. 4: survival, control effectiveness and cost (E3, D36)", [("", pd.DataFrame(rows))],
          "Outside the pilot datasets and the pilot notices. P_U: share of texts with a claim false against the fitted model, as read by three "
          "scoring readings apart from the gate's (a claim counts if two find it); before = the writer's first draft, after = the released "
          "text; E_U = 1 − P_U after / P_U before. With author-reviewed labels, most false claims in released texts are misreadings by the "
          "scoring readings. H1: the facts only; H2: the facts and the statements the verifier certifies. Cost per run: every call of the "
          "trace at its price when made (batch prices for E3).",
          ["p{3.7cm}p{1.7cm}p{2.1cm}p{1.1cm}p{1.9cm}p{1.1cm}p{1.6cm}p{1.1cm}"])  # fmt: skip


CRITICS = {"GPT-6 Luna (c1)": ("gpt-6-luna", "c1"), "GPT-6 Luna, matched inputs (c2)": ("gpt-6-luna", "c2"),
           "GPT-6.1 Sol (c1)": ("gpt-6.1-sol", "c1")}  # results/e2/v2/text/critic/<folder>/<prompt version>
CORRECT = ("correct", "control", "control text")


def _share(hits: int, n: int) -> str:
    return f"{hits} of {n} ({hits / n:.0%})" if n else "–"


def tab5() -> None:
    base = RESULTS / "e2" / "v2" / "text" / "critic"
    tables = {name: pd.read_csv(base / folder / version / "cases.csv") for name, (folder, version) in CRITICS.items()
              if (base / folder / version / "cases.csv").exists()}  # fmt: skip
    luna = next(iter(tables.values()))
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
    checkers = [("Gate (x4)", luna)] + [(f"Critic: {n}", t) for n, t in tables.items()]
    rows = []
    for name, source, column, kind in sets:
        row = {"Texts": name}
        for who, table in checkers:
            part = table[(table.source == source.split()[0]) & (table.critiqued == True)]  # noqa: E712
            if source.endswith("M9"):
                part = part[part.operator == "M9"]
            part = part[part[column].isin(CORRECT if kind == "correct" else (kind,))]
            caught = part["gate caught" if who.startswith("Gate") else "blocked"].astype(bool)
            row[who] = _share(int(caught.sum()), len(part)) if len(part) else "–"
        rows.append(row)
    row = {"Texts": "Balanced accuracy: errors (LLM-written, final labels, and scripted); known-correct texts (templates, control mutants, LLM-written sentences judged correct)"}
    for who, table in checkers:
        t = table[(table.source.isin(("llm", "script", "control"))) & (table.critiqued == True)]  # noqa: E712
        blocked = t["gate caught" if who.startswith("Gate") else "blocked"].astype(bool)
        errors, correct = t.role == "error", t.role.isin(CORRECT)
        complete = {"llm", "script", "control"} <= set(t.source)  # only on all three sets (Sol did not run the scripted ones)
        row[who] = f"{(blocked[errors].mean() + (~blocked[correct]).mean()) / 2:.2f}" if complete else "–"
    rows.append(row)
    fa = pd.read_csv(RESULTS / "e2" / "v2" / "text" / "false_alarms" / "score.csv").set_index("extractor").loc["x4"]
    gate_texts = pd.read_csv(RESULTS / "e2" / "v2" / "text" / "false_alarms" / "texts_x4.csv")
    gate_texts = gate_texts[gate_texts.scored == True].assign(handover=lambda d: d.run.str.split("_").str[2])  # noqa: E712
    for variant, label in (("", "E3's released texts (LLM-written), blocked"), ("H1", "  of them written from the facts only (H1)"),
                           ("H2", "  of them written with the certified statements (H2)")):  # fmt: skip
        g = gate_texts[gate_texts.handover == variant] if variant else gate_texts
        row = {"Texts": label, "Gate (x4)": _share(int(g.blocked.sum()), len(g))}
        for n, t in tables.items():
            e3 = t[(t.source == "e3") & (t.critiqued == True)]  # noqa: E712
            e3 = e3[e3.case.str.split("_").str[2] == variant] if variant else e3
            row[f"Critic: {n}"] = _share(int(e3.blocked.astype(bool).sum()), len(e3)) if len(e3) else "–"
        rows.append(row)
    labelled = {n: base / folder / version / "labels" / "score.csv" for n, (folder, version) in CRITICS.items()}
    row = {"Texts": "E3's released texts: correct texts blocked (false-alarm rate, labelled)", "Gate (x4)": f"{float(fa['false-alarm rate (per correct text)']):.1%}"}
    for n, t in tables.items():
        has_e3 = (t.source == "e3").any()
        rate = pd.read_csv(labelled[n]).set_index("checker").loc["critic", "false-alarm rate (per correct text)"] if labelled[n].exists() else None
        row[f"Critic: {n}"] = f"{rate:.1%}" if rate is not None else "labels pending" if has_e3 else "–"
    rows.append(row)
    first = labelled["GPT-6 Luna (c1)"]
    if first.exists():  # the author's labels of a sample of c1's blocks, and each flag's type (flag_types.csv, assigned by hand)
        score = pd.read_csv(first).set_index("checker").loc["critic"]
        types = pd.read_csv(first.parent / "flag_types.csv")
        misses = types[(types.label == "error") & types["gate miss"]].text.nunique()
        sample = int(score["labelled blocked texts"])
        others = {f"Critic: {n}": "–" for n in tables if n != "GPT-6 Luna (c1)"}
        rows.append({"Texts": "E3's released texts: blocked texts with an error by the author's labels", "Gate (x4)": _share(int(fa["real errors"]), int(fa["blocked"])),
                     "Critic: GPT-6 Luna (c1)": f"{_share(int(score['real error (labelled)']), sample)}, sample"} | others)  # fmt: skip
        rows.append({"Texts": "E3's released texts: blocked texts with an error the round trip does not check", "Gate (x4)": "–",
                     "Critic: GPT-6 Luna (c1)": f"{_share(misses, sample)}, sample"} | others)  # fmt: skip
        compared = base / "gpt-6-luna" / "c2" / "compare.csv"
        if compared.exists() and "Critic: GPT-6 Luna, matched inputs (c2)" in [f"Critic: {n}" for n in tables]:
            kept = pd.read_csv(compared).set_index("set").loc["E3 texts c1 blocked, labelled real error by the author"]
            rows.append({"Texts": "  of these texts with an error (c1's sample), blocked by c2", "Gate (x4)": "–", "Critic: GPT-6 Luna (c1)": "–",
                         "Critic: GPT-6 Luna, matched inputs (c2)": _share(int(kept.k), int(kept.n)), "Critic: GPT-6.1 Sol (c1)": "–"})  # fmt: skip
    confident, cost = {"Texts": "Critic's confident errors: correct text blocked at p ≥ 0.9 / error passed at p ≤ 0.1"}, {"Texts": "Cost per text (USD)"}
    for n, t in tables.items():
        lab = t[(t.source != "e3") & (t.critiqued == True)]  # noqa: E712
        wrong_block = lab[lab.role.isin(CORRECT) & lab.blocked.astype(bool)]
        wrong_pass = lab[(lab.role == "error") & ~lab.blocked.astype(bool)]
        confident[f"Critic: {n}"] = f"{int((wrong_block.p_error >= 0.9).sum())} of {len(wrong_block)} / {int((wrong_pass.p_error <= 0.1).sum())} of {len(wrong_pass)}"
        cost[f"Critic: {n}"] = f"{t.cost.mean():.4f}"
    confident["Gate (x4)"] = "no probability"
    cost["Gate (x4)"] = f"{3 * 1.628 / 9084:.4f}"  # three extractor readings at x4's measured batch price (e2_false_alarms.PER_CALL)
    rows += [confident, cost]
    columns = ["Texts", "Gate (x4)"] + [f"Critic: {n}" for n in tables]
    write("tab5_critic", "Tab. 5: the gate and an LLM critic on the same texts (D56, D72)", [("", pd.DataFrame(rows)[columns])],
          "Outside the pilot datasets. Blocked: the critic names a problem; the gate does not release the text (a text the extractor could not "
          "read falls back to the template). Final labels: the author's labels after a review against the lexicon; first pass: the author's "
          "labels alone, made without any checker's verdict (unsure left out). Template texts and control mutants are correct by construction "
          "(every claim certified on the fitted model). Matched inputs (prompts c2): the critic gets the facts each writer saw (H2, with the "
          "certified statements, for an H2 text) and the writer's whole set of rules with the DSL table; c1 gets the facts only (H1) and the "
          "rules for choosing words. E3's released texts blocked by c2 are not labelled yet. The gate's cost is its three readings at batch prices; the critic's one call at "
          "synchronous prices, reasoning included.",
          [r">{\raggedright\arraybackslash}p{4.9cm}" + r">{\raggedright\arraybackslash}p{2.45cm}" * (len(columns) - 1)])  # fmt: skip


def _interval(row: pd.Series) -> str:
    return f"{row['P_U']:.1%} ({row['P_U 95% low']:.1%}–{row['P_U 95% high']:.1%})"


def tab6() -> None:
    """What the gate adds over its template and a plain prompt (D71), on E3's facts-only cells outside the pilot datasets."""
    path = RESULTS / "e3" / "v3-x3" / "baselines" / prompts.PLAIN_VERSION / "compare.csv"
    if not path.exists():
        return
    t = pd.read_csv(path)
    t = t[t.set == "H1 cells"]
    names = {"template only": "Template only (no LLM)", "plain prompt": "Plain prompt (no gate)", "gate off (first draft)": "Gate off (first draft)",
             "gate on (released)": "Gate on (released text)", "gate on, exit RELEASED": "  gate on: released as written",
             "gate on, exit RELEASED_REDUCED": "  gate on: released reduced", "gate on, exit TEMPLATE": "  gate on: template"}  # fmt: skip
    t = t[t.arm.isin(names)].assign(arm=lambda d: d.arm.map(names))
    control = pd.DataFrame({
        "Arm": t.arm, "texts": t["texts scored"], "P_U (95% interval)": t.apply(_interval, axis=1),
        "E_U vs gate off": t["E_U vs gate off"].map(lambda v: f"{v:.2f}"), "E_U vs plain prompt": t["E_U vs plain prompt"].map(lambda v: f"{v:.2f}"),
        "claims per text": t["claims per text"].map(lambda v: f"{v:.1f}"), "words per text": t["words per text"].map(lambda v: f"{v:.0f}"),
        "claims false vs planted truth": t["claims false vs T, no hedges"].map(lambda v: f"{v:.1%}"),
        "cost per text": t["cost per text"].map(lambda v: "–" if pd.isna(v) else f"${v:.4f}"),
    })  # fmt: skip
    kinds = pd.DataFrame({
        "Arm": t.arm,
        **{name: t[f"{name} claims per text"].map(lambda v: f"{v:.1f}") for name in ("strength", "direction", "rank", "share", "comparison", "interaction", "jump or peak")},
        "hedges (share of claims)": t["hedge share of claims"].map(lambda v: f"{v:.1%}"),
        "every required term covered": t["texts covering every required term"].map(lambda v: f"{v:.0%}"),
        "numbers no claim checks": t["unchecked numbers per text"].map(lambda v: f"{v:.1f}"),
    })  # fmt: skip
    write("tab6_baselines", "Tab. 6: what the gate adds over its template and over a plain prompt (E3 cells, facts only; D71)",
          [("Control effectiveness and volume", control), ("Claims per text by kind, hedges, coverage and numbers", kinds)],
          f"Claude Haiku 5.5 on E3's {int(t.cells.iloc[0])} facts-only (H1) cells outside the pilot datasets (16 datasets × 2 models × 2 namings × 5 draws), every "
          "arm scored by E3's three scoring readings (extractor x3; a claim counts if two find it) and verified on the fitted model under "
          "lexicon v2. Template only: the gate's fallback text from the certified statements, without an LLM. Plain prompt: the same writer "
          "and facts with the writer's role and rules for the text, but no lexicon words, DSL, plan, verifier or repair (prompts p1). Gate off: "
          "the first draft under the gate's prompt; gate on: the released text, and by exit state. P_U: share of texts with a claim false "
          "against the fitted model, as read; 95% Wilson interval. E_U = 1 − P_U / P_U of the reference arm. Claims false vs planted "
          "truth: the share of claims other than hedges that are false against T (a hedge is about the sample, not T). Required terms: the three most "
          "important features and every pair with a share of at least 10%. Numbers no claim checks: statements with a number that no DSL "
          "form expresses (the gate's round trip fails them). Cost per text: the writer's and the gate's calls at batch prices, scoring "
          "readings not included.",
          ["p{3.6cm}rp{2.4cm}rrrrrr", "p{3.6cm}rrrrrrrp{1.6cm}p{1.6cm}p{1.6cm}"])  # fmt: skip


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
