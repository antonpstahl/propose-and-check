"""ast-based parser from DSL lines to claims; anything outside the whitelist is rejected (§5.2).

The line is parsed with `ast.parse(mode="eval")` and the tree is matched against the forms in grammar.py.
Nothing is evaluated, so no input can execute: names, attributes, subscripts, operators other than the
whitelisted comparisons, and literals of the wrong type are all errors.
"""

import ast
from contextvars import ContextVar
from dataclasses import replace

from verifier_gate.dsl.grammar import CALLS, CLASSES, COMPARED, HEDGE, LOCAL_CALLS, LOCAL_KINDS, PATTERNS, RANKS, SETS, Claim
from verifier_gate.lexicon import predicates

COMPARISONS = {ast.Gt: ">", ast.Lt: "<"}
# Set while the gate handles a notice of the local spot check (gate/gate.py): error messages then list the local forms
# too. Outside it they list the global forms only, word for word as before the local forms existed, so a format
# retry of a global run sends the same message and replays from the cache.
LOCAL_SCOPE: ContextVar[bool] = ContextVar("local_dsl_scope", default=False)


class DSLError(ValueError):
    pass


def _calls() -> set[str]:
    """The call forms: `drop` exists from lexicon v3 (D64). Under v2 it does not parse, and error messages list the
    forms as before, so a run of v2 replays from the cache."""
    return set(CALLS) | {HEDGE} if predicates.load().signed_jumps else (set(CALLS) - {"drop"}) | {HEDGE}


def _string(node: ast.AST, what: str) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.strip():
        return node.value.strip()
    raise DSLError(f"{what} must be a non-empty string")


def _number(node: ast.AST, what: str) -> float | int:
    sign = 1
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        sign, node = -1, node.operand
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return sign * node.value
    raise DSLError(f"{what} must be a number")


def _call(node: ast.AST, names: tuple[str, ...] | set[str]) -> ast.Call:
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in names):
        shown = names if LOCAL_SCOPE.get() else [n for n in names if n not in LOCAL_KINDS]
        raise DSLError(f"expected a call to one of {sorted(shown)}")
    return node


def _terms(call: ast.Call, count: int) -> tuple[str, ...]:
    if len(call.args) != count:
        raise DSLError(f"{call.func.id}() takes {count} term(s)")
    return tuple(_string(a, "a term") for a in call.args)


def _keywords(call: ast.Call, allowed: tuple[str, ...]) -> dict[str, ast.AST]:
    found = {k.arg: k.value for k in call.keywords}
    if None in found or set(found) != set(allowed):
        raise DSLError(f"{call.func.id}() takes exactly the keywords {list(allowed)}")
    return found


def _consecutive(positions: list[int]) -> bool:
    return all(b - a == 1 for a, b in zip(positions, positions[1:]))


def _set(node: ast.AST, kind: str) -> tuple:
    """The values of a set claim (D33), in their canonical order. Only neighbouring values form a set."""
    if not isinstance(node, ast.Tuple) or len(node.elts) < 2:
        raise DSLError(f"a set of {kind} values is a tuple of at least two")
    if kind in RANKS:
        ranks = sorted(_number(e, "a rank") for e in node.elts)
        if not all(isinstance(k, int) and k >= 1 for k in ranks) or not _consecutive(ranks):
            raise DSLError("a set of ranks holds consecutive whole numbers >= 1")
        return tuple(ranks)
    labels = [_string(e, f"a {kind}") for e in node.elts]
    if kind == "direction":
        for word in ("increasing", "decreasing"):
            if sorted(labels) == [word, f"mostly_{word}"]:
                return word, f"mostly_{word}"
        raise DSLError('a set of directions is a strict word and its "mostly" word, e.g. ("decreasing", "mostly_decreasing")')
    if not set(labels) <= set(CLASSES):
        raise DSLError(f"a set of strengths holds classes of {list(CLASSES)}")
    positions = sorted(CLASSES.index(label) for label in labels)
    if not _consecutive(positions) or len(positions) == len(CLASSES):
        raise DSLError("a set of strengths holds neighbouring classes, and not all of them")
    return tuple(CLASSES[i] for i in positions)


def _compared(node: ast.Compare) -> Claim:
    left = _call(node.left, set(COMPARED) | {"effect"})
    kind = left.func.id
    op = type(node.ops[0])
    if kind == "effect":
        if op not in COMPARISONS:
            raise DSLError("effects are compared with > or <")
        right = _call(node.comparators[0], {"effect"})
        _keywords(left, ())
        _keywords(right, ())
        return Claim("comparison", _terms(left, 1) + _terms(right, 1), relation=COMPARISONS[op])
    _keywords(left, ())
    terms, right = _terms(left, 1), node.comparators[0]
    if op is ast.In:
        if kind not in SETS:
            raise DSLError(f"{kind}() takes no set of values")
        return Claim(kind, terms, _set(right, kind))
    if op is not ast.Eq:
        raise DSLError(f"{kind}() is compared with ==, or with `in` and a set of values")
    allowed = COMPARED[kind]
    if kind == "share":
        approx = _call(right, {"approx"})
        _keywords(approx, ())
        if len(approx.args) != 1:
            raise DSLError("approx() takes one number")
        value = float(_number(approx.args[0], "a share"))
        if not 0.0 <= value <= 1.0:
            raise DSLError("a share lies between 0 and 1")
    elif kind in RANKS:
        value = _number(right, "a rank")
        if not isinstance(value, int) or value < 1:
            raise DSLError("a rank is a whole number >= 1")
    else:
        value = _string(right, f"the {kind}")
        if value not in allowed:
            raise DSLError(f"{kind} is one of {list(allowed)}")
    return Claim(kind, terms, value)


def _claim(node: ast.AST, hedge: bool = True) -> Claim:
    if isinstance(node, ast.Compare):
        if len(node.ops) != 1:
            raise DSLError("one comparison per claim")
        return _compared(node)
    call = _call(node, _calls())
    kind = call.func.id
    if kind == HEDGE:
        if not hedge:
            raise DSLError("unsettled() hedges a claim, not another hedge")
        if len(call.args) != 1 or call.keywords:
            raise DSLError("unsettled() takes exactly one claim")
        inner = _claim(call.args[0], hedge=False)
        return Claim(HEDGE, inner.terms, inner=inner)
    count, keywords = CALLS[kind]
    terms, found = _terms(call, count), _keywords(call, keywords)
    if kind == "negligible" or kind in LOCAL_CALLS:
        value = None
    elif kind == "interaction":
        value = _string(found["pattern"], "the pattern")
        if value not in PATTERNS:
            raise DSLError(f"pattern is one of {list(PATTERNS)}")
        if terms[0] == terms[1]:
            raise DSLError("an interaction needs two different features")
    else:
        value = float(_number(found["at"], "a location"))
    return Claim(kind, terms, value)


def parse(line: str, sentence_id: int | None = None) -> Claim:
    try:
        tree = ast.parse(line.strip(), mode="eval")
    except SyntaxError as e:
        raise DSLError(f"not a DSL line: {e.msg}") from None
    return replace(_claim(tree.body), sentence_id=sentence_id)
