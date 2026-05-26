"""
sasstep_exec -- hybrid executor over the classified IR.

Turns the proven-correct IR (sasstep_ir) into actual speed. The key analysis is
NOT the classifier alone: "vectorizable" means "pure function of the current
row", but to PRECOMPUTE a column before the row loop we also need every input to
be batch-available. A locally-vectorizable statement that reads a loop-produced
(sequential) value must be demoted back into the loop. `schedule()` does that
forward dataflow pass.

Three execution paths fall out:
  * fully-vectorizable (no sequential statements) -> compute every column as
    arrays, emit rows directly, NO per-row interpretation. The big win.
  * hybrid -> precompute batch-available columns, feed them as extra source
    columns into the reference row loop, which runs only the sequential residual.
  * fallback -> unsupported logic runs unchanged on the reference engine.

Correctness is validated against the reference engine (the oracle) for all paths.
"""
from __future__ import annotations
import numpy as np

from sasstep import ObservationEngine, SetReader
from sasstep_ir import (lower, classify, Unsupported, ir_logic,
                        _expr_sequential, Const, Col, BinOp, Compare, BoolOp,
                        Assign, If, Output, Delete)


# ---- expression helpers ----------------------------------------------------
def _reads(node) -> set:
    if isinstance(node, Col):     return {node.name}
    if isinstance(node, Const):   return set()
    if isinstance(node, BinOp):   return _reads(node.left) | _reads(node.right)
    if isinstance(node, Compare): return _reads(node.left) | _reads(node.right)
    if isinstance(node, BoolOp):
        s = set()
        for v in node.values: s |= _reads(v)
        return s
    return set()                                   # cross-row leaves: handled as seq

def _assigned(stmt) -> set:
    if isinstance(stmt, Assign): return {stmt.target}
    if isinstance(stmt, If):
        s = set()
        for x in stmt.body + stmt.orelse: s |= _assigned(x)
        return s
    return set()


# ---- the forward dataflow pass ---------------------------------------------
def schedule(stmts, source_cols):
    """Split statements into (batch, loop). A statement is BATCH iff it is
    vector-classified AND all its inputs are batch-available at that program
    point. Anything else is LOOP, and its targets become loop-only from then on
    (so later statements reading them are demoted too). Program order preserved
    within loop."""
    avail = set(source_cols)
    batch, loop = [], []
    for s in stmts:
        if isinstance(s, Assign) and not _expr_sequential(s.expr) \
                and _reads(s.expr).issubset(avail):
            batch.append(s)
            avail.add(s.target)                    # now batch-available
        else:
            loop.append(s)
            avail -= _assigned(s)                  # its targets are loop-only
    return batch, loop


# ---- vectorized expression evaluator (numpy over whole columns) ------------
_VA = {"+": np.add, "-": np.subtract, "*": np.multiply, "/": np.divide,
       "%": np.mod, "//": np.floor_divide, "**": np.power}
_VC = {"==": np.equal, "!=": np.not_equal, "<": np.less, "<=": np.less_equal,
       ">": np.greater, ">=": np.greater_equal}

def _veval(node, cols):
    if isinstance(node, Const):   return node.value
    if isinstance(node, Col):     return cols[node.name]
    if isinstance(node, BinOp):   return _VA[node.op](_veval(node.left, cols),
                                                      _veval(node.right, cols))
    if isinstance(node, Compare): return _VC[node.op](_veval(node.left, cols),
                                                      _veval(node.right, cols))
    if isinstance(node, BoolOp):
        vs = [_veval(v, cols) for v in node.values]
        out = vs[0]
        for v in vs[1:]:
            out = np.logical_and(out, v) if node.op == "and" else np.logical_or(out, v)
        return out
    raise Unsupported(repr(node))


def _columns(rows):
    cols = {}
    for k in rows[0].keys():
        cols[k] = np.array([r.get(k) for r in rows])
    return cols

def _scalar(x):
    return x.item() if hasattr(x, "item") else x


