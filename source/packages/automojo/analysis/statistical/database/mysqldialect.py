"""
    .. module:: mysqldialect
        :synopsis: The :class:`MySqlDialect` -- type map and name table for
                   MySQL (PyMySQL FIELD_TYPE codes).

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from automojo.analysis.statistical.database.dialect import Dialect, NUMERIC_SENTINEL
from automojo.analysis.statistical.database.numericresolver import NumericResolver
from automojo.analysis.statistical.database.typemap import TypeMap
from automojo.analysis.statistical.types.constants import CHAR, NUM


_NUMERIC_RESOLVER = NumericResolver.from_description


class MySqlDialect(Dialect):
    """
        MySQL dialect. Read-path keys are PyMySQL FIELD_TYPE integers.
    """

    NAME = "mysql"

    TYPE_MAP = TypeMap(entries={
        0:   _NUMERIC_RESOLVER,
        246: _NUMERIC_RESOLVER,
        1:   (NUM, 8, None),
        2:   (NUM, 8, None),
        3:   (NUM, 8, None),
        8:   (NUM, 8, None),
        4:   (NUM, 8, None),
        5:   (NUM, 8, None),
        10:  (NUM, 8, "DATE9."),
        12:  (NUM, 8, "DATETIME19."),
        7:   (NUM, 8, "DATETIME19."),
        15:  (CHAR, None, None),
        253: (CHAR, None, None),
        254: (CHAR, None, None),
    })

    NAME_TABLE = {
        "DECIMAL": (NUMERIC_SENTINEL, None),
        "TINYINT": (NUM, None),
        "SMALLINT": (NUM, None),
        "INT": (NUM, None),
        "BIGINT": (NUM, None),
        "FLOAT": (NUM, None),
        "DOUBLE": (NUM, None),
        "VARCHAR": (CHAR, None),
        "TEXT": (CHAR, None),
        "CHAR": (CHAR, None),
        "DATE": (NUM, "DATE9."),
        "DATETIME": (NUM, "DATETIME19."),
    }
