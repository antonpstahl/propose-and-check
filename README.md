# feasibility-symb-verific-gate-llm-explanation

Pre-study for the working paper *Propose and Prove: A Symbolic Gate for LLM Explanations of Glass-Box Credit Models*. An LLM writes an explanation of a fitted EBM or XGB2 together with a plan of claims in a small DSL. A deterministic verifier checks every claim against the fitted model through a semantic lexicon, and a gate repairs, reduces or replaces text that fails. The benchmark uses synthetic and plasmode data with planted truth.

## Layout

```
src/verifier_gate/
  data/          dgp.py (synthetic tier), plasmode.py (TaiwanCredit features, planted y)
  models/        fit_ebm.py, fit_xgb2.py (both take Poisson weights for bootstrap refits)
  facts/         steps.py (exact step terms, shared purification), ebm.py, xgb2.py (tree decomposition),
                 schema.py (Facts format, JSON + draws), build.py (frame, bands), bootstrap.py (Poisson refits),
                 symbolic.py (SymPy export)
  lexicon/       lexicon.yaml (thresholds, frozen after discovery), predicates.py
  dsl/           grammar.py (whitelist), parse.py (ast-based)
  verifier/      verify.py (verdict + evidence per claim)
  llm/           client.py (cache, stub mode, retries), propose.py, extract.py, prompts/
  gate/          roundtrip.py, template.py, gate.py (repair loop, stop rules, exit states)
  experiments/   acceptance.py (models vs planted claims, model vs data misses), smoothing.py (EBM setting),
                 recheck.py (EBM setting on fresh seeds), build_facts.py (Facts for all 36 models),
                 null_check.py (bands on the noise features), fig2.py, e1_lexicon.py, e2_mutation.py,
                 e3_end_to_end.py
tests/           DGP, acceptance scorer, decision rules, both fact providers, Facts and bands, SymPy export
notebooks/       01 recovery check, 02 root causes of the week-1 failures (plan §14.2)
data/            raw/, synthetic/, plasmode/ (not tracked, regenerated from seeds)
cache/           llm/ (every LLM call), facts/ (Facts and bootstrap draws, not tracked)
results/         acceptance/, smoothing/, recheck/, facts/, e1/, e2/, e3/ raw results
paper/           working paper, figures/, tables/
```

## Setup

```
uv sync
uv run pytest                                                  # about 15 seconds
uv run python -m verifier_gate.experiments.acceptance          # about 1 minute
uv run python -m verifier_gate.experiments.recheck             # about 15 minutes
uv run python -m verifier_gate.experiments.build_facts         # about 3-4 hours, resumable
uv run python -m verifier_gate.experiments.null_check          # seconds, after build_facts
uv run python -m verifier_gate.experiments.fig2                # seconds, after build_facts
uv run python notebooks/02_root_cause.py                       # about 1.5 hours (--quick: 2 minutes)
```
