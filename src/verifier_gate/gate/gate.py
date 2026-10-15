"""Gate and repair loop with stop rules (§5.8): every run ends in RELEASED, RELEASED_REDUCED, TEMPLATE or ESCALATE.

The gate is a state machine that advances one LLM answer at a time: `start` returns a run with its first request
pending, `advance` takes the answer to the pending request and returns the run with its next request, or with an
exit state when it has ended. The run is plain data, saved as JSON after every step, so it can wait for a Batch API
result and an interrupted run resumes without repeating a paid call (every call is also cached by the client).
`run_sync` drives one run with a client.

Plan check: every claim is verified on M. A claim fails if its verdict is not true: false, or undecidable for any
reason (D30: never released as stated). A DSL line that does not parse fails too. Coverage (§5.7) must pass; a
top-3 term covered only by hedges raises the limited-evidence flag (released, marked for a reviewer).

Round trip (week 6, §5.7, gate/roundtrip.py): a text whose plan passes is read by the extractor three times, in
one step (three pending requests). A statement the text makes beyond its plan that the verifier does not certify,
or an opening sentence that leads with a minor term, fails like a failing claim: a repair round, or the drop step.
After dropping sentences the reduced text gets one round trip (emphasis not checked) and never a repair round;
if it fails, the template. Fewer than two readable extractions is a round trip that could not run: the template.
The template is not round-tripped: its sentences are fixed phrases of its claims. `Context.roundtrip` False skips
the round trip (the first-draft checks of the pilot, whose budget is one call).

Stop rules (§5.8): at most 2 repair rounds; no progress (a problem that failed in an earlier version fails again,
compared by gate/advice.problem_key: the claim's line, or one key for a jump or peak on a curve that has none)
stops repairing; a format problem (no valid JSON, truncated, or DSL lines that do not parse) gets one format-only
retry per text version; at most 16 calls per text; an API failure or a refusal (D39) ends the run as ESCALATE;
after dropping sentences no new repair round starts. The template is verified like any text; if it fails, that is
a bug, and the run ends as ESCALATE.
"""

import json
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path

from verifier_gate.data import labels
from verifier_gate.dsl.grammar import Claim
from verifier_gate.dsl.parse import parse
from verifier_gate.facts.schema import Facts
from verifier_gate.gate import template as templates
from verifier_gate.gate.draft import Draft
from verifier_gate.gate import advice as advising
from verifier_gate.gate import roundtrip as rt
from verifier_gate.gate.roundtrip import coverage
from verifier_gate.lexicon.predicates import TRUE
from verifier_gate.llm import extract, prompts, propose
from verifier_gate.llm.client import Client, Request, Response
from verifier_gate.verifier.verify import evidence_text, verify

RELEASED, RELEASED_REDUCED, TEMPLATE, ESCALATE = "RELEASED", "RELEASED_REDUCED", "TEMPLATE", "ESCALATE"
MAX_ROUNDS = 2
CALL_BUDGET = 16


@dataclass
class Context:
    """What the gate needs besides the run; not saved, rebuilt from the run's ids."""

    facts: Facts
    certified: list[Claim]
    names: Mapping[str, str] = field(default_factory=lambda: labels.SYNTHETIC_NAMES)
    label: Callable[[str], str] | None = None
    descriptions: Mapping[str, str] = field(default_factory=lambda: labels.SYNTHETIC_DESCRIPTIONS)
    roundtrip: bool = True


@dataclass
class Version:
    """One text version and its plan check."""

    source: str
    sentences: list[list]  # [id, text]
    claims: list[list]  # [sentence_id, DSL line in the Facts' names, verdict, code, reason, evidence]
    format_errors: list[str]
    missing: list[str]  # required terms not covered
    flagged: list[str]  # required terms covered only by hedges
    answer: str = ""  # the writer's JSON answer, for the next turn
    roundtrip: dict | None = None  # the round trip of this text (gate/roundtrip.RoundTrip), if it ran

    def failing(self) -> list[str]:
        return [c[1] for c in self.claims if c[2] != TRUE]

    def failing_sentences(self) -> set[int]:
        ids = {c[0] for c in self.claims if c[2] != TRUE}
        return ids | {int(e.split(":")[0].removeprefix("sentence ")) for e in self.format_errors}

    @property
    def passed(self) -> bool:
        return not self.failing() and not self.format_errors and not self.missing


