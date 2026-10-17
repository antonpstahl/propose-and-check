"""Template text from verified facts and fixed lexicon sentences: the gate's last exit before ESCALATE, and a
baseline (§5.8). Also the words for H2's statements in the handover.

`phrase` turns one DSL claim into a fixed English clause built only from the lexicon's words, one form per claim
type and value. `template` builds a text from the certified plan (verifier/certified.py): per feature, in the
order of M's shares, its strength (or "hardly matters") and its direction, then its threshold or peak if
certified; per pair, its certified pattern; then the hedges. Every claim in it is certified, so it passes the plan
check by construction; the gate verifies it anyway, and if it fails there is a bug, which is why ESCALATE exists.

For a notice of the local spot check (`notice_template`, D49): one sentence per certified principal reason, in the
order of M's contributions, with its certified reason rank and, for a feature, how its value compares with the
comparable approved applicants. A pair is "the combination of a and b".
"""

from collections.abc import Callable, Mapping

from verifier_gate.data import labels
from verifier_gate.dsl.grammar import HEDGE, LOCAL_KINDS, Claim
from verifier_gate.facts.local import LocalFacts
from verifier_gate.facts.schema import Facts
from verifier_gate.facts.steps import PAIR_SEPARATOR
from verifier_gate.gate.draft import Draft
from verifier_gate.gate.roundtrip import PAIR_SHARE

STRENGTH_SETS = {
    ("negligible", "weak"): "at most a weak effect",
    ("negligible", "weak", "moderate"): "at most a moderate effect",
    ("weak", "moderate"): "a weak to moderate effect",
    ("moderate", "strong"): "a moderate to strong effect",
    ("weak", "moderate", "strong"): "at least a weak effect",
}
DIRECTION_WORDS = {
    "increasing": "increases", "decreasing": "decreases",
    "mostly_increasing": "mostly increases", "mostly_decreasing": "mostly decreases",
}  # fmt: skip


