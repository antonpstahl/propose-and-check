# Tab. 5: the gate and an LLM critic on the same texts (D56)

| Texts | Gate (x4) | Critic: GPT-6 Luna | Critic: GPT-6.1 Sol |
|---|---|---|---|
| LLM-written errors caught (final labels) | 93 of 95 (98%) | 95 of 95 (100%) | 95 of 95 (100%) |
| LLM-written errors caught (author's first pass) | 74 of 77 (96%) | 77 of 77 (100%) | 76 of 77 (99%) |
| LLM-written sentences judged correct, blocked (final labels) | 1 of 5 (20%) | 4 of 5 (80%) | 3 of 5 (60%) |
| LLM-written sentences judged correct, blocked (first pass) | 8 of 9 (89%) | 8 of 9 (89%) | 8 of 9 (89%) |
| Scripted errors caught (30 per operator) | 232 of 240 (97%) | 240 of 240 (100%) | – |
| Scripted errors caught: a feature the model lacks (M9) | 22 of 30 (73%) | 30 of 30 (100%) | – |
| Template texts, every claim certified, blocked | 0 of 32 (0%) | 20 of 32 (62%) | 26 of 32 (81%) |
| Control mutants (a step moved inside the tolerance), blocked | 1 of 21 (5%) | 7 of 21 (33%) | – |
| E3's released texts (LLM-written), blocked | 64 of 387 (17%) | 300 of 390 (77%) | – |
| E3's released texts: correct texts blocked (false-alarm rate, labelled) | 14.3% | 0.0% | – |
| E3's released texts: blocked texts with an error by the author's labels | 2 of 64 (3%) | 26 of 40 (65%), sample | – |
| E3's released texts: blocked texts with an error the round trip does not check | – | 5 of 40 (12%), sample | – |
| Critic's confident errors: correct text blocked at p ≥ 0.9 / error passed at p ≤ 0.1 | no probability | 31 of 31 / 0 of 0 | 29 of 29 / 0 of 0 |
| Cost per text (USD) | 0.0005 | 0.0011 | 0.0092 |

Outside the pilot datasets. Blocked: the critic names a problem; the gate does not release the text (a text the extractor could not read falls back to the template). Final labels: the author's labels after a review against the lexicon; first pass: the author's labels alone, made without any checker's verdict (unsure left out). Template texts and control mutants are correct by construction (every claim certified on the fitted model). The gate's cost is its three readings at batch prices; the critic's one call at synchronous prices, reasoning included.
