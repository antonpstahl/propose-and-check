"""Round-trip check: three extractions, plan-text comparison, coverage and emphasis (§5.7).

Coverage (§5.7, item 3) needs no LLM and also runs on plans (E2's omission mutants). The top 3 terms by M's share
and every pair with a share of at least 10% must be mentioned. A set covers its term (D33); a hedge
unsettled(<claim>) covers a term only if nothing about the term is certified, and then it raises the
limited-evidence flag (D30): released, but marked for a reviewer.

The comparison (§5.7, items 1 to 4; D44 and D45, decided 15 Oct) takes the extractor's EXTRACTIONS readings of a
text (llm/extract.py) and the plan of that text, every claim of which the verifier has certified. Claims are
compared by their canonical DSL line. A claim counts as extracted if at least EXTRACTED readings find it.
- Fails (repaired like a failing claim): an extracted claim that is not in the plan and that the verifier does
  not certify, false or undecidable (D30: never released as stated), in the sentence most readings put it in; a
  sentence with content no DSL form expresses, in at least EXTRACTED readings: it cannot be checked, so it is
  treated like an undecidable claim if it states a number (D44 b as revised after the round-trip pilot: a digit in
  the statement; the rest is flagged, below); a required term the text does not cover, counted on what the text
  states, the extracted claims that are planned or certified (D44 a: a plan claim the reader never sees covers
  nothing); and an opening sentence that leads with a minor term (emphasis).
- Flagged, logged and counted, not blocking: a plan claim the text does not state (fewer than EXTRACTED readings
  find it), a claim only one reading finds (an ambiguous sentence), and content no DSL form expresses that states
  no number (the expressivity gap).
Emphasis: the opening sentence (the first with a claim) must not mention a term with a share below the moderate
edge (weak or negligible) unless it also mentions a strong term (share at the strong edge or above), when the
model has one. Shares are M's point estimates: emphasis is about prominence, not certification. A stronger word
for a weak term needs no rule of its own: its claim is false.

Unknown terms (M5 of the 20 Oct review; `unknown_terms`): a feature name the model does not have is compared in a
normal form (lower case, no leading "the", spaces, hyphens and underscores as one underscore), and becomes the
model's feature whose name has that form, if one does, so that readings which spell a name differently agree on
it. A claim on a feature the model still does not have then fails if one reading finds it: x4 mostly writes an
invented feature as a claim in one reading and as content without a DSL form in the others. Re-scored offline from
the cached x4 readings, the rule caught 91% of E2's invented-feature mutants instead of 85% (plasmode 87% instead
of 75%) and blocked none of the template texts. E2 and E3 ran without it; the experiments that replay them turn it
off.

A notice of the local spot check (facts/local.LocalFacts; D49, D53, D68): the required terms are M's principal
reasons on its exact contributions, all of them (Regulation B asks for the principal reasons), and a term is
covered by a reason claim (principal_reason, reason_rank), not by a wording claim alone; a hedge covers nothing.
Emphasis is not checked: the order of the reasons is what reason_rank claims state, and those are verified. A
sentence with hedged wording ("the data do not settle whether ...", HEDGED) fails, whatever the readings say: the
verifier refutes every hedge in a notice, and this catches the wording without the extractor.
"""

import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace

from verifier_gate.dsl.grammar import HEDGE, Claim
from verifier_gate.facts.local import LocalFacts
from verifier_gate.facts.schema import Facts
from verifier_gate.facts.steps import PAIR_SEPARATOR
from verifier_gate.lexicon import local as lp
from verifier_gate.lexicon import predicates as p
from verifier_gate.lexicon.predicates import TRUE
from verifier_gate.verifier.verify import evidence_text, verify

