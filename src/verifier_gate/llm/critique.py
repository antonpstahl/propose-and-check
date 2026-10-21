"""The LLM critic (D56, plan §14.29): the baseline a model-risk team asks for first ("why not let another LLM check
it?").

The critic gets what the writer got, the facts in readable form (the handover H1) and the writer's rules for
choosing words, together with the round trip's coverage and emphasis rules (llm/prompts, critic_system.md), and the
text sentence by sentence. It answers with the sentences it finds unsupported, each with a short reason, and its
probability that the text states something the facts do not support. A text is blocked if the critic names a
problem; the probability is kept for the question whether its confidence means anything (a confident critic that
is wrong). It is another vendor's model (settings.CRITIC), so it does not share the writer's model family.

Versions (llm/prompts): c1 gets the writer's rules for choosing words; c2 the writer's whole set of rules with the
DSL table; c3 (D79) the same from writer prompt v4, as D74's writer got it. Which facts it gets is the caller's choice
(experiments/e2_critic.py: H1 for c1, the writer's own handover for c2 and c3).
"""

import json
from dataclasses import dataclass, field

from verifier_gate.llm import prompts, settings
from verifier_gate.llm.client import Request, Response

CRITIQUE_SCHEMA = json.dumps(
    {
        "type": "object",
        "properties": {
            "problems": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"sentence_id": {"type": "integer"}, "problem": {"type": "string"}},
                    "required": ["sentence_id", "problem"],
                    "additionalProperties": False,
                },
            },
            "p_error": {"type": "number"},
        },
        "required": ["problems", "p_error"],
        "additionalProperties": False,
    },
    sort_keys=True,
)
WHOLE_TEXT = 0  # the sentence id of a problem with the whole text: a feature or pair it fails to mention


@dataclass
class Critique:
    problems: dict[int, list[str]] = field(default_factory=dict)  # sentence id (0: the whole text): the critic's reasons
    p_error: float = float("nan")

    @property
    def blocks(self) -> bool:
        return bool(self.problems)


def critic_request(facts_text: str, sentences: list[tuple[int, str]] | list[list], model: str = settings.CRITIC, draw: int = 0,
                   version: str = prompts.CRITIC_VERSION) -> Request:  # fmt: skip
    text = "\n".join(f"{i}. {t}" for i, t in sentences)
    user = prompts.load(prompts.CRITIC_NAMES[version][1]).replace("{facts}", facts_text).replace("{sentences}", text)
    return Request("critic", model, prompts.critic_system(version), (("user", user),), CRITIQUE_SCHEMA, effort=settings.CRITIC_EFFORT,
                   max_tokens=settings.CRITIC_MAX_TOKENS, draw=draw)  # fmt: skip


def critique_from(response: Response, sentence_ids: set[int]) -> Critique:
    """The critique in a parsed answer. Raises ValueError if the answer is not a critique. A problem at a sentence id
    the text does not have is kept with the whole text (id 0): the critic still blocks."""
    data = response.data
    if not isinstance(data, dict) or not isinstance(data.get("problems"), list) or not isinstance(data.get("p_error"), int | float):
        raise ValueError("the answer is not a critique")
    out = Critique(p_error=min(max(float(data["p_error"]), 0.0), 1.0))
    for item in data["problems"]:
        sid = int(item["sentence_id"])
        out.problems.setdefault(sid if sid in sentence_ids else WHOLE_TEXT, []).append(str(item["problem"]).strip())
    return out
