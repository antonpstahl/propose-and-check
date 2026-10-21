"""Text-level E2 (experiments/e2_text.py): the template text with one clause changed and its plan unchanged; the
pipeline in stub mode catches every labelled error at the changed sentence and blocks no unchanged text. The tests
read the Facts in cache/facts/ (the archive or build_facts, see the README); without them they are skipped."""

import pytest

from verifier_gate.data import dgp
from verifier_gate.dsl.parse import parse
from verifier_gate.experiments import e2_text
from verifier_gate.experiments.build_facts import load, path
from verifier_gate.gate.template import template
from verifier_gate.verifier.certified import certified_plan


def built(scenario) -> bool:
    return all(path(scenario, kind).with_suffix(".json").exists() for kind in ("EBM", "XGB2"))


@pytest.fixture(scope="module")
def draft():
    if not built(dgp.SCENARIOS[0]):
        pytest.skip("Facts not on disk (cache/facts/, see the README)")
    facts = load(dgp.SCENARIOS[0], "EBM")
    return template(facts, certified_plan(facts))


def test_a_clause_is_rewritten_in_the_templates_words_and_the_rest_kept(draft):
    original = next(c for c in draft.claims if c.kind == "direction")
    mutant = parse(f'direction("{original.terms[0]}") == "{"decreasing" if "increasing" in original.value else "increasing"}"')
    sentences, changed = e2_text.render(draft, original, mutant, None)
    before, after = dict(draft.sentences), dict((i, t) for i, t in sentences)
    assert changed == original.sentence_id and before[changed] != after[changed]
    assert all(before[i] == after[i] for i in before if i != changed)


def test_an_invented_term_reads_as_a_feature_and_an_omission_drops_the_pair(draft):
    original = draft.claims[0]
    invented = parse(str(original).replace(f'"{original.terms[0]}"', '"savings_balance"'))
    sentences, changed = e2_text.render(draft, original, invented, None)
    assert "savings balance" in dict((i, t) for i, t in sentences)[changed].lower()
    pair = next((c for c in draft.claims if c.kind == "interaction"), None)
    if pair is not None:
        kept, changed = e2_text.render(draft, None, None, frozenset(pair.terms))
        assert changed is None and len(kept) <= len(draft.sentences)


def test_the_script_mutants_of_one_dataset_are_labelled(draft):
    cases = e2_text.script_cases(dgp.SCENARIOS[:1])
    roles = {c.info["role"] for c in cases}
    assert sum(c.source == "control" for c in cases) == 2 and "error" in roles
    assert all(c.changed is not None or c.info.get("omitted") or c.source == "control" for c in cases)


def test_plasmode_texts_use_the_columns_words_and_the_data_dictionary():
    from verifier_gate.data import labels, plasmode, tiers
    from verifier_gate.llm import extract

    scenario = next(s for s in plasmode.SCENARIOS if s.seed == 1)
    if not (built(scenario) and plasmode.XLS.exists()):
        pytest.skip("plasmode Facts or TaiwanCredit not on disk (cache/facts/, data/raw/, see the README)")
    cases = e2_text.script_cases((scenario,))
    control = next(c for c in cases if c.source == "control")
    text = " ".join(t for _, t in control.sentences)
    assert control.naming == "codes" and "the latest repayment status" in text.lower() and "PAY_0" not in text
    ctx = e2_text.context(control, {})
    listed = extract.features_text(ctx.facts, ctx.names, ctx.descriptions)
    assert '"BILL_AMT2": amount of the bill statement in August 2005' in listed
    assert set(labels.PLASMODE_DESCRIPTIONS) == set(plasmode.FEATURES) == set(labels.PLASMODE_LABELS)
    assert tiers.name(scenario) == "plasmode"


def test_the_labelled_llm_mutants_are_read_again_as_labelled():
    """D78: x5 reads the 100 LLM mutants the author labelled, each as the labeller saw it, with its E3 text's plan;
    an unread text counts as caught, not at the change (D32), and is counted apart."""
    import pandas as pd

    cases = e2_text.labelled_cases()
    assert len(cases) == 100 and all(c.plan and dict(c.sentences)[c.changed] == c.info["after"] for c in cases)
    first, second = cases[0].info["item"], cases[1].info["item"]
    table = pd.DataFrame({"item": [first, second], "read": [True, False], "caught": [False, None], "caught at the change": [False, None]})
    score = e2_text.labelled_score(table, "x5").set_index("labels")
    assert score.loc["final", "unread"] == 1 and score.loc["final", "labelled"] + score.loc["final", "unsure"] >= 1
