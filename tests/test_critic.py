"""The LLM critic (D56): OpenAI's answers in the Messages API's shape, the critic's request and answer, and the
comparison with the gate (experiments/e2_critic.py). No network."""

import hashlib
import json
import math

import pandas as pd
import pytest

from verifier_gate.experiments import e2_critic
from verifier_gate.llm import client as c
from verifier_gate.llm import critique, prompts, settings


def openai_answer(content: str | None = '{"problems": [], "p_error": 0.1}', finish: str = "stop", refusal: str | None = None) -> dict:
    return {
        "id": "chatcmpl-1", "model": "gpt-6-luna-2026",
        "choices": [{"finish_reason": finish, "message": {"role": "assistant", "content": content, "refusal": refusal}}],
        "usage": {"prompt_tokens": 3000, "completion_tokens": 900, "prompt_tokens_details": {"cached_tokens": 1000},
                  "completion_tokens_details": {"reasoning_tokens": 800}},
    }  # fmt: skip


def test_an_openai_answer_is_a_message_whose_usage_excludes_cached_input_and_includes_reasoning():
    raw = c.openai_message(openai_answer(), settings.CRITIC)
    assert raw["stop_reason"] == "end_turn" and raw["content"] == [{"type": "text", "text": '{"problems": [], "p_error": 0.1}'}]
    assert raw["usage"] == {"input_tokens": 2000, "cache_read_input_tokens": 1000, "output_tokens": 900, "reasoning_tokens": 800}
    assert c.cost(settings.CRITIC, raw["usage"]) == pytest.approx((2000 * 0.10 + 1000 * 0.01 + 900 * 0.50) / 1e6)


def test_an_openai_refusal_or_cut_off_answer_is_never_parsed():
    request = critique.critic_request("facts", [[1, "Risk rises."]])
    refused = c.interpret(request, c.openai_message(openai_answer(None, refusal="I can't help"), settings.CRITIC), 0.0, False)
    filtered = c.interpret(request, c.openai_message(openai_answer(None, finish="content_filter"), settings.CRITIC), 0.0, False)
    cut = c.interpret(request, c.openai_message(openai_answer('{"problems": [', finish="length"), settings.CRITIC), 0.0, False)
    assert (refused.error, filtered.error, cut.error) == ("refusal", "refusal", "truncated")


def test_an_openai_request_goes_nowhere_under_the_offline_switch(tmp_path, monkeypatch):
    monkeypatch.setenv(c.OFFLINE, "1")
    with pytest.raises(RuntimeError, match="not in the cache"):
        c.Client("sync", cache_dir=tmp_path).call(critique.critic_request("facts", [[1, "Risk rises."]]))


def test_the_critic_gets_the_writers_rules_the_facts_and_the_text():
    request = critique.critic_request("FACTS HERE", [[1, "Risk rises with utilization."], [2, "Age hardly matters."]], version="c1")
    assert request.role == "critic" and request.model == settings.CRITIC and request.effort == settings.CRITIC_EFFORT
    assert prompts.word_rules("v3") in request.system and "{rules}" not in request.system
    assert prompts.word_rules("v3").startswith("# Choosing the words") and "# The claims" not in prompts.word_rules("v3")
    user = request.messages[0][1]
    assert user.index("FACTS HERE") < user.index("1. Risk rises with utilization.\n2. Age hardly matters.")  # facts first: a shared prefix
    assert json.loads(request.schema)["required"] == ["problems", "p_error"]
    assert critique.critic_request("FACTS HERE", [[1, "x"]], model=settings.CRITIC_STRONG).key != critique.critic_request("FACTS HERE", [[1, "x"]]).key


def test_c2_gets_the_writers_whole_set_of_rules_with_the_dsl_table():
    c1, c2 = (critique.critic_request("FACTS", [[1, "x"]], version=v) for v in ("c1", "c2"))
    rules = prompts.writer_rules("v3")
    assert rules in c2.system and prompts.word_rules("v3") in rules and rules not in c1.system
    assert rules.startswith("# The text") and "| Words in the text | DSL claim | Meaning |" in rules and "# The claims" not in rules
    assert "Return one JSON object with two lists" not in rules  # the writer's answer format is not a rule for the critic
    assert c1.messages == c2.messages and c1.key != c2.key  # the same facts and text give another request


def test_both_critic_versions_read_e3s_writer_prompt_v3():
    assert hashlib.sha256(prompts.writer_system("v3").encode()).hexdigest() == prompts.WRITER_SYSTEM["v3"]
    assert prompts.critic_system("c1") == prompts.load("critic_system").replace("{rules}", prompts.word_rules("v3"))


@pytest.mark.parametrize("version", sorted(prompts.CRITIC_NAMES))
def test_critic_prompt_hashes_are_frozen_after_the_pilot(version):
    """The assembled critic prompt includes the writer's rules, so a change there shows here too."""
    frozen = prompts.frozen(prompts.FROZEN_CRITIC[version])
    if frozen is None:
        pytest.skip(f"critic prompts {version} not frozen yet")
    assert prompts.hashes(prompts.CRITIC_NAMES[version]) == frozen


