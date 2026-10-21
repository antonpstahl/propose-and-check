"""Lexicon v3 (D63-D65): equivalence margins for the strict direction words, "hardly matters" and "do not
interact"; signed jumps; and the words the writer, the extractor, the template and Table 1 share, generated from
the lexicon. Each rule is checked against v2 on the same toy facts (tests/test_lexicon.py), so the change shows."""

import dataclasses
import re

import numpy as np
import pytest
import yaml
from test_lexicon import BASE, MIDS, UP, X, exact_facts, main, pair_grid, per_step, shell, toy_facts  # noqa: F401

from verifier_gate.data import dgp
from verifier_gate.dsl.parse import DSLError, parse
from verifier_gate.facts.build import build_facts
from verifier_gate.facts.reference import reference_steps
from verifier_gate.facts.schema import Estimate
from verifier_gate.gate.template import phrase, synthetic_label, template
from verifier_gate.lexicon import predicates as p
from verifier_gate.lexicon import words
from verifier_gate.llm import prompts
from verifier_gate.verifier.certified import certified_plan
from verifier_gate.verifier.verify import verify

V2, V3 = p.load(p.VERSIONS["v2"]), p.load(p.VERSIONS["v3"])


@pytest.fixture(autouse=True)
def current(monkeypatch):
    """These tests are about v3, the default: they run without the pin, whatever the environment says."""
    monkeypatch.delenv(p.PIN, raising=False)


def test_the_default_is_v3_and_the_pin_restores_v2(monkeypatch):
    assert p.load().version == "v3" and p.load() is V3
    monkeypatch.setenv(p.PIN, "v2")
    assert p.load() is V2 and prompts.writer_version() == "v3"
    monkeypatch.setenv(p.PIN, "v9")
    with pytest.raises(ValueError):
        p.load()


def test_v2_is_kept_byte_for_byte_and_lacks_every_v3_key():
    assert (V2.direction_margin, V2.undetected_negligible, V2.signed_jumps) == (None, True, False)
    assert (V3.direction_margin, V3.undetected_negligible, V3.signed_jumps) == (0.05, False, True)
    import hashlib

    assert hashlib.sha256(p.VERSIONS["v2"].read_bytes()).hexdigest() == "111dfe3f08c57fcfed9edda7a10effbeb5f07295867a044a92b81e6548de1ab1"


# --- strict direction words: an equivalence margin (D63) ---------------------------------------------------


def test_the_strict_word_needs_the_band_to_rule_out_a_reversal(X):
    """Narrow bands on a ramp rule out any fall beyond the margin: "increases" is certified and "mostly" is false
    (v2 left "mostly" open, D29). The same dip inside wide bands was "increases" in v2; in v3 it is open, and the
    writer falls back to "generally increases"."""
    ramp = toy_facts(X, BASE)
    assert verify('direction("ramp") == "increasing"', ramp, V3).value == p.TRUE
    assert verify('direction("ramp") == "mostly_increasing"', ramp, V3).value == p.FALSE
    assert verify('direction("ramp") == "mostly_increasing"', ramp, V2).value == p.UNDECIDABLE
    dip = np.linspace(0, 2, 20)
    dip[10] -= 0.6
    wide = toy_facts(X, BASE + [main("dip", dip)], perturb={"dip": per_step(0.3)})
    assert verify('direction("dip") == "increasing"', wide, V2).value == p.TRUE
    verdict = verify('direction("dip") == "increasing"', wide, V3)
    assert verdict.value == p.UNDECIDABLE and verdict.evidence["largest reversal the band allows"] > verdict.evidence["margin"]
    assert p.direction_in(wide, "dip", UP, V3).value == p.TRUE


