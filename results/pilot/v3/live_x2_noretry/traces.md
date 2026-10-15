# Pilot traces: live

## syn-dominant-n50000-s1_EBM_H1_d0_claude-haiku-5-5_plausible

**RELEASED**: passed after 1 repair round(s) (6 calls, 1 repair rounds)

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
Round trip (3 readings):
    - sentence 2 also states `threshold("n_delinquencies", at=1.0)`: ok
    - sentence 3 also states `strength("n_delinquencies & utilization") == "strong"`: ok
    - flag, plan claim not in the text: sentence 2 `share("n_delinquencies") == approx(0.17)`
    - flag, no DSL form: sentence 1: risk rises steeply as utilization goes up; risk rises steeply
    - flag, no DSL form: sentence 3: high utilization combined with past delinquencies carries the greatest risk

## syn-dominant-n50000-s1_EBM_H2_d0_claude-haiku-5-5_plausible

**RELEASED**: passed after 1 repair round(s) (8 calls, 1 repair rounds)

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
Round trip (3 readings):
    - sentence 1 also states `share("utilization") == approx(0.28)`: ok
    - sentence 2 also states `share("n_delinquencies") == approx(0.17)`: ok
    - sentence 2 also states `threshold("n_delinquencies", at=1.0)`: ok
    - sentence 5 also states `share("dti") == approx(0.05)`: ok
    - sentence 7 also states `unsettled(interaction("utilization", "history_months", pattern="amplification"))`: **false** (the claim is settled: it is false)
    - flag, plan claim not in the text: sentence 1 `strength("utilization") == "strong"`
    - flag, plan claim not in the text: sentence 1 `share("utilization") == approx(0.279)`
    - flag, plan claim not in the text: sentence 2 `strength("n_delinquencies") == "strong"`
    - flag, plan claim not in the text: sentence 2 `share("n_delinquencies") == approx(0.172)`
    - flag, plan claim not in the text: sentence 2 `threshold("n_delinquencies", at=0.5)`
    - flag, plan claim not in the text: sentence 4 `rank("income") in (3, 4)`
    - flag, plan claim not in the text: sentence 4 `rank("history_months") in (3, 4)`
    - flag, plan claim not in the text: sentence 5 `rank("dti") == 5`
    - flag, plan claim not in the text: sentence 7 `interaction("n_delinquencies", "income", pattern="none")`
    - flag, one reading only: sentence 7 `unsettled(interaction("utilization", "history_months", pattern="sign_flip"))`

### Version 1: repair 1 (25 claims, 0 failing)
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
7. Credit utilization and credit history length do not interact: the effect of utilization is essentially the same whether an applicant's credit history is short or long, and the interaction accounts for a negligible share of the model's importance.
    - `interaction("utilization", "history_months", pattern="none")`: ok
    - `interaction("n_delinquencies", "income", pattern="none")`: ok
Round trip (3 readings):
    - sentence 1 also states `share("utilization") == approx(0.28)`: ok
    - sentence 2 also states `share("n_delinquencies") == approx(0.17)`: ok
    - sentence 2 also states `threshold("n_delinquencies", at=1.0)`: ok
    - sentence 5 also states `share("dti") == approx(0.05)`: ok
    - sentence 7 also states `negligible("history_months & utilization")`: ok
    - flag, plan claim not in the text: sentence 1 `strength("utilization") == "strong"`
    - flag, plan claim not in the text: sentence 1 `share("utilization") == approx(0.279)`
    - flag, plan claim not in the text: sentence 2 `strength("n_delinquencies") == "strong"`
    - flag, plan claim not in the text: sentence 2 `share("n_delinquencies") == approx(0.172)`
    - flag, plan claim not in the text: sentence 2 `threshold("n_delinquencies", at=0.5)`
    - flag, plan claim not in the text: sentence 4 `rank("income") in (3, 4)`
    - flag, plan claim not in the text: sentence 4 `rank("history_months") in (3, 4)`
    - flag, plan claim not in the text: sentence 5 `rank("dti") == 5`
    - flag, plan claim not in the text: sentence 7 `interaction("n_delinquencies", "income", pattern="none")`
    - flag, no DSL form: sentence 3: utilization matters far more for applicants with delinquencies than for those with none, as a comparison of the two groups; utilization matters far more for applicants with past delinquencies than for those with none
    - flag, no DSL form: sentence 7: the effect of utilization is essentially the same whether credit history is short or long

