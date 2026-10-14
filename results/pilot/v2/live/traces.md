# Pilot traces: live

## syn-dominant-n50000-s1_EBM_H1_d0_claude-haiku-5-5_plausible

**RELEASED**: passed after 1 repair round(s) (3 calls, 1 repair rounds)

### Version 0: format retry (15 claims, 1 failing)
1. Revolving credit utilization is the most important driver of default risk, accounting for roughly 28% of the model's importance, and risk rises steeply as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `share("utilization") == approx(0.28)`: ok
2. The number of past delinquencies is the second most important driver, and risk increases with it, with the largest rise between no delinquencies and one or two.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `share("n_delinquencies") == approx(0.17)`: ok
3. The two features interact strongly: the effect of utilization is far larger for applicants with delinquencies, so high utilization combined with past delinquencies carries the greatest risk.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Annual income is among the next most important features, and risk decreases as income rises.
    - `direction("income") == "decreasing"`: ok
    - `rank("income") in (3, 4)`: ok
5. Length of credit history is also among the next most important features, and risk decreases as the history gets longer.
    - `direction("history_months") == "decreasing"`: ok
    - `rank("history_months") in (3, 4)`: ok
6. The debt-to-income ratio has a weak to moderate effect, and risk increases with it.
    - `strength("dti") in ("weak", "moderate")`: ok
    - `direction("dti") == "increasing"`: ok
7. The data do not settle whether the number of dependents matters for default risk.
    - `unsettled(negligible("noise_2"))`: **false** (the claim is settled: it is true)
8. Age hardly matters.
    - `negligible("age")`: ok

### Version 1: repair 1 (15 claims, 0 failing)
1. Revolving credit utilization is the most important driver of default risk, accounting for roughly 28% of the model's importance, and risk rises steeply as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `share("utilization") == approx(0.28)`: ok
2. The number of past delinquencies is the second most important driver, and risk increases with it, with the largest rise between no delinquencies and one or two.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `share("n_delinquencies") == approx(0.17)`: ok
3. The two features interact strongly: the effect of utilization is far larger for applicants with delinquencies, so high utilization combined with past delinquencies carries the greatest risk.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Annual income is among the next most important features, and risk decreases as income rises.
    - `direction("income") == "decreasing"`: ok
    - `rank("income") in (3, 4)`: ok
5. Length of credit history is also among the next most important features, and risk decreases as the history gets longer.
    - `direction("history_months") == "decreasing"`: ok
    - `rank("history_months") in (3, 4)`: ok
6. The debt-to-income ratio has a weak to moderate effect, and risk increases with it.
    - `strength("dti") in ("weak", "moderate")`: ok
    - `direction("dti") == "increasing"`: ok
7. The number of dependents hardly matters for default risk.
    - `negligible("noise_2")`: ok
8. Age hardly matters.
    - `negligible("age")`: ok

## syn-dominant-n50000-s1_EBM_H2_d0_claude-haiku-5-5_plausible

**RELEASED**: passed after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (25 claims, 0 failing)
1. Credit utilization is the most important driver of default risk, accounting for about 28% of the model's importance, and risk increases as utilization rises.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
    - `share("utilization") == approx(0.279)`: ok
2. The number of past delinquencies is the second most important driver, accounting for about 17% of importance, and default risk rises with it, with a jump between zero and one or more past delinquencies.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `strength("n_delinquencies") == "strong"`: ok
    - `share("n_delinquencies") == approx(0.172)`: ok
    - `threshold("n_delinquencies", at=0.5)`: ok
3. The effect of credit utilization grows with the number of past delinquencies: utilization matters far more for applicants who have past delinquencies than for those who have none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income and length of credit history each have a moderate effect, with default risk decreasing as income and credit history length rise.
    - `rank("income") in (3, 4)`: ok
    - `direction("income") == "decreasing"`: ok
    - `strength("income") == "moderate"`: ok
    - `rank("history_months") in (3, 4)`: ok
    - `direction("history_months") == "decreasing"`: ok
    - `strength("history_months") == "moderate"`: ok
