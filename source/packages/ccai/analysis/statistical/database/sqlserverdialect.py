"""
    .. module:: sqlserverdialect
        :synopsis: The :class:`SqlServerDialect` -- type map and name table
                   for SQL Server (pyodbc reports Python *types* as the
                   type code).

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


import datetime
from decimal import Decimal

from ccai.analysis.statistical.database.dialect import Dialect, NUMERIC_SENTINEL
from ccai.analysis.statistical.database.numericresolver import NumericResolver
from ccai.analysis.statistical.database.typemap import TypeMap
from ccai.analysis.statistical.types.constants import CHAR, NUM


_NUMERIC_RESOLVER = NumericResolver.from_description


class SqlServerDialect(Dialect):
    """
        SQL Server dialect. Read-path keys are Python *type objects*
        (``int``, ``Decimal``, ``str``, ``datetime.date``, ...).
    """

    NAME = "sqlserver"

    TYPE_MAP = TypeMap(entries={
        int:               (NUM, 8, None),
        float:             (NUM, 8, None),
        bool:              (NUM, 8, None),
        Decimal:           _NUMERIC_RESOLVER,
        str:               (CHAR, None, None),
        datetime.date:     (NUM, 8, "DATE9."),
        datetime.datetime: (NUM, 8, "DATETIME19."),
    })

    NAME_TABLE = {
        "DECIMAL": (NUMERIC_SENTINEL, None),
        "NUMERIC": (NUMERIC_SENTINEL, None),
        "MONEY": (NUMERIC_SENTINEL, None),
        "INT": (NUM, None),
        "BIGINT": (NUM, None),
        "SMALLINT": (NUM, None),
        "BIT": (NUM, None),
        "FLOAT": (NUM, None),
        "REAL": (NUM, None),
        "VARCHAR": (CHAR, None),
        "NVARCHAR": (CHAR, None),
        "CHAR": (CHAR, None),
        "DATE": (NUM, "DATE9."),
        "DATETIME2": (NUM, "DATETIME19."),
    }