## syn-dominant-n50000-s1_XGB2_H1_d0_claude-haiku-5-5_plausible

**RELEASED**: passed after 1 repair round(s) (5 calls, 1 repair rounds)

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
7. The number of dependents has at most a weak effect on predicted default, and the facts show no clear movement in its effect.
    - `strength("noise_2") in ("negligible", "weak")`: ok
8. Age and months at the current address hardly matter for the predictions.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
Round trip (3 readings):
    - sentence 7 also states `unsettled(direction("noise_2") == "decreasing")`: ok
    - sentence 7 also states `unsettled(direction("noise_2") == "increasing")`: ok
    - flag, plan claim not in the text: sentence 1 `strength("utilization") == "strong"`
    - flag, no DSL form: sentence 2: the rise is mainly from none to one or two delinquencies
    - flag, no DSL form: sentence 7: the facts show no clear movement in the effect of dependents; the facts show no clear movement in the effect of the number of dependents

## syn-dominant-n50000-s1_XGB2_H2_d0_claude-haiku-5-5_plausible

**RELEASED**: passed after 0 repair round(s) (4 calls, 0 repair rounds)

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
Round trip (3 readings):
    - sentence 1 also states `share("utilization") == approx(0.27)`: ok
    - flag, plan claim not in the text: sentence 1 `strength("utilization") == "strong"`
    - flag, plan claim not in the text: sentence 1 `share("utilization") == approx(0.268)`
    - flag, plan claim not in the text: sentence 2 `direction("n_delinquencies") == "increasing"`
    - flag, plan claim not in the text: sentence 3 `effect("utilization") > effect("n_delinquencies")`
    - flag, plan claim not in the text: sentence 4 `share("income") == approx(0.087)`
    - flag, plan claim not in the text: sentence 5 `share("history_months") == approx(0.073)`
    - flag, plan claim not in the text: sentence 6 `share("dti") == approx(0.055)`
    - flag, plan claim not in the text: sentence 7 `rank("age") in (8, 9)`
    - flag, plan claim not in the text: sentence 8 `rank("n_inquiries") in (6, 7, 8)`
    - flag, plan claim not in the text: sentence 11 `interaction("income", "history_months", pattern="none")`
    - flag, plan claim not in the text: sentence 11 `interaction("income", "dti", pattern="none")`
    - flag, plan claim not in the text: sentence 11 `interaction("dti", "noise_2", pattern="none")`
    - flag, plan claim not in the text: sentence 11 `interaction("noise_1", "noise_2", pattern="none")`

## syn-dominant-n50000-s1_XGB2_H2_d0_claude-sonnet-5-5_plausible

**RELEASED**: passed after 0 repair round(s) (4 calls, 0 repair rounds)

### Version 0: proposer (23 claims, 0 failing)
1. Credit utilization is the most important driver of default risk, accounting for about 27% of the model's importance, and it has a strong effect: risk increases with the share of the credit limit in use.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
    - `share("utilization") == approx(0.268)`: ok
2. The number of past delinquencies is the second most important feature, with a moderate to strong effect, and risk increases with it.
    - `rank("n_delinquencies") == 2`: ok
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
3. These two drivers interact: the effect of credit utilization grows with the number of past delinquencies.
    - `interaction("utilization", "n_delinquencies", pattern="amplification")`: ok
