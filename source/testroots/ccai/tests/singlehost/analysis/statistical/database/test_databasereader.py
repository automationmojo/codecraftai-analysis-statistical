"""
    Tests for :class:`DatabaseReader` and :class:`DialectDeclaration`. Covers:

    * end-to-end iteration over a real ``sqlite3`` cursor
    * postgres NUMERIC precision routing to num vs decimal
    * cross-dialect identical declarations for the same logical column
    * dialect-named declarations
    * unmappable types rejected at declare time
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


import sqlite3
from decimal import Decimal

from ccai.analysis.statistical.database.databasereader import DatabaseReader
from ccai.analysis.statistical.database.dialectdeclaration import DialectDeclaration
from ccai.analysis.statistical.database.mysqldialect import MySqlDialect
from ccai.analysis.statistical.database.postgresqldialect import PostgreSqlDialect
from ccai.analysis.statistical.database.sqlserverdialect import SqlServerDialect
from ccai.analysis.statistical.engine.observationengine import ObservationEngine
from ccai.analysis.statistical.readers.setreader import SetReader


class _FakeCursor:
    """
        Minimal PEP 249 cursor stand-in for tests. ``description`` is a list
        of 7-tuples and rows are pre-supplied.
    """

    def __init__(self, description: list, rows: list) -> None:
        """
            Initialize the fake cursor.

            :param description: A list of PEP 249 description tuples.
            :param rows: A list of row tuples to serve.

            :returns: ``None``
        """
        self.description = description
        self._rows = iter(rows)
        return

    def fetchmany(self, n: int) -> list:
        """
            Return up to ``n`` rows.

            :param n: The batch size.

            :returns: A list of rows.
        """
        out = []
        for _ in range(n):
            try:
                out.append(next(self._rows))
            except StopIteration:
                break
        return out


def test_sqlite_round_trip_emits_rows_in_order():
    """
        A real ``sqlite3`` query streams through :class:`DatabaseReader`.
    """
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        "CREATE TABLE t (k TEXT, v REAL);"
        "INSERT INTO t VALUES ('a', 1.0),('b', 2.0),('c', 3.0);"
    )
    cur = conn.cursor()
    cur.execute("SELECT k, v FROM t ORDER BY k")

    reader = DatabaseReader(cursor=cur)
    engine = ObservationEngine(reader=reader, logic=lambda p: None)
    out = list(engine)
    keys = [r["k"] for r in out]
    values = [r["v"] for r in out]
    conn.close()

    same_keys = keys == ["a", "b", "c"]
    same_values = values == [1.0, 2.0, 3.0]
    assert same_keys is True
    assert same_values is True
    return


def test_postgres_numeric_routes_low_precision_to_num():
    """
        ``NUMERIC(8,2)`` -> ``num``.
    """
    desc = [("small", 1700, None, None, 8, 2, True)]
    cursor = _FakeCursor(description=desc, rows=[])
    reader = DatabaseReader(cursor=cursor, dialect=PostgreSqlDialect.TYPE_MAP)
    decls = reader.declarations()
    same = decls[0]["stype"] == "num"
    assert same is True
    return


def test_postgres_numeric_routes_high_precision_to_decimal():
    """
        ``NUMERIC(38,2)`` -> ``decimal``.
    """
    desc = [("big", 1700, None, None, 38, 2, True)]
    cursor = _FakeCursor(description=desc, rows=[])
    reader = DatabaseReader(cursor=cursor, dialect=PostgreSqlDialect.TYPE_MAP)
    decls = reader.declarations()
    same = decls[0]["stype"] == "decimal"
    assert same is True
    return


def test_same_high_precision_column_resolves_identically_across_dialects():
    """
        The same logical column declared in three dialects yields identical
        declarations (storage mapping is dialect-agnostic).
    """
    pg = DatabaseReader(cursor=_FakeCursor(
        description=[("price", 1700, None, None, 38, 2, True)], rows=[]),
        dialect=PostgreSqlDialect.TYPE_MAP).declarations()
    my = DatabaseReader(cursor=_FakeCursor(
        description=[("price", 246, None, None, 38, 2, True)], rows=[]),
        dialect=MySqlDialect.TYPE_MAP).declarations()
    ms = DatabaseReader(cursor=_FakeCursor(
        description=[("price", Decimal, None, None, 38, 2, True)], rows=[]),
        dialect=SqlServerDialect.TYPE_MAP).declarations()

    same_one = pg == my
    same_two = my == ms
    assert same_one is True
    assert same_two is True
    return


def test_decimal_storage_preserves_high_precision_value():
    """
        A value beyond float64's safe range is preserved when routed through
        ``decimal``.
    """
    desc = [("big", 1700, None, None, 38, 2, True)]
    big = Decimal("12345678901234567890.12")
    cursor = _FakeCursor(description=desc, rows=[(big,)])
    reader = DatabaseReader(cursor=cursor, dialect=PostgreSqlDialect.TYPE_MAP)
    engine = ObservationEngine(reader=reader, logic=lambda p: None)
    rows = list(engine)
    same = rows[0]["big"] == big
    assert same is True
    return


def test_oracle_dialect_named_declaration_routes_to_canonical_types():
    """
        ``VARCHAR2(3)`` -> CHAR(3); ``NUMBER(38,2)`` -> decimal;
        ``DATE`` -> num + ``DATE9.`` format.
    """
    name_decl = DialectDeclaration.resolve(name="name",
                                           type_string="VARCHAR2(3)",
                                           dialect="oracle")
    salary_decl = DialectDeclaration.resolve(name="salary",
                                             type_string="NUMBER(38,2)",
                                             dialect="oracle")
    date_decl = DialectDeclaration.resolve(name="hired",
                                           type_string="DATE",
                                           dialect="oracle")
    name_ok = name_decl == {"name": "name", "stype": "char",
                            "length": 3, "fmt": None}
    salary_ok = salary_decl == {"name": "salary", "stype": "decimal",
                                "length": None, "fmt": None}
    date_ok = date_decl == {"name": "hired", "stype": "num",
                            "length": 8, "fmt": "DATE9."}
    assert name_ok is True
    assert salary_ok is True
    assert date_ok is True
    return


def test_oracle_named_declaration_truncates_char_at_declared_width():
    """
        Declaring ``VARCHAR2(3)`` truncates an assigned long string.
    """
    decls = [DialectDeclaration.resolve(name="name",
                                        type_string="VARCHAR2(3)",
                                        dialect="oracle")]
    reader = SetReader(source=[{"name": "HELLO"}])
    engine = ObservationEngine(reader=reader, logic=lambda p: None,
                               declare=decls)
    rows = list(engine)
    same = rows[0]["name"] == "HEL"
    assert same is True
    return


def test_unmappable_dialect_type_raises_value_error():
    """
        Postgres ``JSONB`` has no canonical engine home: declaration must
        raise :class:`ValueError`.
    """
    raised = False
    try:
        DialectDeclaration.resolve(name="doc", type_string="JSONB",
                                   dialect="postgresql")
    except ValueError:
        raised = True
    assert raised is True
    return


def test_unknown_dialect_raises_value_error():
    """
        An unregistered dialect name raises :class:`ValueError`.
    """
    raised = False
    try:
        DialectDeclaration.resolve(name="x", type_string="VARCHAR(10)",
                                   dialect="db2")
    except ValueError:
        raised = True
    assert raised is True
    return
