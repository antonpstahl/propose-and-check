"""Claude API wrapper (plan §14.14): every call cached to disk and logged, a stub mode, retries, and no parsing of
truncated or refused output.

A Request holds everything that determines an API call. Its cache key is a hash of all of it, including the draw
number, so the draws of one cell are separate calls (D38) and a rerun never pays twice. The full response is
stored in cache/llm/<key>.json, and every call, cached or not, is appended to the call log with model, effort,
thinking, prompt hashes, stop reason, token use, request id, latency and cost.

Transports: "stub" (no network; a responder function scripts the response: tests and dry runs) and "sync" (the
Messages API: the smoke test and the pilot). The Batch API (E3, the Sonnet subset) is driven by llm/batch.py, which
stores each result through `store`, so a batched answer sits in the same cache and log as a synchronous one.

Outcomes, in `Response.error`: "" (parsed JSON in `data`), "truncated" (stop_reason max_tokens: never parsed, a
format error for the gate), "refusal" (D39: no fallback; the gate escalates), "invalid_json", "no_text", "api" (the
API failed after the SDK's retries; not cached, so a rerun tries again; the gate escalates with reason "api").
A rejected request (400, 401, 403, 404) is a bug in our code, not a run outcome, and raises.
"""

import hashlib
import json
import os
import time
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path

from verifier_gate.llm import settings

CACHE = Path(__file__).parents[3] / "cache" / "llm"
DOTENV = Path(__file__).parents[3] / ".env"  # git-ignored; .env.example is the template
EFFORTS_WITHOUT_THINKING = ("low", "medium", "high")
THINKING_OFF = {"claude-haiku-5-5": {"type": "disabled"}, "claude-sonnet-5-5": {"type": "between_tools"}}


def load_dotenv(path: Path = DOTENV) -> list[str]:
    """Put the `KEY = value` lines of a .env file into the environment, without overriding what is set and
    without ever printing a value. Returns the keys it set."""
    if not path.exists():
        return []
    added = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        value = value.strip("'\"")
        if key and value and key not in os.environ:
            os.environ[key] = value
            added.append(key)
    return added


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def thinking_param(model: str, thinking: str, effort: str) -> dict:
    """The thinking parameter for a model. "off" is model-specific: Claude Haiku 5.5 takes {"type": "disabled"},
    Claude Sonnet 5.5 {"type": "between_tools"}, both only at effort high or below; Claude Opus 5.5 cannot switch
    thinking off."""
    if thinking == "adaptive":
        return {"type": "adaptive"}
    if thinking != "off":
        raise ValueError(f"thinking is 'off' or 'adaptive', not {thinking!r}")
    if model not in THINKING_OFF:
        raise ValueError(f"{model} cannot run with thinking off")
    if effort not in EFFORTS_WITHOUT_THINKING:
        raise ValueError(f"thinking off needs effort high or below, not {effort!r}")
    return THINKING_OFF[model]


@dataclass(frozen=True)
class Request:
    role: str  # proposer, repair, extractor: for the log only, not part of the key
    model: str
    system: str
    messages: tuple[tuple[str, str], ...]  # (role, text)
    schema: str  # the JSON schema of the answer, as JSON text
    effort: str = settings.EFFORT
    thinking: str = settings.THINKING
    max_tokens: int = settings.MAX_TOKENS
    draw: int = 0
    attempt: int = 0  # the format-only retry of the same request is a new call (§5.8)

    def params(self) -> dict:
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": [{"type": "text", "text": self.system, "cache_control": {"type": "ephemeral"}}],
            "messages": [{"role": role, "content": text} for role, text in self.messages],
            "output_config": {"format": {"type": "json_schema", "schema": json.loads(self.schema)}, "effort": self.effort},
            "thinking": thinking_param(self.model, self.thinking, self.effort),
        }

    @property
    def key(self) -> str:
        fields = {k: v for k, v in asdict(self).items() if k != "role"}
        return sha(json.dumps(fields, sort_keys=True))


@dataclass
class Response:
    key: str
    role: str
    model: str
    stop_reason: str
    error: str
    text: str | None = None
    data: dict | None = None
    usage: dict = field(default_factory=dict)
    stop_details: dict | None = None
    request_id: str | None = None
    latency: float = 0.0
    cost: float = 0.0  # what this call cost when it was made (0 for an API error)
    cached: bool = False

    @property
    def ok(self) -> bool:
        return not self.error


def cost(model: str, usage: Mapping, batch: bool = False) -> float:
    """USD for one call from its usage (settings.PRICES; input_tokens excludes cached tokens)."""
    price_in, price_out, price_read = settings.PRICES[model]
    total = (
        usage.get("input_tokens", 0) * price_in
        + (usage.get("cache_creation_input_tokens") or 0) * price_in * settings.CACHE_WRITE
        + (usage.get("cache_read_input_tokens") or 0) * price_read
        + usage.get("output_tokens", 0) * price_out
    ) / 1e6
    return total * (settings.BATCH_DISCOUNT if batch else 1.0)


