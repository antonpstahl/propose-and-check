"""SymPy export of Facts (§5.1): each term as a Piecewise, the whole model as one expression, and relations
between terms as SymPy relationals.

Where SymPy is needed and where numpy is enough:
- Evaluating, comparing and checking monotonicity: numpy is enough. Both models are step functions, so these
  are searchsorted and np.diff on the facts; the verifier uses numpy.
- SymPy adds (a) an exact symbolic form of the fitted model (exact=True keeps every float bit for bit; the
  test lambdifies it and reproduces the model's logit), (b) a short readable form for the handover, with
  scores rounded, cuts to 6 significant digits and equal neighbouring steps merged (the EBM's dti curve: 6
  pieces at one decimal instead of about 1,000 bins; approximate, so for the prompt only), and (c) relations between terms as objects, e.g. importance(utilization) > importance(income), that
  print as evidence and evaluate to True or False on the facts.
Steps follow facts/steps.py: x == cut belongs to the upper step, hence `x < cut` in each condition.
"""

from collections.abc import Sequence

import numpy as np
import sympy

from verifier_gate.facts.schema import Facts, FeatureFacts, PairFacts


def symbol(feature: str) -> sympy.Symbol:
    return sympy.Symbol(feature, real=True)


CUT_DIGITS = 6  # significant digits of the cuts in the readable form


def _number(value: float, exact: bool, digits: int | None):
    if exact:
        return sympy.Float(float(value), precision=53)  # the float64 itself, no decimal rounding
    return sympy.Float(round(float(value), digits) if digits is not None else float(value), 15)


def _cut(value: float, exact: bool):
    return sympy.Float(float(value), precision=53) if exact else sympy.Float(float(value), CUT_DIGITS)


def _merged(cuts: np.ndarray, scores: np.ndarray, digits: int | None) -> tuple[np.ndarray, np.ndarray]:
    """Drop the cuts between neighbouring steps whose (rounded) scores are equal."""
    values = np.round(scores, digits) if digits is not None else scores
    keep = np.flatnonzero(values[1:] != values[:-1])
    return cuts[keep], values[np.concatenate([keep, [len(values) - 1]])]


def _piecewise(x: sympy.Symbol, cuts: np.ndarray, pieces: Sequence, exact: bool):
    args = [(piece, x < _cut(c, exact)) for piece, c in zip(pieces[:-1], cuts)]
    args.append((pieces[-1], True))
    return pieces[0] if len(pieces) == 1 else sympy.Piecewise(*args, evaluate=False)


def main_term(feature: FeatureFacts, exact: bool = True, digits: int | None = None) -> sympy.Expr:
    """The feature's curve as a Piecewise in its symbol; digits rounds the scores and merges equal steps."""
    cuts, scores = (feature.cuts, feature.scores) if exact else _merged(feature.cuts, feature.scores, digits)
    return _piecewise(symbol(feature.name), cuts, [_number(s, exact, digits) for s in scores], exact)


def pair_term(pair: PairFacts, exact: bool = True, digits: int | None = None) -> sympy.Expr:
    """The pair grid as a Piecewise over the first feature of Piecewise terms over the second."""
    a, b = (symbol(f) for f in pair.features)
    rows = []
    for row in pair.scores:
        cuts, scores = (pair.cuts[1], row) if exact else _merged(pair.cuts[1], row, digits)
        rows.append(_piecewise(b, cuts, [_number(s, exact, digits) for s in scores], exact))
    return _piecewise(a, pair.cuts[0], rows, exact)


def expression(facts: Facts, exact: bool = True, digits: int | None = None, pairs: bool = True) -> sympy.Expr:
    """intercept + sum of the main terms (+ the pairs): the model's logit as one SymPy expression."""
    terms = [_number(facts.intercept, exact, digits)] + [main_term(f, exact, digits) for f in facts.features]
    if pairs:
        terms += [pair_term(p, exact, digits) for p in facts.pairs]
    return sympy.Add(*terms, evaluate=False)


def importance_symbol(term: str) -> sympy.Symbol:
    return sympy.Symbol(f"importance({term})", nonnegative=True)


def relations(facts: Facts) -> list[tuple[sympy.Rel, bool, float | None]]:
    """importance(a) > importance(b) for each feature and the next one in M's ranking, with its truth value on
    M and the share of refits in which it holds (None without draws). The lexicon decides what share counts."""
    ranked = sorted(facts.features, key=lambda f: f.rank.value)
    values = {importance_symbol(f.name): f.importance.value for f in facts.features}
    out = []
    for a, b in zip(ranked, ranked[1:]):
        relation = sympy.Gt(importance_symbol(a.name), importance_symbol(b.name), evaluate=False)
        holds = bool(relation.subs(values))
        refits = None
        if facts.draws is not None:
            refits = float(np.mean(facts.draws.importance[a.name] > facts.draws.importance[b.name]))
        out.append((relation, holds, refits))
    return out
