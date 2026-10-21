"""The writer's prompts, the proposer's requests and answers (llm/prompts, llm/propose.py) and the handover
(llm/handover.py)."""

import json
import re

import numpy as np
import pytest

from verifier_gate.data import dgp, labels
from verifier_gate.dsl.grammar import Claim
from verifier_gate.dsl.parse import parse
from verifier_gate.facts import bootstrap
from verifier_gate.facts.build import Frame, build_facts
from verifier_gate.lexicon.predicates import TRUE
from verifier_gate.llm import prompts, propose
from verifier_gate.llm.client import Response
from verifier_gate.llm.handover import handover
from verifier_gate.verifier.certified import certified_plan
from verifier_gate.verifier.verify import verify


def test_every_dsl_example_in_the_system_prompt_parses():
    examples = re.findall(r"`([a-z_]+\(.*?\)(?: [=<>in]+ .+?)?)`", prompts.load("system"))
    examples = [e for e in examples if "<" not in e and "..." not in e]  # placeholders: unsettled(<any claim above>), unsettled(...)
    assert len(examples) >= 15
    for line in examples:
        parse(line.replace('"x"', '"a"').replace('"y"', '"b"'))
    example = json.loads(prompts.load("system").split("Example (other features than in your facts):")[1].strip())
    for claim in example["claims"]:
        parse(claim["dsl"])


def test_prompt_hashes_are_frozen_after_the_pilot():
    frozen = prompts.expected()  # the hashes of the version the lexicon gives (frozen.json: v3, frozen_v4.json: v4)
    if frozen is None:
        pytest.skip("prompts not frozen yet (the pilot freezes them)")
    assert prompts.hashes() == frozen


def test_extractor_prompt_hashes_are_frozen_after_the_pilot():
    """The assembled extractor prompt includes the writer's DSL table, so a change there shows here too."""
    frozen = prompts.expected(prompts.EXTRACTOR_NAMES)
    if frozen is None:
        pytest.skip("extractor prompts not frozen yet (the round-trip pilot freezes them)")
    assert prompts.hashes(prompts.EXTRACTOR_NAMES) == frozen


def test_the_proposer_request_carries_the_handover_and_the_schema():
    request = propose.proposer_request("FACTS HERE", draw=2)
    assert request.role == "proposer" and request.draw == 2 and request.system == prompts.load("system")
    assert "FACTS HERE" in request.messages[0][1]
    schema = json.loads(request.schema)
    assert schema["required"] == ["sentences", "claims"] and not schema["additionalProperties"]
    assert propose.proposer_request("FACTS HERE", draw=3).key != request.key


def response(data) -> Response:
    return Response("k", "proposer", "m", "end_turn", "", json.dumps(data), data)


def test_a_draft_maps_names_back_and_keeps_format_errors():
    data = {"sentences": [{"id": 1, "text": "Months at address hardly matters."}, {"id": 2, "text": "Income matters."}],
            "claims": [{"sentence_id": 1, "dsl": 'negligible("months_at_address")'},
                       {"sentence_id": 2, "dsl": 'strength("income") is "moderate"'},
                       {"sentence_id": 7, "dsl": 'negligible("age")'}]}  # fmt: skip
    draft = propose.draft_from(response(data), "proposer")
    assert draft.claims == [Claim("negligible", ("noise_1",), sentence_id=1)]
    assert len(draft.format_errors) == 2
    assert draft.format_errors[0].startswith('sentence 2: strength("income") is "moderate":')
    assert "no sentence with this id" in draft.format_errors[1]


def test_an_answer_that_is_not_a_draft_is_refused():
    with pytest.raises(ValueError):
        propose.draft_from(response({"text": "hello"}), "proposer")


@pytest.fixture(scope="module")
def oracle_facts():
    """Facts with bands, cheaply: the oracle with 20 refits on one small dataset."""
    data = dgp.generate(dgp.Scenario("dominant", 5_000, 1))
    reference = bootstrap.fit_steps("oracle", data.X, data.y, seed=1)
    draws = bootstrap.refit_draws("oracle", data.X, data.y, 1, Frame.of(reference, data.X), refits=20)
    return build_facts(reference, data.X, draws, {"kind": "oracle"}), data.X


def test_the_handover_shows_every_feature_under_its_writer_name_and_passes_its_check(oracle_facts):
    facts, X = oracle_facts
    plan = certified_plan(facts)
    h1, h2 = handover(facts, X, "H1", plan), handover(facts, X, "H2", plan)
    assert h1.passed and h2.passed and len(h1.checks) == len(facts.features)
    for name in ("utilization", "n_delinquencies", "months_at_address", "num_dependents"):
        assert f"`{name}`" in h1.text
    assert "noise" not in h1.text.lower() and "noise" not in h2.text.lower()
    assert "Statements the verifier certifies" in h2.text and "Statements" not in h1.text
    assert h2.text.startswith(h1.text)
    assert 'rank("utilization") == 1' in h2.text
    assert np.isclose(len(h1.text), len(handover(facts, X, "H1", plan).text))  # deterministic


@pytest.mark.parametrize("naming", ["plausible", "opaque"])
def test_h2_lists_the_certified_statements_under_the_writer_names_and_each_verifies(oracle_facts, naming):
    """The H2 naming bug (M5 of the 20 Oct review): under opaque names, H2 listed the certified statements under the
    plausible ones, which the verifier then found unknown. naming_bug rebuilds that handover, to replay E3 as run."""
    facts, X = oracle_facts
    plan = certified_plan(facts)
    names, other = (labels.SYNTHETIC_NAMES, labels.OPAQUE_NAMES) if naming == "plausible" else (labels.OPAQUE_NAMES, labels.SYNTHETIC_NAMES)
    h2 = handover(facts, X, "H2", plan, names=names)
    for name in other.values():
        assert not re.search(rf"\b(?:{name}|{labels.SYNTHETIC_LABELS[name]})\b", h2.text), name
    shown = {labels.shown(f.name, names) for f in facts.features}
    listed = h2.text.split("Statements the verifier certifies")[1].splitlines()[1:]
    assert listed
    for line in listed:
        claim = parse(line.removeprefix("- ").split("  (")[0])
        assert {s.strip() for t in (claim.inner or claim).terms for s in t.split("&")} <= shown, line
        assert verify(labels.internal(claim, names), facts).value == TRUE, line
    as_run = handover(facts, X, "H2", plan, names=names, naming_bug=True)
    assert (as_run.text == h2.text) == (naming == "plausible")


def test_each_extractor_version_in_the_history_differs_from_the_current_one():
    current = prompts.hashes(prompts.EXTRACTOR_NAMES)
    assert prompts.EXTRACTOR_VERSION not in prompts.EXTRACTOR_HISTORY
    for version, hashes in prompts.EXTRACTOR_HISTORY.items():
        assert hashes != current, version
