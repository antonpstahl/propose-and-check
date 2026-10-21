"""The Claude API wrapper (llm/client.py) in stub mode: no network."""

import json

import pytest

from verifier_gate.llm import client as c
from verifier_gate.llm import settings

SCHEMA = json.dumps({"type": "object", "properties": {"x": {"type": "integer"}}, "required": ["x"], "additionalProperties": False})


def request(**changes) -> c.Request:
    fields = dict(role="proposer", model=settings.WRITER, system="You write.", messages=(("user", "facts"),), schema=SCHEMA)
    return c.Request(**(fields | changes))


def scripted(*messages):
    """A stub responder returning the given raw messages in turn, counting its calls."""
    calls = []

    def respond(req):
        calls.append(req)
        return messages[min(len(calls), len(messages)) - 1]

    return respond, calls


def test_the_cache_key_covers_the_call_and_the_draw_but_not_the_role():
    assert request().key == request(role="extractor").key
    assert request().key != request(draw=1).key
    assert request().key != request(system="You write well.").key
    assert request().key != request(model=settings.WRITER_SUBSET).key


def test_params_cache_the_system_prompt_and_put_schema_and_effort_in_output_config():
    p = request().params()
    assert p["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert p["output_config"] == {"format": {"type": "json_schema", "schema": json.loads(SCHEMA)}, "effort": settings.EFFORT}
    assert "temperature" not in p  # current models reject sampling parameters (D38)
    assert p["thinking"] == {"type": "disabled"}


def test_thinking_off_is_model_specific():
    assert c.thinking_param("claude-haiku-5-5", "off", "medium") == {"type": "disabled"}
    assert c.thinking_param("claude-sonnet-5-5", "off", "low") == {"type": "between_tools"}
    assert c.thinking_param("claude-opus-5-5", "adaptive", "low") == {"type": "adaptive"}
    with pytest.raises(ValueError):
        c.thinking_param("claude-opus-5-5", "off", "low")  # cannot be switched off
    with pytest.raises(ValueError):
        c.thinking_param("claude-haiku-5-5", "off", "xhigh")


def test_a_call_is_parsed_cached_and_logged(tmp_path):
    respond, calls = scripted(c.stub_message({"x": 3}, usage={"input_tokens": 2000, "output_tokens": 500, "cache_read_input_tokens": 4000}))
    client = c.Client("stub", respond, cache_dir=tmp_path)
    first = client.call(request())
    assert first.ok and first.data == {"x": 3} and not first.cached
    assert first.cost == pytest.approx((2000 * 0.10 + 4000 * 0.01 + 500 * 0.50) / 1e6)
    second = client.call(request())
    assert second.cached and second.data == {"x": 3} and len(calls) == 1  # not sent again
    log = [json.loads(line) for line in (tmp_path / "calls.jsonl").read_text().splitlines()]
    assert [r["cached"] for r in log] == [False, True]
    assert {"stop_reason", "usage", "cost", "system_hash", "messages_hash", "draw", "price_date"} <= set(log[0])


def test_a_new_draw_is_a_new_call(tmp_path):
    respond, calls = scripted(c.stub_message({"x": 1}), c.stub_message({"x": 2}))
    client = c.Client("stub", respond, cache_dir=tmp_path)
    assert client.call(request(draw=0)).data == {"x": 1}
    assert client.call(request(draw=1)).data == {"x": 2}
    assert len(calls) == 2


@pytest.mark.parametrize(
    "message, error",
    [
        (c.stub_message('{"x": 3', stop_reason="max_tokens"), "truncated"),
        (c.stub_message('{"x": 3}', stop_reason="max_tokens"), "truncated"),  # never parsed, even if it would parse
        (c.stub_message(None, stop_reason="refusal"), "refusal"),
        (c.stub_message("not json"), "invalid_json"),
        (c.stub_message(None), "no_text"),
    ],
)
def test_truncated_refused_and_broken_answers_are_not_parsed(tmp_path, message, error):
    respond, _ = scripted(message)
    response = c.Client("stub", respond, cache_dir=tmp_path).call(request())
    assert response.error == error and response.data is None


def test_an_api_failure_is_not_cached(tmp_path):
    respond, calls = scripted(None, c.stub_message({"x": 5}))
    client = c.Client("stub", respond, cache_dir=tmp_path)
    assert client.call(request()).error == "api"
    assert client.call(request()).data == {"x": 5} and len(calls) == 2  # tried again


def test_batch_prices_are_half():
    usage = {"input_tokens": 1_000_000, "output_tokens": 1_000_000}
    assert c.cost("claude-haiku-5-5", usage, batch=True) == pytest.approx(0.30)
    assert c.cost("claude-sonnet-5-5", usage) == pytest.approx(12.0)


def test_the_dotenv_loader_reads_spaced_lines_and_never_overrides(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("# the key\nANTHROPIC_API_KEY = sk-test-123\nEMPTY =\nQUOTED='x y'\n")
    for key in ("ANTHROPIC_API_KEY", "QUOTED"):  # record the original state, so nothing leaks into later tests
        monkeypatch.setenv(key, "placeholder")
        monkeypatch.delenv(key)
    monkeypatch.setenv("KEEP", "1")
    assert sorted(c.load_dotenv(env)) == ["ANTHROPIC_API_KEY", "QUOTED"]
    import os

    assert os.environ["ANTHROPIC_API_KEY"] == "sk-test-123" and os.environ["QUOTED"] == "x y"
    env.write_text("KEEP = 2\n")
    assert c.load_dotenv(env) == [] and os.environ["KEEP"] == "1"


def test_a_local_model_answers_in_the_api_shape_and_costs_nothing(monkeypatch):
    import io
    import urllib.request

    from verifier_gate.llm import client as c

    sent = {}

    def fake_urlopen(req, timeout=None):
        sent["body"] = json.loads(req.data)
        answer = {"message": {"content": json.dumps({"sentences": [], "claims": []})}, "done_reason": "stop",
                  "prompt_eval_count": 4800, "eval_count": 700, "total_duration": 9}  # fmt: skip
        return io.BytesIO(json.dumps(answer).encode())

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    request = c.Request("proposer", "ollama/qwen-test", "system text", (("user", "the facts"),), json.dumps({"type": "object"}))
    raw = c.send_local(request)
    assert sent["body"]["model"] == "qwen-test" and sent["body"]["think"] is False and sent["body"]["format"] == {"type": "object"}
    assert sent["body"]["messages"][0] == {"role": "system", "content": "system text"}
    response = c.interpret(request, raw, latency=1.0, cached=False)
    assert response.ok and response.data == {"sentences": [], "claims": []} and response.cost == 0.0
    assert response.usage == {"input_tokens": 4800, "output_tokens": 700}


def test_the_call_log_is_read_across_its_closed_parts_in_order(tmp_path):
    """D80: closing the log moves it, byte for byte, into a gzipped part; the reader sees every record in the order
    written, the closed parts first; the same log closes to the same bytes; an empty log is not closed."""
    log = tmp_path / "calls.jsonl"
    log.write_text("".join(json.dumps({"n": k}) + "\n" for k in range(3)))
    first = c.close_log(tmp_path)
    assert first.name == "calls-0001.jsonl.gz" and log.read_text() == "" and c.close_log(tmp_path) is None
    log.write_text(json.dumps({"n": 3}) + "\n")
    assert [r["n"] for r in c.log_records(tmp_path)] == [0, 1, 2, 3]
    again = tmp_path / "again"
    again.mkdir()
    (again / "calls.jsonl").write_text("".join(json.dumps({"n": k}) + "\n" for k in range(3)))
    assert c.close_log(again).read_bytes() == first.read_bytes()
