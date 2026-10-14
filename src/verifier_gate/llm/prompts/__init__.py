"""The writer's prompts, as files: system.md (role, rules, the lexicon's words, the DSL, the answer format),
propose.md (wraps the handover) and repair.md (wraps the verifier's problems).

Change control (§14.14): after the pilot, freeze() writes the prompts' hashes to frozen.json, and from then on a
test fails if a frozen prompt changes. A changed prompt after the freeze is a new version: logged, E3 rerun.

Versions: v1 ran the smoke test, the naming check and the first pilot (results/pilot/v1/); v2 states the lexicon's
rules for turning bands into words, after the v1 pilot's errors (plan §14.14). HISTORY keeps each earlier
version's hashes; its text is in git history.
"""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).parent
NAMES = ("system", "propose", "repair")
FROZEN = HERE / "frozen.json"
VERSION = "v2"
HISTORY = {
    "v1": {
        "system": "3ab395f8ad3a2cae4810b28e3e9fa99ac48e0c2d7ecb70bbbad9264c19fd5b82",
        "propose": "807eb0a35f777b44cb3ff1c2d667d83b24a5e93b862e87c7b431ccff63cb553f",
        "repair": "ca60695ce6da8607d0f7a74d7adb1a35a35773fcb934fe30855fe6420301dbdf",
    },
}


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