5. The debt-to-income ratio has a weak to moderate effect, accounting for about 5% of importance, and default risk increases with it.
    - `rank("dti") == 5`: ok
    - `direction("dti") == "increasing"`: ok
    - `strength("dti") in ("weak", "moderate")`: ok
6. Recent credit inquiries have at most a weak effect, while the number of dependents, months at the current address and age hardly matter for default risk.
    - `strength("n_inquiries") in ("negligible", "weak")`: ok
    - `negligible("noise_2")`: ok
    - `negligible("noise_1")`: ok
    - `negligible("age")`: ok
7. The data do not settle whether the effects of credit utilization and credit history length interact, though the model shows no clear interaction between them at this sample size.
    - `interaction("utilization", "history_months", pattern="none")`: ok
    - `interaction("n_delinquencies", "income", pattern="none")`: ok

## syn-dominant-n50000-s1_XGB2_H1_d0_claude-haiku-5-5_plausible

**RELEASED**: passed after 1 repair round(s) (2 calls, 1 repair rounds)

### Version 0: proposer (15 claims, 1 failing)
1. Revolving credit utilization is the single most important driver of predicted default, and predicted risk rises steadily as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk rises with it, mainly from none to one or two.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. The effect of utilization grows strongly with the number of past delinquencies: it matters far more for applicants with two delinquencies than for those with none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Higher income is associated with lower predicted risk, though income is a weak to moderate driver overall.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
5. A longer credit history is associated with lower predicted risk, and this is also a weak to moderate driver.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. A higher debt-to-income ratio increases predicted risk, but its effect is weak to moderate in size.
    - `strength("dti") in ("weak", "moderate")`: ok
    - `direction("dti") == "increasing"`: ok
7. The data do not settle whether the number of dependents matters for predicted default.
    - `unsettled(strength("noise_2") == "moderate")`: **false** (the claim is settled: it is false)
8. Age and months at the current address hardly matter for the predictions.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok

### Version 1: repair 1 (15 claims, 0 failing)
1. Revolving credit utilization is the single most important driver of predicted default, and predicted risk rises steadily as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk rises with it, mainly from none to one or two.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. The effect of utilization grows strongly with the number of past delinquencies: it matters far more for applicants with two delinquencies than for those with none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Higher income is associated with lower predicted risk, though income is a weak to moderate driver overall.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
5. A longer credit history is associated with lower predicted risk, and this is also a weak to moderate driver.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. A higher debt-to-income ratio increases predicted risk, but its effect is weak to moderate in size.
    - `strength("dti") in ("weak", "moderate")`: ok
    - `direction("dti") == "increasing"`: ok
7. The data do not settle whether the number of dependents matters for predicted default.
    - `unsettled(strength("noise_2") in ("weak", "moderate"))`: ok
8. Age and months at the current address hardly matter for the predictions.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok

## syn-dominant-n50000-s1_XGB2_H2_d0_claude-haiku-5-5_plausible

**RELEASED**: passed after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (38 claims, 0 failing)
1. Revolving credit utilization is the most important driver of predicted default, accounting for about 27% of the model's importance, and default risk rises with it.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
    - `share("utilization") == approx(0.268)`: ok