TOP_TERMS = 3
PAIR_SHARE = 0.10
EXTRACTED = 2  # of llm/extract.EXTRACTIONS readings
REASON_KINDS = ("principal_reason", "reason_rank")  # the claims that state a reason in a notice
NUMBER = re.compile(r"\d")  # a statement with a number: digits, a percentage, an amount (the extractor keeps them as written)
HEDGED = re.compile(r"\b(?:do|does|did) not settle\b|\bunsettled\b", re.IGNORECASE)  # banned in a notice (D68)


@dataclass(frozen=True)
class Coverage:
    required: tuple[frozenset, ...]
    missing: tuple[frozenset, ...]
    hedged_only: tuple[frozenset, ...]  # covered by hedges alone: the limited-evidence flag

    @property
    def passed(self) -> bool:
        return not self.missing

    @property
    def flagged(self) -> bool:
        return bool(self.hedged_only)


def term_key(name: str) -> frozenset:
    """A feature or a pair ("a & b", either order) as the set of its features."""
    return frozenset(s.strip() for s in name.split(PAIR_SEPARATOR.strip()))


def claim_terms(claim: Claim) -> set[frozenset]:
    """The terms a claim is about: an interaction is about its pair, a comparison about both features."""
    if claim.kind == HEDGE:
        return claim_terms(claim.inner)
    if claim.kind == "interaction":
        return {frozenset(claim.terms)}
    return {term_key(t) for t in claim.terms}


def required_terms(facts: Facts | LocalFacts) -> tuple[frozenset, ...]:
    if isinstance(facts, LocalFacts):  # every principal reason under M, in the order of M's contributions
        return tuple(term_key(t) for t in lp.principal_reasons(facts))
    shares = {frozenset([f.name]): f.share.value for f in facts.features}
    shares |= {frozenset(q.features): q.share.value for q in facts.pairs}
    top = sorted(shares, key=lambda k: -shares[k])[:TOP_TERMS]
    pairs = [k for k, s in shares.items() if len(k) == 2 and s >= PAIR_SHARE and k not in top]
    return tuple(top + sorted(pairs, key=lambda k: -shares[k]))


def coverage(claims: Iterable[Claim], facts: Facts, certified: Iterable[Claim]) -> Coverage:
    """certified: what the verifier certifies about the model (verifier/certified.py), to decide whether a hedge
    may cover a term."""
    claims = list(claims)
    if isinstance(facts, LocalFacts):
        claims = [c for c in claims if c.kind in REASON_KINDS]
        certified = [c for c in certified if c.kind in REASON_KINDS]
    stated = set().union(*(claim_terms(c) for c in claims if c.kind != HEDGE))
    hedged = set().union(*(claim_terms(c) for c in claims if c.kind == HEDGE))
    settled = set().union(*(claim_terms(c) for c in certified if c.kind != HEDGE))
    required = required_terms(facts)
    hedge_covers = {k for k in hedged if k not in settled}
    missing = tuple(k for k in required if k not in stated and k not in hedge_covers)
    hedged_only = tuple(k for k in required if k not in stated and k in hedge_covers)
    return Coverage(required, missing, hedged_only)


# --- the comparison of the text with its plan -------------------------------------------------------------


def canonical(claim: Claim) -> str:
    """The line a claim is compared by: its DSL line, with the features of a pair in a fixed order. An
    interaction keeps its order (the effect of the first feature, moderated by the second)."""
    if claim.kind == HEDGE:
        return f"{HEDGE}({canonical(claim.inner)})"
    terms = claim.terms if claim.kind == "interaction" else tuple(PAIR_SEPARATOR.join(sorted(term_key(t))) for t in claim.terms)
    return str(Claim(claim.kind, terms, claim.value, claim.relation))


def feature_names(facts: Facts | LocalFacts) -> set[str]:
    return {v.feature for v in facts.values} if isinstance(facts, LocalFacts) else {f.name for f in facts.features}


def normal_name(name: str) -> str:
    """A feature name in its normal form: "The savings-balance" -> "savings_balance"."""
    return re.sub(r"[\s_-]+", "_", re.sub(r"^the[\s_-]+", "", name.strip().lower()))


