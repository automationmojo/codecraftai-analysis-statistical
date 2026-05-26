"""
sasstep_report -- migration & optimization advisor over the classified IR.

The connective tissue between the two stories. It runs the same analysis the
executor uses, but instead of picking a path it explains one: per statement,
fast (batch) or loop, and for every loop statement the precise REASON, sorted
into what you can act on vs what's irreducible:

  * irreducible   -- inherent cross-row semantics (lag/dif/first./last./_N_) or
                     output cardinality. Can't be realigned away; only the JIT
                     speeds these up.
  * tool-limited  -- a vectorizable conditional that today runs in the loop
                     (where()-style vectorization not yet built). Not your code.
  * dependency    -- a statement that would vectorize but reads a sequential
                     value; if that value can come from an upstream step, this
                     one moves to the fast path. THIS is the realignment lever.
  * unsupported   -- outside the sublanguage; whole step falls back. Rewrite in
                     the sublanguage to enable any vectorization.

Same oracle, same IR -- so the advice matches what the executor actually does.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from sasstep_ir import (lower, Unsupported, _expr_sequential,
                        Assign, If, Output, Delete, BinOp, Compare, BoolOp,
                        Lag, Dif, FirstLast, Auto)
from sasstep_exec import _reads, _assigned


def _crossrow_labels(node) -> list:
    out = []
    def walk(n):
        if isinstance(n, Lag):       out.append(f"lag(n={n.n})")
        elif isinstance(n, Dif):     out.append(f"dif(n={n.n})")
        elif isinstance(n, FirstLast): out.append(f"{n.which}.{n.by}")
        elif isinstance(n, Auto):    out.append(f"_{n.name}_")
        elif isinstance(n, BinOp):   walk(n.left); walk(n.right)
        elif isinstance(n, Compare): walk(n.left); walk(n.right)
        elif isinstance(n, BoolOp):  [walk(v) for v in n.values]
    walk(node)
    return out


@dataclass
class Line:
    index: int
    stmt: str
    klass: str         # "batch" | "loop"
    category: str      # "batch"|"irreducible"|"tool-limited"|"dependency"|"cardinality"
    reason: str
    blockers: list = field(default_factory=list)


@dataclass
class Report:
    path: str          # "vector" | "hybrid" | "fallback"
    lines: list
    unsupported: str = ""

    @property
    def n_batch(self): return sum(1 for L in self.lines if L.klass == "batch")
    @property
    def n_total(self): return len(self.lines)

    @property
    def text(self) -> str:
        if self.path == "fallback":
            return (f"PATH: fallback (row loop, no vectorization)\n"
                    f"  cause: {self.unsupported}\n"
                    f"  fix:   rewrite in the sublanguage (assignment / if / lag / "
                    f"dif / first./last. / output) to enable any fast path.")
        frac = f"{self.n_batch}/{self.n_total}"
        pct = (100 * self.n_batch // self.n_total) if self.n_total else 0
        head = f"PATH: {self.path} -- {frac} statements vectorized ({pct}%)"
        rows = []
        for L in self.lines:
            mark = "FAST" if L.klass == "batch" else "loop"
            rows.append(f"  [{mark}] {L.stmt:<10} {L.reason}")
        # synthesize guidance by category
        cats = {}
        for L in self.lines:
            if L.klass == "loop":
                cats.setdefault(L.category, []).append(L)
        advice = []
        if "dependency" in cats:
            blk = sorted({b for L in cats["dependency"] for b in L.blockers})
            advice.append(f"  REALIGN: {len(cats['dependency'])} statement(s) would "
                          f"vectorize but read sequential value(s) {blk}. If those are "
                          f"produced in a separate upstream step, these move to FAST.")
        if "tool-limited" in cats:
            advice.append(f"  TOOL:    {len(cats['tool-limited'])} vectorizable "
                          f"conditional(s) run in the loop today (where()-vectorization "
                          f"not yet built). Not a code problem.")
        irr = len(cats.get("irreducible", [])) + len(cats.get("cardinality", []))
        if irr:
            advice.append(f"  JIT:     {irr} statement(s) are irreducibly sequential "
                          f"(inherent cross-row logic / output). Speed here needs the "
                          f"compiled loop, not realignment.")
        if not advice and self.path == "vector":
            advice.append("  Already fully vectorized; columnar output would remove the "
                          "remaining per-row materialization cost.")
        return "\n".join([head] + rows + [""] + advice)


def report(logic, source_cols, retain=None) -> Report:
    retain = set(retain or [])
    try:
        stmts = lower(logic)
    except Unsupported as e:
        return Report("fallback", [], unsupported=str(e)[:70])

    avail = set(source_cols) - retain
    lines = []
    for i, s in enumerate(stmts):
        if isinstance(s, Assign):
            cr = _crossrow_labels(s.expr)
            if cr:
                lines.append(Line(i, "assign", "loop", "irreducible",
                                  "reads cross-row state: " + ", ".join(cr), cr))
                avail.discard(s.target)
            else:
                blockers = sorted(_reads(s.expr) - avail)
                if blockers:
                    lines.append(Line(i, "assign", "loop", "dependency",
                                      f"depends on sequential value(s): {blockers}", blockers))
                    avail.discard(s.target)
                else:
                    lines.append(Line(i, "assign", "batch", "batch",
                                      "pure current-row arithmetic"))
                    avail.add(s.target)
        elif isinstance(s, If):
            cr = _crossrow_labels(s.test)
            dep = sorted(_reads(s.test) - avail)
            if cr:
                lines.append(Line(i, "if", "loop", "irreducible",
                                  "conditional on cross-row state: " + ", ".join(cr), cr))
            elif dep:
                lines.append(Line(i, "if", "loop", "dependency",
                                  f"conditional on sequential value(s): {dep}", dep))
            else:
                lines.append(Line(i, "if", "loop", "tool-limited",
                                  "vectorizable conditional (runs in loop for now)"))
            for t in _assigned(s):
                avail.discard(t)
        elif isinstance(s, (Output, Delete)):
            lines.append(Line(i, type(s).__name__.lower(), "loop", "cardinality",
                              "changes output cardinality"))

    path = "vector" if all(L.klass == "batch" for L in lines) and lines else "hybrid"
    return Report(path, lines)


if __name__ == "__main__":
    def transform(pdv):
        pdv["gross"] = pdv["qty"] * pdv["price"]
        pdv["net"] = pdv["gross"] * (1 - pdv["disc"])
        pdv["tax"] = pdv["net"] * 0.2

    def mixed(pdv):
        pdv["gross"] = pdv["qty"] * pdv["price"]          # batch
        pdv["net"] = pdv["gross"] * (1 - pdv["disc"])     # batch
        pdv["prev"] = pdv.lag(pdv["net"])                 # irreducible (lag)
        if pdv["net"] > 100:                              # tool-limited (vectorizable if)
            pdv["band"] = 2
        else:
            pdv["band"] = 1
        if pdv.first["region"]:                           # irreducible (first.)
            pdv["running"] = 0
        pdv["running"] = pdv["running"] + pdv["net"]      # dependency (reads running)
        pdv["flag"] = pdv["running"] > 1000               # dependency (reads running)

    def exotic(pdv):
        pdv["x"] = sum(int(c) for c in str(pdv["qty"]))

    print(report(transform, ["qty", "price", "disc"]).text)
    print("\n" + "=" * 72 + "\n")
    print(report(mixed, ["region", "qty", "price", "disc"], retain={"running"}).text)
    print("\n" + "=" * 72 + "\n")
    print(report(exotic, ["qty"]).text)