2. The number of past delinquencies is the second most important driver, with a moderate to strong effect, and risk jumps once an applicant has at least one delinquency.
    - `rank("n_delinquencies") == 2`: ok
    - `threshold("n_delinquencies", at=1.0)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
3. The effect of utilization grows with the number of past delinquencies, so high utilization matters much more for applicants with delinquencies than for those without.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
    - `effect("utilization") > effect("n_delinquencies")`: ok
4. Income is third or fourth in importance, with a moderate effect: default risk decreases as income rises.
    - `rank("income") in (3, 4)`: ok
    - `direction("income") == "decreasing"`: ok
    - `strength("income") == "moderate"`: ok
    - `share("income") == approx(0.087)`: ok
5. The length of credit history is also third or fourth in importance, with a moderate effect, and risk decreases as history lengthens.
    - `rank("history_months") in (3, 4)`: ok
    - `direction("history_months") == "decreasing"`: ok
    - `strength("history_months") == "moderate"`: ok
    - `share("history_months") == approx(0.073)`: ok
6. The debt-to-income ratio ranks fifth, with a weak to moderate effect, and risk increases with it.
    - `rank("dti") == 5`: ok
    - `direction("dti") == "increasing"`: ok
    - `strength("dti") in ("weak", "moderate")`: ok
    - `share("dti") == approx(0.055)`: ok
7. Age hardly matters for default risk.
    - `negligible("age")`: ok
    - `rank("age") in (8, 9)`: ok
8. Recent credit inquiries have at most a weak effect, with risk increasing as inquiries rise.
    - `rank("n_inquiries") in (6, 7, 8)`: ok
    - `direction("n_inquiries") == "increasing"`: ok
    - `strength("n_inquiries") in ("negligible", "weak")`: ok
9. Months at the current address hardly matter, and the number of dependents has at most a weak effect.
    - `negligible("noise_1")`: ok
    - `strength("noise_2") in ("negligible", "weak")`: ok
10. The data do not settle whether credit history length and recent inquiries interact.
    - `unsettled(interaction("history_months", "n_inquiries", pattern="none"))`: ok
11. Utilization does not interact with income or credit history length, and delinquencies do not interact with income or credit history length.
    - `interaction("utilization", "income", pattern="none")`: ok
    - `interaction("utilization", "history_months", pattern="none")`: ok
    - `interaction("n_delinquencies", "income", pattern="none")`: ok
    - `interaction("n_delinquencies", "history_months", pattern="none")`: ok
    - `interaction("income", "history_months", pattern="none")`: ok
    - `interaction("income", "dti", pattern="none")`: ok
    - `interaction("dti", "noise_2", pattern="none")`: ok
    - `interaction("noise_1", "noise_2", pattern="none")`: ok

## syn-dominant-n50000-s1_XGB2_H2_d1_claude-haiku-5-5_plausible

**RELEASED**: passed after 1 repair round(s) (2 calls, 1 repair rounds)

### Version 0: proposer (24 claims, 1 failing)
1. Credit utilization is by far the most important driver of default risk, accounting for about 27% of the model's importance, and risk rises steadily as utilization increases, with the strongest effect at the highest levels.
    - `rank("utilization") == 1`: ok
    - `share("utilization") == approx(0.268)`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
2. The number of past delinquencies is the second most important driver, with a moderate to strong effect, and default risk jumps once an applicant has at least one delinquency.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `threshold("n_delinquencies", at=1.0)`: ok
3. The effect of utilization grows with the number of past delinquencies, so high utilization matters much more for applicants who have had several delinquencies.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income and the length of credit history are both moderate drivers, ranking third or fourth, and default risk decreases as income and credit history length rise.
    - `rank("income") in (3, 4)`: ok
    - `direction("income") == "decreasing"`: ok
    - `strength("income") == "moderate"`: ok
    - `rank("history_months") in (3, 4)`: ok
    - `direction("history_months") == "decreasing"`: ok
    - `strength("history_months") == "moderate"`: ok
5. The debt-to-income ratio is a weak to moderate driver ranked fifth, with risk increasing as the ratio rises.
    - `rank("dti") == 5`: ok
    - `direction("dti") == "increasing"`: ok
    - `strength("dti") in ("weak", "moderate")`: ok
6. The number of recent inquiries has at most a weak effect, and age and months at the current address hardly matter, while the number of dependents has at most a weak effect. The data do not settle whether credit history length and recent inquiries interact.
    - `strength("n_inquiries") in ("negligible", "weak")`: ok
    - `rank("n_inquiries") in (6, 7, 8)`: ok
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `strength("noise_2") in ("negligible", "weak")`: ok
    - `interaction("history_months", "n_inquiries", pattern="none")`: **undecidable**
7. Credit utilization and income, and credit utilization and credit history length, do not interact in any meaningful way.

### Version 1: repair 1 (24 claims, 0 failing)
1. Credit utilization is by far the most important driver of default risk, accounting for about 27% of the model's importance, and risk rises steadily as utilization increases, with the strongest effect at the highest levels.
    - `rank("utilization") == 1`: ok
    - `share("utilization") == approx(0.268)`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
2. The number of past delinquencies is the second most important driver, with a moderate to strong effect, and default risk jumps once an applicant has at least one delinquency.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `threshold("n_delinquencies", at=1.0)`: ok
3. The effect of utilization grows with the number of past delinquencies, so high utilization matters much more for applicants who have had several delinquencies.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income and the length of credit history are both moderate drivers, ranking third or fourth, and default risk decreases as income and credit history length rise.
    - `rank("income") in (3, 4)`: ok
    - `direction("income") == "decreasing"`: ok
    - `strength("income") == "moderate"`: ok
    - `rank("history_months") in (3, 4)`: ok
    - `direction("history_months") == "decreasing"`: ok
    - `strength("history_months") == "moderate"`: ok
5. The debt-to-income ratio is a weak to moderate driver ranked fifth, with risk increasing as the ratio rises.
    - `rank("dti") == 5`: ok
    - `direction("dti") == "increasing"`: ok
    - `strength("dti") in ("weak", "moderate")`: ok
6. The number of recent inquiries has at most a weak effect, and age and months at the current address hardly matter, while the number of dependents has at most a weak effect. The data do not settle whether credit history length and recent inquiries interact.
    - `strength("n_inquiries") in ("negligible", "weak")`: ok
    - `rank("n_inquiries") in (6, 7, 8)`: ok
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `strength("noise_2") in ("negligible", "weak")`: ok
    - `unsettled(interaction("history_months", "n_inquiries", pattern="none"))`: ok
7. Credit utilization and income, and credit utilization and credit history length, do not interact in any meaningful way.

## syn-dominant-n50000-s1_XGB2_H2_d2_claude-haiku-5-5_plausible

**RELEASED**: passed after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (27 claims, 0 failing)
1. Credit utilization is the strongest driver of default risk, accounting for about 27% of the model's importance, and risk generally increases as the share of the credit limit in use rises.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
    - `share("utilization") == approx(0.268)`: ok
2. The number of past delinquencies is the second most important driver, with a moderate to strong effect, and default risk jumps once an applicant has at least one delinquency.
    - `rank("n_delinquencies") == 2`: ok
    - `threshold("n_delinquencies", at=1.0)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
