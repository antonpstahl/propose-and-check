"""Whitelist of DSL function names, keyword names and literal types (§5.2), and the Claim they parse into.

The eight claim types, one line each:

| kind        | form                                                         | value                              |
|-------------|--------------------------------------------------------------|------------------------------------|
| rank        | rank("t") == k                                               | k, an int >= 1                     |
| share       | share("t") == approx(v)                                      | v, a number in [0, 1]              |
| direction   | direction("t") == "increasing"                               | one of DIRECTIONS                  |
| strength    | strength("t") == "weak"                                      | one of STRENGTHS                   |
| negligible  | negligible("t")                                              |                                    |
| comparison  | effect("a") > effect("b")                                    | relation, ">" or "<"               |
| threshold   | threshold("t", at=x)  /  peak("t", at=x)                     | x, a number                        |
| interaction | interaction("a", "b", pattern="amplification")               | one of PATTERNS                    |

Terms are strings: a feature, or a pair "a & b" where the claim type allows it (share, strength, negligible,
comparison). Nothing outside this table parses.
"""

from dataclasses import dataclass

from verifier_gate.lexicon.predicates import DIRECTIONS, PATTERNS, STRENGTHS

__all__ = ["CALLS", "COMPARED", "DIRECTIONS", "KINDS", "PATTERNS", "RELATIONS", "STRENGTHS", "Claim"]

KINDS =("rank", "share", "direction", "strength", "negligible", "comparison", "threshold", "peak", "interaction")
COMPARED = {"rank": int, "share": float, "direction": DIRECTIONS, "strength": STRENGTHS}  # f("t") == value
CALLS = {"negligible": (1, ()), "threshold": (1, ("at",)), "peak": (1, ("at",)), "interaction": (2, ("pattern",))}
RELATIONS = (">", "<")


@dataclass(frozen=True)
class Claim:
    kind: str
    terms: tuple[str, ...]
    value: int | float | str | None = None  # rank, share, direction, strength, location or pattern
    relation: str | None = None  # comparison only
    sentence_id: int | None = None

    def __str__(self) -> str:
        """The canonical DSL line."""
        t = [f'"{term}"' for term in self.terms]
        if self.kind == "share":
            return f"share({t[0]}) == approx({self.value})"
        if self.kind in COMPARED:
            value = f'"{self.value}"' if isinstance(self.value, str) else self.value
            return f"{self.kind}({t[0]}) == {value}"
        if self.kind == "negligible":
            return f"negligible({t[0]})"
        if self.kind == "comparison":
            return f"effect({t[0]}) {self.relation} effect({t[1]})"
        if self.kind in ("threshold", "peak"):
            return f"{self.kind}({t[0]}, at={self.value})"
        return f'interaction({t[0]}, {t[1]}, pattern="{self.value}")'
