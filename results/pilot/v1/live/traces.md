# Pilot traces: live

## syn-dominant-n50000-s1_EBM_H1_d0_claude-haiku-5-5_plausible

**RELEASED**: passed after 2 repair round(s) (3 calls, 2 repair rounds)

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

### Version 1: repair 1 (15 claims, 1 failing)
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
6. The debt-to-income ratio may have a weak effect, and risk may rise somewhat once the ratio passes about 0.44, but the data do not settle either point at this sample size.
    - `unsettled(strength("dti") == "weak")`: ok
    - `unsettled(direction("dti") == "increasing")`: **false** (the claim is settled: it is true)
7. Age, number of dependents and months at the current address hardly matter, since the data do not resolve any clear effect for them.
    - `negligible("age")`: ok
    - `negligible("noise_2")`: ok
    - `negligible("noise_1")`: ok
8. The data do not settle whether the effect of credit history reverses direction with recent credit inquiries, so we do not draw a conclusion about that interaction.
    - `unsettled(interaction("history_months", "n_inquiries", pattern="sign_flip"))`: ok

### Version 2: repair 2 (15 claims, 0 failing)
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
6. The debt-to-income ratio may have a weak effect, and risk rises somewhat once the ratio passes about 0.44, but the data do not settle how large that effect is at this sample size.
    - `unsettled(strength("dti") == "weak")`: ok
    - `direction("dti") == "increasing"`: ok
7. Age, number of dependents and months at the current address hardly matter, since the data do not resolve any clear effect for them.
    - `negligible("age")`: ok
    - `negligible("noise_2")`: ok
    - `negligible("noise_1")`: ok
8. The data do not settle whether the effect of credit history reverses direction with recent credit inquiries, so we do not draw a conclusion about that interaction.
    - `unsettled(interaction("history_months", "n_inquiries", pattern="sign_flip"))`: ok

## syn-dominant-n50000-s1_EBM_H2_d0_claude-haiku-5-5_plausible

**RELEASED**: passed after 1 repair round(s) (2 calls, 1 repair rounds)

### Version 0: proposer (0 claims, 0 failing, missing: utilization, n_delinquencies & utilization, n_delinquencies)

### Version 1: repair 1 (12 claims, 0 failing)
1. Credit utilization, the share of the credit limit in use, is the most important driver of default risk, accounting for about 28% of the model's importance, and risk rises strongly as utilization increases.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
    - `share("utilization") == approx(0.279)`: ok
2. The number of past delinquencies is the second most important driver, accounting for about 17% of importance, and risk jumps when an applicant has at least one past delinquency.
    - `rank("n_delinquencies") == 2`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `strength("n_delinquencies") == "strong"`: ok
    - `share("n_delinquencies") == approx(0.172)`: ok
    - `threshold("n_delinquencies", at=0.5)`: ok
3. The effect of credit utilization grows with the number of past delinquencies, and the pair together accounts for about 20% of the model's importance.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
    - `share("utilization & n_delinquencies") == approx(0.197)`: ok
    - `effect("utilization") > effect("n_delinquencies")`: ok
4. Income and the length of credit history have moderate effects, with risk falling as either rises.
5. The debt-to-income ratio has a weak to moderate effect, with risk rising as it increases.
6. Recent credit inquiries have at most a weak effect, while the number of dependents, months at the current address and age hardly matter.
7. The data do not settle whether the length of credit history and credit utilization interact.

## syn-dominant-n50000-s1_XGB2_H1_d0_claude-haiku-5-5_plausible

**RELEASED**: passed after 1 repair round(s) (2 calls, 1 repair rounds)

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

### Version 1: repair 1 (18 claims, 0 failing)
1. Revolving credit utilization is the most important driver of predicted default, and risk rises steeply as the share of the credit limit in use goes up, with the largest increases above roughly 0.76.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second most important driver, with a moderate to strong effect, and risk rises as delinquencies accumulate, though the step from one to two or more is the main change.
    - `rank("n_delinquencies") == 2`: ok
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
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
8. The number of recent credit inquiries has at most a weak effect, and risk rises slightly once an applicant has three or more recent inquiries.
    - `strength("n_inquiries") in ("negligible", "weak")`: ok
    - `direction("n_inquiries") == "increasing"`: ok

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

## syn-dominant-n50000-s1_XGB2_H2_d1_claude-haiku-5-5_plausible

