You translate a short text into claims in a small formal language, the DSL below, so that a verifier can check what the text tells its reader. The text gives the reasons why a credit model declined one applicant. You see only the text and the list of the model's features. You do not see the model or its facts, and you do not judge whether a statement is true: write what the text says, even if it seems unlikely.

# What to extract

- Go through the text sentence by sentence. For every statement a sentence makes about the decision, write the DSL claim that says exactly that, no more and no less. One sentence can make several statements; a statement that names several features can need one claim per feature.
- Read the words as a careful reader would, with the meanings in the table: "the main reason" is reason rank 1, "a key reason" is a principal reason, and "your high credit utilization" states that the applicant's utilization is higher than that of approved applicants; if the sentence gives it as a reason, it is a principal reason as well.
- Do not add what the sentence does not say: nothing from your knowledge of credit, and nothing that only other sentences say.
- A statement the text presents as open ("the data do not settle whether ...", "it is unclear whether ...") is `unsettled(<claim>)`, with the claim it leaves open.
- Use the feature names exactly as listed below, in quotes, also when the text describes a listed feature in other words ("your debt-to-income ratio" for "dti"), but only if the words mean the same quantity as the listed feature: a related but different quantity (the length of employment for the length of credit history) is a feature the list does not have.
- A statement about a feature that matches none in the list, even in other words, is still a statement about the decision: write its claim, not an entry under `unexpressed`. Name the feature with all of the text's words for it but a leading "the" or "your", in snake_case ("the number of open accounts" is "number_of_open_accounts"). This holds wherever the feature appears, also in a clause after a statement about a listed feature. A group of features ("other factors", "the rest of your credit file") is not a feature: write no claim with its name, and write the statement under `unexpressed`.
- If a sentence states something about the decision or the model that no form in the table expresses (a number, a score, a probability, how two reasons compare, how the model works in general), write that statement in a few words under `unexpressed` for the sentence, and do not force it into a claim. Keep any number exactly as the text gives it.
- Not unexpressed: a restatement or a consequence of a claim you wrote for the same sentence, or an intensity word on it ("much", "clearly"). Write the claim once, and nothing under `unexpressed` for it.
- A sentence that only frames the text ("We have reviewed your application.", "You may ask for a free copy of your credit report.") or gives advice that is not about the decision has no claims and nothing unexpressed.

# The DSL

{dsl}

# The answer

Return one JSON object with one list, `sentences`: one entry per sentence of the text, in order, each with the sentence's `id`, its `claims` (DSL lines) and its `unexpressed` statements (short phrases). Use empty lists where a sentence has none.

Example (other features than in your text):

Text:
1. The main reason for our decision is the number of missed payments on your credit file, which is higher than for applicants we approved.
2. A short time in your current job is also a principal reason.
3. The data do not settle whether your loan amount is a principal reason.
4. Your credit score was 612.
5. You may ask for a free copy of your credit report.

{"sentences": [{"id": 1, "claims": ["reason_rank(\"missed_payments\") == 1", "higher_than_reference(\"missed_payments\")"], "unexpressed": []}, {"id": 2, "claims": ["principal_reason(\"months_in_job\")", "lower_than_reference(\"months_in_job\")"], "unexpressed": []}, {"id": 3, "claims": ["unsettled(principal_reason(\"loan_amount\"))"], "unexpressed": []}, {"id": 4, "claims": [], "unexpressed": ["credit score of 612"]}, {"id": 5, "claims": [], "unexpressed": []}]}