3. The effect of credit utilization grows with the number of past delinquencies, so high utilization is far more damaging for applicants who have had delinquencies.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
    - `effect("utilization") > effect("n_delinquencies")`: ok
4. Income and the length of credit history both have moderate effects, with risk decreasing as income and credit history length rise.
    - `rank("income") in (3, 4)`: ok
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
    - `rank("history_months") in (3, 4)`: ok
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok
    - `effect("n_delinquencies") > effect("income")`: ok
5. The debt-to-income ratio has a weak to moderate effect, with risk increasing as it rises, and it matters more than the number of dependents.
    - `effect("history_months") > effect("dti")`: ok
    - `rank("dti") == 5`: ok
    - `direction("dti") == "increasing"`: ok
    - `strength("dti") in ("weak", "moderate")`: ok
    - `effect("dti") > effect("noise_2")`: ok
6. Recent credit inquiries have at most a weak effect, and age and months at the current address hardly matter.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `strength("n_inquiries") in ("negligible", "weak")`: ok
7. The data do not settle whether the length of credit history and the number of recent inquiries interact.
    - `unsettled(interaction("history_months", "n_inquiries", pattern="none"))`: ok
8. Credit utilization does not interact with income in its effect on default risk.
    - `interaction("utilization", "income", pattern="none")`: ok

## syn-none-n5000-s1_EBM_H1_d0_claude-haiku-5-5_plausible

**RELEASED**: passed after 2 repair round(s) (3 calls, 2 repair rounds)

### Version 0: proposer (15 claims, 3 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
2. The number of past delinquencies is the second or third most important driver, and having at least one delinquency raises the predicted risk compared with having none.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `threshold("n_delinquencies", at=1.0)`: **false**
3. Annual income is the second or third most important driver, and higher income lowers the predicted risk, with the largest drop above about $84,000.
    - `rank("income") in (2, 3)`: ok
    - `direction("income") == "decreasing"`: ok
    - `strength("income") == "moderate"`: **undecidable** (share band straddles a class edge)
4. Length of credit history has a weak to moderate effect, and longer histories lower the predicted risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
5. The model shows no clear interaction between utilization and credit history length.
    - `interaction("utilization", "history_months", pattern="none")`: ok
