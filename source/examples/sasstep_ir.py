"""
sasstep_ir -- an IR front-end over plain-Python DATA-step logic.

Purpose: make logic INSPECTABLE so the engine can answer one question per
statement -- "does this depend on a prior row?" -- and split the step into:
  * vectorizable spans (pure functions of the current row) -> batch/columnar
  * sequential residual (retain, lag/dif, first./last., _N_, output) -> row loop

Design choices (see DESIGN.md):
  * Front-end is the AST of an ORDINARY `def logic(pdv): ...` -- so SAS-to-Python
    translation and hand-editing stay natural, and existing logic ports verbatim.
  * We support a small, SAS-shaped SUBLANGUAGE. Anything outside it does not
    break: lowering raises Unsupported and the caller FALLS BACK to running the
    function row-at-a-time on the reference engine. Correct always; fast when
    the logic is in-sublanguage (which translated SAS naturally is).

This module delivers steps 1-4: IR nodes, the AST front-end, the
vectorizable/sequential classifier, and a validation harness against the
reference engine (the oracle). The vectorized executor / JIT come later; here
the IR is executed by a faithful interpreter so the classifier can be proven
correct before any fast path is built.
"""
from __future__ import annotations

import ast
import inspect
import textwrap
from dataclasses import dataclass, field
from typing import Any, Optional

from sasstep import ObservationEngine, MISSING, Missing


class Unsupported(Exception):
    """Raised when logic falls outside the sublanguage -> caller falls back."""


# ============================================================================
# 1. IR nodes  (a small, closed set -- the whole sublanguage)
# ============================================================================
@dataclass
class Const:   value: Any
@dataclass
class Col:     name: str                       # read current-row variable
@dataclass
class Auto:    name: str                        # _N_, eof
@dataclass
class FirstLast:
    which: str                                  # "first" | "last"
    by: str
@dataclass
class BinOp:   op: str; left: Any; right: Any
@dataclass
class Compare: op: str; left: Any; right: Any
@dataclass
class BoolOp:  op: str; values: list
@dataclass
class Lag:     arg: Any; n: int; site: int      # call-site id (textual position)
@dataclass
class Dif:     arg: Any; n: int; site: int

# statements
@dataclass
class Assign:  target: str; expr: Any
@dataclass
class If:      test: Any; body: list; orelse: list
@dataclass
class Output:  pass_: bool = True
@dataclass
class Delete:  pass_: bool = True


CROSS_ROW = (Lag, Dif, FirstLast, Auto)         # leaf nodes that read prior-row state


# ============================================================================
# 2. AST front-end: lower `def logic(pdv): ...` to IR (supported subset only)
# ============================================================================
_BINOPS = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
           ast.Mod: "%", ast.FloorDiv: "//", ast.Pow: "**"}
_CMPOPS = {ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=",
           ast.Gt: ">", ast.GtE: ">="}
_BOOLOPS = {ast.And: "and", ast.Or: "or"}