def stub_message(data: Mapping | str | None, stop_reason: str = "end_turn", usage: Mapping | None = None, model: str = "") -> dict:
    """A raw message in the API's shape, for stub responders: the answer as one text block."""
    text = data if isinstance(data, str) or data is None else json.dumps(data)
    return {
        "id": "stub", "model": model, "stop_reason": stop_reason, "stop_details": None,
        "content": [] if text is None else [{"type": "text", "text": text}],
        "usage": dict(usage or {"input_tokens": 1000, "output_tokens": 300}),
    }  # fmt: skip


def interpret(request: Request, raw: Mapping, latency: float, cached: bool) -> Response:
    stop = raw.get("stop_reason") or ""
    texts = [b["text"] for b in raw.get("content", []) if b.get("type") == "text"]
    usage = dict(raw.get("usage") or {})
    response = Response(
        request.key, request.role, raw.get("model") or request.model, stop, "", texts[0] if texts else None,
        usage=usage, stop_details=raw.get("stop_details"), request_id=raw.get("_request_id"), latency=latency,
        cost=cost(request.model, usage, batch=bool(raw.get("_batch"))), cached=cached,
    )  # fmt: skip
    if stop == "max_tokens":
        response.error = "truncated"
    elif stop == "refusal":
        response.error = "refusal"
    elif response.text is None:
        response.error = "no_text"
    else:
        try:
            response.data = json.loads(response.text)
        except json.JSONDecodeError:
            response.error = "invalid_json"
    return response


class Client:
    def __init__(self, transport: str = "stub", responder: Callable[[Request], Mapping] | None = None,
                 cache_dir: Path = CACHE, log_path: Path | None = None, max_retries: int = 3):  # fmt: skip
        if transport not in ("stub", "sync", "batch"):
            raise ValueError(f"transport is 'stub', 'sync' or 'batch', not {transport!r}")
        if transport == "stub" and responder is None:
            raise ValueError("stub mode needs a responder")
        self.transport, self.responder, self.max_retries = transport, responder, max_retries
        self.cache_dir = Path(cache_dir)
        self.log_path = Path(log_path) if log_path else self.cache_dir / "calls.jsonl"
        self._sdk = None

    def call(self, request: Request) -> Response:
        response = self.lookup(request)
        if response is not None:
            return response
        if self.transport == "batch":
            raise RuntimeError("a batch client answers from the cache only; llm/batch.py submits the rest")
        start = time.monotonic()
        raw = self.responder(request) if self.transport == "stub" else self._send(request)
        latency = time.monotonic() - start
        if raw is None:  # the API failed after the retries: not cached
            return self.failed(request, latency, self.transport)
        return self.store(request, raw, latency, self.transport)

    def lookup(self, request: Request) -> Response | None:
        """The cached answer to a request (logged as a cache hit), or None."""
        path = self.cache_dir / f"{request.key}.json"
        if not path.exists():
            return None
        stored = json.loads(path.read_text())
        response = interpret(request, stored["raw"], stored["latency"], cached=True)
        self._log(request, response, self.transport)
        return response

    def store(self, request: Request, raw: Mapping, latency: float, transport: str) -> Response:
        """Cache and log a new answer; a batched one carries `_batch` in its raw message and costs the batch price."""
        response = interpret(request, raw, latency, cached=False)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        record = {"request": {**asdict(request), "messages": list(request.messages)}, "raw": dict(raw), "latency": latency}
        (self.cache_dir / f"{request.key}.json").write_text(json.dumps(record))
        self._log(request, response, transport)
        return response

    def failed(self, request: Request, latency: float, transport: str) -> Response:
        """Log a call the API did not answer (not cached, so a rerun tries again); the "api" outcome."""
        response = Response(request.key, request.role, request.model, "", "api", latency=latency)
        self._log(request, response, transport)
        return response

    def _send(self, request: Request) -> dict | None:
        import anthropic

        if self._sdk is None:
            load_dotenv()
            self._sdk = anthropic.Anthropic(max_retries=self.max_retries)
        try:
            message = self._sdk.messages.create(**request.params())
        except (anthropic.APIConnectionError, anthropic.RateLimitError):
            return None
        except anthropic.APIStatusError as e:
            if e.status_code >= 500:
                return None
            raise  # 400, 401, 403, 404: our request is wrong, not a run outcome
        raw = message.to_dict()
        raw["_request_id"] = message._request_id
        return raw

    def _log(self, request: Request, response: Response, transport: str) -> None:
        record = {
            "time": time.strftime("%Y-%m-%dT%H:%M:%S"), "transport": transport, "key": request.key,
            "role": request.role, "model": request.model, "effort": request.effort, "thinking": request.thinking,
            "draw": request.draw, "system_hash": sha(request.system)[:16],
            "messages_hash": sha(json.dumps(request.messages))[:16], "stop_reason": response.stop_reason,
            "error": response.error, "usage": response.usage, "request_id": response.request_id,
            "latency": round(response.latency, 3), "cost": response.cost, "cached": response.cached,
            "price_date": settings.PRICE_DATE,
        }  # fmt: skip
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a") as log:
            log.write(json.dumps(record) + "\n")
