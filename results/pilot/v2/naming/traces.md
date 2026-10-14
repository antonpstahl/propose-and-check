# Pilot traces: naming

## syn-dominant-n50000-s1_EBM_H1_d0_claude-haiku-5-5_opaque

**RELEASED_REDUCED**: failing sentences dropped after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (14 claims, 3 failing)
1. Revolving credit utilization is the most important driver of predicted default, and risk rises steadily as the share of the credit limit in use grows, with the steepest increase at the highest utilization levels.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk increases as delinquencies accumulate, with the largest rise between zero and one past delinquency.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Higher annual income generally lowers predicted risk, with the effect strongest at the bottom of the income range.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
4. A longer credit history generally lowers predicted risk, and the effect is moderate to weak in size.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
5. A higher debt-to-income ratio generally increases predicted risk, but the effect is weak.
    - `strength("dti") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("dti") == "increasing"`: ok
6. The effect of utilization grows with the number of past delinquencies: high utilization matters far more for applicants who have delinquencies on their file.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
7. The effect of recent credit inquiries reverses with credit history length: for short histories more inquiries raise risk, while for long histories they lower it.
    - `interaction("history_months", "n_inquiries", pattern="sign_flip")`: **undecidable**
8. Applicant age hardly matters to the model's predictions.
    - `negligible("age")`: ok
9. The data do not settle whether the two application attributes, feature_a and feature_b, matter for predicted default.
    - `unsettled(negligible("noise_1"))`: **false** (the claim is settled: it is true)

### Version 1: reduced (10 claims, 0 failing)
1. Revolving credit utilization is the most important driver of predicted default, and risk rises steadily as the share of the credit limit in use grows, with the steepest increase at the highest utilization levels.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk increases as delinquencies accumulate, with the largest rise between zero and one past delinquency.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Higher annual income generally lowers predicted risk, with the effect strongest at the bottom of the income range.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
4. A longer credit history generally lowers predicted risk, and the effect is moderate to weak in size.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The effect of utilization grows with the number of past delinquencies: high utilization matters far more for applicants who have delinquencies on their file.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
8. Applicant age hardly matters to the model's predictions.
    - `negligible("age")`: ok

## syn-dominant-n50000-s1_EBM_H1_d0_claude-haiku-5-5_plausible

**RELEASED_REDUCED**: failing sentences dropped after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (14 claims, 0 failing)
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
8. Age hardly matters.
    - `negligible("age")`: ok
    - format error: sentence 7: unsettled(strength("num_dependents") == "negligible"): strength is one of ['weak', 'moderate', 'strong']

### Version 1: reduced (14 claims, 0 failing)
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
8. Age hardly matters.
    - `negligible("age")`: ok

## syn-dominant-n50000-s1_EBM_H1_d1_claude-haiku-5-5_opaque

