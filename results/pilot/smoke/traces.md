# Pilot traces: smoke

## syn-dominant-n50000-s1_XGB2_H1_d0_claude-haiku-5-5_plausible

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (18 claims, 2 failing)
1. Revolving credit utilization is the most important driver of predicted default, and risk rises steeply as the share of the credit limit in use goes up, with the largest increases above roughly 0.76.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk rises as delinquencies accumulate, though the step from one to two or more is the main change.
    - `rank("n_delinquencies") == 2`: ok
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
    - `direction("n_delinquencies") == "increasing"`: ok
3. The two drivers reinforce each other: the effect of utilization is much larger for applicants with two or more past delinquencies than for those with none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Annual income has a moderate effect, with lower income raising predicted risk and higher income lowering it.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a moderate effect, with longer histories lowering predicted risk.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has a weak to moderate effect, with higher ratios raising predicted risk.
    - `strength("dti") in ("weak", "moderate")`: ok
    - `direction("dti") == "increasing"`: ok
7. Age and months at the current address have negligible effects, and the data do not settle whether the number of dependents has any effect at all.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `unsettled(negligible("noise_2"))`: ok
8. The number of recent credit inquiries has at most a weak effect, and the data do not settle whether higher counts raise risk.
    - `strength("n_inquiries") in ("negligible", "weak")`: ok
    - `unsettled(direction("n_inquiries") == "increasing")`: **false** (the claim is settled: it is true)

### Version 1: reduced (13 claims, 0 failing, missing: n_delinquencies)
1. Revolving credit utilization is the most important driver of predicted default, and risk rises steeply as the share of the credit limit in use goes up, with the largest increases above roughly 0.76.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
3. The two drivers reinforce each other: the effect of utilization is much larger for applicants with two or more past delinquencies than for those with none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Annual income has a moderate effect, with lower income raising predicted risk and higher income lowering it.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a moderate effect, with longer histories lowering predicted risk.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has a weak to moderate effect, with higher ratios raising predicted risk.
    - `strength("dti") in ("weak", "moderate")`: ok
    - `direction("dti") == "increasing"`: ok
7. Age and months at the current address have negligible effects, and the data do not settle whether the number of dependents has any effect at all.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `unsettled(negligible("noise_2"))`: ok

### Version 2: template (17 claims, 0 failing)
1. Credit utilization has a strong effect on default risk; default risk increases with credit utilization.
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies has a moderate to strong effect on default risk; default risk increases with the number of past delinquencies.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Default risk jumps at the number of past delinquencies = 1.
    - `threshold("n_delinquencies", at=1.0)`: ok
4. Income has a moderate effect on default risk; default risk decreases with income.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
5. The length of credit history has a moderate effect on default risk; default risk decreases with the length of credit history.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has a weak to moderate effect on default risk; default risk increases with the debt-to-income ratio.
    - `strength("dti") in ("weak", "moderate")`: ok
    - `direction("dti") == "increasing"`: ok
7. The number of dependents has at most a weak effect on default risk.
    - `strength("noise_2") in ("negligible", "weak")`: ok
8. The number of recent inquiries has at most a weak effect on default risk; default risk increases with the number of recent inquiries.
    - `strength("n_inquiries") in ("negligible", "weak")`: ok
    - `direction("n_inquiries") == "increasing"`: ok
9. Months at the current address hardly matters for default risk.
    - `negligible("noise_1")`: ok
10. Age hardly matters for default risk.
    - `negligible("age")`: ok
11. The effect of credit utilization grows with the number of past delinquencies.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok

## syn-dominant-n50000-s1_XGB2_H2_d0_claude-haiku-5-5_plausible

**RELEASED**: passed after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (28 claims, 0 failing)
1. Credit utilization is the most important driver of default risk, accounting for about 27% of the model's importance, and risk rises strongly as utilization climbs.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
    - `share("utilization") == approx(0.268)`: ok
2. The number of past delinquencies is the second most important driver, with a moderate to strong effect, and risk jumps once an applicant has at least one delinquency.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `threshold("n_delinquencies", at=1.0)`: ok
3. The effect of credit utilization grows with the number of past delinquencies: utilization adds much more risk for applicants who have delinquencies than for those who have none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
    - `effect("utilization") > effect("n_delinquencies")`: ok
4. Income is the third or fourth most important driver, with a moderate effect, and risk falls as income rises.
    - `rank("income") in (3, 4)`: ok
    - `direction("income") == "decreasing"`: ok
    - `strength("income") == "moderate"`: ok
    - `effect("n_delinquencies") > effect("income")`: ok
5. The length of credit history is also a third or fourth most important driver with a moderate effect, and risk falls as the history gets longer; this matters more than the debt-to-income ratio.
    - `rank("history_months") in (3, 4)`: ok
    - `direction("history_months") == "decreasing"`: ok
    - `strength("history_months") == "moderate"`: ok
    - `effect("history_months") > effect("dti")`: ok
6. The debt-to-income ratio is the fifth most important driver, with a weak to moderate effect, and risk rises with it, though it matters less than the length of credit history.
    - `direction("dti") == "increasing"`: ok
    - `strength("dti") in ("weak", "moderate")`: ok
    - `rank("dti") == 5`: ok
    - `effect("dti") > effect("noise_2")`: ok
7. Age and months at the current address hardly matter for default risk, and the number of dependents has at most a weak effect.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `strength("noise_2") in ("negligible", "weak")`: ok
8. Credit utilization does not interact with income or with the length of credit history, and the number of past delinquencies does not interact with income; the data do not settle whether the length of credit history and recent inquiries interact.
    - `interaction("utilization", "income", pattern="none")`: ok
    - `interaction("utilization", "history_months", pattern="none")`: ok
    - `interaction("n_delinquencies", "income", pattern="none")`: ok
