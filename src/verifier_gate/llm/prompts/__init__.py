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
(repair.md) is shared. LOCAL_VERSION; frozen_local.json, written after the local pilot. l1 (16 Oct) gave the writer
the refit bands and let it hedge; l2 (20 Oct, D68) gives M's exact numbers and its principal reasons, and forbids
hedging. LOCAL_HISTORY keeps l1's hashes.

The LLM critic's prompts (D56, plan §14.29), versioned and frozen apart from the others: critic_system.md (role,
what counts as unsupported, the answer format), whose rules section is the writer's "Choosing the words" from
system.md, so the critic judges by the rules the writer was given, and whose coverage and emphasis rules are the
round trip's (gate/roundtrip.py); and critic.md (the facts and the text). c1 ran first (frozen_critic.json, written
after the critic's pilot). c2 (M4 of the 20 Oct review) gets what the writer got: critic_system_c2.md, whose rules
section is the writer's whole set of rules ("# The text" and "# Choosing the words" from system.md, then the DSL
table with what each phrase claims), and, from experiments/e2_critic.py, the handover each writer saw (H2 for an H2
text). critic.md is shared. CRITIC_VERSION is the current one; CRITIC_NAMES and FROZEN_CRITIC are per version.

The plain-prompt arm of E3 (e3_baselines, M4): plain_system.md (the writer's role and the bullets of its "# The text"
that do not refer to the word table or the claims; no lexicon rules, no DSL, no plan) and plain.md (wraps the
handover). PLAIN_VERSION; frozen_plain.json, written after its pilot.

Writer v4 and extractor x5 (D65, lexicon v3): system_v4.md is a template whose rules for choosing words ({rules}),
DSL table ({table}) and numbers ({level}, ...) are rendered from the lexicon's words (lexicon/words.py), so no
threshold in the prompt is written by hand; advice_v4.json adds the advice for a jump of the wrong sign; frozen_v4.json
holds v4's hashes. x5 is extract_system.md, as in x4, with v4's DSL table (frozen_extractor_x5.json). The version
follows the lexicon (WRITER_VERSIONS, EXTRACTOR_VERSIONS): with VERIFIER_GATE_LEXICON=v2 (lexicon/predicates.PIN)
the writer's prompts are v3 (system.md, advice.json, frozen.json, all as frozen) and the extractor is x4, so every
step that replays a result run under v2 sends the same requests. history/x3/ keeps x3's extract_system.md, so that
its replay needs no git.
"""

import hashlib
import json
import subprocess
from pathlib import Path

from verifier_gate.lexicon import predicates

HERE = Path(__file__).parent
NAMES = ("system", "propose", "repair", "advice")
FILES = {"advice": "advice.json", "advice_local": "advice_local.json"}  # the others are <name>.md
FROZEN = HERE / "frozen.json"
WRITER_VERSIONS = {"v2": "v3", "v3": "v4"}  # the writer's prompts for each lexicon version (D65)
EXTRACTOR_VERSIONS = {"v2": "x4", "v3": "x5"}  # x5: x4's extract_system.md with v4's DSL table
WRITER_FILES = {"v4": {"system": "system_v4.md", "advice": "advice_v4.json"}}  # v3's are system.md and advice.json
FROZEN_VERSIONS = {"v3": FROZEN, "v4": HERE / "frozen_v4.json"}
FROZEN_EXTRACTOR_VERSIONS = {"x4": HERE / "frozen_extractor.json", "x5": HERE / "frozen_extractor_x5.json"}
EXTRACTOR_TABLES = {"x3": "v3"}  # the writer version whose DSL table an earlier extractor read


def writer_version() -> str:
    """The writer's prompt version for the default (pinned) lexicon."""
    return WRITER_VERSIONS[predicates.pinned()]


