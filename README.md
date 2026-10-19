# feasibility-symb-verific-gate-llm-explanation

Code, data and results of the working paper *Propose and Prove: A Symbolic Gate for LLM Explanations of Glass-Box
Credit Models* (draft of 19 October 2026, `paper/main.pdf`). An LLM writes an explanation of a fitted EBM or depth-2
XGBoost (XGB2) together with a plan of claims in a small DSL. A deterministic verifier checks every claim against the
fitted model and its bootstrap bands through a lexicon of truth conditions; a round trip reads the finished text back
into claims; and a gate repairs, reduces or replaces text that fails. The benchmark has a planted truth: a synthetic
tier and a plasmode tier on real credit features.

## Quick start: every number of the paper, offline, in about seven minutes

Developed and run on macOS (Apple silicon) with Python 3.13; needs Python 3.11 or later and
[uv](https://docs.astral.sh/uv/).

```
git clone https://github.com/antonpstahl/feasibility-symb-verific-gate-llm-explanation.git
cd feasibility-symb-verific-gate-llm-explanation
uv sync
gh release download facts-v1          # the Facts archive, 320 MB (or download facts-v1.tar.gz from the release page)
uv run python -m verifier_gate.experiments.facts_archive --unpack facts-v1.tar.gz
uv run python -m verifier_gate.experiments.reproduce
```

- **The Facts archive** holds what git does not: the fitted models' Facts and bootstrap draws (`cache/facts/`, 484 MB
  unpacked) and the TaiwanCredit file (`data/raw/`). `--unpack` checks every file against `cache/facts_manifest.csv`
  (size and SHA-256) before it writes anything.
- **`reproduce`** runs 30 steps, from E1 to the figures, tables and worked example, with every LLM answer read from
  the committed cache (`cache/llm/`). It sets `VERIFIER_GATE_OFFLINE`, so a request that is not in the cache stops
  the run instead of calling an API: a reproduction costs $0. At the end it compares every output under `results/`
  and `paper/` with the committed one; all should be equal. `--list` prints each step's command, `--only` and
  `--from` run a part.
- **Without the archive** the same command first refits every model from the fixed seeds (about 3–4 hours for the
  synthetic tier and 2 hours for the plasmode tier) and downloads TaiwanCredit from UCI (hash-checked). Whether
  refits are bit-identical on another platform has not been tested; `facts_archive --check` compares the Facts on
  disk with the archived ones.
- **The paper:** `cd paper && latexmk -lualatex main.tex` (LuaLaTeX with the Libertinus fonts).
- **Tests:** `uv run pytest` (440 tests, about 30 seconds). The tests that read the Facts are skipped without them,
  and the plasmode tests without TaiwanCredit in `data/raw/`; no test calls an API or downloads anything.

Which file backs which number of the paper: `results/README.md`. What D-numbers and "plan §" in the code mean:
`docs/decisions.md`.

## Running live

Every LLM call goes through `llm/client.py`, which caches each answer under its request key in `cache/llm/` and logs
every call in `cache/llm/calls.jsonl`. A run whose answers are cached costs nothing; a new model, prompt or draw is a
new request and is paid.

- **API key:** copy `.env.example` to `.env` and set `ANTHROPIC_API_KEY` (`.env` is git-ignored), and make sure
  `VERIFIER_GATE_OFFLINE` is not set.
- **Models:** the writers are Claude Haiku 5.5 (`claude-haiku-5-5`) and, in a subset, Claude Sonnet 5.5
  (`claude-sonnet-5-5`); the extractor is Haiku 5.5 throughout (`llm/settings.py`, with prices). Large runs go
  through the Batch API at half price and resume where they stopped.
- **Costs as paid:** $8.77 for every live call of the pre-study (`results/spend.csv`, by day, model and role; written
  by `python -m verifier_gate.experiments.spend` from the call log). An E3 run, with its repairs and round trips,
  cost about $0.002 with the Haiku writer and $0.018 with Sonnet (Tab. 4); E3's 792 runs cost $3.77. Price a run
  before starting it.
- **Self-hosted writer** (`--writer ollama/qwen3.8:27b` in `e3_end_to_end`): needs [Ollama](https://ollama.com) with
  `ollama pull qwen3.8:27b` (27.8B parameters in NVFP4 weights, 17.6 GB in GPU memory). On an Apple M4 Pro with 24 GB
  of memory it ran only after raising the GPU's memory limit (`sudo sysctl iogpu.wired_limit_mb=21504`, reset on
  reboot) and with a 10,240-token context (`OLLAMA_NUM_CTX`, the client's default; the writer's prompt alone is about
  5,500 tokens). The 72 runs took about 2.5 hours, a median of 51 s per writer call; the writer cost $0, and the
  extractor stayed Haiku through the API. `experiments/local_writer_smoke.py` tests one call first.

### Steps one by one

