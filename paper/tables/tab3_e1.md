# Tab. 3: E1, the lexicon's verdicts against the planted truth, by tier (lexicon v3 with D74's fixes)

| tier | layer (reference) | model | n | claims | decided | accuracy among decided | confident errors | 95% interval |
|---|---|---|---|---|---|---|---|---|
| synthetic | data | oracle | 5,000 | 1530 | 58% | 99.8% | 0.13% | 0.00%–0.39% |
| synthetic | data | oracle | 50,000 | 1530 | 86% | 100.0% | 0.00% | 0.00%–0.00% |
| synthetic | model | EBM | 5,000 | 895 | 60% | 100.0% | 0.00% | 0.00%–0.00% |
| synthetic | model | EBM | 50,000 | 1318 | 76% | 100.0% | 0.00% | 0.00%–0.00% |
| synthetic | model | XGB2 | 5,000 | 895 | 55% | 99.0% | 0.56% | 0.11%–0.99% |
| synthetic | model | XGB2 | 50,000 | 1318 | 71% | 99.8% | 0.15% | 0.00%–0.46% |
| synthetic | end to end | EBM | 5,000 | 1530 | 38% | 98.8% | 0.46% | 0.07%–0.98% |
| synthetic | end to end | EBM | 50,000 | 1530 | 67% | 99.8% | 0.13% | 0.00%–0.39% |
| synthetic | end to end | XGB2 | 5,000 | 1530 | 37% | 96.4% | 1.31% | 0.72%–2.16% |
| synthetic | end to end | XGB2 | 50,000 | 1530 | 63% | 99.6% | 0.26% | 0.00%–0.52% |
| plasmode | data | oracle | 5,000 | 1521 | 55% | 99.9% | 0.07% | 0.00%–0.20% |
| plasmode | data | oracle | 30,000 | 1521 | 75% | 100.0% | 0.00% | 0.00%–0.00% |
| plasmode | model | EBM | 5,000 | 829 | 53% | 95.2% | 2.53% | 1.39%–3.97% |
| plasmode | model | EBM | 30,000 | 1146 | 69% | 97.6% | 1.66% | 0.89%–2.33% |
| plasmode | model | XGB2 | 5,000 | 829 | 46% | 96.1% | 1.81% | 1.08%–2.84% |
| plasmode | model | XGB2 | 30,000 | 1146 | 62% | 98.0% | 1.22% | 0.80%–1.62% |
| plasmode | end to end | EBM | 5,000 | 1521 | 36% | 89.9% | 3.68% | 2.24%–5.19% |
| plasmode | end to end | EBM | 30,000 | 1521 | 55% | 96.5% | 1.91% | 1.12%–2.83% |
| plasmode | end to end | XGB2 | 5,000 | 1521 | 32% | 90.6% | 3.02% | 2.10%–3.94% |
| plasmode | end to end | XGB2 | 30,000 | 1521 | 49% | 96.7% | 1.64% | 1.25%–2.10% |

Data layer: the lexicon on the oracle (what the sample supports); model layer: on the fitted model, against the oracle's labels; end to end: on the fitted model, against the planted labels (D12). Each tier pools its three seeds (synthetic: the discovery seed and the two confirmation seeds); the model layer counts only the claims the oracle decides. Confident errors: a false claim certified or a true claim refuted, over all claims (D31), with a 95% percentile interval from a bootstrap over the datasets (9 per cell).
