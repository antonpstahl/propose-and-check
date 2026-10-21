"""The plain-prompt writer (E3's baselines, M4 of the 20 Oct review): what a bank gets without the gate.

The same writer model and settings as E3's, the same facts (the handover H1), and the writer's own role and rules
for the text, without anything the gate adds: no lexicon rules for choosing words, no DSL, no plan of claims, no
certified statements, no verifier, round trip or repair (llm/prompts, plain_system.md and plain.md, frozen as p1).
It answers with the sentences only, each with an id, so that the scoring readings can read it like any other text.
"""

import json

from verifier_gate.llm import prompts, settings
from verifier_gate.llm.client import Request, Response

PLAIN_SCHEMA = json.dumps(
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
        },
        "required": ["sentences"],
        "additionalProperties": False,
    },
    sort_keys=True,
)


def plain_request(handover: str, model: str = settings.WRITER, draw: int = 0, attempt: int = 0) -> Request:
    user = prompts.load("plain").format(handover=handover)
    return Request("plain writer", model, prompts.load("plain_system"), (("user", user),), PLAIN_SCHEMA, settings.EFFORT, settings.THINKING,
                   draw=draw, attempt=attempt)  # fmt: skip


def sentences_from(response: Response) -> list[list]:
    """The text in a parsed answer, as [id, text] sentences. Raises ValueError if the answer is not a text."""
    data = response.data
    if response.error or not isinstance(data, dict) or not isinstance(data.get("sentences"), list):
        raise ValueError(f"the answer is not a text ({response.error or 'no sentences'})")
    sentences = [[int(s["id"]), str(s["text"]).strip()] for s in data["sentences"]]
    if not sentences or any(not t for _, t in sentences) or len({i for i, _ in sentences}) != len(sentences):
        raise ValueError("the answer is an empty text, has an empty sentence or repeats an id")
    return sentences
