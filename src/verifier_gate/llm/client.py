"""Claude API wrapper (plan §14.14): every call cached to disk and logged, a stub mode, retries, and no parsing of
truncated or refused output.

A Request holds everything that determines an API call. Its cache key is a hash of all of it, including the draw
number, so the draws of one cell are separate calls (D38) and a rerun never pays twice. The full response is
stored in cache/llm/<key>.json, and every call, cached or not, is appended to the call log with model, effort,
thinking, prompt hashes, stop reason, token use, request id, latency and cost.

Transports: "stub" (no network; a responder function scripts the response: tests and dry runs) and "sync" (the
Messages API: the smoke test and the pilot). The Batch API (E3, the Sonnet subset) is driven by llm/batch.py, which
stores each result through `store`, so a batched answer sits in the same cache and log as a synchronous one. A
model named ollama/<tag> runs on the local Ollama server (D55), and one named openai/<model> on OpenAI's Chat
Completions API (the LLM critic, D56); both answers are returned in the Messages API's shape, so the cache, the
log and the cost work unchanged. The client is safe to call from several threads (the critic's calls run in parallel).

Outcomes, in `Response.error`: "" (parsed JSON in `data`), "truncated" (stop_reason max_tokens: never parsed, a
format error for the gate), "refusal" (D39: no fallback; the gate escalates), "invalid_json", "no_text", "api" (the
API failed after the SDK's retries; not cached, so a rerun tries again; the gate escalates with reason "api").
A rejected request (400, 401, 403, 404) is a bug in our code, not a run outcome, and raises.
"""

import hashlib
import json
import os
import sys
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path

from verifier_gate.llm import settings

CACHE = Path(__file__).parents[3] / "cache" / "llm"
OFFLINE = "VERIFIER_GATE_OFFLINE"
LOCAL_PREFIX = "ollama/"  # a model named ollama/<tag> runs on the local Ollama server (D55): synchronous, $0
OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_NUM_CTX = int(os.environ.get("OLLAMA_NUM_CTX", "10240"))  # writer prompt 5.5k tokens; two repair rounds reach about 8k
OLLAMA_NUM_BATCH = int(os.environ.get("OLLAMA_NUM_BATCH", "64"))  # small prompt batches keep the peak memory down (24 GB machine)  # set: a request not in the cache raises instead of calling the API (experiments/reproduce.py)
OPENAI_PREFIX = "openai/"  # a model named openai/<model> runs on OpenAI's Chat Completions API (the critic, D56)
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
DOTENV = Path(__file__).parents[3] / ".env"  # git-ignored; .env.example is the template
EFFORTS_WITHOUT_THINKING = ("low", "medium", "high")
_LOG_LOCK = threading.Lock()
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
    replica: int = 0  # the independent extractions of one text (§5.7): 0, 1, 2

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
        """Hash of everything that determines the call. `replica` enters only when it is not 0, so the keys of
        the requests cached before it existed stay the same."""
        fields = {k: v for k, v in asdict(self).items() if k != "role" and not (k == "replica" and v == 0)}
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
    """USD for one call from its usage (settings.PRICES; input_tokens excludes cached tokens). A local model costs 0."""
    if model.startswith(LOCAL_PREFIX):
        return 0.0
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


