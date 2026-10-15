You translate a short text about a fitted credit-risk model into claims in a small formal language, the DSL below, so that a verifier can check what the text tells its reader. You see only the text and the list of the model's features. You do not see the model or its facts, and you do not judge whether a statement is true: write what the text says, even if it seems unlikely.

# What to extract

- Go through the text sentence by sentence. For every statement a sentence makes about the model, write the DSL claim that says exactly that, no more and no less. One sentence can make several statements; a statement that names several features can need one claim per feature.
- Read the words as a careful reader would, with the meanings in the table: "the most important driver" is rank 1, "a moderate effect" is strength moderate, "risk jumps once utilization passes about 0.7" is a jump at 0.7.
- Do not add what the sentence does not say: nothing from your knowledge of credit risk, and nothing that only other sentences say.
- Numbers as the text gives them: "about 30% of the importance" is `approx(0.30)`, "at around 0.7" is `at=0.7`.
- A statement the text presents as open ("the data do not settle whether ...", "it is unclear whether ...") is `unsettled(<claim>)`, with the claim it leaves open.
- But a statement that something is one of several values and the data do not settle which ("the data do not settle whether its effect is weak or moderate", "... negligible, weak or moderate") states the set: `strength("x") in ("weak", "moderate")`, not a hedge. A hedge says the data leave a claim open; a set says the value lies among those named.
- Nor is a statement that the data do not show or confirm something ("the data do not confirm a single sharp step", "no clear interaction is shown") a hedge: it says that thing is absent. Write the claim of its absence if the table has one (no interaction: `pattern="none"`); otherwise it is unexpressed.
- Use the feature names exactly as listed below, in quotes, also when the text describes a feature in other words ("the debt-to-income ratio" for "dti").
- If a sentence states something about the model that no form in the table expresses, write that statement in a few words under `unexpressed` for the sentence, and do not force it into a claim. Keep any number exactly as the text gives it. This includes statements weakened only by "may", "might", "possibly" or "perhaps", and descriptions of a curve's shape that are not a jump, a peak or a direction. Write only the statement, without comments.
- Not unexpressed: a restatement or a consequence of a claim you wrote for the same sentence ("so high utilization matters more for applicants with delinquencies" after the amplification claim; "the two act separately" after a claim of no interaction), or an intensity word on it ("far", "much", "clearly"). Write the claim once, and nothing under `unexpressed` for it.
- Risk being highest at the top or the bottom of a feature's range is a direction, not a peak: a peak lies inside the range, with lower risk on both sides.
- A sentence that only frames the text ("This summary covers the main drivers.") or gives advice that is not about the model has no claims and nothing unexpressed.

# The DSL

{dsl}

# The answer

Return one JSON object with one list, `sentences`: one entry per sentence of the text, in order, each with the sentence's `id`, its `claims` (DSL lines) and its `unexpressed` statements (short phrases). Use empty lists where a sentence has none.

Example (other features than in your text):

Text:
1. Missed payments are the most important driver of default risk, and risk jumps at the second missed payment.
2. Loan purpose hardly matters.
3. The data do not settle whether the loan amount has a moderate effect.
4. Applicants with longer credit histories are safer, a pattern that holds across all regions.
5. This summary covers the main drivers.

{"sentences": [{"id": 1, "claims": ["rank(\"missed_payments\") == 1", "threshold(\"missed_payments\", at=2)"], "unexpressed": []}, {"id": 2, "claims": ["negligible(\"loan_purpose\")"], "unexpressed": []}, {"id": 3, "claims": ["unsettled(strength(\"loan_amount\") == \"moderate\")"], "unexpressed": []}, {"id": 4, "claims": ["direction(\"credit_history_months\") == \"decreasing\""], "unexpressed": ["the pattern holds across all regions"]}, {"id": 5, "claims": [], "unexpressed": []}]}
