# feasibility-symb-verific-gate-llm-explanation

Pre-study for the working paper *Propose and Prove: A Symbolic Gate for LLM Explanations of Glass-Box Credit Models*. An LLM writes an explanation of a fitted EBM or XGB2 together with a plan of claims in a small DSL. A deterministic verifier checks every claim against the fitted model through a semantic lexicon, and a gate repairs, reduces or replaces text that fails. The benchmark uses synthetic and plasmode data with planted truth.

## Layout

```
src/verifier_gate/
  data/          dgp.py (synthetic tier), planted.py (planted claims with labels: E1, scorer test),
                 plasmode.py (TaiwanCredit features, planted y)
  models/        fit_ebm.py, fit_xgb2.py, fit_oracle.py (all take Poisson weights for bootstrap refits)
  facts/         steps.py (exact step terms, shared purification), ebm.py, xgb2.py (tree decomposition),
                 reference.py (T and the oracle on a fine grid), schema.py (Facts format, JSON + draws),
                 build.py (frame, bands), bootstrap.py (Poisson refits), symbolic.py (SymPy export)
  lexicon/       lexicon.yaml (thresholds, v0; frozen after calibration), predicates.py (three-valued verdicts
                 with reason codes, sets of values, the unsettled hedge)
  dsl/           grammar.py (whitelist, Claim; sets of values, unsettled), parse.py (ast-based)
  verifier/      verify.py (verdict + evidence per claim)
  llm/           client.py (cache, stub mode, retries), propose.py, extract.py, prompts/
  gate/          roundtrip.py, template.py, gate.py (repair loop, stop rules, exit states)
  experiments/   acceptance.py (models vs planted claims, model vs data misses), smoothing.py (EBM setting),
                 recheck.py (EBM setting on fresh seeds), build_facts.py (Facts for all 36 models, the oracle
                 and T),
                 null_check.py (bands on the noise features), fig2.py, metrics.py (outcomes and metrics for
                 three-valued verdicts, shared by E1 to E3), e1_lexicon.py, e2_mutation.py, e3_end_to_end.py
tests/           DGP, acceptance scorer, decision rules, both fact providers, Facts and bands, SymPy export,
                 lexicon predicates on toy shapes, DSL parser, reference Facts, scorer test (lexicon on T),
                 metrics
notebooks/       01 recovery check, 02 root causes of the week-1 failures (plan §14.2),
                 03 what the bootstrap bands can decide (plan §14.4)
piml_check/      our XGB2 decomposition vs PiML's (plan §14.4, D27); own Python 3.10 environment, see its README
data/            raw/, synthetic/, plasmode/ (not tracked, regenerated from seeds)
cache/           llm/ (every LLM call), facts/ (Facts and bootstrap draws, not tracked)
results/         acceptance/, smoothing/, recheck/, facts/, e1/, e2/, e3/ raw results
paper/           working paper, figures/, tables/
```

## Setup

```
uv sync
uv run pytest                                                  # about 20 seconds
uv run python -m verifier_gate.experiments.acceptance          # about 1 minute
uv run python -m verifier_gate.experiments.recheck             # about 15 minutes
uv run python -m verifier_gate.experiments.build_facts         # about 3-4 hours, resumable (oracle and T: minutes)
uv run python -m verifier_gate.experiments.null_check          # seconds, after build_facts
uv run python -m verifier_gate.experiments.fig2                # seconds, after build_facts
uv run python notebooks/02_root_cause.py                       # about 1.5 hours (--quick: 2 minutes)
uv run python notebooks/03_bands.py                            # seconds, after build_facts
```