6. The data do not settle whether debt-to-income ratio has any effect on default risk at this sample size.
    - `unsettled(strength("dti") == "weak")`: ok
7. Recent credit inquiries hardly matter for the predicted risk.
    - `negligible("n_inquiries")`: ok
    - `unsettled(interaction("income", "age", pattern="none"))`: **false** (the claim is settled: it is true)

### Version 1: repair 1 (15 claims, 1 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
2. The number of past delinquencies is the second or third most important driver, and the largest step in predicted risk comes between zero and one delinquency, with having at least one delinquency raising the predicted risk compared with having none.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `threshold("n_delinquencies", at=0.5)`: ok
3. Annual income is the second or third most important driver, and higher income generally lowers the predicted risk, with the largest drop above about $84,000.
    - `rank("income") in (2, 3)`: ok
    - `direction("income") == "decreasing"`: ok
    - `strength("income") in ("weak", "moderate")`: **undecidable** (share band not settled against [2%, 15%))
4. Length of credit history has a weak to moderate effect, and longer histories lower the predicted risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
5. The model shows no clear interaction between utilization and credit history length.
    - `interaction("utilization", "history_months", pattern="none")`: ok
6. The data do not settle whether debt-to-income ratio has any effect on default risk at this sample size.
    - `unsettled(strength("dti") == "weak")`: ok
7. Income and age do not interact in the model, and recent credit inquiries hardly matter for the predicted risk.
    - `negligible("n_inquiries")`: ok
    - `interaction("income", "age", pattern="none")`: ok

### Version 2: repair 2 (15 claims, 0 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
2. The number of past delinquencies is the second or third most important driver, and the largest step in predicted risk comes between zero and one delinquency, with having at least one delinquency raising the predicted risk compared with having none.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `threshold("n_delinquencies", at=0.5)`: ok
3. Annual income is the second or third most important driver, and higher income generally lowers the predicted risk, with the largest drop above about $84,000; the data do not settle whether its effect is weak to moderate or stronger at this sample size.
    - `rank("income") in (2, 3)`: ok
    - `direction("income") == "decreasing"`: ok
    - `unsettled(strength("income") in ("weak", "moderate"))`: ok
4. Length of credit history has a weak to moderate effect, and longer histories lower the predicted risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
5. The model shows no clear interaction between utilization and credit history length.
    - `interaction("utilization", "history_months", pattern="none")`: ok
6. The data do not settle whether debt-to-income ratio has any effect on default risk at this sample size.
    - `unsettled(strength("dti") == "weak")`: ok
7. Income and age do not interact in the model, and recent credit inquiries hardly matter for the predicted risk.
    - `negligible("n_inquiries")`: ok
    - `interaction("income", "age", pattern="none")`: ok

## syn-none-n5000-s1_EBM_H2_d0_claude-haiku-5-5_plausible

**RELEASED**: passed after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (22 claims, 0 failing)
1. Credit utilization is the most important driver of default risk, and risk rises as the share of the credit limit in use goes up, with a strong effect overall.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
2. The number of past delinquencies is the second or third most important driver, and having any delinquency on file raises default risk in a step, with a moderate to strong effect.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `threshold("n_delinquencies", at=0.5)`: ok
3. Annual income is the other leading driver: higher income lowers default risk, with a moderate to strong effect.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
    - `rank("income") in (2, 3)`: ok
4. Utilization matters more than delinquencies, and income matters more than the length of credit history.
    - `effect("utilization") > effect("n_delinquencies")`: ok
    - `effect("income") > effect("history_months")`: ok
5. Longer credit history is associated with lower default risk, but this effect is weak to moderate and ranks fourth to sixth in importance.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
    - `rank("history_months") in (4, 5, 6)`: ok
6. The effect of utilization does not depend on credit history length, so the two act largely separately.
    - `interaction("utilization", "history_months", pattern="none")`: ok
