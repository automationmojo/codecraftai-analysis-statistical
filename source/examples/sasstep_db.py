"""
sasstep_db -- database source readers (the SAS/ACCESS-engine analogue).

A relational source is a READER, not a change to the engine or type system.
Each RDBMS contributes exactly ONE thing that differs: a type-mapping table from
the driver's column type codes to the engine's (type, length, format). Everything
else is shared.

Note the heterogeneity the maps below absorb: the four drivers don't agree on
what a "type code" even is --
    psycopg  : integer OIDs            (e.g. 1700 = numeric)
    PyMySQL  : FIELD_TYPE ints         (e.g. 246  = newdecimal)
    oracledb : DbType objects          (e.g. DB_TYPE_NUMBER)
    pyodbc   : Python type objects     (e.g. decimal.Decimal)
...but the map *shape* is identical: {type_code: (type, length, format)} or a
callable(description_entry) -> (type, length, format) when precision matters.

Works against any PEP 249 (DB-API 2.0) driver.
"""
from __future__ import annotations
from decimal import Decimal
from typing import Optional

from sasstep import (SetReader, ObservationEngine, TypeHandler, register_type,
                     NUM, CHAR, MISSING, Missing)


# ---------------------------------------------------------------------------
# A clean-room DECIMAL storage type, registered for precision that float64 can't
# hold exactly (Oracle NUMBER(38), Postgres NUMERIC, etc.). This is the custom-
# type hook from the core being used for real: the engine core stays num+char;
# the DB layer opts into decimal where correctness demands it.
# ---------------------------------------------------------------------------
DECIMAL = "decimal"

def _coerce_decimal(value, length):
    if isinstance(value, Missing):
        return value
    try:
        return value if isinstance(value, Decimal) else Decimal(str(value))
    except Exception:
        return MISSING

register_type(TypeHandler(DECIMAL, _coerce_decimal, MISSING, 16))

# float64 holds ~15-16 significant digits exactly; beyond that, prefer DECIMAL.
_FLOAT64_SAFE_DIGITS = 15

def _resolve_numeric(precision):
    """num vs decimal by precision -- shared by the read path and declare path."""
    if precision is not None and precision > _FLOAT64_SAFE_DIGITS:
        return (DECIMAL, None, None)
    return (NUM, 8, None)

def _numeric_by_precision(desc_entry):
    """Read-path resolver for NUMERIC/NUMBER columns (keyed by driver type_code)."""
    return _resolve_numeric(desc_entry[4])         # description: (.,.,.,.,prec,scale,.)


# ---------------------------------------------------------------------------
# Per-dialect type maps. Each value is (type, length, format) or a callable.
# Dates/datetimes -> NUM + a format (faithful: a SAS date is a number).
# Commented rows have NO num/char home -> a deliberate policy decision per build:
#   stringify to CHAR | register a custom type | reject at declare time.
# ---------------------------------------------------------------------------
# PostgreSQL -- psycopg type OIDs
POSTGRESQL = {
    16:   (NUM, 8, None),           # bool
    21:   (NUM, 8, None),           # int2
    23:   (NUM, 8, None),           # int4
    20:   (NUM, 8, None),           # int8
    700:  (NUM, 8, None),           # float4
    701:  (NUM, 8, None),           # float8
    1700: _numeric_by_precision,    # numeric  -> num or decimal by precision
    1043: (CHAR, None, None),       # varchar  (length from internal_size)
    25:   (CHAR, None, None),       # text
    1082: (NUM, 8, "DATE9."),       # date
    1114: (NUM, 8, "DATETIME19."),  # timestamp
    # 3802 jsonb | 1007 int4[] | 2950 uuid : no num/char home -> policy
}

# MySQL -- PyMySQL FIELD_TYPE codes
MYSQL = {
    0:   _numeric_by_precision,     # DECIMAL
    246: _numeric_by_precision,     # NEWDECIMAL
    1:   (NUM, 8, None),            # TINY  (TINY(1) often boolean)
    2:   (NUM, 8, None),            # SHORT
    3:   (NUM, 8, None),            # LONG
    8:   (NUM, 8, None),            # LONGLONG
    4:   (NUM, 8, None),            # FLOAT
    5:   (NUM, 8, None),            # DOUBLE
    10:  (NUM, 8, "DATE9."),        # DATE
    12:  (NUM, 8, "DATETIME19."),   # DATETIME
    7:   (NUM, 8, "DATETIME19."),   # TIMESTAMP
    15:  (CHAR, None, None),        # VARCHAR
    253: (CHAR, None, None),        # VAR_STRING
    254: (CHAR, None, None),        # STRING
    # 252 BLOB/TEXT family : CHAR if text, policy if binary
}