VERSION = writer_version()
EXTRACTOR_NAMES = ("extract_system", "extract")
FROZEN_EXTRACTOR = HERE / "frozen_extractor.json"
EXTRACTOR_VERSION = EXTRACTOR_VERSIONS[predicates.pinned()]  # x1, x2: the round-trip pilot runs in results/pilot/v3/live_x1/, live_x2/ (plan §14.15)
LOCAL_NAMES = ("system_local", "propose_local", "extract_local_system", "advice_local")
FROZEN_LOCAL = HERE / "frozen_local.json"
LOCAL_VERSION = "l2"
LOCAL_HISTORY = {
    "l1": {
        "system_local": "058da70bc4ff464fe705c3b0b8b83878a91c349ca7e89e6b514baee02cec059d",
        "propose_local": "0a9ffc3594ec92f091aba17a733968e9b7f618240742f1b2ca10030e70b80278",
        "extract_local_system": "ba2fe5846eb30a8ae5ea3b2cb74d36a1468cfd05cf1105dd3ed28aef3a0431b2",
        "advice_local": "d8a12c3987790540291b761729927983d7f7c26f064619084b7bff296d321f0d",
    },
}
CRITIC_VERSION = "c2"
CRITIC_NAMES = {"c1": ("critic_system", "critic"), "c2": ("critic_system_c2", "critic")}
FROZEN_CRITIC = {"c1": HERE / "frozen_critic.json", "c2": HERE / "frozen_critic_c2.json"}
PLAIN_NAMES = ("plain_system", "plain")
FROZEN_PLAIN = HERE / "frozen_plain.json"
PLAIN_VERSION = "p1"
EXTRACTOR_COMMITS = {"x3": "56c77b0a"}  # the last commit with each earlier extractor version (E3 ran with x3)
WRITER_COMMITS = {"v3": "c2a69dc4"}  # a commit with each writer version's system.md: writer_system's fallback
WRITER_SYSTEM = {"v3": "1d0ef6ad39ae0fa38faeded63764400b03f7a8202be677c5258d833fe3090363"}  # its hash (v3's system.md is v2's)
_PINNED: dict[str, str] = {}  # an earlier extractor version used for global readings, by pin_extractor
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
    """A prompt file; the writer's system prompt and advice of the writer version the lexicon gives
    (writer_version): v4's rendered from the lexicon (WRITER_FILES), v3's as frozen."""
    version = writer_version()
    if name in ("system", "advice") and version in WRITER_FILES:
        text = (HERE / WRITER_FILES[version][name]).read_text()
        return render(text) if name == "system" else text
    return (HERE / FILES.get(name, f"{name}.md")).read_text()


def render(template: str) -> str:
    """A writer template with the lexicon's words and numbers (D65): {rules}, {table}, and {level} and the other
    numbers of lexicon/words.numbers. Replaced by name, so the template's JSON example keeps its braces."""
    from verifier_gate.lexicon import words  # words reads the DSL, which reads the lexicon

    lex = predicates.load()
    text = template.replace("{rules}", words.rules(lex)).replace("{table}", words.table(lex))
    for name, value in words.numbers(lex).items():
        text = text.replace("{" + name + "}", value)
    return text


def advice(local: bool = False) -> dict[str, str]:
    """The repair message's lines; for a notice, with advice_local.json's lines in place of the global ones."""
    return json.loads(load("advice")) | (json.loads(load("advice_local")) if local else {})


def writer_system(version: str = "v3") -> str:
    """system.md as the writer of a version saw it, checked against its hash: the stored copy in history/<version>/,
    else system.md if it is that version, else from git. The critic's rules (c1, c2) are E3's writer's, v3."""
    stored = HERE / "history" / version / "system.md"
    candidates = [lambda: stored.read_text() if stored.exists() else "", lambda: (HERE / "system.md").read_text(),
                  lambda: subprocess.run(["git", "show", f"{WRITER_COMMITS[version]}:src/verifier_gate/llm/prompts/system.md"],
                                         cwd=HERE.parents[3], capture_output=True, text=True, check=True).stdout]  # fmt: skip
    for read in candidates:
        text = read()
        if hashlib.sha256(text.encode()).hexdigest() == WRITER_SYSTEM[version]:
            return text
    raise ValueError(f"no copy of the writer's system prompt {version} matches its hash")


def dsl_reference(source: str = "system", version: str | None = None) -> str:
    """The writer's DSL table and the rules of the DSL, from system.md (system_local.md for a notice; `version`: the
    writer prompt of that version, writer_system): the one source of what the words mean."""
    lines = (writer_system(version) if version else load(source)).splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("| Words in the text |"))
    end = next(i for i, line in enumerate(lines) if line.startswith("Rules of the DSL:"))
    return "\n".join(lines[start : end + 1])


