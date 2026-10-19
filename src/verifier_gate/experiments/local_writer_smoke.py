"""D55 smoke test: can a local open-weight model on this machine serve as the writer? One call, $0.

The writer's request of the worked example (syn-dominant-n50000-s1, XGB2, handover H1, plausible names, prompts v3),
sent to a local model on the Ollama server instead of Claude Haiku 5.5. Reports what decides whether a 72-run subset
is worth starting: whether the model is loaded and how much of it sits in GPU memory, the time and the tokens per
second, whether the answer is valid JSON in the schema, how many DSL lines parse, and the plan check's verdicts (how
many claims the verifier certifies). The answer is cached like any other, so a later run reuses it.

Run (after `ollama pull <tag>`): `uv run python -m verifier_gate.experiments.local_writer_smoke --model ollama/<tag>`.
"""

import argparse
import json
import time
import urllib.request
from collections import Counter

from verifier_gate.data import dgp, labels
from verifier_gate.experiments.build_facts import load
from verifier_gate.gate import gate as g
from verifier_gate.llm import propose
from verifier_gate.llm.client import LOCAL_PREFIX, OLLAMA_NUM_CTX, OLLAMA_URL, Client
from verifier_gate.llm.handover import handover
from verifier_gate.verifier.certified import certified_plan

SCENARIO, MODEL = "syn-dominant-n50000-s1", "XGB2"


def ollama(path: str) -> dict:
    with urllib.request.urlopen(f"{OLLAMA_URL}{path}", timeout=10) as answer:
        return json.loads(answer.read())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help=f"{LOCAL_PREFIX}<tag>, e.g. {LOCAL_PREFIX}qwen3.6:27b")
    args = parser.parse_args()
    if not args.model.startswith(LOCAL_PREFIX):
        raise SystemExit(f"the model must start with {LOCAL_PREFIX!r}")
    tag = args.model.removeprefix(LOCAL_PREFIX)
    try:
        installed = [m["name"] for m in ollama("/api/tags").get("models", [])]
    except OSError:
        raise SystemExit(f"no Ollama server at {OLLAMA_URL}: start it with `ollama serve`")
    if tag not in installed:
        raise SystemExit(f"{tag} is not pulled yet; installed: {installed or 'none'}")

    scenario = next(s for s in dgp.SCENARIOS if s.id == SCENARIO)
    facts = load(scenario, MODEL)
    certified = certified_plan(facts)
    text = handover(facts, dgp.generate(scenario).X, "H1", certified, names=labels.SYNTHETIC_NAMES).text
    request = propose.proposer_request(text, model=args.model)
    print(f"writer request: {len(request.system) + len(request.messages[0][1]):,} characters; context window {OLLAMA_NUM_CTX:,} tokens")
    t0 = time.perf_counter()
    response = Client("sync").call(request)
    seconds = time.perf_counter() - t0
    if response.error == "api":
        raise SystemExit("the Ollama server did not answer (out of memory, or the model failed to load)")
    loaded = next((m for m in ollama("/api/ps").get("models", []) if m.get("name") == tag), None)
    if loaded:
        size, vram = loaded.get("size", 0), loaded.get("size_vram", 0)
        print(f"loaded: {size / 2**30:.1f} GB, of which {vram / 2**30:.1f} GB in GPU memory ({vram / max(size, 1):.0%})")
    out_tokens = response.usage.get("output_tokens", 0)
    print(f"answer: {seconds:.0f} s{' (from the cache)' if response.cached else ''}; {response.usage.get('input_tokens', 0):,} tokens in, "
          f"{out_tokens:,} out" + (f", {out_tokens / seconds:.1f} tokens/s" if not response.cached and seconds else ""))  # fmt: skip
    if response.error:
        raise SystemExit(f"not a usable answer: {response.error}")
    try:
        draft = propose.draft_from(response, "proposer", labels.SYNTHETIC_NAMES)
    except (ValueError, KeyError, TypeError) as e:
        raise SystemExit(f"valid JSON, but not a draft: {e}")
    version = g.check(draft, g.Context(facts, certified))
    verdicts = Counter(c[2] for c in version.claims)
    print(f"draft: {len(draft.sentences)} sentences, {len(draft.claims)} DSL lines parsed, {len(draft.format_errors)} did not parse")
    print(f"plan check: {dict(verdicts)}; required terms not covered: {version.missing or 'none'}")
    for i, sentence in draft.sentences:
        print(f"  {i}. {sentence}")
    for c in version.claims:
        if c[2] != "true":
            print(f"     [{c[0]}] {c[1]} -> {c[2]} | {c[5][:100]}")


if __name__ == "__main__":
    main()