# Oracle -- oracledb DbType objects. Keys are the DbType singletons; shown by
# name here since the driver isn't importable in this sandbox. At runtime:
#   import oracledb
#   ORACLE = {oracledb.DB_TYPE_NUMBER: _numeric_by_precision, ...}
ORACLE_BY_NAME = {
    "DB_TYPE_NUMBER":    _numeric_by_precision,
    "DB_TYPE_BINARY_DOUBLE": (NUM, 8, None),
    "DB_TYPE_BINARY_FLOAT":  (NUM, 8, None),
    "DB_TYPE_VARCHAR":   (CHAR, None, None),
    "DB_TYPE_CHAR":      (CHAR, None, None),
    "DB_TYPE_NVARCHAR":  (CHAR, None, None),
    "DB_TYPE_DATE":      (NUM, 8, "DATE9."),
    "DB_TYPE_TIMESTAMP": (NUM, 8, "DATETIME19."),
    # DB_TYPE_CLOB -> CHAR (stream); DB_TYPE_BLOB / DB_TYPE_JSON -> policy
}

# SQL Server -- pyodbc reports Python *types* as the type code
import datetime as _dt
SQLSERVER = {
    int:           (NUM, 8, None),
    float:         (NUM, 8, None),
    bool:          (NUM, 8, None),            # BIT
    Decimal:       _numeric_by_precision,     # DECIMAL / NUMERIC / MONEY
    str:           (CHAR, None, None),        # VARCHAR / NVARCHAR
    _dt.date:      (NUM, 8, "DATE9."),
    _dt.datetime:  (NUM, 8, "DATETIME19."),
    # bytes (VARBINARY) | uuid.UUID (UNIQUEIDENTIFIER) -> policy / CHAR(36)
}

DIALECTS = {"postgresql": POSTGRESQL, "mysql": MYSQL,
            "oracle_by_name": ORACLE_BY_NAME, "sqlserver": SQLSERVER}


# ---------------------------------------------------------------------------
# Dialect-NAMED declaration (clean-room convenience; SAS itself discards dialect).
# Lets a user write declarations in their database's terms -- "NUMBER(38,2)",
# "VARCHAR2(30)", "DATE" -- which RESOLVE to the engine's canonical types. This
# promises a storage mapping ONLY, never the dialect's runtime semantics.
#
# Each dialect is defined once by canonical type name. "numeric" is a sentinel
# meaning "route by precision" (reusing _resolve_numeric, the same logic the
# read path uses) so the two paths can't drift.
# ---------------------------------------------------------------------------
import re as _re

_NUMERIC = "numeric"   # sentinel: precision-routed

NAME_TABLES = {
    "oracle": {
        "NUMBER": (_NUMERIC, None), "BINARY_DOUBLE": (NUM, None),
        "BINARY_FLOAT": (NUM, None), "FLOAT": (_NUMERIC, None),
        "VARCHAR2": (CHAR, None), "NVARCHAR2": (CHAR, None), "CHAR": (CHAR, None),
        "CLOB": (CHAR, None), "DATE": (NUM, "DATE9."), "TIMESTAMP": (NUM, "DATETIME19."),
    },
    "postgresql": {
        "NUMERIC": (_NUMERIC, None), "DECIMAL": (_NUMERIC, None),
        "SMALLINT": (NUM, None), "INTEGER": (NUM, None), "INT": (NUM, None),
        "BIGINT": (NUM, None), "REAL": (NUM, None), "DOUBLE PRECISION": (NUM, None),
        "BOOLEAN": (NUM, None), "VARCHAR": (CHAR, None), "TEXT": (CHAR, None),
        "CHAR": (CHAR, None), "DATE": (NUM, "DATE9."), "TIMESTAMP": (NUM, "DATETIME19."),
    },
    "mysql": {
        "DECIMAL": (_NUMERIC, None), "TINYINT": (NUM, None), "SMALLINT": (NUM, None),
        "INT": (NUM, None), "BIGINT": (NUM, None), "FLOAT": (NUM, None),
        "DOUBLE": (NUM, None), "VARCHAR": (CHAR, None), "TEXT": (CHAR, None),
        "CHAR": (CHAR, None), "DATE": (NUM, "DATE9."), "DATETIME": (NUM, "DATETIME19."),
    },
    "sqlserver": {
        "DECIMAL": (_NUMERIC, None), "NUMERIC": (_NUMERIC, None), "MONEY": (_NUMERIC, None),
        "INT": (NUM, None), "BIGINT": (NUM, None), "SMALLINT": (NUM, None),
        "BIT": (NUM, None), "FLOAT": (NUM, None), "REAL": (NUM, None),
        "VARCHAR": (CHAR, None), "NVARCHAR": (CHAR, None), "CHAR": (CHAR, None),
        "DATE": (NUM, "DATE9."), "DATETIME2": (NUM, "DATETIME19."),
    },
}

