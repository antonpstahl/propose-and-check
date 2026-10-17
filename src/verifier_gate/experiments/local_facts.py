"""The 54 notices of the local spot check (D49) with their facts, and what the local predicates say before any
LLM writes: for every term of every notice, whether "principal reason" is true, false or undecidable under M
(with the refits' bands) and under T. No LLM, $0.

Per dataset (seed 2, n = 50,000, three interaction levels) and model (EBM, XGB2): M from its Facts, its 100
refits from experiments/local_refits.py, the decision rule and the reference (facts/local.py), 9 declined
applicants drawn from the generator seeded by (SAMPLE_SEED, dataset seed, interaction index, model index).

Writes results/local/facts/<scenario>_<kind>.json (the notices' LocalFacts, with draws) and
results/local/facts/summary.csv (one row per notice and term: contribution, fraction and rank with bands, the
truth, and both verdicts).

Run: `uv run python -m verifier_gate.experiments.local_facts` (after local_refits).
"""

import csv
import json
from collections import Counter
from pathlib import Path

from verifier_gate.data import dgp, tiers
from verifier_gate.experiments import build_facts
from verifier_gate.experiments.local_refits import MODELS, SCENARIOS
from verifier_gate.experiments.local_refits import path as refits_path
from verifier_gate.facts import local, refits
from verifier_gate.lexicon import local as lp
from verifier_gate.lexicon.predicates import FALSE, TRUE, UNDECIDABLE

OUT = Path(__file__).parents[3] / "results" / "local" / "facts"


def notices(scenario: dgp.Scenario, kind: str) -> list[local.LocalFacts]:
    data = tiers.generate(scenario)
    M = build_facts.load(scenario, kind, draws=False).steps()
    decision = local.decide(M, data.X)
    rows = local.draw_applicants(decision, (scenario.seed, dgp.INTERACTION_LEVELS.index(scenario.interaction), MODELS.index(kind)))
    model = {"kind": kind, "scenario": scenario.id, "interaction": scenario.interaction, "seed": scenario.seed}
    return local.local_facts(M, refits.load_models(refits_path(scenario, kind)), data.truth, data.X, rows, decision, model)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows, by_notice = [], []
    for scenario in SCENARIOS:
        for kind in MODELS:
            found = notices(scenario, kind)
            (OUT / f"{scenario.id}_{kind}.json").write_text(json.dumps([f.to_json() for f in found]))
            for f in found:
                truth = lp.truth_view(f)
                counts = Counter()
                for r in f.reasons:
                    m, t = lp.principal_reason(f, r.term).value, lp.principal_reason(truth, r.term).value
                    counts[(m, t)] += 1
                    rows.append({
                        "scenario": scenario.id, "kind": kind, "row": f.model["row"], "term": r.term,
                        "contribution": r.contribution.value, "contribution_band": r.contribution.band,
                        "fraction": r.fraction.value, "fraction_band": r.fraction.band,
                        "rank": None if r.rank is None else r.rank.value, "rank_band": None if r.rank is None else r.rank.band,
                        "truth": r.truth, "truth_fraction": r.truth_fraction, "truth_rank": r.truth_rank,
                        "principal_M": m, "principal_T": t,
                    })  # fmt: skip
                by_notice.append((scenario.id, kind, f, truth.model["declined_by_m_only"], counts))
    with (OUT / "summary.csv").open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    total = Counter()
    for *_, counts in by_notice:
        total.update(counts)
    print(f"{len(by_notice)} notices, {sum(total.values())} terms; 'principal reason' under M (bands) vs T:")
    for m in (TRUE, UNDECIDABLE, FALSE):
        print(f"  M {m:12s}" + "".join(f"  T {t}: {total[(m, t)]:4d}" for t in (TRUE, FALSE)))
    certified = [sum(n for (m, _), n in c.items() if m == TRUE) for *_, c in by_notice]
    open_ = [sum(n for (m, _), n in c.items() if m == UNDECIDABLE) for *_, c in by_notice]
    print(f"certified principal reasons per notice: {Counter(certified)}; undecidable per notice: {Counter(open_)}")
    print(f"declined by M only (T's gap <= 0): {sum(d for _, _, _, d, _ in by_notice)} of {len(by_notice)}")
    for kind in MODELS:
        sub = [c for _, k, _, _, c in by_notice if k == kind]
        t = Counter()
        for c in sub:
            t.update(c)
        print(f"  {kind}: certified {t[(TRUE, TRUE)] + t[(TRUE, FALSE)]}, of which false against T {t[(TRUE, FALSE)]}; "
              f"refuted {t[(FALSE, TRUE)] + t[(FALSE, FALSE)]}, of which true against T {t[(FALSE, TRUE)]}; undecidable {t[(UNDECIDABLE, TRUE)] + t[(UNDECIDABLE, FALSE)]}")  # fmt: skip


if __name__ == "__main__":
    main()
