# feasibility-symb-verific-gate-llm-explanation

Pre-study for the working paper *Propose and Prove: A Symbolic Gate for LLM Explanations of Glass-Box Credit Models*. An LLM writes an explanation of a fitted EBM or XGB2 together with a plan of claims in a small DSL. A deterministic verifier checks every claim against the fitted model through a semantic lexicon, and a gate repairs, reduces or replaces text that fails. The benchmark uses synthetic and plasmode data with planted truth.

## Layout

```
src/verifier_gate/
  data/          dgp.py (synthetic tier), planted.py (planted claims with labels: E1, scorer test),
                 labels.py (the names and descriptions the writer sees), plasmode.py (TaiwanCredit features, planted y)
  models/        fit_ebm.py, fit_xgb2.py, fit_oracle.py (all take Poisson weights for bootstrap refits)
  facts/         steps.py (exact step terms, shared purification), ebm.py, xgb2.py (tree decomposition),
                 reference.py (T and the oracle on a fine grid), schema.py (Facts format, JSON + draws),
                 build.py (frame, bands), bootstrap.py (Poisson refits), symbolic.py (SymPy export),
                 readable.py (the readable form of a curve for the handover, and its check against M)
  lexicon/       lexicon.yaml (thresholds, v1: frozen 14 Oct, tag e1-frozen), predicates.py (three-valued verdicts
                 with reason codes, sets of values, the unsettled hedge)
  dsl/           grammar.py (whitelist, Claim; sets of values, unsettled), parse.py (ast-based)
  verifier/      verify.py (verdict + evidence per claim), certified.py (the most specific certified statement
                 per term: correct plans for E2, later H2 and the template)
  llm/           settings.py (models, thinking, prices), client.py (disk cache, call log, stub mode, retries),
                 handover.py (H1, H2), prompts/ (system, propose, repair; frozen after the pilot), propose.py,
                 extract.py (week 6)
  gate/          draft.py, roundtrip.py (coverage built; extraction and emphasis in week 6), template.py (phrases
                 and the template text), gate.py (the state machine: repair loop, stop rules, exit states; resumable)
  experiments/   acceptance.py (stand-in checks: models vs planted claims, model vs data misses),
                 acceptance_binding.py (the binding run on the frozen lexicon, D24), smoothing.py (EBM setting),
                 recheck.py (EBM setting on fresh seeds), build_facts.py (Facts for all 36 models, the oracle
                 and T),
                 null_check.py (bands on the noise features), fig2.py, metrics.py (outcomes and metrics for
                 three-valued verdicts, shared by E1 to E3), calibrate.py (lexicon calibration on the discovery
                 seed, +-50% sensitivity; plan §14.9), e1_lexicon.py (E1: three references, D31 metrics),
                 e2_mutation.py (M1-M11, plan level), pilot.py (dry run, smoke test, live pilot), e3_end_to_end.py
tests/           DGP, acceptance scorer, decision rules, both fact providers, Facts and bands, SymPy export,
                 lexicon predicates on toy shapes, DSL parser, reference Facts, scorer test (lexicon on T),
                 metrics, calibration rule, E1 scorers and the binding rule, certified plans, coverage, mutation
                 operators, readable form, LLM client (stub mode), prompts and handover, template, gate
notebooks/       01 recovery check, 02 root causes of the week-1 failures (plan §14.2),
                 03 what the bootstrap bands can decide (plan §14.4)
piml_check/      our XGB2 decomposition vs PiML's (plan §14.4, D27); own Python 3.10 environment, see its README
data/            raw/, synthetic/, plasmode/ (not tracked, regenerated from seeds)
cache/           llm/ (every LLM call), facts/ (Facts and bootstrap draws, not tracked)
results/         acceptance/, smoothing/, recheck/, facts/, calibration/, e1/, e2/, e3/ raw results
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
uv run python -m verifier_gate.experiments.calibrate           # about 1.5 minutes, after build_facts
uv run python -m verifier_gate.experiments.e1_lexicon          # seconds, after build_facts (--seeds 2,3: confirmation)
uv run python -m verifier_gate.experiments.acceptance_binding  # seconds, after build_facts
uv run python -m verifier_gate.experiments.e2_mutation         # seconds, after build_facts (plan level)
uv run python -m verifier_gate.experiments.pilot               # dry run, no network, $0
uv run python -m verifier_gate.experiments.pilot --smoke       # 2 live calls (needs ANTHROPIC_API_KEY), < $0.01
uv run python -m verifier_gate.experiments.pilot --live        # the 10 pilot traces, about $0.01-0.05
uv run python notebooks/02_root_cause.py                       # about 1.5 hours (--quick: 2 minutes)
uv run python notebooks/03_bands.py                            # seconds, after build_facts
```