7. Debt-to-income ratio, number of dependents, and months at the current address have at most a moderate effect, while the number of recent credit inquiries and applicant age hardly matter.
    - `strength("dti") in ("negligible", "weak", "moderate")`: ok
    - `negligible("n_inquiries")`: ok
    - `negligible("age")`: ok
    - `strength("noise_2") in ("negligible", "weak", "moderate")`: ok
    - `strength("noise_1") in ("negligible", "weak", "moderate")`: ok
8. Income and age do not interact in the model's predictions.
    - `interaction("income", "age", pattern="none")`: ok

## syn-none-n5000-s1_XGB2_H1_d0_claude-haiku-5-5_plausible

**RELEASED_REDUCED**: failing sentences dropped after 2 repair round(s) (3 calls, 2 repair rounds)

### Version 0: proposer (16 claims, 6 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk generally increases as the share of the credit limit in use rises.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. Its effect is concentrated at high levels: risk shows a sharp step up once utilization passes about 0.72.
    - `threshold("utilization", at=0.719)`: **false**
3. Past delinquencies are the second or third most important driver, and having any delinquency raises the risk of default compared with having none.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
4. Annual income is also among the leading drivers, with higher income generally lowering the risk of default.
    - `strength("income") in ("weak", "moderate")`: **undecidable** (share band not settled against [2%, 15%))
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has at most a weak effect, with longer histories generally associated with lower risk.
    - `strength("history_months") in ("negligible", "weak")`: **undecidable** (share band not settled against [0%, 5%))
    - `direction("history_months") == "decreasing"`: ok
6. The effect of utilization grows with the number of past delinquencies, so high utilization matters more for applicants who have delinquencies.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: **undecidable**
7. The data do not settle whether the effect of utilization depends on credit history length.
    - `unsettled(interaction("utilization", "history_months", pattern="amplification"))`: ok
8. Debt-to-income ratio hardly matters, and the data do not show a clear pattern in its effect.
    - `negligible("dti")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
9. Age, number of dependents, months at address and recent credit inquiries have no detectable effect on predicted default risk.
    - `negligible("noise_2")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `negligible("n_inquiries")`: ok

### Version 1: repair 1 (16 claims, 1 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk generally increases as the share of the credit limit in use rises.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. Its effect is concentrated at high levels, with the largest step up appearing around 0.73, although the data do not settle the exact location of that step.
    - `unsettled(threshold("utilization", at=0.735))`: **false** (the claim is settled: it is false)
3. Past delinquencies are the second or third most important driver, and having any delinquency raises the risk of default compared with having none.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
4. Annual income is also among the leading drivers, with higher income generally lowering the risk of default, though the data do not settle whether its effect is weak or moderate.
    - `direction("income") == "decreasing"`: ok
    - `unsettled(strength("income") in ("weak", "moderate"))`: ok
5. Length of credit history generally lowers risk as it lengthens, but the data do not settle whether its effect is negligible, weak or moderate.
    - `direction("history_months") == "decreasing"`: ok
    - `unsettled(strength("history_months") in ("negligible", "weak"))`: ok
6. The data do not settle whether the effect of utilization grows with the number of past delinquencies.
    - `unsettled(interaction("utilization", "n_delinquencies", pattern="amplification"))`: ok
7. The data do not settle whether the effect of utilization depends on credit history length.
    - `unsettled(interaction("utilization", "history_months", pattern="amplification"))`: ok
8. The data do not settle whether debt-to-income ratio matters, as no clear pattern in its effect is shown.
    - `unsettled(negligible("dti"))`: ok
9. Age, months at address and recent credit inquiries have no detectable effect on predicted default risk, and the data do not settle whether the number of dependents matters.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `negligible("n_inquiries")`: ok
    - `unsettled(negligible("noise_2"))`: ok

### Version 2: repair 2 (16 claims, 1 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk generally increases as the share of the credit limit in use rises.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. Its effect is concentrated at high levels, and the data do not settle the exact location of the step up in risk, which lies somewhere in the upper part of the range.
    - `unsettled(threshold("utilization", at=0.72))`: **false** (the claim is settled: it is false)
3. Past delinquencies are the second or third most important driver, and having any delinquency raises the risk of default compared with having none.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
4. Annual income is also among the leading drivers, with higher income generally lowering the risk of default, though the data do not settle whether its effect is weak or moderate.
    - `direction("income") == "decreasing"`: ok
    - `unsettled(strength("income") in ("weak", "moderate"))`: ok
