# Pilot traces: naming

## syn-dominant-n50000-s1_EBM_H1_d0_claude-haiku-5-5_opaque

**RELEASED_REDUCED**: failing sentences dropped after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (14 claims, 3 failing)
1. Revolving credit utilization is the most important driver of predicted default, and risk rises steeply as utilization climbs, especially above about 60% of the credit limit.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk rises with it, with the largest jump between zero and one past delinquency.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Higher income is associated with lower predicted risk, though its effect is moderate to weak.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
4. A longer credit history is associated with lower predicted risk, with a moderate to weak effect.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
5. The effect of utilization grows with the number of past delinquencies, so high utilization matters far more for applicants who have delinquencies.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
6. The debt-to-income ratio has a weak effect, with risk somewhat higher above a ratio of about 0.44.
    - `strength("dti") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("dti") == "increasing"`: ok
7. Age has a negligible effect, and the data do not settle whether the two application attributes matter at all.
    - `negligible("age")`: ok
    - `unsettled(negligible("noise_1"))`: **false** (the claim is settled: it is true)
    - `unsettled(negligible("noise_2"))`: **false** (the claim is settled: it is true)

### Version 1: reduced (9 claims, 0 failing)
1. Revolving credit utilization is the most important driver of predicted default, and risk rises steeply as utilization climbs, especially above about 60% of the credit limit.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk rises with it, with the largest jump between zero and one past delinquency.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Higher income is associated with lower predicted risk, though its effect is moderate to weak.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
4. A longer credit history is associated with lower predicted risk, with a moderate to weak effect.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
5. The effect of utilization grows with the number of past delinquencies, so high utilization matters far more for applicants who have delinquencies.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok

## syn-dominant-n50000-s1_EBM_H1_d0_claude-haiku-5-5_plausible

