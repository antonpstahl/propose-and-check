# Labelling guide (b1)

## What you see

Each item is one explanation of a fitted credit-risk model (an EBM or a depth-2 XGBoost), written for a reader of
model documentation. Beside it are the facts about that model: each feature's share of the model's importance with
its 95% band from bootstrap refits, the shape of its curve, and the interaction facts for pairs. Every text about the
same model is shown with the same facts. The words table says what the vague words mean.

The items come from several sources and are shuffled. You are not told which source an item comes from, whether
anything checked or changed it, or what any checker said about it. Do not try to find out, and do not open the
project's results for these texts until you have finished all your items.

## What you judge

For each sentence, ask what it says about the model, and whether the facts on the page support that. Judge what a
careful reader of model documentation would take the sentence to say. Where a sentence uses a word from the words
table, judge it by the table's meaning. If your own reading of the word differs, tick **I read the words
differently** and say how you read them in the note.

## Labels for each sentence

- **Supported**: everything the sentence says about the model holds under the facts. A hedge ("the data do not
  settle whether …") is supported when the facts leave that question open.
- **False**: the facts contradict something the sentence says. This includes a statement about a feature or pair
  the model does not have, and a hedge on a question the facts do settle.
- **Not settled**: the sentence states as settled something the facts leave open. Examples are a share whose band
  crosses a class edge, a direction the curve's bands do not establish, a ranking whose bands overlap, or a number
  the facts do not give.
- **Misleading**: what the sentence says holds, but a reader would take away something wrong. Examples are a minor
  feature presented as a main driver, or a true statement placed so that it suggests a false one.
- **Nothing to check**: the sentence says nothing about this model, such as an introduction or a general remark.
- **Unsure**: you cannot tell. Say why in the note.

If a sentence says several things, give it the label of its worst part, in this order: False, Not settled,
Misleading, Supported.

## The whole text

After the sentences, answer one question: taken as a whole, would a reader come away with a wrong picture of the
model? Examples are a main driver left out, the order of importance turned around, or a strong interaction not
mentioned. Answer Yes, No or Unsure.

## Rules

- Label every sentence of every item assigned to you, and answer the whole-text question.
- Use only what the page shows: the facts and the words table.
- Keep notes short and factual: which fact contradicts the sentence, which band leaves it open.
- You may change a label. The page keeps every label you set and every change, with its time.
- Do not change a label after you have seen another rater's labels or any checker's verdict on that text.
- The second rater sees only the items assigned to them. The two raters do not discuss items until both have
  finished.

## How the labels are counted

These rules were fixed before the first label.

A text counts as an error under three standards:

- **refuted**: at least one sentence is False;
- **release rule**: at least one sentence is False or Not settled;
- **broad**: at least one sentence is False, Not settled or Misleading, or the whole text gives a wrong picture.

A text with no error but with an Unsure is open. It is reported both as an error and as no error.
