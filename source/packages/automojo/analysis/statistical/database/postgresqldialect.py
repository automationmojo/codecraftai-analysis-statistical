"""
    .. module:: postgresqldialect
        :synopsis: The :class:`PostgreSqlDialect` -- type map and name table
                   for PostgreSQL (psycopg type OIDs).

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from automojo.analysis.statistical.database.dialect import Dialect, NUMERIC_SENTINEL
from automojo.analysis.statistical.database.numericresolver import NumericResolver
from automojo.analysis.statistical.database.typemap import TypeMap
from automojo.analysis.statistical.types.constants import CHAR, NUM


_NUMERIC_RESOLVER = NumericResolver.from_description


class PostgreSqlDialect(Dialect):
    """
        PostgreSQL dialect. Read-path keys are psycopg type OIDs.
    """

    NAME = "postgresql"

    TYPE_MAP = TypeMap(entries={
        16:   (NUM, 8, None),
        21:   (NUM, 8, None),
        23:   (NUM, 8, None),
        20:   (NUM, 8, None),
        700:  (NUM, 8, None),
        701:  (NUM, 8, None),
        1700: _NUMERIC_RESOLVER,
        1043: (CHAR, None, None),
        25:   (CHAR, None, None),
        1082: (NUM, 8, "DATE9."),
        1114: (NUM, 8, "DATETIME19."),
    })

    NAME_TABLE = {
        "NUMERIC": (NUMERIC_SENTINEL, None),
        "DECIMAL": (NUMERIC_SENTINEL, None),
        "SMALLINT": (NUM, None),
        "INTEGER": (NUM, None),
        "INT": (NUM, None),
        "BIGINT": (NUM, None),
        "REAL": (NUM, None),
        "DOUBLE PRECISION": (NUM, None),
        "BOOLEAN": (NUM, None),
        "VARCHAR": (CHAR, None),
        "TEXT": (CHAR, None),
        "CHAR": (CHAR, None),
        "DATE": (NUM, "DATE9."),
        "TIMESTAMP": (NUM, "DATETIME19."),
    }