**RELEASED**: passed after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (24 claims, 0 failing)
1. Revolving credit utilization is the most important driver of default risk, accounting for about 27% of the model's importance, and risk rises with it, steeply once utilization passes roughly 0.6 of the limit.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
    - `share("utilization") == approx(0.268)`: ok
2. Utilization matters much more for applicants with past delinquencies: its effect grows with the number of delinquencies.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
3. The number of past delinquencies is the second most important driver, with default risk jumping once an applicant has at least one delinquency and rising further at two or more.
    - `rank("n_delinquencies") == 2`: ok
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `threshold("n_delinquencies", at=1.0)`: ok
4. Income and length of credit history each have a moderate effect: default risk falls as income rises and as the credit history gets longer.
    - `rank("income") in (3, 4)`: ok
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
    - `rank("history_months") in (3, 4)`: ok
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok
5. The debt-to-income ratio has a weak to moderate effect, with risk increasing as the ratio rises, and it ranks fifth in importance.
    - `rank("dti") == 5`: ok
    - `strength("dti") in ("weak", "moderate")`: ok
    - `direction("dti") == "increasing"`: ok
6. Recent credit inquiries have at most a weak effect, with risk rising slightly as their number grows.
    - `strength("n_inquiries") in ("negligible", "weak")`: ok
    - `direction("n_inquiries") == "increasing"`: ok
7. Age and months at the current address hardly matter, and the number of dependents has at most a weak effect.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `strength("noise_2") in ("negligible", "weak")`: ok
8. The data do not settle whether credit history length and recent inquiries interact.
    - `unsettled(interaction("history_months", "n_inquiries", pattern="none"))`: ok

## syn-dominant-n50000-s1_XGB2_H2_d2_claude-haiku-5-5_plausible

**RELEASED**: passed after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (47 claims, 0 failing)
1. Credit utilization is the most important driver of default risk, accounting for about 27% of the model's importance, and risk rises steadily as the share of the credit limit in use grows.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
    - `share("utilization") == approx(0.268)`: ok
    - `effect("utilization") > effect("n_delinquencies")`: ok
2. The number of past delinquencies is the second most important driver, and risk jumps once an applicant has at least one delinquency.
    - `rank("n_delinquencies") == 2`: ok
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `threshold("n_delinquencies", at=1.0)`: ok
    - `effect("n_delinquencies") > effect("income")`: ok
3. The effect of credit utilization grows with the number of past delinquencies, so high utilization matters much more for applicants with several delinquencies, while utilization shows no practical interaction with income or credit history length.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
    - `interaction("utilization", "income", pattern="none")`: ok
    - `interaction("utilization", "history_months", pattern="none")`: ok
    - `interaction("n_delinquencies", "income", pattern="none")`: ok
    - `interaction("n_delinquencies", "history_months", pattern="none")`: ok
    - `interaction("income", "history_months", pattern="none")`: ok
    - `interaction("income", "dti", pattern="none")`: ok
    - `unsettled(interaction("history_months", "n_inquiries", pattern="none"))`: ok
    - `interaction("dti", "noise_2", pattern="none")`: ok
    - `interaction("noise_1", "noise_2", pattern="none")`: ok
4. Income has a moderate effect, and default risk decreases as income rises.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
    - `rank("income") in (3, 4)`: ok
    - `share("income") == approx(0.087)`: ok
5. The length of credit history also has a moderate effect, with risk decreasing as history gets longer, and it matters more than the debt-to-income ratio.
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok
    - `rank("history_months") in (3, 4)`: ok
    - `share("history_months") == approx(0.073)`: ok
    - `effect("history_months") > effect("dti")`: ok
6. The debt-to-income ratio is the fifth most important feature, with a weak to moderate effect in which risk increases with the ratio.
    - `strength("dti") in ("weak", "moderate")`: ok
    - `direction("dti") == "increasing"`: ok
    - `rank("dti") == 5`: ok
    - `share("dti") == approx(0.055)`: ok
    - `effect("dti") > effect("noise_2")`: ok
7. Recent credit inquiries have at most a weak effect, with risk increasing slightly as their number grows.
    - `strength("n_inquiries") in ("negligible", "weak")`: ok
    - `direction("n_inquiries") == "increasing"`: ok
    - `rank("n_inquiries") in (6, 7, 8)`: ok
    - `share("n_inquiries") == approx(0.018)`: ok
