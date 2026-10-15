You help test a checker of explanations of credit-risk models. You get the facts about one fitted model and an explanation of it that is correct. Change exactly one sentence so that it states something about the model that the facts do not support: a subtle, plausible error that a careless writer could make. For example: a strength one class too high or too low, the wrong direction, a rank off by one, a jump or a peak in the wrong place, an interaction the facts do not show, or "the data do not settle" about something the facts settle.

- Keep the rest of the sentence, its style and its length. Do not mark or explain the change in the text.
- Change only one statement in that sentence.

Return one JSON object: `sentence_id` (the sentence you changed), `sentence` (its new text), and `claim`: the one DSL claim that states your error, with the feature names exactly as in the facts, in a form from this reference:

{dsl}
