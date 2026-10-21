"""Text-level E2 on held-out invented features (experiments/e2_heldout.py, data/invented.py): the terms are new to
extractor x4's development, a template case changes one clause and nothing else, the reading of a change tells an
unknown term from a mapped one, a rewrite is used only if it names the term and drops the feature, and the frozen
set matches its manifest. The template test reads the Facts in cache/facts/; without them it is skipped."""

import json
import re
from pathlib import Path

import pandas as pd
import pytest

from verifier_gate.data import dgp, invented, labels, tiers
from verifier_gate.dsl.parse import parse
from verifier_gate.experiments import e2_heldout as h
from verifier_gate.experiments import e2_mutation as e2
from verifier_gate.experiments import e2_text
from verifier_gate.experiments.build_facts import path
from verifier_gate.llm import prompts
from verifier_gate.llm.extract import Extraction

REPO = Path(__file__).parents[1]


def development() -> dict[str, str]:
    """What x4's development read: its prompts, its probe, and E2's M9 term."""
    return {"extract_system.md": prompts.load("extract_system"), "extract.md": prompts.load("extract"), "dsl": prompts.dsl_reference(),
            "04_x4_heldout.py": (REPO / "notebooks" / "04_x4_heldout.py").read_text(), "E2's M9 term": e2_text._label(e2.UNKNOWN)}  # fmt: skip


def test_the_held_out_terms_are_new_to_x4_and_the_anchors_are_not():
    sources = development()
    for t in invented.TERMS:
        hits = [name for name, text in sources.items() if re.search(t.cue, text, re.I)]
        assert hits == [] if t.held_out else hits, (t.name, hits)


def test_an_invented_term_is_no_name_the_feature_list_already_gives():
    for t in invented.TERMS:
        if t.kind == "paraphrase":
            continue
        shown = labels.SYNTHETIC_LABELS | labels.SYNTHETIC_DESCRIPTIONS if t.tier == "synthetic" else labels.PLASMODE_LABELS | labels.PLASMODE_DESCRIPTIONS
        assert not any(re.search(t.cue, f"{k} {v}", re.I) for k, v in shown.items()), t.name


def test_the_terms_cover_the_review_and_pair_each_near_synonym_with_a_paraphrase():
    names = [t.name for t in invented.TERMS]
    assert len(names) == len(set(names))
    assert sum(t.held_out and t.kind != "paraphrase" for t in invented.TERMS) >= 10
    for t in invented.TERMS:
        features = tiers.module(t.tier).FEATURES
        assert t.kind in invented.KINDS and t.name not in features and re.search(t.cue, t.words, re.I), t.name
        assert (t.neighbour in features) if t.kind != "unrelated" else t.neighbour is None, t.name
        if t.kind == "near-synonym":
            assert any(u.kind == "paraphrase" and u.neighbour == t.neighbour and u.tier == t.tier for u in invented.TERMS), t.name


def test_a_template_case_changes_one_clause_and_shares_its_clauses():
    scenario = dgp.SCENARIOS[0]
    if not all(path(scenario, kind).with_suffix(".json").exists() for kind in e2.MODELS):
        pytest.skip("Facts not on disk (cache/facts/, see the README)")
    cases = h.template_cases("synthetic", h.p.load(), (scenario,))
    for c in cases:
        words = invented.term(c.info["term"]).words
        changed = dict((i, s) for i, s in c.sentences)[c.changed]
        assert words.lower() in changed.lower() and sum(words.lower() in s.lower() for _, s in c.sentences) == 1
    clauses = lambda term, placement: {(c.model, c.info["original"]) for c in cases if c.info["term"] == term and c.info["placement"] == placement}  # noqa: E731
    assert clauses("revolving_balance", "on the neighbour") == clauses("fraction_of_the_credit_limit_in_use", "on the neighbour") != set()
    assert clauses("down_payment", "elsewhere") == clauses("savings_balance", "elsewhere") != set()
    assert all(c.info["replaced"] != c.info["neighbour"] for c in cases if c.info["placement"] == "elsewhere")


