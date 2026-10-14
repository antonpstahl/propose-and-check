"""Proposer: text plus claim plan from a symbolic handover (H1 facts, H2 facts plus the certified statements).

The writer answers in one JSON object (D40): `sentences` ({id, text}) and `claims` ({sentence_id, dsl}). The API
enforces the JSON shape; the DSL lines are ours, so each goes through the `ast` parser, and a line that does not
parse, or names a sentence that does not exist, is a format error kept with the draft. The writer's names for
features are mapped back to the Facts' names (data/labels.py) before anything is verified.

Repair and format-only retries continue the same conversation: the writer's previous answer, then the problems.
"""

import json
from collections.abc import Mapping

from verifier_gate.data import labels
from verifier_gate.dsl.parse import DSLError, parse
from verifier_gate.gate.draft import Draft
from verifier_gate.llm import prompts, settings
from verifier_gate.llm.client import Request, Response

DRAFT_SCHEMA = json.dumps(
    {
        "type": "object",
        "properties": {
            "sentences": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"id": {"type": "integer"}, "text": {"type": "string"}},
                    "required": ["id", "text"],
                    "additionalProperties": False,
                },
            },
            "claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"sentence_id": {"type": "integer"}, "dsl": {"type": "string"}},
                    "required": ["sentence_id", "dsl"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["sentences", "claims"],
        "additionalProperties": False,
    },
    sort_keys=True,
)


def proposer_request(handover: str, model: str = settings.WRITER, draw: int = 0, effort: str = settings.EFFORT,
                     thinking: str = settings.THINKING) -> Request:  # fmt: skip
    user = prompts.load("propose").format(handover=handover)
    return Request("proposer", model, prompts.load("system"), (("user", user),), DRAFT_SCHEMA, effort, thinking, draw=draw)


def follow_up(previous: Request, answer: str, message: str, role: str) -> Request:
    """The next turn of the same conversation: the writer's answer, then our message."""
    messages = previous.messages + (("assistant", answer), ("user", message))
    return Request(role, previous.model, previous.system, messages, previous.schema, previous.effort, previous.thinking,
                   previous.max_tokens, previous.draw)  # fmt: skip


def repair_request(previous: Request, answer: str, problems: str, round_: int) -> Request:
    return follow_up(previous, answer, prompts.load("repair").format(problems=problems), f"repair {round_}")


def draft_from(response: Response, source: str, names: Mapping[str, str] = labels.SYNTHETIC_NAMES) -> Draft:
    """The draft in a parsed answer. Raises ValueError if the answer is not a draft at all."""
    data = response.data
    if not isinstance(data, dict) or not isinstance(data.get("sentences"), list) or not isinstance(data.get("claims"), list):
        raise ValueError("the answer is not a draft")
    if not data["sentences"]:
        raise ValueError("the answer is an empty draft")  # seen in the pilot: valid JSON with nothing in it
    sentences = [(int(s["id"]), str(s["text"]).strip()) for s in data["sentences"]]
    ids = {i for i, _ in sentences}
    claims, errors = [], []
    for item in data["claims"]:
        sentence_id, line = int(item["sentence_id"]), str(item["dsl"]).strip()
        if sentence_id not in ids:
            errors.append(f"sentence {sentence_id}: {line}: there is no sentence with this id")
            continue
        try:
            claims.append(labels.internal(parse(line, sentence_id=sentence_id), names))
        except DSLError as e:
            errors.append(f"sentence {sentence_id}: {line}: {e}")
    return Draft(sentences, claims, errors, source)