`reproduce --list` prints the commands it runs. Steps outside it, as run during the pre-study:

```
uv run python -m verifier_gate.experiments.acceptance          # acceptance checks, about 1 minute
uv run python -m verifier_gate.experiments.recheck             # the EBM setting on fresh seeds, about 15 minutes
uv run python -m verifier_gate.experiments.build_facts         # Facts for the synthetic tier, 3-4 hours, resumable
uv run python -m verifier_gate.data.plasmode                   # fetches TaiwanCredit (UCI 350), writes the 18 datasets
uv run python -m verifier_gate.experiments.build_facts --tier plasmode   # about 2 hours, resumable
uv run python -m verifier_gate.experiments.null_check          # seconds, after build_facts
uv run python -m verifier_gate.experiments.calibrate           # the lexicon's calibration, about 1.5 minutes
uv run python -m verifier_gate.experiments.acceptance_binding  # seconds
uv run python -m verifier_gate.experiments.pilot               # dry run, no network, $0 (--smoke, --live, --naming: paid)
uv run python -m verifier_gate.experiments.e3_end_to_end --dry # stub writer and extractor, 16 runs, $0
uv run python notebooks/02_root_cause.py                       # about 1.5 hours (--quick: 2 minutes)
```

## Data

- **Synthetic tier:** generated from fixed seeds (`data/dgp.py`); nothing to download.
- **Plasmode tier:** "Default of Credit Card Clients" (TaiwanCredit), UCI Machine Learning Repository, dataset 350;
  Yeh, I-Cheng (2009), https://doi.org/10.24432/C55S3H; licensed CC BY 4.0. `python -m verifier_gate.data.plasmode`
  downloads it once into `data/raw/` and checks its hash; the Facts archive includes the file unchanged. The 18
  plasmode datasets keep its feature rows (without SEX and MARRIAGE) and replace its label with a planted one.
- **LLM answers** (`cache/llm/`, about 37,000 files): every answer as received, about synthetic and plasmode data only.

## Layout

```
src/verifier_gate/
  data/          dgp.py (synthetic tier), plasmode.py (TaiwanCredit features, planted y), tiers.py (both tiers behind
                 one interface), planted.py (planted claims with labels), labels.py (the names the writer sees)
  models/        fit_ebm.py, fit_xgb2.py, fit_oracle.py (all take Poisson weights for bootstrap refits)
  facts/         steps.py (exact step terms, purification), ebm.py, xgb2.py (exact decomposition), reference.py (T and
                 the oracle), schema.py (the Facts format), build.py and bootstrap.py (bands), refits.py and local.py
                 (local facts for adverse-action reasons), readable.py (the handover's curves, checked against M),
                 symbolic.py (SymPy export)
  lexicon/       lexicon.yaml (thresholds, v2), predicates.py (three-valued verdicts with reason codes), local.py
  dsl/           grammar.py (the claim forms), parse.py (ast against a whitelist; nothing is executed)
  verifier/      verify.py (verdict and evidence per claim), certified.py (the most specific certified statements)
  llm/           client.py (cache, call log, offline switch, retries, the local Ollama transport), batch.py (Batch API),
                 settings.py (models and prices), handover.py, handover_local.py, propose.py, extract.py (the round
                 trip's readings), prompts/ (frozen and hash-tested)
  gate/          gate.py (repair loop, stop rules, exit states), roundtrip.py, advice.py, draft.py, template.py
  experiments/   reproduce.py (every number, offline), facts_archive.py, spend.py;
                 E1: calibrate.py, e1_lexicon.py; E2: e2_mutation.py (plan level), e2_text.py (text level),
                 e2_labels.py and e2_false_alarms.py (labeling pages, false alarms, labeled re-scores);
                 E3: e3_end_to_end.py, e3_truth.py; local spot check: local_refits.py, local_facts.py, local_run.py;
                 fig1.py to fig4.py, tables.py, worked_example.py; acceptance, recheck, smoothing, null check, pilot
tests/           one file per module; conftest.py clears the offline switch
notebooks/       01 recovery check, 02 root causes of the week-1 failures, 03 what the bands can decide,
                 04 the extractor on hand-written sentences that name features the model lacks
piml_check/      our XGB2 decomposition against PiML's (own Python 3.10 environment, see its README)
docs/            decisions.md: the design decisions, the freeze tags, the plan sections cited in the code
data/            raw/ (TaiwanCredit), synthetic/, plasmode/: not tracked
cache/           llm/ (every LLM answer and the call log, tracked), facts/ (not tracked: the archive),
                 facts_manifest.csv (the archive's files and hashes)
results/         every result as run, by experiment and version (results/README.md)
paper/           main.tex, main.pdf, references.bib, worked_example.md, figures/, tables/ (all generated)
```

## License

Code: MIT (`LICENSE`). The TaiwanCredit data: CC BY 4.0 (above).
