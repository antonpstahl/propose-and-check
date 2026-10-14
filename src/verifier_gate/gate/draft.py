"""A draft: sentences with ids and the claims attached to them, from the writer (llm/propose.py) or from the
template (gate/template.py). Claims use the Facts' names; format errors are DSL lines that did not parse."""

from dataclasses import dataclass, field

from verifier_gate.dsl.grammar import Claim


@dataclass
class Draft:
    sentences: list[tuple[int, str]]  # (id, text)
    claims: list[Claim]  # each with its sentence_id
    format_errors: list[str] = field(default_factory=list)  # "sentence <id>: <line>: <parser message>"
    source: str = ""  # "writer", "repair <round>", "reduced", "template"

    @property
    def text(self) -> str:
        return " ".join(text for _, text in self.sentences)

    def ids(self) -> list[int]:
        return [i for i, _ in self.sentences]

    def without(self, ids: set[int], source: str) -> "Draft":
        """The draft with the given sentences and their claims dropped."""
        return Draft([(i, t) for i, t in self.sentences if i not in ids], [c for c in self.claims if c.sentence_id not in ids],
                     [], source)  # fmt: skip