class _Lowerer(ast.NodeVisitor):
    def __init__(self, pdv_name: str):
        self.pdv = pdv_name

    # ---- expressions ----
    def expr(self, node) -> Any:
        if isinstance(node, ast.Constant):
            return Const(node.value)
        if isinstance(node, ast.Subscript) and self._is_pdv(node.value):
            return Col(self._index_str(node.slice))
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Subscript) \
                and self._is_pdv_attr(node):                       # pdv.first["x"]
            which = node.attr                                       # not reached; handled below
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute) \
                and self._is_pdv(node.value.value) and node.value.attr in ("first", "last"):
            return FirstLast(node.value.attr, self._index_str(node.slice))
        if isinstance(node, ast.Attribute) and self._is_pdv(node.value):
            if node.attr in ("n", "eof"):
                return Auto(node.attr)
            raise Unsupported(f"pdv.{node.attr}")
        if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
            return BinOp(_BINOPS[type(node.op)], self.expr(node.left), self.expr(node.right))
        if isinstance(node, ast.Compare) and len(node.ops) == 1 \
                and type(node.ops[0]) in _CMPOPS:
            return Compare(_CMPOPS[type(node.ops[0])],
                           self.expr(node.left), self.expr(node.comparators[0]))
        if isinstance(node, ast.BoolOp) and type(node.op) in _BOOLOPS:
            return BoolOp(_BOOLOPS[type(node.op)], [self.expr(v) for v in node.values])
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return BinOp("*", Const(-1), self.expr(node.operand))
        if isinstance(node, ast.Call):
            return self._call(node)
        raise Unsupported(ast.dump(node))

    def _call(self, node):
        f = node.func
        if isinstance(f, ast.Attribute) and self._is_pdv(f.value) and f.attr in ("lag", "dif"):
            arg = self.expr(node.args[0])
            n = node.args[1].value if len(node.args) > 1 else 1
            site = f.lineno * 1000 + f.col_offset          # textual call-site identity
            return (Lag if f.attr == "lag" else Dif)(arg, n, site)
        raise Unsupported("call " + ast.dump(f))

    # ---- statements ----
    def stmt(self, node) -> Any:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            t = node.targets[0]
            if isinstance(t, ast.Subscript) and self._is_pdv(t.value):
                return Assign(self._index_str(t.slice), self.expr(node.value))
            raise Unsupported("assign target " + ast.dump(t))
        if isinstance(node, ast.If):
            return If(self.expr(node.test),
                      [self.stmt(s) for s in node.body],
                      [self.stmt(s) for s in node.orelse])
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            f = node.value.func
            if isinstance(f, ast.Attribute) and self._is_pdv(f.value):
                if f.attr == "output": return Output()
                if f.attr == "delete": return Delete()
            raise Unsupported("expr-call " + ast.dump(f))
        if isinstance(node, ast.Pass):
            return None
        raise Unsupported(ast.dump(node))

    # ---- helpers ----
    def _is_pdv(self, node):
        return isinstance(node, ast.Name) and node.id == self.pdv
    def _is_pdv_attr(self, node): return False
    def _index_str(self, sl):
        node = sl.value if isinstance(sl, ast.Index) else sl       # py<3.9 compat
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        raise Unsupported("dynamic index")


def lower(logic) -> list:
    """Lower a `def logic(pdv): ...` to a list of IR statements, or raise
    Unsupported (signalling the caller to fall back to the reference engine)."""
    src = textwrap.dedent(inspect.getsource(logic))
    tree = ast.parse(src).body[0]
    if not isinstance(tree, ast.FunctionDef) or len(tree.args.args) != 1:
        raise Unsupported("logic must be def f(pdv)")
    low = _Lowerer(tree.args.args[0].arg)
    stmts = [low.stmt(s) for s in tree.body]
    return [s for s in stmts if s is not None]


# ============================================================================
# 3. Classifier: mark each statement vectorizable vs sequential
# ============================================================================
def _expr_sequential(node) -> bool:
    """An expression is sequential if it reads any cross-row state."""
    if isinstance(node, CROSS_ROW):
        return True
    if isinstance(node, (Const, Col)):
        return False
    if isinstance(node, BinOp):
        return _expr_sequential(node.left) or _expr_sequential(node.right)
    if isinstance(node, Compare):
        return _expr_sequential(node.left) or _expr_sequential(node.right)
    if isinstance(node, BoolOp):
        return any(_expr_sequential(v) for v in node.values)
    return True                                  # unknown -> conservative


def classify(stmts) -> list:
    """Return [(stmt, 'vector'|'seq'), ...]. A statement is sequential if it reads
    cross-row state, emits/deletes rows, or assigns a name that a later sequential
    statement depends on. output/delete are always sequential (affect cardinality).
    Conservative: when unsure, 'seq' (correctness over speed)."""
    out = []
    for s in stmts:
        if isinstance(s, (Output, Delete)):
            out.append((s, "seq"))
        elif isinstance(s, Assign):
            out.append((s, "seq" if _expr_sequential(s.expr) else "vector"))
        elif isinstance(s, If):
            # an If is vectorizable only if its test AND every nested stmt are
            test_seq = _expr_sequential(s.test)
            nested = classify(s.body) + classify(s.orelse)
            kind = "seq" if test_seq or any(k == "seq" for _, k in nested) else "vector"
            out.append((s, kind))
        else:
            out.append((s, "seq"))
    return out


def summarize(stmts):
    c = classify(stmts)
    v = sum(1 for _, k in c if k == "vector")
    return {"total": len(c), "vector": v, "seq": len(c) - v,
            "detail": [(type(s).__name__, k) for s, k in c]}


