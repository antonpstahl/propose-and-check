"""The worked example (plan §7): one XGB2 model, one explanation, traced through every step of the gate; the EBM
version in the appendix. Every number is read from E3's run as made (prompts v3, extractor x3), from the models'
Facts and from the writer's DSL table; nothing is rerun and nothing is paid.

The run: `syn-dominant-n50000-s1`, XGB2, H1, draw 4, plausible names, the only XGB2 run on this dataset whose first
draft fails on one claim that one repair round fixes. The EBM run (draw 2, H1, plausible) shows the jump the
readable handover invites (D52).

Run: `uv run python -m verifier_gate.experiments.worked_example`. Writes paper/worked_example.md and
paper/figures/worked_example_shapes.png and .pdf (three features of Fig. 2: the top driver, the repaired
sentence's feature, and the feature whose released claim is faithful to the model and false against T).
"""

import json
import re
from pathlib import Path

from verifier_gate.data import dgp, labels
from verifier_gate.dsl.parse import parse
from verifier_gate.experiments import fig2
from verifier_gate.experiments.build_facts import load
from verifier_gate.llm import prompts
from verifier_gate.llm.handover import handover
from verifier_gate.verifier.certified import certified_plan
from verifier_gate.verifier.verify import evidence_text, verify

ROOT = Path(__file__).parents[3]
SCENARIO = "syn-dominant-n50000-s1"
RUNS = ROOT / "results" / "e3" / "v3-x3" / "haiku" / "runs"
XGB2_RUN = f"{SCENARIO}_XGB2_H1_d4_claude-haiku-5-5_plausible"
EBM_RUN = f"{SCENARIO}_EBM_H1_d2_claude-haiku-5-5_plausible"
SHAPES = ("utilization", "dti", "history_months")
EXCERPT = ("utilization", "dti", "history_months")
SIGN_FLIP = 'interaction("n_inquiries", "history_months", pattern="sign_flip")'
OUT = ROOT / "paper"


def lexicon_rules() -> dict[tuple[str, bool], str]:
    """(claim kind, is a set) -> the meaning column of the writer's DSL table (system.md), first row of each kind."""
    rules = {}
    for line in prompts.dsl_reference().splitlines():
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 3 or not cells[1].startswith("`"):
            continue
        dsl = cells[1].split("`")[1]
        kind = "comparison" if dsl.startswith("effect(") else dsl.split("(")[0]
        rules.setdefault((kind, " in (" in dsl), cells[2])
    return rules


def rule_for(line: str, rules: dict) -> str:
    claim = parse(line)
    if claim.kind == "unsettled":
        return rules.get(("unsettled", False), "")
    rule = rules.get((claim.kind, isinstance(claim.value, tuple)), rules.get((claim.kind, False), ""))
    if claim.kind == "direction" and "decreasing" in str(claim.value):  # the table's row is written for "increasing"
        rule = rule.replace("rises", "falls")
    return rule


def excerpt(text: str, features: tuple[str, ...]) -> str:
    lines, keep = text.splitlines(), [text.splitlines()[0]]
    for f in features:
        i = next(k for k, line in enumerate(lines) if line.startswith(f"- `{f}`"))
        keep += lines[i : i + 3]
    return "\n".join(keep)


def sentences_md(sentences: list, mark: set[int] = frozenset()) -> str:
    return "\n".join(f"{i}. {'**' + t + '**' if i in mark else t}" for i, t in sentences)


def table(rows: list[list[str]], head: list[str]) -> str:
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    return "\n".join(out + ["| " + " | ".join(r) + " |" for r in rows])