@dataclass
class Run:
    run_id: str
    budget: int = CALL_BUDGET
    calls: int = 0
    rounds: int = 0
    format_retry_used: bool = False  # for the current text version
    pending: dict | None = None  # the writer request waiting for its answer
    extracting: list[dict] = field(default_factory=list)  # the extractor requests waiting for their answers
    checking: dict | None = None  # the version whose text is being extracted
    checking_mode: str = ""  # "draft" or "reduced"
    writer: dict | None = None  # the last writer request answered: a repair continues its conversation
    candidate: dict | None = None  # a version waiting for its format-only retry
    versions: list[dict] = field(default_factory=list)
    failed_before: list[str] = field(default_factory=list)
    exit: str = ""
    reason: str = ""
    flagged: bool = False
    roundtrip: str = "not run"
    cost: float = 0.0
    usage: dict = field(default_factory=dict)
    events: list[str] = field(default_factory=list)

    def request(self) -> Request | None:
        """The writer request waiting for its answer."""
        return None if self.pending is None else _request(self.pending)

    def requests(self) -> list[Request]:
        """Every request waiting for its answer: the writer's, or the extractions of a text."""
        return [self.request()] if self.pending is not None else [_request(r) for r in self.extracting]

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=1))

    @classmethod
    def load(cls, path: Path) -> "Run":
        return cls(**json.loads(Path(path).read_text()))


def _request(plain: Mapping) -> Request:
    return Request(**{**plain, "messages": tuple(tuple(m) for m in plain["messages"])})


def _pending(run: Run, request: Request | None) -> Run:
    run.pending = None if request is None else asdict(request)
    return run


def start(run_id: str, handover: str, model: str, draw: int = 0, budget: int = CALL_BUDGET, **request_options) -> Run:
    run = Run(run_id, budget)
    return _pending(run, propose.proposer_request(handover, model, draw, **request_options))


# --- the plan check ---------------------------------------------------------------------------------------


def check(draft: Draft, ctx: Context) -> Version:
    claims = []
    for c in draft.claims:
        verdict = verify(c, ctx.facts)
        claims.append([c.sentence_id, str(Claim(c.kind, c.terms, c.value, c.relation, None, c.inner)), verdict.value, verdict.code,
                       verdict.reason, evidence_text(verdict.evidence)])  # fmt: skip
    passing = [c for c, row in zip(draft.claims, claims) if row[2] == TRUE]
    cov = coverage(passing, ctx.facts, ctx.certified)
    return Version(draft.source, [[i, t] for i, t in draft.sentences], claims, list(draft.format_errors),
                   [" & ".join(sorted(k)) for k in cov.missing], [" & ".join(sorted(k)) for k in cov.hedged_only])  # fmt: skip


def _shown(line: str, ctx: Context) -> str:
    return str(labels.external(parse(line), ctx.names))


def _advice(line: str, ctx: Context) -> str:
    claim = parse(line)
    return advising.explain(claim, verify(claim, ctx.facts))


def problem_keys(lines: list[str], ctx: Context) -> set[str]:
    """The failing claims as the no-progress rule compares them (gate/advice.problem_key)."""
    keys = set()
    for line in lines:
        claim = parse(line)
        keys.add(advising.problem_key(claim, verify(claim, ctx.facts)))
    return keys


def problems(version: Version, ctx: Context) -> str:
    """The repair message's list: each failing claim with its verdict, reason, evidence and advice that says why it
    failed (gate/advice.py), then the format errors and the missing terms. In the writer's names; the texts are in
    llm/prompts/advice.json."""
    text = prompts.advice()
    lines = []
    for sentence_id, line, value, code, reason, evidence in version.claims:
        if value == TRUE:
            continue
        why = f" ({reason})" if reason else ""
        lines.append(text["claim"].format(sentence=sentence_id, claim=_shown(line, ctx), value=value, why=why, evidence=evidence,
                                          advice=_advice(line, ctx)))  # fmt: skip
    for error in version.format_errors:
        lines.append(text["format_error"].format(error=error))
    for term in version.missing:
        names = " & ".join(f"`{labels.shown(t.strip(), ctx.names)}`" for t in term.split("&"))
        lines.append(text["missing_term"].format(names=names))
    return "\n".join(lines)


def text_problems(trip: rt.RoundTrip, ctx: Context) -> str:
    """The repair message's list for a text that failed its round trip, in the writer's names."""
    text = prompts.advice()
    shares = {" & ".join(sorted(k)): v for k, v in rt._shares(ctx.facts).items()}
    lines = []
    for sentence_id, line, value, code, reason, evidence in trip.unplanned:
        if value == TRUE:
            continue
        why = f" ({reason})" if reason else ""
        lines.append(text["text_beyond_claims"].format(sentence=sentence_id, claim=_shown(line, ctx), value=value, why=why,
                                                       evidence=evidence, advice=_advice(line, ctx)))  # fmt: skip
    for sentence_id, minor, strong in trip.emphasis:
        listed = ", ".join(f"`{labels.shown(k, ctx.names)}` ({shares[k]:.1%})" for k in minor)
        named = ", ".join(f"`{labels.shown(k, ctx.names)}`" for k in strong)
        lines.append(text["emphasis"].format(sentence=sentence_id, minor=listed, strong=named))
    return "\n".join(lines)


