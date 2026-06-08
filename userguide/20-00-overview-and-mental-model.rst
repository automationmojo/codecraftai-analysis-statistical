.. _20-00-overview-and-mental-model:

===================================================
codecraftai-analysis-statistical -- Overview and Model
===================================================

This package provides patterns for authoring and porting statistical analysis
jobs to Python whose results are *directly comparable* to the equivalent SAS
jobs. The core mental model is the SAS DATA step: a row-at-a-time procedural
machine with three pieces:

* a Program Data Vector (PDV) -- the working register set for the current row;
* an implicit loop driving ``reset -> read -> execute -> output -> repeat``;
* cross-row state rules (RETAIN, BY-group ``first.``/``last.``, LAG/DIF).

Public surface
==============

The supported public surface is everything listed in
``ccai.analysis.statistical.__all__``. Highlights:

* ``ObservationEngine`` -- the iterator over the implicit loop.
* ``SetReader``, ``MergeReader``, ``DatabaseReader`` -- the READ-phase
  strategies.
* ``Missing``, ``MISSING``, ``missing`` -- the SAS missing-value family.
* ``Phase`` -- the implicit-loop state machine, made explicit.
* ``register_format`` / ``register_informat`` / ``register_type`` -- the
  SAS-faithful extension points.
* ``CompiledStep`` / ``ColumnarStep`` / ``ColumnFrame`` -- the optimizing
  executor and its columnar output.
* ``LogicCompiler`` / ``UnsupportedError`` -- the IR front end and fallback
  contract.
* ``ReportBuilder`` / ``report`` -- the migration / optimization advisor.
* ``DialectDeclaration`` / ``PostgreSqlDialect`` / ``OracleDialect`` /
  ``MySqlDialect`` / ``SqlServerDialect`` -- dialect-named declaration and
  per-RDBMS type maps.

Three-layer architecture
========================

1. **Reference engine (correctness oracle).** The ``ObservationEngine`` and
   the readers implement SAS DATA-step semantics row at a time. This is the
   authority every other layer is validated against.
2. **IR front end.** ``AstLowerer`` lowers a plain Python ``def logic(pdv)``
   to a small set of IR nodes. ``Classifier`` marks each statement as
   vectorizable or sequential. ``IrInterpreter`` re-runs the IR through the
   reference engine -- proving the IR is faithful before any fast path is
   built.
3. **Optimizing executor.** ``Scheduler`` performs a forward dataflow pass and
   splits the IR into ``(batch, loop)``. ``CompiledStep`` dispatches:
   ``vector`` when there is no row loop, ``hybrid`` when there is, and
   ``fallback`` when the function is outside the sublanguage. ``ColumnarStep``
   keeps the fast path columnar end to end.

See :doc:`20-07-porting-sas-jobs-to-python` for worked SAS-to-Python ports.