_TYPESTR = _re.compile(r"^\s*([A-Za-z0-9_ ]+?)\s*(?:\(\s*(\d+)\s*(?:,\s*(\d+)\s*)?\))?\s*$")

def dialect_declare(name, type_string, dialect):
    """
    'salary', 'NUMBER(38,2)', 'oracle' -> declare-dict for the engine.
    Resolves a dialect type string to a canonical (stype, length, fmt). Raises on
    a type with no num/char/decimal home -- so unmappable types fail loud here
    rather than silently mangling.
    """
    table = NAME_TABLES.get(dialect)
    if table is None:
        raise ValueError(f"unknown dialect {dialect!r}")
    m = _TYPESTR.match(type_string)
    if not m:
        raise ValueError(f"unparseable type {type_string!r}")
    tname = m.group(1).upper()
    p1 = int(m.group(2)) if m.group(2) else None     # precision or char length
    entry = table.get(tname)
    if entry is None:
        raise ValueError(f"{tname!r} has no canonical mapping in {dialect!r} "
                         f"(stringify, register a custom type, or reject)")
    kind, fmt = entry
    if kind == _NUMERIC:
        stype, length, _ = _resolve_numeric(p1)
        return {"name": name, "stype": stype, "length": length, "fmt": fmt}
    if kind == CHAR:
        return {"name": name, "stype": CHAR, "length": p1, "fmt": fmt}
    return {"name": name, "stype": NUM, "length": 8, "fmt": fmt}


# ---------------------------------------------------------------------------
def _cursor_rows(cursor, arraysize: int = 500):
    """Lazily stream a cursor as dict rows -- never loads the whole table."""
    cols = [d[0] for d in cursor.description]
    while True:
        batch = cursor.fetchmany(arraysize)
        if not batch:
            break
        for row in batch:
            yield dict(zip(cols, row))


class DatabaseReader(SetReader):
    """
    Wraps an already-executed DB-API cursor. Push ORDER BY / WHERE into the SQL
    (the database sorts and filters better, and MergeReader REQUIRES sorted
    input). Streams rows and declares typed slots from cursor.description + the
    dialect map. Unmapped type codes are skipped -> the engine auto-infers.
    """
    def __init__(self, cursor, by=None, dialect: Optional[dict] = None,
                 char_default_len: int = 200):
        self._cursor = cursor
        self._dialect = dialect or {}
        self._char_default = char_default_len
        super().__init__(_cursor_rows(cursor), by=by)

    def declarations(self):
        decls = []
        for d in self._cursor.description:
            name, type_code, internal_size = d[0], d[1], d[3]
            mapped = self._dialect.get(type_code)
            if callable(mapped):                   # precision-aware resolver
                mapped = mapped(d)
            if mapped is None:                     # unknown / sqlite -> auto-infer
                continue
            stype, length, fmt = mapped
            if stype == CHAR and length is None:
                length = internal_size if internal_size and internal_size > 0 \
                    else self._char_default
            decls.append({"name": name, "stype": stype,
                          "length": length, "fmt": fmt})
        return decls


