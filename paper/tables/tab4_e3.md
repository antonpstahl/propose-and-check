# Tab. 4: survival, control effectiveness and cost (E3, D36)

| Writer, setting | runs | released / reduced / template / escalate | repair rounds (mean) | P_U before | P_U after | E_U | cost per run |
|---|---|---|---|---|---|---|---|
| Claude Haiku 5.5, global (E3) | 640 | 49% / 12% / 39% / 0% | 1.27 | 58.5% | 4.5% | 0.92 | $0.0023 |
| Claude Haiku 5.5, global, with author-reviewed labels | 40 drafts, all released texts with a false claim |  |  | 20.5% (95% interval 13.0%–29.5%) | 0.16% | 0.99 (worst case 0.94) |  |
| Claude Haiku 5.5, global, facts only (H1) | 320 | 27% / 9% / 64% / 0% | 1.46 | 81.9% | 4.7% | 0.94 | $0.0021 |
| Claude Haiku 5.5, global, with certified statements (H2) | 320 | 72% / 14% / 14% / 0% | 1.08 | 35.1% | 4.4% | 0.88 | $0.0026 |
| Claude Sonnet 5.5, global (E3 subset) | 64 | 88% / 8% / 5% / 0% | 0.78 | 25.0% | 0.0% | 1.00 | $0.0184 |
| qwen3.8:27b (NVFP4), self-hosted, global (E3 subset) | 64 | 89% / 6% / 5% / 0% | 0.86 | 28.1% | 1.6% | 0.94 | $0.0006 |
| Claude Haiku 5.5, adverse-action notices (local spot check) | 52 | 62% / 27% / 12% / 0% | 1.31 | 47.1% | 3.8% | 0.92 | $0.0011 |

Outside the pilot datasets and the pilot notices. P_U: share of texts with a claim false against the fitted model, as read by three scoring readings apart from the gate's (a claim counts if two find it); before = the writer's first draft, after = the released text; E_U = 1 − P_U after / P_U before. With author-reviewed labels, most false claims in released texts are misreadings by the scoring readings. H1: the facts only; H2: the facts and the statements the verifier certifies. Cost per run: every call of the trace at its price when made (batch prices for E3).