def ordinal(k: int) -> str:
    return {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth", 6: "sixth", 7: "seventh", 8: "eighth", 9: "ninth"}.get(k, f"{k}th")


def _number(x: float) -> str:
    return f"{x:,.0f}" if abs(x) >= 1000 else f"{x:.3g}"


def _share(v: float) -> str:
    return f"{v:.0%}" if v >= 0.095 else f"{v:.1%}"


def phrase(c: Claim, label: Callable[[str], str]) -> str:
    """One claim as a clause (no capital, no full stop). label: the feature's words in a sentence."""
    if c.kind == HEDGE:
        return f"the data do not settle whether {phrase(c.inner, label)}"
    t = [label(term) for term in c.terms]
    match c.kind:
        case "strength" if isinstance(c.value, tuple):
            return f"{t[0]} has {STRENGTH_SETS[c.value]} on default risk"
        case "strength":
            return f"{t[0]} has a {c.value} effect on default risk"
        case "negligible":
            return f"{t[0]} hardly matters for default risk"
        case "rank" if isinstance(c.value, tuple):
            first, last = c.value[0], c.value[-1]
            if first == 1:
                return f"{t[0]} is among the {last} most important features"
            return f"{t[0]} is the {ordinal(first)} to {ordinal(last)} most important feature"
        case "rank":
            return f"{t[0]} is the most important feature" if c.value == 1 else f"{t[0]} is the {ordinal(c.value)} most important feature"
        case "share":
            return f"{t[0]} accounts for about {_share(c.value)} of the model's importance"
        case "comparison":
            return f"{t[0]} matters more than {t[1]}" if c.relation == ">" else f"{t[0]} matters less than {t[1]}"
        case "direction" if isinstance(c.value, tuple):
            return f"default risk generally {DIRECTION_WORDS[c.value[0]]} with {t[0]}"
        case "direction":
            return f"default risk {DIRECTION_WORDS[c.value]} with {t[0]}"
        case "threshold":
            return f"default risk jumps at {t[0]} = {_number(c.value)}"
        case "peak":
            return f"default risk peaks at {t[0]} = {_number(c.value)}"
        case "interaction" if c.value == "amplification":
            return f"the effect of {t[0]} grows with {t[1]}"
        case "interaction" if c.value == "sign_flip":
            return f"the effect of {t[0]} reverses its sign as {t[1]} changes"
        case "interaction":
            return f"{t[0]} and {t[1]} do not interact"
        case "principal_reason":
            return f"{t[0]} is a principal reason for the decision"
        case "reason_rank" if isinstance(c.value, tuple):
            first, last = c.value[0], c.value[-1]
            if first == 1:
                return f"{t[0]} is among the {last} main reasons for the decision"
            return f"{t[0]} is the {ordinal(first)} to {ordinal(last)} reason for the decision"
        case "reason_rank":
            return f"{t[0]} is the main reason for the decision" if c.value == 1 else f"{t[0]} is the {ordinal(c.value)} reason for the decision"
        case "higher_than_reference":
            return f"{t[0]} is higher than for comparable approved applicants"
        case "lower_than_reference":
            return f"{t[0]} is lower than for comparable approved applicants"
    raise ValueError(f"no phrase for {c}")


def sentence(clauses: list[str]) -> str:
    text = "; ".join(clauses)
    return text[0].upper() + text[1:] + "."


def synthetic_label(names: Mapping[str, str] = labels.SYNTHETIC_NAMES) -> Callable[[str], str]:
    return lambda term: labels.SYNTHETIC_LABELS.get(labels.shown(term, names), labels.shown(term, names))


def plasmode_label(term: str) -> str:
    """A TaiwanCredit column in a sentence (D54): its plain words, or the code if it has none."""
    return labels.PLASMODE_LABELS.get(term, term)


def notice_template(lf: LocalFacts, certified: list[Claim], label: Callable[[str], str] | None = None) -> Draft:
    label = label or synthetic_label()

    def term_label(term: str) -> str:
        parts = term.split(PAIR_SEPARATOR)
        return f"the combination of {label(parts[0])} and {label(parts[1])}" if len(parts) == 2 else label(term)

    order = {"principal_reason": 0, "reason_rank": 1, "higher_than_reference": 2, "lower_than_reference": 2}
    sentences, claims = [], []
    for r in lf.reasons:
        key = set(r.term.split(PAIR_SEPARATOR))
        group = sorted((c for c in certified if c.kind in LOCAL_KINDS and set(c.terms[0].split(PAIR_SEPARATOR)) == key), key=lambda c: order[c.kind])
        if not any(c.kind == "principal_reason" for c in group):
            continue
        k = len(sentences) + 1
        sentences.append((k, sentence([phrase(c, term_label) for c in group])))
        claims.extend(Claim(c.kind, c.terms, c.value, c.relation, k, c.inner) for c in group)
    return Draft(sentences, claims, [], "template")


def template(facts: Facts | LocalFacts, certified: list[Claim], label: Callable[[str], str] | None = None) -> Draft:
    """The template draft from the certified plan. Claims keep the Facts' names. It covers what the coverage
    check asks (§5.7): every feature gets its strength and direction, else its rank or share, else its hedge; every
    pair with a share of at least 10% gets its certified pattern, else its "none" or its hedge."""
    if isinstance(facts, LocalFacts):
        return notice_template(facts, certified, label)
    label = label or synthetic_label()
    sentences, claims = [], []

    def add(group: list[Claim]) -> None:
        if group:
            k = len(sentences) + 1
            sentences.append((k, sentence([phrase(c, label) for c in group])))
            claims.extend(Claim(c.kind, c.terms, c.value, c.relation, k, c.inner) for c in group)

    def about(terms: tuple[str, ...], kinds: tuple[str, ...]) -> list[Claim]:
        return [c for c in certified if c.kind in kinds and set(c.terms) == set(terms)]

    by_share = sorted((f.name for f in facts.features), key=lambda n: -facts.feature(n).share.value)
    for name in by_share:
        group = about((name,), ("strength", "negligible")) + about((name,), ("direction",))
        group = group or about((name,), ("rank",))[:1] or about((name,), ("share",))[:1] or about((name,), (HEDGE,))
        add(group)
        add(about((name,), ("threshold", "peak")))
    dominant = [pair.features for pair in facts.pairs if pair.share.value >= PAIR_SHARE]
    for c in certified:
        if c.kind == "interaction" and c.value != "none":
            add([c])
    for pair in dominant:
        if not [c for c in about(pair, ("interaction",)) if c.value != "none"]:
            add(about(pair, ("interaction",))[:1] or about(pair, (HEDGE,)))
    return Draft(sentences, claims, [], "template")