# ---- the compiled step ------------------------------------------------------
class CompiledStep:
    def __init__(self, logic, by=None, retain=None):
        self.by = by or []; self.retain = retain or {}
        self._logic = logic
        try:
            self.stmts = lower(logic)
            self.mode = "ir"
        except Unsupported:
            self.stmts = None
            self.mode = "fallback"

    def plan(self, source_cols):
        if self.mode == "fallback":
            return "fallback", None, None
        batch, loop = schedule(self.stmts, source_cols)
        return ("vector" if not loop else "hybrid"), batch, loop

    def run(self, rows):
        if not rows:
            return []
        source_cols = list(rows[0].keys())
        path, batch, loop = self.plan(source_cols)

        if path == "fallback":
            return list(ObservationEngine(SetReader(rows, by=self.by), self._logic,
                                          by=self.by, retain=self.retain))
        # precompute batch-available columns as arrays
        cols = _columns(rows)
        n = len(rows)
        for s in batch:
            val = _veval(s.expr, cols)
            cols[s.target] = val if np.ndim(val) else np.full(n, val)

        if path == "vector":                       # no row loop at all
            names = list(cols.keys())
            return [{k: _scalar(cols[k][i]) for k in names} for i in range(n)]

        # hybrid: feed precomputed columns as source into the row loop
        names = list(cols.keys())
        augmented = ({k: _scalar(cols[k][i]) for k in names} for i in range(n))
        return list(ObservationEngine(SetReader(augmented, by=self.by),
                                      ir_logic(loop), by=self.by, retain=self.retain))


if __name__ == "__main__":
    import time

    def reference(rows, logic, **kw):
        return list(ObservationEngine(SetReader(list(rows), by=kw.get("by", [])),
                                      logic, **kw))

    # ---- (1) FULLY-VECTORIZABLE: pure arithmetic transform -----------------
    def transform(pdv):
        pdv["gross"] = pdv["qty"] * pdv["price"]
        pdv["net"] = pdv["gross"] * (1 - pdv["disc"])
        pdv["tax"] = pdv["net"] * 0.2
        pdv["total"] = pdv["net"] + pdv["tax"]

    small = [{"qty": 2, "price": 60.0, "disc": 0.1},
             {"qty": 1, "price": 200.0, "disc": 0.0}]
    cs = CompiledStep(transform)
    print("# plan:", cs.plan(list(small[0].keys()))[0])
    ref = reference(small, transform)
    got = cs.run(small)
    print("# fully-vector matches reference:", ref == got)

    # ---- (2) HYBRID: vector arithmetic + sequential spine ------------------
    def mixed(pdv):
        pdv["gross"] = pdv["qty"] * pdv["price"]      # vector
        pdv["net"] = pdv["gross"] * (1 - pdv["disc"]) # vector
        pdv["prev_net"] = pdv.lag(pdv["net"])         # seq
        if pdv.first["region"]:                       # seq test
            pdv["running"] = 0
        pdv["running"] = pdv["running"] + pdv["net"]  # seq
    mrows = [{"region": "E", "qty": 2, "price": 60.0, "disc": 0.1},
             {"region": "E", "qty": 1, "price": 200.0, "disc": 0.0},
             {"region": "W", "qty": 3, "price": 50.0, "disc": 0.2}]
    cs2 = CompiledStep(mixed, by=["region"], retain={"running": 0})
    print("\n# plan:", cs2.plan(list(mrows[0].keys()))[0])
    ref2 = reference(mrows, mixed, by=["region"], retain={"running": 0})
    got2 = cs2.run(mrows)
    print("# hybrid matches reference:", ref2 == got2)

    # ---- (3) FALLBACK ------------------------------------------------------
    def exotic(pdv):
        pdv["x"] = sum(int(c) for c in str(pdv["qty"]))
    cs3 = CompiledStep(exotic)
    print("\n# plan:", cs3.plan(["qty"])[0])
    print("# fallback matches reference:",
          reference(mrows[:1], exotic) == cs3.run(mrows[:1]))

    # ---- (4) BENCHMARK: fully-vector vs reference on 200k rows -------------
    N = 200_000
    big = [{"qty": i % 7 + 1, "price": float(i % 100 + 1), "disc": (i % 5) / 10.0}
           for i in range(N)]
    t0 = time.perf_counter(); r_ref = reference(big, transform); t1 = time.perf_counter()
    t2 = time.perf_counter(); r_vec = CompiledStep(transform).run(big); t3 = time.perf_counter()
    print(f"\n# benchmark on {N:,} rows (pure transform)")
    print(f"  reference engine : {t1 - t0:7.3f}s")
    print(f"  vectorized       : {t3 - t2:7.3f}s   ({(t1 - t0) / (t3 - t2):.1f}x faster)")
    print(f"  identical output : {r_ref == r_vec}")
