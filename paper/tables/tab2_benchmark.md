# Tab. 2: the benchmark, synthetic and plasmode tiers

**Synthetic tier: n = 5,000, 50,000; seeds 1, 2, 3; base rate 22%**

| Feature | Role | Distribution | Planted shape | Share (no interaction) |
|---|---|---|---|---|
| utilization | strong | Beta(2, 3) | increasing, steeper above 0.6 | 40% |
| n_delinquencies | strong | min(Poisson(0.8), 6) | increasing, saturating | 24% |
| income | moderate | lognormal, median 50,000, σ 0.5 | decreasing (−log income) | 13% |
| history_months | peak | uniform 6 to 360 | decreasing, with a bump at 36 months (rising on 7% of the data) | 10% |
| dti | threshold | uniform 0 to 0.6 | a step up at 0.43 | 8% |
| n_inquiries | weak | Poisson(1.5) | increasing (linear) | 4% |
| age | near flat | uniform 21 to 75 | decreasing (linear) | 1% |
| noise_1 | noise | N(0, 1) | zero | 0% |
| noise_2 | noise | N(0, 1) | zero | 0% |

**Plasmode tier: TaiwanCredit features (UCI 350), planted outcome; n = 5,000, 30,000; seeds 1, 2, 3**

| Feature | Role | Planted shape | Share (no interaction) |
|---|---|---|---|
| PAY_0 | strong | the real-label EBM's, per status value | 40% |
| LIMIT_BAL | strong | decreasing, smooth | 24% |
| BILL_AMT1 | moderate | increasing, smooth | 13% |
| PAY_AMT1 | moderate | decreasing, smooth | 10% |
| PAY_AMT2 | threshold | a step down at 2,000 | 8% |
| AGE | weak | increasing, smooth | 4% |
| EDUCATION | near flat | linear in the code, clipped to 1 to 3 | 1% |
| BILL_AMT2 | correlated null | zero; Spearman 0.91 with BILL_AMT1 | 0% |
| PAY_AMT3 | noise | zero | 0% |

**Planted pairs (pairs take their share from the total; main terms keep their coefficients)**

| Tier | Pair | Pattern | Share, none | Share, weak | Share, dominant |
|---|---|---|---|---|---|
| synthetic | utilization & n_delinquencies | amplification | 0% | 3% | 21% |
| synthetic | history_months & n_inquiries | sign flip | 0% | 6% | 6% |
| plasmode | PAY_0 & EDUCATION | amplification | 0% | 3% | 21% |
| plasmode | AGE & BILL_AMT1 | sign flip | 0% | 6% | 6% |

18 datasets per tier: 3 interaction levels × 2 sample sizes × 3 seeds. EBM and XGB2 are fitted on each (36 models per tier).
