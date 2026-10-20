# Results: which file backs which number of the paper

Every number in the working paper comes from a file below; the tables and figures are generated from them by
`experiments/tables.py`, `fig1.py` to `fig4.py` and `worked_example.py`, and `experiments/reproduce.py` re-derives all
of them (see the top-level README). Folders are versioned by what produced them: `v1`, `v2` (lexicon version), `v3-x3`
(writer prompts v3, extractor x3), `x3`/`x4` (extractor version), `l1` (the local spot check's prompts). Older
versions are kept as run; the paper reports the ones named here.

| Paper | Number | File (written by) |
|---|---|---|
| Tab. E1, abstract | confident errors, decided rate, accuracy by tier, layer, model and n | `paper/tables/tab3_e1.csv` from `e1/v2/discovery/`, `e1/v2/confirmation/`, `e1/v2/plasmode/` (`headline.csv`; `e1_lexicon.py`) |
| Tab. E1 caption | the confirmation seeds alone: oracle 0.8% and 0% | `e1/v2/confirmation/headline.csv` (released wrong plus blocked correct, over claims) |
| E2, plan level | 10,720 errors, 826 equivalent mutants, 604 controls, 3 refuted | `e2/v2/plan_discovery/`, `plan_seeds-2-3/`, `plan_plasmode/`, `by_operator.csv` summed (`e2_mutation.py`) |
| E2, M10 | 365 unlabeled mutants, verdicts by n | `e2/v2/plan_*/m10_by_n.csv` |
| E2, text level, Fig. 3 | 2,219 of 2,306 caught (96.2%); invented features 85% (x4), 36% (x3), 75% (plasmode) | `paper/tables/fig3_recall.csv` from `e2/v2/text/x3/`, `e2/v2/text/x4/`, `e2/v2/text_plasmode/x4/` (`script.csv`; `e2_text.py`) |
| E2, LLM-written errors | 93 of 95 caught | `e2/v2/text/labels/score_final.csv` (labels: `labels_pass1.json`, `review.json`, `labels_final.json`) |
| False alarms | 7.7% (x3; 7.9% with the boundary case), 14.3% (x4) of correct texts blocked | `e2/v2/text/false_alarms/score.csv`, labels in `labels.json`, `labels.csv` (`e2_false_alarms.py --score`) |
| LLM critic (D56, D61) | Luna and Sol: 95 of 95 LLM-written errors; Luna 240 of 240 scripted (M9 30 of 30; the gate 22 of 30); templates blocked 20 (Luna) and 26 (Sol) of 32; E3 released texts blocked 300 of 390 (Luna); 60 of 60 wrong blocks at p ≥ 0.9; $0.0011 and $0.0092 per text | `e2/v2/text/critic/<model>/c1/cases.csv` and `summary.csv` (`e2_critic`; pilot rounds in `pilot/r1`, `r2`); Tab. 5 in `paper/tables/tab5_critic.*`; labels of Luna's E3 flags in `critic/gpt-6-luna/c1/labels/` (`e2_critic --page`, `--score labels.json`) |
| LLM critic, E3 labels (D62) | 26 of 40 blocked texts with an error by the author's reading, 0 false alarms, 14 open; by type: 36 of 45 errors where the writer's prompt is stricter than the lexicon, 5 statements the round trip does not check (5 texts), 2 "at most" readings, 2 slips | `e2/v2/text/critic/gpt-6-luna/c1/labels/`: `labels.json` (the author's labels), `score.csv` (`e2_critic --score`), `flag_types.csv` (each flag's type, assigned by hand from the sentence, its certified claims and the critic's reason; not generated) |
| E3, Tab. E3 | Haiku 58.5% → 4.5% (E_U 0.92); H1 and H2; Sonnet 25.0% → 0%; qwen3.8:27b 28.1% → 1.6% | `paper/tables/tab4_e3.csv` from `e3/v3-x3/haiku/`, `sonnet/`, `qwen3.8-27b/` (`rows.csv`, `summary.csv`, the run traces in `runs/`; `e3_end_to_end.py`) |
| E3, labeled | 20.5% (13.0–29.5%) → 0.16%, E_U 0.99 (worst case 0.94) | `e2/v2/text/false_alarms/e3_effect.csv` (`e2_false_alarms --effect`; labels in `false_alarms/labels.json` and `false_alarms/drafts/labels.json`) |
| E3 against T | 11.6% → 7.6% (Haiku), hedges excluded | `e3/v3-x3/truth_without_hedges.csv` (`e3_truth.py`) |
| Fig. 4 | faithfulness by feature role and interaction level | `paper/tables/fig4_faithfulness.csv` from `e3/v3-x3/claims.csv` (`e3_truth.py`, `fig4.py`) |
| Spot check | 52 notices; 47% (24 of 51 scored) → 4% (2 of 52); 74 of 76 reasons; 12 without a certified reason; 6 declined by M only | `local/run/l1/summary.csv`, `rows.csv` (`local_run.py`); the local Facts in `local/facts/` |
| Worked example | 13 claims, 12 certified, 7 calls, $0.0025 | `paper/worked_example.md` from `e3/v3-x3/haiku/runs/syn-dominant-n50000-s1_XGB2_H1_d4_claude-haiku-5-5_plausible.json` |
| Abstract, cost | $10.94 for every live call ($2.17 of it the critic, pilots included); about $0.002 per Haiku run | `spend.csv` (`spend.py`, from `cache/llm/calls.jsonl`); cost per run in `tab4_e3.csv` |

Before E1 and E3, and not quoted in the paper: `acceptance/`, `smoothing/`, `recheck/` (the model settings),
`facts/null_check.csv` (the bands' null check), `calibration/` (the lexicon's calibration), `pilot/v1` to `v3`
(the writer pilots; `v3/live_x1`, `live_x2`: the extractor's), `local/pilot/` (the spot check's pilot notices).

**What the self-hosted writer's arm paid.** Its 72 run traces and `e3/v3-x3/qwen3.8-27b/rows.csv` show `spent` = $0:
an offline replay rewrote them before they were first committed. What the arm paid is in the call log: 662 Haiku
extractor requests on 17 Oct 2026, 13:11 to 16:36, $0.108 in all, of which $0.048 for the gate's own calls (the runs'
`cost`) and the rest for E3's scoring readings
(`uv run python -m verifier_gate.experiments.spend --from 2026-10-17T13:00 --to 2026-10-17T17:00`). The Haiku and
Sonnet arms keep their `spent`.