4. Income and the length of credit history each have a moderate effect and rank third or fourth, and in both cases risk decreases as the value goes up.
    - `strength("income") == "moderate"`: ok
    - `direction("income") == "decreasing"`: ok
    - `rank("income") in (3, 4)`: ok
    - `strength("history_months") == "moderate"`: ok
    - `direction("history_months") == "decreasing"`: ok
    - `rank("history_months") in (3, 4)`: ok
5. The debt-to-income ratio is the fifth most important feature, with a weak to moderate effect, and risk increases with it.
    - `strength("dti") in ("weak", "moderate")`: ok
    - `direction("dti") == "increasing"`: ok
    - `rank("dti") == 5`: ok
6. The number of recent inquiries and the number of dependents have at most a weak effect on default risk.
    - `strength("n_inquiries") in ("negligible", "weak")`: ok
    - `strength("noise_2") in ("negligible", "weak")`: ok
7. Age and months at the current address hardly matter.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
8. Credit utilization and income do not interact, while the data do not settle whether the length of credit history and the number of recent inquiries interact.
    - `unsettled(interaction("history_months", "n_inquiries", pattern="none"))`: ok
    - `interaction("utilization", "income", pattern="none")`: ok
Round trip (3 readings):
    - sentence 1 also states `share("utilization") == approx(0.27)`: ok
    - flag, plan claim not in the text: sentence 1 `share("utilization") == approx(0.268)`

## syn-dominant-n50000-s1_XGB2_H2_d1_claude-haiku-5-5_plausible

**RELEASED**: passed after 2 repair round(s) (9 calls, 2 repair rounds)

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
Round trip (3 readings):
    - sentence 1 also states `peak("utilization", at=1.0)`: **false**
    - sentence 1 also states `share("utilization") == approx(0.27)`: ok
    - sentence 6 also states `unsettled(interaction("history_months", "n_inquiries", pattern="amplification"))`: ok
    - sentence 7 also states `interaction("utilization", "history_months", pattern="none")`: ok
    - sentence 7 also states `interaction("utilization", "income", pattern="none")`: ok
    - flag, plan claim not in the text: sentence 1 `share("utilization") == approx(0.268)`
    - flag, plan claim not in the text: sentence 1 `strength("utilization") == "strong"`
    - flag, plan claim not in the text: sentence 2 `direction("n_delinquencies") == "increasing"`
    - flag, plan claim not in the text: sentence 6 `rank("n_inquiries") in (6, 7, 8)`
    - flag, plan claim not in the text: sentence 6 `unsettled(interaction("history_months", "n_inquiries", pattern="none"))`
    - flag, no DSL form: sentence 1: risk rises steadily as utilization increases; the strongest effect at the highest levels; the strongest effect at the highest levels is an edge maximum rather than an interior peak

### Version 2: repair 2 (24 claims, 0 failing)
1. Credit utilization is by far the most important driver of default risk, accounting for about 27% of the model's importance, and risk generally increases as utilization rises, with the largest steps at the highest levels.
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
Round trip (3 readings):
    - sentence 1 also states `direction("utilization") in ("increasing", "mostly_increasing")`: ok
    - sentence 1 also states `share("utilization") == approx(0.27)`: ok
    - sentence 6 also states `unsettled(interaction("history_months", "n_inquiries", pattern="amplification"))`: ok
    - sentence 7 also states `interaction("utilization", "history_months", pattern="none")`: ok
    - sentence 7 also states `interaction("utilization", "income", pattern="none")`: ok
    - flag, plan claim not in the text: sentence 1 `share("utilization") == approx(0.268)`
    - flag, plan claim not in the text: sentence 1 `direction("utilization") == "increasing"`
    - flag, plan claim not in the text: sentence 1 `strength("utilization") == "strong"`
    - flag, plan claim not in the text: sentence 2 `direction("n_delinquencies") == "increasing"`
    - flag, plan claim not in the text: sentence 6 `rank("n_inquiries") in (6, 7, 8)`
    - flag, plan claim not in the text: sentence 6 `unsettled(interaction("history_months", "n_inquiries", pattern="none"))`
    - flag, one reading only: sentence 6 `unsettled(interaction("history_months", "n_inquiries", pattern="none"))`
    - flag, no DSL form: sentence 1: the largest steps occur at the highest utilization levels

