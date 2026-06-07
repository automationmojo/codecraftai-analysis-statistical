.. _20-06-migration-advisor:

============================
Migration Advisor
============================

The advisor answers two questions:

1. For each statement in a user logic function, will the executor put it on
   the fast path or the row loop?
2. For each statement that landed in the loop, *why*?

It uses the same lowerer and scheduler that the executor uses, so its
verdict matches the executor's actual behavior. No need to benchmark to
find out where the slow path is hiding.

Calling the advisor
===================

.. code-block:: python

    from ccai.analysis.statistical import report

    def step(pdv):
        pdv["gross"]   = pdv["qty"] * pdv["price"]
        pdv["net"]     = pdv["gross"] * (1 - pdv["disc"])
        pdv["prev"]    = pdv.lag(pdv["net"])
        if pdv["net"] > 100:
            pdv["band"] = 2
        else:
            pdv["band"] = 1
        if pdv.first["region"]:
            pdv["running"] = 0
        pdv["running"] = pdv["running"] + pdv["net"]
        pdv["flag"]    = pdv["running"] > 1000
        return

    print(report(logic=step,
                 source_cols=["region", "qty", "price", "disc"],
                 retain={"running"}).text)

The :class:`Report` exposes:

* ``path`` -- ``"vector"``, ``"hybrid"``, or ``"fallback"``;
* ``lines`` -- one :class:`Line` per top-level statement, each carrying its
  classification (``"batch"`` or ``"loop"``), a category, a short reason,
  and a list of blocker identifiers;
* ``unsupported`` -- a short cause when the whole step falls back;
* ``text`` -- a human-readable rendering for terminals.

Categories
==========

Loop-bound statements get one of four categories:

* **irreducible** -- the statement reads cross-row state (LAG, DIF,
  first./last., automatic variables). The reference engine is the only
  thing that can run it. Speeding these up needs a JIT, not realignment.
* **tool-limited** -- a vectorizable conditional ``if`` that currently runs
  in the loop because ``where()``-style vectorization is not yet built.
  Not a code problem; not a JIT problem either. A future executor pass
  closes this gap.
* **dependency** -- a statement that *would* vectorize but reads a column
  produced by a sequential statement upstream. If that upstream column is
  produced in a separate compiled step (so it joins the available set
  before this step runs), this statement moves to the fast path. This is
  the lever you have: realign your pipeline boundaries.
* **cardinality** -- ``output`` and ``delete`` change the number of rows
  emitted. They must run in the loop by definition.

A fully ``"vector"`` report still includes a hint: the columnar output
in :doc:`20-05-columnar-output` removes the remaining per-row dict
materialization cost.

When to consult the advisor
===========================

* **Before you tune.** If the advisor says the step is fully vectorized,
  the bottleneck is elsewhere (your reader, your serializer, your I/O).
* **When porting a SAS job.** Run the advisor against the first Python
  draft. Any *unsupported* causes are direct rewriting hints. Any
  *dependency* causes suggest the SAS step is naturally two steps in
  disguise; splitting it gives you both a clearer port and faster output.
* **When a step regresses in CI.** Run the advisor before and after; the
  per-line categories make it obvious which statement(s) changed.
