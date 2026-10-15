"""The writer's prompts, as files: system.md (role, rules, the lexicon's words, the DSL, the answer format),
propose.md (wraps the handover), repair.md (wraps the verifier's problems) and advice.json (the lines of a repair
message: what failed, and the advice per kind of failure, gate/advice.py).

Change control (§14.14): after the pilot, freeze() writes the prompts' hashes to frozen.json, and from then on a
test fails if a frozen prompt changes. A changed prompt after the freeze is a new version: logged, E3 rerun.

Versions: v1 ran the smoke test, the naming check and the first pilot (results/pilot/v1/); v2 states the lexicon's
rules for turning bands into words, after the v1 pilot's errors (plan §14.14); v3 (15 Oct) moves the repair
messages into advice.json, under the freeze, and makes the advice say why a claim failed (review items 12 and 13).
HISTORY keeps each earlier version's hashes; its text is in git history.

The extractor's prompts (week 6, §5.7) are versioned and frozen apart from the writer's: extract_system.md (role,
rules, the answer format), whose DSL section is the writer's table and DSL rules taken from system.md, so both read
the words the same way; and extract.md (the features and the text). EXTRACTOR_VERSION; frozen_extractor.json.
"""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).parent
NAMES = ("system", "propose", "repair", "advice")
FILES = {"advice": "advice.json"}  # the others are <name>.md
FROZEN = HERE / "frozen.json"
VERSION = "v3"
EXTRACTOR_NAMES = ("extract_system", "extract")
FROZEN_EXTRACTOR = HERE / "frozen_extractor.json"
EXTRACTOR_VERSION = "x3"  # x1, x2: the round-trip pilot runs in results/pilot/v3/live_x1/, live_x2/ (plan §14.15)
HISTORY = {
    "v2": {
        "system": "1d0ef6ad39ae0fa38faeded63764400b03f7a8202be677c5258d833fe3090363",
        "propose": "807eb0a35f777b44cb3ff1c2d667d83b24a5e93b862e87c7b431ccff63cb553f",
        "repair": "ca60695ce6da8607d0f7a74d7adb1a35a35773fcb934fe30855fe6420301dbdf",
    },
    "v1": {
        "system": "3ab395f8ad3a2cae4810b28e3e9fa99ac48e0c2d7ecb70bbbad9264c19fd5b82",
        "propose": "807eb0a35f777b44cb3ff1c2d667d83b24a5e93b862e87c7b431ccff63cb553f",
        "repair": "ca60695ce6da8607d0f7a74d7adb1a35a35773fcb934fe30855fe6420301dbdf",
    },
}


def load(name: str) -> str:
    return (HERE / FILES.get(name, f"{name}.md")).read_text()


def advice() -> dict[str, str]:
    return json.loads(load("advice"))


def dsl_reference() -> str:
    """The writer's DSL table and the rules of the DSL, from system.md: the one source of what the words mean."""
    lines = load("system").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("| Words in the text |"))
    end = next(i for i, line in enumerate(lines) if line.startswith("Rules of the DSL:"))
    return "\n".join(lines[start : end + 1])


def extractor_system() -> str:
    return load("extract_system").replace("{dsl}", dsl_reference())


def _texts(names: tuple[str, ...]) -> dict[str, str]:
    return {name: extractor_system() if name == "extract_system" else load(name) for name in names}


def hashes(names: tuple[str, ...] = NAMES) -> dict[str, str]:
    return {name: hashlib.sha256(text.encode()).hexdigest() for name, text in _texts(names).items()}


def frozen(path: Path = FROZEN) -> dict[str, str] | None:
    return json.loads(path.read_text()) if path.exists() else None


def freeze(names: tuple[str, ...] = NAMES, path: Path = FROZEN) -> dict[str, str]:
    current = hashes(names)
    path.write_text(json.dumps(current, indent=1) + "\n")
    return current
