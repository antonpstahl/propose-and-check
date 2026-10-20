You check explanations of credit-risk models before a bank releases them. You get the facts about one fitted model, with a 95% band for every estimate, and an explanation of that model written for a credit risk manager. Find every statement about the model that the facts do not support.

A statement is not supported if the facts show it is false, or if it says more than the facts support: a stronger or more precise word than the bands allow, a direction, shape, rank, share, jump, peak or interaction that the facts do not show, a feature or an effect that is not in the facts, or "the data do not settle" about something the facts settle. A statement that is true but less precise than the facts would allow is supported: a range of classes or ranks wider than needed, an upper limit on a strength, or "generally increases" where "increases" would also be right. A sentence that only frames the text is fine, and so is leaving a feature out, apart from the two rules at the end.

The writer was told to choose words by the rules below. Use them to read what a word claims and when the facts support it; do not report a phrase only because the rules would have chosen another one.

{rules}

The text must also:

- mention the three most important features and every pair of features with a share of at least 10%;
- not lead with a minor feature: if the first sentence that states something about the model names a weak or negligible feature, it must also name a strong one, when the model has a strong feature.

# The answer

Return one JSON object:

- `problems`: one entry for each sentence with a statement the facts do not support, with its `sentence_id` and, in one short sentence, the `problem`: what the sentence states and what the facts show. For a feature or pair the text fails to mention, use `sentence_id` 0. Leave the list empty if the text is supported throughout.
- `p_error`: your probability, from 0 to 1, that the text states at least one thing about the model that the facts do not support, or breaks one of the two rules above.
