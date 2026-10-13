# feasibility-symb-verific-gate-llm-explanation

Pre-study for the working paper *Propose and Prove: A Symbolic Gate for LLM Explanations of Glass-Box Credit Models*. An LLM writes an explanation of a fitted EBM or XGB2 together with a plan of claims in a small DSL. A deterministic verifier checks every claim against the fitted model through a semantic lexicon, and a gate repairs, reduces or replaces text that fails. The benchmark uses synthetic and plasmode data with planted truth.

## Layout

```
src/verifier_gate/
  data/          dgp.py (synthetic tier), plasmode.py (TaiwanCredit features, planted y)
  models/        fit_ebm.py, fit_xgb2.py
  facts/         schema.py (Facts interface), ebm.py, xgb2.py, symbolic.py (SymPy export)
  lexicon/       lexicon.yaml (thresholds, frozen after discovery), predicates.py
  dsl/           grammar.py (whitelist), parse.py (ast-based)
  verifier/      verify.py (verdict + evidence per claim)
  llm/           client.py (cache, stub mode, retries), propose.py, extract.py, prompts/
  gate/          roundtrip.py, template.py, gate.py (repair loop, stop rules, exit states)
  experiments/   acceptance.py (models vs planted claims), smoothing.py (EBM setting),
                 e1_lexicon.py, e2_mutation.py, e3_end_to_end.py
tests/           DGP, purified EBM terms, acceptance scorer; later predicates, parser
notebooks/       exploration
data/            raw/, synthetic/, plasmode/ (not tracked, regenerated from seeds)
cache/llm/       every LLM call, cached to disk
results/         e1/, e2/, e3/ raw results
paper/           working paper, figures/, tables/
```

## Setup

```
uv sync
uv run pytest
uv run python -m verifier_gate.experiments.acceptance   # about 1 minute
```