def _parts(term: str) -> list[str]:
    return [s.strip() for s in term.split(PAIR_SEPARATOR.strip())]


def normalised(claim: Claim, features: set[str]) -> Claim:
    """The claim with each feature name the model does not have in its normal form, or as the model's feature
    whose name has that form (module docstring, unknown terms)."""
    if claim.kind == HEDGE:
        return replace(claim, inner=normalised(claim.inner, features))
    by_form = {normal_name(f): f for f in features}
    one = lambda s: s if s in features else by_form.get(normal_name(s), normal_name(s))  # noqa: E731
    terms = tuple(t if all(s in features for s in _parts(t)) else PAIR_SEPARATOR.join(map(one, _parts(t))) for t in claim.terms)
    return replace(claim, terms=terms)


def unknown(claim: Claim, features: set[str]) -> bool:
    """The claim names a feature the model does not have."""
    inner = claim.inner if claim.kind == HEDGE else claim
    return any(s not in features for t in inner.terms for s in _parts(t))


@dataclass
class RoundTrip:
    readings: int  # extractions that could be read
    extracted: list = field(default_factory=list)  # [sentence id, line, readings that found it], at least EXTRACTED
    unplanned: list = field(default_factory=list)  # [sentence id, line, verdict, code, reason, evidence]: extracted, or on an unknown term, not planned
    plan_only: list = field(default_factory=list)  # [sentence id, line]: planned, not extracted
    ambiguous: list = field(default_factory=list)  # [sentence id, line]: found by one reading only
    gap: list = field(default_factory=list)  # [sentence id, statements no DSL form expresses]
    numbers: list = field(default_factory=list)  # [sentence id, such statements with a number]: these fail
    hedged: list = field(default_factory=list)  # [sentence id, the hedged words]: a notice's sentences that hedge; these fail
    missing: list = field(default_factory=list)  # required terms the text does not cover
    emphasis: list = field(default_factory=list)  # [sentence id, minor terms, strong terms]
    format_errors: int = 0  # DSL lines of the readings that did not parse

    def failures(self) -> list[str]:
        """What blocks the text: the failing lines (the same key space as the plan's, so a statement that failed as
        a claim and comes back in the text without one is no progress) and the emphasis problem."""
        keys = [line for _, line, value, *_ in self.unplanned if value != TRUE]
        keys += [f"unchecked number: sentence {sid}" for sid, _ in self.numbers] + [f"not covered by the text: {term}" for term in self.missing]
        keys += [f"hedged wording: sentence {sid}" for sid, _ in self.hedged]
        return keys + [f"emphasis: sentence {sid}" for sid, *_ in self.emphasis]

    @property
    def passed(self) -> bool:
        return not self.failures()

    def failing_sentences(self) -> set[int]:
        """The sentences to drop if repairs end: a missing term is in no sentence."""
        failing = {sid for sid, _, value, *_ in self.unplanned if value != TRUE} | {sid for sid, _ in self.numbers}
        failing |= {sid for sid, _ in self.hedged}
        return failing | {sid for sid, *_ in self.emphasis}


def _shares(facts: Facts) -> dict[frozenset, float]:
    return {frozenset([f.name]): f.share.value for f in facts.features} | {frozenset(q.features): q.share.value for q in facts.pairs}


def emphasis(order: Sequence[int], mentions: dict[int, set[frozenset]], facts: Facts, lex: p.Lexicon) -> list:
    """The opening sentence's emphasis problem, if any: [sentence id, minor terms, strong terms]."""
    if isinstance(facts, LocalFacts):
        return []
    opening = next((sid for sid in order if mentions.get(sid)), None)
    if opening is None:
        return []
    shares = _shares(facts)
    strong = sorted((k for k, v in shares.items() if v >= lex.strength["strong"]), key=lambda k: -shares[k])
    minor = sorted((k for k in mentions[opening] if shares.get(k, 0.0) < lex.strength["moderate"]), key=lambda k: shares.get(k, 0.0))
    if not strong or not minor or mentions[opening] & set(strong):
        return []
    names = lambda keys: [PAIR_SEPARATOR.join(sorted(k)) for k in keys]  # noqa: E731
    return [[opening, names(minor), names(strong)]]


