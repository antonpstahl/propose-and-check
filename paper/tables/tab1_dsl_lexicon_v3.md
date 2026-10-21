# Tab. 1: the DSL and the lexicon (lexicon v3)

**Claims about the model (global)**

| Words in the text | DSL claim | Meaning (judged on the whole 95% band) |
|---|---|---|
| "x has a strong effect on the model's predictions" / "x has a moderate effect on the model's predictions" / "x has a weak effect on the model's predictions" | `strength("x") == "strong"` / `strength("x") == "moderate"` / `strength("x") == "weak"` | share of the model's importance at least 15% / 5% to 15% / 2% to 5%, and an effect the data can detect |
| "x has a weak to moderate effect on the model's predictions" / "x has a moderate to strong effect on the model's predictions" | `strength("x") in ("weak", "moderate")` / `strength("x") in ("moderate", "strong")` | the share lies somewhere in the classes named |
| "x has at most a weak effect on the model's predictions" | `strength("x") in ("negligible", "weak")` | share below 5% |
| "x hardly matters to the model's predictions" | `negligible("x")` | share below 2% |
| "x is the model's most important feature" / "x is the model's second most important feature" | `rank("x") == 1` / `rank("x") == 2` | rank among the features by importance |
| "x is the model's second or third most important feature" / "x is among the model's three most important features" | `rank("x") in (2, 3)` / `rank("x") in (1, 2, 3)` | one of consecutive ranks |
| "x accounts for about 30% of the model's importance" | `share("x") == approx(0.30)` | share of importance, within 2 points or 10% |
| "x matters more to the model than y" | `effect("x") > effect("y")` | x's importance exceeds y's |
| "the model's predicted default risk increases with x" / "the model's predicted default risk decreases with x" | `direction("x") == "increasing"` / `direction("x") == "decreasing"` | rises (falls) from the 5th to the 95th percentile, and the band rules out any move the other way larger than 5% of the curve's range |
| "the model's predicted default risk mostly increases with x" / "the model's predicted default risk mostly decreases with x" | `direction("x") == "mostly_increasing"` / `direction("x") == "mostly_decreasing"` | rises (falls) overall, with a move the other way larger than 5% of the curve's range, confirmed by the band, on at most 10% of the data |
| "the model's predicted default risk generally increases with x" | `direction("x") in ("increasing", "mostly_increasing")` | either of the two above |
| "the model's predicted default risk jumps at x = 0.43" | `threshold("x", at=0.43)` | one sharp step up near that value, at least 50% of the curve's range |
| "the model's predicted default risk drops at x = 2,000" | `drop("x", at=2000)` | one sharp step down near that value, at least 50% of the curve's range |
| "the model's predicted default risk peaks at x = 36" | `peak("x", at=36)` | the highest point of the curve lies near that value, with lower values on both sides |
| "in the model, the effect of x grows with y" | `interaction("x", "y", pattern="amplification")` | the effect of x is larger when y is high, and the pair's share band lies at or above 2% |
| "in the model, the effect of x reverses its sign as y changes" | `interaction("x", "y", pattern="sign_flip")` | the effect of x has opposite signs at low and high y |
| "the model shows no interaction between x and y" | `interaction("x", "y", pattern="none")` | the model has no such pair, or the pair's whole share band lies below 2% |
| "the data do not settle whether ..." | `unsettled(<any claim above>)` | the facts leave that claim open at this sample size |

**Claims about one declined applicant (local spot check)**

| Words in the text | DSL claim | Meaning (judged on the whole 95% band) |
|---|---|---|
| "a principal reason", "a key reason for the decision" | `principal_reason("x")` | x pushes the score towards the decline by at least 10% of the gap to comparable approved applicants, and is among the four largest such factors |
| "the main reason", "the first reason" | `reason_rank("x") == 1` | x pushes the score towards the decline more than any other factor |
| "the second reason", "the third reason" | `reason_rank("x") == 2` (or 3, 4) | x is the second (third, fourth) largest factor pushing towards the decline |
| "one of the two main reasons", "the second or third reason" | `reason_rank("x") in (1, 2)`, `reason_rank("x") in (2, 3)` | one of consecutive ranks |
| "high x", "x is higher than for approved applicants" | `higher_than_reference("x")` | the applicant's value is above the median of comparable approved applicants |
| "low x", "a short x", "few x" | `lower_than_reference("x")` | the applicant's value is below that median |

**The lexicon's thresholds**

| Threshold | Value |
|---|---|
| strength classes (share of importance) | negligible < 2% ≤ weak < 5% ≤ moderate < 15% ≤ strong |
| detectable effect | simultaneous band excludes 0 on more than 5% of the data, or a significant net change |
| "hardly matters", "no interaction" | the whole share band (a pair's share band) below 2% (2%), or a pair the model lacks (v3) |
| "about x%" | within 2 points or 10% of the share |
| direction margin | 5% of the term's range between its 1st and 99th percentile; "increases" needs the band to rule out any fall larger than that (v3) |
| "mostly" (exception mass) | a fall larger than the margin, detected, on at most 10% of the data |
| jump / peak location (window w) | 2% of the 5th-95th percentile range; on counts, the gap between observed values (v2) |
| jump size and sign | at least 50% of the term's range, significant; "jumps at" a step up, "drops at" a step down (v3) |
| interaction present | pair share band at or above 2% and a significant interaction contrast |
| band level | 95%, from 100 Poisson bootstrap refits; curves: simultaneous (sup-t) bands |

A claim is true if the whole band lies inside the set its word names, false if it lies outside, undecidable otherwise; undecidable claims are never released as stated (D30). The global rows and the thresholds are generated from the lexicon, as the writer's and the extractor's prompts are (D65).