# --- the loop ---------------------------------------------------------------------------------------------


def _end(run: Run, exit_state: str, reason: str, version: Version | None = None) -> Run:
    run.exit, run.reason = exit_state, reason
    if version is not None:
        run.versions.append(asdict(version))
        run.flagged = bool(version.flagged)
        if version.roundtrip is not None:
            run.roundtrip = "passed" if exit_state in (RELEASED, RELEASED_REDUCED) else "failed"
    run.events.append(f"{exit_state}: {reason}")
    run.extracting, run.checking, run.checking_mode = [], None, ""
    return _pending(run, None)


def _template(run: Run, ctx: Context) -> Run:
    draft = templates.template(ctx.facts, ctx.certified, ctx.label or templates.synthetic_label(ctx.names))
    version = check(draft, ctx)
    if version.passed:
        return _end(run, TEMPLATE, "template text from the certified facts", version)
    return _end(run, ESCALATE, "the template failed the plan check: a bug in the template or the verifier", version)


def _reduce(run: Run, version: Version, ctx: Context, why: str, drop: set[int] | None = None) -> Run:
    run.events.append(f"stop repairing: {why}")
    drop = version.failing_sentences() if drop is None else drop
    keep = [s for s in version.sentences if s[0] not in drop]
    if not keep:
        return _template(run, ctx)
    sentences = [(i, t) for i, t in keep]
    claims = [parse(line, sentence_id=sid) for sid, line, value, *_ in version.claims if value == TRUE and sid in {i for i, _ in sentences}]
    reduced = check(Draft(sentences, claims, [], "reduced"), ctx)
    if reduced.passed:
        return _roundtrip(run, reduced, ctx, "reduced")
    run.versions.append(asdict(reduced))
    return _template(run, ctx)


def _release(run: Run, version: Version, mode: str) -> Run:
    if mode == "draft":
        return _end(run, RELEASED, f"passed after {run.rounds} repair round(s)", version)
    return _end(run, RELEASED_REDUCED, f"failing sentences dropped after {run.rounds} repair round(s)", version)


def _roundtrip(run: Run, version: Version, ctx: Context, mode: str) -> Run:
    """Release a text whose plan passed, or first send it to the extractor."""
    if not ctx.roundtrip:
        return _release(run, version, mode)
    if run.calls + extract.EXTRACTIONS > run.budget:
        run.versions.append(asdict(version))
        run.events.append("no calls left for the round trip")
        return _template(run, ctx)
    features = extract.features_text(ctx.facts, ctx.names, ctx.descriptions)
    draw = run.writer["draw"] if run.writer else 0
    run.checking, run.checking_mode = asdict(version), mode
    run.extracting = [asdict(extract.extractor_request(version.sentences, features, draw, k)) for k in range(extract.EXTRACTIONS)]
    run.events.append(f"round trip of the {'draft' if mode == 'draft' else 'reduced text'}: {extract.EXTRACTIONS} extractions")
    return _pending(run, None)


def _round_trip_answered(run: Run, responses: list[Response], ctx: Context) -> Run:
    version, mode = Version(**run.checking), run.checking_mode
    run.checking, run.checking_mode, run.extracting = None, "", []
    ids = {i for i, _ in version.sentences}
    readings = []
    for response in responses:
        if response.error:
            continue
        try:
            readings.append(extract.extraction_from(response, ids, ctx.names))
        except (ValueError, KeyError, TypeError):
            continue
    if len(readings) < rt.EXTRACTED:
        run.versions.append(asdict(version))
        run.events.append(f"round trip could not run: {len(readings)} readable extraction(s)")
        return _template(run, ctx)
    plan = [parse(line, sentence_id=sid) for sid, line, *_ in version.claims]
    trip = rt.compare(readings, plan, [i for i, _ in version.sentences], ctx.facts, check_emphasis=mode == "draft")
    version.roundtrip = asdict(trip)
    if trip.passed:
        return _release(run, version, mode)
    run.versions.append(asdict(version))
    if mode == "reduced":
        run.events.append("the reduced text failed its round trip")
        return _template(run, ctx)
    failing = problem_keys([line for _, line, value, *_ in trip.unplanned if value != TRUE], ctx)
    failing |= {key for key in trip.failures() if key.startswith("emphasis:")}
    repeated = failing & set(run.failed_before)
    drop = trip.failing_sentences()
    if repeated:
        return _reduce(run, version, ctx, f"no progress: {sorted(repeated)[0]} failed before", drop)
    if run.rounds >= MAX_ROUNDS:
        return _reduce(run, version, ctx, f"{MAX_ROUNDS} repair rounds used", drop)
    if run.calls >= run.budget:
        return _reduce(run, version, ctx, "call budget used", drop)
    run.rounds += 1
    run.failed_before = sorted(set(run.failed_before) | failing)
    run.format_retry_used = False
    run.events.append(f"repair round {run.rounds}: {len(failing)} problem(s) in the text")
    return _pending(run, propose.repair_request(_request(run.writer), version.answer, text_problems(trip, ctx), run.rounds))


