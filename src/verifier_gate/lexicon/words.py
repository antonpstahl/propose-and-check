"""The lexicon's words (D65, lexicon v3): the one source of the writer's rules for choosing words, the DSL table
that the writer and the extractor read, Table 1, and the template's phrases.

lexicon.yaml's `words` section holds them as text with {name} placeholders for the lexicon's numbers (NUMBERS):
no threshold is written by hand, so the prompt, the table and the verifier cannot disagree on one (minor issue 21
of the 20 Oct review: v2's prompt stated stricter rules than the verifier applied). A table row's words are the
template's phrases of its example claims, worded about the model (M10: "the model's predicted default risk
increases with x", not "x drives risk"); its DSL column is the example claims as written. Lexicon v2 has no words:
its prompts (v3) are stored text, and the template keeps v2's phrases (gate/template.py).
"""

from collections.abc import Callable
from functools import cache
from pathlib import Path

import yaml

from verifier_gate.dsl.grammar import HEDGE, Claim
from verifier_gate.lexicon import predicates as p

TABLE_HEADER = ("| Words in the text | DSL claim | Meaning |", "|---|---|---|")


def _pct(v: float) -> str:
    return f"{v:.1%}".replace(".0%", "%")


def numbers(lex: p.Lexicon) -> dict[str, str]:
    """The placeholders of the words, from the lexicon's numbers."""
    return {
        "weak": _pct(lex.strength["weak"]), "moderate": _pct(lex.strength["moderate"]), "strong": _pct(lex.strength["strong"]),
        "detectable": _pct(lex.detectable_mass), "share_points": f"{lex.share_absolute * 100:g}", "share_relative": _pct(lex.share_relative),
        "exception": _pct(lex.exception_mass), "margin": _pct(lex.direction_margin or 0.0), "jump": _pct(lex.jump_fraction),
        "pair_share": _pct(lex.pair_share), "window": _pct(lex.window), "level": _pct(lex.level),
    }  # fmt: skip


@cache
def _section(path: Path) -> dict | None:
    return yaml.safe_load(path.read_text()).get("words")


def section(lex: p.Lexicon | None = None) -> dict | None:
    """The words of a lexicon version, None for one without (v2)."""
    lex = lex or p.load()
    return _section(lex.source) if lex.source is not None else None


def _fill(text: str, lex: p.Lexicon) -> str:
    return " ".join(text.split()).format(**numbers(lex))


# --- phrases -----------------------------------------------------------------------------------------------


def ordinal(k: int) -> str:
    return {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth", 6: "sixth", 7: "seventh", 8: "eighth", 9: "ninth"}.get(k, f"{k}th")


def cardinal(k: int) -> str:
    return {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}.get(k, str(k))


def number(x: float) -> str:
    return f"{x:,.0f}" if abs(x) >= 1000 else f"{x:.3g}"


def share_text(v: float) -> str:
    return f"{v:.0%}" if v >= 0.095 else f"{v:.1%}"


def phrase(c: Claim, label: Callable[[str], str], lex: p.Lexicon | None = None) -> str:
    """A global claim as a clause of the template (no capital, no full stop), in the words of a lexicon with words.
    label: the feature's words in a sentence."""
    w = section(lex)
    if w is None:
        raise ValueError("this lexicon version has no words (v2: gate/template.py keeps its phrases)")
    forms = w["phrases"]
    if c.kind == HEDGE:
        return forms["hedge"].format(inner=phrase(c.inner, label, lex))
    t = [label(term) for term in c.terms]
    x, y = t[0], t[-1]
    match c.kind:
        case "strength" if isinstance(c.value, tuple):
            return forms["strength_set"].format(x=x, value=w["strength_sets"][" ".join(c.value)])
        case "strength":
            return forms["strength"].format(x=x, value=c.value)
        case "negligible":
            return forms["negligible"].format(x=x)
        case "rank" if isinstance(c.value, tuple):
            first, last = c.value[0], c.value[-1]
            if first == 1:
                return forms["rank_top"].format(x=x, last=cardinal(last))
            joined = f"{ordinal(first)} {'or' if last == first + 1 else 'to'} {ordinal(last)}"
            return forms["rank_set"].format(x=x, value=joined)
        case "rank":
            return forms["rank_first"].format(x=x) if c.value == 1 else forms["rank"].format(x=x, value=ordinal(c.value))
        case "share":
            return forms["share"].format(x=x, value=share_text(c.value))
        case "comparison":
            return forms["more" if c.relation == ">" else "less"].format(x=x, y=y)
        case "direction" if isinstance(c.value, tuple):
            return forms["direction_set"].format(x=x, value=w["directions"][c.value[0]])
        case "direction":
            return forms["direction"].format(x=x, value=w["directions"][c.value])
        case "threshold" | "drop" | "peak":
            return forms[c.kind].format(x=x, value=number(c.value))
        case "interaction":
            return forms[c.value].format(x=x, y=y)
    raise ValueError(f"no phrase for {c}")


# --- the writer's rules and the DSL table ----------------------------------------------------------------


def rules(lex: p.Lexicon | None = None) -> str:
    """The writer's rules for choosing words, as the bullets of "# Choosing the words"."""
    lex = lex or p.load()
    return "\n".join(f"- **{r['name']}.** {_fill(r['text'], lex)}" for r in section(lex)["rules"])


def table_rows(lex: p.Lexicon | None = None) -> list[tuple[str, str, str]]:
    """The DSL table: (words in the text, DSL claim, meaning) per claim form; the words are the template's phrases
    of the row's example claims, with x and y as the terms."""
    from verifier_gate.dsl.parse import parse  # parse reads the lexicon version too

    lex = lex or p.load()
    out = []
    for row in section(lex)["table"]:
        if "claims" in row:
            words = " / ".join(f'"{phrase(parse(line), str, lex)}"' for line in row["claims"])
            dsl = " / ".join(f"`{line}`" for line in row["claims"])
        else:
            words, dsl = row["words"], row["dsl"]
        out.append((words, dsl, _fill(row["meaning"], lex)))
    return out


def table(lex: p.Lexicon | None = None) -> str:
    return "\n".join([*TABLE_HEADER, *(f"| {w} | {d} | {m} |" for w, d, m in table_rows(lex))])
