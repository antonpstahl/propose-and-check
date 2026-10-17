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
x3 (frozen 15 Oct) ran E3 and the first text-level E2; x4 (15 Oct, after text-level E2, plan §14.17) writes a
statement about a feature the list does not have as a claim with the text's name, so that the verifier finds the
term unknown, where x3 filed it as content without a DSL form (M9: 36% caught). EXTRACTOR_HISTORY keeps x3's hashes.

The local spot check's prompts (D49), versioned and frozen apart from both: system_local.md (the writer of an
adverse-action notice's reasons, with the local DSL table), propose_local.md (wraps the notice's handover),
extract_local_system.md (the extractor, x4's rules for a notice, whose DSL section is system_local.md's table) and
advice_local.json (the repair lines that differ for a notice; the rest of advice.json applies). The repair message
(repair.md) is shared. LOCAL_VERSION; frozen_local.json, written after the local pilot.
"""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).parent
NAMES = ("system", "propose", "repair", "advice")
FILES = {"advice": "advice.json", "advice_local": "advice_local.json"}  # the others are <name>.md
FROZEN = HERE / "frozen.json"
VERSION = "v3"
EXTRACTOR_NAMES = ("extract_system", "extract")
FROZEN_EXTRACTOR = HERE / "frozen_extractor.json"
EXTRACTOR_VERSION = "x4"  # x1, x2: the round-trip pilot runs in results/pilot/v3/live_x1/, live_x2/ (plan §14.15)
LOCAL_NAMES = ("system_local", "propose_local", "extract_local_system", "advice_local")
FROZEN_LOCAL = HERE / "frozen_local.json"
LOCAL_VERSION = "l1"
EXTRACTOR_HISTORY = {
    "x3": {
        "extract_system": "55b93253eeba587e88bc1c1aebf4759e1a46b4c66baa3540bac6b1cb192cb127",
        "extract": "1fb9d7d60625c4d412f19100c9dae3191f9713f30871292772bc81bdf3bac65a",
    },
}
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


def advice(local: bool = False) -> dict[str, str]:
    """The repair message's lines; for a notice, with advice_local.json's lines in place of the global ones."""
    return json.loads(load("advice")) | (json.loads(load("advice_local")) if local else {})


def dsl_reference(source: str = "system") -> str:
    """The writer's DSL table and the rules of the DSL, from system.md (system_local.md for a notice): the one
    source of what the words mean."""
    lines = load(source).splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("| Words in the text |"))
    end = next(i for i, line in enumerate(lines) if line.startswith("Rules of the DSL:"))
    return "\n".join(lines[start : end + 1])


def extractor_system(local: bool = False) -> str:
    if local:
        return load("extract_local_system").replace("{dsl}", dsl_reference("system_local"))
    return load("extract_system").replace("{dsl}", dsl_reference())


def _text(name: str) -> str:
    if name in ("extract_system", "extract_local_system"):
        return extractor_system(local=name == "extract_local_system")
    return load(name)


def _texts(names: tuple[str, ...]) -> dict[str, str]:
    return {name: _text(name) for name in names}


def hashes(names: tuple[str, ...] = NAMES) -> dict[str, str]:
    return {name: hashlib.sha256(text.encode()).hexdigest() for name, text in _texts(names).items()}


def frozen(path: Path = FROZEN) -> dict[str, str] | None:
    return json.loads(path.read_text()) if path.exists() else None


def freeze(names: tuple[str, ...] = NAMES, path: Path = FROZEN) -> dict[str, str]:
    current = hashes(names)
    path.write_text(json.dumps(current, indent=1) + "\n")
    return current