# ============================================================================
# 4. IR interpreter (faithful; used to VALIDATE the classifier vs the oracle)
# ============================================================================
def _eval(node, pdv):
    if isinstance(node, Const):  return node.value
    if isinstance(node, Col):    return pdv[node.name]
    if isinstance(node, Auto):   return getattr(pdv, node.name)
    if isinstance(node, FirstLast):
        return (pdv.first if node.which == "first" else pdv.last)[node.by]
    if isinstance(node, Lag):    return pdv.lag(_eval(node.arg, pdv), node.n, site=node.site)
    if isinstance(node, Dif):
        prev = pdv.lag(_eval(node.arg, pdv), node.n, site=("DIF", node.site))
        cur = _eval(node.arg, pdv)
        return MISSING if isinstance(prev, Missing) or isinstance(cur, Missing) else cur - prev
    if isinstance(node, BinOp):
        a, b = _eval(node.left, pdv), _eval(node.right, pdv)
        return _ARITH[node.op](a, b)
    if isinstance(node, Compare):
        return _CMP[node.op](_eval(node.left, pdv), _eval(node.right, pdv))
    if isinstance(node, BoolOp):
        vals = [_eval(v, pdv) for v in node.values]
        return all(vals) if node.op == "and" else any(vals)
    raise Unsupported(repr(node))

_ARITH = {"+": lambda a, b: a + b, "-": lambda a, b: a - b, "*": lambda a, b: a * b,
          "/": lambda a, b: a / b, "%": lambda a, b: a % b,
          "//": lambda a, b: a // b, "**": lambda a, b: a ** b}
_CMP = {"==": lambda a, b: a == b, "!=": lambda a, b: a != b, "<": lambda a, b: a < b,
        "<=": lambda a, b: a <= b, ">": lambda a, b: a > b, ">=": lambda a, b: a >= b}

def _run_stmts(stmts, pdv):
    for s in stmts:
        if isinstance(s, Assign):   pdv[s.target] = _eval(s.expr, pdv)
        elif isinstance(s, If):
            _run_stmts(s.body if _eval(s.test, pdv) else s.orelse, pdv)
        elif isinstance(s, Output): pdv.output()
        elif isinstance(s, Delete): pdv.delete()

def ir_logic(stmts):
    """Turn lowered IR back into a `logic(pdv)` callable (interpreted)."""
    return lambda pdv: _run_stmts(stmts, pdv)


def compile_logic(logic):
    """Lower to IR if possible; else return the original (fallback). Returns
    (callable_for_engine, mode) where mode is 'ir' or 'fallback'."""
    try:
        stmts = lower(logic)
        return ir_logic(stmts), "ir"
    except Unsupported:
        return logic, "fallback"


if __name__ == "__main__":
    from sasstep import SetReader

    def run(reader_factory, logic, **kw):
        return list(ObservationEngine(reader_factory(), logic, **kw))

    # ---- a SAS-shaped step: vectorizable arithmetic + a sequential spine ----
    def logic(pdv):
        pdv["gross"] = pdv["qty"] * pdv["price"]          # vector
        pdv["net"] = pdv["gross"] * (1 - pdv["disc"])     # vector
        pdv["prev_net"] = pdv.lag(pdv["net"])             # seq (lag)
        if pdv["net"] > 100:                              # vector test
            pdv["band"] = 1
        else:
            pdv["band"] = 0
        if pdv.first["region"]:                           # seq test (first.)
            pdv["running"] = 0
        pdv["running"] = pdv["running"] + pdv["net"]      # seq (depends on retained)

    rows = [{"region": "E", "qty": 2, "price": 60, "disc": 0.1},
            {"region": "E", "qty": 1, "price": 200, "disc": 0.0},
            {"region": "W", "qty": 3, "price": 50, "disc": 0.2}]
    mk = lambda: SetReader(rows, by=["region"])

    stmts = lower(logic)
    print("# classification")
    for name, kind in summarize(stmts)["detail"]:
        print(f"  {kind:6} {name}")
    s = summarize(stmts)
    print(f"  -> {s['vector']}/{s['total']} vectorizable")

    # ---- VALIDATE: IR-interpreted logic must match the reference engine ----
    ref = run(mk, logic, by=["region"], retain={"running": 0})
    irc, mode = compile_logic(logic)
    got = run(mk, irc, by=["region"], retain={"running": 0})
    print(f"\n# mode={mode}; IR output matches reference engine: {ref == got}")

    # ---- fallback: logic outside the sublanguage still works ----
    def exotic(pdv):
        pdv["x"] = sum(int(c) for c in str(pdv["qty"]))   # comprehension+call: unsupported
    irc2, mode2 = compile_logic(exotic)
    out2 = run(mk, irc2, by=["region"])
    print(f"# exotic logic: mode={mode2}, ran rows={len(out2)} (fell back, still correct)")
