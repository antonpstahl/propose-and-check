"""E3's text-level error against T (D66; review M1, fix 6), by claim form. No API call, $0.

A text is wrong against T if it states at least one claim, other than a hedge, that is false against the planted
truth (a hedge is a statement about the evidence in one sample, not about T: e3_truth). Claims are what the scoring
readings find (experiments/e3_truth.py, claims.csv): first drafts (gate off) and released texts (gate on, templates
included), Claude Haiku 5.5, outside the two synthetic pilot datasets. Three sources:

- "as run, v2": E3 as run (results/e3/v3-x3), its claims verified against T under lexicon v2, as reported;
- "as run, v3": the same texts and claims verified against T under lexicon v3, which separates the change of the
  words' meaning from the change of the texts;
- "rerun, v3": the rerun after the review (D66; results/e3/v4-x5-m5): lexicon v3, prompts v4, extractor x5, both
  tiers.

Per source, tier and arm: texts, the share wrong against T with a 95% interval from a bootstrap over the datasets
(2,000 resamples, seed 0), and the share of claims false against T; by model and n; and by claim form (the kind and
whether it is a single value, a set, a "mostly" word or a strict word), the share of texts with a false claim of
that form and its share of all false claims. top_claims.csv lists the claims most often false against T.

Run: `uv run python -m verifier_gate.experiments.e3_text_error` (after e3_truth for each source). Writes
results/e3/text_error/: summary.csv, by_model_n.csv, by_form.csv, top_claims.csv, report.md.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from verifier_gate.data import tiers
from verifier_gate.dsl.grammar import HEDGE
from verifier_gate.dsl.parse import parse
from verifier_gate.experiments.build_facts import load
from verifier_gate.experiments.e3_end_to_end import PILOT, RESULTS
from verifier_gate.experiments.tables import markdown
from verifier_gate.lexicon import predicates as p
from verifier_gate.verifier.verify import verify

AS_RUN, RERUN = "v3-x3", "v4-x5-m5"
OUT = RESULTS / "text_error"
WRITER = "haiku"
RESAMPLES = 2_000


def form(line: str) -> str:
    """A claim's form: its kind, and for a direction or strength whether it is a strict word, a "mostly" word or a
    set."""
    c = parse(line)
    if c.kind == HEDGE:
        return "hedge"
    if c.kind == "direction":
        return "direction, set (generally)" if isinstance(c.value, tuple) else "direction, mostly" if c.value.startswith("mostly") else "direction, strict"
    if c.kind in ("strength", "rank") and isinstance(c.value, tuple):
        return f"{c.kind}, set"
    if c.kind == "interaction":
        return f"interaction, {c.value}"
    return c.kind


def scenario_of(run: str) -> str:
    return run.split("_")[0]


def claims_of(source: str, lex: p.Lexicon | None) -> pd.DataFrame:
    """The source's claims (claims.csv), Haiku, outside the pilot datasets; with `lex`, re-verified against T under
    it."""
    claims = pd.read_csv(RESULTS / source / "claims.csv")
    claims = claims[(claims.writer == WRITER) & ~claims.scenario.isin(PILOT)].copy()
    if lex is not None:
        truths = {s: load(tiers.scenario(s), "T") for s in claims.scenario.unique()}
        claims["verdict T"] = [verify(line, truths[s], lex).value for line, s in zip(claims.dsl, claims.scenario)]
    claims["form"] = claims.dsl.map(form)
    claims["tier"] = claims.scenario.map(lambda s: tiers.name(tiers.scenario(s)))
    claims["false T"] = (claims["verdict T"] == p.FALSE) & ~claims.hedge.astype(bool)
    return claims


def texts_of(source: str, claims: pd.DataFrame) -> pd.DataFrame:
    """One row per scored text: its tier, model, n, and whether it states a claim false against T."""
    rows = pd.read_csv(RESULTS / source / "truth_rows.csv")
    rows = rows[(rows.writer == WRITER) & rows.scored.astype(bool)].copy()
    rows["scenario"] = rows.run.map(scenario_of)
    rows = rows[~rows.scenario.isin(PILOT)]
    wrong = claims[claims["false T"]].groupby(["run", "arm"]).size()
    rows["false claims"] = [int(wrong.get((r, a), 0)) for r, a in zip(rows.run, rows.arm)]
    rows["wrong"] = rows["false claims"] > 0
    rows["non-hedge claims"] = rows.claims - rows.hedges
    rows["tier"] = rows.scenario.map(lambda s: tiers.name(tiers.scenario(s)))
    rows["model"] = rows.run.map(lambda r: r.split("_")[1])
    rows["n"] = rows.scenario.map(lambda s: tiers.scenario(s).n)
    return rows


def interval(texts: pd.DataFrame, seed: int = 0) -> tuple[float, float]:
    """95% interval of the share of wrong texts, from a bootstrap over the datasets."""
    by = texts.groupby("scenario").wrong.agg(["sum", "count"])
    if len(by) < 2:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    pick = rng.integers(0, len(by), size=(RESAMPLES, len(by)))
    shares = by["sum"].to_numpy()[pick].sum(axis=1) / by["count"].to_numpy()[pick].sum(axis=1)
    return float(np.quantile(shares, 0.025)), float(np.quantile(shares, 0.975))


def summary(texts: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    out = []
    for key, part in texts.groupby(by):
        low, high = interval(part)
        out.append(dict(zip(by, key if isinstance(key, tuple) else (key,))) | {
            "texts": len(part), "wrong vs T": round(float(part.wrong.mean()), 3), "low": round(low, 3), "high": round(high, 3),
            "claims false vs T": round(float(part["false claims"].sum() / max(part["non-hedge claims"].sum(), 1)), 3),
            "claims per text": round(float(part["non-hedge claims"].mean()), 1),
        })  # fmt: skip
    return pd.DataFrame(out)


def by_form(claims: pd.DataFrame, texts: pd.DataFrame) -> pd.DataFrame:
    """Per source, tier, arm and claim form: the share of texts with a false claim of that form, and the form's
    share of all false claims."""
    out = []
    keys = ["source", "tier", "arm"]
    scored = texts.set_index(["source", "run", "arm"]).index
    claims = claims[pd.MultiIndex.from_frame(claims[["source", "run", "arm"]]).isin(scored)]
    for key, part in claims[claims["false T"]].groupby(keys):
        n_texts = int(((texts.source == key[0]) & (texts.tier == key[1]) & (texts.arm == key[2])).sum())
        total = len(part)
        for f, group in part.groupby("form"):
            out.append(dict(zip(keys, key)) | {"form": f, "texts with one": round(group[["run"]].drop_duplicates().shape[0] / n_texts, 3),
                                                "false claims": len(group), "of all false claims": round(len(group) / total, 3)})  # fmt: skip
    return pd.DataFrame(out).sort_values(keys + ["false claims"], ascending=[True, True, True, False])


def main() -> None:
    sources = {"as run, v2": (AS_RUN, None), "as run, v3": (AS_RUN, p.load(p.VERSIONS["v3"])), "rerun, v3": (RERUN, None)}
    all_claims, all_texts = [], []
    for name, (folder, lex) in sources.items():
        if not (RESULTS / folder / "claims.csv").exists():
            print(f"{name}: no claims.csv in {folder}; run e3_truth --source {folder} first")
            continue
        claims = claims_of(folder, lex).assign(source=name)
        all_claims.append(claims)
        all_texts.append(texts_of(folder, claims).assign(source=name))
    claims, texts = pd.concat(all_claims), pd.concat(all_texts)
    OUT.mkdir(parents=True, exist_ok=True)
    head = summary(texts, ["source", "tier", "arm"])
    model_n = summary(texts, ["source", "tier", "arm", "model", "n"])
    forms = by_form(claims, texts)
    top = (claims[claims["false T"]].groupby(["source", "tier", "arm", "dsl"]).run.nunique().rename("texts").reset_index()
           .sort_values(["source", "tier", "arm", "texts"], ascending=[True, True, True, False]).groupby(["source", "tier", "arm"]).head(8))  # fmt: skip
    head.to_csv(OUT / "summary.csv", index=False)
    model_n.to_csv(OUT / "by_model_n.csv", index=False)
    forms.to_csv(OUT / "by_form.csv", index=False)
    top.to_csv(OUT / "top_claims.csv", index=False)
    report = ["# E3: the text-level error against T", "", "Texts with at least one claim false against T (hedges excluded), Claude Haiku 5.5, "
              "outside the pilot datasets; 95% interval from a bootstrap over the datasets.", "", markdown(head), "",
              "## By model and n", "", markdown(model_n), "", "## By claim form", "", markdown(forms), "",
              "## The claims most often false against T", "", markdown(top), ""]  # fmt: skip
    (OUT / "report.md").write_text("\n".join(report))
    pd.set_option("display.width", 250)
    print(head.to_string(index=False))
    print(f"\nwritten to {OUT}")


if __name__ == "__main__":
    main()