def compare(readings: Sequence, plan: Iterable[Claim], order: Sequence[int], facts: Facts, certified: Iterable[Claim] = (),
            check_emphasis: bool = True, lex: p.Lexicon | None = None, texts: Mapping[int, str] | None = None,
            unknown_terms: bool = True) -> RoundTrip:  # fmt: skip
    """readings: the extractions that could be read (llm/extract.Extraction); plan: the text's certified claims,
    each with its sentence id; order: the text's sentence ids in order; certified: what the verifier certifies
    about the model (for the hedge rule of coverage); texts: the sentences by id, for a notice's hedged wording;
    unknown_terms: the rule on unknown terms (module docstring), off to replay E2 and E3 as they ran."""
    lex = lex or p.load()
    features = feature_names(facts)
    found, where, claims = Counter(), defaultdict(Counter), {}
    gap_votes, gap_words, number_votes = Counter(), defaultdict(list), Counter()
    for reading in readings:
        keys = set()
        for c in reading.claims:
            c = normalised(c, features) if unknown_terms else c
            key = canonical(c)
            where[key][c.sentence_id] += 1
            claims.setdefault(key, c)
            keys.add(key)
        found.update(keys)
        for sid, statements in reading.unexpressed.items():
            gap_votes[sid] += 1
            number_votes[sid] += any(NUMBER.search(s) for s in statements)
            gap_words[sid] += [s for s in statements if s not in gap_words[sid]]
    planned = {}
    for c in plan:
        planned.setdefault(canonical(c), c)
    sentence = {key: where[key].most_common(1)[0][0] for key in where}
    rt = RoundTrip(len(readings), format_errors=sum(len(r.format_errors) for r in readings))
    for key, n in sorted(found.items(), key=lambda kv: (sentence[kv[0]], kv[0])):
        if n < EXTRACTED and not (unknown_terms and unknown(claims[key], features)):  # an unknown term: one reading is enough
            rt.ambiguous.append([sentence[key], key])
            continue
        if n >= EXTRACTED:
            rt.extracted.append([sentence[key], key, n])
        if key not in planned:
            verdict = verify(claims[key], facts, lex)
            rt.unplanned.append([sentence[key], key, verdict.value, verdict.code, verdict.reason, evidence_text(verdict.evidence)])
    rt.plan_only = [[c.sentence_id, key] for key, c in planned.items() if found[key] < EXTRACTED]
    rt.gap = [[sid, gap_words[sid]] for sid in order if gap_votes[sid] >= EXTRACTED]
    rt.numbers = [[sid, [w for w in gap_words[sid] if NUMBER.search(w)]] for sid in order if number_votes[sid] >= EXTRACTED]
    if isinstance(facts, LocalFacts) and texts:
        rt.hedged = [[sid, m.group(0)] for sid in order if (m := HEDGED.search(texts.get(sid, "")))]
    true = {key for _, key, value, *_ in rt.unplanned if value == TRUE}
    stated = [claims[key] for _, key, _ in rt.extracted if key in planned or key in true]
    cover = coverage(stated, facts, certified)
    rt.missing = [PAIR_SEPARATOR.join(sorted(k)) for k in cover.missing]
    if check_emphasis:
        mentions = defaultdict(set)
        for c in planned.values():
            mentions[c.sentence_id] |= claim_terms(c)
        for sid, key, _ in rt.extracted:
            mentions[sid] |= claim_terms(claims[key])
        rt.emphasis = emphasis(order, mentions, facts, lex)
    return rt