8. Age and months at the current address hardly matter, and the number of dependents has at most a weak effect.
    - `negligible("age")`: ok
    - `rank("age") in (8, 9)`: ok
    - `share("age") == approx(0.008)`: ok
    - `negligible("noise_1")`: ok
    - `rank("noise_1") in (6, 7, 8, 9)`: ok
    - `share("noise_1") == approx(0.017)`: ok
    - `strength("noise_2") in ("negligible", "weak")`: ok
    - `rank("noise_2") in (6, 7, 8)`: ok
    - `share("noise_2") == approx(0.023)`: ok

## syn-none-n5000-s1_EBM_H1_d0_claude-haiku-5-5_plausible

**RELEASED_REDUCED**: failing sentences dropped after 1 repair round(s) (2 calls, 1 repair rounds)

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

### Version 1: repair 1 (21 claims, 1 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises sharply as the share of the credit limit in use goes up, especially above roughly 0.7, though the data do not settle exactly how much of the model's importance it accounts for.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
    - `unsettled(share("utilization") == approx(0.376))`: ok
2. Past delinquencies are the second or third strongest driver, with a moderate to strong effect, and having at least one delinquency on file raises the predicted risk compared with having none.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
3. Annual income is the second or third strongest driver, with a moderate to strong effect, and risk falling as income rises, mostly through the drop between the lowest income band and the middle and upper bands.
    - `rank("income") in (2, 3)`: ok
    - `direction("income") == "decreasing"`: ok
    - `strength("income") in ("moderate", "strong")`: ok
4. Length of credit history has a weak to moderate effect, with longer histories associated with somewhat lower risk, though the data do not settle how large this effect is.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
    - `unsettled(strength("history_months") in ("weak", "moderate"))`: **false** (the claim is settled: it is true)
5. Debt-to-income ratio, number of dependents and months at address are each unsettled as to whether they matter at all at this sample size, while age and recent credit inquiries have a negligible effect in this model.
    - `unsettled(negligible("dti"))`: ok
    - `unsettled(negligible("noise_2"))`: ok
    - `unsettled(negligible("noise_1"))`: ok
    - `negligible("age")`: ok
    - `negligible("n_inquiries")`: ok
6. The interactions in the model are small, and the data do not settle whether utilization's effect depends on debt-to-income, so the main drivers can be read largely on their own.
    - `interaction("utilization", "history_months", pattern="none")`: ok
    - `interaction("income", "age", pattern="none")`: ok
    - `interaction("utilization", "dti", pattern="none")`: ok

### Version 2: reduced (18 claims, 0 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises sharply as the share of the credit limit in use goes up, especially above roughly 0.7, though the data do not settle exactly how much of the model's importance it accounts for.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
    - `unsettled(share("utilization") == approx(0.376))`: ok
2. Past delinquencies are the second or third strongest driver, with a moderate to strong effect, and having at least one delinquency on file raises the predicted risk compared with having none.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
3. Annual income is the second or third strongest driver, with a moderate to strong effect, and risk falling as income rises, mostly through the drop between the lowest income band and the middle and upper bands.
    - `rank("income") in (2, 3)`: ok
    - `direction("income") == "decreasing"`: ok
    - `strength("income") in ("moderate", "strong")`: ok
5. Debt-to-income ratio, number of dependents and months at address are each unsettled as to whether they matter at all at this sample size, while age and recent credit inquiries have a negligible effect in this model.
    - `unsettled(negligible("dti"))`: ok
    - `unsettled(negligible("noise_2"))`: ok
    - `unsettled(negligible("noise_1"))`: ok
    - `negligible("age")`: ok
    - `negligible("n_inquiries")`: ok
6. The interactions in the model are small, and the data do not settle whether utilization's effect depends on debt-to-income, so the main drivers can be read largely on their own.
    - `interaction("utilization", "history_months", pattern="none")`: ok
    - `interaction("income", "age", pattern="none")`: ok
    - `interaction("utilization", "dti", pattern="none")`: ok

## syn-none-n5000-s1_EBM_H2_d0_claude-haiku-5-5_plausible

**RELEASED**: passed after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (29 claims, 0 failing)
1. Credit utilization is the most important driver of default risk, and its effect is strong: risk rises as the share of the credit limit in use goes up, with the largest jump for applicants using about three-quarters of their limit or more.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second or third most important driver, with a moderate to strong effect; having any delinquency on file raises the risk of default, and the data indicate a sharp step between zero and one or more.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `threshold("n_delinquencies", at=0.5)`: ok
3. Income is also among the top three drivers, with a moderate to strong effect that lowers the risk of default as income rises, mainly between the lowest incomes and mid-range incomes.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
    - `rank("income") in (2, 3)`: ok