## syn-dominant-n50000-s1_XGB2_H2_d2_claude-haiku-5-5_plausible

**RELEASED**: passed after 0 repair round(s) (4 calls, 0 repair rounds)

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
Round trip (3 readings):
    - sentence 1 also states `direction("utilization") in ("increasing", "mostly_increasing")`: ok
    - sentence 1 also states `share("utilization") == approx(0.27)`: ok
    - flag, plan claim not in the text: sentence 1 `direction("utilization") == "increasing"`
    - flag, plan claim not in the text: sentence 1 `strength("utilization") == "strong"`
    - flag, plan claim not in the text: sentence 1 `share("utilization") == approx(0.268)`
    - flag, plan claim not in the text: sentence 2 `direction("n_delinquencies") == "increasing"`
    - flag, plan claim not in the text: sentence 3 `effect("utilization") > effect("n_delinquencies")`
    - flag, plan claim not in the text: sentence 4 `rank("income") in (3, 4)`
    - flag, plan claim not in the text: sentence 4 `rank("history_months") in (3, 4)`
    - flag, plan claim not in the text: sentence 4 `effect("n_delinquencies") > effect("income")`
    - flag, plan claim not in the text: sentence 5 `effect("history_months") > effect("dti")`
    - flag, plan claim not in the text: sentence 5 `rank("dti") == 5`
    - flag, plan claim not in the text: sentence 7 `unsettled(interaction("history_months", "n_inquiries", pattern="none"))`
    - flag, one reading only: sentence 7 `unsettled(interaction("history_months", "n_inquiries", pattern="amplification"))`
    - flag, one reading only: sentence 7 `unsettled(interaction("history_months", "n_inquiries", pattern="none"))`

## syn-none-n5000-s1_EBM_H1_d0_claude-haiku-5-5_plausible

**RELEASED**: passed after 2 repair round(s) (9 calls, 2 repair rounds)

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

### Version 1: repair 1 (15 claims, 0 failing)
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
    - `strength("income") in ("moderate", "strong")`: ok
4. Length of credit history has a weak to moderate effect, and longer histories lower the predicted risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
5. The model shows no clear interaction between utilization and credit history length.
    - `interaction("utilization", "history_months", pattern="none")`: ok
6. The data do not settle whether debt-to-income ratio has any effect on default risk at this sample size.
    - `unsettled(strength("dti") == "weak")`: ok
7. Annual income and applicant age do not interact in the model, so the effect of income is the same across ages.
    - `negligible("n_inquiries")`: ok
    - `interaction("income", "age", pattern="none")`: ok
Round trip (3 readings):
    - sentence 3 also states `threshold("income", at=84000.0)`: **false**
    - flag, plan claim not in the text: sentence 1 `strength("utilization") == "strong"`
    - flag, plan claim not in the text: sentence 3 `strength("income") in ("moderate", "strong")`
    - flag, plan claim not in the text: sentence 6 `unsettled(strength("dti") == "weak")`
    - flag, plan claim not in the text: sentence 7 `negligible("n_inquiries")`

### Version 2: repair 2 (15 claims, 0 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk rises as the share of the credit limit in use goes up.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
    - `strength("utilization") == "strong"`: ok
2. The number of past delinquencies is the second or third most important driver, and having at least one delinquency raises the predicted risk compared with having none.
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `threshold("n_delinquencies", at=1.0)`: ok
3. Annual income is the second or third most important driver, and higher income gradually lowers the predicted risk across the range of incomes.
    - `rank("income") in (2, 3)`: ok
    - `direction("income") == "decreasing"`: ok
    - `strength("income") in ("moderate", "strong")`: ok
