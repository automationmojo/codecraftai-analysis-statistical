.. _20-04-ir-classification-and-vectorization:

==========================================
IR, Classification, and Vectorization
==========================================

The reference engine is correct. It is not fast. For workloads where speed
matters, the package compiles user logic into an inspectable IR, classifies
each statement, and dispatches a hybrid execution plan. The fast path is
**proven** to match the reference engine row for row -- it is an
optimization of correct semantics, never a redefinition.

The sublanguage
===============

The IR covers a small, closed sublanguage of Python:

* literal constants,
* PDV reads (``pdv["x"]``), assignments (``pdv["x"] = ...``),
* engine automatics (``pdv.n``, ``pdv.eof``),
* BY-group flags (``pdv.first["x"]``, ``pdv.last["x"]``),
* binary arithmetic (``+ - * / % // **``),
* single comparisons (``== != < <= > >=``),
* boolean ``and`` / ``or`` chains,
* ``pdv.lag(...)`` / ``pdv.dif(...)``,
* ``if`` / ``else`` blocks,
* ``pdv.output()`` / ``pdv.delete()``.

Logic that strays outside the sublanguage -- comprehensions, calls to
arbitrary functions, dynamic indexing, etc. -- raises :class:`UnsupportedError`
during lowering, and the executor falls back to running the original Python
function through the reference engine. The result is still correct; only the
fast path is unavailable.

Classification
==============

:class:`Classifier` walks the IR and labels each top-level statement:

* **vector** -- a pure function of the current row. Safe to evaluate over
  whole-column arrays.
* **seq** -- reads cross-row state (``lag``, ``dif``, ``first.``, ``last.``,
  ``_N_``), or affects output cardinality (``output``, ``delete``), or has
  any nested statement that does.

The classification is conservative: when in doubt, ``seq``. Correctness
beats speed, always.

Scheduling
==========

Classification alone is not enough. A statement that is *locally*
vectorizable may still need to run inside the row loop because one of its
inputs is produced by a sequential statement. :class:`Scheduler` performs a
forward dataflow pass:

* Start with the source columns as the available set.
* For each statement in source order:

  * If it is an :class:`AssignNode`, is classified vector, and every column
    it reads is available, it goes into ``batch`` and its target joins the
    available set.
  * Otherwise it goes into ``loop`` and its targets *leave* the available
    set (later statements that read them must also be demoted).

The output is two lists: ``(batch, loop)``. ``batch`` runs once over arrays
before the row loop starts; ``loop`` runs through the reference engine over
the already-augmented rows.

Three execution paths
=====================

:class:`CompiledStep` dispatches on the schedule:

* **vector** -- ``loop`` is empty. No row iteration; every column is
  computed as an array and the output is materialized only when callers
  request rows.
* **hybrid** -- ``loop`` is non-empty. The batch columns are materialized
  per-row and fed into the reference engine as augmented source rows; the
  engine runs only the sequential residual.
* **fallback** -- lowering failed. The original function runs unchanged
  through the reference engine.

Bit-equal output is the contract. Every test that pins the executor against
the reference engine in ``tests/.../oracle/`` enforces it.

Inspecting a plan
=================

:doc:`20-06-migration-advisor` covers the :class:`ReportBuilder` advisor,
which uses the same scheduler the executor does to explain, per statement,
why it ended up where it did -- and what (if anything) you can rewrite to
move more statements onto the fast path.
