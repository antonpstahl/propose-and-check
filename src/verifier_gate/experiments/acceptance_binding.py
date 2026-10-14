"""The binding acceptance run (§4.1; D10, D24 as refined in §14.5): on the frozen lexicon, three-valued verdicts.

Rule, fixed 13 Oct (§14.3, §14.4) and refined the same night (§14.5: the binding run uses the frozen lexicon):
on all nine n = 50,000 datasets, every labelled claim of data/planted.py is verified on the oracle and on each
fitted model. A **model miss** is a claim the oracle's verdict calls true and the model's verdict calls false. A
model is accepted if it has no model miss. E1 does not wait for a pass: remaining model misses enter E1 as the
model layer (D12, D14).

Reported separately, as the rule says: the model undecidable where the oracle's verdict is true, and the
reverse (the oracle undecidable, the model decided). Also reported, not part of the rule fixed on 13 Oct: the
mirror of a miss, the oracle false and the model true (the model certifies what the sample refutes), and the
data misses, claims true in T that the oracle refutes.

Run: `uv run python -m verifier_gate.experiments.acceptance_binding` (about 15 s, after build_facts). Writes
results/acceptance/binding.csv (one row per dataset and claim) and binding_summary.csv.
"""

from pathlib import Path

import pandas as pd

from verifier_gate.data import dgp
from verifier_gate.experiments.e1_lexicon import MODELS, verdicts
from verifier_gate.lexicon import predicates as p
from verifier_gate.lexicon.predicates import FALSE, TRUE, UNDECIDABLE

SCENARIOS = tuple(s for s in dgp.SCENARIOS if s.n == max(dgp.SAMPLE_SIZES))
RESULTS = Path(__file__).parents[3] / "results" / "acceptance"


def summarise(table: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for m in MODELS:
        o, v = table.oracle, table[m]
        rows.append({
            "model": m, "claims": len(table),
            "model misses (oracle true, model false)": int(((o == TRUE) & (v == FALSE)).sum()),
            "model undecidable where the oracle is true": int(((o == TRUE) & (v == UNDECIDABLE)).sum()),
            "oracle undecidable, model decided": int(((o == UNDECIDABLE) & (v != UNDECIDABLE)).sum()),
            "mirror (oracle false, model true), reported only": int(((o == FALSE) & (v == TRUE)).sum()),
            "data misses (label true, oracle false)": int(((table.label == TRUE) & (o == FALSE)).sum()),
        })  # fmt: skip
        rows[-1]["accepted"] = rows[-1]["model misses (oracle true, model false)"] == 0
    return pd.DataFrame(rows).set_index("model")


def main() -> None:
    lex = p.load()
    assert lex.version == "v1", "the binding run uses the frozen lexicon (D24 as refined)"
    table = verdicts(SCENARIOS, lex)
    RESULTS.mkdir(parents=True, exist_ok=True)
    table.to_csv(RESULTS / "binding.csv", index=False)
    summary = summarise(table)
    summary.to_csv(RESULTS / "binding_summary.csv")

    pd.set_option("display.width", 250)
    pd.set_option("display.max_rows", 200)
    print(f"Binding acceptance run: {len(SCENARIOS)} datasets at n = {max(dgp.SAMPLE_SIZES):,}, {len(table)} claims, lexicon {lex.version}")
    print(summary.T.to_string())
    for m in MODELS:
        for name, mask in (("Model misses", (table.oracle == TRUE) & (table[m] == FALSE)),
                           ("Mirror cases", (table.oracle == FALSE) & (table[m] == TRUE))):  # fmt: skip
            part = table[mask]
            print(f"\n{m}: {name.lower()} ({len(part)})")
            if len(part):
                print(part.groupby(["claim", "label"]).scenario.apply(lambda s: ", ".join(x.removeprefix("syn-") for x in s)).to_string())
    print("\nData misses (label true, oracle false)")
    data = table[(table.label == TRUE) & (table.oracle == FALSE)]
    print(data[["scenario", "claim"]].to_string(index=False) if len(data) else "  none")


if __name__ == "__main__":
    main()