**RELEASED_REDUCED**: failing sentences dropped after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (15 claims, 1 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises steeply as the share of the credit limit in use climbs, especially above about 0.7.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, with risk higher for applicants with at least one delinquency on file than for those with none.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. The effect of utilization grows with the number of delinquencies: a high utilization adds much more risk for applicants who have past delinquencies than for those who have none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income has a weak to moderate effect, with higher income associated with lower default risk.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a weak to moderate effect, with longer histories associated with lower default risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has a weak effect, and risk rises somewhat once the ratio passes about 0.44.
    - `strength("dti") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("dti") == "increasing"`: ok
7. Age, number of dependents and months at the current address hardly matter, since the data do not resolve any clear effect for them.
    - `negligible("age")`: ok
    - `negligible("noise_2")`: ok
    - `negligible("noise_1")`: ok
8. The data do not settle whether the effect of credit history reverses direction with recent credit inquiries, so we do not draw a conclusion about that interaction.
    - `unsettled(interaction("history_months", "n_inquiries", pattern="sign_flip"))`: ok

### Version 1: reduced (13 claims, 0 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises steeply as the share of the credit limit in use climbs, especially above about 0.7.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, with risk higher for applicants with at least one delinquency on file than for those with none.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. The effect of utilization grows with the number of delinquencies: a high utilization adds much more risk for applicants who have past delinquencies than for those who have none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income has a weak to moderate effect, with higher income associated with lower default risk.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a weak to moderate effect, with longer histories associated with lower default risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
7. Age, number of dependents and months at the current address hardly matter, since the data do not resolve any clear effect for them.
    - `negligible("age")`: ok
    - `negligible("noise_2")`: ok
    - `negligible("noise_1")`: ok
8. The data do not settle whether the effect of credit history reverses direction with recent credit inquiries, so we do not draw a conclusion about that interaction.
    - `unsettled(interaction("history_months", "n_inquiries", pattern="sign_flip"))`: ok

## syn-dominant-n50000-s1_EBM_H1_d1_claude-haiku-5-5_opaque

**RELEASED_REDUCED**: failing sentences dropped after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (15 claims, 2 failing)
1. Revolving credit utilization is the most important driver of default risk, with about 28% of the model's importance, and risk rises steeply as the share of the credit limit in use goes up, especially above roughly 0.6.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk rises from none to one delinquency and then levels off at two or more.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Income and length of credit history each have a moderate to weak effect, with higher income and longer histories associated with lower predicted risk.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
4. Utilization and past delinquencies interact strongly: the effect of utilization is much larger for applicants with two delinquencies than for those with none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
5. The debt-to-income ratio has a weak effect, with risk somewhat higher above about 0.44.
    - `strength("dti") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("dti") == "increasing"`: ok
6. Age and the two anonymised application attributes have negligible effects, and the data do not settle whether feature_b matters at all.
    - `negligible("noise_1")`: ok
    - `negligible("age")`: ok
    - `unsettled(negligible("noise_2"))`: **false** (the claim is settled: it is true)
7. Recent credit inquiries have at most a weak effect on the predictions.
    - `strength("n_inquiries") in ("negligible", "weak")`: ok

### Version 1: reduced (10 claims, 0 failing)
1. Revolving credit utilization is the most important driver of default risk, with about 28% of the model's importance, and risk rises steeply as the share of the credit limit in use goes up, especially above roughly 0.6.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk rises from none to one delinquency and then levels off at two or more.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Income and length of credit history each have a moderate to weak effect, with higher income and longer histories associated with lower predicted risk.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
4. Utilization and past delinquencies interact strongly: the effect of utilization is much larger for applicants with two delinquencies than for those with none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
7. Recent credit inquiries have at most a weak effect on the predictions.
    - `strength("n_inquiries") in ("negligible", "weak")`: ok

## syn-dominant-n50000-s1_EBM_H1_d1_claude-haiku-5-5_plausible

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (13 claims, 4 failing)
1. Revolving credit utilization is the most important driver of default risk, accounting for about 28% of the model's importance, and risk rises steadily as utilization climbs, most sharply above roughly 0.6 of the credit limit in use.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk mostly increases with it, with the largest rise between zero and one past delinquency.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "mostly_increasing"`: **undecidable** (no exception detected, and the bands do not rule a small one out (D29))
3. Utilization and past delinquencies interact strongly: the effect of high utilization is much larger for applicants who have delinquencies on record.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income has a weak to moderate effect, with lower income associated with higher risk.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a weak to moderate effect, with longer histories associated with lower risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. Recent credit inquiries interact with credit history length, so the effect of inquiries reverses depending on how long the applicant's history is.
    - `interaction("history_months", "n_inquiries", pattern="sign_flip")`: **undecidable**
7. The debt-to-income ratio has a weak effect, with risk rising somewhat once the ratio passes about 0.44.
    - `strength("dti") == "weak"`: **undecidable** (share band straddles a class edge)
8. The data do not settle whether the number of dependents matters at all, and months at address and age have negligible effects on the predictions.
    - `unsettled(negligible("noise_2"))`: **false** (the claim is settled: it is true)
    - `negligible("age")`: ok

### Version 1: reduced (7 claims, 0 failing, missing: n_delinquencies)
1. Revolving credit utilization is the most important driver of default risk, accounting for about 28% of the model's importance, and risk rises steadily as utilization climbs, most sharply above roughly 0.6 of the credit limit in use.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
3. Utilization and past delinquencies interact strongly: the effect of high utilization is much larger for applicants who have delinquencies on record.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income has a weak to moderate effect, with lower income associated with higher risk.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a weak to moderate effect, with longer histories associated with lower risk.
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

## syn-dominant-n50000-s1_EBM_H1_d2_claude-haiku-5-5_opaque

**RELEASED_REDUCED**: failing sentences dropped after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (15 claims, 2 failing)
1. Credit card utilization is the most important driver of predicted default, and predicted risk rises steeply as the share of the credit limit in use goes up, from a clear reduction in risk at low use to a large increase at high use.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and predicted risk rises as delinquencies accumulate, with the largest step between zero and one past delinquency.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Higher income is associated with lower predicted risk, but income is a weak to moderate effect rather than one of the leading drivers.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
4. A longer credit history is associated with lower predicted risk, a weak to moderate effect of similar size to income.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
5. The debt-to-income ratio is a weak effect, with predicted risk somewhat higher above a ratio of about 0.44.
    - `strength("dti") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("dti") == "increasing"`: ok
6. The effect of utilization is much larger for applicants with past delinquencies, so the two features amplify each other.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
7. The data do not settle whether the effect of credit history reverses with the number of recent inquiries, although the estimated effects of history length have opposite signs at low and high inquiry counts.
    - `interaction("history_months", "n_inquiries", pattern="sign_flip")`: **undecidable**
8. The applicant's age and the two unnamed application attributes hardly matter for predicted default.
    - `negligible("noise_1")`: ok
    - `negligible("noise_2")`: ok
    - `negligible("age")`: ok

### Version 1: reduced (12 claims, 0 failing)
1. Credit card utilization is the most important driver of predicted default, and predicted risk rises steeply as the share of the credit limit in use goes up, from a clear reduction in risk at low use to a large increase at high use.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and predicted risk rises as delinquencies accumulate, with the largest step between zero and one past delinquency.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Higher income is associated with lower predicted risk, but income is a weak to moderate effect rather than one of the leading drivers.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
4. A longer credit history is associated with lower predicted risk, a weak to moderate effect of similar size to income.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The effect of utilization is much larger for applicants with past delinquencies, so the two features amplify each other.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
8. The applicant's age and the two unnamed application attributes hardly matter for predicted default.
    - `negligible("noise_1")`: ok
    - `negligible("noise_2")`: ok
    - `negligible("age")`: ok

## syn-dominant-n50000-s1_EBM_H1_d2_claude-haiku-5-5_plausible

**RELEASED_REDUCED**: failing sentences dropped after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (14 claims, 3 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk generally increases with it, with the largest jump between zero and one delinquency.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") in ("increasing", "mostly_increasing")`: ok
3. The effect of utilization grows strongly with the number of delinquencies: a high utilization adds far more risk for applicants with delinquencies than for those without.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income has a moderate effect, and risk decreases as income rises.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a moderate effect, with risk decreasing as the history gets longer.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has a weak effect, with risk increasing as the ratio rises.
    - `strength("dti") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("dti") == "increasing"`: ok
7. Age has negligible influence, and the data do not settle whether the number of dependents matters at all.
    - `negligible("age")`: ok
    - `unsettled(negligible("noise_2"))`: **false** (the claim is settled: it is true)
8. Recent credit inquiries and credit history length interact, with the effect of history length reversing direction depending on the number of inquiries.
    - `interaction("history_months", "n_inquiries", pattern="sign_flip")`: **undecidable**

### Version 1: reduced (9 claims, 0 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk generally increases with it, with the largest jump between zero and one delinquency.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") in ("increasing", "mostly_increasing")`: ok
3. The effect of utilization grows strongly with the number of delinquencies: a high utilization adds far more risk for applicants with delinquencies than for those without.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income has a moderate effect, and risk decreases as income rises.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a moderate effect, with risk decreasing as the history gets longer.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok

## syn-dominant-n50000-s1_EBM_H1_d3_claude-haiku-5-5_opaque

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (17 claims, 4 failing)
1. Revolving credit utilization is the most important driver of predicted default, accounting for about 28% of the model's importance, and risk rises strongly as utilization climbs toward the top of its range.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "mostly_increasing"`: **undecidable** (no exception detected, and the bands do not rule a small one out (D29))
    - `share("utilization") == approx(0.279)`: ok
2. The number of past delinquencies is the second most important driver, with risk rising from no delinquencies to one and then to two or more.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "mostly_increasing"`: **undecidable** (no exception detected, and the bands do not rule a small one out (D29))
    - `share("n_delinquencies") == approx(0.172)`: ok
3. The two leading drivers interact strongly: the effect of utilization is much larger for applicants with two past delinquencies than for applicants with none, so high utilization is far more dangerous when the credit file already shows delinquencies.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income and length of credit history have moderate-to-weak effects, with higher income and longer histories both associated with lower predicted risk.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") in ("decreasing", "mostly_decreasing")`: ok
5. The debt-to-income ratio has a weak effect, with risk generally rising for higher ratios.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") in ("decreasing", "mostly_decreasing")`: ok
6. Recent credit inquiries interact with credit history length: the effect of inquiries reverses direction depending on how long the history is, and the data do not settle how this reversal should be interpreted in isolation.
    - `strength("dti") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("dti") in ("increasing", "mostly_increasing")`: ok
7. Feature_b, feature_a and age hardly matter to the model's predictions.
    - `interaction("history_months", "n_inquiries", pattern="sign_flip")`: **undecidable**
8. The data do not settle whether utilization's effect depends on feature_a, since that interaction's share of importance is too uncertain to rule out a small effect.
    - `negligible("noise_2")`: ok
    - `negligible("noise_1")`: ok
    - `negligible("age")`: ok
    - format error: sentence 9: unsettled(interaction("utilization", "feature_a", pattern="none")): there is no sentence with this id

### Version 1: reduced (8 claims, 0 failing, missing: utilization, n_delinquencies)
3. The two leading drivers interact strongly: the effect of utilization is much larger for applicants with two past delinquencies than for applicants with none, so high utilization is far more dangerous when the credit file already shows delinquencies.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income and length of credit history have moderate-to-weak effects, with higher income and longer histories both associated with lower predicted risk.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") in ("decreasing", "mostly_decreasing")`: ok
5. The debt-to-income ratio has a weak effect, with risk generally rising for higher ratios.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") in ("decreasing", "mostly_decreasing")`: ok
8. The data do not settle whether utilization's effect depends on feature_a, since that interaction's share of importance is too uncertain to rule out a small effect.
    - `negligible("noise_2")`: ok
    - `negligible("noise_1")`: ok
    - `negligible("age")`: ok

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
8. Feature b hardly matters for default risk.
    - `negligible("noise_2")`: ok
9. Feature a hardly matters for default risk.
    - `negligible("noise_1")`: ok
10. Age hardly matters for default risk.
    - `negligible("age")`: ok
11. The effect of credit utilization grows with the number of past delinquencies.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
12. The effect of the number of past delinquencies reverses its sign as credit utilization changes.
    - `interaction("n_delinquencies", "utilization", pattern="sign_flip")`: ok
13. The effect of the number of recent inquiries reverses its sign as the length of credit history changes.
    - `interaction("n_inquiries", "history_months", pattern="sign_flip")`: ok

## syn-dominant-n50000-s1_EBM_H1_d3_claude-haiku-5-5_plausible

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (16 claims, 3 failing)
1. Revolving credit utilization is the most important driver of predicted default, accounting for about 28% of the model's importance, and risk generally rises as utilization climbs, with the sharpest increases at the high end.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "mostly_increasing"`: **undecidable** (no exception detected, and the bands do not rule a small one out (D29))
    - `share("utilization") == approx(0.28)`: ok
2. The number of past delinquencies is the second most important driver, and risk increases with it, with most of the rise occurring between zero and one or two delinquencies.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `strength("n_delinquencies") == "strong"`: ok
3. The two features interact strongly: the added risk from high utilization is much larger for applicants with past delinquencies, so the effect of utilization grows with the number of delinquencies.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
    - `effect("utilization & n_delinquencies") > effect("income")`: ok
4. Income and length of credit history each have a moderate effect, with higher income and longer histories associated with lower predicted risk.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
5. Debt-to-income ratio has a weak effect, and the data do not settle how strongly the remaining features matter beyond the ones named above.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The data do not settle whether number of dependents has any effect, and age and months at the current address show no effect that the data can detect.
    - `unsettled(strength("noise_2") == "weak")`: ok
    - `unsettled(negligible("age"))`: **false** (the claim is settled: it is true)
7. Credit history length and recent inquiries interact, with the effect of inquiries reversing direction depending on how long the credit history is.
    - `interaction("history_months", "n_inquiries", pattern="sign_flip")`: **undecidable**
8. Utilization does not interact with months at the current address in any practically meaningful way.
    - `interaction("utilization", "noise_1", pattern="none")`: ok

### Version 1: reduced (10 claims, 0 failing, missing: utilization)
2. The number of past delinquencies is the second most important driver, and risk increases with it, with most of the rise occurring between zero and one or two delinquencies.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `strength("n_delinquencies") == "strong"`: ok
3. The two features interact strongly: the added risk from high utilization is much larger for applicants with past delinquencies, so the effect of utilization grows with the number of delinquencies.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
    - `effect("utilization & n_delinquencies") > effect("income")`: ok
4. Income and length of credit history each have a moderate effect, with higher income and longer histories associated with lower predicted risk.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
5. Debt-to-income ratio has a weak effect, and the data do not settle how strongly the remaining features matter beyond the ones named above.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
8. Utilization does not interact with months at the current address in any practically meaningful way.
    - `interaction("utilization", "noise_1", pattern="none")`: ok

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

## syn-dominant-n50000-s1_EBM_H1_d4_claude-haiku-5-5_opaque

**RELEASED_REDUCED**: failing sentences dropped after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (15 claims, 3 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises steadily as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk rises with it, mainly moving from zero to one or two past delinquencies.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Higher income is associated with lower risk, with a moderate effect.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
4. Longer credit history is associated with lower risk, with a moderate effect.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok
5. Utilization and past delinquencies interact strongly: the effect of utilization is much larger for applicants with two past delinquencies than for those with none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
6. History length and recent inquiries reverse each other: more inquiries raise risk for applicants with short histories but lower it for those with long histories.
    - `interaction("history_months", "n_inquiries", pattern="sign_flip")`: **undecidable**
7. The debt-to-income ratio has a weak effect, with higher ratios raising risk.
    - `strength("dti") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("dti") == "increasing"`: ok
8. Age and the two unnamed application attributes hardly matter, and the data do not settle whether feature_b has any effect at all.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `unsettled(negligible("noise_2"))`: **false** (the claim is settled: it is true)

### Version 1: reduced (9 claims, 0 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises steadily as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk rises with it, mainly moving from zero to one or two past delinquencies.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Higher income is associated with lower risk, with a moderate effect.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
4. Longer credit history is associated with lower risk, with a moderate effect.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok
5. Utilization and past delinquencies interact strongly: the effect of utilization is much larger for applicants with two past delinquencies than for those with none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok

## syn-dominant-n50000-s1_EBM_H1_d4_claude-haiku-5-5_plausible

**RELEASED_REDUCED**: failing sentences dropped after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (16 claims, 3 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises steeply as the share of the credit limit in use climbs, with the largest increases above roughly 0.6.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
2. The number of past delinquencies is the second most important driver, and risk rises with it, mainly going from zero to one or two delinquencies.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `strength("n_delinquencies") == "strong"`: ok
3. The two drivers reinforce each other: the effect of utilization is much larger for applicants with two delinquencies than for applicants with none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income has a moderate effect, with risk falling as income rises.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a moderate effect, with risk falling as the history gets longer.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok
6. Debt-to-income ratio has a weak effect, with risk somewhat higher above about 0.44.
    - `strength("dti") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("dti") == "increasing"`: ok
7. Age hardly matters, and the data do not settle whether the number of dependents or months at the current address matter at all.
    - `negligible("age")`: ok
    - `unsettled(negligible("noise_2"))`: **false** (the claim is settled: it is true)
    - `unsettled(negligible("noise_1"))`: **false** (the claim is settled: it is true)
8. The data do not settle whether recent credit inquiries have a negligible effect, since their contribution is small and its band is wide.
    - format error: sentence 8: unsettled(strength("n_inquiries") == "negligible"): strength is one of ['weak', 'moderate', 'strong']

### Version 1: reduced (11 claims, 0 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises steeply as the share of the credit limit in use climbs, with the largest increases above roughly 0.6.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
2. The number of past delinquencies is the second most important driver, and risk rises with it, mainly going from zero to one or two delinquencies.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `strength("n_delinquencies") == "strong"`: ok
3. The two drivers reinforce each other: the effect of utilization is much larger for applicants with two delinquencies than for applicants with none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income has a moderate effect, with risk falling as income rises.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a moderate effect, with risk falling as the history gets longer.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok

## syn-dominant-n50000-s1_XGB2_H1_d0_claude-haiku-5-5_opaque

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (16 claims, 3 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises steeply as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, with risk rising from no delinquencies to two or more.
    - `rank("n_delinquencies") == 2`: ok
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
    - `direction("n_delinquencies") == "increasing"`: ok
3. Higher income is associated with lower default risk, a moderate effect.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
4. Longer credit history is associated with lower default risk, a moderate effect.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok
5. The effect of utilization grows with the number of past delinquencies, so high utilization matters much more for applicants who have delinquencies.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
6. The debt-to-income ratio has a weak effect, with risk rising at higher ratios.
    - `strength("dti") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("dti") == "increasing"`: ok
7. Age, and the two standardised application attributes, have effects the data do not settle as negligible.
    - `negligible("age")`: ok
    - `unsettled(negligible("noise_1"))`: **false** (the claim is settled: it is true)
    - `unsettled(negligible("noise_2"))`: ok

### Version 1: reduced (8 claims, 0 failing, missing: n_delinquencies)
1. Revolving credit utilization is the most important driver of default risk, and risk rises steeply as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
3. Higher income is associated with lower default risk, a moderate effect.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
4. Longer credit history is associated with lower default risk, a moderate effect.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok
5. The effect of utilization grows with the number of past delinquencies, so high utilization matters much more for applicants who have delinquencies.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok

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

## syn-dominant-n50000-s1_XGB2_H1_d1_claude-haiku-5-5_opaque

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (18 claims, 3 failing)
1. Revolving credit utilization is the most important driver of default risk, with a strong effect: risk rises as the share of the credit limit in use goes up, with the largest step at the highest utilization levels.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, also with a strong effect, and risk rises as the count goes from zero to two or more.
    - `rank("n_delinquencies") == 2`: ok
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
    - `direction("n_delinquencies") in ("increasing", "mostly_increasing")`: ok
3. Annual income has a moderate effect, and risk falls as income rises.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
4. Length of credit history has a moderate effect, and risk falls as the history gets longer.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok
5. The effect of utilization grows with the number of past delinquencies: the rise in risk from higher utilization is far larger for applicants with two delinquencies than for those with none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
6. Debt-to-income ratio has a weak effect, with risk rising somewhat at higher ratios.
    - `strength("dti") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("dti") == "increasing"`: ok
7. Age has no effect that the model can detect, and feature_a hardly matters.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `unsettled(direction("age") == "increasing")`: ok
8. The data do not settle whether feature_b has any real effect, or whether feature_a and feature_b interact.
    - `unsettled(negligible("noise_2"))`: ok
    - `unsettled(interaction("noise_1", "noise_2", pattern="none"))`: **false** (the claim is settled: it is true)

### Version 1: reduced (11 claims, 0 failing, missing: n_delinquencies)
1. Revolving credit utilization is the most important driver of default risk, with a strong effect: risk rises as the share of the credit limit in use goes up, with the largest step at the highest utilization levels.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
3. Annual income has a moderate effect, and risk falls as income rises.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
4. Length of credit history has a moderate effect, and risk falls as the history gets longer.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok
5. The effect of utilization grows with the number of past delinquencies: the rise in risk from higher utilization is far larger for applicants with two delinquencies than for those with none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
7. Age has no effect that the model can detect, and feature_a hardly matters.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `unsettled(direction("age") == "increasing")`: ok

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

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (18 claims, 3 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises steeply as the share of the credit limit in use goes up, with the biggest jump at high utilization.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk rises as delinquencies accumulate.
    - `rank("n_delinquencies") == 2`: ok
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
    - `direction("n_delinquencies") == "increasing"`: ok
3. The effect of utilization is much larger for applicants with more past delinquencies, so the two features amplify each other.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Higher income is associated with lower risk, but its effect is moderate to weak in importance.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
5. A longer credit history is associated with lower risk, and history length ranks among the next most important features.
    - `rank("history_months") in (3, 4)`: ok
    - `direction("history_months") == "decreasing"`: ok
6. Debt-to-income ratio has a weak effect, with risk higher at larger ratios.
    - `strength("dti") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("dti") == "increasing"`: ok
7. Age has a negligible effect, and the data do not settle whether the number of dependents or months at the current address matter.
    - `negligible("age")`: ok
    - `unsettled(negligible("noise_2"))`: ok
    - `unsettled(negligible("noise_1"))`: **false** (the claim is settled: it is true)
8. Recent credit inquiries have at most a weak effect, with risk slightly higher once there are three or more.
    - `strength("n_inquiries") in ("negligible", "weak")`: ok
    - `direction("n_inquiries") == "increasing"`: ok

### Version 1: reduced (10 claims, 0 failing, missing: n_delinquencies)
1. Revolving credit utilization is the most important driver of default risk, and risk rises steeply as the share of the credit limit in use goes up, with the biggest jump at high utilization.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
3. The effect of utilization is much larger for applicants with more past delinquencies, so the two features amplify each other.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Higher income is associated with lower risk, but its effect is moderate to weak in importance.
    - `strength("income") in ("weak", "moderate")`: ok
    - `direction("income") == "decreasing"`: ok
5. A longer credit history is associated with lower risk, and history length ranks among the next most important features.
    - `rank("history_months") in (3, 4)`: ok
    - `direction("history_months") == "decreasing"`: ok
8. Recent credit inquiries have at most a weak effect, with risk slightly higher once there are three or more.
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

## syn-dominant-n50000-s1_XGB2_H1_d2_claude-haiku-5-5_opaque

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (22 claims, 5 failing)
1. Revolving credit utilization is the most important driver of predicted default, accounting for about 27% of the model's importance, and predicted risk rises steadily as utilization goes up.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk rises as delinquencies accumulate.
    - `rank("n_delinquencies") == 2`: ok
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
    - `direction("n_delinquencies") == "increasing"`: ok
3. The two drivers interact strongly: the effect of utilization is much larger for applicants with two past delinquencies than for those with none, so the two together matter more than either alone.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income has a moderate effect, with higher income associated with lower predicted risk.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a moderate effect, with longer histories associated with lower predicted risk, though this effect is weaker for applicants with many recent inquiries.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has a weak effect, with higher ratios associated with somewhat higher risk.
    - `strength("dti") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("dti") == "increasing"`: ok
7. The data do not settle whether feature_a, feature_b and age have any consistent direction of effect, and each of them has a negligible share of importance.
    - `negligible("noise_2")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("noise_1")`: ok
    - `negligible("age")`: ok
    - `unsettled(direction("noise_2") == "increasing")`: ok
    - `unsettled(direction("noise_1") == "increasing")`: ok
    - `unsettled(direction("age") == "increasing")`: ok
8. Recent credit inquiries have a weak effect, with three or more inquiries adding a small amount to predicted risk.
    - `strength("n_inquiries") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("n_inquiries") == "increasing"`: ok
    - `interaction("history_months", "n_inquiries", pattern="amplification")`: **undecidable**

### Version 1: reduced (8 claims, 0 failing, missing: n_delinquencies)
1. Revolving credit utilization is the most important driver of predicted default, accounting for about 27% of the model's importance, and predicted risk rises steadily as utilization goes up.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
3. The two drivers interact strongly: the effect of utilization is much larger for applicants with two past delinquencies than for those with none, so the two together matter more than either alone.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income has a moderate effect, with higher income associated with lower predicted risk.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a moderate effect, with longer histories associated with lower predicted risk, though this effect is weaker for applicants with many recent inquiries.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok

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

## syn-dominant-n50000-s1_XGB2_H1_d2_claude-haiku-5-5_plausible

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (17 claims, 3 failing)
1. Revolving credit utilization is the most important driver of default risk, with a share of importance of about 27%, and risk rises steadily as utilization climbs, with the largest increases at the highest levels.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk rises as delinquencies accumulate, moving from low to clearly higher risk once an applicant has two or more.
    - `rank("n_delinquencies") == 2`: ok
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
    - `direction("n_delinquencies") == "increasing"`: ok
3. The effect of utilization grows with delinquencies: high utilization adds much more risk for applicants with past delinquencies than for those without.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Higher income is associated with lower risk, and the effect is moderate in size.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
5. A longer credit history is associated with lower risk, a moderate effect.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has a weak effect, with risk higher above about 0.43.
    - `strength("dti") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("dti") == "increasing"`: ok
7. Age and months at the current address have negligible effects, and the data do not settle whether the number of dependents matters.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `unsettled(negligible("noise_2"))`: ok
8. The data suggest that the number of recent credit inquiries reverses its effect depending on credit history length: it adds risk for short histories and hardly matters for long ones.
    - `interaction("history_months", "n_inquiries", pattern="sign_flip")`: **false**

### Version 1: reduced (11 claims, 0 failing, missing: n_delinquencies)
1. Revolving credit utilization is the most important driver of default risk, with a share of importance of about 27%, and risk rises steadily as utilization climbs, with the largest increases at the highest levels.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
3. The effect of utilization grows with delinquencies: high utilization adds much more risk for applicants with past delinquencies than for those without.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Higher income is associated with lower risk, and the effect is moderate in size.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
5. A longer credit history is associated with lower risk, a moderate effect.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok
7. Age and months at the current address have negligible effects, and the data do not settle whether the number of dependents matters.
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

## syn-dominant-n50000-s1_XGB2_H1_d3_claude-haiku-5-5_opaque

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (17 claims, 4 failing)
1. Revolving credit utilization is the most important driver of predicted default, and risk rises steeply as the share of the credit limit in use goes up, from a strongly lower contribution at low utilization to a strongly higher one above roughly 0.76.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
2. The number of past delinquencies is the second most important driver, and risk rises with it, with the largest step between zero and one or more past delinquencies.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
3. The effect of utilization grows with the number of delinquencies: a high utilization adds much more risk for applicants with past delinquencies than for those without.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Annual income is a moderate driver, and predicted risk falls as income rises.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history is a moderate driver, and risk falls as the history gets longer.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has at most a weak effect, with risk somewhat higher above a ratio of about 0.43.
    - `strength("dti") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("dti") == "increasing"`: ok
7. The data do not settle whether the two application attributes matter at all, and the applicant's age has a negligible effect.
    - `negligible("age")`: ok
    - `unsettled(negligible("noise_2"))`: ok
    - `unsettled(negligible("noise_1"))`: **false** (the claim is settled: it is true)
8. The number of recent credit inquiries matters mainly for applicants with short credit histories, so the two do interact, though this interaction is small compared with the main drivers.
    - `interaction("history_months", "n_inquiries", pattern="none")`: **undecidable**

### Version 1: reduced (8 claims, 0 failing, missing: n_delinquencies)
1. Revolving credit utilization is the most important driver of predicted default, and risk rises steeply as the share of the credit limit in use goes up, from a strongly lower contribution at low utilization to a strongly higher one above roughly 0.76.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
3. The effect of utilization grows with the number of delinquencies: a high utilization adds much more risk for applicants with past delinquencies than for those without.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Annual income is a moderate driver, and predicted risk falls as income rises.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history is a moderate driver, and risk falls as the history gets longer.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok

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

### Version 0: proposer (17 claims, 4 failing)
1. Revolving credit utilization is the most important driver of predicted default, accounting for about 27% of the model's importance, and predicted risk rises steadily as utilization climbs, with the largest increases above roughly 0.6 of the credit limit in use.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and predicted risk rises from having none to having two or more.
    - `rank("n_delinquencies") == 2`: ok
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
    - `direction("n_delinquencies") == "increasing"`: ok
3. The effect of utilization grows with the number of past delinquencies: a high utilization adds far more risk for applicants who have been delinquent before than for those who have not.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Annual income is a moderate driver, with predicted risk falling as income rises, mostly through the difference between the lowest incomes and those above about 82,000 dollars.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history is also a moderate driver, with longer histories associated with lower predicted risk.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has at most a weak effect, with predicted risk rising somewhat once the ratio passes about 0.43.
    - `strength("dti") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("dti") == "increasing"`: ok
7. Number of dependents, months at the current address, and age have negligible effects on predicted default in this model.
    - `negligible("noise_2")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("noise_1")`: ok
    - `negligible("age")`: ok
8. The data do not settle whether the effect of length of credit history reverses with the number of recent credit inquiries.
    - `unsettled(interaction("history_months", "n_inquiries", pattern="sign_flip"))`: **false** (the claim is settled: it is false)

### Version 1: reduced (8 claims, 0 failing, missing: n_delinquencies)
1. Revolving credit utilization is the most important driver of predicted default, accounting for about 27% of the model's importance, and predicted risk rises steadily as utilization climbs, with the largest increases above roughly 0.6 of the credit limit in use.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
3. The effect of utilization grows with the number of past delinquencies: a high utilization adds far more risk for applicants who have been delinquent before than for those who have not.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Annual income is a moderate driver, with predicted risk falling as income rises, mostly through the difference between the lowest incomes and those above about 82,000 dollars.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history is also a moderate driver, with longer histories associated with lower predicted risk.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok

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

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (19 claims, 3 failing)
1. Revolving credit utilization is the most important driver of predicted default, and risk rises steeply as the share of the credit limit in use goes up, from a strong negative contribution at low use to a large positive one at high use.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and risk rises with it, with the largest step between none and two or more.
    - `rank("n_delinquencies") == 2`: ok
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
    - `direction("n_delinquencies") == "increasing"`: ok
3. Annual income is a moderate driver, and higher income lowers predicted default risk.
    - `rank("income") in (3, 4)`: ok
    - `direction("income") == "decreasing"`: ok
    - `strength("income") == "moderate"`: ok
4. Length of credit history is also a moderate driver, and longer histories lower predicted default risk.
    - `rank("history_months") in (3, 4)`: ok
    - `direction("history_months") == "decreasing"`: ok
    - `strength("history_months") == "moderate"`: ok
5. Utilization and past delinquencies interact: the effect of utilization is much larger when an applicant has two delinquencies than when they have none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
6. The debt-to-income ratio has a weak effect, with higher ratios raising risk slightly.
    - `strength("dti") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("dti") == "increasing"`: ok
7. The data do not settle whether feature_b matters at all, since its share of importance is small and uncertain.
    - `unsettled(negligible("noise_2"))`: ok
8. Age has a negligible effect, and feature_a also has a negligible effect.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
9. The data do not settle whether feature_a and feature_b interact.
    - `unsettled(interaction("noise_1", "noise_2", pattern="none"))`: **false** (the claim is settled: it is true)

### Version 1: reduced (13 claims, 0 failing, missing: n_delinquencies)
1. Revolving credit utilization is the most important driver of predicted default, and risk rises steeply as the share of the credit limit in use goes up, from a strong negative contribution at low use to a large positive one at high use.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
3. Annual income is a moderate driver, and higher income lowers predicted default risk.
    - `rank("income") in (3, 4)`: ok
    - `direction("income") == "decreasing"`: ok
    - `strength("income") == "moderate"`: ok
4. Length of credit history is also a moderate driver, and longer histories lower predicted default risk.
    - `rank("history_months") in (3, 4)`: ok
    - `direction("history_months") == "decreasing"`: ok
    - `strength("history_months") == "moderate"`: ok
5. Utilization and past delinquencies interact: the effect of utilization is much larger when an applicant has two delinquencies than when they have none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
7. The data do not settle whether feature_b matters at all, since its share of importance is small and uncertain.
    - `unsettled(negligible("noise_2"))`: ok
8. Age has a negligible effect, and feature_a also has a negligible effect.
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

## syn-dominant-n50000-s1_XGB2_H1_d4_claude-haiku-5-5_plausible

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (15 claims, 4 failing)
1. Revolving credit utilization is the most important driver of predicted default, accounting for about 27% of the model's importance, and predicted risk rises steadily as the share of the credit limit in use goes up, with the largest increase at high utilization.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, and predicted risk rises with it, mainly moving from zero to one or two past delinquencies.
    - `rank("n_delinquencies") == 2`: ok
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
    - `direction("n_delinquencies") == "increasing"`: ok
3. The two features interact strongly: the rise in risk from higher utilization is far larger for applicants with two past delinquencies than for those with none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Annual income has a moderate effect, with predicted risk falling as income rises.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a moderate effect, with predicted risk falling as history gets longer, and this effect is stronger when the applicant has many recent credit inquiries.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The debt-to-income ratio has only a weak effect, with predicted risk rising somewhat once the ratio passes about 0.43.
    - `strength("dti") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("dti") == "increasing"`: ok
7. The data do not settle whether the number of dependents has more than a negligible effect on predicted default.
    - `unsettled(strength("noise_2") in ("negligible", "weak"))`: **false** (the claim is settled: it is true)
8. The data do not settle whether the applicant's age matters for predicted default.
    - `unsettled(negligible("age"))`: **false** (the claim is settled: it is true)

### Version 1: reduced (8 claims, 0 failing, missing: n_delinquencies)
1. Revolving credit utilization is the most important driver of predicted default, accounting for about 27% of the model's importance, and predicted risk rises steadily as the share of the credit limit in use goes up, with the largest increase at high utilization.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
3. The two features interact strongly: the rise in risk from higher utilization is far larger for applicants with two past delinquencies than for those with none.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Annual income has a moderate effect, with predicted risk falling as income rises.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a moderate effect, with predicted risk falling as history gets longer, and this effect is stronger when the applicant has many recent credit inquiries.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok

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

## syn-none-n5000-s1_EBM_H1_d0_claude-haiku-5-5_opaque

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (16 claims, 4 failing)
1. The largest driver of default risk is revolving credit utilization, the share of the credit limit an applicant is using, and risk rises steeply with it.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. Risk climbs most sharply once utilization passes about 0.735, where the contribution to default risk is highest.
    - `threshold("utilization", at=0.735)`: **false**
3. Past delinquencies are the next most important factor, and any delinquency raises risk compared with none.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `strength("n_delinquencies") == "moderate"`: **undecidable** (share band straddles a class edge)
    - `direction("n_delinquencies") == "increasing"`: ok
4. Higher income is associated with lower default risk, though its effect is smaller than that of utilization or delinquencies.
    - `rank("income") in (2, 3)`: ok
    - `direction("income") == "decreasing"`: ok
    - `strength("income") == "moderate"`: **undecidable** (share band straddles a class edge)
5. Utilization and credit history length are included in the model as an interaction, but the data do not settle whether the effect of utilization depends on history length.
    - `interaction("utilization", "history_months", pattern="none")`: ok
6. Credit history length has at most a weak effect on predicted risk, and its direction is not firmly established.
    - `unsettled(strength("history_months") in ("negligible", "weak"))`: ok
7. Debt-to-income ratio hardly matters, since no movement in its effect is resolved at this sample size.
    - `negligible("dti")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
8. The remaining features, including age, the two application attributes and recent credit inquiries, have effects that are negligible.
    - `negligible("noise_1 & noise_2")`: ok
    - `negligible("age")`: ok
    - `negligible("n_inquiries")`: ok

### Version 1: reduced (8 claims, 0 failing, missing: n_delinquencies, income)
1. The largest driver of default risk is revolving credit utilization, the share of the credit limit an applicant is using, and risk rises steeply with it.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
5. Utilization and credit history length are included in the model as an interaction, but the data do not settle whether the effect of utilization depends on history length.
    - `interaction("utilization", "history_months", pattern="none")`: ok
6. Credit history length has at most a weak effect on predicted risk, and its direction is not firmly established.
    - `unsettled(strength("history_months") in ("negligible", "weak"))`: ok
8. The remaining features, including age, the two application attributes and recent credit inquiries, have effects that are negligible.
    - `negligible("noise_1 & noise_2")`: ok
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

### Version 0: proposer (18 claims, 7 failing)
1. Revolving credit utilization is the most important driver of default risk, accounting for about 38% of the model's importance, and risk rises sharply as the share of the credit limit in use goes up, especially above roughly 0.7.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `share("utilization") == approx(0.376)`: **undecidable**
2. Past delinquencies are the second strongest driver, and having at least one delinquency on file raises the predicted risk compared with having none.
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. Annual income is the third strongest driver, with risk falling as income rises, mostly through the drop between the lowest income band and the middle and upper bands.
    - `strength("income") == "strong"`: **undecidable** (share band straddles a class edge)
    - `direction("income") == "decreasing"`: ok
4. Length of credit history has a weak to moderate effect, with longer histories associated with somewhat lower risk, though the data do not settle how large this effect is.
    - `unsettled(strength("history_months") in ("weak", "moderate"))`: **false** (the claim is settled: it is true)
    - `direction("history_months") == "decreasing"`: ok
5. Debt-to-income ratio, number of dependents, months at address, age and recent credit inquiries each have a negligible effect in this model, and the data do not settle whether debt-to-income has any effect at all.
    - `unsettled(negligible("dti"))`: ok
    - `negligible("noise_2")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("noise_1")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("age")`: ok
    - `negligible("n_inquiries")`: ok
6. The interactions in the model are small, and the data do not settle whether utilization's effect depends on debt-to-income, so the main drivers can be read largely on their own.
    - `interaction("utilization", "history_months", pattern="none")`: ok
    - `interaction("income", "age", pattern="none")`: ok
    - `unsettled(interaction("utilization", "dti", pattern="none"))`: **false** (the claim is settled: it is true)

### Version 1: template (14 claims, 0 failing)
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

### Version 0: proposer (20 claims, 7 failing)
1. Revolving credit utilization is the most important driver of default risk, with a strong effect: risk rises steadily as the share of the credit limit in use goes up, and is highest for applicants above about 0.74 utilization.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
    - `effect("utilization") > effect("n_delinquencies")`: ok
2. Past delinquencies are the second or third most important driver, with a moderate effect: having at least one delinquency raises the risk of default compared with having none.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `strength("n_delinquencies") == "moderate"`: **undecidable** (share band straddles a class edge)
3. Annual income is also among the top three drivers, with a weak to moderate effect: higher income lowers the predicted risk, with the largest drop between roughly 41,000 and 84,000 dollars.
    - `rank("income") in (2, 3)`: ok
    - `direction("income") == "decreasing"`: ok
    - `strength("income") in ("weak", "moderate")`: **undecidable** (share band not settled against [2%, 15%))
4. Length of credit history has a weak effect, mostly lowering risk as the history gets longer, though the data do not settle whether its effect is larger than weak.
    - `strength("history_months") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("history_months") == "decreasing"`: ok
    - `unsettled(strength("history_months") == "moderate")`: ok
5. The interaction between utilization and credit history is small, so the effect of utilization is about the same whatever the length of the history.
    - `interaction("utilization", "history_months", pattern="none")`: ok
6. Debt-to-income ratio, the two application attributes, applicant age and recent credit inquiries hardly matter to the model's predictions.
    - `negligible("dti")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("noise_1")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("noise_2")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("age")`: ok
    - `negligible("n_inquiries")`: ok
7. The data do not settle whether the lowering effect of income grows or shrinks with age.
    - `unsettled(interaction("income", "age", pattern="amplification"))`: **false** (the claim is settled: it is false)

### Version 1: reduced (5 claims, 0 failing, missing: income)
1. Revolving credit utilization is the most important driver of default risk, with a strong effect: risk rises steadily as the share of the credit limit in use goes up, and is highest for applicants above about 0.74 utilization.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
    - `effect("utilization") > effect("n_delinquencies")`: ok
5. The interaction between utilization and credit history is small, so the effect of utilization is about the same whatever the length of the history.
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

### Version 0: proposer (19 claims, 5 failing)
1. Revolving credit utilization is the most important driver of predicted default, with a strong effect that accounts for roughly 38% of the model's importance.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. Risk rises steeply once utilization passes about 0.74, where the contribution to default log-odds reaches its highest level.
    - `threshold("utilization", at=0.735)`: **false**
3. Past delinquencies are the second or third most important driver, with a moderate effect: having any past delinquency raises predicted risk compared with having none.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `strength("n_delinquencies") == "moderate"`: **undecidable** (share band straddles a class edge)
    - `direction("n_delinquencies") == "increasing"`: ok
4. Income is also among the top three drivers, and higher income lowers predicted default risk, with the largest change at the low end of the income range.
    - `rank("income") in (2, 3)`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a weak to moderate effect, with longer histories associated with lower risk, although the data do not settle the exact size of this effect.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
    - `unsettled(strength("history_months") == "moderate")`: ok
6. The effect of utilization is slightly larger when credit history is long, but the data do not settle whether this interaction is real at this sample size.
    - `unsettled(interaction("utilization", "history_months", pattern="amplification"))`: ok
7. Debt-to-income ratio, number of dependents, months at address, age and recent credit inquiries each have a negligible effect on predicted default.
    - `negligible("dti")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("noise_2")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("noise_1")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("age")`: ok
    - `negligible("n_inquiries")`: ok
8. Utilization and debt-to-income ratio do not interact in any way that matters for the predictions.
    - `interaction("utilization", "dti", pattern="none")`: ok

### Version 1: reduced (10 claims, 0 failing, missing: n_delinquencies)
1. Revolving credit utilization is the most important driver of predicted default, with a strong effect that accounts for roughly 38% of the model's importance.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
4. Income is also among the top three drivers, and higher income lowers predicted default risk, with the largest change at the low end of the income range.
    - `rank("income") in (2, 3)`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a weak to moderate effect, with longer histories associated with lower risk, although the data do not settle the exact size of this effect.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
    - `unsettled(strength("history_months") == "moderate")`: ok
6. The effect of utilization is slightly larger when credit history is long, but the data do not settle whether this interaction is real at this sample size.
    - `unsettled(interaction("utilization", "history_months", pattern="amplification"))`: ok
8. Utilization and debt-to-income ratio do not interact in any way that matters for the predictions.
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

## syn-none-n5000-s1_EBM_H1_d2_claude-haiku-5-5_opaque

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (17 claims, 6 failing)
1. Revolving credit utilization is by far the most important driver of default risk, accounting for about 38% of the model's importance, and risk rises steeply as utilization increases.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The steepest rise occurs once utilization passes about 0.74, where the added risk is largest.
    - `threshold("utilization", at=0.735)`: **false**
3. The number of past delinquencies is the next strongest driver: having any delinquency raises risk relative to none, and the effect is strong in importance but modest in size.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
    - `direction("n_delinquencies") == "increasing"`: ok
4. Income has a moderate effect, with risk falling as income rises, though most of that fall happens between the lower and middle income ranges.
    - `rank("income") in (2, 3)`: ok
    - `strength("income") == "moderate"`: **undecidable** (share band straddles a class edge)
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a moderate effect, with longer histories associated with lower risk.
    - `strength("history_months") == "moderate"`: **undecidable** (share band straddles a class edge)
    - `direction("history_months") == "decreasing"`: ok
6. The data show no meaningful interaction between utilization and credit history length.
    - `interaction("utilization", "history_months", pattern="none")`: ok
7. Debt-to-income ratio, feature_b, and feature_a each matter little, and the data do not settle whether feature_a has any effect at all.
    - `negligible("dti")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `unsettled(negligible("noise_1"))`: ok
8. Recent credit inquiries and applicant age hardly matter, and the data do not settle whether applicant age has any effect.
    - `negligible("n_inquiries")`: ok
    - `unsettled(negligible("age"))`: **false** (the claim is settled: it is true)

### Version 1: reduced (4 claims, 0 failing, missing: n_delinquencies, income)
1. Revolving credit utilization is by far the most important driver of default risk, accounting for about 38% of the model's importance, and risk rises steeply as utilization increases.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
6. The data show no meaningful interaction between utilization and credit history length.
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

### Version 0: proposer (17 claims, 5 failing)
1. Revolving credit utilization is the most important driver of default risk, accounting for roughly 38% of the model's importance, and risk rises as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
2. The increase is concentrated at high utilization: the contribution to risk is small below about 0.6 and climbs steeply above about 0.7.
    - `threshold("utilization", at=0.7)`: **false**
3. Past delinquencies come next, with about 23% of the importance; any delinquency on the file raises the risk of default relative to having none, and the effect is moderate.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `strength("n_delinquencies") == "moderate"`: **undecidable** (share band straddles a class edge)
4. Annual income is the third driver at about 16%; higher income lowers the predicted risk, with the effect strongest between the lowest and middle incomes.
    - `rank("income") in (2, 3)`: ok
    - `direction("income") == "decreasing"`: ok
    - `strength("income") == "moderate"`: **undecidable** (share band straddles a class edge)
5. Length of credit history has a weak effect, with longer histories lowering risk slightly.
    - `strength("history_months") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("history_months") == "decreasing"`: ok
6. The data do not settle whether debt-to-income ratio, number of dependents, months at address, age or recent credit inquiries matter at all, since their effects are not resolved at this sample size and they carry little importance.
    - `unsettled(strength("dti") in ("negligible", "weak"))`: ok
    - `negligible("noise_2")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("n_inquiries")`: ok
7. Utilization's effect is essentially the same whether history length or debt-to-income ratio is high or low, so no meaningful interaction is found with either.
    - `interaction("utilization", "history_months", pattern="none")`: ok
    - `interaction("utilization", "dti", pattern="none")`: ok

### Version 1: reduced (5 claims, 0 failing, missing: n_delinquencies, income)
1. Revolving credit utilization is the most important driver of default risk, accounting for roughly 38% of the model's importance, and risk rises as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
7. Utilization's effect is essentially the same whether history length or debt-to-income ratio is high or low, so no meaningful interaction is found with either.
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

## syn-none-n5000-s1_EBM_H1_d3_claude-haiku-5-5_opaque

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (15 claims, 4 failing)
1. Revolving credit utilization is by far the most important driver of default risk, and the risk rises steeply as the share of the credit limit in use climbs, most sharply above about 0.7.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. Past delinquencies are the next most important driver: having at least one delinquency on the file raises the predicted risk, with a moderate effect.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `strength("n_delinquencies") == "moderate"`: **undecidable** (share band straddles a class edge)
    - `direction("n_delinquencies") in ("increasing", "mostly_increasing")`: ok
3. Annual income is also a moderate driver, and higher income lowers the predicted risk, with the largest drop among applicants whose income is above about 84,000 dollars.
    - `rank("income") in (2, 3)`: ok
    - `strength("income") == "moderate"`: **undecidable** (share band straddles a class edge)
    - `direction("income") == "decreasing"`: ok
4. Length of credit history has a weaker effect, with longer histories associated with lower risk, though the size of this effect is uncertain.
    - `strength("history_months") == "moderate"`: **undecidable** (share band straddles a class edge)
    - `direction("history_months") == "decreasing"`: ok
5. The effect of utilization is about the same across different credit history lengths, so the two do not interact in any practically meaningful way.
    - `interaction("utilization", "history_months", pattern="none")`: ok
6. The data do not settle whether debt-to-income ratio, the two application attributes, and the age and inquiry features matter at all, since their effects cannot be resolved at this sample size.
    - `unsettled(negligible("dti"))`: ok
    - `unsettled(negligible("noise_1 & noise_2"))`: **false** (the claim is settled: it is true)
7. Recent credit inquiries hardly matter to the model's predictions.
    - `negligible("n_inquiries")`: ok

### Version 1: reduced (5 claims, 0 failing, missing: n_delinquencies, income)
1. Revolving credit utilization is by far the most important driver of default risk, and the risk rises steeply as the share of the credit limit in use climbs, most sharply above about 0.7.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
5. The effect of utilization is about the same across different credit history lengths, so the two do not interact in any practically meaningful way.
    - `interaction("utilization", "history_months", pattern="none")`: ok
7. Recent credit inquiries hardly matter to the model's predictions.
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

## syn-none-n5000-s1_EBM_H1_d3_claude-haiku-5-5_plausible

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (19 claims, 3 failing)
1. Revolving credit utilization is by far the most important driver of default risk, and risk rises sharply as utilization climbs, with a clear jump once utilization passes about 0.73.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
    - `threshold("utilization", at=0.735)`: **false**
    - `effect("utilization") > effect("n_delinquencies")`: ok
2. The number of past delinquencies is the next most important driver, with a moderate effect: having any delinquency raises default risk compared with having none.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `strength("n_delinquencies") == "moderate"`: **undecidable** (share band straddles a class edge)
    - `direction("n_delinquencies") == "increasing"`: ok
3. Annual income is also an important factor with a moderate effect, and higher income is associated with lower default risk.
    - `rank("income") in (2, 3)`: ok
    - `strength("income") == "moderate"`: **undecidable** (share band straddles a class edge)
    - `direction("income") == "decreasing"`: ok
4. Length of credit history has a weak to moderate effect, with longer histories associated with somewhat lower risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
5. The data do not settle whether debt-to-income ratio, number of dependents, months at address, age and recent inquiries matter, because their effects are too small or too uncertain to resolve at this sample size.
    - `unsettled(strength("dti") == "weak")`: ok
    - `unsettled(negligible("noise_2"))`: ok
6. Recent credit inquiries and applicant age hardly matter for the model's predictions.
    - `negligible("n_inquiries")`: ok
    - `negligible("age")`: ok
7. The interactions in the model are small: the effect of utilization is about the same whether credit history or debt-to-income ratio is high or low.
    - `interaction("utilization", "history_months", pattern="none")`: ok
    - `interaction("utilization", "dti", pattern="none")`: ok

### Version 1: reduced (8 claims, 0 failing, missing: utilization, n_delinquencies, income)
4. Length of credit history has a weak to moderate effect, with longer histories associated with somewhat lower risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
5. The data do not settle whether debt-to-income ratio, number of dependents, months at address, age and recent inquiries matter, because their effects are too small or too uncertain to resolve at this sample size.
    - `unsettled(strength("dti") == "weak")`: ok
    - `unsettled(negligible("noise_2"))`: ok
6. Recent credit inquiries and applicant age hardly matter for the model's predictions.
    - `negligible("n_inquiries")`: ok
    - `negligible("age")`: ok
7. The interactions in the model are small: the effect of utilization is about the same whether credit history or debt-to-income ratio is high or low.
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

### Version 0: proposer (18 claims, 4 failing)
1. Revolving credit utilization is the most important driver of default risk, accounting for about 38% of the model's importance, and risk rises steeply as utilization climbs, especially above about 70% of the credit limit.
    - `rank("utilization") == 1`: ok
    - `share("utilization") == approx(0.376)`: **undecidable**
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is a strong driver, and having at least one delinquency raises the predicted risk compared with having none.
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
    - `direction("n_delinquencies") == "increasing"`: ok
3. Annual income is a moderate to strong driver, and risk falls as income rises, with the largest drop between the lower and middle income bands.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
4. The effect of utilization is essentially the same whether the applicant has a short or long credit history, so the two do not meaningfully interact.
    - `interaction("utilization", "history_months", pattern="none")`: ok
5. Length of credit history has at most a weak effect, with longer histories associated with slightly lower risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The data do not settle whether the debt-to-income ratio has any effect on risk at this sample size.
    - `negligible("dti")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `unsettled(negligible("dti"))`: ok
7. Age, recent credit inquiries, and the two unnamed application attributes each hardly matter for the model's predictions.
    - `negligible("noise_1")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("age")`: ok
    - `negligible("n_inquiries")`: ok
8. The remaining interactions, between income and the application attributes or age, and between utilization and debt-to-income, are too small to matter in practice.
    - `interaction("income", "noise_2", pattern="none")`: ok
    - `interaction("income", "age", pattern="none")`: ok
    - `interaction("utilization", "dti", pattern="none")`: ok

### Version 1: reduced (8 claims, 0 failing, missing: utilization, n_delinquencies)
3. Annual income is a moderate to strong driver, and risk falls as income rises, with the largest drop between the lower and middle income bands.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
4. The effect of utilization is essentially the same whether the applicant has a short or long credit history, so the two do not meaningfully interact.
    - `interaction("utilization", "history_months", pattern="none")`: ok
5. Length of credit history has at most a weak effect, with longer histories associated with slightly lower risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
8. The remaining interactions, between income and the application attributes or age, and between utilization and debt-to-income, are too small to matter in practice.
    - `interaction("income", "noise_2", pattern="none")`: ok
    - `interaction("income", "age", pattern="none")`: ok
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

### Version 0: proposer (21 claims, 10 failing, missing: n_delinquencies, income)
1. Revolving credit utilization is the most important driver of default risk, and risk generally rises as utilization climbs.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "mostly_increasing"`: **undecidable** (no exception detected, and the bands do not rule a small one out (D29))
    - `strength("utilization") == "strong"`: ok
2. The steepest rise comes at high utilization, where the contribution to default risk jumps once utilization passes about 0.74 of the credit limit.
    - `threshold("utilization", at=0.735)`: **false**
3. Past delinquencies are the second or third most important driver, and having any delinquency on file raises default risk compared with having none.
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
    - `direction("n_delinquencies") == "mostly_increasing"`: **undecidable** (no exception detected, and the bands do not rule a small one out (D29))
    - `threshold("n_delinquencies", at=1.0)`: **false**
4. Income is also an important driver, with higher income lowering default risk, although the data do not settle whether its importance is moderate.
    - `unsettled(strength("income") == "moderate")`: ok
    - `direction("income") == "mostly_decreasing"`: **undecidable** (no exception detected, and the bands do not rule a small one out (D29))
    - `effect("n_delinquencies") > effect("income")`: **undecidable**
5. Length of credit history has a weak to moderate effect, with longer histories associated with somewhat lower default risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
6. Debt-to-income ratio, number of dependents, months at address, age and recent credit inquiries each hardly matter for the model's predictions.
    - `negligible("dti")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("noise_2")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("noise_1")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("age")`: ok
    - `negligible("n_inquiries")`: ok
7. The interactions in the model are small, and the data do not show that any of the pairs we examined changes the effect of one feature depending on the other.
    - `interaction("utilization", "history_months", pattern="none")`: ok
    - `interaction("income", "age", pattern="none")`: ok
    - `interaction("income", "noise_2", pattern="none")`: ok
    - `interaction("utilization", "dti", pattern="none")`: ok
    - `interaction("noise_1", "noise_2", pattern="none")`: ok

### Version 1: reduced (6 claims, 0 failing, missing: utilization, n_delinquencies, income)
5. Length of credit history has a weak to moderate effect, with longer histories associated with somewhat lower default risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
7. The interactions in the model are small, and the data do not show that any of the pairs we examined changes the effect of one feature depending on the other.
    - `interaction("utilization", "history_months", pattern="none")`: ok
    - `interaction("income", "age", pattern="none")`: ok
    - `interaction("income", "noise_2", pattern="none")`: ok
    - `interaction("utilization", "dti", pattern="none")`: ok
    - `interaction("noise_1", "noise_2", pattern="none")`: ok

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

### Version 0: proposer (18 claims, 7 failing)
1. Revolving credit utilization is the most important driver of default risk, accounting for roughly 37% of the model's importance, and risk rises with it.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The rise is concentrated: applicants using less than about 64% of their credit limit contribute little, while those above about 72% add a large increase in risk.
    - `threshold("utilization", at=0.719)`: **false**
3. Past delinquencies are the second strongest driver, with risk mostly increasing as the number of delinquencies rises from zero to one or more, though this effect is clearly smaller than that of utilization.
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
    - `direction("n_delinquencies") == "mostly_increasing"`: **undecidable** (no exception detected, and the bands do not rule a small one out (D29))
    - `effect("utilization") > effect("n_delinquencies")`: ok
4. Annual income is a moderate to strong driver in the model, with higher income associated with lower default risk.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a weak effect, with longer histories associated with somewhat lower risk.
    - `strength("history_months") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("history_months") == "decreasing"`: ok
6. The data do not settle whether debt-to-income ratio matters at all, since its estimated effect is not resolved at this sample size.
    - `unsettled(negligible("dti"))`: ok
7. Age, the two standardised application attributes and recent credit inquiries hardly matter to the model's predictions.
    - `negligible("noise_1")`: ok
    - `negligible("noise_2")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("age")`: ok
    - `negligible("n_inquiries")`: ok
8. Utilization's effect does not noticeably change with delinquencies or credit history length, so its influence is broadly the same across those applicants.
    - `interaction("utilization", "n_delinquencies", pattern="none")`: **undecidable**
    - `interaction("utilization", "history_months", pattern="none")`: **undecidable**

### Version 1: reduced (6 claims, 0 failing, missing: n_delinquencies)
1. Revolving credit utilization is the most important driver of default risk, accounting for roughly 37% of the model's importance, and risk rises with it.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
4. Annual income is a moderate to strong driver in the model, with higher income associated with lower default risk.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
6. The data do not settle whether debt-to-income ratio matters at all, since its estimated effect is not resolved at this sample size.
    - `unsettled(negligible("dti"))`: ok

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

### Version 0: proposer (17 claims, 5 failing)
1. Revolving credit utilization is by far the most important driver of predicted default, accounting for roughly 37% of the model's importance, and predicted risk rises as utilization increases.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The effect is concentrated at high utilization: risk stays roughly flat at low levels, rises modestly around 0.64 to 0.72, and jumps sharply above about 0.72.
    - `threshold("utilization", at=0.719)`: **false**
3. Past delinquencies are the second most important driver, and having any delinquency raises predicted default risk compared with having none.
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
    - `direction("n_delinquencies") == "increasing"`: ok
4. Higher income is associated with lower predicted risk, though its effect is smaller than that of utilization or delinquencies.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a weak effect, with longer histories associated with somewhat lower risk, and the shape of this relationship between the extremes is not resolved by the data.
    - `strength("history_months") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("history_months") == "decreasing"`: ok
6. The effect of utilization does not meaningfully change with the number of past delinquencies, so the two act largely independently.
    - `interaction("utilization", "n_delinquencies", pattern="none")`: **undecidable**
7. The data do not settle whether debt-to-income ratio has any real effect on predicted risk, since its estimated contribution is small and uncertain.
    - `unsettled(strength("dti") in ("negligible", "weak"))`: ok
8. Number of dependents, age, months at current address and recent credit inquiries each have a negligible effect on the model's predictions.
    - `negligible("noise_2")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `negligible("n_inquiries")`: ok
9. The data do not settle whether the effect of utilization grows with credit history length.
    - `unsettled(interaction("utilization", "history_months", pattern="amplification"))`: ok

### Version 1: reduced (7 claims, 0 failing, missing: n_delinquencies)
1. Revolving credit utilization is by far the most important driver of predicted default, accounting for roughly 37% of the model's importance, and predicted risk rises as utilization increases.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
4. Higher income is associated with lower predicted risk, though its effect is smaller than that of utilization or delinquencies.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
7. The data do not settle whether debt-to-income ratio has any real effect on predicted risk, since its estimated contribution is small and uncertain.
    - `unsettled(strength("dti") in ("negligible", "weak"))`: ok
9. The data do not settle whether the effect of utilization grows with credit history length.
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

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (23 claims, 8 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises sharply once utilization passes about 72% of the credit limit.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
    - `threshold("utilization", at=0.719)`: **false**
2. The number of past delinquencies is the second or third most important driver, and risk mostly increases with it, mainly moving from zero to one or more.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
    - `direction("n_delinquencies") == "mostly_increasing"`: **undecidable** (no exception detected, and the bands do not rule a small one out (D29))
    - `effect("utilization") > effect("n_delinquencies")`: ok
3. Annual income is also among the top three drivers, and higher income is associated with lower risk, though the effect is moderate and its shape is less clear.
    - `rank("income") in (2, 3)`: ok
    - `strength("income") == "moderate"`: **undecidable** (share band straddles a class edge)
    - `direction("income") == "decreasing"`: ok
4. Length of credit history has a weak effect, with longer histories associated with somewhat lower risk.
    - `strength("history_months") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("history_months") == "decreasing"`: ok
5. The data do not settle whether debt-to-income ratio matters at all at this sample size.
    - `unsettled(negligible("dti"))`: ok
6. The remaining features, including the two application attributes, age and recent credit inquiries, have effects that hardly matter.
    - `negligible("noise_2")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `negligible("n_inquiries")`: ok
7. Utilization's effect is stronger for applicants with more past delinquencies, while the other interactions are small and do not change the picture.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: **undecidable**
    - `interaction("utilization", "history_months", pattern="none")`: **undecidable**
    - `interaction("n_delinquencies", "history_months", pattern="none")`: ok
    - `interaction("utilization", "income", pattern="none")`: ok
    - `interaction("utilization", "dti", pattern="none")`: ok

### Version 1: reduced (1 claims, 0 failing, missing: utilization, n_delinquencies, income)
5. The data do not settle whether debt-to-income ratio matters at all at this sample size.
    - `unsettled(negligible("dti"))`: ok

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

## syn-none-n5000-s1_XGB2_H1_d1_claude-haiku-5-5_plausible

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (20 claims, 8 failing)
1. Revolving credit utilization is by far the most important driver of default risk, accounting for about 37% of the model's importance.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
    - `threshold("utilization", at=0.719)`: **false**
2. Past delinquencies are the second most important driver, and risk mostly increases with their count, with an effect that is strong in the model.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
    - `direction("n_delinquencies") == "mostly_increasing"`: **undecidable** (no exception detected, and the bands do not rule a small one out (D29))
3. Higher income is associated with lower default risk, though its effect is moderate.
    - `strength("income") == "moderate"`: **undecidable** (share band straddles a class edge)
    - `direction("income") == "decreasing"`: ok
4. Length of credit history has at most a weak effect, with longer histories linked to slightly lower risk.
    - `strength("history_months") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("history_months") == "decreasing"`: ok
5. The data do not settle whether debt-to-income ratio affects risk at all.
    - `unsettled(direction("dti") == "increasing")`: ok
6. Age, months at address, number of dependents and recent credit inquiries hardly matter for the predictions.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `negligible("noise_2")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("n_inquiries")`: ok
7. The effect of utilization is largely the same across the levels of delinquencies and income, so these pairs do not interact in any practically meaningful way.
    - `interaction("utilization", "n_delinquencies", pattern="none")`: **undecidable**
    - `interaction("utilization", "income", pattern="none")`: ok
8. Utilization's effect grows somewhat with delinquencies, and the interaction between history length and debt-to-income is too small to matter.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: **undecidable**
    - `interaction("history_months", "dti", pattern="none")`: ok

### Version 1: reduced (1 claims, 0 failing, missing: utilization, n_delinquencies, income)
5. The data do not settle whether debt-to-income ratio affects risk at all.
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

### Version 0: proposer (19 claims, 8 failing)
1. Revolving credit utilization is the strongest driver of predicted default, accounting for about 37% of the model's importance, and its effect is mostly increasing: risk stays low until utilization passes roughly 0.72 and then rises sharply.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "mostly_increasing"`: **undecidable** (no exception detected, and the bands do not rule a small one out (D29))
    - `threshold("utilization", at=0.719)`: **false**
2. Past delinquencies are the second most important driver, and risk increases with their number, mainly from having none to having at least one.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
    - `direction("n_delinquencies") == "increasing"`: ok
3. Higher income is associated with lower predicted risk, though its effect is moderate and concentrated in the step around 54,200 dollars.
    - `strength("income") == "moderate"`: **undecidable** (share band straddles a class edge)
    - `direction("income") == "decreasing"`: ok
4. Length of credit history has only a weak effect, with longer histories associated with somewhat lower risk.
    - `strength("history_months") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("history_months") == "decreasing"`: ok
5. The data do not settle whether the debt-to-income ratio has any consistent effect on risk.
    - `unsettled(direction("dti") == "increasing")`: ok
6. Application attributes such as age, the two standardised features and recent credit inquiries hardly matter.
    - `negligible("noise_1")`: ok
    - `negligible("noise_2")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("age")`: ok
    - `negligible("n_inquiries")`: ok
7. The effect of utilization is larger when there are past delinquencies, though this interaction is modest.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: **undecidable**
8. Utilization does not meaningfully interact with credit history length, and income and delinquencies do not interact in a way of practical size.
    - `interaction("utilization", "history_months", pattern="none")`: **undecidable**
    - `interaction("n_delinquencies", "income", pattern="none")`: ok

### Version 1: reduced (1 claims, 0 failing, missing: utilization, n_delinquencies, income)
5. The data do not settle whether the debt-to-income ratio has any consistent effect on risk.
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

### Version 0: proposer (21 claims, 8 failing)
1. Revolving credit utilization is by far the most important driver of default risk, and risk rises sharply once utilization reaches about 0.72 of the credit limit.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
    - `threshold("utilization", at=0.719)`: **false**
2. The number of past delinquencies is the second or third most important driver, and having at least one delinquency raises default risk.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
    - `direction("n_delinquencies") == "increasing"`: ok
3. Income is also a moderate driver that lowers risk at higher levels, though it matters less than delinquencies.
    - `strength("income") == "moderate"`: **undecidable** (share band straddles a class edge)
    - `direction("income") == "decreasing"`: ok
    - `effect("n_delinquencies") > effect("income")`: **undecidable**
4. Length of credit history has at most a weak to moderate effect, with longer histories associated with lower risk, though the data do not settle its exact size or shape.
    - `strength("history_months") in ("weak", "moderate")`: **undecidable** (share band not settled against [2%, 15%))
    - `direction("history_months") == "decreasing"`: ok
    - `unsettled(strength("history_months") == "moderate")`: ok
5. Debt-to-income ratio, number of dependents, age, months at address and recent inquiries each have negligible effects on predicted default.
    - `negligible("dti")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("noise_2")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `negligible("n_inquiries")`: ok
6. The effect of utilization is larger when the applicant has more past delinquencies.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: **undecidable**
7. The data do not settle whether utilization and credit history length interact in a way that matters.
    - `unsettled(interaction("utilization", "history_months", pattern="none"))`: ok
8. Utilization and income do not interact in any practically meaningful way.
    - `interaction("utilization", "income", pattern="none")`: ok

### Version 1: reduced (2 claims, 0 failing, missing: utilization, n_delinquencies, income)
7. The data do not settle whether utilization and credit history length interact in a way that matters.
    - `unsettled(interaction("utilization", "history_months", pattern="none"))`: ok
8. Utilization and income do not interact in any practically meaningful way.
    - `interaction("utilization", "income", pattern="none")`: ok

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
1. Revolving credit utilization is the most important driver of default risk, and risk rises sharply once utilization passes about 72% of the credit limit.
2. Past delinquencies are the second most important driver, and having at least one delinquency raises the risk of default.
3. Income is a moderate effect, with higher incomes associated with lower risk of default.
4. Length of credit history has a weak effect, with longer histories associated with somewhat lower risk.
5. The effect of utilization is roughly the same at every level of income, so the two do not interact in a way the data can detect.
6. Debt-to-income ratio, applicant age, the two application attributes and recent credit inquiries hardly matter for the predictions, and the data do not settle whether debt-to-income has any effect at all.
7. The data do not settle whether the effect of past delinquencies grows or shrinks with credit history length.

### Version 1: reduced (0 claims, 0 failing, missing: utilization, n_delinquencies, income)
1. Revolving credit utilization is the most important driver of default risk, and risk rises sharply once utilization passes about 72% of the credit limit.
2. Past delinquencies are the second most important driver, and having at least one delinquency raises the risk of default.
3. Income is a moderate effect, with higher incomes associated with lower risk of default.
4. Length of credit history has a weak effect, with longer histories associated with somewhat lower risk.
5. The effect of utilization is roughly the same at every level of income, so the two do not interact in a way the data can detect.
6. Debt-to-income ratio, applicant age, the two application attributes and recent credit inquiries hardly matter for the predictions, and the data do not settle whether debt-to-income has any effect at all.
7. The data do not settle whether the effect of past delinquencies grows or shrinks with credit history length.

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

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (19 claims, 10 failing)
1. Revolving credit utilization is by far the most important driver of predicted default, accounting for about 37.5% of the model's importance, and risk rises sharply once utilization passes roughly 0.72 of the credit limit.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `share("utilization") == approx(0.375)`: **undecidable**
    - `unsettled(threshold("utilization", at=0.719))`: **false** (the claim is settled: it is false)
2. The number of past delinquencies is the second or third most important driver, and having any delinquency raises predicted risk compared with having none.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
3. Annual income has a moderate effect, with higher income associated with somewhat lower predicted risk, and it matters less than utilization or delinquencies.
    - `strength("income") == "moderate"`: **undecidable** (share band straddles a class edge)
    - `direction("income") == "decreasing"`: ok
    - `effect("utilization") > effect("n_delinquencies")`: ok
4. Utilization and delinquencies do not appear to interact in any practical sense, and the same holds for utilization and credit history length.
    - `interaction("utilization", "n_delinquencies", pattern="none")`: **undecidable**
    - `interaction("utilization", "history_months", pattern="none")`: **undecidable**
5. Length of credit history has at most a weak to moderate effect, with longer histories linked to slightly lower risk, but the data do not settle how this effect is shaped across its range.
    - `strength("history_months") in ("weak", "moderate")`: **undecidable** (share band not settled against [2%, 15%))
    - `unsettled(direction("history_months") == "decreasing")`: **false** (the claim is settled: it is true)
6. Debt-to-income ratio, number of dependents, age, months at address and recent credit inquiries have effects too small to be distinguished from zero at this sample size.
    - `negligible("dti")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("noise_2")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `negligible("n_inquiries")`: ok

### Version 1: template (14 claims, 0 failing)
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

## syn-none-n5000-s1_XGB2_H1_d4_claude-haiku-5-5_opaque

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (19 claims, 8 failing)
1. Revolving credit utilization is the most important driver of default risk, accounting for about 37% of the model's importance.
    - `rank("utilization") == 1`: ok
    - `share("utilization") == approx(0.375)`: **undecidable**
    - `direction("utilization") == "mostly_increasing"`: **undecidable** (no exception detected, and the bands do not rule a small one out (D29))
    - `threshold("utilization", at=0.719)`: **false**
2. Past delinquencies are the next strongest driver, and risk rises once an applicant has at least one delinquency.
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
    - `direction("n_delinquencies") == "increasing"`: ok
    - `rank("n_delinquencies") in (2, 3)`: ok
3. Annual income carries a moderate share of importance, and higher income is associated with lower risk.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
    - `rank("income") in (2, 3)`: ok
4. Utilization and past delinquencies appear to have no meaningful interaction, though the data do not settle whether the effect of utilization grows with the number of delinquencies.
    - `interaction("utilization", "n_delinquencies", pattern="none")`: **undecidable**
    - `unsettled(interaction("utilization", "n_delinquencies", pattern="amplification"))`: ok
5. Length of credit history has a weak to moderate effect, with longer histories linked to lower risk; the data do not settle whether this relationship is strictly decreasing.
    - `strength("history_months") in ("weak", "moderate")`: **undecidable** (share band not settled against [2%, 15%))
    - `direction("history_months") == "decreasing"`: ok
    - `unsettled(direction("history_months") == "decreasing")`: **false** (the claim is settled: it is true)
6. Debt-to-income ratio, age, recent credit inquiries and the two application attributes hardly matter for the model's predictions.
    - `negligible("dti")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("age")`: ok
    - `negligible("n_inquiries")`: ok
    - `negligible("noise_1 & noise_2")`: ok

### Version 1: reduced (3 claims, 0 failing, missing: utilization, n_delinquencies)
3. Annual income carries a moderate share of importance, and higher income is associated with lower risk.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
    - `rank("income") in (2, 3)`: ok

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

**TEMPLATE**: template text from the certified facts (1 calls, 0 repair rounds)

### Version 0: proposer (23 claims, 10 failing)
1. Revolving credit utilization is by far the most important driver of default risk, accounting for roughly 37% of the model's importance, and risk rises as utilization increases.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
    - `effect("utilization") > effect("n_delinquencies")`: ok
2. The jump is sharpest around a utilization of about 0.72, above which the predicted risk of default rises steeply compared with lower levels.
    - `threshold("utilization", at=0.719)`: **false**
3. Past delinquencies are the second most important driver, and having at least one delinquency raises predicted default risk relative to having none.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `strength("n_delinquencies") == "strong"`: **undecidable** (share band straddles a class edge)
4. Higher income is associated with somewhat lower predicted risk, although the effect is moderate and its exact size is less certain than that of utilization.
    - `strength("income") == "moderate"`: **undecidable** (share band straddles a class edge)
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a weak effect, with longer histories associated with slightly lower risk.
    - `strength("history_months") == "weak"`: **undecidable** (share band straddles a class edge)
    - `direction("history_months") == "decreasing"`: ok
6. The data do not settle whether debt-to-income ratio has any effect on default risk at this sample size.
    - `unsettled(strength("dti") == "weak")`: ok
    - `unsettled(direction("dti") == "increasing")`: ok
7. Age, months at address, number of dependents and recent credit inquiries hardly matter to the model's predictions.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `negligible("noise_2")`: **undecidable** (neither a detectable non-negligible effect nor a negligible one is shown)
    - `negligible("n_inquiries")`: ok
8. Utilization and past delinquencies appear to interact only weakly, since the rise in risk from utilization is similar whether or not an applicant has delinquencies.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: **undecidable**
    - `interaction("utilization", "n_delinquencies", pattern="sign_flip")`: **false**
    - `interaction("utilization", "n_delinquencies", pattern="none")`: **undecidable**
9. The data do not settle whether the effect of delinquencies grows with utilization, so that pairing should be treated with caution.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: **undecidable**
    - `interaction("utilization", "n_delinquencies", pattern="none")`: **undecidable**

### Version 1: reduced (6 claims, 0 failing, missing: income)
1. Revolving credit utilization is by far the most important driver of default risk, accounting for roughly 37% of the model's importance, and risk rises as utilization increases.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
    - `effect("utilization") > effect("n_delinquencies")`: ok
6. The data do not settle whether debt-to-income ratio has any effect on default risk at this sample size.
    - `unsettled(strength("dti") == "weak")`: ok
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
