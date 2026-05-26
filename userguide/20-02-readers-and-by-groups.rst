.. _20-02-readers-and-by-groups:

==========================
Readers and BY-Groups
==========================

The READ phase is the only phase that changes shape across input modes. The
engine never branches on input mode; every reader returns a uniform tuple::

    (row, in_flags, cur_key, next_key)

Built-in readers
================

:class:`SetReader` -- the SAS ``SET`` analogue
----------------------------------------------

Reads a single iterable of dictionaries. With a BY-key list, it derives
``cur_key`` and ``next_key`` from the named columns. Empty ``in_flags``;
single-source readers don't report IN= flags.

.. code-block:: python

    reader = SetReader(source=rows, by=["region", "customer"])

:class:`MergeReader` -- the SAS ``MERGE`` analogue
--------------------------------------------------

Multi-cursor sub-state-machine. Each input source must already be sorted by
the BY key (push ``ORDER BY`` into the database, or use a future PROC SORT
shim). For each BY group the reader:

* combines rows positionally (not Cartesian),
* fills in retained values from sources that have exhausted within the group,
* reports ``IN=`` flags (``1`` when a source contributed this row,
  ``0`` otherwise),
* later sources win on shared column names.

.. code-block:: python

    reader = MergeReader(sources={"A": a_rows, "B": b_rows}, by=["id"],
                         in_flags={"A": "inA", "B": "inB"})

:class:`DatabaseReader` -- the SAS/ACCESS analogue
--------------------------------------------------

Wraps any PEP 249 cursor. See :doc:`20-03-database-sources-and-dialects` for
how dialect type maps shape the produced PDV declarations.

Custom readers
==============

A new input mode is a new :class:`Reader` subclass. Implement
:meth:`has_more` and :meth:`next_obs`. Optionally implement ``declarations()``
returning a list of declaration dicts; the engine will call it once during
construction and pre-declare the PDV. Readers may also be stateful (the
:class:`MergeReader` is) but the engine treats them uniformly: a reader is a
black box that produces one tuple at a time.

BY-group flags
==============

``first.`` / ``last.`` flags are computed by the engine using the
``cur_key`` and ``next_key`` produced by the reader. For nested BY variables
(``by=["region", "customer"]``):

* ``pdv.first["customer"]`` is True when the customer-portion of the current
  key differs from the previous row, *or* on the first observation overall;
* ``pdv.first["region"]`` is True when the region-portion differs;
* ``pdv.last["customer"]`` is True when the customer-portion of the *next*
  key differs (or there is no next row).

The engine is responsible for prefix matching across nesting levels. The
reader's only obligation is to return well-formed keys.

A note on sort order
====================

:class:`MergeReader` *requires* sorted input on the BY key, and the engine
trusts that input is sorted when computing ``first.``/``last.`` flags. SAS
fails loudly on out-of-order input; today the engine does not validate this
upfront. The future PROC SORT shim will close that gap. For now: sort at the
source -- in SQL via ``ORDER BY``, or before feeding rows in -- and your job
will match SAS.