4. Length of credit history has a weak to moderate effect, lowering default risk as history gets longer, and it matters less than income.
    - `effect("income") > effect("history_months")`: ok
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
    - `rank("history_months") in (4, 5, 6)`: ok
5. Credit utilization does not meaningfully interact with either length of credit history or debt-to-income ratio, so their effects on risk can be read separately.
    - `interaction("utilization", "history_months", pattern="none")`: ok
    - `interaction("utilization", "dti", pattern="none")`: ok
6. The debt-to-income ratio and the number of dependents have at most a moderate effect, and the data do not settle whether either changes risk in a consistent direction.
    - `strength("dti") in ("negligible", "weak", "moderate")`: ok
    - `rank("dti") in (4, 5, 6, 7, 8)`: ok
    - `strength("noise_2") in ("negligible", "weak", "moderate")`: ok
    - `rank("noise_2") in (4, 5, 6, 7, 8)`: ok
7. Months at the current address has at most a moderate effect, and age hardly matters for default risk.
    - `strength("noise_1") in ("negligible", "weak", "moderate")`: ok
    - `rank("noise_1") in (5, 6, 7, 8, 9)`: ok
    - `negligible("age")`: ok
    - `rank("age") in (5, 6, 7, 8, 9)`: ok
8. The number of recent credit inquiries hardly matters, and income, age, number of dependents and months at address show no meaningful interactions with one another.
    - `negligible("n_inquiries")`: ok
    - `rank("n_inquiries") in (7, 8, 9)`: ok
    - `interaction("income", "age", pattern="none")`: ok
    - `interaction("income", "noise_2", pattern="none")`: ok
    - `interaction("noise_1", "noise_2", pattern="none")`: ok

## syn-none-n5000-s1_XGB2_H1_d0_claude-haiku-5-5_plausible

**RELEASED_REDUCED**: failing sentences dropped after 2 repair round(s) (3 calls, 2 repair rounds)

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

### Version 1: repair 1 (17 claims, 1 failing)
1. Revolving credit utilization is by far the most important driver of predicted default, accounting for roughly 37% of the model's importance, and predicted risk rises as utilization increases.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The effect is concentrated at high utilization: risk stays roughly flat at low levels, rises modestly around 0.64 to 0.72, and the largest single jump occurs near 0.735, within a band of roughly 0.67 to 0.83.
    - `threshold("utilization", at=0.735)`: **false**
3. Past delinquencies are the second most important driver, and having any delinquency raises predicted default risk compared with having none; the data do not settle whether this effect is strong.
    - `unsettled(strength("n_delinquencies") == "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
4. Higher income is associated with lower predicted risk, though its effect is smaller than that of utilization or delinquencies.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history is associated with somewhat lower risk for longer histories, though the data do not settle whether its effect is weak, and the shape of this relationship between the extremes is not resolved by the data.
    - `unsettled(strength("history_months") == "weak")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The data do not settle whether the effect of utilization changes with the number of past delinquencies, so the two may act largely independently or interact.
    - `unsettled(interaction("utilization", "n_delinquencies", pattern="none"))`: ok
7. The data do not settle whether debt-to-income ratio has any real effect on predicted risk, since its estimated contribution is small and uncertain.
    - `unsettled(strength("dti") in ("negligible", "weak"))`: ok
8. Number of dependents, age, months at current address and recent credit inquiries each have a negligible effect on the model's predictions, though the data do not settle this for number of dependents.
    - `unsettled(negligible("noise_2"))`: ok
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `negligible("n_inquiries")`: ok
9. The data do not settle whether the effect of utilization grows with credit history length.
    - `unsettled(interaction("utilization", "history_months", pattern="amplification"))`: ok

### Version 2: repair 2 (17 claims, 1 failing)
1. Revolving credit utilization is by far the most important driver of predicted default, accounting for roughly 37% of the model's importance, and predicted risk rises as utilization increases.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The effect is concentrated at high utilization: risk stays roughly flat at low levels, rises modestly around 0.64 to 0.72, and then climbs further at higher values, though the data do not settle where exactly the steepest change occurs.
    - `unsettled(threshold("utilization", at=0.735))`: **false** (the claim is settled: it is false)