def _case(original: str) -> e2_text.Case:
    plan = [parse('strength("utilization") == "strong"', sentence_id=1), parse('direction("utilization") == "increasing"', sentence_id=1)]
    info = {"original": original, "replaced kinds": parse(original).kind, "replaced": "utilization", "neighbour": "utilization"}
    return e2_text.Case("x", "template", "s", "EBM", "plausible", [], plan, 1, info)


def _reading(*lines: str, unexpressed: bool = False) -> Extraction:
    return Extraction([parse(line, sentence_id=1) for line in lines], {1: ["something"]} if unexpressed else {})


def test_the_reading_of_a_change_tells_an_unknown_term_from_a_mapped_one():
    case, listed = _case('direction("utilization") == "increasing"'), {"utilization", "income"}
    kept = 'strength("utilization") == "strong"'
    unknown = h.change_reading(case, [_reading(kept, 'direction("revolving_balance") == "increasing"'),
                                      _reading(kept, 'direction("the_revolving_balance") == "increasing"'), _reading(kept)], listed)  # fmt: skip
    assert unknown["read as unknown"] and not unknown["mapped"]  # under two names: a normalising rule would still block it
    mapped = h.change_reading(case, [_reading(kept, 'direction("utilization") == "increasing"')] * 2 + [_reading(kept)], listed)
    assert mapped["mapped onto the neighbour"] and mapped["mapped onto the replaced feature"] and not mapped["read as unknown"]
    neither = h.change_reading(case, [_reading(kept, unexpressed=True)] * 3, listed)
    assert not neither["mapped"] and not neither["read as unknown"] and neither["unexpressed"]
    hardly = h.change_reading(_case('negligible("utilization")'), [_reading('strength("utilization") in ("negligible", "weak")')] * 2, listed)
    assert hardly["mapped"]  # "hardly matters" read as a strength set is still about that feature's strength


def test_a_rewrite_must_name_the_term_and_drop_the_feature():
    term = invented.term
    before = "Age has a weak effect on default risk."
    assert h.rewrite_problem(before, "The age of the newest account has a weak effect on default risk.", "age", term("age_of_newest_account")) == ""
    assert h.rewrite_problem("Income has a weak effect, and the debt-to-income ratio a moderate one.",
                             "The co-applicant's income has a weak effect, and the debt-to-income ratio a moderate one.", "income",
                             term("co_applicants_income")) == ""  # fmt: skip
    assert h.rewrite_problem(before, "Risk falls for older applicants with a larger down payment.", "age", term("down_payment")) == "the feature is still named"
    assert h.rewrite_problem("Recent credit inquiries have a weak effect; risk increases as inquiries rise.",
                             "The age of the newest account has a weak effect; risk increases as the newest account gets younger.", "n_inquiries",
                             term("age_of_newest_account")) == ""  # a younger account is not a younger applicant  # fmt: skip
    assert h.rewrite_problem("Length of credit history has a moderate effect, with risk falling as the history gets longer.",
                             "The age of the newest account has a moderate effect, with risk falling as that age grows.", "history_months",
                             term("age_of_newest_account")) == ""  # "that age" points back to the term  # fmt: skip
    assert h.rewrite_problem("Credit utilization, the share of the limit in use, matters most.",
                             "Income, the share in use, is not it; the co-applicant's income matters most.", "utilization",
                             term("co_applicants_income")) == "another feature is named"  # fmt: skip
    assert h.rewrite_problem(before, "Savings have a weak effect on default risk.", "age", term("revolving_balance")) == "the term is not named"
    assert h.rewrite_problem(before, before, "age", term("down_payment")) == "unchanged"


def test_the_frozen_set_matches_its_manifest(tmp_path):
    manifest = h.SET / "manifest.json"
    if not manifest.exists():
        pytest.skip("the held-out set is not built (e2_heldout --build)")
    record = json.loads(manifest.read_text())
    assert all(h.sha256(h.SET / name) == digest for name, digest in record["sha256"].items())
    pd.DataFrame(invented.table()).to_csv(tmp_path / "terms.csv", index=False)
    assert h.sha256(tmp_path / "terms.csv") == record["sha256"]["terms.csv"], "the terms changed after the set was frozen"