4. Length of credit history has a weak to moderate effect, and longer histories lower the predicted risk.
    - `strength("history_months") in ("weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
5. The model shows no clear interaction between utilization and credit history length.
    - `interaction("utilization", "history_months", pattern="none")`: ok
6. The data do not settle whether debt-to-income ratio has any effect on default risk at this sample size.
    - `unsettled(strength("dti") == "weak")`: ok
7. Annual income and applicant age do not interact in the model, so the effect of income is the same across ages.
    - `negligible("n_inquiries")`: ok
    - `interaction("income", "age", pattern="none")`: ok
Round trip (3 readings):
    - flag, plan claim not in the text: sentence 1 `strength("utilization") == "strong"`
    - flag, plan claim not in the text: sentence 2 `direction("n_delinquencies") == "increasing"`
    - flag, plan claim not in the text: sentence 3 `strength("income") in ("moderate", "strong")`
    - flag, plan claim not in the text: sentence 6 `unsettled(strength("dti") == "weak")`
    - flag, plan claim not in the text: sentence 7 `negligible("n_inquiries")`
    - flag, one reading only: sentence 6 `unsettled(strength("dti") == "moderate")`
    - flag, one reading only: sentence 6 `unsettled(strength("dti") == "weak")`
    - flag, no DSL form: sentence 3: the decrease is gradual across the range of incomes; the decrease in predicted risk is gradual across the range of incomes

## syn-none-n5000-s1_EBM_H2_d0_claude-haiku-5-5_plausible

**RELEASED**: passed after 0 repair round(s) (4 calls, 0 repair rounds)

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
Round trip (3 readings):
    - sentence 2 also states `threshold("n_delinquencies", at=1.0)`: ok
    - flag, plan claim not in the text: sentence 2 `direction("n_delinquencies") == "increasing"`
    - flag, plan claim not in the text: sentence 2 `threshold("n_delinquencies", at=0.5)`
    - flag, plan claim not in the text: sentence 3 `rank("income") in (2, 3)`
    - flag, one reading only: sentence 3 `rank("income") == 2`
    - flag, one reading only: sentence 3 `rank("income") in (1, 2)`
    - flag, one reading only: sentence 3 `rank("income") in (1, 2, 3)`
    - flag, no DSL form: sentence 6: the two act largely separately

## syn-none-n5000-s1_XGB2_H1_d0_claude-haiku-5-5_plausible

**TEMPLATE**: template text from the certified facts (9 calls, 2 repair rounds)

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
2. Its effect is concentrated at high levels: risk rises steeply once utilization gets high, though the data do not confirm a single sharp step.
    - `direction("utilization") == "increasing"`: ok
3. Past delinquencies are the second or third most important driver, and having any delinquency raises the risk of default compared with having none.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
4. Annual income is also among the leading drivers, with higher income generally lowering the risk of default.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a weak to moderate effect, with longer histories generally associated with lower risk.
    - `unsettled(strength("history_months") in ("negligible", "weak"))`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The data do not settle whether the effect of utilization grows with the number of past delinquencies.
    - `unsettled(interaction("utilization", "n_delinquencies", pattern="amplification"))`: ok
7. The data do not settle whether the effect of utilization depends on credit history length.
    - `unsettled(interaction("utilization", "history_months", pattern="amplification"))`: ok
8. The data do not settle whether debt-to-income ratio matters for predicted default risk.
    - `unsettled(negligible("dti"))`: ok
9. The data do not settle whether age matters, and number of dependents likewise cannot be confirmed as negligible; months at address and recent credit inquiries have no detectable effect on predicted default risk.
    - `unsettled(negligible("noise_2"))`: ok
    - `unsettled(negligible("age"))`: **false** (the claim is settled: it is true)
    - `negligible("noise_1")`: ok
    - `negligible("n_inquiries")`: ok

### Version 2: repair 2 (16 claims, 0 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk generally increases as the share of the credit limit in use rises.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. Its effect is concentrated at high levels: risk rises steeply once utilization gets high, though the data do not confirm a single sharp step.
    - `direction("utilization") == "increasing"`: ok
3. Past delinquencies are the second or third most important driver, and having any delinquency raises the risk of default compared with having none.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
4. Annual income is also among the leading drivers, with higher income generally lowering the risk of default.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
5. Length of credit history has a weak to moderate effect, with longer histories generally associated with lower risk.
    - `unsettled(strength("history_months") in ("negligible", "weak"))`: ok
    - `direction("history_months") == "decreasing"`: ok
6. The data do not settle whether the effect of utilization grows with the number of past delinquencies.
    - `unsettled(interaction("utilization", "n_delinquencies", pattern="amplification"))`: ok
7. The data do not settle whether the effect of utilization depends on credit history length.
    - `unsettled(interaction("utilization", "history_months", pattern="amplification"))`: ok
8. The data do not settle whether debt-to-income ratio matters for predicted default risk.
    - `unsettled(negligible("dti"))`: ok
9. Age has no detectable effect, and months at address and recent credit inquiries likewise have no detectable effect on predicted default risk; the data do not settle whether number of dependents matters.
    - `unsettled(negligible("noise_2"))`: ok
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `negligible("n_inquiries")`: ok
Round trip (3 readings):
    - sentence 1 also states `direction("utilization") in ("increasing", "mostly_increasing")`: ok
    - sentence 3 also states `rank("n_delinquencies") in (2, 3)`: ok
    - sentence 4 also states `direction("income") in ("decreasing", "mostly_decreasing")`: ok
    - sentence 5 also states `direction("history_months") in ("decreasing", "mostly_decreasing")`: ok
    - sentence 5 also states `strength("history_months") in ("weak", "moderate")`: **undecidable** (share band not settled against [2%, 15%))
    - sentence 7 also states `unsettled(interaction("utilization", "history_months", pattern="none"))`: ok
    - flag, plan claim not in the text: sentence 1 `direction("utilization") == "increasing"`
    - flag, plan claim not in the text: sentence 3 `strength("n_delinquencies") in ("moderate", "strong")`
    - flag, plan claim not in the text: sentence 4 `strength("income") in ("moderate", "strong")`
    - flag, plan claim not in the text: sentence 4 `direction("income") == "decreasing"`
    - flag, plan claim not in the text: sentence 5 `unsettled(strength("history_months") in ("negligible", "weak"))`
    - flag, plan claim not in the text: sentence 5 `direction("history_months") == "decreasing"`
    - flag, plan claim not in the text: sentence 7 `unsettled(interaction("utilization", "history_months", pattern="amplification"))`
    - flag, plan claim not in the text: sentence 8 `unsettled(negligible("dti"))`
    - flag, plan claim not in the text: sentence 9 `unsettled(negligible("noise_2"))`
    - flag, one reading only: sentence 3 `direction("n_delinquencies") in ("increasing", "mostly_increasing")`
    - flag, one reading only: sentence 4 `rank("income") in (1, 2, 3)`
    - flag, one reading only: sentence 4 `strength("income") in ("moderate", "strong")`
    - flag, one reading only: sentence 4 `strength("income") in ("weak", "moderate", "strong")`
    - flag, one reading only: sentence 8 `unsettled(negligible("dti"))`
    - flag, one reading only: sentence 9 `unsettled(negligible("noise_2"))`
    - flag, no DSL form: sentence 2: risk rises steeply once utilization gets high; the data do not confirm a single sharp step
    - flag, no DSL form: sentence 3: any delinquency raises risk compared with none; having any delinquency raises risk compared with none

### Version 3: reduced (14 claims, 0 failing)
1. Revolving credit utilization is the most important driver of default risk, and risk generally increases as the share of the credit limit in use rises.
    - `rank("utilization") == 1`: ok
    - `direction("utilization") == "increasing"`: ok
2. Its effect is concentrated at high levels: risk rises steeply once utilization gets high, though the data do not confirm a single sharp step.
    - `direction("utilization") == "increasing"`: ok
3. Past delinquencies are the second or third most important driver, and having any delinquency raises the risk of default compared with having none.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
4. Annual income is also among the leading drivers, with higher income generally lowering the risk of default.
    - `strength("income") in ("moderate", "strong")`: ok
    - `direction("income") == "decreasing"`: ok
6. The data do not settle whether the effect of utilization grows with the number of past delinquencies.
    - `unsettled(interaction("utilization", "n_delinquencies", pattern="amplification"))`: ok
7. The data do not settle whether the effect of utilization depends on credit history length.
    - `unsettled(interaction("utilization", "history_months", pattern="amplification"))`: ok
8. The data do not settle whether debt-to-income ratio matters for predicted default risk.
    - `unsettled(negligible("dti"))`: ok
9. Age has no detectable effect, and months at address and recent credit inquiries likewise have no detectable effect on predicted default risk; the data do not settle whether number of dependents matters.
    - `unsettled(negligible("noise_2"))`: ok
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `negligible("n_inquiries")`: ok
Round trip (3 readings):
    - **not covered by the text**: utilization
    - **not covered by the text**: n_delinquencies
    - **not covered by the text**: income
    - flag, plan claim not in the text: sentence 1 `rank("utilization") == 1`
    - flag, plan claim not in the text: sentence 1 `direction("utilization") == "increasing"`
    - flag, plan claim not in the text: sentence 3 `strength("n_delinquencies") in ("moderate", "strong")`
    - flag, plan claim not in the text: sentence 3 `direction("n_delinquencies") == "increasing"`
    - flag, plan claim not in the text: sentence 4 `strength("income") in ("moderate", "strong")`
    - flag, plan claim not in the text: sentence 4 `direction("income") == "decreasing"`
    - flag, plan claim not in the text: sentence 6 `unsettled(interaction("utilization", "n_delinquencies", pattern="amplification"))`
    - flag, plan claim not in the text: sentence 7 `unsettled(interaction("utilization", "history_months", pattern="amplification"))`
    - flag, plan claim not in the text: sentence 8 `unsettled(negligible("dti"))`
    - flag, plan claim not in the text: sentence 9 `unsettled(negligible("noise_2"))`
    - flag, plan claim not in the text: sentence 9 `negligible("age")`
    - flag, plan claim not in the text: sentence 9 `negligible("noise_1")`
    - flag, plan claim not in the text: sentence 9 `negligible("n_inquiries")`
    - flag, one reading only: sentence 1 `direction("utilization") in ("increasing", "mostly_increasing")`
    - flag, one reading only: sentence 1 `rank("utilization") == 1`
    - flag, one reading only: sentence 3 `direction("n_delinquencies") == "increasing"`
    - flag, one reading only: sentence 3 `rank("n_delinquencies") in (2, 3)`
    - flag, one reading only: sentence 4 `direction("income") in ("decreasing", "mostly_decreasing")`
    - flag, one reading only: sentence 4 `strength("income") in ("moderate", "strong")`
    - flag, one reading only: sentence 6 `unsettled(interaction("utilization", "n_delinquencies", pattern="amplification"))`
    - flag, one reading only: sentence 7 `unsettled(interaction("utilization", "history_months", pattern="none"))`
    - flag, one reading only: sentence 8 `unsettled(negligible("dti"))`
    - flag, one reading only: sentence 9 `negligible("age")`
    - flag, one reading only: sentence 9 `negligible("n_inquiries")`
    - flag, one reading only: sentence 9 `negligible("noise_1")`
    - flag, one reading only: sentence 9 `unsettled(negligible("noise_2"))`

### Version 4: template (14 claims, 0 failing)
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

## syn-none-n5000-s1_XGB2_H2_d0_claude-haiku-5-5_plausible

**RELEASED**: passed after 1 repair round(s) (8 calls, 1 repair rounds)

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
Round trip (3 readings):
    - sentence 1 also states `threshold("utilization", at=0.72)`: **false**
    - sentence 5 also states `unsettled(direction("dti") == "increasing")`: ok
    - flag, plan claim not in the text: sentence 2 `direction("n_delinquencies") == "increasing"`
    - flag, one reading only: sentence 7 `unsettled(interaction("utilization", "n_delinquencies", pattern="amplification"))`
    - flag, no DSL form: sentence 5: the data do not settle how the effect of the debt-to-income ratio is shaped

### Version 1: repair 1 (20 claims, 0 failing)
1. Revolving credit utilization is the most important driver of default risk, with a strong effect: risk rises as the share of the credit limit in use goes up, with the rise concentrated in the higher utilization values.
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
Round trip (3 readings):
    - sentence 5 also states `unsettled(direction("dti") == "increasing")`: ok
    - sentence 7 also states `unsettled(interaction("utilization", "n_delinquencies", pattern="amplification"))`: ok
    - flag, plan claim not in the text: sentence 2 `direction("n_delinquencies") == "increasing"`
    - flag, plan claim not in the text: sentence 7 `unsettled(interaction("utilization", "n_delinquencies", pattern="none"))`
    - flag, one reading only: sentence 1 `peak("utilization", at=0.7)`
    - flag, one reading only: sentence 1 `threshold("utilization", at=0.5)`
    - flag, one reading only: sentence 1 `threshold("utilization", at=0.7)`
    - flag, one reading only: sentence 4 `strength("history_months") in ("weak", "moderate")`
    - flag, one reading only: sentence 7 `unsettled(interaction("utilization", "n_delinquencies", pattern="none"))`
    - flag, no DSL form: sentence 1: risk rises as the share of the credit limit in use goes up, with the rise concentrated in the higher utilization values; the rise is concentrated in the higher utilization values
    - flag, no DSL form: sentence 5: the data do not settle how the effect of the debt-to-income ratio is shaped; the data do not settle how its effect is shaped

## syn-none-n5000-s1_XGB2_H2_d0_claude-sonnet-5-5_plausible

**RELEASED**: passed after 0 repair round(s) (4 calls, 0 repair rounds)

### Version 0: proposer (20 claims, 0 failing)
1. Revolving credit utilization is the most important driver of default risk, with a strong effect, and risk increases with utilization.
    - `rank("utilization") == 1`: ok
    - `strength("utilization") == "strong"`: ok
    - `direction("utilization") == "increasing"`: ok
2. The number of past delinquencies is the second or third most important feature, with a moderate to strong effect; risk increases with it and jumps at one delinquency.
    - `strength("n_delinquencies") in ("moderate", "strong")`: ok
    - `rank("n_delinquencies") in (2, 3)`: ok
    - `direction("n_delinquencies") == "increasing"`: ok
    - `threshold("n_delinquencies", at=1.0)`: ok
3. Utilization matters more than the number of past delinquencies.
    - `effect("utilization") > effect("n_delinquencies")`: ok
4. Income is also second or third in importance, with a moderate to strong effect, and risk decreases as income rises.
    - `strength("income") in ("moderate", "strong")`: ok
    - `rank("income") in (2, 3)`: ok
    - `direction("income") == "decreasing"`: ok
5. The length of credit history has at most a moderate effect, with risk decreasing as the history gets longer, and income matters more than it does.
    - `strength("history_months") in ("negligible", "weak", "moderate")`: ok
    - `direction("history_months") == "decreasing"`: ok
    - `effect("income") > effect("history_months")`: ok
6. Age, months at the current address and the number of recent credit inquiries hardly matter.
    - `negligible("age")`: ok
    - `negligible("noise_1")`: ok
    - `negligible("n_inquiries")`: ok
7. Utilization and income do not interact, and neither do delinquencies and income.
    - `interaction("utilization", "income", pattern="none")`: ok
    - `interaction("n_delinquencies", "income", pattern="none")`: ok
8. The data do not settle whether utilization and the number of past delinquencies do not interact.
    - `unsettled(interaction("utilization", "n_delinquencies", pattern="none"))`: ok
Round trip (3 readings): nothing beyond the plan, no flags
