# Tab. 6: what the gate adds over its template and over a plain prompt (E3 cells, facts only; D71)

**Control effectiveness and volume**

| Arm | texts | P_U (95% interval) | E_U vs gate off | E_U vs plain prompt | claims per text | words per text | claims false vs planted truth | cost per text |
|---|---|---|---|---|---|---|---|---|
| Template only (no LLM) | 319 | 0.0% (0.0%–1.2%) | 1.00 | 1.00 | 15.9 | 151 | 8.5% | $0.0000 |
| Plain prompt (no gate) | 319 | 95.9% (93.2%–97.6%) | -0.17 | 0.00 | 21.9 | 248 | 27.1% | $0.0003 |
| Gate off (first draft) | 320 | 81.9% (77.3%–85.7%) | 0.00 | 0.15 | 16.3 | 165 | 16.6% | – |
| Gate on (released text) | 320 | 4.7% (2.9%–7.6%) | 0.94 | 0.95 | 15.2 | 149 | 8.5% | $0.0021 |
|   gate on: released as written | 86 | 16.3% (10.0%–25.5%) | 0.80 | 0.83 | 15.4 | 158 | 7.3% | $0.0021 |
|   gate on: released reduced | 29 | 3.5% (0.6%–17.2%) | 0.96 | 0.96 | 12.3 | 131 | 7.2% | $0.0028 |
|   gate on: template | 205 | 0.0% (0.0%–1.8%) | 1.00 | 1.00 | 15.5 | 147 | 9.1% | $0.0019 |

**Claims per text by kind, hedges, coverage and numbers**

| Arm | strength | direction | rank | share | comparison | interaction | jump or peak | hedges (share of claims) | every required term covered | numbers no claim checks |
|---|---|---|---|---|---|---|---|---|---|---|
| Template only (no LLM) | 9.0 | 5.4 | 0.0 | 0.0 | 0.0 | 0.8 | 0.7 | 0.0% | 100% | 0.0 |
| Plain prompt (no gate) | 6.0 | 4.0 | 2.4 | 2.5 | 0.8 | 2.1 | 2.1 | 9.0% | 92% | 2.1 |
| Gate off (first draft) | 4.9 | 4.4 | 2.8 | 0.5 | 0.1 | 1.3 | 1.0 | 8.4% | 99% | 0.1 |
| Gate on (released text) | 7.4 | 5.0 | 1.1 | 0.1 | 0.0 | 0.8 | 0.5 | 2.0% | 100% | 0.0 |
|   gate on: released as written | 5.0 | 4.8 | 3.0 | 0.2 | 0.1 | 1.1 | 0.4 | 5.5% | 100% | 0.0 |
|   gate on: released reduced | 3.5 | 3.6 | 2.7 | 0.1 | 0.1 | 1.0 | 0.5 | 6.5% | 100% | 0.0 |
|   gate on: template | 9.0 | 5.3 | 0.0 | 0.0 | 0.0 | 0.6 | 0.6 | 0.0% | 100% | 0.0 |

Claude Haiku 5.5 on E3's 320 facts-only (H1) cells outside the pilot datasets (16 datasets × 2 models × 2 namings × 5 draws), every arm scored by E3's three scoring readings (extractor x3; a claim counts if two find it) and verified on the fitted model under lexicon v2. Template only: the gate's fallback text from the certified statements, without an LLM. Plain prompt: the same writer and facts with the writer's role and rules for the text, but no lexicon words, DSL, plan, verifier or repair (prompts p1). Gate off: the first draft under the gate's prompt; gate on: the released text, and by exit state. P_U: share of texts with a claim false against the fitted model, as read; 95% Wilson interval. E_U = 1 − P_U / P_U of the reference arm. Claims false vs planted truth: the share of claims other than hedges that are false against T (a hedge is about the sample, not T). Required terms: the three most important features and every pair with a share of at least 10%. Numbers no claim checks: statements with a number that no DSL form expresses (the gate's round trip fails them). Cost per text: the writer's and the gate's calls at batch prices, scoring readings not included.