def _format_problem(run: Run, request: Request, ctx: Context, what: str) -> Run:
    if not run.format_retry_used and run.calls < run.budget:
        run.format_retry_used = True
        run.events.append(f"format-only retry: {what}")
        retry = Request(**{**asdict(request), "messages": request.messages, "attempt": request.attempt + 1})
        return _pending(run, retry)
    best = run.candidate or (run.versions[-1] if run.versions else None)  # the best text there is
    if best is not None:
        run.candidate = None
        return _reduce(run, Version(**best), ctx, f"format problem after the retry ({what})")
    return _template(run, ctx)


def _decide(run: Run, version: Version, request: Request, ctx: Context) -> Run:
    if version.passed:
        return _roundtrip(run, version, ctx, "draft")
    failing = problem_keys(version.failing(), ctx) | set(version.format_errors)
    repeated = failing & set(run.failed_before)
    run.versions.append(asdict(version))
    if repeated:
        return _reduce(run, version, ctx, f"no progress: {sorted(repeated)[0]} failed before")
    if run.rounds >= MAX_ROUNDS:
        return _reduce(run, version, ctx, f"{MAX_ROUNDS} repair rounds used")
    if run.calls >= run.budget:
        return _reduce(run, version, ctx, "call budget used")
    run.rounds += 1
    run.failed_before = sorted(set(run.failed_before) | failing)
    run.format_retry_used = False
    run.events.append(f"repair round {run.rounds}: {len(failing)} problem(s)")
    return _pending(run, propose.repair_request(request, version.answer, problems(version, ctx), run.rounds))


def advance(run: Run, response: Response | list[Response], ctx: Context) -> Run:
    """Take the answers to the pending requests (one writer answer, or the extractions of a text); return the run
    with its next requests or its exit state."""
    responses = response if isinstance(response, list) else [response]
    expected = run.requests()
    if not expected:
        raise ValueError(f"run {run.run_id} has no pending request")
    if [r.key for r in responses] != [q.key for q in expected]:
        raise ValueError(f"run {run.run_id}: the answers are not for the pending requests")
    for answer in responses:
        run.calls += 1
        run.cost += answer.cost if not answer.cached else 0.0
        for k, v in answer.usage.items():
            if isinstance(v, (int, float)):
                run.usage[k] = run.usage.get(k, 0) + v
    for answer in responses:
        if answer.error == "api":
            return _end(run, ESCALATE, "api")
        if answer.error == "refusal":
            category = (answer.stop_details or {}).get("category")
            return _end(run, ESCALATE, f"refusal ({category})" if category else "refusal")
    if run.pending is None:
        return _round_trip_answered(run, responses, ctx)
    request, response = expected[0], responses[0]
    run.writer = asdict(request)
    if response.error:
        return _format_problem(run, request, ctx, response.error)
    try:
        draft = propose.draft_from(response, request.role, ctx.names)
    except (ValueError, KeyError, TypeError):
        return _format_problem(run, request, ctx, "the answer is not a draft")
    version = check(draft, ctx)
    version.answer = response.text or ""
    if draft.format_errors and not run.format_retry_used and run.calls < run.budget:
        run.format_retry_used = True
        run.candidate = asdict(version)
        run.events.append(f"format-only retry: {len(draft.format_errors)} DSL line(s) do not parse")
        message = "These claim lines are not valid DSL:\n" + "\n".join(f"- {e}" for e in draft.format_errors) + (
            "\n\nReturn the whole draft again, all sentences and all claims, with these lines fixed and nothing else changed.")  # fmt: skip
        return _pending(run, propose.follow_up(request, version.answer, message, "format retry"))
    run.candidate = None
    return _decide(run, version, request, ctx)


def run_sync(run: Run, client: Client, ctx: Context, path: Path | None = None) -> Run:
    """Drive a run to its exit with synchronous calls, saving it after every step."""
    while run.requests():
        run = advance(run, [client.call(r) for r in run.requests()], ctx)
        if path is not None:
            run.save(path)
    return run
