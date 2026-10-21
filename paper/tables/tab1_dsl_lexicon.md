# Tab. 1: the DSL and the lexicon (lexicon v2, frozen)

**Claims about the model (global)**

| Words in the text | DSL claim | Meaning (judged on the whole 95% band) |
|---|---|---|
| "a strong / moderate / weak effect" | `strength("x") == "strong"` (or "moderate", "weak") | share of the model's importance at least 15% / 5% to 15% / 2% to 5%, and an effect the data can detect |
| "a weak to moderate effect", "a moderate to strong effect" | `strength("x") in ("weak", "moderate")` | the share lies somewhere in the classes named |
| "at most a weak effect", "a small effect" | `strength("x") in ("negligible", "weak")` | share below 5% |
| "hardly matters", "negligible" | `negligible("x")` | share below 2%, or no detectable effect and a small share |
| "the most important", "the second most important" | `rank("x") == 1` | rank among the features by importance |
| "second or third", "among the three most important" | `rank("x") in (2, 3)`, `rank("x") in (1, 2, 3)` | one of consecutive ranks |
| "about 30% of the importance" | `share("x") == approx(0.30)` | share of importance, within 2 points or 10% |
| "matters more than" | `effect("x") > effect("y")` | x's importance exceeds y's |
| "risk increases with x" / "decreases" | `direction("x") == "increasing"` (or "decreasing") | rises from the 5th to the 95th percentile, with no reversal the data can detect |
| "risk mostly increases with x" | `direction("x") == "mostly_increasing"` (or "mostly_decreasing") | rises overall, with a detected reversal on at most 10% of the data |
| "risk generally increases with x" | `direction("x") in ("increasing", "mostly_increasing")` | either of the two above |
| "risk jumps at x = 0.43" | `threshold("x", at=0.43)` | one sharp step near that value, at least half of the curve's range |
| "risk peaks at x = 36" | `peak("x", at=36)` | the highest point of the curve lies near that value, with lower values on both sides |
| "the effect of x grows with y" | `interaction("x", "y", pattern="amplification")` | the effect of x is larger when y is high |
| "the effect of x reverses with y" | `interaction("x", "y", pattern="sign_flip")` | the effect of x has opposite signs at low and high y |
| "x and y do not interact" | `interaction("x", "y", pattern="none")` | no interaction of practical size |
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
| "about x%" | within 2% points or 10% of the share |
| "mostly" (exception mass) | a detected reversal on at most 10% of the data |
| jump / peak location (window w) | 2% of the 5th-95th percentile range; on counts, the gap between observed values (v2) |
| jump size | at least 50% of the term's range, significant |
| interaction present | pair share band at or above 2% and a significant interaction contrast |
| band level | 95%, from 100 Poisson bootstrap refits; curves: simultaneous (sup-t) bands |

A claim is true if the whole band lies inside the set its word names, false if it lies outside, undecidable otherwise; undecidable claims are never released as stated (D30).
