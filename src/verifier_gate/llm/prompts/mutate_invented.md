You help test a checker of explanations of credit-risk models. You get an explanation of one fitted model, sentence by sentence, and an instruction to change one sentence: what it says about one of the model's features, it must say about another quantity instead, one the model does not have. This is the error of a writer who names the wrong variable.

- Rewrite only that sentence. Every statement it makes about the feature is now about the new quantity. The new sentence does not name the feature, by its name, its description or a word that points back to it.
- Name the new quantity in the words you are given. You may change the article or the grammar around them so that the sentence reads naturally, but not the words themselves.
- Keep everything else: what the sentence says (strength, direction, rank, shares, numbers, hedges), what it says about other features, its style and its length. Do not mark or explain the change.

Return one JSON object with `sentence`: the new text of that sentence.
