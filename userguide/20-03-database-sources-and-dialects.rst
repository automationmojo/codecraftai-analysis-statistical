.. _20-03-database-sources-and-dialects:

================================
Database Sources and Dialects
================================

A relational source is a **reader**, not an engine change. The engine never
learns about your database; it just consumes the same ``(row, in_flags,
cur_key, next_key)`` tuple a :class:`DatabaseReader` produces from any PEP 249
cursor.

The shape of a dialect
======================

What differs between databases is exactly one thing: a mapping from the
driver's column **type code** to an engine ``(stype, length, fmt)`` triple.
Drivers don't agree on what a "type code" even is:

* psycopg uses integer OIDs (``1700`` is ``NUMERIC``);
* PyMySQL uses ``FIELD_TYPE`` integers (``246`` is ``NEWDECIMAL``);
* oracledb uses ``DbType`` objects (``DB_TYPE_NUMBER``);
* pyodbc uses Python type objects (``decimal.Decimal``).

The :class:`TypeMap` shape is identical across all of them. Each shipped
dialect is a :class:`Dialect` subclass that exposes:

* ``TYPE_MAP`` -- the read-path ``{type_code: triple_or_callable}``;
* ``NAME_TABLE`` -- the dialect-named declaration table.

Precision routing
=================

``NUMERIC``, ``NUMBER``, ``DECIMAL``, and ``MONEY`` columns route through
:class:`NumericResolver`. The rule is simple: if the declared precision
exceeds float64's safe range (~15-16 digits) the column is stored as
``decimal`` rather than ``num``. ``NUMBER(38,2)`` becomes a
:class:`decimal.Decimal` slot; ``NUMERIC(8,2)`` stays float64.

This is the only place where a clean-room storage type is introduced. The
``decimal`` type is opt-in (the database subpackage registers its
:class:`TypeHandler` on import) and is never inferred from a value.

.. warning::

    The engine guarantees *storage* fidelity for high-precision values, not
    *arithmetic* fidelity. If your logic mixes ``Decimal`` and ``float``, the
    result depends on Python's arithmetic rules. Keep computation in one
    family.

Dialect-named declarations
==========================

Sometimes you want to declare a slot in your database's own terms without
opening a cursor first. :class:`DialectDeclaration` accepts a dialect type
string and resolves it to a declaration dict:

.. code-block:: python

    from ccai.analysis.statistical import dialect_declare

    decls = [
        dialect_declare(name="name",   type_string="VARCHAR2(3)",   dialect="oracle"),
        dialect_declare(name="salary", type_string="NUMBER(38,2)",  dialect="oracle"),
        dialect_declare(name="hired",  type_string="DATE",          dialect="oracle"),
    ]
    engine = ObservationEngine(reader=..., logic=..., declare=decls)

The promise is a *storage mapping only* -- never the dialect's runtime
semantics (rounding, fixed scale, collation). Unmappable type names raise
:class:`ValueError` at declaration time, so a typo or unsupported type
fails loud rather than silently mangling the data downstream.

Rejected (deliberately)
=======================

Some driver type codes have no canonical num/char/decimal home: JSON columns,
arrays, UUIDs, blobs. The shipped :class:`TypeMap` entries for these are
absent on purpose. ``DialectDeclaration`` for the same canonical names
**raises** so a build that depends on routing them must make an explicit
policy choice:

* stringify to ``char``,
* register a custom :class:`TypeHandler` for that storage type,
* reject and drop the column in SQL.

A silent default would be the wrong answer for clinical/financial data; a
loud rejection is the right one.

Push work into SQL
==================

The reader streams via ``fetchmany`` so memory stays bounded, but query
planning is the database's job. Always:

* push ``ORDER BY`` into the SQL -- :class:`MergeReader` requires sorted
  input, and the database sorts faster;
* push ``WHERE`` filters into the SQL -- you'll move fewer rows;
* be careful with cross-database merges -- collation rules don't survive
  the wire crossing, so two NVARCHAR columns from different vendors may
  compare differently than they would in either source.

NULL in SQL maps cleanly to MISSING in the PDV. SQL three-valued logic does
not survive the crossing; once you're in the engine, missing values follow
the SAS ordering documented in :doc:`20-01-engine-core-and-pdv`.