3. Past delinquencies are the second most important driver, and having any delinquency raises predicted default risk compared with having none; the data do not settle whether this effect is strong.
    - `unsettled(strength("n_delinquencies") == "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
4. Higher income is associated with lower predicted risk, though its effect is smaller than that of utilization or delinquencies.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history is associated with somewhat lower risk for longer histories, though the data do not settle whether its effect is weak, and the shape of this relationship between the extremes is not resolved by the data.
    - `unsettled(strength("history_months") == "weak")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The data do not settle whether the effect of utilization changes with the number of past delinquencies, so the two may act largely independently or interact.
    - `unsettled(interaction("utilization", "n_delinquencies", pattern="none"))`: ok
7. The data do not settle whether debt-to-income ratio has any real effect on predicted risk, since its estimated contribution is small and uncertain.
    - `unsettled(strength("dti") in ("negligible", "weak"))`: ok
8. Number of dependents, age, months at current address and recent credit inquiries each have a negligible effect on the model's predictions, though the data do not settle this for number of dependents.
    - `unsettled(negligible("noise_2"))`: ok
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `negligible("n_inquiries")`: ok
9. The data do not settle whether the effect of utilization grows with credit history length.
    - `unsettled(interaction("utilization", "history_months", pattern="amplification"))`: ok

### Version 3: reduced (16 claims, 0 failing)
1. Revolving credit utilization is by far the most important driver of predicted default, accounting for roughly 37% of the model's importance, and predicted risk rises as utilization increases.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
3. Past delinquencies are the second most important driver, and having any delinquency raises predicted default risk compared with having none; the data do not settle whether this effect is strong.
    - `unsettled(strength("n_delinquencies") == "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
4. Higher income is associated with lower predicted risk, though its effect is smaller than that of utilization or delinquencies.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history is associated with somewhat lower risk for longer histories, though the data do not settle whether its effect is weak, and the shape of this relationship between the extremes is not resolved by the data.
    - `unsettled(strength("history_months") == "weak")`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The data do not settle whether the effect of utilization changes with the number of past delinquencies, so the two may act largely independently or interact.
    - `unsettled(interaction("utilization", "n_delinquencies", pattern="none"))`: ok
7. The data do not settle whether debt-to-income ratio has any real effect on predicted risk, since its estimated contribution is small and uncertain.
    - `unsettled(strength("dti") in ("negligible", "weak"))`: ok
8. Number of dependents, age, months at current address and recent credit inquiries each have a negligible effect on the model's predictions, though the data do not settle this for number of dependents.
    - `unsettled(negligible("noise_2"))`: ok
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `negligible("n_inquiries")`: ok
9. The data do not settle whether the effect of utilization grows with credit history length.
    - `unsettled(interaction("utilization", "history_months", pattern="amplification"))`: ok

## syn-none-n5000-s1_XGB2_H2_d0_claude-haiku-5-5_plausible

**RELEASED**: passed after 0 repair round(s) (1 calls, 0 repair rounds)

### Version 0: proposer (22 claims, 0 failing)
1. Credit utilization is the most important driver of default risk, with a strong effect: risk increases as the share of the credit limit in use rises, and the rise is concentrated above about 0.72.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second or third most important driver, with a moderate to strong effect, and risk jumps once an applicant has at least one delinquency.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `threshold("n_delinquencies", at=1.0)`: ok
3. Credit utilization matters more than the number of past delinquencies.
    - `effect("utilization") > effect("n_delinquencies")`: ok
4. Income is also among the top three drivers, with a moderate to strong effect: risk decreases as income rises, and income matters more than the length of credit history.
    - `rank("income") in (2, 3)`: ok
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
    - `effect("income") > effect("history_months")`: ok
5. The data do not settle whether credit utilization and the number of past delinquencies interact, although the effect of delinquencies appears somewhat larger at high utilization.
    - `unsettled(interaction("utilization", "n_delinquencies", pattern="none"))`: ok
6. The length of credit history has at most a moderate effect, with risk decreasing as history gets longer, and it ranks roughly fourth to sixth in importance.
    - `strength("history_months") in ("negligible", "weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
    - `rank("history_months") in (4, 5, 6)`: ok
7. The debt-to-income ratio has at most a moderate effect on default risk and ranks fourth to eighth, with no clear movement resolved at this sample size.
    - `strength("dti") in ("negligible", "weak", "moderate")`: ok
    - `rank("dti") in (4, 5, 6, 7, 8)`: ok
8. Recent credit inquiries, age, months at the current address and the number of dependents hardly matter for default risk.
    - `negligible("n_inquiries")`: ok
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `strength("noise_2") in ("negligible", "weak", "moderate")`: ok
