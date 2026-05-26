.. _20-01-engine-core-and-pdv:

============================
Engine Core and the PDV
============================

The reference engine is a faithful Python rendition of the SAS DATA step. It
exists to be **correct**, not fast; everything else in the package is
validated against it.

The Program Data Vector
=======================

The Program Data Vector (PDV) is the working register set for the current
row. In code it is :class:`RecordFrame`, a dictionary-ordered table of typed
:class:`Slot` entries. Each slot carries:

* ``stype`` -- the storage type name (``num``, ``char``, or a registered
  custom type such as ``decimal``);
* ``length`` -- fixed storage length (in characters for ``char``);
* ``fmt`` -- optional default output format spec;
* ``informat`` -- optional default input informat spec;
* ``retain`` -- the load-bearing flag that controls top-of-step reset;
* ``value`` -- the current value.

A slot is declared explicitly via :meth:`RecordFrame.declare` or implicitly on
first assignment. Implicit declaration infers ``num`` for numbers and ``char``
for strings; custom storage types are never inferred (declare-only opt-in).

The implicit loop
=================

The engine drives the PDV through five explicit :class:`Phase` states per
observation::

    TOP_OF_STEP -> READ -> EXECUTE -> BOTTOM -> ... -> DONE

* **TOP_OF_STEP** -- :meth:`RecordFrame.reset_non_retained` runs. Slots
  flagged retained survive; everything else returns to its storage-type
  missing sentinel.
* **READ** -- the configured :class:`Reader` returns
  ``(row, in_flags, cur_key, next_key)``. :meth:`RecordFrame.load` writes the
  row's values and marks every loaded slot retained for the duration of the
  row (source variables retain until the next read overwrites them).
* **EXECUTE** -- the user's ``logic(pdv)`` callable runs. It reads/writes the
  PDV by name and may call ``pdv.output()`` or ``pdv.delete()``.
* **BOTTOM** -- if no ``output()`` and no ``delete()`` was called, the engine
  emits a snapshot of the PDV (optionally projected by KEEP/DROP/RENAME).
* **DONE** -- the reader is exhausted; iteration ends.

Cross-row state
===============

The PDV's reset rule is what makes cross-row features explainable rather
than ad-hoc. Every cross-row feature comes down to "which slots survive the
top-of-step reset":

* **RETAIN** declared at construction time marks a slot retained from the
  outset. The engine even seeds an initial value, equivalent to SAS
  ``retain total 0;``.
* **Sum statement** (``pdv["total"] = pdv["total"] + pdv["amount"]``) works
  because ``total`` was retained.
* **BY-group first./last.** are computed by the engine, not the reader, by
  inspecting ``cur_key`` and ``next_key`` against the previous key. The
  reader's only job is to produce those keys.
* **LAG/DIF** are stateful functions hosted by the engine's
  :class:`StatefulFunctions` mixin. Each call site keeps its own
  :class:`LagQueue`, keyed by source filename and line number, so a
  conditional ``pdv.lag()`` only enqueues values when its branch executes.

User-logic API surface
======================

Inside ``logic(pdv)`` the user has:

* ``pdv["name"]`` / ``pdv["name"] = value`` -- read / write a PDV slot.
* ``pdv.first[by_var]`` / ``pdv.last[by_var]`` -- BY-group boundary flags.
* ``pdv.in_["flag"]`` -- IN= flags from a :class:`MergeReader`.
* ``pdv.lag(value, n=1)`` / ``pdv.dif(value, n=1)`` -- cross-row queues.
* ``pdv.output()`` -- emit the current PDV snapshot.
* ``pdv.delete()`` -- suppress this row's BOTTOM emission.
* ``pdv.put(name, spec=None)`` -- apply a format to a slot's value.
* ``pdv.n`` -- the 1-based observation counter; ``pdv.eof`` -- True after the
  last row has been read.

That's the entire surface. The IR sublanguage covered in
:doc:`20-04-ir-classification-and-vectorization` is exactly what can be
detected and rewritten from this surface.
