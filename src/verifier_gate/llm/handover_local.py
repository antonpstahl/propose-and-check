"""The handover for one notice of the local spot check (D49, D68): what the writer reads about one declined
applicant (facts/local.LocalFacts).

The decision and its scale: the model, the decision rule (the riskiest 20% declined), the applicant's predicted
default risk and the average of the comparable approved applicants (the reference), and the score gap between
them. Then M's principal reasons by name (lexicon/local.principal_reasons), and every factor that pushes towards
the decline, largest first: its name in the DSL and a short description, the applicant's value and the
reference's median (both, for a pair), its contribution to the gap, its share of the gap and its rank among the
factors. All of it is M's exact numbers for this decision: no bands (D68; the bands are the lender's internal
flag, lexicon/local.second_look). Factors whose share of the gap is below SMALL go in one line; the factors in
the applicant's favour that take at least SMALL of the gap in another, and the rest are counted. Terms of T the
model does not have are not shown: the writer sees the model, never the planted truth.
"""

from collections.abc import Mapping

from verifier_gate.data import labels
from verifier_gate.facts import readable
from verifier_gate.facts.local import DECLINE_SHARE, MATERIALITY, MAX_REASONS, LocalFacts, Reason
from verifier_gate.facts.steps import PAIR_SEPARATOR
from verifier_gate.lexicon import local as lp
from verifier_gate.llm.handover import MODEL_NAMES

SMALL = 0.02  # share of the gap below which a factor is listed in one line


def _pct(x: float) -> str:
    return f"{x:.0%}" if abs(x) >= 0.095 else f"{x:.1%}"


def _rank(r: Reason) -> str:
    return f"rank {int(r.rank.value)}"


def _values(lf: LocalFacts, term: str, names: Mapping[str, str]) -> str:
    parts = []
    for feature in term.split(PAIR_SEPARATOR):
        v = lf.value(feature)
        parts.append(f"`{labels.shown(feature, names)}` {readable._x(v.applicant)} (comparable approved applicants' median "
                     f"{readable._x(v.reference_median)})")  # fmt: skip
    return "; ".join(parts)


def _description(term: str, names: Mapping[str, str], descriptions: Mapping[str, str]) -> str:
    shown = [labels.shown(f, names) for f in term.split(PAIR_SEPARATOR)]
    if len(shown) == 2:
        words = [labels.SYNTHETIC_LABELS.get(x, x) for x in shown]
        return f"the combination of {words[0]} and {words[1]} (an interaction in the model)"
    return descriptions.get(shown[0], shown[0])


def notice_handover(lf: LocalFacts, names: Mapping[str, str] = labels.SYNTHETIC_NAMES,
                    descriptions: Mapping[str, str] = labels.SYNTHETIC_DESCRIPTIONS) -> str:  # fmt: skip
    kind = lf.model.get("kind", "")
    principal = ", ".join(f"`{labels.shown(t, names)}` ({_rank(lf.reason(t))})" for t in lp.principal_reasons(lf))
    lines = [
        f"Decision: the credit model, {MODEL_NAMES.get(kind, 'a fitted model')}, declined this applicant. The lender "
        f"declines the {DECLINE_SHARE:.0%} of applicants with the highest predicted risk of default.",
        f"The applicant's predicted risk of default is {lf.risk:.1%}. Comparable approved applicants (the "
        f"{lf.model.get('reference_size', 0)} approved applicants closest to the cutoff) have an average predicted risk of "
        f"{lf.reference_risk:.1%}.",
        f"The gap between the applicant's score and their average score is {lf.gap.value:+.2f} on the log-odds scale. "
        f"Each factor below adds to the gap or takes from it, and together they make it up exactly. These are the "
        f"model's exact numbers for this decision.",
        f"A factor is a principal reason if its share of the gap is at least {MATERIALITY:.0%} and it is among the "
        f"{MAX_REASONS} largest factors. The principal reasons for this decision: {principal or 'none'}.",
        "",
        "Factors that push towards the decline, largest first:",
    ]  # fmt: skip
    model_terms = [r for r in lf.reasons if r.rank is not None]
    against = [r for r in model_terms if r.contribution.value > 0]
    listed = [r for r in against if r.fraction.value >= SMALL]
    small = [r for r in against if r.fraction.value < SMALL]
    favour = [r for r in model_terms if r.contribution.value <= 0 and r.fraction.value <= -SMALL]
    negligible = len(model_terms) - len(listed) - len(small) - len(favour)
    for r in listed:
        name = labels.shown(r.term, names)
        lines += [
            f"- `{name}`: {_description(r.term, names, descriptions)}. {_values(lf, r.term, names)}.",
            f"  Contribution {r.contribution.value:+.2f}; share of the gap {_pct(r.fraction.value)}; "
            f"{_rank(r)} among the {len(model_terms)} factors.",
        ]  # fmt: skip
    if small:
        lines.append(f"Smaller factors pushing towards the decline (each under {SMALL:.0%} of the gap): "
                     + ", ".join(f"`{labels.shown(r.term, names)}`" for r in small) + ".")  # fmt: skip
    if favour:
        lines += ["", "Factors in the applicant's favour (they reduce the gap): "
                  + ", ".join(f"`{labels.shown(r.term, names)}` {r.contribution.value:+.2f}" for r in favour) + "."]  # fmt: skip
    if negligible:
        lines.append(f"The other {negligible} factors reduce the gap by less than {SMALL:.0%} each.")
    return "\n".join(lines)