def test_a_reversal_within_the_margin_is_immaterial_and_one_beyond_it_is_an_exception(X):
    """On an exact curve (T): the margin is 5% of the curve's range (about 0.1 here). A fall of about 0.045 does
    not refute "increases" in v3 (v2 refuted it); a fall of about 0.5 on 5% of the data makes it "mostly"."""
    small, large = np.linspace(0, 2, 20), np.linspace(0, 2, 20)
    small[10] -= 0.15
    large[10] -= 0.6
    for values, strict, mostly in ((small, p.TRUE, p.FALSE), (large, p.FALSE, p.TRUE)):
        facts = exact_facts(X, BASE + [main("dip", values)])
        verdict = verify('direction("dip") == "increasing"', facts, V3)
        assert verdict.value == strict and 0.09 < verdict.evidence["margin"] < 0.11
        assert verify('direction("dip") == "mostly_increasing"', facts, V3).value == mostly
    assert verify('direction("dip") == "increasing"', exact_facts(X, BASE + [main("dip", small)]), V2).value == p.FALSE


def test_strict_and_mostly_are_never_both_certified(X):
    for perturb in (None, {"dip": per_step(0.05)}, {"dip": per_step(0.3)}):
        dip = np.linspace(0, 2, 20)
        dip[10] -= 0.3
        facts = toy_facts(X, BASE + [main("dip", dip)], perturb=perturb)
        values = {verify(f'direction("dip") == "{w}"', facts, V3).value for w in ("increasing", "mostly_increasing")}
        assert values != {p.TRUE}


# --- "hardly matters" and "do not interact": the band below the edge (D63) ------------------------------------


def test_hardly_matters_needs_the_whole_band_below_the_weak_edge():
    """v2 also certified an undetected effect with a share below 2% and a band below 5%: absence of evidence. v3
    leaves it open, and "at most a weak effect" (band below 5%) is what the template states instead."""

    def judge(band, lex, claim='negligible("x")'):
        facts = shell(np.zeros(20))  # no detectable effect
        object.__setattr__(facts.feature("x"), "share", Estimate(sum(band) / 2, band))
        return verify(claim, facts, lex).value

    assert judge((0.004, 0.03), V2) == p.TRUE  # share 1.7%
    assert judge((0.004, 0.03), V3) == p.UNDECIDABLE
    assert judge((0.004, 0.03), V3, 'strength("x") in ("negligible", "weak")') == p.TRUE
    assert judge((0.002, 0.018), V3) == judge((0.002, 0.018), V2) == p.TRUE


def test_do_not_interact_needs_the_pair_band_below_the_edge_and_a_missing_pair_is_none(X):
    a, b = np.meshgrid(MIDS, MIDS, indexing="ij")
    rescale = lambda scores, rng: scores * (1 + rng.normal(0, 1.5))  # noqa: E731  an undetectable pair
    facts = toy_facts(X, BASE + [main("a", MIDS), main("b", MIDS), pair_grid(0.02 * a * b)], perturb={"a & b": rescale})
    pair = facts.pair("a", "b")
    object.__setattr__(pair, "share", Estimate(0.012, (0.004, 0.03)))
    assert verify('interaction("a", "b", pattern="none")', facts, V2).value == p.TRUE
    verdict = verify('interaction("a", "b", pattern="none")', facts, V3)
    assert verdict.value == p.UNDECIDABLE and not verdict.evidence["detectable"]
    lacking = toy_facts(X, BASE + [main("a", MIDS), main("b", MIDS)])
    assert verify('interaction("a", "b", pattern="none")', lacking, V3).value == p.TRUE


# --- signed jumps (D64) --------------------------------------------------------------------------------------


def test_jumps_are_signed_in_v3(X):
    up = toy_facts(X, BASE + [main("step", np.where(MIDS >= 0.6, 1.0, 0.0))])
    down = toy_facts(X, BASE + [main("step", np.where(MIDS >= 0.6, 0.0, 1.0))])
    assert verify('threshold("step", at=0.6)', up, V3).value == p.TRUE
    assert verify('drop("step", at=0.6)', up, V3).value == p.FALSE
    assert verify('drop("step", at=0.6)', down, V3).value == p.TRUE
    assert verify('threshold("step", at=0.6)', down, V3).value == p.FALSE
    assert verify('threshold("step", at=0.6)', down, V2).value == p.TRUE  # v2: either sign
    exact = exact_facts(X, BASE + [main("step", np.where(MIDS >= 0.6, 0.0, 1.0))])
    assert verify('drop("step", at=0.6)', exact, V3).value == p.TRUE
    assert verify('threshold("step", at=0.6)', exact, V3).value == p.FALSE


