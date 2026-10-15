"""Batch API transport (plan §14.14, D37): the gate's runs advance in waves, at half price.

A wave is one Message Batch holding every pending request of every run (a writer request, or the extractions of
a text) whose answer is not in the disk cache. Each request's custom_id is its cache key (a SHA-256 in hex, 64
characters, the API's limit), since results come back in any order. Before anything is waited for, the wave is saved in cache/llm/batches/<batch id>.json with its requests,
so a stopped process resumes the wave instead of submitting it again. When the batch has ended, each answer is
stored in the disk cache and the call log like a synchronous one (transport "batch", cost at the batch price), and
its run advances; every run is saved after every step. The next wave holds the runs' next requests (repairs,
format retries), until every run has ended. A collected wave keeps only its keys and outcomes: the record of which
batch produced which answer.

Failures: a request whose result errored on the server, expired or was canceled is not cached and goes into the
next wave; after MAX_SUBMISSIONS submissions without an answer its run ends as ESCALATE "api", as a synchronous
call does after the SDK's retries. An invalid request is a bug in our code: the wave's other answers are stored,
then it raises.

Prompt caching inside a batch is best-effort (§14.14); the cost estimate does not depend on it. A process stopped
between submitting a batch and saving its wave (a fraction of a second) leaves that batch unrecorded, and its
requests are submitted again on the next start.
"""

import json
import time
from collections import Counter
from collections.abc import Callable, Iterator, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import NamedTuple

from verifier_gate.gate import gate as g
from verifier_gate.llm.client import Client, Request, Response, load_dotenv

MAX_SUBMISSIONS = 3
MAX_WAVES = g.CALL_BUDGET * MAX_SUBMISSIONS  # a run needs at most this many; more is a bug, never more paid batches
POLL_SECONDS = 60


class Result(NamedTuple):
    key: str
    outcome: str  # succeeded, errored, expired, canceled
    raw: dict | None  # the message, if succeeded
    error: str = ""  # the error type, if errored


class BatchAPI:
    """The Message Batches endpoints, reduced to what a wave needs."""

    def __init__(self, max_retries: int = 3):
        self.max_retries, self._sdk = max_retries, None

    def sdk(self):
        import anthropic

        if self._sdk is None:
            load_dotenv()
            self._sdk = anthropic.Anthropic(max_retries=self.max_retries)
        return self._sdk

    def create(self, requests: list[Request]) -> str:
        batch = self.sdk().messages.batches.create(requests=[{"custom_id": r.key, "params": r.params()} for r in requests])
        return batch.id

    def status(self, batch_id: str) -> tuple[str, dict]:
        batch = self.sdk().messages.batches.retrieve(batch_id)
        return batch.processing_status, batch.request_counts.to_dict()

    def results(self, batch_id: str) -> Iterator[Result]:
        for item in self.sdk().messages.batches.results(batch_id):
            result = item.result
            if result.type == "succeeded":
                yield Result(item.custom_id, result.type, result.message.to_dict())
            elif result.type == "errored":
                yield Result(item.custom_id, result.type, None, result.error.error.type)
            else:
                yield Result(item.custom_id, result.type, None)


class StubBatchAPI:
    """No network: a responder answers each request with a raw message, or with an error type ("api_error",
    "invalid_request_error", "expired"); a batch ends after `polls` status checks."""

    def __init__(self, responder: Callable[[Request], Mapping | str], polls: int = 1):
        self.responder, self.polls = responder, polls
        self.batches: dict[str, dict] = {}

    def create(self, requests: list[Request]) -> str:
        batch_id = f"msgbatch_stub{len(self.batches) + 1}"
        self.batches[batch_id] = {"requests": list(requests), "checks": 0}
        return batch_id

    def status(self, batch_id: str) -> tuple[str, dict]:
        batch = self.batches[batch_id]
        batch["checks"] += 1
        return ("ended" if batch["checks"] >= self.polls else "in_progress"), {"processing": len(batch["requests"])}

    def results(self, batch_id: str) -> Iterator[Result]:
        for request in self.batches[batch_id]["requests"]:
            answer = self.responder(request)
            if answer == "expired":
                yield Result(request.key, "expired", None)
            elif isinstance(answer, str):
                yield Result(request.key, "errored", None, answer)
            else:
                yield Result(request.key, "succeeded", dict(answer))


@dataclass
class Job:
    """One gate run with what it needs to advance, and where it is saved."""

    run: g.Run
    ctx: g.Context
    path: Path | None = None


