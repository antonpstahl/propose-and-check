"""Gate and repair loop with stop rules (§5.8): every run ends in RELEASED, RELEASED_REDUCED, TEMPLATE or ESCALATE.

The gate is a state machine that advances one LLM answer at a time: `start` returns a run with its first request
pending, `advance` takes the answer to the pending request and returns the run with its next request, or with an
exit state when it has ended. The run is plain data, saved as JSON after every step, so it can wait for a Batch API
result and an interrupted run resumes without repeating a paid call (every call is also cached by the client).
`run_sync` drives one run with a client.

Plan check (week 5): every claim is verified on M. A claim fails if its verdict is not true: false, or undecidable
for any reason (D30: never released as stated). A DSL line that does not parse fails too. Coverage (§5.7) must
pass; a top-3 term covered only by hedges raises the limited-evidence flag (released, marked for a reviewer). The
round trip (three extractions, emphasis) comes in week 6; until then each release records it as not run.

Stop rules (§5.8): at most 2 repair rounds; no progress (a claim that failed in an earlier version fails again)
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
from verifier_gate.gate.roundtrip import coverage
from verifier_gate.lexicon import predicates as p
from verifier_gate.lexicon.predicates import TRUE, UNDECIDABLE
from verifier_gate.llm import propose
from verifier_gate.llm.client import Client, Request, Response
from verifier_gate.verifier.verify import verify

RELEASED, RELEASED_REDUCED, TEMPLATE, ESCALATE = "RELEASED", "RELEASED_REDUCED", "TEMPLATE", "ESCALATE"
MAX_ROUNDS = 2
CALL_BUDGET = 16
ADVICE = {
    "false": "The facts contradict it. Change the statement to what the facts show, or drop it.",
    p.INSUFFICIENT_EVIDENCE: ("The data do not settle it at this sample size. State it as a set of values (for example "
                              "\"weak to moderate\" or \"generally decreases\"), hedge it with unsettled(...), or drop it."),
    p.UNKNOWN_TERM: "The model has no such term. Use only the features named in the facts.",
    p.NOT_APPLICABLE: "This kind of claim does not apply to that term.",
}  # fmt: skip


@dataclass
class Context:
    """What the gate needs besides the run; not saved, rebuilt from the run's ids."""

    facts: Facts
    certified: list[Claim]
    names: Mapping[str, str] = field(default_factory=lambda: labels.SYNTHETIC_NAMES)
    label: Callable[[str], str] | None = None


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
    pending: dict | None = None  # the request waiting for its answer
    candidate: dict | None = None  # a version waiting for its format-only retry
    versions: list[dict] = field(default_factory=list)
    failed_before: list[str] = field(default_factory=list)
    exit: str = ""
    reason: str = ""
    flagged: bool = False
    roundtrip: str = "not run (week 6)"
    cost: float = 0.0
    usage: dict = field(default_factory=dict)
    events: list[str] = field(default_factory=list)

    def request(self) -> Request | None:
        return None if self.pending is None else Request(**{**self.pending, "messages": tuple(tuple(m) for m in self.pending["messages"])})

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=1))

    @classmethod
    def load(cls, path: Path) -> "Run":
        return cls(**json.loads(Path(path).read_text()))


def _pending(run: Run, request: Request | None) -> Run:
    run.pending = None if request is None else asdict(request)
    return run


def start(run_id: str, handover: str, model: str, draw: int = 0, budget: int = CALL_BUDGET, **request_options) -> Run:
    run = Run(run_id, budget)
    return _pending(run, propose.proposer_request(handover, model, draw, **request_options))


# --- the plan check ---------------------------------------------------------------------------------------


def _evidence(evidence: Mapping) -> str:
    def fmt(v):
        if isinstance(v, float):
            return f"{v:.3g}"
        if isinstance(v, (tuple, list)) and all(isinstance(x, (int, float)) for x in v):
            return " to ".join(f"{x:.3g}" for x in v)
        return str(v)

    items = [(k, v) for k, v in evidence.items() if k not in ("term", "claim", "claim reason") and not isinstance(v, dict)]
    return "; ".join(f"{k} {fmt(v)}" for k, v in items[:5])


