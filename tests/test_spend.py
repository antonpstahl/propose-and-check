"""The spend counts each paid request once, by its costliest live answer (D81)."""

import json

from verifier_gate.experiments import spend


def test_a_failed_attempt_and_a_twice_collected_answer_are_counted_once_at_their_price(tmp_path, monkeypatch):
    rows = [
        {"key": "a", "cost": 0.0, "error": "api"},  # failed for lack of credits: not paid
        {"key": "a", "cost": 0.01, "error": ""},  # the retry, paid
        {"key": "b", "cost": 0.02, "error": ""},
        {"key": "b", "cost": 0.02, "error": ""},  # the same batch answer collected twice
        {"key": "c", "cost": 0.03, "error": "not a reading"},  # paid, though unusable
    ]
    log = tmp_path / "calls.jsonl"
    log.write_text("".join(json.dumps(r | {"time": f"2026-10-21T16:0{k}", "cached": False, "transport": "sync", "model": "m", "role": "scorer"}) + "\n"
                           for k, r in enumerate(rows)))  # fmt: skip
    monkeypatch.setattr(spend, "LOG", log)
    frame = spend.paid()
    assert len(frame) == 3 and round(frame.cost.sum(), 6) == 0.06