def word_rules(version: str | None = None) -> str:
    """The writer's rules for choosing words ("# Choosing the words" up to "# The claims"), from system.md or from the
    writer prompt of `version` (writer_system)."""
    text = writer_system(version) if version else load("system")
    return text[text.index("# Choosing the words") : text.index("# The claims")].strip()


def writer_rules(version: str | None = None) -> str:
    """The writer's whole set of rules (critic c2): "# The text" and "# Choosing the words", then the DSL table, which
    says what each phrase claims; from system.md or from the writer prompt of `version`."""
    text = writer_system(version) if version else load("system")
    table = [line for line in dsl_reference(version=version).splitlines() if line.startswith("|")]
    return text[text.index("# The text") : text.index("# The claims")].strip() + "\n\n# What each phrase claims\n\n" + "\n".join(table)


def critic_system(version: str = CRITIC_VERSION) -> str:
    """c1: the rules section is the writer's "Choosing the words"; c2: the writer's whole set of rules. Both are E3's
    writer's, v3, whatever the current writer prompt is."""
    name = CRITIC_NAMES[version][0]
    return load(name).replace("{rules}", word_rules("v3") if version == "c1" else writer_rules("v3"))


def historical_extractor_system(version: str) -> str:
    """An earlier extractor version's system prompt: its extract_system.md from history/<version>/ (else from git),
    with the DSL table of the writer version it read (EXTRACTOR_TABLES), checked against its frozen hash."""
    stored = HERE / "history" / version / "extract_system.md"
    if stored.exists():
        text = stored.read_text()
    else:
        text = subprocess.run(["git", "show", f"{EXTRACTOR_COMMITS[version]}:src/verifier_gate/llm/prompts/extract_system.md"],
                              cwd=HERE.parents[3], capture_output=True, text=True, check=True).stdout  # fmt: skip
    system = text.replace("{dsl}", dsl_reference(version=EXTRACTOR_TABLES[version]))
    if hashlib.sha256(system.encode()).hexdigest() != EXTRACTOR_HISTORY[version]["extract_system"]:
        raise ValueError(f"{version}'s system prompt does not match its frozen hash")
    return system


def pin_extractor(version: str) -> None:
    """Read global texts with an earlier extractor version (E3 and its writer subsets ran with x3)."""
    _PINNED.clear()
    if version != EXTRACTOR_VERSION:
        _PINNED[version] = historical_extractor_system(version)


def extractor_version() -> str:
    return next(iter(_PINNED), EXTRACTOR_VERSION)


def extractor_system(local: bool = False) -> str:
    if local:
        return load("extract_local_system").replace("{dsl}", dsl_reference("system_local"))
    if _PINNED:
        return next(iter(_PINNED.values()))
    return load("extract_system").replace("{dsl}", dsl_reference())


def _text(name: str) -> str:
    if name in ("extract_system", "extract_local_system"):
        return extractor_system(local=name == "extract_local_system")
    if name.startswith("critic_system"):
        return critic_system(next(v for v, names in CRITIC_NAMES.items() if names[0] == name))
    return load(name)


def _texts(names: tuple[str, ...]) -> dict[str, str]:
    return {name: _text(name) for name in names}


def hashes(names: tuple[str, ...] = NAMES) -> dict[str, str]:
    return {name: hashlib.sha256(text.encode()).hexdigest() for name, text in _texts(names).items()}


def frozen(path: Path = FROZEN) -> dict[str, str] | None:
    return json.loads(path.read_text()) if path.exists() else None


def frozen_path(names: tuple[str, ...] = NAMES) -> Path:
    """Where the writer's (NAMES) or the extractor's (EXTRACTOR_NAMES) hashes of the version the lexicon gives are
    frozen."""
    if names == EXTRACTOR_NAMES:
        return FROZEN_EXTRACTOR_VERSIONS[EXTRACTOR_VERSIONS[predicates.pinned()]]
    return FROZEN_VERSIONS[writer_version()]


def expected(names: tuple[str, ...] = NAMES) -> dict[str, str] | None:
    """The frozen hashes of the version the lexicon gives; None before its pilot froze them."""
    return frozen(frozen_path(names))


def freeze(names: tuple[str, ...] = NAMES, path: Path = FROZEN) -> dict[str, str]:
    current = hashes(names)
    path.write_text(json.dumps(current, indent=1) + "\n")
    return current