def main() -> None:
    scenario = next(s for s in dgp.SCENARIOS if s.id == SCENARIO)
    X = dgp.generate(scenario).X
    facts = {k: load(scenario, k) for k in ("EBM", "XGB2", "T")}
    run = json.loads((RUNS / f"{XGB2_RUN}.json").read_text())
    ebm = json.loads((RUNS / f"{EBM_RUN}.json").read_text())
    rules = lexicon_rules()
    h = handover(facts["XGB2"], X, "H1", certified_plan(facts["XGB2"]))
    if not (h.passed and h.text in run["writer"]["messages"][0][1]):
        raise ValueError("the rebuilt handover is not the one the run's writer read")
    figure = fig2.draw(scenario, OUT / "figures", SHAPES, "worked_example_shapes")

    first, released = run["versions"][0], run["versions"][-1]
    failing = [c for c in first["claims"] if c[2] != "true"]
    fixed = {c[0] for c in failing}
    repair = run["writer"]["messages"][-1][1]
    trip = released["roundtrip"]
    plan_rows = [[str(c[0]), f"`{c[1]}`", c[2], c[5]] for c in failing]
    released_rows = [[str(c[0]), f"`{c[1]}`", c[2], rule_for(c[1], rules)] for c in released["claims"]]
    t_rows = []
    for c in released["claims"]:
        if c[1].startswith("unsettled("):
            continue  # a hedge is about the evidence in one sample, not about T (§14.23)
        vt = verify(c[1], facts["T"])
        if vt.value != "true":
            t_rows.append([str(c[0]), f"`{c[1]}`", c[2], vt.value, evidence_text(vt.evidence)])
    flip = []
    for kind in ("EBM", "XGB2", "T"):
        v = verify(SIGN_FLIP, facts[kind])
        e = v.evidence
        band = lambda key: "" if kind == "T" else f" ({e[key + ' band'][0]:+.2f} to {e[key + ' band'][1]:+.2f})"  # noqa: E731
        flip.append([kind, f"{e['effect at low']:+.2f}{band('effect at low')}", f"{e['effect at high']:+.2f}{band('effect at high')}", v.value])

    ebm_first = ebm["versions"][0]
    jump = next(c for c in ebm_first["claims"] if c[1].startswith("threshold(") and c[2] != "true")
    sid = jump[0]
    ebm_text = {v["source"]: dict((i, t) for i, t in v["sentences"]) for v in ebm["versions"]}

    md = f"""# Worked example: one XGB2 model, one explanation, through the gate

*Generated by `experiments/worked_example.py` from E3 as run on 15 Oct 2026 (prompts v3, extractor x3; git tag
`prompts-v3-x3`): every text, verdict and number below is read from the run's trace and the models' Facts; nothing was
rerun. Decision numbers (D34, D41, D52) are explained in `docs/decisions.md`.*

**Setting.** Dataset `{SCENARIO}` (dominant interactions, n = 50,000, seed 1; one of the two pilot datasets, on
which the prompts were shaped), the XGB2 model, handover H1 (the facts only), writer Claude Haiku 5.5 (draw 4,
plausible names). Run `{XGB2_RUN}`: {run['exit']} after {run['rounds']} repair round, {run['calls']} calls,
${run['cost']:.4f}.

**Names.** The two planted noise features are never called noise in front of the writer: it sees them under plausible
names (D41), {' and '.join(f"`{k}` as `{v}`" for k, v in labels.SYNTHETIC_NAMES.items())}. Claims are mapped back to
the internal names before they are verified, so the tables below show `noise_2` where the text says "the number of
dependents".

## 1. The model and the truth

Figure: `{figure.relative_to(ROOT)}` (three panels of Fig. 2): the planted term T, the purified EBM and XGB2 terms
and their simultaneous 95% bands for utilization (the top driver), the debt-to-income ratio (the sentence the gate
repairs) and the length of credit history (a plan line that is true of the model and false of T, §7 below).

## 2. What the writer reads (excerpt of the handover)

```
{excerpt(h.text, EXCERPT)}
```

## 3. The first draft

{sentences_md(first['sentences'], fixed)}

## 4. The plan check

{len(first['claims'])} claims; {len(first['claims']) - len(failing)} are certified, {len(failing)} is not:

{table(plan_rows, ['Sentence', 'Claim', 'Verdict', 'Evidence (from the 100 refits)'])}

The sentence says "at most a weak effect", its claim says "weak": the whole share band would have to lie in 2% to 5%,
and it reaches 6.3%. Neither the sentence nor the claim is supported; the band spans two classes.

## 5. The repair

The message the writer gets (verbatim):

```
{repair}
```

Repaired sentence {', '.join(str(i) for i in sorted(fixed))}: "{dict((i, t) for i, t in released['sentences'])[min(fixed)]}"

## 6. The released text and the round trip

{sentences_md(released['sentences'], fixed)}

{table(released_rows, ['Sentence', 'Claim', 'Verdict on M', 'What the word means (lexicon)'])}

The round trip: {trip['readings']} independent readings of the text by the extractor, which sees neither the plan nor
the facts. What two of three readings find beyond the plan is verified too: {'; '.join(f'`{u[1]}` ({u[2]})' for u in trip['unplanned'])}.
A statement no DSL form expresses and that states no number is flagged, not blocked:
{'; '.join(f'sentence {g[0]}: "{g[1][0]}"' for g in trip['gap'])}. Nothing blocks, so the text is released.

## 7. Two faithful stories, and what "verified" means

The same data, two models. The planted sign flip: recent inquiries raise the risk for short credit histories and
lower it for long ones. The claim `{SIGN_FLIP}`, the effect of inquiries from their 5th to their 95th percentile, at
a short and at a long history:

{table(flip, ['Model', 'Effect at short history', 'Effect at long history', 'Verdict'])}

The gate lets an EBM text say "the effect of inquiries reverses with the length of the credit history" and does
not release the same sentence for XGB2, whose effect at long histories is not significant. Both texts are faithful
to their model; T sides with the EBM. (XGB2's estimate at short histories lies just above its own refit band: the
bootstrap is skewed there.)

Against T, the released text holds one plan line that is false:

{table(t_rows, ['Sentence', 'Claim', 'On M', 'On T', 'Evidence on T'])}

Its sentence, "longer histories generally lower the risk", is right: the readings take "generally" as the set
"decreases or mostly decreases" (found by the round trip above), which is true of the model and of T. The plan line
is stricter than its sentence. It is certified on M because a direction word is judged at the resolution of the
model's bands: both models trace the planted bump at about 36 months (figure), but their bootstrap bands do not show
the rise before it as significant, so no exception is detected (D34), and the readable handover merges the bump away
for the same reason (excerpt above). The documentation is as simple as the model's uncertainty allows, never
opposite to it. Where a model misses part of the world, as XGB2 misses the reversal, the gate cannot add it back: it
certifies that a text matches the model, and model validation owns the rest.

## Appendix: the EBM version (run `{EBM_RUN}`)

{ebm['exit']} after {ebm['rounds']} repair rounds, {ebm['calls']} calls, ${ebm['cost']:.4f}. The first draft's
sentence {sid}: "{ebm_text[ebm_first['source']][sid]}" with the claim `{jump[1]}`: **{jump[2]}** ({jump[5]}). The
readable handover draws the gradual rise of utilization as a few large steps, and the writer reads the largest as a
jump (D52). The repair drops the location: "{ebm_text[ebm['versions'][1]['source']][sid]}"
"""
    md = re.sub(r"\n{3,}", "\n\n", md)
    (OUT / "worked_example.md").write_text(md)
    print(f"written: {OUT / 'worked_example.md'} and {figure}")


if __name__ == "__main__":
    main()