def send_local(request: Request, url: str = OLLAMA_URL, timeout: float = 3600.0) -> dict | None:
    """One call to a local model on an Ollama server (D55), returned in the API's message shape so that the rest of
    the pipeline (cache, parsing, gate) is unchanged. The answer is constrained to the request's JSON schema;
    thinking is off. None if the server cannot be reached (the "api" outcome, not cached)."""
    import urllib.error
    import urllib.request

    tag = request.model.removeprefix(LOCAL_PREFIX)
    body = {
        "model": tag, "stream": False, "think": request.thinking != "off", "format": json.loads(request.schema), "keep_alive": "30m",
        "messages": [{"role": "system", "content": request.system}] + [{"role": r, "content": t} for r, t in request.messages],
        "options": {"num_ctx": OLLAMA_NUM_CTX, "num_batch": OLLAMA_NUM_BATCH, "num_predict": request.max_tokens},
    }  # fmt: skip

    def post(payload: dict) -> dict:
        req = urllib.request.Request(f"{url}/api/chat", json.dumps(payload).encode(), {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as answer:
            return json.loads(answer.read())

    try:
        try:
            out = post(body)
        except urllib.error.HTTPError as e:  # a model without a thinking switch rejects the "think" field
            message = e.read().decode(errors="ignore")
            if e.code == 400 and "think" in message.lower():
                out = post({k: v for k, v in body.items() if k != "think"})
            else:
                sys.stderr.write(f"ollama: HTTP {e.code}: {message[:300]}\n")  # e.g. out of memory at this context size
                return None
    except urllib.error.URLError as e:
        sys.stderr.write(f"ollama: {e.reason}\n")
        return None
    reason = out.get("done_reason") or ""
    if out.get("prompt_eval_count", 0) >= OLLAMA_NUM_CTX - 32:  # the prompt filled the context: its start may be cut
        sys.stderr.write(f"ollama: the prompt filled the context of {OLLAMA_NUM_CTX} tokens; answer treated as truncated\n")
        reason = "length"
    return {
        "id": "local", "model": request.model, "stop_details": None,
        "stop_reason": "max_tokens" if reason == "length" else "end_turn",
        "content": [{"type": "text", "text": (out.get("message") or {}).get("content", "")}],
        "usage": {"input_tokens": out.get("prompt_eval_count", 0), "output_tokens": out.get("eval_count", 0)},
        "_local": {k: out.get(k) for k in ("total_duration", "load_duration", "prompt_eval_duration", "eval_duration")},
    }  # fmt: skip


def openai_message(out: Mapping, model: str) -> dict:
    """An answer of OpenAI's Chat Completions API in the Messages API's shape. Usage: input_tokens excludes the cached
    prompt tokens, as on the Claude API; output_tokens includes the reasoning tokens, which are billed as output and
    also kept apart. A refusal or a content filter is a refusal; a cut-off answer is truncated."""
    choice = (out.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    finish = choice.get("finish_reason") or ""
    usage = out.get("usage") or {}
    cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens") or 0
    stop = "refusal" if message.get("refusal") or finish == "content_filter" else "max_tokens" if finish == "length" else "end_turn"
    return {
        "id": out.get("id"), "model": model, "stop_reason": stop, "stop_details": {"finish_reason": finish, "refusal": message.get("refusal")},
        "content": [] if message.get("content") is None else [{"type": "text", "text": message["content"]}],
        "usage": {"input_tokens": usage.get("prompt_tokens", 0) - cached, "cache_read_input_tokens": cached,
                  "output_tokens": usage.get("completion_tokens", 0),
                  "reasoning_tokens": (usage.get("completion_tokens_details") or {}).get("reasoning_tokens", 0)},
        "_served_by": out.get("model"),
    }  # fmt: skip


def send_openai(request: Request, url: str = OPENAI_URL, timeout: float = 600.0, max_retries: int = 3) -> dict | None:
    """One call to an OpenAI model (the critic, D56), returned in the API's message shape. The answer is constrained
    to the request's JSON schema (strict); `effort` is the reasoning effort. A rate limit, a server error or a lost
    connection is retried with a growing wait; after `max_retries` it is the "api" outcome (None, not cached). Any
    other rejection is a bug in our request and raises."""
    import urllib.error
    import urllib.request

    body = {
        "model": request.model.removeprefix(OPENAI_PREFIX), "reasoning_effort": request.effort, "max_completion_tokens": request.max_tokens,
        "messages": [{"role": "system", "content": request.system}] + [{"role": r, "content": t} for r, t in request.messages],
        "response_format": {"type": "json_schema", "json_schema": {"name": request.role, "strict": True, "schema": json.loads(request.schema)}},
    }  # fmt: skip
    headers = {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}", "Content-Type": "application/json"}
    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, json.dumps(body).encode(), headers), timeout=timeout) as answer:
                raw = openai_message(json.loads(answer.read()), request.model)
                raw["_request_id"] = answer.headers.get("x-request-id")
                return raw
        except urllib.error.HTTPError as e:
            message = e.read().decode(errors="ignore")
            if e.code != 429 and e.code < 500:
                raise RuntimeError(f"openai: HTTP {e.code}: {message[:500]}") from None  # our request is wrong
            wait = float(e.headers.get("retry-after") or 2 ** (attempt + 1))
            sys.stderr.write(f"openai: HTTP {e.code}, retry in {wait:.0f}s\n")
        except (urllib.error.URLError, TimeoutError) as e:
            wait = 2 ** (attempt + 1)
            sys.stderr.write(f"openai: {getattr(e, 'reason', e)}, retry in {wait}s\n")
        if attempt < max_retries:
            time.sleep(wait)
    return None


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
        default_log = "offline_lookups.jsonl" if os.environ.get(OFFLINE) else "calls.jsonl"  # a reproduction logs apart (git-ignored)
        self.log_path = Path(log_path) if log_path else self.cache_dir / default_log
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
        """Cache and log a new answer; a batched one carries `_batch` in its raw message and costs the batch price.
        An answer already in the cache (a batch collected twice) is logged as cached, so it is not counted as paid."""
        path = self.cache_dir / f"{request.key}.json"
        response = interpret(request, raw, latency, cached=path.exists())
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        record = {"request": {**asdict(request), "messages": list(request.messages)}, "raw": dict(raw), "latency": latency}
        path.write_text(json.dumps(record))
        self._log(request, response, transport)
        return response

    def failed(self, request: Request, latency: float, transport: str) -> Response:
        """Log a call the API did not answer (not cached, so a rerun tries again); the "api" outcome."""
        response = Response(request.key, request.role, request.model, "", "api", latency=latency)
        self._log(request, response, transport)
        return response

    def _send(self, request: Request) -> dict | None:
        import anthropic

        if os.environ.get(OFFLINE):
            raise RuntimeError(f"{OFFLINE} is set and a {request.role} request is not in the cache: nothing is sent")
        if request.model.startswith(LOCAL_PREFIX):
            return send_local(request)
        if request.model.startswith(OPENAI_PREFIX):
            load_dotenv()
            return send_openai(request, max_retries=self.max_retries)
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
            "price_date": settings.PRICE_DATES.get(request.model, settings.PRICE_DATE),
        }  # fmt: skip
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with _LOG_LOCK, self.log_path.open("a") as log:
            log.write(json.dumps(record) + "\n")