def test_c2_gets_the_handover_each_writer_saw_from_e3s_run_traces():
    h1, h2 = (f"syn-dominant-n5000-s2_EBM_{v}_d0_claude-haiku-5-5_opaque" for v in ("H1", "H2"))
    texts = [e2_critic.writer_handover(run) for run in (h1, h2)]
    assert all(t.startswith("Model: ") for t in texts) and not any("Write the explanation" in t for t in texts)
    assert "Statements the verifier certifies" in texts[1] and "Statements the verifier certifies" not in texts[0]
    assert texts[1].startswith(texts[0])  # H2 is H1 and the certified statements
    case = lambda source, info=None: e2_critic.Case("L001" if source == "llm" else h2, source, "syn-dominant-n5000-s2", "EBM", "opaque", [], [], None, info or {})  # noqa: E731
    assert e2_critic.written_by(case("e3")) == h2 and e2_critic.written_by(case("llm", {"gate case": h1})) == h1
    assert e2_critic.written_by(case("control")) == h1  # a template text: the H1 of its cell


def test_kappa_of_two_checkers():
    a, b = pd.Series([True, True, False, False]), pd.Series([True, False, False, False])
    assert e2_critic.kappa(a, a) == 1.0 and e2_critic.kappa(a, b) == pytest.approx(0.5)


def response(data) -> c.Response:
    return c.Response("k", "critic", settings.CRITIC, "end_turn", "", json.dumps(data), data)


def test_a_critique_keeps_problems_by_sentence_and_files_unknown_ids_with_the_whole_text():
    out = critique.critique_from(response({"problems": [{"sentence_id": 2, "problem": "too strong"}, {"sentence_id": 9, "problem": "x"},
                                                        {"sentence_id": 0, "problem": "income not mentioned"}], "p_error": 1.3}), {1, 2})  # fmt: skip
    assert out.problems == {2: ["too strong"], 0: ["x", "income not mentioned"]} and out.blocks and out.p_error == 1.0
    assert not critique.critique_from(response({"problems": [], "p_error": 0.2}), {1}).blocks
    with pytest.raises(ValueError):
        critique.critique_from(response({"sentences": []}), {1})


def table(rows: list[dict]) -> pd.DataFrame:
    base = {"critiqued": True, "source": "script", "operator": "M1", "p_error": 0.5, "gate at the change": True}
    return pd.DataFrame([base | r for r in rows])


def test_critic_and_gate_are_scored_on_the_same_cases():
    t = table([
        {"role": "error", "blocked": True, "at the change": True, "gate caught": True, "p_error": 0.95},
        {"role": "error", "blocked": False, "at the change": False, "gate caught": True, "p_error": 0.05},  # a confident miss
        {"role": "control text", "source": "control", "operator": "", "blocked": True, "at the change": False, "gate caught": False,
         "gate at the change": False, "p_error": 0.97},  # a confident false alarm
        {"role": "error", "blocked": True, "at the change": True, "gate caught": None},  # the gate has no outcome: left out
    ])  # fmt: skip
    s = e2_critic.summarise(t).set_index(["cases", "checker"])
    assert s.loc[("script, all operators", "critic"), "recall"] == 0.5 and s.loc[("script, all operators", "gate"), "recall"] == 1.0
    assert s.loc[("template texts, unchanged", "critic"), "false alarms"] == 1 and s.loc[("template texts, unchanged", "gate"), "false alarms"] == 0
    conf = s.loc[("all labelled", "critic")]
    assert conf["errors passed with p_error <= 0.1"] == 1 and conf["correct blocked with p_error >= 0.9"] == 1
    assert conf["brier"] == pytest.approx(((0.95 - 1) ** 2 + (0.05 - 1) ** 2 + 0.97**2) / 3, abs=1e-4)


def test_a_blocked_e3_text_is_a_real_error_if_any_flag_is_right_and_a_false_alarm_only_if_all_are_wrong(tmp_path):
    (tmp_path / "key.csv").write_text("item,case,sentence_id,problems,p_error\nC001,a,1,1,0.9\nC002,a,3,1,0.9\nC003,b,2,2,0.8\nC004,c,1,1,0.7\n")
    labels = {"C001": {"labels": {"0": "misreading"}}, "C002": {"labels": {"0": "error"}}, "C003": {"labels": {"0": "misreading", "1": "misreading"}},
              "C004": {"labels": {"0": "unsure"}}}  # fmt: skip
    (tmp_path / "labels.json").write_text(json.dumps(labels))
    pd.DataFrame([{"extractor": "x4", "texts scored": 10, "blocked": 1, "real errors": 0, "false alarms": 1, "open": 0,
                   "false-alarm rate (per correct text)": 0.1}]).to_csv(tmp_path / "gate.csv", index=False)  # fmt: skip
    cases = pd.DataFrame([{"case": x, "source": "e3", "critiqued": True, "blocked": x in "abc"} for x in "abcdefghij"])
    out = e2_critic.score_e3(cases, tmp_path, tmp_path / "labels.json", tmp_path / "gate.csv").set_index("checker")
    critic = out.loc["critic"]
    assert (critic["real error (labelled)"], critic["false alarm (labelled)"], critic["open (labelled)"]) == (1, 1, 1)
    # 10 texts, 3 blocked, all labelled: 1 real error and 1 open leave 8 correct texts, 1 of them blocked
    assert critic["false-alarm rate (per correct text)"] == pytest.approx(round(1 / 8, 3)) and not math.isnan(critic["false-alarm rate (per correct text)"])
