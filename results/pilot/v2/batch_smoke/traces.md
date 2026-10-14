# Pilot traces: batch_smoke

## syn-dominant-n50000-s1_XGB2_H1_d5_claude-haiku-5-5_plausible

**RELEASED**: passed after 1 repair round(s) (3 calls, 1 repair rounds)

### Version 0: format retry (14 claims, 1 failing)
1. Revolving credit utilization is the most important driver of default risk, accounting for about 27% of the model's importance, and risk rises steadily as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `share("utilization") == approx(0.27)`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk rises as delinquencies accumulate, with the largest step between none and two or more.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Utilization and delinquencies interact strongly: the effect of utilization grows with the number of past delinquencies, so high utilization matters far more for applicants who have already been delinquent.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income is a moderate to weak driver, and higher income is associated with lower default risk.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history is a moderate to weak driver, and longer histories are associated with lower risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio is a weak driver, and risk generally increases as it rises.
    - `strength("dti") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("dti") == "increasing"`: ok
7. The data do not settle whether the number of dependents matters for default risk.
    - `unsettled(strength("noise_2") == "weak")`: ok
8. Age hardly matters for the model's predictions.
    - `negligible("age")`: ok

### Version 1: repair 1 (14 claims, 0 failing)
1. Revolving credit utilization is the most important driver of default risk, accounting for about 27% of the model's importance, and risk rises steadily as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `share("utilization") == approx(0.27)`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk rises as delinquencies accumulate, with the largest step between none and two or more.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Utilization and delinquencies interact strongly: the effect of utilization grows with the number of past delinquencies, so high utilization matters far more for applicants who have already been delinquent.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income is a moderate to weak driver, and higher income is associated with lower default risk.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history is a moderate to weak driver, and longer histories are associated with lower risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio is a weak to moderate driver, and risk generally increases as it rises.
    - `strength("dti") in ("weak", "moderate")`: ok
    - `direction("dti") == "increasing"`: ok
7. The data do not settle whether the number of dependents matters for default risk.
    - `unsettled(strength("noise_2") == "weak")`: ok
8. Age hardly matters for the model's predictions.
    - `negligible("age")`: ok

## syn-dominant-n50000-s1_XGB2_H2_d5_claude-haiku-5-5_plausible

**RELEASED**: passed after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (27 claims, 0 failing)
1. Credit utilization is the most important driver of default risk, accounting for about 27% of the model's importance, and risk increases steadily as the share of the credit limit in use rises.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
    - `share("utilization") == approx(0.268)`: ok
2. The number of past delinquencies is the second most important driver, with a moderate to strong effect, and risk jumps when an applicant has at least one past delinquency.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `threshold("n_delinquencies", at=1.0)`: ok
    - `effect("utilization") > effect("n_delinquencies")`: ok
3. The effect of credit utilization grows with the number of past delinquencies: utilization matters far more for applicants with two delinquencies than for those with none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income is the third or fourth most important driver, with a moderate effect, and default risk decreases as income rises.
    - `rank("income") in (3, 4)`: ok
    - `direction("income") == "decreasing"`: ok
    - `strength("income") == "moderate"`: ok
    - `effect("n_delinquencies") > effect("income")`: ok
5. Length of credit history is also third or fourth in importance, with a moderate effect, and risk decreases with longer histories; its effect matters more than the debt-to-income ratio.
    - `rank("history_months") in (3, 4)`: ok
    - `direction("history_months") == "decreasing"`: ok
    - `strength("history_months") == "moderate"`: ok
    - `effect("history_months") > effect("dti")`: ok
6. The debt-to-income ratio is the fifth most important driver, with a weak to moderate effect, and risk increases with it.
    - `rank("dti") == 5`: ok
    - `direction("dti") == "increasing"`: ok
    - `strength("dti") in ("weak", "moderate")`: ok
    - `effect("dti") > effect("noise_2")`: ok
7. Age and months at the current address hardly matter for default risk, and the number of dependents has at most a weak effect; the data do not show a clear movement for these features.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `strength("noise_2") in ("negligible", "weak")`: ok
8. The number of recent credit inquiries has at most a weak effect, with risk increasing slightly as inquiries rise.
    - `strength("n_inquiries") in ("negligible", "weak")`: ok
    - `direction("n_inquiries") == "increasing"`: ok
