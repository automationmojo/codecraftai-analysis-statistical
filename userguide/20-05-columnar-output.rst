.. _20-05-columnar-output:

==================
Columnar Output
==================

For pipelines that stay on the vector path, materializing one Python dict
per row at every stage is the dominant cost. :class:`ColumnFrame` and
:class:`ColumnarStep` keep results columnar end to end and materialize rows
only when a consumer needs them.

ColumnFrame
===========

A :class:`ColumnFrame` wraps a ``{name: numpy.ndarray}`` mapping plus an
ordered list of column names. It supports:

* ``frame.columns`` -- the ordered column list;
* ``len(frame)`` -- number of rows;
* ``frame["name"]`` -- the underlying ``ndarray`` (no copy);
* ``frame[index]`` -- a single row dict (materialized on demand);
* iteration over rows;
* ``frame.head(k)`` -- the first ``k`` rows;
* ``frame.to_dicts()`` -- materialize every row;
* ``frame.to_pandas()`` -- requires ``pandas``;
* ``frame.to_arrow()`` -- requires ``pyarrow``.

The class is deliberately thin. It is a typed view over numpy arrays, not a
DataFrame. Use ``to_pandas`` or ``to_arrow`` when you need richer operations
downstream.

ColumnarStep
============

:class:`ColumnarStep` extends :class:`CompiledStep`. It accepts either a row
iterable *or* a :class:`ColumnFrame` and returns a :class:`ColumnFrame`. When
the input is already a :class:`ColumnFrame`, the underlying arrays are
reused -- no per-row materialization happens between stages.

.. code-block:: python

    from ccai.analysis.statistical import ColumnarStep

    def stage_one(pdv):
        pdv["gross"] = pdv["qty"] * pdv["price"]
        pdv["net"]   = pdv["gross"] * (1 - pdv["disc"])
        return

    def stage_two(pdv):
        pdv["margin"] = pdv["net"] / pdv["gross"]
        return

    cf1 = ColumnarStep(logic=stage_one).run_columnar(data=rows)
    cf2 = ColumnarStep(logic=stage_two).run_columnar(data=cf1)
    materialized = cf2.to_dicts()

For pipelines that hit the hybrid or fallback path, :class:`ColumnarStep`
still returns a :class:`ColumnFrame` -- it materializes the row-loop output
once at the boundary so the return type stays uniform.

Pandas / Arrow interoperability
===============================

``to_pandas`` and ``to_arrow`` are import-on-demand. The package does not
declare ``pandas`` or ``pyarrow`` as dependencies; you opt in by installing
them in your environment. The exporters share the same column arrays the
frame holds, so the conversion is cheap.

When not to use it
==================

If your step has a sequential spine (LAG, RETAIN, BY-group accumulation),
:class:`ColumnarStep` will produce a :class:`ColumnFrame` but the heavy
lifting will still happen in the row loop. The columnar advantage only
materializes when the whole step is vector-classified end to end. Use the
advisor in :doc:`20-06-migration-advisor` to confirm before benchmarking.
