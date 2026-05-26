"""
    .. module:: oracledialect
        :synopsis: The :class:`OracleDialect` -- type map (keyed by DbType
                   *name strings*, since the oracledb module may not be
                   importable at design time) and name table for Oracle.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from automojo.analysis.statistical.database.dialect import Dialect, NUMERIC_SENTINEL
from automojo.analysis.statistical.database.numericresolver import NumericResolver
from automojo.analysis.statistical.database.typemap import TypeMap
from automojo.analysis.statistical.types.constants import CHAR, NUM


_NUMERIC_RESOLVER = NumericResolver.from_description


class OracleDialect(Dialect):
    """
        Oracle dialect. Read-path keys are DbType object *name strings* (for
        example ``"DB_TYPE_NUMBER"``). At runtime the caller binds the real
        ``oracledb`` singletons by building a derivative
        :class:`TypeMap`.
    """

    NAME = "oracle"

    TYPE_MAP = TypeMap(entries={
        "DB_TYPE_NUMBER":         _NUMERIC_RESOLVER,
        "DB_TYPE_BINARY_DOUBLE":  (NUM, 8, None),
        "DB_TYPE_BINARY_FLOAT":   (NUM, 8, None),
        "DB_TYPE_VARCHAR":        (CHAR, None, None),
        "DB_TYPE_CHAR":           (CHAR, None, None),
        "DB_TYPE_NVARCHAR":       (CHAR, None, None),
        "DB_TYPE_DATE":           (NUM, 8, "DATE9."),
        "DB_TYPE_TIMESTAMP":      (NUM, 8, "DATETIME19."),
    })

    NAME_TABLE = {
        "NUMBER": (NUMERIC_SENTINEL, None),
        "BINARY_DOUBLE": (NUM, None),
        "BINARY_FLOAT": (NUM, None),
        "FLOAT": (NUMERIC_SENTINEL, None),
        "VARCHAR2": (CHAR, None),
        "NVARCHAR2": (CHAR, None),
        "CHAR": (CHAR, None),
        "CLOB": (CHAR, None),
        "DATE": (NUM, "DATE9."),
        "TIMESTAMP": (NUM, "DATETIME19."),
    }