def test_the_certified_jump_takes_the_sign_of_m_s_step(X):
    down = toy_facts(X, BASE + [main("step", np.where(MIDS >= 0.6, 0.0, 1.0))])
    jumps = [c for c in certified_plan(down, V3) if c.kind in ("threshold", "drop") and c.terms == ("step",)]
    assert [c.kind for c in jumps] == ["drop"]
    assert [c.kind for c in certified_plan(down, V2) if c.kind in ("threshold", "drop") and c.terms == ("step",)] == ["threshold"]


def test_drop_parses_only_from_v3(monkeypatch):
    assert str(parse('drop("x", at=2000)')) == 'drop("x", at=2000.0)'
    monkeypatch.setenv(p.PIN, "v2")
    with pytest.raises(DSLError, match=r"\['interaction', 'negligible', 'peak', 'threshold', 'unsettled'\]"):
        parse('drop("x", at=2000)')  # v2's message, word for word, so v2's format retries replay


# --- the words: one source for the writer, the extractor, the template and Table 1 (D65) -------------------


def test_no_number_in_the_words_is_written_by_hand():
    """Every threshold comes from a placeholder: the word spec and the writer's template hold no number with a
    percent sign ("about x%" names a variable)."""
    spec = yaml.safe_load(p.VERSIONS["v3"].read_text())["words"]
    texts = [r["text"] for r in spec["rules"]] + [r["meaning"] for r in spec["table"]] + list(spec["phrases"].values())
    texts.append((prompts.HERE / prompts.WRITER_FILES["v4"]["system"]).read_text())
    assert not [t for t in texts if re.search(r"\d\s*(%|percent|points)", t)]


def test_the_prompt_follows_the_lexicon_s_numbers():
    moved = dataclasses.replace(V3, strength={"weak": 0.03, "moderate": 0.07, "strong": 0.21}, direction_margin=0.08,
                                exception_mass=0.12, jump_fraction=0.6, pair_share=0.04, share_absolute=0.03)  # fmt: skip
    text = words.rules(moved) + words.table(moved)
    for shown in ("3% to 7%", "21% or more", "8% of the curve's range", "12% of the data", "60% of the curve's range", "below 4%", "3 points"):
        assert shown in text, shown
    for old in ("2% to 5%", "15% or more", "5% of the curve's range", "10% of the data", "50% of the curve's range"):
        assert old not in text, old


def test_every_table_row_parses_and_its_words_are_the_template_s_phrases():
    for row in words.section(V3)["table"]:
        for line in row.get("claims", []):
            claim = parse(line)
            assert f'"{phrase(claim, str, V3)}"' in words.table(V3)
    rows = words.table_rows(V3)
    assert len(rows) == len(words.section(V3)["table"]) and any("drop(" in dsl for _, dsl, _ in rows)


def test_the_writer_and_the_extractor_read_the_generated_table():
    table = words.table(V3)
    assert table in prompts.load("system") and table in prompts.extractor_system()
    assert words.rules(V3) in prompts.word_rules()
    assert prompts.EXTRACTOR_VERSIONS[p.pinned()] == "x5" and prompts.writer_version() == "v4"


def test_v3_phrases_refer_to_the_model_and_v2_s_do_not_change():
    label = synthetic_label()
    for line, v2_words in (('direction("income") == "decreasing"', "default risk decreases with income"),
                           ('negligible("noise_1")', "months at the current address hardly matters for default risk")):  # fmt: skip
        assert phrase(parse(line), label, V2) == v2_words
        assert "model" in phrase(parse(line), label, V3)
    assert phrase(parse('rank("income") in (2, 3)'), label, V3) == "income is the model's second or third most important feature"


def test_every_template_sentence_under_v3_refers_to_the_model():
    data = dgp.generate(dgp.SCENARIOS[1])
    facts = build_facts(reference_steps(data.truth, data.X), data.X)
    draft = template(facts, certified_plan(facts, V3))
    assert draft.sentences and all("model" in text for _, text in draft.sentences)
