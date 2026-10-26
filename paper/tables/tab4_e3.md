# Tab. 4: survival, control effectiveness and cost (E3, D36)

**E3 with D74's fixes: Claude Haiku 5.5, lexicon v3, writer prompts v4, extractor x5**

| Tier, texts | runs | released / reduced / template / escalate | repair rounds (mean) | P_U before | P_U after | E_U | cost per run |
|---|---|---|---|---|---|---|---|
| synthetic, global | 640 | 60% / 11% / 29% / 0% | 1.15 | 45.4% | 2.5% | 0.94 | $0.0023 |
| synthetic, facts only (H1) | 320 | 33% / 14% / 52% / 0% | 1.62 | 67.8% | 3.4% | 0.95 | $0.0023 |
| synthetic, with certified statements (H2) | 320 | 86% / 7% / 7% / 0% | 0.68 | 22.8% | 1.6% | 0.93 | $0.0022 |
| plasmode, global | 360 | 36% / 10% / 54% / 0% | 1.27 | 42.3% | 8.1% | 0.81 | $0.0027 |
| plasmode, facts only (H1) | 180 | 7% / 10% / 83% / 0% | 1.66 | 60.3% | 8.9% | 0.85 | $0.0025 |
| plasmode, with certified statements (H2) | 180 | 64% / 9% / 26% / 0% | 0.89 | 24.4% | 7.2% | 0.70 | $0.0029 |
| synthetic, adverse-action notices | 52 | 88% / 4% / 8% / 0% | 0.38 | 17.6% | 7.8% | 0.56 | $0.0005 |
| plasmode, adverse-action notices | 54 | 87% / 7% / 6% / 0% | 0.48 | 24.1% | 0.0% | 1.00 | $0.0007 |

**The residual of D74 by reference and standard**

| Tier, standard | Read by | P_U before | P_U after | of LLM-written texts | of templates | E_U |
|---|---|---|---|---|---|---|
| synthetic, refuted | Claude Haiku 5.5 (the gate's extractor, x5) | 45.4% (38.9%–51.5%) | 2.5% (1.4%–3.9%) | 3.5% (2.0%–5.3%) | 0.0% (0.0%–0.0%) | 0.94 (0.90 to 0.97) |
| synthetic, refuted | GPT-6 Luna (another vendor) | 26.9% (22.2%–31.4%) | 0.6% (0.2%–1.1%) | 0.7% (0.0%–1.4%) | 0.5% (0.0%–1.7%) | 0.98 (0.95 to 0.99) |
| synthetic, refuted | either reader | 45.9% (39.6%–52.0%) | 3.0% (1.9%–4.2%) | 4.0% (2.6%–5.6%) | 0.5% (0.0%–1.7%) | 0.94 (0.90 to 0.96) |
| synthetic, refuted | blind labels, one rater (40 texts) | 27.8% (12.5%–50.9%), 5 of 18 | 16.6% (4.2%–33.2%) | 4 of 17 | 0 of 7 | 0.40 (-1.24 to 0.88) |
| synthetic, release rule | Claude Haiku 5.5 (the gate's extractor, x5) | 69.7% (65.2%–74.3%) | 5.2% (3.6%–7.0%) | 6.9% (4.8%–9.1%) | 1.1% (0.0%–2.8%) | 0.93 (0.90 to 0.95) |
| synthetic, release rule | GPT-6 Luna (another vendor) | 61.6% (58.0%–65.2%) | 5.2% (3.3%–7.2%) | 7.1% (4.6%–9.8%) | 0.5% (0.0%–1.7%) | 0.92 (0.88 to 0.94) |
| synthetic, release rule | either reader | 70.3% (65.9%–75.0%) | 8.9% (6.6%–11.5%) | 12.0% (8.7%–15.2%) | 1.6% (0.0%–3.5%) | 0.87 (0.83 to 0.91) |
| synthetic, release rule | blind labels, one rater (40 texts) | 66.7% (43.8%–83.7%), 12 of 18 | 41.8% (25.1%–58.5%) | 5 of 17 | 5 of 7 | 0.37 (-0.09 to 0.66) |
| plasmode, refuted | Claude Haiku 5.5 (the gate's extractor, x5) | 42.3% (33.7%–52.6%) | 8.1% (1.9%–16.0%) | 2.4% (0.6%–4.7%) | 12.8% (0.6%–26.9%) | 0.81 (0.64 to 0.95) |
| plasmode, refuted | GPT-6 Luna (another vendor) | 28.1% (18.3%–39.3%) | 5.9% (3.4%–8.6%) | 1.2% (0.0%–2.9%) | 9.7% (5.5%–14.4%) | 0.79 (0.64 to 0.89) |
| plasmode, refuted | either reader | 44.6% (36.2%–54.2%) | 13.9% (8.1%–21.2%) | 3.7% (1.3%–6.2%) | 22.6% (12.2%–34.6%) | 0.69 (0.53 to 0.81) |
| plasmode, release rule | Claude Haiku 5.5 (the gate's extractor, x5) | 68.2% (62.8%–74.3%) | 9.2% (3.0%–17.4%) | 3.7% (1.3%–6.0%) | 13.9% (1.6%–28.0%) | 0.87 (0.75 to 0.96) |
| plasmode, release rule | GPT-6 Luna (another vendor) | 60.5% (55.7%–66.0%) | 7.2% (4.7%–10.1%) | 4.3% (1.2%–8.1%) | 9.7% (5.5%–14.4%) | 0.88 (0.83 to 0.92) |
| plasmode, release rule | either reader | 69.1% (63.6%–74.9%) | 15.9% (10.6%–22.6%) | 7.3% (3.7%–11.3%) | 23.1% (12.8%–34.9%) | 0.77 (0.68 to 0.84) |

**E3's first run: lexicon v2, writer prompts v3, extractor x3 (synthetic tier)**

| Writer, setting | runs | released / reduced / template / escalate | repair rounds (mean) | P_U before | P_U after | E_U | cost per run |
|---|---|---|---|---|---|---|---|
| Claude Haiku 5.5 | 640 | 49% / 12% / 39% / 0% | 1.27 | 58.5% | 4.5% | 0.92 | $0.0023 |
| Claude Sonnet 5.5 (subset) | 64 | 88% / 8% / 5% / 0% | 0.78 | 25.0% | 0.0% | 1.00 | $0.0184 |
| qwen3.8:27b, self-hosted (subset) | 64 | 89% / 6% / 5% / 0% | 0.86 | 28.1% | 1.6% | 0.94 | $0.0006 |

Outside the pilot datasets and the pilot notices. P_U: share of texts with a claim false against the fitted model (refuted), or false or stated as settled where the facts leave it open (release rule); before = the writer's first draft, after = the released text; E_U = 1 − P_U after / P_U before. In the first and third parts, P_U is as read by E3's three scoring readings (the gate's extractor request, replicas 3 to 5; a claim counts if two find it). In the second, intervals for the readers come from a bootstrap over the datasets; for the blind labels, Wilson intervals per stratum, P_U after weighted by the strata's population sizes, and E_U from a stratified bootstrap. Cost per run: every call of the trace at its price when made (batch prices).
