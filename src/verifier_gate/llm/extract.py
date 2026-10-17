"""Extractor (§5.7): translates a text into DSL claims without seeing the plan or the facts.

It sees the text, sentence by sentence, and the features under the names and descriptions the writer saw (D43,
proposed), with the writer's table of what the words mean (llm/prompts, extract_system.md). It answers in one
JSON object: per sentence its DSL lines and the statements no DSL form expresses (`unexpressed`, the expressivity
gap). The gate asks for EXTRACTIONS independent extractions of each text, as separate calls (`replica`); a claim
counts if at least two of them find it (gate/roundtrip.py). Claims are mapped back to the Facts' names like the
writer's. A DSL line that does not parse is kept as a format error of that extraction. An answer that leaves out a
sentence is not a reading: in the round-trip pilot 9 of 117 answers were valid JSON with one empty entry, and
counting them would weaken the 2-of-3 rule; the gate retries such a reading once.
"""

import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from verifier_gate.data import labels
from verifier_gate.dsl.grammar import Claim
from verifier_gate.dsl.parse import DSLError, parse
from verifier_gate.facts.local import LocalFacts
from verifier_gate.facts.schema import Facts
from verifier_gate.llm import prompts, settings
from verifier_gate.llm.client import Request, Response

EXTRACTIONS = 3
EXTRACTION_SCHEMA = json.dumps(
    {
        "type": "object",
        "properties": {
            "sentences": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "claims": {"type": "array", "items": {"type": "string"}},
                        "unexpressed": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["id", "claims", "unexpressed"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["sentences"],
        "additionalProperties": False,
    },
    sort_keys=True,
)


@dataclass
class Extraction:
    claims: list[Claim]  # each with its sentence_id, in the Facts' names
    unexpressed: dict[int, list[str]] = field(default_factory=dict)  # sentence id: statements no DSL form expresses
    format_errors: list[str] = field(default_factory=list)


def features_text(facts: Facts | LocalFacts, names: Mapping[str, str] = labels.SYNTHETIC_NAMES,
                  descriptions: Mapping[str, str] = labels.SYNTHETIC_DESCRIPTIONS) -> str:  # fmt: skip
    """The features as the writer saw them, in the Facts' order (not by importance: the extractor does not see it)."""
    features = [v.feature for v in facts.values] if isinstance(facts, LocalFacts) else [f.name for f in facts.features]
    shown = [labels.shown(f, names) for f in features]
    return "\n".join(f'- "{name}": {descriptions.get(name, "")}'.rstrip(": ") for name in sorted(shown))


def extractor_request(sentences: list[tuple[int, str]] | list[list], features: str, draw: int = 0, replica: int = 0,
                      model: str = settings.EXTRACTOR, local: bool = False) -> Request:  # fmt: skip
    """local: a notice of the local spot check, read with the local extractor prompt."""
    text = "\n".join(f"{i}. {t}" for i, t in sentences)
    user = prompts.load("extract").replace("{features}", features).replace("{sentences}", text)
    system = prompts.extractor_system(local=local)
    return Request("extractor", model, system, (("user", user),), EXTRACTION_SCHEMA, draw=draw, replica=replica)


def extraction_from(response: Response | Mapping, sentence_ids: set[int], names: Mapping[str, str] = labels.SYNTHETIC_NAMES) -> Extraction:
    """The claims in a parsed answer (a response, or its JSON data). Raises ValueError if the answer is not an
    extraction, or leaves out a sentence of the text."""
    data = response.data if isinstance(response, Response) else response
    if not isinstance(data, dict) or not isinstance(data.get("sentences"), list):
        raise ValueError("the answer is not an extraction")
    if not sentence_ids <= {int(item["id"]) for item in data["sentences"]}:
        raise ValueError("the answer leaves out sentences of the text")
    out = Extraction([])
    for item in data["sentences"]:
        sentence_id = int(item["id"])
        if sentence_id not in sentence_ids:
            out.format_errors.append(f"sentence {sentence_id}: there is no sentence with this id")
            continue
        for line in (str(x).strip() for x in item.get("claims", [])):
            try:
                out.claims.append(labels.internal(parse(line, sentence_id=sentence_id), names))
            except DSLError as e:
                out.format_errors.append(f"sentence {sentence_id}: {line}: {e}")
        statements = [str(x).strip() for x in item.get("unexpressed", []) if str(x).strip()]
        if statements:
            out.unexpressed[sentence_id] = statements
    return out


def faithful_reading(request: Request, answers: Iterable[Mapping]) -> dict:
    """A stub extractor for tests and dry runs: reads each sentence of the request's text as exactly the claims a
    writer attached to the same sentence in one of `answers` (writer JSON answers), and nothing else."""
    by_text: dict[str, set[str]] = {}
    for answer in answers:
        texts = {s["id"]: s["text"].strip() for s in answer["sentences"]}
        for c in answer["claims"]:
            if c["sentence_id"] in texts:
                by_text.setdefault(texts[c["sentence_id"]], set()).add(c["dsl"])
    text = request.messages[0][1].split("The text, sentence by sentence:")[1]
    sentences = re.findall(r"^(\d+)\. (.*)$", text, re.M)
    return {"sentences": [{"id": int(i), "claims": sorted(by_text.get(t.strip(), set())), "unexpressed": []} for i, t in sentences]}
