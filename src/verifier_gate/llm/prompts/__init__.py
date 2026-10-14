"""The writer's prompts, as files: system.md (role, rules, the lexicon's words, the DSL, the answer format),
propose.md (wraps the handover) and repair.md (wraps the verifier's problems).

Change control (§14.14): after the pilot, freeze() writes the prompts' hashes to frozen.json, and from then on a
test fails if a frozen prompt changes. A changed prompt after the freeze is a new version: logged, E3 rerun.
"""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).parent
NAMES = ("system", "propose", "repair")
FROZEN = HERE / "frozen.json"


def load(name: str) -> str:
    return (HERE / f"{name}.md").read_text()


def hashes() -> dict[str, str]:
    return {name: hashlib.sha256(load(name).encode()).hexdigest() for name in NAMES}


def frozen() -> dict[str, str] | None:
    return json.loads(FROZEN.read_text()) if FROZEN.exists() else None


def freeze() -> dict[str, str]:
    current = hashes()
    FROZEN.write_text(json.dumps(current, indent=1) + "\n")
    return current