def _plain(request: Request) -> dict:
    return {**asdict(request), "messages": [list(m) for m in request.messages]}


def _request(plain: Mapping) -> Request:
    return Request(**{**plain, "messages": tuple(tuple(m) for m in plain["messages"])})


def _waves(folder: Path) -> list[tuple[Path, dict]]:
    return [(path, json.loads(path.read_text())) for path in sorted(folder.glob("*.json"))]


def submit(requests: list[Request], folder: Path, api, log: Callable = print) -> str:
    batch_id = api.create(requests)
    folder.mkdir(parents=True, exist_ok=True)
    wave = {"id": batch_id, "submitted": time.time(), "collected": False, "requests": {r.key: _plain(r) for r in requests}}
    (folder / f"{batch_id}.json").write_text(json.dumps(wave))
    log(f"batch {batch_id}: {len(requests)} request(s) submitted")
    return batch_id


def collect(path: Path, wave: dict, client: Client, api, poll: float = POLL_SECONDS, log: Callable = print) -> dict[str, Response]:
    """Wait for a wave's batch to end, store its answers and record its failures; the fresh answers by key."""
    while True:
        status, counts = api.status(wave["id"])
        if status == "ended":
            break
        log(f"batch {wave['id']}: {status} {counts}; next check in {poll:.0f} s (stopping here is safe: a rerun resumes)")
        time.sleep(poll)
    latency = time.time() - wave["submitted"]
    requests = {key: _request(plain) for key, plain in wave["requests"].items()}
    fresh, failed = {}, {}
    for result in api.results(wave["id"]):
        request = requests.get(result.key)
        if request is None:
            continue
        if result.outcome == "succeeded":
            raw = {**result.raw, "_batch": True, "_request_id": wave["id"]}
            fresh[result.key] = client.store(request, raw, latency, "batch")
        else:
            failed[result.key] = result.error or result.outcome
            client.failed(request, latency, "batch")
    for key in set(requests) - set(fresh) - set(failed):
        failed[key] = "no result"
    invalid = sorted(k for k, e in failed.items() if "invalid_request" in e)
    wave.update(collected=True, ended=time.time(), requests={k: r.role for k, r in requests.items()}, failed=failed)
    path.write_text(json.dumps(wave))
    log(f"batch {wave['id']}: {len(fresh)} answered, {len(failed)} failed")
    if invalid:
        raise RuntimeError(f"batch {wave['id']}: {len(invalid)} invalid request(s), a bug in our request (first: {invalid[0]})")
    return fresh


def _advance(jobs: Mapping[str, Job], client: Client, fresh: dict[str, Response], submissions: Counter) -> list[Request]:
    """Advance every run as far as the answers at hand allow; the requests still without an answer."""
    wave: dict[str, Request] = {}
    for job in jobs.values():
        while requests := job.run.requests():
            answers = [fresh.pop(r.key, None) or client.lookup(r) for r in requests]
            answers = [Response(r.key, r.role, r.model, "", "api") if a is None and submissions[r.key] >= MAX_SUBMISSIONS else a
                       for r, a in zip(requests, answers)]  # fmt: skip
            if any(a is None for a in answers):
                for r, a in zip(requests, answers):
                    if a is None:
                        wave.setdefault(r.key, r)
                break
            job.run = g.advance(job.run, answers, job.ctx)
            if job.path is not None:
                job.run.save(job.path)
    return list(wave.values())


def run_waves(jobs: Mapping[str, Job], client: Client, api, folder: Path | None = None, poll: float = POLL_SECONDS,
              log: Callable = print) -> dict[str, g.Run]:  # fmt: skip
    """Drive the runs to their exits in waves. Open waves (from a stopped process) are collected first."""
    folder = folder or client.cache_dir / "batches"
    for submitted in range(MAX_WAVES + 1):
        fresh = {}
        for path, wave in _waves(folder):
            if not wave["collected"]:
                fresh |= collect(path, wave, client, api, poll, log)
        submissions = Counter(k for _, wave in _waves(folder) for k in wave.get("failed", {}))
        pending = _advance(jobs, client, fresh, submissions)
        if not pending:
            return {name: job.run for name, job in jobs.items()}
        if submitted == MAX_WAVES:
            break
        submit(pending, folder, api, log)
    raise RuntimeError(f"more than {MAX_WAVES} waves: a bug in the transport, stopped before submitting more")
