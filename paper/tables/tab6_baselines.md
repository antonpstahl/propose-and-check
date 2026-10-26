# Tab. 6: what the gate adds over its template and over a plain prompt (facts-only cells; D71, D76)

**Control effectiveness and volume**

| Tier | Arm | texts | P_U (95% interval) | E_U vs gate off | E_U vs plain prompt | claims per text | words per text | claims false vs planted truth | cost per text |
|---|---|---|---|---|---|---|---|---|---|
| synthetic | Template only (no LLM) | 320 | 0.0% (0.0%–1.2%) | 1.00 | 1.00 | 15.9 | 196 | 0.6% | $0.0000 |
| synthetic | Plain prompt (no gate) | 319 | 93.1% (89.8%–95.4%) | -0.37 | 0.00 | 21.1 | 248 | 26.8% | $0.0003 |
| synthetic | Gate off (first draft) | 320 | 67.8% (62.5%–72.7%) | 0.00 | 0.27 | 15.9 | 176 | 11.6% | – |
| synthetic | Gate on (released text) | 320 | 3.4% (1.9%–6.0%) | 0.95 | 0.96 | 14.6 | 183 | 0.9% | $0.0023 |
| synthetic |   gate on: released as written | 107 | 8.4% (4.5%–15.2%) | 0.88 | 0.91 | 14.3 | 187 | 0.8% | $0.0023 |
| synthetic |   gate on: released reduced | 46 | 4.3% (1.2%–14.5%) | 0.94 | 0.95 | 11.9 | 153 | 1.3% | $0.0028 |
| synthetic |   gate on: template | 167 | 0.0% (0.0%–2.2%) | 1.00 | 1.00 | 15.5 | 190 | 0.8% | $0.0023 |
| plasmode | Template only (no LLM) | 179 | 8.4% (5.1%–13.4%) | 0.86 | 0.88 | 15.2 | 196 | 13.3% | $0.0000 |
| plasmode | Plain prompt (no gate) | 179 | 71.0% (63.9%–77.1%) | -0.18 | 0.00 | 18.7 | 275 | 36.1% | $0.0003 |
| plasmode | Gate off (first draft) | 179 | 60.3% (53.0%–67.2%) | 0.00 | 0.15 | 15.2 | 197 | 23.6% | – |
| plasmode | Gate on (released text) | 179 | 8.9% (5.6%–14.0%) | 0.85 | 0.87 | 14.7 | 194 | 13.2% | $0.0025 |
| plasmode |   gate on: released as written | 13 | 0.0% (0.0%–22.8%) | 1.00 | 1.00 | 14.6 | 216 | 11.7% | $0.0026 |
| plasmode |   gate on: released reduced | 18 | 5.6% (1.0%–25.8%) | 0.91 | 0.92 | 10.9 | 158 | 14.6% | $0.0032 |
| plasmode |   gate on: template | 148 | 10.1% (6.2%–16.1%) | 0.83 | 0.86 | 15.1 | 196 | 13.2% | $0.0024 |

**Claims per text by kind, hedges, coverage and numbers**

| Tier | Arm | strength | direction | rank | share | comparison | interaction | jump or peak | hedges (share of claims) | every required term covered | numbers no claim checks |
|---|---|---|---|---|---|---|---|---|---|---|---|
| synthetic | Template only (no LLM) | 9.0 | 5.4 | 0.0 | 0.0 | 0.0 | 0.8 | 0.7 | 0.0% | 100% | 0.0 |
| synthetic | Plain prompt (no gate) | 5.6 | 4.1 | 2.4 | 2.5 | 0.5 | 2.0 | 1.8 | 10.3% | 67% | 2.1 |
| synthetic | Gate off (first draft) | 5.0 | 4.5 | 2.8 | 0.3 | 0.0 | 1.3 | 0.6 | 8.4% | 99% | 0.1 |
| synthetic | Gate on (released text) | 6.2 | 4.4 | 1.4 | 0.1 | 0.0 | 0.7 | 0.4 | 9.2% | 100% | 0.0 |
| synthetic |   gate on: released as written | 3.4 | 3.4 | 3.0 | 0.2 | 0.0 | 0.9 | 0.2 | 21.9% | 100% | 0.0 |
| synthetic |   gate on: released reduced | 2.6 | 3.5 | 2.9 | 0.1 | 0.1 | 0.5 | 0.2 | 16.8% | 100% | 0.0 |
| synthetic |   gate on: template | 9.0 | 5.3 | 0.0 | 0.0 | 0.0 | 0.6 | 0.6 | 0.0% | 100% | 0.0 |
| plasmode | Template only (no LLM) | 9.0 | 5.0 | 0.0 | 0.0 | 0.0 | 0.7 | 0.5 | 0.0% | 100% | 0.0 |
| plasmode | Plain prompt (no gate) | 4.7 | 3.7 | 2.3 | 2.2 | 0.1 | 1.8 | 1.3 | 13.4% | 32% | 2.9 |
| plasmode | Gate off (first draft) | 4.9 | 4.0 | 2.4 | 0.3 | 0.0 | 1.1 | 0.5 | 12.9% | 93% | 0.4 |
| plasmode | Gate on (released text) | 8.1 | 4.7 | 0.4 | 0.0 | 0.0 | 0.7 | 0.4 | 2.5% | 100% | 0.0 |
| plasmode |   gate on: released as written | 4.7 | 4.1 | 2.4 | 0.0 | 0.0 | 1.1 | 0.2 | 14.2% | 100% | 0.1 |
| plasmode |   gate on: released reduced | 2.7 | 2.8 | 2.3 | 0.0 | 0.1 | 0.6 | 0.2 | 19.9% | 100% | 0.1 |
| plasmode |   gate on: template | 9.0 | 5.0 | 0.0 | 0.0 | 0.0 | 0.7 | 0.5 | 0.0% | 100% | 0.0 |

Claude Haiku 5.5 on the facts-only (H1) cells of D74 outside the pilot datasets (320 synthetic: 16 datasets × 2 models × 2 namings × 5 draws; 180 plasmode: 18 datasets × 2 models × 5 draws), every arm scored by E3's three scoring readings (extractor x5; a claim counts if two find it) and verified on the fitted model under lexicon v3 with D74's fixes. Template only: the gate's fallback text from the certified statements, without an LLM. Plain prompt: the same writer and facts with the writer's role and rules for the text, but no lexicon words, DSL, plan, verifier or repair (prompts p1). Gate off: the first draft under the gate's prompt; gate on: the released text, and by exit state. P_U: share of texts with a claim false against the fitted model, as read; 95% Wilson interval. E_U = 1 − P_U / P_U of the reference arm. Claims false vs planted truth: the share of claims other than hedges that are false against T (a hedge is about the sample, not T). Required terms: the three most important features and every pair with a share of at least 10%. Numbers no claim checks: statements with a number that no DSL form expresses (the gate's round trip fails them). Cost per text: the writer's and the gate's calls at batch prices, scoring readings not included.