**RELEASED_REDUCED**: failing sentences dropped after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (14 claims, 3 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises as the share of the credit limit in use grows.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk rises from zero to two or more delinquencies.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. The two drive each other: utilization matters far more for applicants with two delinquencies than for those with none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income is among the next most important features, and risk generally falls as income rises.
    - `rank("income") in (3, 4)`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history is also among the next most important features, and risk generally falls as the history gets longer.
    - `rank("history_months") in (3, 4)`: ok
    - `direction("history_months") == "decreasing"`: ok
6. Debt-to-income ratio has a weak effect, and risk increases with it.
    - `strength("dti") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("dti") == "increasing"`: ok
7. Applicant age has a negligible share of importance, and the data do not settle whether the two application attributes, feature_a and feature_b, matter.
    - `negligible("age")`: ok
    - `unsettled(negligible("noise_1"))`: **false** (the claim is settled: it is true)
    - `unsettled(negligible("noise_2"))`: **false** (the claim is settled: it is true)

### Version 1: reduced (9 claims, 0 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises as the share of the credit limit in use grows.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk rises from zero to two or more delinquencies.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. The two drive each other: utilization matters far more for applicants with two delinquencies than for those with none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income is among the next most important features, and risk generally falls as income rises.
    - `rank("income") in (3, 4)`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history is also among the next most important features, and risk generally falls as the history gets longer.
    - `rank("history_months") in (3, 4)`: ok
    - `direction("history_months") == "decreasing"`: ok

## syn-dominant-n50000-s1_EBM_H1_d1_claude-haiku-5-5_plausible

**RELEASED_REDUCED**: failing sentences dropped after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (13 claims, 1 failing)
1. Revolving credit utilization is the most important driver of default risk, accounting for roughly 28% of the model's importance, and risk rises as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `share("utilization") == approx(0.28)`: ok
2. The number of past delinquencies is the second most important driver, and risk increases with it, with the largest rise between zero and one or two delinquencies.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `share("n_delinquencies") == approx(0.17)`: ok
3. The two leading drivers reinforce each other: the effect of utilization grows with the number of past delinquencies, so high utilization matters far more for applicants with delinquencies on file.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Higher income is associated with lower risk, though income ranks third or fourth in importance and its effect is modest.
    - `direction("income") == "decreasing"`: ok
    - `rank("income") in (3, 4)`: ok
5. Longer credit history is associated with lower risk, and this feature also ranks third or fourth in importance.
    - `direction("history_months") == "decreasing"`: ok
    - `rank("history_months") in (3, 4)`: ok
6. Debt-to-income ratio has a weak effect, with risk generally increasing as it rises above about 0.44.
    - `strength("dti") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("dti") == "increasing"`: ok
7. The data do not settle whether the number of dependents or the age of the applicant matters for default risk.
    - format error: sentence 7: unsettled(strength("num_dependents") == "negligible"): strength is one of ['weak', 'moderate', 'strong']
    - format error: sentence 7: unsettled(strength("age") == "negligible"): strength is one of ['weak', 'moderate', 'strong']

### Version 1: reduced (11 claims, 0 failing)
1. Revolving credit utilization is the most important driver of default risk, accounting for roughly 28% of the model's importance, and risk rises as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `share("utilization") == approx(0.28)`: ok
2. The number of past delinquencies is the second most important driver, and risk increases with it, with the largest rise between zero and one or two delinquencies.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `share("n_delinquencies") == approx(0.17)`: ok
3. The two leading drivers reinforce each other: the effect of utilization grows with the number of past delinquencies, so high utilization matters far more for applicants with delinquencies on file.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Higher income is associated with lower risk, though income ranks third or fourth in importance and its effect is modest.
    - `direction("income") == "decreasing"`: ok
    - `rank("income") in (3, 4)`: ok
5. Longer credit history is associated with lower risk, and this feature also ranks third or fourth in importance.
    - `direction("history_months") == "decreasing"`: ok
    - `rank("history_months") in (3, 4)`: ok

## syn-dominant-n50000-s1_EBM_H1_d2_claude-haiku-5-5_opaque

**RELEASED_REDUCED**: failing sentences dropped after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (11 claims, 1 failing)
1. Revolving credit utilization is the most important driver of predicted default, and risk rises steeply as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk increases with it, with most of the rise occurring between none and one or two delinquencies.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. The two interact strongly: the effect of utilization is much larger for applicants with delinquencies, and the effect of delinquencies is much larger at high utilization.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income is among the next most important features, and predicted risk decreases as income goes up.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history is also among the next most important features, and predicted risk decreases as the history gets longer.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. Debt-to-income ratio has at most a weak effect, with risk increasing as the ratio rises.
    - `strength("dti") in ("negligible", "weak")`: **undecidable** (share band not settled against [0%, 5%))
    - `direction("dti") == "increasing"`: ok
7. The data do not settle whether age, feature_a or feature_b matter, as their effects are too small to resolve at this sample size.
    - format error: sentence 7: unsettled(strength("age") == "negligible"): strength is one of ['weak', 'moderate', 'strong']
    - format error: sentence 7: unsettled(strength("feature_a") == "negligible"): strength is one of ['weak', 'moderate', 'strong']
    - format error: sentence 7: unsettled(strength("feature_b") == "negligible"): strength is one of ['weak', 'moderate', 'strong']

### Version 1: reduced (9 claims, 0 failing)
1. Revolving credit utilization is the most important driver of predicted default, and risk rises steeply as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk increases with it, with most of the rise occurring between none and one or two delinquencies.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. The two interact strongly: the effect of utilization is much larger for applicants with delinquencies, and the effect of delinquencies is much larger at high utilization.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income is among the next most important features, and predicted risk decreases as income goes up.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history is also among the next most important features, and predicted risk decreases as the history gets longer.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok

## syn-dominant-n50000-s1_EBM_H1_d2_claude-haiku-5-5_plausible

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (16 claims, 4 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk increases as the share of the credit limit in use rises.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. Its effect is strongest at high utilization, rising steeply above about 0.785, while the number of past delinquencies is the second most important driver and risk increases with it.
    - `threshold("utilization", at=0.785)`: **false**
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. The two interact strongly: the effect of utilization grows with the number of past delinquencies, so high utilization matters far more for applicants with delinquencies on file.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Annual income and length of credit history are the third and fourth most important drivers, and risk decreases as both rise.
    - `rank("income") in (3, 4)`: ok
    - `direction("income") == "decreasing"`: ok
5. Debt-to-income ratio adds a weak to moderate increase in risk, and recent credit inquiries have at most a weak effect.
    - `rank("history_months") in (3, 4)`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The data do not settle whether the number of dependents or months at the current address matter for predictions, and applicant age hardly matters.
    - `strength("dti") in ("weak", "moderate")`: ok
    - `direction("dti") == "increasing"`: ok
7. History length and recent inquiries reverse direction with each other: a longer history lowers risk only when inquiries are frequent.
    - `negligible("age")`: ok
    - `unsettled(negligible("noise_2"))`: **false** (the claim is settled: it is true)
    - `unsettled(negligible("noise_1"))`: **false** (the claim is settled: it is true)
8. Overall the model rests mainly on credit utilization and delinquency history, with the other features playing supporting roles.
    - `interaction("history_months", "n_inquiries", pattern="sign_flip")`: **undecidable**

### Version 1: reduced (9 claims, 0 failing, missing: n_delinquencies)
1. Revolving credit utilization is the most important driver of default risk, and risk increases as the share of the credit limit in use rises.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
3. The two interact strongly: the effect of utilization grows with the number of past delinquencies, so high utilization matters far more for applicants with delinquencies on file.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Annual income and length of credit history are the third and fourth most important drivers, and risk decreases as both rise.
    - `rank("income") in (3, 4)`: ok
    - `direction("income") == "decreasing"`: ok
5. Debt-to-income ratio adds a weak to moderate increase in risk, and recent credit inquiries have at most a weak effect.
    - `rank("history_months") in (3, 4)`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The data do not settle whether the number of dependents or months at the current address matter for predictions, and applicant age hardly matters.
    - `strength("dti") in ("weak", "moderate")`: ok
    - `direction("dti") == "increasing"`: ok

### Version 2: template (19 claims, 0 failing)
1. Credit utilization has a strong effect on default risk; default risk increases with credit utilization.
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies has a strong effect on default risk; default risk increases with the number of past delinquencies.
    - `strength("n_delinquencies") == "strong"`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Default risk jumps at the number of past delinquencies = 0.5.
    - `threshold("n_delinquencies", at=0.5)`: ok
4. Income has a moderate effect on default risk; default risk decreases with income.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
5. The length of credit history has a moderate effect on default risk; default risk decreases with the length of credit history.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has a weak to moderate effect on default risk; default risk increases with the debt-to-income ratio.
    - `strength("dti") in ("weak", "moderate")`: ok
    - `direction("dti") == "increasing"`: ok
7. The number of recent inquiries has at most a weak effect on default risk; default risk increases with the number of recent inquiries.
    - `strength("n_inquiries") in ("negligible", "weak")`: ok
    - `direction("n_inquiries") == "increasing"`: ok
8. The number of dependents hardly matters for default risk.
    - `negligible("noise_2")`: ok
9. Months at the current address hardly matters for default risk.
    - `negligible("noise_1")`: ok
10. Age hardly matters for default risk.
    - `negligible("age")`: ok
11. The effect of credit utilization grows with the number of past delinquencies.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
12. The effect of the number of past delinquencies reverses its sign as credit utilization changes.
    - `interaction("n_delinquencies", "utilization", pattern="sign_flip")`: ok
13. The effect of the number of recent inquiries reverses its sign as the length of credit history changes.
    - `interaction("n_inquiries", "history_months", pattern="sign_flip")`: ok

## syn-dominant-n50000-s1_EBM_H1_d3_claude-haiku-5-5_opaque

**RELEASED_REDUCED**: failing sentences dropped after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (14 claims, 2 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises steeply as the share of the credit limit in use climbs above about 0.5.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk generally increases with it.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. The effect of utilization grows with the number of past delinquencies: a high utilization adds much more risk for applicants who have delinquencies than for those who have none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income is among the third or fourth most important drivers, and risk decreases as income rises.
    - `rank("income") in (3, 4)`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history is also among the third or fourth most important drivers, and risk decreases as the history gets longer.
    - `rank("history_months") in (3, 4)`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has at most a weak effect, and risk increases with it.
    - `strength("dti") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("dti") == "increasing"`: ok
7. Age hardly matters. The data do not settle whether feature_a or feature_b affects default risk.
    - `negligible("age")`: ok
    - `unsettled(negligible("noise_1"))`: **false** (the claim is settled: it is true)
    - `unsettled(direction("noise_2") == "decreasing")`: ok

### Version 1: reduced (9 claims, 0 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises steeply as the share of the credit limit in use climbs above about 0.5.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk generally increases with it.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. The effect of utilization grows with the number of past delinquencies: a high utilization adds much more risk for applicants who have delinquencies than for those who have none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income is among the third or fourth most important drivers, and risk decreases as income rises.
    - `rank("income") in (3, 4)`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history is also among the third or fourth most important drivers, and risk decreases as the history gets longer.
    - `rank("history_months") in (3, 4)`: ok
    - `direction("history_months") == "decreasing"`: ok

## syn-dominant-n50000-s1_EBM_H1_d3_claude-haiku-5-5_plausible

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: template (19 claims, 0 failing)
1. Credit utilization has a strong effect on default risk; default risk increases with credit utilization.
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies has a strong effect on default risk; default risk increases with the number of past delinquencies.
    - `strength("n_delinquencies") == "strong"`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Default risk jumps at the number of past delinquencies = 0.5.
    - `threshold("n_delinquencies", at=0.5)`: ok
4. Income has a moderate effect on default risk; default risk decreases with income.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
5. The length of credit history has a moderate effect on default risk; default risk decreases with the length of credit history.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has a weak to moderate effect on default risk; default risk increases with the debt-to-income ratio.
    - `strength("dti") in ("weak", "moderate")`: ok
    - `direction("dti") == "increasing"`: ok
7. The number of recent inquiries has at most a weak effect on default risk; default risk increases with the number of recent inquiries.
    - `strength("n_inquiries") in ("negligible", "weak")`: ok
    - `direction("n_inquiries") == "increasing"`: ok
8. The number of dependents hardly matters for default risk.
    - `negligible("noise_2")`: ok
9. Months at the current address hardly matters for default risk.
    - `negligible("noise_1")`: ok
10. Age hardly matters for default risk.
    - `negligible("age")`: ok
11. The effect of credit utilization grows with the number of past delinquencies.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
12. The effect of the number of past delinquencies reverses its sign as credit utilization changes.
    - `interaction("n_delinquencies", "utilization", pattern="sign_flip")`: ok
13. The effect of the number of recent inquiries reverses its sign as the length of credit history changes.
    - `interaction("n_inquiries", "history_months", pattern="sign_flip")`: ok

## syn-dominant-n50000-s1_EBM_H1_d4_claude-haiku-5-5_opaque

**RELEASED_REDUCED**: failing sentences dropped after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (14 claims, 1 failing)
1. Revolving credit utilization is the most important driver of default risk, with about 28% of the model's importance, and risk generally increases as utilization rises across its range.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `share("utilization") == approx(0.279)`: ok
2. The number of past delinquencies is the second most important driver, and risk increases with it, rising most sharply between no delinquencies and two or more.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `share("n_delinquencies") == approx(0.172)`: ok
3. The effect of utilization grows strongly with delinquencies: at high utilization the added risk from each delinquency is far larger than at low utilization.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income and length of credit history each have a weak to moderate effect, with higher income and longer history associated with lower risk.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
5. Debt-to-income ratio has a weak to moderate effect, and risk increases as that ratio rises.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. Recent credit inquiries interact with credit history length: the effect of history length reverses depending on the number of inquiries.
    - `interaction("history_months", "n_inquiries", pattern="sign_flip")`: **undecidable**
7. The data do not settle whether the remaining features, such as the two standardised application attributes and applicant age, matter for predictions.
    - `strength("dti") in ("weak", "moderate")`: ok
    - `direction("dti") == "increasing"`: ok
    - format error: sentence 8: unsettled(negligible("feature_a")): there is no sentence with this id
    - format error: sentence 8: unsettled(negligible("feature_b")): there is no sentence with this id

### Version 1: reduced (13 claims, 0 failing)
1. Revolving credit utilization is the most important driver of default risk, with about 28% of the model's importance, and risk generally increases as utilization rises across its range.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `share("utilization") == approx(0.279)`: ok
2. The number of past delinquencies is the second most important driver, and risk increases with it, rising most sharply between no delinquencies and two or more.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `share("n_delinquencies") == approx(0.172)`: ok
3. The effect of utilization grows strongly with delinquencies: at high utilization the added risk from each delinquency is far larger than at low utilization.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income and length of credit history each have a weak to moderate effect, with higher income and longer history associated with lower risk.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
5. Debt-to-income ratio has a weak to moderate effect, and risk increases as that ratio rises.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
7. The data do not settle whether the remaining features, such as the two standardised application attributes and applicant age, matter for predictions.
    - `strength("dti") in ("weak", "moderate")`: ok
    - `direction("dti") == "increasing"`: ok

## syn-dominant-n50000-s1_EBM_H1_d4_claude-haiku-5-5_plausible

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (15 claims, 4 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises with it, with a strong effect that becomes steep for applicants using most of their credit limit.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `threshold("utilization", at=0.785)`: **false**
2. The number of past delinquencies is the second most important driver, and risk increases with it, rising most between no delinquencies and one delinquency.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. The effect of utilization grows with the number of past delinquencies: it is much larger for applicants with two delinquencies than for those with none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income has a weak to moderate effect, and risk decreases as income rises.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a weak to moderate effect, and risk decreases as the history gets longer.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has a weak effect, and risk increases with it.
    - `strength("dti") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("dti") == "increasing"`: ok
7. The data do not settle whether number of dependents or months at the current address matter, and age hardly matters.
    - `negligible("age")`: ok
    - `unsettled(negligible("noise_2"))`: **false** (the claim is settled: it is true)
    - `unsettled(negligible("noise_1"))`: **false** (the claim is settled: it is true)

### Version 1: reduced (7 claims, 0 failing, missing: utilization)
2. The number of past delinquencies is the second most important driver, and risk increases with it, rising most between no delinquencies and one delinquency.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. The effect of utilization grows with the number of past delinquencies: it is much larger for applicants with two delinquencies than for those with none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income has a weak to moderate effect, and risk decreases as income rises.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a weak to moderate effect, and risk decreases as the history gets longer.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok

### Version 2: template (19 claims, 0 failing)
1. Credit utilization has a strong effect on default risk; default risk increases with credit utilization.
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies has a strong effect on default risk; default risk increases with the number of past delinquencies.
    - `strength("n_delinquencies") == "strong"`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Default risk jumps at the number of past delinquencies = 0.5.
    - `threshold("n_delinquencies", at=0.5)`: ok
4. Income has a moderate effect on default risk; default risk decreases with income.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
5. The length of credit history has a moderate effect on default risk; default risk decreases with the length of credit history.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has a weak to moderate effect on default risk; default risk increases with the debt-to-income ratio.
    - `strength("dti") in ("weak", "moderate")`: ok
    - `direction("dti") == "increasing"`: ok
7. The number of recent inquiries has at most a weak effect on default risk; default risk increases with the number of recent inquiries.
    - `strength("n_inquiries") in ("negligible", "weak")`: ok
    - `direction("n_inquiries") == "increasing"`: ok
8. The number of dependents hardly matters for default risk.
    - `negligible("noise_2")`: ok
9. Months at the current address hardly matters for default risk.
    - `negligible("noise_1")`: ok
10. Age hardly matters for default risk.
    - `negligible("age")`: ok
11. The effect of credit utilization grows with the number of past delinquencies.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
12. The effect of the number of past delinquencies reverses its sign as credit utilization changes.
    - `interaction("n_delinquencies", "utilization", pattern="sign_flip")`: ok
13. The effect of the number of recent inquiries reverses its sign as the length of credit history changes.
    - `interaction("n_inquiries", "history_months", pattern="sign_flip")`: ok

## syn-dominant-n50000-s1_XGB2_H1_d0_claude-haiku-5-5_opaque

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (21 claims, 2 failing)
1. Revolving credit utilization is the most important driver of predicted default, with a strong effect that accounts for roughly a quarter of the model's importance, and risk rises as utilization increases.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
2. The number of past delinquencies is the second most important driver, with a strong effect, and risk rises as delinquencies accumulate.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
3. The effect of utilization grows with the number of delinquencies: at high utilization, each additional delinquency adds much more risk than at low utilization.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income and length of credit history each have a moderate to weak effect, both lowering predicted risk as they rise, and the data do not settle whether the two interact in a way that changes this picture.
    - `direction("income") == "decreasing"`: ok
    - `rank("income") in (3, 4)`: ok
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
    - `rank("history_months") in (3, 4)`: ok
    - `strength("history_months") in ("weak", "moderate")`: ok
5. The debt-to-income ratio has a moderate effect, and risk increases with it.
    - `strength("dti") == "moderate"`: **undecidable** (share band straddles a class edge)
    - `direction("dti") == "increasing"`: ok
6. The data do not settle whether the two application attributes, feature_a and feature_b, matter for predicted default, and the data do not settle the direction of feature_b.
    - `unsettled(negligible("noise_2"))`: ok
    - `unsettled(direction("noise_2") == "decreasing")`: ok
7. Applicant age hardly matters, and recent credit inquiries have at most a weak effect, with risk generally increasing as inquiries rise.
    - `negligible("age")`: ok
    - `unsettled(direction("noise_1") == "increasing")`: ok
    - `strength("n_inquiries") in ("negligible", "weak")`: ok
    - `direction("n_inquiries") == "increasing"`: ok

### Version 1: reduced (16 claims, 0 failing, missing: n_delinquencies)
1. Revolving credit utilization is the most important driver of predicted default, with a strong effect that accounts for roughly a quarter of the model's importance, and risk rises as utilization increases.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
3. The effect of utilization grows with the number of delinquencies: at high utilization, each additional delinquency adds much more risk than at low utilization.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income and length of credit history each have a moderate to weak effect, both lowering predicted risk as they rise, and the data do not settle whether the two interact in a way that changes this picture.
    - `direction("income") == "decreasing"`: ok
    - `rank("income") in (3, 4)`: ok
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
    - `rank("history_months") in (3, 4)`: ok
    - `strength("history_months") in ("weak", "moderate")`: ok
6. The data do not settle whether the two application attributes, feature_a and feature_b, matter for predicted default, and the data do not settle the direction of feature_b.
    - `unsettled(negligible("noise_2"))`: ok
    - `unsettled(direction("noise_2") == "decreasing")`: ok
7. Applicant age hardly matters, and recent credit inquiries have at most a weak effect, with risk generally increasing as inquiries rise.
    - `negligible("age")`: ok
    - `unsettled(direction("noise_1") == "increasing")`: ok
    - `strength("n_inquiries") in ("negligible", "weak")`: ok
    - `direction("n_inquiries") == "increasing"`: ok

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
7. Feature b has at most a weak effect on default risk.
    - `strength("noise_2") in ("negligible", "weak")`: ok
8. The number of recent inquiries has at most a weak effect on default risk; default risk increases with the number of recent inquiries.
    - `strength("n_inquiries") in ("negligible", "weak")`: ok
    - `direction("n_inquiries") == "increasing"`: ok
9. Feature a hardly matters for default risk.
    - `negligible("noise_1")`: ok
10. Age hardly matters for default risk.
    - `negligible("age")`: ok
11. The effect of credit utilization grows with the number of past delinquencies.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok

## syn-dominant-n50000-s1_XGB2_H1_d0_claude-haiku-5-5_plausible

**RELEASED_REDUCED**: failing sentences dropped after 0 repair round(s) (1 calls, 0 repair rounds)

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

### Version 1: reduced (14 claims, 0 failing)
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
8. Age and months at the current address hardly matter for the predictions.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok

## syn-dominant-n50000-s1_XGB2_H1_d1_claude-haiku-5-5_opaque

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (16 claims, 2 failing)
1. Revolving credit utilization is the most important driver of predicted default, accounting for roughly a quarter of the model's importance, and risk rises steadily as utilization increases.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and each additional delinquency, up to two, raises predicted default risk.
    - `rank("n_delinquencies") == 2`: ok
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
    - `direction("n_delinquencies") == "increasing"`: ok
3. The effect of utilization grows with the number of delinquencies: at zero delinquencies a higher utilization adds only a modest amount of risk, while with two delinquencies the same change adds a much larger amount.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Higher income lowers predicted risk, with a weak to moderate effect.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
5. A longer credit history lowers predicted risk, with a weak to moderate effect that is somewhat weaker when there are many recent inquiries.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. A higher debt-to-income ratio raises predicted risk, but its effect is small.
    - `strength("dti") in ("weak", "moderate")`: ok
    - `direction("dti") == "increasing"`: ok
7. The data do not settle whether feature_a or feature_b matter, and the applicant's age hardly matters to the predictions.
    - `unsettled(negligible("noise_2"))`: ok
    - `negligible("age")`: ok
    - `unsettled(negligible("noise_1"))`: **false** (the claim is settled: it is true)

### Version 1: reduced (10 claims, 0 failing, missing: n_delinquencies)
1. Revolving credit utilization is the most important driver of predicted default, accounting for roughly a quarter of the model's importance, and risk rises steadily as utilization increases.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
3. The effect of utilization grows with the number of delinquencies: at zero delinquencies a higher utilization adds only a modest amount of risk, while with two delinquencies the same change adds a much larger amount.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Higher income lowers predicted risk, with a weak to moderate effect.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
5. A longer credit history lowers predicted risk, with a weak to moderate effect that is somewhat weaker when there are many recent inquiries.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. A higher debt-to-income ratio raises predicted risk, but its effect is small.
    - `strength("dti") in ("weak", "moderate")`: ok
    - `direction("dti") == "increasing"`: ok

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
7. Feature b has at most a weak effect on default risk.
    - `strength("noise_2") in ("negligible", "weak")`: ok
8. The number of recent inquiries has at most a weak effect on default risk; default risk increases with the number of recent inquiries.
    - `strength("n_inquiries") in ("negligible", "weak")`: ok
    - `direction("n_inquiries") == "increasing"`: ok
9. Feature a hardly matters for default risk.
    - `negligible("noise_1")`: ok
10. Age hardly matters for default risk.
    - `negligible("age")`: ok
11. The effect of credit utilization grows with the number of past delinquencies.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok

## syn-dominant-n50000-s1_XGB2_H1_d1_claude-haiku-5-5_plausible

**RELEASED_REDUCED**: failing sentences dropped after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (14 claims, 2 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises steeply as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk increases with more delinquencies.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. The effect of utilization grows with the number of past delinquencies: it adds much more risk for applicants who have had delinquencies than for those who have not.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income is among the third or fourth most important drivers, and higher income decreases default risk.
    - `rank("income") in (3, 4)`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history is also among the third or fourth most important drivers, and longer histories decrease default risk.
    - `rank("history_months") in (3, 4)`: ok
    - `direction("history_months") == "decreasing"`: ok
6. Debt-to-income ratio has a weak effect, and risk increases with it.
    - `strength("dti") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("dti") == "increasing"`: ok
7. The data do not settle whether the number of dependents matters, since no movement in its curve is resolved at this sample size.
    - `unsettled(strength("noise_2") in ("negligible", "weak"))`: **false** (the claim is settled: it is true)
8. Recent credit inquiries have at most a weak effect, and applicant age hardly matters.
    - `strength("n_inquiries") in ("negligible", "weak")`: ok
    - `negligible("age")`: ok

### Version 1: reduced (11 claims, 0 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises steeply as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk increases with more delinquencies.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. The effect of utilization grows with the number of past delinquencies: it adds much more risk for applicants who have had delinquencies than for those who have not.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income is among the third or fourth most important drivers, and higher income decreases default risk.
    - `rank("income") in (3, 4)`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history is also among the third or fourth most important drivers, and longer histories decrease default risk.
    - `rank("history_months") in (3, 4)`: ok
    - `direction("history_months") == "decreasing"`: ok
8. Recent credit inquiries have at most a weak effect, and applicant age hardly matters.
    - `strength("n_inquiries") in ("negligible", "weak")`: ok
    - `negligible("age")`: ok

## syn-dominant-n50000-s1_XGB2_H1_d2_claude-haiku-5-5_opaque

**RELEASED_REDUCED**: failing sentences dropped after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (15 claims, 2 failing)
1. Revolving credit utilization is the most important driver of default risk, accounting for about 27% of the model's importance, and risk increases as utilization rises.
    - `rank("utilization") == 1`: ok
    - `share("utilization") == approx(0.268)`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk increases with it, rising most clearly between zero and two delinquencies.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. The two largest drivers interact: the effect of utilization grows with the number of past delinquencies, so high utilization matters far more for applicants with delinquencies.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Higher income is associated with lower default risk, and income is among the next most important features, though its effect is moderate to weak.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
5. Longer credit history is associated with lower risk, with an effect of similar moderate to weak size to income.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has a weak to moderate effect, and risk increases with it.
    - `strength("dti") in ("weak", "moderate")`: ok
    - `direction("dti") == "increasing"`: ok
7. Age and the two application attributes feature_a and feature_b hardly matter; for feature_a the data do not settle whether it matters at all.
    - `negligible("noise_2")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("age")`: ok
    - `unsettled(negligible("noise_1"))`: **false** (the claim is settled: it is true)

### Version 1: reduced (12 claims, 0 failing)
1. Revolving credit utilization is the most important driver of default risk, accounting for about 27% of the model's importance, and risk increases as utilization rises.
    - `rank("utilization") == 1`: ok
    - `share("utilization") == approx(0.268)`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk increases with it, rising most clearly between zero and two delinquencies.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. The two largest drivers interact: the effect of utilization grows with the number of past delinquencies, so high utilization matters far more for applicants with delinquencies.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Higher income is associated with lower default risk, and income is among the next most important features, though its effect is moderate to weak.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
5. Longer credit history is associated with lower risk, with an effect of similar moderate to weak size to income.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has a weak to moderate effect, and risk increases with it.
    - `strength("dti") in ("weak", "moderate")`: ok
    - `direction("dti") == "increasing"`: ok

## syn-dominant-n50000-s1_XGB2_H1_d2_claude-haiku-5-5_plausible

**RELEASED_REDUCED**: failing sentences dropped after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (10 claims, 0 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk generally increases as the share of the credit limit in use rises, with the steepest rise at the highest levels.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk increases with it, rising most between zero and two delinquencies.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. The effect of utilization grows with the number of past delinquencies: the rise in risk from higher utilization is much larger for applicants with two delinquencies than for those with none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income has a weak to moderate effect, and risk decreases as income rises.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a weak to moderate effect, and risk decreases as the history gets longer.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The data do not settle whether the number of dependents or months at the current address matter for risk.
7. Age hardly matters for the model's predictions.
    - `negligible("age")`: ok
    - format error: sentence 6: unsettled(strength("num_dependents") == "negligible"): strength is one of ['weak', 'moderate', 'strong']
    - format error: sentence 6: unsettled(strength("months_at_address") == "negligible"): strength is one of ['weak', 'moderate', 'strong']

### Version 1: reduced (10 claims, 0 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk generally increases as the share of the credit limit in use rises, with the steepest rise at the highest levels.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk increases with it, rising most between zero and two delinquencies.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. The effect of utilization grows with the number of past delinquencies: the rise in risk from higher utilization is much larger for applicants with two delinquencies than for those with none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income has a weak to moderate effect, and risk decreases as income rises.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a weak to moderate effect, and risk decreases as the history gets longer.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
7. Age hardly matters for the model's predictions.
    - `negligible("age")`: ok

## syn-dominant-n50000-s1_XGB2_H1_d3_claude-haiku-5-5_opaque

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (17 claims, 2 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises steadily as the share of the credit limit in use goes up, with the largest increase at the highest levels.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
2. The number of past delinquencies is the second most important driver, and risk goes up as delinquencies accumulate.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
3. The effect of utilization grows with the number of delinquencies: for applicants with no past delinquencies, higher utilization adds moderate risk, but for applicants with two delinquencies it adds far more.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income and length of credit history come next in importance: higher income generally lowers risk, and a longer credit history generally lowers risk.
    - `direction("income") == "decreasing"`: ok
    - `rank("income") in (3, 4)`: ok
    - `direction("history_months") == "decreasing"`: ok
    - `rank("history_months") in (3, 4)`: ok
5. The debt-to-income ratio has a moderate effect, and risk increases with it.
    - `strength("dti") == "moderate"`: **undecidable** (share band straddles a class edge)
    - `direction("dti") == "increasing"`: ok
6. The number of recent credit inquiries has at most a weak effect, and the data do not settle whether the two application attributes matter.
    - `direction("n_inquiries") == "increasing"`: ok
    - `strength("n_inquiries") in ("negligible", "weak")`: ok
7. Age and the remaining application attributes hardly matter for the model's predictions.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - format error: sentence 6: unsettled(strength("feature_b") == "negligible"): strength is one of ['weak', 'moderate', 'strong']

### Version 1: reduced (10 claims, 0 failing, missing: n_delinquencies)
1. Revolving credit utilization is the most important driver of default risk, and risk rises steadily as the share of the credit limit in use goes up, with the largest increase at the highest levels.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
3. The effect of utilization grows with the number of delinquencies: for applicants with no past delinquencies, higher utilization adds moderate risk, but for applicants with two delinquencies it adds far more.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income and length of credit history come next in importance: higher income generally lowers risk, and a longer credit history generally lowers risk.
    - `direction("income") == "decreasing"`: ok
    - `rank("income") in (3, 4)`: ok
    - `direction("history_months") == "decreasing"`: ok
    - `rank("history_months") in (3, 4)`: ok
7. Age and the remaining application attributes hardly matter for the model's predictions.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok

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
7. Feature b has at most a weak effect on default risk.
    - `strength("noise_2") in ("negligible", "weak")`: ok
8. The number of recent inquiries has at most a weak effect on default risk; default risk increases with the number of recent inquiries.
    - `strength("n_inquiries") in ("negligible", "weak")`: ok
    - `direction("n_inquiries") == "increasing"`: ok
9. Feature a hardly matters for default risk.
    - `negligible("noise_1")`: ok
10. Age hardly matters for default risk.
    - `negligible("age")`: ok
11. The effect of credit utilization grows with the number of past delinquencies.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok

## syn-dominant-n50000-s1_XGB2_H1_d3_claude-haiku-5-5_plausible

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (17 claims, 2 failing)
1. Revolving credit utilization is the most important driver of default risk, with about 27% of the model's importance, and risk rises steeply as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk increases with it, rising noticeably from zero to two or more delinquencies.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
3. The effect of utilization grows with the number of past delinquencies, so a high utilization adds much more risk for applicants who have been delinquent before.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income is a moderate driver among the top four: higher income generally lowers the predicted risk, and the effect is largest at the low end of the income range.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
    - `rank("income") in (3, 4)`: ok
5. Length of credit history is also a moderate driver, with longer histories generally lowering risk.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok
    - `rank("history_months") in (3, 4)`: ok
6. The debt-to-income ratio has a moderate effect, with risk generally increasing as the ratio rises.
    - `strength("dti") == "moderate"`: **undecidable** (share band straddles a class edge)
    - `direction("dti") == "increasing"`: ok
7. The data do not settle whether number of dependents or the other remaining features matter, and age has at most a weak effect.
    - `unsettled(direction("age") == "increasing")`: ok
    - `strength("age") in ("negligible", "weak")`: ok
    - format error: sentence 7: unsettled(strength("num_dependents") == "negligible"): strength is one of ['weak', 'moderate', 'strong']

### Version 1: reduced (10 claims, 0 failing, missing: n_delinquencies)
1. Revolving credit utilization is the most important driver of default risk, with about 27% of the model's importance, and risk rises steeply as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
3. The effect of utilization grows with the number of past delinquencies, so a high utilization adds much more risk for applicants who have been delinquent before.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income is a moderate driver among the top four: higher income generally lowers the predicted risk, and the effect is largest at the low end of the income range.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
    - `rank("income") in (3, 4)`: ok
5. Length of credit history is also a moderate driver, with longer histories generally lowering risk.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok
    - `rank("history_months") in (3, 4)`: ok

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

## syn-dominant-n50000-s1_XGB2_H1_d4_claude-haiku-5-5_opaque

**RELEASED_REDUCED**: failing sentences dropped after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (12 claims, 2 failing)
1. Revolving credit utilization is the most important driver of predicted default, and risk rises steadily as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk increases with it, with the largest rise from none to two or more.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. The effect of utilization grows with the number of delinquencies: a high utilization adds much more risk for applicants with past delinquencies than for those without.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Annual income is among the third or fourth most important features, and higher income generally lowers predicted risk.
    - `rank("income") in (3, 4)`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history is also among the third or fourth most important features, and longer histories generally lower predicted risk.
    - `rank("history_months") in (3, 4)`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has at most a weak effect, with risk somewhat higher above about 0.43.
    - `strength("dti") in ("negligible", "weak")`: **undecidable** (share band not settled against [0%, 5%))
7. The data do not settle whether feature_b or age matter for predictions.
    - `unsettled(strength("noise_2") == "weak")`: ok
    - `unsettled(strength("age") == "weak")`: **false** (the claim is settled: it is false)

### Version 1: reduced (9 claims, 0 failing)
1. Revolving credit utilization is the most important driver of predicted default, and risk rises steadily as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk increases with it, with the largest rise from none to two or more.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. The effect of utilization grows with the number of delinquencies: a high utilization adds much more risk for applicants with past delinquencies than for those without.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Annual income is among the third or fourth most important features, and higher income generally lowers predicted risk.
    - `rank("income") in (3, 4)`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history is also among the third or fourth most important features, and longer histories generally lower predicted risk.
    - `rank("history_months") in (3, 4)`: ok
    - `direction("history_months") == "decreasing"`: ok

## syn-dominant-n50000-s1_XGB2_H1_d4_claude-haiku-5-5_plausible

**RELEASED_REDUCED**: failing sentences dropped after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (12 claims, 1 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises steadily as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk rises with it, with the largest rise between none and one or more.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. The effect of utilization grows with the number of past delinquencies: a high utilization adds far more risk for applicants who have delinquencies than for those who have none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income is among the third or fourth most important drivers, and higher income generally lowers the risk of default.
    - `rank("income") in (3, 4)`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history is also among the third or fourth most important drivers, and longer histories generally lower the risk.
    - `rank("history_months") in (3, 4)`: ok
    - `direction("history_months") == "decreasing"`: ok
6. Debt-to-income ratio has at most a weak effect, with higher ratios raising the risk somewhat.
    - `strength("dti") == "weak"`: **undecidable** (share band straddles a class edge)
7. The number of recent credit inquiries and the number of dependents have at most a weak effect, and the data do not settle whether the number of dependents matters at all.
    - `strength("n_inquiries") in ("negligible", "weak")`: ok
8. The applicant's age hardly matters for the model's predictions.
    - `negligible("age")`: ok
    - format error: sentence 7: unsettled(strength("num_dependents") == "negligible"): strength is one of ['weak', 'moderate', 'strong']

### Version 1: reduced (10 claims, 0 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises steadily as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk rises with it, with the largest rise between none and one or more.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. The effect of utilization grows with the number of past delinquencies: a high utilization adds far more risk for applicants who have delinquencies than for those who have none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income is among the third or fourth most important drivers, and higher income generally lowers the risk of default.
    - `rank("income") in (3, 4)`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history is also among the third or fourth most important drivers, and longer histories generally lower the risk.
    - `rank("history_months") in (3, 4)`: ok
    - `direction("history_months") == "decreasing"`: ok
8. The applicant's age hardly matters for the model's predictions.
    - `negligible("age")`: ok

## syn-none-n5000-s1_EBM_H1_d0_claude-haiku-5-5_opaque

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (15 claims, 3 failing)
1. Revolving credit utilization is the most important driver of default risk, accounting for roughly 38% of the model's importance, and risk rises as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `share("utilization") == approx(0.376)`: **undecidable**
    - `direction("utilization") == "increasing"`: ok
2. Past delinquencies are the second or third most important driver, and having at least one delinquency raises the predicted risk of default.
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Annual income is also a strong driver, ranking second or third, and higher income generally lowers the predicted risk of default.
    - `strength("income") == "strong"`: **undecidable** (share band straddles a class edge)
    - `rank("income") in (2, 3)`: ok
    - `direction("income") == "decreasing"`: ok
4. Length of credit history has a weak to moderate effect, and longer histories tend to lower predicted risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
5. The data do not settle whether debt-to-income ratio, the two application attributes, or applicant age carry any effect beyond a small one.
    - `unsettled(strength("dti") == "weak")`: ok
    - `unsettled(strength("noise_2") == "weak")`: ok
6. Recent credit inquiries hardly matter.
    - `negligible("age")`: ok
    - `negligible("n_inquiries")`: ok
7. The interactions in the model are small, and the data do not settle whether income and age interact.
    - format error: sentence 5: unsettled(strength("feature_a") == "negligible"): strength is one of ['weak', 'moderate', 'strong']
    - format error: sentence 7: interaction("utilization & history_months", pattern="none"): interaction() takes 2 term(s)
    - format error: sentence 7: unsettled(interaction("income & age", pattern="none")): interaction() takes 2 term(s)

### Version 1: reduced (4 claims, 0 failing, missing: utilization, n_delinquencies, income)
4. Length of credit history has a weak to moderate effect, and longer histories tend to lower predicted risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. Recent credit inquiries hardly matter.
    - `negligible("age")`: ok
    - `negligible("n_inquiries")`: ok

### Version 2: template (14 claims, 0 failing)
1. Credit utilization has a strong effect on default risk; default risk increases with credit utilization.
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies has a moderate to strong effect on default risk; default risk increases with the number of past delinquencies.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Default risk jumps at the number of past delinquencies = 0.5.
    - `threshold("n_delinquencies", at=0.5)`: ok
4. Income has a moderate to strong effect on default risk; default risk decreases with income.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
5. The length of credit history has a weak to moderate effect on default risk; default risk decreases with the length of credit history.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has at most a moderate effect on default risk.
    - `strength("dti") in ("negligible", "weak", "moderate")`: ok
7. Feature b has at most a moderate effect on default risk.
    - `strength("noise_2") in ("negligible", "weak", "moderate")`: ok
8. Feature a has at most a moderate effect on default risk.
    - `strength("noise_1") in ("negligible", "weak", "moderate")`: ok
9. Age hardly matters for default risk.
    - `negligible("age")`: ok
10. The number of recent inquiries hardly matters for default risk.
    - `negligible("n_inquiries")`: ok

## syn-none-n5000-s1_EBM_H1_d0_claude-haiku-5-5_plausible

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (15 claims, 2 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
2. The number of past delinquencies is the second or third most important driver, and having at least one delinquency raises the predicted risk compared with having none.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `threshold("n_delinquencies", at=1.0)`: ok
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

### Version 1: reduced (10 claims, 0 failing, missing: income)
1. Revolving credit utilization is the most important driver of default risk, and risk rises as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
2. The number of past delinquencies is the second or third most important driver, and having at least one delinquency raises the predicted risk compared with having none.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `threshold("n_delinquencies", at=1.0)`: ok
4. Length of credit history has a weak to moderate effect, and longer histories lower the predicted risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
5. The model shows no clear interaction between utilization and credit history length.
    - `interaction("utilization", "history_months", pattern="none")`: ok
6. The data do not settle whether debt-to-income ratio has any effect on default risk at this sample size.
    - `unsettled(strength("dti") == "weak")`: ok

### Version 2: template (14 claims, 0 failing)
1. Credit utilization has a strong effect on default risk; default risk increases with credit utilization.
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies has a moderate to strong effect on default risk; default risk increases with the number of past delinquencies.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Default risk jumps at the number of past delinquencies = 0.5.
    - `threshold("n_delinquencies", at=0.5)`: ok
4. Income has a moderate to strong effect on default risk; default risk decreases with income.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
5. The length of credit history has a weak to moderate effect on default risk; default risk decreases with the length of credit history.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has at most a moderate effect on default risk.
    - `strength("dti") in ("negligible", "weak", "moderate")`: ok
7. The number of dependents has at most a moderate effect on default risk.
    - `strength("noise_2") in ("negligible", "weak", "moderate")`: ok
8. Months at the current address has at most a moderate effect on default risk.
    - `strength("noise_1") in ("negligible", "weak", "moderate")`: ok
9. Age hardly matters for default risk.
    - `negligible("age")`: ok
10. The number of recent inquiries hardly matters for default risk.
    - `negligible("n_inquiries")`: ok

## syn-none-n5000-s1_EBM_H1_d1_claude-haiku-5-5_opaque

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (17 claims, 4 failing)
1. Revolving credit utilization is the most important driver of default risk, accounting for about 38% of the model's importance, and risk rises steeply as utilization climbs, especially above roughly 0.7 of the limit.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `share("utilization") == approx(0.376)`: **undecidable**
2. Past delinquencies are the second or third most important driver, and any delinquency on the credit file raises the risk of default compared with none.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
3. Annual income is also among the top three drivers, and higher income lowers the risk of default, with the decrease holding across the income range.
    - `rank("income") in (2, 3)`: ok
    - `direction("income") == "decreasing"`: ok
    - `strength("income") == "moderate"`: **undecidable** (share band straddles a class edge)
    - `effect("utilization") > effect("income")`: ok
4. Length of credit history has a weak to moderate effect, and longer histories are associated with lower default risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
5. The data do not settle whether the debt-to-income ratio, the two application attributes, or applicant age matter for predictions.
    - `unsettled(strength("dti") == "weak")`: ok
    - `unsettled(direction("dti") == "increasing")`: ok
6. Recent credit inquiries hardly matter.
    - `negligible("n_inquiries")`: ok
7. Utilization and credit history do not interact in any way of practical size, and the data do not settle whether income and the standardised application attribute interact.
    - `interaction("utilization", "history_months", pattern="none")`: ok
    - `unsettled(interaction("income", "noise_2", pattern="none"))`: **false** (the claim is settled: it is true)

### Version 1: reduced (5 claims, 0 failing, missing: utilization, n_delinquencies, income)
4. Length of credit history has a weak to moderate effect, and longer histories are associated with lower default risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
5. The data do not settle whether the debt-to-income ratio, the two application attributes, or applicant age matter for predictions.
    - `unsettled(strength("dti") == "weak")`: ok
    - `unsettled(direction("dti") == "increasing")`: ok
6. Recent credit inquiries hardly matter.
    - `negligible("n_inquiries")`: ok

### Version 2: template (14 claims, 0 failing)
1. Credit utilization has a strong effect on default risk; default risk increases with credit utilization.
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies has a moderate to strong effect on default risk; default risk increases with the number of past delinquencies.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Default risk jumps at the number of past delinquencies = 0.5.
    - `threshold("n_delinquencies", at=0.5)`: ok
4. Income has a moderate to strong effect on default risk; default risk decreases with income.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
5. The length of credit history has a weak to moderate effect on default risk; default risk decreases with the length of credit history.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has at most a moderate effect on default risk.
    - `strength("dti") in ("negligible", "weak", "moderate")`: ok
7. Feature b has at most a moderate effect on default risk.
    - `strength("noise_2") in ("negligible", "weak", "moderate")`: ok
8. Feature a has at most a moderate effect on default risk.
    - `strength("noise_1") in ("negligible", "weak", "moderate")`: ok
9. Age hardly matters for default risk.
    - `negligible("age")`: ok
10. The number of recent inquiries hardly matters for default risk.
    - `negligible("n_inquiries")`: ok

## syn-none-n5000-s1_EBM_H1_d1_claude-haiku-5-5_plausible

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (14 claims, 3 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises steadily as utilization climbs, with the sharpest increase at the highest levels.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `share("utilization") == approx(0.376)`: **undecidable**
2. The number of past delinquencies is the second or third most important driver, and any past delinquency raises the predicted risk compared with none.
    - `direction("n_delinquencies") == "increasing"`: ok
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
3. Income is the other leading driver, and higher income is associated with lower predicted risk, with the effect of income decreasing as income rises.
    - `direction("income") == "decreasing"`: ok
    - `rank("income") in (2, 3)`: ok
    - `strength("income") == "moderate"`: **undecidable** (share band straddles a class edge)
4. Length of credit history has a weak to moderate effect, with longer histories associated with lower risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
5. The data do not settle whether debt-to-income ratio, number of dependents, months at address and age matter at all; their effects are small and not clearly detectable at this sample size.
    - `unsettled(strength("dti") == "weak")`: ok
6. Recent credit inquiries hardly matter.
    - `negligible("n_inquiries")`: ok
7. The effect of utilization is essentially the same at short and long credit histories, so the two do not interact in a way that changes the picture.
    - `interaction("utilization", "history_months", pattern="none")`: ok

### Version 1: reduced (5 claims, 0 failing, missing: utilization, n_delinquencies, income)
4. Length of credit history has a weak to moderate effect, with longer histories associated with lower risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
5. The data do not settle whether debt-to-income ratio, number of dependents, months at address and age matter at all; their effects are small and not clearly detectable at this sample size.
    - `unsettled(strength("dti") == "weak")`: ok
6. Recent credit inquiries hardly matter.
    - `negligible("n_inquiries")`: ok
7. The effect of utilization is essentially the same at short and long credit histories, so the two do not interact in a way that changes the picture.
    - `interaction("utilization", "history_months", pattern="none")`: ok

### Version 2: template (14 claims, 0 failing)
1. Credit utilization has a strong effect on default risk; default risk increases with credit utilization.
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies has a moderate to strong effect on default risk; default risk increases with the number of past delinquencies.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Default risk jumps at the number of past delinquencies = 0.5.
    - `threshold("n_delinquencies", at=0.5)`: ok
4. Income has a moderate to strong effect on default risk; default risk decreases with income.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
5. The length of credit history has a weak to moderate effect on default risk; default risk decreases with the length of credit history.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has at most a moderate effect on default risk.
    - `strength("dti") in ("negligible", "weak", "moderate")`: ok
7. The number of dependents has at most a moderate effect on default risk.
    - `strength("noise_2") in ("negligible", "weak", "moderate")`: ok
8. Months at the current address has at most a moderate effect on default risk.
    - `strength("noise_1") in ("negligible", "weak", "moderate")`: ok
9. Age hardly matters for default risk.
    - `negligible("age")`: ok
10. The number of recent inquiries hardly matters for default risk.
    - `negligible("n_inquiries")`: ok

## syn-none-n5000-s1_EBM_H1_d2_claude-haiku-5-5_opaque

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (14 claims, 5 failing)
1. Revolving credit utilization is the most important driver of default risk, accounting for roughly 38% of the model's importance, and risk generally increases as utilization rises.
    - `rank("utilization") == 1`: ok
    - `share("utilization") == approx(0.376)`: **undecidable**
    - `direction("utilization") == "increasing"`: ok
2. The effect is strongly non-linear: low utilization lowers predicted risk, while utilization above about 0.735 adds the largest push toward default.
    - `threshold("utilization", at=0.735)`: **false**
3. Past delinquencies are the second or third most important driver, and having at least one delinquency raises predicted risk compared with having none.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `strength("n_delinquencies") == "moderate"`: **undecidable** (share band straddles a class edge)
    - `direction("n_delinquencies") == "increasing"`: ok
4. Annual income is also among the top three drivers, and higher income generally lowers predicted default risk.
    - `rank("income") in (2, 3)`: ok
    - `strength("income") == "moderate"`: **undecidable** (share band straddles a class edge)
    - `direction("income") == "decreasing"`: ok
5. The effect of utilization does not meaningfully depend on credit history length, and the two do not interact in a practically important way.
    - `interaction("utilization", "history_months", pattern="none")`: ok
6. The data do not settle whether debt-to-income ratio matters for default risk at this sample size, since its effect is small and its band is wide.
7. Recent credit inquiries and the two standardised application attributes, feature_a and feature_b, hardly matter to the model's predictions.
    - `negligible("noise_1")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("n_inquiries")`: ok
8. Length of credit history has at most a weak to moderate effect, with longer histories generally associated with slightly lower risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - format error: sentence 6: unsettled(strength("dti") == "negligible"): strength is one of ['weak', 'moderate', 'strong']

### Version 1: reduced (2 claims, 0 failing, missing: utilization, n_delinquencies, income)
5. The effect of utilization does not meaningfully depend on credit history length, and the two do not interact in a practically important way.
    - `interaction("utilization", "history_months", pattern="none")`: ok
8. Length of credit history has at most a weak to moderate effect, with longer histories generally associated with slightly lower risk.
    - `strength("history_months") in ("weak", "moderate")`: ok

### Version 2: template (14 claims, 0 failing)
1. Credit utilization has a strong effect on default risk; default risk increases with credit utilization.
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies has a moderate to strong effect on default risk; default risk increases with the number of past delinquencies.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Default risk jumps at the number of past delinquencies = 0.5.
    - `threshold("n_delinquencies", at=0.5)`: ok
4. Income has a moderate to strong effect on default risk; default risk decreases with income.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
5. The length of credit history has a weak to moderate effect on default risk; default risk decreases with the length of credit history.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has at most a moderate effect on default risk.
    - `strength("dti") in ("negligible", "weak", "moderate")`: ok
7. Feature b has at most a moderate effect on default risk.
    - `strength("noise_2") in ("negligible", "weak", "moderate")`: ok
8. Feature a has at most a moderate effect on default risk.
    - `strength("noise_1") in ("negligible", "weak", "moderate")`: ok
9. Age hardly matters for default risk.
    - `negligible("age")`: ok
10. The number of recent inquiries hardly matters for default risk.
    - `negligible("n_inquiries")`: ok

## syn-none-n5000-s1_EBM_H1_d2_claude-haiku-5-5_plausible

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (19 claims, 6 failing)
1. Revolving credit utilization is by far the most important driver of default risk, and risk rises as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `share("utilization") == approx(0.376)`: **undecidable**
2. The number of past delinquencies is the second or third most important driver, and having any delinquency raises the predicted risk compared with having none.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
    - `effect("n_delinquencies") > effect("income")`: **undecidable**
3. Annual income is the other second or third most important driver, and higher income is associated with lower predicted risk, mainly at the lower end of the income range.
    - `rank("income") in (2, 3)`: ok
    - `direction("income") == "decreasing"`: ok
    - `strength("income") == "moderate"`: **undecidable** (share band straddles a class edge)
4. Length of credit history has a weak to moderate effect, with longer histories associated with lower predicted risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
5. The data do not settle whether debt-to-income ratio matters at all, or whether its effect is increasing.
    - `unsettled(strength("dti") in ("negligible", "weak"))`: ok
    - `unsettled(direction("dti") == "increasing")`: ok
6. The data do not settle whether number of dependents or age matter for predicted risk.
    - `unsettled(negligible("noise_2"))`: ok
    - `unsettled(negligible("age"))`: **false** (the claim is settled: it is true)
7. Recent credit inquiries hardly matter.
    - `negligible("n_inquiries")`: ok
8. The effect of utilization is larger for applicants with shorter credit histories, while utilization and debt-to-income ratio do not interact in any practical way.
    - `interaction("utilization", "history_months", pattern="amplification")`: **undecidable**
    - `interaction("utilization", "dti", pattern="none")`: ok

### Version 1: reduced (5 claims, 0 failing, missing: utilization, n_delinquencies, income)
4. Length of credit history has a weak to moderate effect, with longer histories associated with lower predicted risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
5. The data do not settle whether debt-to-income ratio matters at all, or whether its effect is increasing.
    - `unsettled(strength("dti") in ("negligible", "weak"))`: ok
    - `unsettled(direction("dti") == "increasing")`: ok
7. Recent credit inquiries hardly matter.
    - `negligible("n_inquiries")`: ok

### Version 2: template (14 claims, 0 failing)
1. Credit utilization has a strong effect on default risk; default risk increases with credit utilization.
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies has a moderate to strong effect on default risk; default risk increases with the number of past delinquencies.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Default risk jumps at the number of past delinquencies = 0.5.
    - `threshold("n_delinquencies", at=0.5)`: ok
4. Income has a moderate to strong effect on default risk; default risk decreases with income.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
5. The length of credit history has a weak to moderate effect on default risk; default risk decreases with the length of credit history.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has at most a moderate effect on default risk.
    - `strength("dti") in ("negligible", "weak", "moderate")`: ok
7. The number of dependents has at most a moderate effect on default risk.
    - `strength("noise_2") in ("negligible", "weak", "moderate")`: ok
8. Months at the current address has at most a moderate effect on default risk.
    - `strength("noise_1") in ("negligible", "weak", "moderate")`: ok
9. Age hardly matters for default risk.
    - `negligible("age")`: ok
10. The number of recent inquiries hardly matters for default risk.
    - `negligible("n_inquiries")`: ok

## syn-none-n5000-s1_EBM_H1_d3_claude-haiku-5-5_opaque

**RELEASED_REDUCED**: failing sentences dropped after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (14 claims, 1 failing)
1. Revolving credit utilization is the most important driver, and its effect is strong: risk rises as the share of the credit limit in use climbs, with the largest increase at high utilization.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. Past delinquencies are the second or third most important driver, and risk increases with the number of delinquencies on the credit file, with the largest step coming from having none versus at least one.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Income is also among the top three drivers, with an effect of moderate to strong size: higher income generally lowers the risk of default.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
4. Length of credit history has a weak to moderate effect, and longer histories generally lower risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
5. The data do not settle whether debt-to-income ratio has a weak effect, since no movement in its curve is resolved.
    - `unsettled(strength("dti") == "weak")`: ok
6. The effect of utilization does not meaningfully change with credit history length.
    - `interaction("utilization", "history_months", pattern="none")`: ok
7. The data do not settle whether income and feature_b interact.
    - `unsettled(interaction("income", "noise_2", pattern="none"))`: **false** (the claim is settled: it is true)
8. The number of recent credit inquiries hardly matters, while the data do not settle whether feature_a matters at all.
    - `negligible("n_inquiries")`: ok
    - `unsettled(negligible("noise_1"))`: ok

### Version 1: reduced (13 claims, 0 failing)
1. Revolving credit utilization is the most important driver, and its effect is strong: risk rises as the share of the credit limit in use climbs, with the largest increase at high utilization.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. Past delinquencies are the second or third most important driver, and risk increases with the number of delinquencies on the credit file, with the largest step coming from having none versus at least one.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Income is also among the top three drivers, with an effect of moderate to strong size: higher income generally lowers the risk of default.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
4. Length of credit history has a weak to moderate effect, and longer histories generally lower risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
5. The data do not settle whether debt-to-income ratio has a weak effect, since no movement in its curve is resolved.
    - `unsettled(strength("dti") == "weak")`: ok
6. The effect of utilization does not meaningfully change with credit history length.
    - `interaction("utilization", "history_months", pattern="none")`: ok
8. The number of recent credit inquiries hardly matters, while the data do not settle whether feature_a matters at all.
    - `negligible("n_inquiries")`: ok
    - `unsettled(negligible("noise_1"))`: ok

## syn-none-n5000-s1_EBM_H1_d3_claude-haiku-5-5_plausible

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (18 claims, 3 failing)
1. Revolving credit utilization is the strongest driver of default risk: it accounts for about 38% of the model's importance, and risk rises sharply as utilization climbs, with the largest increase among applicants using most of their credit limit.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
2. Past delinquencies are the second or third most important driver, and having at least one delinquency raises default risk compared with having none.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `threshold("n_delinquencies", at=1.0)`: ok
3. Income is the other leading driver, and higher income generally lowers default risk, with the effect strongest at the top of the income range.
    - `rank("income") in (2, 3)`: ok
    - `direction("income") == "decreasing"`: ok
    - `strength("income") == "moderate"`: **undecidable** (share band straddles a class edge)
4. Length of credit history is a weak effect, ranking among the less important features, and a longer history is associated with somewhat lower risk.
    - `rank("history_months") in (4, 5, 6)`: ok
    - `direction("history_months") == "decreasing"`: ok
    - `strength("history_months") in ("negligible", "weak")`: **undecidable** (share band not settled against [0%, 5%))
5. The data do not settle whether debt-to-income ratio, number of dependents, months at address and age matter, since their effects are too uncertain to separate from zero at this sample size.
    - `unsettled(strength("dti") == "weak")`: ok
    - `unsettled(direction("dti") == "increasing")`: ok
6. Recent credit inquiries hardly matter for the model's predictions.
    - `strength("n_inquiries") == "weak"`: **undecidable** (share band straddles a class edge)
    - `negligible("n_inquiries")`: ok
7. The interactions in the model are small, and none of the pairs we examined changes the picture of the main drivers.
    - `interaction("utilization", "history_months", pattern="none")`: ok
    - `interaction("utilization", "dti", pattern="none")`: ok

### Version 1: reduced (10 claims, 0 failing, missing: income)
1. Revolving credit utilization is the strongest driver of default risk: it accounts for about 38% of the model's importance, and risk rises sharply as utilization climbs, with the largest increase among applicants using most of their credit limit.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
2. Past delinquencies are the second or third most important driver, and having at least one delinquency raises default risk compared with having none.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `threshold("n_delinquencies", at=1.0)`: ok
5. The data do not settle whether debt-to-income ratio, number of dependents, months at address and age matter, since their effects are too uncertain to separate from zero at this sample size.
    - `unsettled(strength("dti") == "weak")`: ok
    - `unsettled(direction("dti") == "increasing")`: ok
7. The interactions in the model are small, and none of the pairs we examined changes the picture of the main drivers.
    - `interaction("utilization", "history_months", pattern="none")`: ok
    - `interaction("utilization", "dti", pattern="none")`: ok

### Version 2: template (14 claims, 0 failing)
1. Credit utilization has a strong effect on default risk; default risk increases with credit utilization.
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies has a moderate to strong effect on default risk; default risk increases with the number of past delinquencies.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Default risk jumps at the number of past delinquencies = 0.5.
    - `threshold("n_delinquencies", at=0.5)`: ok
4. Income has a moderate to strong effect on default risk; default risk decreases with income.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
5. The length of credit history has a weak to moderate effect on default risk; default risk decreases with the length of credit history.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has at most a moderate effect on default risk.
    - `strength("dti") in ("negligible", "weak", "moderate")`: ok
7. The number of dependents has at most a moderate effect on default risk.
    - `strength("noise_2") in ("negligible", "weak", "moderate")`: ok
8. Months at the current address has at most a moderate effect on default risk.
    - `strength("noise_1") in ("negligible", "weak", "moderate")`: ok
9. Age hardly matters for default risk.
    - `negligible("age")`: ok
10. The number of recent inquiries hardly matters for default risk.
    - `negligible("n_inquiries")`: ok

## syn-none-n5000-s1_EBM_H1_d4_claude-haiku-5-5_opaque

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (15 claims, 3 failing)
1. Revolving credit utilization is the most important driver of default risk, accounting for roughly 38% of the model's importance.
    - `rank("utilization") == 1`: ok
    - `share("utilization") == approx(0.376)`: **undecidable**
    - `direction("utilization") == "increasing"`: ok
2. Risk rises steeply once utilization passes about 0.74, and it rises across the full range of utilization from low to high values.
    - `threshold("utilization", at=0.735)`: **false**
3. Past delinquencies are the second or third most important driver, and having any delinquency raises the predicted risk of default.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
4. Annual income has a moderate to strong effect, and higher income is associated with lower predicted default risk.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a weak to moderate effect, and longer histories generally lower the predicted risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The effect of utilization does not meaningfully depend on credit history length.
    - `interaction("utilization", "history_months", pattern="none")`: ok
7. The data do not settle whether debt-to-income ratio matters for the model's predictions.
    - `unsettled(negligible("dti"))`: ok
8. Feature_a, feature_b, applicant age and recent credit inquiries have at most a negligible effect on predicted default.
    - `negligible("noise_1")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("n_inquiries")`: ok
    - `negligible("age")`: ok

### Version 1: reduced (8 claims, 0 failing, missing: utilization)
3. Past delinquencies are the second or third most important driver, and having any delinquency raises the predicted risk of default.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
4. Annual income has a moderate to strong effect, and higher income is associated with lower predicted default risk.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a weak to moderate effect, and longer histories generally lower the predicted risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The effect of utilization does not meaningfully depend on credit history length.
    - `interaction("utilization", "history_months", pattern="none")`: ok
7. The data do not settle whether debt-to-income ratio matters for the model's predictions.
    - `unsettled(negligible("dti"))`: ok

### Version 2: template (14 claims, 0 failing)
1. Credit utilization has a strong effect on default risk; default risk increases with credit utilization.
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies has a moderate to strong effect on default risk; default risk increases with the number of past delinquencies.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Default risk jumps at the number of past delinquencies = 0.5.
    - `threshold("n_delinquencies", at=0.5)`: ok
4. Income has a moderate to strong effect on default risk; default risk decreases with income.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
5. The length of credit history has a weak to moderate effect on default risk; default risk decreases with the length of credit history.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has at most a moderate effect on default risk.
    - `strength("dti") in ("negligible", "weak", "moderate")`: ok
7. Feature b has at most a moderate effect on default risk.
    - `strength("noise_2") in ("negligible", "weak", "moderate")`: ok
8. Feature a has at most a moderate effect on default risk.
    - `strength("noise_1") in ("negligible", "weak", "moderate")`: ok
9. Age hardly matters for default risk.
    - `negligible("age")`: ok
10. The number of recent inquiries hardly matters for default risk.
    - `negligible("n_inquiries")`: ok

## syn-none-n5000-s1_EBM_H1_d4_claude-haiku-5-5_plausible

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (15 claims, 3 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises steeply as the share of the credit limit in use grows, with the largest increase at high utilization.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `share("utilization") == approx(0.376)`: **undecidable**
2. The number of past delinquencies is the second or third most important driver, and having any delinquency raises the risk of default.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
3. Annual income is also the second or third most important driver, and higher income lowers the risk of default, with most of the drop coming between the lower and middle income bands.
    - `rank("income") in (2, 3)`: ok
    - `direction("income") == "decreasing"`: ok
    - `strength("income") == "moderate"`: **undecidable** (share band straddles a class edge)
4. Length of credit history has a weak to moderate effect, with longer histories associated with lower risk.
    - `direction("history_months") == "decreasing"`: ok
    - `strength("history_months") in ("weak", "moderate")`: ok
5. Utilization and credit history do not interact in any way the data can detect.
    - `interaction("utilization", "history_months", pattern="none")`: ok
6. The data do not settle whether debt-to-income ratio has a weak effect on default risk, since no movement in its curve is resolved at this sample size.
    - `unsettled(strength("dti") == "weak")`: ok
7. Number of recent credit inquiries and applicant age hardly matter for the predictions.
    - `negligible("n_inquiries")`: ok
    - `negligible("age")`: ok

### Version 1: reduced (6 claims, 0 failing, missing: utilization, n_delinquencies, income)
4. Length of credit history has a weak to moderate effect, with longer histories associated with lower risk.
    - `direction("history_months") == "decreasing"`: ok
    - `strength("history_months") in ("weak", "moderate")`: ok
5. Utilization and credit history do not interact in any way the data can detect.
    - `interaction("utilization", "history_months", pattern="none")`: ok
6. The data do not settle whether debt-to-income ratio has a weak effect on default risk, since no movement in its curve is resolved at this sample size.
    - `unsettled(strength("dti") == "weak")`: ok
7. Number of recent credit inquiries and applicant age hardly matter for the predictions.
    - `negligible("n_inquiries")`: ok
    - `negligible("age")`: ok

### Version 2: template (14 claims, 0 failing)
1. Credit utilization has a strong effect on default risk; default risk increases with credit utilization.
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies has a moderate to strong effect on default risk; default risk increases with the number of past delinquencies.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Default risk jumps at the number of past delinquencies = 0.5.
    - `threshold("n_delinquencies", at=0.5)`: ok
4. Income has a moderate to strong effect on default risk; default risk decreases with income.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
5. The length of credit history has a weak to moderate effect on default risk; default risk decreases with the length of credit history.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has at most a moderate effect on default risk.
    - `strength("dti") in ("negligible", "weak", "moderate")`: ok
7. The number of dependents has at most a moderate effect on default risk.
    - `strength("noise_2") in ("negligible", "weak", "moderate")`: ok
8. Months at the current address has at most a moderate effect on default risk.
    - `strength("noise_1") in ("negligible", "weak", "moderate")`: ok
9. Age hardly matters for default risk.
    - `negligible("age")`: ok
10. The number of recent inquiries hardly matters for default risk.
    - `negligible("n_inquiries")`: ok

## syn-none-n5000-s1_XGB2_H1_d0_claude-haiku-5-5_opaque

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (15 claims, 5 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises as the share of the credit limit in use grows.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The steepest rise is at a utilization of about 0.72, where the added risk jumps sharply.
    - `threshold("utilization", at=0.719)`: **false**
3. Past delinquencies rank second or third in importance, and having any delinquency raises default risk compared with having none.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
4. Income has a weak to moderate effect, and higher income generally lowers default risk.
    - `strength("income") in ("weak", "moderate")`: **undecidable** (share band not settled against [2%, 15%))
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has at most a weak effect, with longer histories generally associated with lower risk.
    - `strength("history_months") in ("negligible", "weak")`: **undecidable** (share band not settled against [0%, 5%))
    - `direction("history_months") == "decreasing"`: ok
6. The data do not settle whether debt-to-income ratio matters at all, since no movement in its curve is resolved.
    - `unsettled(strength("dti") == "weak")`: ok
7. Age, feature_a, and recent credit inquiries hardly matter for the predictions.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `negligible("n_inquiries")`: ok
8. The effect of delinquencies is larger when utilization is high.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: **undecidable**
9. Utilization and credit history length do not interact in any practically meaningful way.
    - `interaction("utilization", "history_months", pattern="none")`: **undecidable**

### Version 1: reduced (8 claims, 0 failing, missing: income)
1. Revolving credit utilization is the most important driver of default risk, and risk rises as the share of the credit limit in use grows.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
3. Past delinquencies rank second or third in importance, and having any delinquency raises default risk compared with having none.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
6. The data do not settle whether debt-to-income ratio matters at all, since no movement in its curve is resolved.
    - `unsettled(strength("dti") == "weak")`: ok
7. Age, feature_a, and recent credit inquiries hardly matter for the predictions.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `negligible("n_inquiries")`: ok

### Version 2: template (14 claims, 0 failing)
1. Credit utilization has a strong effect on default risk; default risk increases with credit utilization.
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies has a moderate to strong effect on default risk; default risk increases with the number of past delinquencies.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Default risk jumps at the number of past delinquencies = 1.
    - `threshold("n_delinquencies", at=1.0)`: ok
4. Income has a moderate to strong effect on default risk; default risk decreases with income.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
5. The length of credit history has at most a moderate effect on default risk; default risk decreases with the length of credit history.
    - `strength("history_months") in ("negligible", "weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has at most a moderate effect on default risk.
    - `strength("dti") in ("negligible", "weak", "moderate")`: ok
7. Feature b has at most a moderate effect on default risk.
    - `strength("noise_2") in ("negligible", "weak", "moderate")`: ok
8. Age hardly matters for default risk.
    - `negligible("age")`: ok
9. Feature a hardly matters for default risk.
    - `negligible("noise_1")`: ok
10. The number of recent inquiries hardly matters for default risk.
    - `negligible("n_inquiries")`: ok

## syn-none-n5000-s1_XGB2_H1_d0_claude-haiku-5-5_plausible

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

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

### Version 1: reduced (5 claims, 0 failing, missing: income)
1. Revolving credit utilization is the most important driver of default risk, and risk generally increases as the share of the credit limit in use rises.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
3. Past delinquencies are the second or third most important driver, and having any delinquency raises the risk of default compared with having none.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
7. The data do not settle whether the effect of utilization depends on credit history length.
    - `unsettled(interaction("utilization", "history_months", pattern="amplification"))`: ok

### Version 2: template (14 claims, 0 failing)
1. Credit utilization has a strong effect on default risk; default risk increases with credit utilization.
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies has a moderate to strong effect on default risk; default risk increases with the number of past delinquencies.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Default risk jumps at the number of past delinquencies = 1.
    - `threshold("n_delinquencies", at=1.0)`: ok
4. Income has a moderate to strong effect on default risk; default risk decreases with income.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
5. The length of credit history has at most a moderate effect on default risk; default risk decreases with the length of credit history.
    - `strength("history_months") in ("negligible", "weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has at most a moderate effect on default risk.
    - `strength("dti") in ("negligible", "weak", "moderate")`: ok
7. The number of dependents has at most a moderate effect on default risk.
    - `strength("noise_2") in ("negligible", "weak", "moderate")`: ok
8. Age hardly matters for default risk.
    - `negligible("age")`: ok
9. Months at the current address hardly matters for default risk.
    - `negligible("noise_1")`: ok
10. The number of recent inquiries hardly matters for default risk.
    - `negligible("n_inquiries")`: ok

## syn-none-n5000-s1_XGB2_H1_d1_claude-haiku-5-5_opaque

**RELEASED_REDUCED**: failing sentences dropped after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (16 claims, 5 failing)
1. Revolving credit utilization is the most important driver of predicted default, and risk generally increases as utilization rises.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. Risk climbs most sharply once utilization passes about 0.72 of the credit limit.
    - `threshold("utilization", at=0.719)`: **false**
3. The number of past delinquencies is the second or third most important driver, and risk rises once an applicant has at least one delinquency.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
4. Annual income is also second or third in importance, and higher income is associated with lower predicted risk.
    - `rank("income") in (2, 3)`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has at most a weak effect, with longer histories associated with somewhat lower risk.
    - `strength("history_months") in ("negligible", "weak")`: **undecidable** (share band not settled against [0%, 5%))
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio hardly matters: the data do not show a detectable effect of it on predicted default.
    - `negligible("dti")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
7. The effect of utilization does not appear to change with the number of delinquencies, and the data do not settle whether the effect of utilization grows with credit history length.
    - `interaction("utilization & n_delinquencies", "n_delinquencies", pattern="none")`: **undecidable** (utilization & n_delinquencies & n_delinquencies is not a term of this model)
    - `unsettled(interaction("utilization", "history_months", pattern="amplification"))`: ok
8. The remaining features, including age, the two standardised application attributes and recent credit inquiries, have negligible influence on the model's predictions.
    - `negligible("noise_2")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `negligible("n_inquiries")`: ok

### Version 1: reduced (6 claims, 0 failing)
1. Revolving credit utilization is the most important driver of predicted default, and risk generally increases as utilization rises.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
3. The number of past delinquencies is the second or third most important driver, and risk rises once an applicant has at least one delinquency.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
4. Annual income is also second or third in importance, and higher income is associated with lower predicted risk.
    - `rank("income") in (2, 3)`: ok
    - `direction("income") == "decreasing"`: ok

## syn-none-n5000-s1_XGB2_H1_d1_claude-haiku-5-5_plausible

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (18 claims, 6 failing)
1. Revolving credit utilization is the most important driver of default risk, accounting for roughly a third of the model's importance, and risk rises as utilization rises.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The steepest increase comes at high utilization, where the risk contribution jumps sharply once utilization passes about 72% of the credit limit.
    - `threshold("utilization", at=0.719)`: **false**
3. Past delinquencies are the second or third most important driver, and having any delinquency on file raises the predicted risk.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `strength("n_delinquencies") == "moderate"`: **undecidable** (share band straddles a class edge)
4. Higher income lowers predicted risk, though its effect is moderate at most.
    - `rank("income") in (2, 3)`: ok
    - `direction("income") == "decreasing"`: ok
    - `strength("income") in ("weak", "moderate")`: **undecidable** (share band not settled against [2%, 15%))
5. The effect of utilization grows with the number of past delinquencies, so applicants with both high utilization and delinquencies carry the most risk.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: **undecidable**
6. Length of credit history has a weak to moderate effect, with longer histories associated with lower risk.
    - `strength("history_months") in ("weak", "moderate")`: **undecidable** (share band not settled against [2%, 15%))
    - `direction("history_months") == "decreasing"`: ok
7. The data do not settle whether debt-to-income ratio affects default risk at this sample size.
    - `unsettled(direction("dti") == "increasing")`: ok
8. Number of dependents, age, months at address and recent credit inquiries hardly matter.
    - `negligible("noise_2")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `negligible("n_inquiries")`: ok

### Version 1: reduced (4 claims, 0 failing, missing: n_delinquencies, income)
1. Revolving credit utilization is the most important driver of default risk, accounting for roughly a third of the model's importance, and risk rises as utilization rises.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
7. The data do not settle whether debt-to-income ratio affects default risk at this sample size.
    - `unsettled(direction("dti") == "increasing")`: ok

### Version 2: template (14 claims, 0 failing)
1. Credit utilization has a strong effect on default risk; default risk increases with credit utilization.
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies has a moderate to strong effect on default risk; default risk increases with the number of past delinquencies.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Default risk jumps at the number of past delinquencies = 1.
    - `threshold("n_delinquencies", at=1.0)`: ok
4. Income has a moderate to strong effect on default risk; default risk decreases with income.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
5. The length of credit history has at most a moderate effect on default risk; default risk decreases with the length of credit history.
    - `strength("history_months") in ("negligible", "weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has at most a moderate effect on default risk.
    - `strength("dti") in ("negligible", "weak", "moderate")`: ok
7. The number of dependents has at most a moderate effect on default risk.
    - `strength("noise_2") in ("negligible", "weak", "moderate")`: ok
8. Age hardly matters for default risk.
    - `negligible("age")`: ok
9. Months at the current address hardly matters for default risk.
    - `negligible("noise_1")`: ok
10. The number of recent inquiries hardly matters for default risk.
    - `negligible("n_inquiries")`: ok

## syn-none-n5000-s1_XGB2_H1_d2_claude-haiku-5-5_opaque

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (14 claims, 5 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. Its effect is strongest at high utilization, where the data show a sharp step up in risk at about 0.72.
    - `threshold("utilization", at=0.719)`: **false**
3. Past delinquencies are the second or third most important driver, and having any delinquency raises the risk of default compared with having none.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
4. Annual income is also among the top few drivers, and higher income generally lowers the risk of default.
    - `direction("income") == "decreasing"`: ok
    - `strength("income") in ("weak", "moderate")`: **undecidable** (share band not settled against [2%, 15%))
5. Length of credit history has at most a weak effect, with longer histories associated with slightly lower risk.
    - `direction("history_months") == "decreasing"`: ok
    - `strength("history_months") in ("negligible", "weak")`: **undecidable** (share band not settled against [0%, 5%))
6. The data do not settle whether debt-to-income ratio affects risk, and age, the two standardised application attributes and credit inquiries hardly matter.
    - `unsettled(direction("dti") == "increasing")`: ok
    - `negligible("age")`: ok
7. The effect of utilization is larger when delinquencies are present, while utilization and credit history do not interact in a way the data can detect.
    - `negligible("noise_1")`: ok
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: **undecidable**
    - `interaction("utilization", "history_months", pattern="none")`: **undecidable**

### Version 1: reduced (6 claims, 0 failing, missing: income)
1. Revolving credit utilization is the most important driver of default risk, and risk rises as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
3. Past delinquencies are the second or third most important driver, and having any delinquency raises the risk of default compared with having none.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
6. The data do not settle whether debt-to-income ratio affects risk, and age, the two standardised application attributes and credit inquiries hardly matter.
    - `unsettled(direction("dti") == "increasing")`: ok
    - `negligible("age")`: ok

### Version 2: template (14 claims, 0 failing)
1. Credit utilization has a strong effect on default risk; default risk increases with credit utilization.
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies has a moderate to strong effect on default risk; default risk increases with the number of past delinquencies.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Default risk jumps at the number of past delinquencies = 1.
    - `threshold("n_delinquencies", at=1.0)`: ok
4. Income has a moderate to strong effect on default risk; default risk decreases with income.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
5. The length of credit history has at most a moderate effect on default risk; default risk decreases with the length of credit history.
    - `strength("history_months") in ("negligible", "weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has at most a moderate effect on default risk.
    - `strength("dti") in ("negligible", "weak", "moderate")`: ok
7. Feature b has at most a moderate effect on default risk.
    - `strength("noise_2") in ("negligible", "weak", "moderate")`: ok
8. Age hardly matters for default risk.
    - `negligible("age")`: ok
9. Feature a hardly matters for default risk.
    - `negligible("noise_1")`: ok
10. The number of recent inquiries hardly matters for default risk.
    - `negligible("n_inquiries")`: ok

## syn-none-n5000-s1_XGB2_H1_d2_claude-haiku-5-5_plausible

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (17 claims, 5 failing)
1. Revolving credit utilization is the most important driver of predicted default, and risk rises sharply once the share of the credit limit in use gets high.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
2. The number of past delinquencies is the second or third most important driver, and having any delinquency raises risk.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
3. Annual income is also among the top three drivers, and higher income lowers predicted risk.
    - `rank("income") in (2, 3)`: ok
    - `direction("income") == "decreasing"`: ok
    - `strength("income") == "moderate"`: **undecidable** (share band straddles a class edge)
4. The effect of utilization grows with the number of past delinquencies, so high utilization matters more for applicants with a delinquency history.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: **undecidable**
5. Length of credit history lowers risk, but its effect is small.
    - `direction("history_months") == "decreasing"`: ok
    - `strength("history_months") in ("negligible", "weak")`: **undecidable** (share band not settled against [0%, 5%))
6. The data do not settle whether debt-to-income ratio has a weak effect on its own.
    - `unsettled(strength("dti") == "weak")`: ok
7. Age, months at address, recent inquiries and number of dependents hardly matter for predicted default.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `negligible("n_inquiries")`: ok
    - `negligible("noise_2")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)

### Version 1: reduced (4 claims, 0 failing, missing: n_delinquencies, income)
1. Revolving credit utilization is the most important driver of predicted default, and risk rises sharply once the share of the credit limit in use gets high.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
6. The data do not settle whether debt-to-income ratio has a weak effect on its own.
    - `unsettled(strength("dti") == "weak")`: ok

### Version 2: template (14 claims, 0 failing)
1. Credit utilization has a strong effect on default risk; default risk increases with credit utilization.
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies has a moderate to strong effect on default risk; default risk increases with the number of past delinquencies.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Default risk jumps at the number of past delinquencies = 1.
    - `threshold("n_delinquencies", at=1.0)`: ok
4. Income has a moderate to strong effect on default risk; default risk decreases with income.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
5. The length of credit history has at most a moderate effect on default risk; default risk decreases with the length of credit history.
    - `strength("history_months") in ("negligible", "weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has at most a moderate effect on default risk.
    - `strength("dti") in ("negligible", "weak", "moderate")`: ok
7. The number of dependents has at most a moderate effect on default risk.
    - `strength("noise_2") in ("negligible", "weak", "moderate")`: ok
8. Age hardly matters for default risk.
    - `negligible("age")`: ok
9. Months at the current address hardly matters for default risk.
    - `negligible("noise_1")`: ok
10. The number of recent inquiries hardly matters for default risk.
    - `negligible("n_inquiries")`: ok

## syn-none-n5000-s1_XGB2_H1_d3_claude-haiku-5-5_opaque

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (0 claims, 0 failing, missing: utilization, n_delinquencies, income)
1. Revolving credit utilization is by far the most important driver of default risk, and risk rises sharply once utilization passes about 0.72.
2. The number of past delinquencies is the second or third most important driver, and risk increases when an applicant has any past delinquency.
3. Income is also among the second or third most important drivers, and risk generally decreases as income rises.
4. Length of credit history has at most a weak effect, with risk decreasing as history gets longer.
5. Debt-to-income ratio has at most a weak effect, and the data do not settle whether it moves risk in either direction.
6. Age, the two standardised application attributes and recent credit inquiries hardly matter, and the data do not settle whether they affect risk at all.
7. The effect of utilization is largely the same whatever the level of delinquencies, income or history, so these pairs do not change the picture much.

### Version 1: reduced (0 claims, 0 failing, missing: utilization, n_delinquencies, income)
1. Revolving credit utilization is by far the most important driver of default risk, and risk rises sharply once utilization passes about 0.72.
2. The number of past delinquencies is the second or third most important driver, and risk increases when an applicant has any past delinquency.
3. Income is also among the second or third most important drivers, and risk generally decreases as income rises.
4. Length of credit history has at most a weak effect, with risk decreasing as history gets longer.
5. Debt-to-income ratio has at most a weak effect, and the data do not settle whether it moves risk in either direction.
6. Age, the two standardised application attributes and recent credit inquiries hardly matter, and the data do not settle whether they affect risk at all.
7. The effect of utilization is largely the same whatever the level of delinquencies, income or history, so these pairs do not change the picture much.

### Version 2: template (14 claims, 0 failing)
1. Credit utilization has a strong effect on default risk; default risk increases with credit utilization.
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies has a moderate to strong effect on default risk; default risk increases with the number of past delinquencies.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Default risk jumps at the number of past delinquencies = 1.
    - `threshold("n_delinquencies", at=1.0)`: ok
4. Income has a moderate to strong effect on default risk; default risk decreases with income.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
5. The length of credit history has at most a moderate effect on default risk; default risk decreases with the length of credit history.
    - `strength("history_months") in ("negligible", "weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has at most a moderate effect on default risk.
    - `strength("dti") in ("negligible", "weak", "moderate")`: ok
7. Feature b has at most a moderate effect on default risk.
    - `strength("noise_2") in ("negligible", "weak", "moderate")`: ok
8. Age hardly matters for default risk.
    - `negligible("age")`: ok
9. Feature a hardly matters for default risk.
    - `negligible("noise_1")`: ok
10. The number of recent inquiries hardly matters for default risk.
    - `negligible("n_inquiries")`: ok

## syn-none-n5000-s1_XGB2_H1_d3_claude-haiku-5-5_plausible

**RELEASED_REDUCED**: failing sentences dropped after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (16 claims, 5 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk generally increases as the share of the credit limit in use rises.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. Its effect is sharpest above about 72% utilization, where the model's contribution to default risk rises much more steeply than at lower levels.
    - `threshold("utilization", at=0.719)`: **false**
3. Past delinquencies are the second or third most important driver: having any delinquency on file raises default risk compared with having none.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
4. Income is also among the top three drivers, and higher income generally lowers default risk.
    - `rank("income") in (2, 3)`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has at most a weak effect, with longer histories generally associated with lower risk.
    - `strength("history_months") in ("negligible", "weak")`: **undecidable** (share band not settled against [0%, 5%))
    - `direction("history_months") == "decreasing"`: ok
6. The effect of utilization grows with past delinquencies, so the combination of high utilization and delinquencies is especially risky.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: **undecidable**
7. Debt-to-income ratio has at most a weak effect, and the data do not settle whether it increases default risk.
    - `strength("dti") in ("negligible", "weak")`: **undecidable** (share band not settled against [0%, 5%))
    - `unsettled(direction("dti") == "increasing")`: ok
8. Age, number of dependents, months at address and recent credit inquiries hardly matter for the model's predictions.
    - `negligible("age")`: ok
    - `negligible("noise_2")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("noise_1")`: ok
    - `negligible("n_inquiries")`: ok

### Version 1: reduced (6 claims, 0 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk generally increases as the share of the credit limit in use rises.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
3. Past delinquencies are the second or third most important driver: having any delinquency on file raises default risk compared with having none.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
4. Income is also among the top three drivers, and higher income generally lowers default risk.
    - `rank("income") in (2, 3)`: ok
    - `direction("income") == "decreasing"`: ok

## syn-none-n5000-s1_XGB2_H1_d4_claude-haiku-5-5_opaque

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (16 claims, 6 failing)
1. Revolving credit utilization is the most important driver of default risk, accounting for roughly a third to almost half of the model's importance, and risk increases as utilization rises.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The increase is concentrated at high utilization, where risk takes a sharp step up at about 0.72 of the credit limit in use.
    - `threshold("utilization", at=0.719)`: **false**
3. Past delinquencies are the second strongest driver, and applicants with at least one delinquency carry clearly higher risk than those with none.
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
    - `direction("n_delinquencies") == "increasing"`: ok
4. Income has a weak to moderate effect, with higher incomes associated with lower default risk.
    - `strength("income") in ("weak", "moderate")`: **undecidable** (share band not settled against [2%, 15%))
    - `direction("income") == "decreasing"`: ok
5. The effect of utilization does not depend much on the number of delinquencies, so the two do not interact in a practically meaningful way, while the data do not settle whether the effect of utilization grows with credit history length.
    - `interaction("utilization", "n_delinquencies", pattern="none")`: **undecidable**
    - `unsettled(interaction("utilization", "history_months", pattern="amplification"))`: ok
6. Length of credit history has at most a weak effect, with longer histories linked to slightly lower risk.
    - `strength("history_months") in ("negligible", "weak")`: **undecidable** (share band not settled against [0%, 5%))
    - `direction("history_months") == "decreasing"`: ok
7. Debt-to-income ratio, applicant age, the two standardised application attributes and recent credit inquiries show no effect that the data can resolve, so their contribution is at most minor.
    - `unsettled(negligible("dti"))`: ok
    - `negligible("noise_2")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `negligible("n_inquiries")`: ok

### Version 1: reduced (2 claims, 0 failing, missing: n_delinquencies, income)
1. Revolving credit utilization is the most important driver of default risk, accounting for roughly a third to almost half of the model's importance, and risk increases as utilization rises.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok

### Version 2: template (14 claims, 0 failing)
1. Credit utilization has a strong effect on default risk; default risk increases with credit utilization.
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies has a moderate to strong effect on default risk; default risk increases with the number of past delinquencies.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Default risk jumps at the number of past delinquencies = 1.
    - `threshold("n_delinquencies", at=1.0)`: ok
4. Income has a moderate to strong effect on default risk; default risk decreases with income.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
5. The length of credit history has at most a moderate effect on default risk; default risk decreases with the length of credit history.
    - `strength("history_months") in ("negligible", "weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has at most a moderate effect on default risk.
    - `strength("dti") in ("negligible", "weak", "moderate")`: ok
7. Feature b has at most a moderate effect on default risk.
    - `strength("noise_2") in ("negligible", "weak", "moderate")`: ok
8. Age hardly matters for default risk.
    - `negligible("age")`: ok
9. Feature a hardly matters for default risk.
    - `negligible("noise_1")`: ok
10. The number of recent inquiries hardly matters for default risk.
    - `negligible("n_inquiries")`: ok

## syn-none-n5000-s1_XGB2_H1_d4_claude-haiku-5-5_plausible

**RELEASED_REDUCED**: failing sentences dropped after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (13 claims, 3 failing)
1. Revolving credit utilization is the most important driver of predicted default, and risk rises as utilization goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The jump is sharpest at about 72% utilization, where the added risk becomes large compared with lower levels.
    - `threshold("utilization", at=0.719)`: **false**
3. Past delinquencies are the second or third most important driver, and having any delinquency raises risk.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
4. Income is also a second or third most important driver, and higher income is associated with lower risk.
    - `rank("income") in (2, 3)`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history matters at most weakly, with longer histories associated with somewhat lower risk.
    - `strength("history_months") in ("negligible", "weak")`: **undecidable** (share band not settled against [0%, 5%))
    - `direction("history_months") == "decreasing"`: ok
6. The data do not settle how much the debt-to-income ratio matters, since its estimated effect is small and uncertain.
    - `unsettled(strength("dti") == "weak")`: ok
7. The effect of utilization on default risk is at least as large when there are past delinquencies, though the data leave this interaction only partly settled.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: **undecidable**
8. The data do not settle whether the effect of utilization grows with length of credit history.
    - `unsettled(interaction("utilization", "history_months", pattern="amplification"))`: ok
9. Age hardly matters for the model's predictions.
    - `negligible("age")`: ok

### Version 1: reduced (9 claims, 0 failing)
1. Revolving credit utilization is the most important driver of predicted default, and risk rises as utilization goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
3. Past delinquencies are the second or third most important driver, and having any delinquency raises risk.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
4. Income is also a second or third most important driver, and higher income is associated with lower risk.
    - `rank("income") in (2, 3)`: ok
    - `direction("income") == "decreasing"`: ok
6. The data do not settle how much the debt-to-income ratio matters, since its estimated effect is small and uncertain.
    - `unsettled(strength("dti") == "weak")`: ok
8. The data do not settle whether the effect of utilization grows with length of credit history.
    - `unsettled(interaction("utilization", "history_months", pattern="amplification"))`: ok
9. Age hardly matters for the model's predictions.
    - `negligible("age")`: ok