if __name__ == "__main__":
    class FakeCursor:
        """Stands in for a real driver cursor to exercise declarations()."""
        def __init__(self, description, rows):
            self.description = description; self._rows = iter(rows)
        def fetchmany(self, n):
            out = []
            for _ in range(n):
                try: out.append(next(self._rows))
                except StopIteration: break
            return out

    # ---- (A) real DB-API end-to-end via sqlite3 ----------------------------
    import sqlite3
    conn = sqlite3.connect(":memory:")
    conn.executescript("""
        CREATE TABLE sales (region TEXT, customer TEXT, amount REAL);
        INSERT INTO sales VALUES ('East','A',10),('East','A',15),
            ('East','B',7),('West','C',20),('West','C',5);
    """)
    cur = conn.cursor()
    cur.execute("SELECT region, customer, amount FROM sales "
                "ORDER BY region, customer")
    def accumulate(p):
        if p.first["customer"]: p["total"] = 0
        p["total"] = p["total"] + p["amount"]
        if p.last["customer"]: p.output()
    print("# sqlite3 -> by-group accumulate")
    for r in ObservationEngine(DatabaseReader(cur, by=["region", "customer"]),
                               accumulate, by=["region", "customer"],
                               retain={"total": 0}):
        print("  ", r)
    conn.close()

    # ---- (B) precision routing: NUMERIC(8,2) -> num, NUMERIC(38,2) -> decimal
    desc = [("small_amt", 1700, None, None, 8,  2, True),    # -> NUM (float64)
            ("big_amt",   1700, None, None, 38, 2, True)]    # -> DECIMAL (exact)
    big = Decimal("12345678901234567890.12")                 # 22 digits
    reader = DatabaseReader(FakeCursor(desc, [(99.5, big)]),
                            dialect=DIALECTS["postgresql"])
    print("\n# postgres NUMERIC precision routing")
    print("  declarations:", reader.declarations())
    for r in ObservationEngine(reader, lambda p: None):
        print("  small_amt:", r["small_amt"], "(float64)")
        print("  big_amt:  ", r["big_amt"], "(exact Decimal)")
        print("  if it had gone to num (float64):", float(big), "<- precision lost")

    # ---- (C) same schema, MySQL + SQL Server dialects produce identical decls
    pg = DatabaseReader(FakeCursor(
        [("price", 1700, None, None, 38, 2, True)], []),
        dialect=DIALECTS["postgresql"]).declarations()
    my = DatabaseReader(FakeCursor(
        [("price", 246, None, None, 38, 2, True)], []),
        dialect=DIALECTS["mysql"]).declarations()
    ms = DatabaseReader(FakeCursor(
        [("price", Decimal, None, None, 38, 2, True)], []),
        dialect=DIALECTS["sqlserver"]).declarations()
    print("\n# same high-precision column, three dialects, one result")
    print("  postgres:", pg)
    print("  mysql:   ", my)
    print("  sqlserver:", ms)

    # ---- (D) dialect-NAMED declaration -> canonical types, end to end -------
    from sasstep import SetReader
    decls = [dialect_declare("name", "VARCHAR2(3)", "oracle"),     # -> CHAR(3)
             dialect_declare("salary", "NUMBER(38,2)", "oracle"),  # -> decimal (38>15)
             dialect_declare("hired", "DATE", "oracle")]           # -> NUM + DATE9.
    print("\n# user declares in Oracle terms; engine resolves to canonical types")
    for d in decls:
        print("  ", d)
    rows = [{"name": "HELLO", "salary": Decimal("12345678901234567890.12"), "hired": 0}]
    def fmt_hired(p): p["start"] = p.put("hired")
    for r in ObservationEngine(SetReader(rows), fmt_hired, declare=decls):
        print("  ->", r)

    # same column declared in Postgres terms at low precision stays float64
    print("\n# NUMERIC(8,2) (postgres) vs NUMBER(38,2) (oracle)")
    print("  ", dialect_declare("p", "NUMERIC(8,2)", "postgresql"), "<- num")
    print("  ", dialect_declare("p", "NUMBER(38,2)", "oracle"), "<- decimal")

    # an unmappable type fails loud, not silently
    try:
        dialect_declare("doc", "JSONB", "postgresql")
    except ValueError as e:
        print("\n# unmappable type rejected:", e)
