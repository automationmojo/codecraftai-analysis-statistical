.. _20-07-porting-sas-jobs-to-python:

==================================
Porting SAS Jobs to Python (Recipe)
==================================

The package is built to make the port a *mechanical* exercise. Each SAS
statement has a single corresponding shape in Python.

BY-group accumulation
=====================

SAS::

    data totals;
        set sales;
        by region customer;
        retain total 0;
        if first.customer then total = 0;
        total = total + amount;
        if last.customer then output;
    run;

Python::

    from automojo.analysis.statistical import (ObservationEngine, SetReader)

    def accumulate(pdv):
        if pdv.first["customer"] is True:
            pdv["total"] = 0
        pdv["total"] = pdv["total"] + pdv["amount"]
        if pdv.last["customer"] is True:
            pdv.output()
        return

    rows = list(ObservationEngine(
        reader=SetReader(source=sales, by=["region", "customer"]),
        logic=accumulate, by=["region", "customer"],
        retain={"total": 0}))

Match-merge with IN= flags
==========================

SAS::

    data merged;
        merge A (in=inA) B (in=inB);
        by id;
    run;

Python::

    from automojo.analysis.statistical import (MergeReader, ObservationEngine)

    reader = MergeReader(sources={"A": a_rows, "B": b_rows}, by=["id"],
                         in_flags={"A": "inA", "B": "inB"})

    def passthrough(pdv):
        pdv["inA"] = pdv.in_["inA"]
        pdv["inB"] = pdv.in_["inB"]
        return

    list(ObservationEngine(reader=reader, logic=passthrough, by=["id"]))

LAG / DIF
=========

SAS::

    prev = lag(amount);
    delta = dif(amount);

Python::

    pdv["prev"] = pdv.lag(pdv["amount"])
    pdv["delta"] = pdv.dif(pdv["amount"])

KEEP / DROP / RENAME
====================

SAS::

    data out;
        set in;
        keep x doubled;
        rename x = n;
        doubled = x * 2;
    run;

Python::

    list(ObservationEngine(reader=SetReader(source=in_rows),
                           logic=lambda p: p.__setitem__("doubled",
                                                         p["x"] * 2),
                           keep=["x", "doubled"], rename={"x": "n"}))

Database sources
================

Wrap any PEP 249 cursor with :class:`DatabaseReader` and supply the dialect
type map so the PDV can be typed from ``cursor.description``::

    from automojo.analysis.statistical import (DatabaseReader, ObservationEngine,
                                               PostgreSqlDialect)
    cur = conn.cursor()
    cur.execute("SELECT id, salary FROM employees ORDER BY id")
    list(ObservationEngine(reader=DatabaseReader(
        cursor=cur, dialect=PostgreSqlDialect.TYPE_MAP),
        logic=lambda p: None))

Validating equivalence against SAS
==================================

Run the SAS job and the Python port over the same input; compare row by row::

    assert python_rows == sas_rows

The reference engine is bit-deterministic given the same logic and inputs; if
any optimization is enabled (``CompiledStep``, ``ColumnarStep``) the package
guarantees its output equals the reference engine's. So a Python port that
matches the reference engine and the SAS job is portable to the fast path
without further validation.