def check(draft: Draft, ctx: Context) -> Version:
    claims = []
    for c in draft.claims:
        verdict = verify(c, ctx.facts)
        claims.append([c.sentence_id, str(Claim(c.kind, c.terms, c.value, c.relation, None, c.inner)), verdict.value, verdict.code,
                       verdict.reason, _evidence(verdict.evidence)])  # fmt: skip
    passing = [c for c, row in zip(draft.claims, claims) if row[2] == TRUE]
    cov = coverage(passing, ctx.facts, ctx.certified)
    return Version(draft.source, [[i, t] for i, t in draft.sentences], claims, list(draft.format_errors),
                   [" & ".join(sorted(k)) for k in cov.missing], [" & ".join(sorted(k)) for k in cov.hedged_only])  # fmt: skip


def problems(version: Version, ctx: Context) -> str:
    """The repair message's list: each failing claim with its verdict, reason, evidence and the advice for its
    reason code (D30), then the format errors and the missing terms. In the writer's names."""
    def shown(line: str) -> str:
        return str(labels.external(parse(line), ctx.names))

    lines = []
    for sentence_id, line, value, code, reason, evidence in version.claims:
        if value == TRUE:
            continue
        advice = ADVICE[code] if value == UNDECIDABLE else ADVICE["false"]
        why = f" ({reason})" if reason else ""
        lines.append(f"- Sentence {sentence_id}: `{shown(line)}` is {value}{why}. Evidence: {evidence}. {advice}")
    for error in version.format_errors:
        lines.append(f"- {error}. This is not a valid DSL line; use only the forms in the DSL reference.")
    for term in version.missing:
        names = " & ".join(f"`{labels.shown(t.strip(), ctx.names)}`" for t in term.split("&"))
        lines.append(f"- The text does not mention {names}, one of the model's most important terms. Add a sentence about it, with its claims.")
    return "\n".join(lines)


# --- the loop ---------------------------------------------------------------------------------------------


def _end(run: Run, exit_state: str, reason: str, version: Version | None = None) -> Run:
    run.exit, run.reason = exit_state, reason
    if version is not None:
        run.versions.append(asdict(version))
        run.flagged = bool(version.flagged)
    run.events.append(f"{exit_state}: {reason}")
    return _pending(run, None)


def _template(run: Run, ctx: Context) -> Run:
    draft = templates.template(ctx.facts, ctx.certified, ctx.label or templates.synthetic_label(ctx.names))
    version = check(draft, ctx)
    if version.passed:
        return _end(run, TEMPLATE, "template text from the certified facts", version)
    return _end(run, ESCALATE, "the template failed the plan check: a bug in the template or the verifier", version)


def _reduce(run: Run, version: Version, ctx: Context, why: str) -> Run:
    run.events.append(f"stop repairing: {why}")
    keep = [s for s in version.sentences if s[0] not in version.failing_sentences()]
    if not keep:
        return _template(run, ctx)
    sentences = [(i, t) for i, t in keep]
    claims = [parse(line, sentence_id=sid) for sid, line, value, *_ in version.claims if value == TRUE and sid in {i for i, _ in sentences}]
    reduced = check(Draft(sentences, claims, [], "reduced"), ctx)
    if reduced.passed:
        return _end(run, RELEASED_REDUCED, f"failing sentences dropped after {run.rounds} repair round(s)", reduced)
    run.versions.append(asdict(reduced))
    return _template(run, ctx)


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
        return _end(run, RELEASED, f"passed after {run.rounds} repair round(s)", version)
    failing = set(version.failing()) | set(version.format_errors)
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


def advance(run: Run, response: Response, ctx: Context) -> Run:
    """Take the answer to the pending request; return the run with its next request or its exit state."""
    request = run.request()
    if request is None:
        raise ValueError(f"run {run.run_id} has no pending request")
    if response.key != request.key:
        raise ValueError(f"run {run.run_id}: the answer is not for the pending request")
    run.calls += 1
    run.cost += response.cost if not response.cached else 0.0
    for k, v in response.usage.items():
        if isinstance(v, (int, float)):
            run.usage[k] = run.usage.get(k, 0) + v
    if response.error == "api":
        return _end(run, ESCALATE, "api")
    if response.error == "refusal":
        category = (response.stop_details or {}).get("category")
        return _end(run, ESCALATE, f"refusal ({category})" if category else "refusal")
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
    while run.pending is not None:
        run = advance(run, client.call(run.request()), ctx)
        if path is not None:
            run.save(path)
    return run
