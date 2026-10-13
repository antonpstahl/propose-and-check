"""ast-based parser from DSL lines to claims; anything outside the whitelist is rejected (§5.2).

The line is parsed with `ast.parse(mode="eval")` and the tree is matched against the forms in grammar.py.
Nothing is evaluated, so no input can execute: names, attributes, subscripts, operators other than the
whitelisted comparisons, and literals of the wrong type are all errors.
"""

import ast

from verifier_gate.dsl.grammar import CALLS, COMPARED, PATTERNS, Claim

COMPARISONS = {ast.Gt: ">", ast.Lt: "<"}


class DSLError(ValueError):
    pass


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
        raise DSLError(f"expected a call to one of {sorted(names)}")
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
    if op is not ast.Eq:
        raise DSLError(f"{kind}() is compared with ==")
    _keywords(left, ())
    terms, right = _terms(left, 1), node.comparators[0]
    allowed = COMPARED[kind]
    if kind == "share":
        approx = _call(right, {"approx"})
        _keywords(approx, ())
        if len(approx.args) != 1:
            raise DSLError("approx() takes one number")
        value = float(_number(approx.args[0], "a share"))
        if not 0.0 <= value <= 1.0:
            raise DSLError("a share lies between 0 and 1")
    elif kind == "rank":
        value = _number(right, "a rank")
        if not isinstance(value, int) or value < 1:
            raise DSLError("a rank is a whole number >= 1")
    else:
        value = _string(right, f"the {kind}")
        if value not in allowed:
            raise DSLError(f"{kind} is one of {list(allowed)}")
    return Claim(kind, terms, value)


def parse(line: str, sentence_id: int | None = None) -> Claim:
    try:
        tree = ast.parse(line.strip(), mode="eval")
    except SyntaxError as e:
        raise DSLError(f"not a DSL line: {e.msg}") from None
    node = tree.body
    if isinstance(node, ast.Compare):
        if len(node.ops) != 1:
            raise DSLError("one comparison per claim")
        claim = _compared(node)
    else:
        call = _call(node, set(CALLS))
        kind = call.func.id
        count, keywords = CALLS[kind]
        terms, found = _terms(call, count), _keywords(call, keywords)
        if kind == "negligible":
            value = None
        elif kind == "interaction":
            value = _string(found["pattern"], "the pattern")
            if value not in PATTERNS:
                raise DSLError(f"pattern is one of {list(PATTERNS)}")
            if terms[0] == terms[1]:
                raise DSLError("an interaction needs two different features")
        else:
            value = float(_number(found["at"], "a location"))
        claim = Claim(kind, terms, value)
    return Claim(claim.kind, claim.terms, claim.value, claim.relation, sentence_id)
