# Tab. 5: the gate and an LLM critic on the same texts (D78, D79, D83)

| Texts | Gate (x5) | Critic c3 (GPT-6 Luna) |
|---|---|---|
| LLM-written errors caught (final labels) | 94 of 95 (99%) | 95 of 95 (100%) |
| LLM-written errors caught (author's first pass) | 75 of 77 (97%) | 77 of 77 (100%) |
| LLM-written sentences judged correct, blocked (final labels) | 1 of 5 (20%) | 5 of 5 (100%) |
| LLM-written sentences judged correct, blocked (first pass) | 8 of 9 (89%) | 9 of 9 (100%) |
| Scripted errors caught (30 per operator) | 237 of 240 (99%) | 240 of 240 (100%) |
| Scripted errors caught: a feature the model lacks (M9) | 29 of 30 (97%) | 30 of 30 (100%) |
| Template texts, every claim certified, blocked | 1 of 32 (3%) | 13 of 32 (41%) |
| Control mutants (a step moved inside the tolerance), blocked | 2 of 22 (9%) | 11 of 22 (50%) |
| Balanced accuracy: errors (LLM-written, final labels, and scripted); known-correct texts (templates, control mutants, LLM-written sentences judged correct) | 0.96 | 0.75 |
| Blind sample (all 42 entries): texts with a sentence labelled false, flagged | 3 of 9 (33%), as a scoring reader | 8 of 9 (89%) |
|   texts labelled without such a sentence, flagged | 4 of 26 (15%), as a scoring reader | 9 of 26 (35%) |
| Blind sample (LLM-written releases): texts with a sentence labelled false, flagged | 0 of 4 (0%), as a scoring reader | 3 of 4 (75%) |
|   texts labelled without such a sentence, flagged | 0 of 8 (0%), as a scoring reader | 1 of 8 (12%) |
| Blind sample (all 42 entries): texts with a sentence labelled false or not settled, flagged | 7 of 22 (32%), as a scoring reader | 12 of 22 (55%) |
|   texts labelled without such a sentence, flagged | 4 of 15 (27%), as a scoring reader | 6 of 15 (40%) |
| Blind sample (LLM-written releases): texts with a sentence labelled false or not settled, flagged | 0 of 5 (0%), as a scoring reader | 3 of 5 (60%) |
|   texts labelled without such a sentence, flagged | 0 of 7 (0%), as a scoring reader | 1 of 7 (14%) |
| Critic's confident errors: correct text blocked at p ≥ 0.9 / error passed at p ≤ 0.1 | no probability | 29 of 29 / 0 of 0 |
| Cost per text (USD) | 0.0005 (x4's batch price) | 0.0010 |

Outside the pilot datasets. Blocked: the critic names a problem; the gate does not release the text (a text the extractor could not read counts as caught, D32). Final labels: the author's labels after a review against the lexicon; first pass: the author's labels alone, made without any checker's verdict (unsure left out). Template texts and control mutants are correct by construction (every claim certified on the fitted model). The critic c3 gets the facts each writer saw (H2 with the certified statements for an H2 text) and the writer's whole set of rules, from writer prompt v4 as D74's writer got it. Blind sample: B01 to B40 of D76's sample, labelled by the author (D82, D83); the gate's column there is its extractor as one of E3's scoring readings, since the gate itself released every text of the on arm. The gate's cost is its three readings at batch prices; the critic's one call at synchronous prices, reasoning included.
