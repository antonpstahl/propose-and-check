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

Sets of values (D33): a tuple after `in`, stored in the order below.

| kind        | form                                                         | value                              |
|-------------|--------------------------------------------------------------|------------------------------------|
| rank        | rank("t") in (2, 3)                                          | two or more consecutive ranks      |
| direction   | direction("t") in ("decreasing", "mostly_decreasing")        | a strict word and its "mostly" word |
| strength    | strength("t") in ("negligible", "weak")                      | two or more neighbouring CLASSES, not all four |

The hedge (D30): unsettled(<claim>), where <claim> is any form above; it covers the terms of its claim.

Terms are strings: a feature, or a pair "a & b" where the claim type allows it (share, strength, negligible,
comparison). Nothing outside these tables parses.
"""

from dataclasses import dataclass

from verifier_gate.lexicon.predicates import CLASSES, DIRECTIONS, PATTERNS, STRENGTHS

__all__ = ["CALLS", "CLASSES", "COMPARED", "DIRECTIONS", "HEDGE", "KINDS", "PATTERNS", "RELATIONS", "SETS", "STRENGTHS", "Claim"]

KINDS = ("rank", "share", "direction", "strength", "negligible", "comparison", "threshold", "peak", "interaction", "unsettled")
COMPARED = {"rank": int, "share": float, "direction": DIRECTIONS, "strength": STRENGTHS}  # f("t") == value
SETS = ("rank", "direction", "strength")  # f("t") in (values)
CALLS = {"negligible": (1, ()), "threshold": (1, ("at",)), "peak": (1, ("at",)), "interaction": (2, ("pattern",))}
HEDGE = "unsettled"
RELATIONS = (">", "<")


@dataclass(frozen=True)
class Claim:
    kind: str
    terms: tuple[str, ...]
    value: int | float | str | tuple | None = None  # rank, share, direction, strength, location, pattern; a tuple: a set
    relation: str | None = None  # comparison only
    sentence_id: int | None = None
    inner: "Claim | None" = None  # unsettled only: the claim the data do not settle

    def __str__(self) -> str:
        """The canonical DSL line."""
        t = [f'"{term}"' for term in self.terms]
        if self.kind == HEDGE:
            return f"{HEDGE}({self.inner})"
        if isinstance(self.value, tuple):
            values = ", ".join(f'"{v}"' if isinstance(v, str) else str(v) for v in self.value)
            return f"{self.kind}({t[0]}) in ({values})"
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