5. Length of credit history generally lowers risk as it lengthens, but the data do not settle whether its effect is negligible, weak or moderate.
    - `direction("history_months") == "decreasing"`: ok
    - `unsettled(strength("history_months") in ("negligible", "weak"))`: ok
6. The data do not settle whether the effect of utilization grows with the number of past delinquencies.
    - `unsettled(interaction("utilization", "n_delinquencies", pattern="amplification"))`: ok
7. The data do not settle whether the effect of utilization depends on credit history length.
    - `unsettled(interaction("utilization", "history_months", pattern="amplification"))`: ok
8. The data do not settle whether debt-to-income ratio matters, as no clear pattern in its effect is shown.
    - `unsettled(negligible("dti"))`: ok
9. Age, months at address and recent credit inquiries have no detectable effect on predicted default risk, and the data do not settle whether the number of dependents matters.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `negligible("n_inquiries")`: ok
    - `unsettled(negligible("noise_2"))`: ok

### Version 3: reduced (15 claims, 0 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk generally increases as the share of the credit limit in use rises.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
3. Past delinquencies are the second or third most important driver, and having any delinquency raises the risk of default compared with having none.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
4. Annual income is also among the leading drivers, with higher income generally lowering the risk of default, though the data do not settle whether its effect is weak or moderate.
    - `direction("income") == "decreasing"`: ok
    - `unsettled(strength("income") in ("weak", "moderate"))`: ok
5. Length of credit history generally lowers risk as it lengthens, but the data do not settle whether its effect is negligible, weak or moderate.
    - `direction("history_months") == "decreasing"`: ok
    - `unsettled(strength("history_months") in ("negligible", "weak"))`: ok
6. The data do not settle whether the effect of utilization grows with the number of past delinquencies.
    - `unsettled(interaction("utilization", "n_delinquencies", pattern="amplification"))`: ok
7. The data do not settle whether the effect of utilization depends on credit history length.
    - `unsettled(interaction("utilization", "history_months", pattern="amplification"))`: ok
8. The data do not settle whether debt-to-income ratio matters, as no clear pattern in its effect is shown.
    - `unsettled(negligible("dti"))`: ok
9. Age, months at address and recent credit inquiries have no detectable effect on predicted default risk, and the data do not settle whether the number of dependents matters.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `negligible("n_inquiries")`: ok
    - `unsettled(negligible("noise_2"))`: ok

## syn-none-n5000-s1_XGB2_H2_d0_claude-haiku-5-5_plausible

**RELEASED**: passed after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (20 claims, 0 failing)
1. Revolving credit utilization is the most important driver of default risk, with a strong effect: risk rises as the share of the credit limit in use goes up, and the increase is sharpest once utilization passes about 72%.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second or third most important driver, with a moderate to strong effect, and default risk jumps once an applicant has at least one delinquency.
    - `threshold("n_delinquencies", at=1.0)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
3. Income is also the second or third most important driver, with a moderate to strong effect: higher income lowers default risk.
    - `rank("income") in (2, 3)`: ok
    - `direction("income") == "decreasing"`: ok
    - `strength("income") in ("moderate", "strong")`: ok
4. Length of credit history matters at most moderately and is ranked fourth to sixth; default risk decreases as the history gets longer.
    - `direction("history_months") == "decreasing"`: ok
    - `strength("history_months") in ("negligible", "weak", "moderate")`: ok
    - `rank("history_months") in (4, 5, 6)`: ok
5. The debt-to-income ratio ranks fourth to eighth and has at most a moderate effect, and the data do not settle how its effect is shaped.
    - `strength("dti") in ("negligible", "weak", "moderate")`: ok
    - `rank("dti") in (4, 5, 6, 7, 8)`: ok
6. Age, months at the current address and the number of recent credit inquiries hardly matter for default risk.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `negligible("n_inquiries")`: ok
7. Utilization and income do not interact, while the data do not settle whether utilization and past delinquencies interact.
    - `interaction("utilization", "income", pattern="none")`: ok
    - `unsettled(interaction("utilization", "n_delinquencies", pattern="none"))`: ok
