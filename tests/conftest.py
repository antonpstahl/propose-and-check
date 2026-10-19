"""Shared test setup. The reproduction's offline switch (VERIFIER_GATE_OFFLINE, llm/client.py) sends the call log to
offline_lookups.jsonl and refuses uncached requests; the tests must not depend on whether it is set in the shell."""

import pytest

from verifier_gate.llm.client import OFFLINE


@pytest.fixture(autouse=True)
def _without_the_offline_switch(monkeypatch):
    monkeypatch.delenv(OFFLINE, raising=False)
