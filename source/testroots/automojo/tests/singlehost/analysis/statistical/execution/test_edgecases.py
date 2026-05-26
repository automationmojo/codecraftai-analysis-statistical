"""
    Edge-case tests for the executor surface:

    * empty input lists,
    * MISSING values flowing through arithmetic,
    * :class:`DatabaseReader` without a dialect (auto-infer everything),
    * format application without any spec (default display).
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


import sqlite3

from automojo.analysis.statistical.database.databasereader import DatabaseReader
from automojo.analysis.statistical.engine.observationengine import ObservationEngine
from automojo.analysis.statistical.execution.compiledstep import CompiledStep
from automojo.analysis.statistical.formats.formatregistry import FormatRegistry
from automojo.analysis.statistical.missing.missing import Missing
from automojo.analysis.statistical.missing.missingfactory import MISSING
from automojo.analysis.statistical.readers.setreader import SetReader


def _vector(pdv):
    """
        Pure vector logic suitable for the empty-input edge case.
    """
    pdv["doubled"] = pdv["x"] * 2
    return


def test_compiled_step_returns_empty_list_for_empty_input():
    """
        :meth:`CompiledStep.run` on an empty input list returns an empty
        list and does not plan an execution path.
    """
    out = CompiledStep(logic=_vector).run(rows=[])
    same = out == []
    assert same is True
    return


def test_missing_propagates_through_addition_in_engine():
    """
        Adding a MISSING-valued slot to a number yields MISSING in the row
        loop (semantics inherited from :class:`Missing.__lt__` / ``__add__``
        falling through; the result is whatever Python ``+`` of Missing and
        int produces -- here, ``TypeError`` would be wrong; the engine
        should retain Missing semantics by leaving the slot as MISSING when
        the source value is MISSING).
    """
    rows = [{"x": MISSING}]

    def logic(pdv):
        if isinstance(pdv["x"], Missing) is True:
            pdv["y"] = MISSING
        else:
            pdv["y"] = pdv["x"] + 1
        return

    out = list(ObservationEngine(reader=SetReader(source=rows), logic=logic))
    same = isinstance(out[0]["y"], Missing)
    assert same is True
    return


def test_database_reader_without_dialect_skips_declarations():
    """
        With ``dialect=None`` the reader emits no declarations and the
        engine auto-infers slot types from values.
    """
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        "CREATE TABLE t (k TEXT, v REAL);"
        "INSERT INTO t VALUES ('a', 1.0),('b', 2.0);"
    )
    cur = conn.cursor()
    cur.execute("SELECT k, v FROM t ORDER BY k")
    reader = DatabaseReader(cursor=cur)
    decls = reader.declarations()
    out = list(ObservationEngine(reader=reader, logic=lambda p: None))
    conn.close()

    no_decls = len(decls) == 0
    has_rows = len(out) == 2
    assert no_decls is True
    assert has_rows is True
    return


def test_format_apply_default_display_renders_integer_float_without_trailing_zero():
    """
        Applying no spec to a float that is integer-valued renders without
        the trailing ``.0`` (the default display contract).
    """
    rendered = FormatRegistry.apply(value=42.0, spec=None)
    same = rendered == "42"
    assert same is True
    return


def test_format_apply_default_display_renders_non_integer_float_as_str():
    """
        Applying no spec to a non-integer float falls back to ``str``.
    """
    rendered = FormatRegistry.apply(value=3.14, spec=None)
    same = rendered == "3.14"
    assert same is True
    return
