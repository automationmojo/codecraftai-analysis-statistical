"""
    .. module:: dialectdeclaration
        :synopsis: The :class:`DialectDeclaration` helper -- resolves a
                   dialect-named type string (for example
                   ``("salary", "NUMBER(38,2)", "oracle")``) to an engine
                   declaration dictionary.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


import os
import re

from automojo.analysis.statistical.database.dialect import NUMERIC_SENTINEL
from automojo.analysis.statistical.database.mysqldialect import MySqlDialect
from automojo.analysis.statistical.database.numericresolver import NumericResolver
from automojo.analysis.statistical.database.oracledialect import OracleDialect
from automojo.analysis.statistical.database.postgresqldialect import PostgreSqlDialect
from automojo.analysis.statistical.database.sqlserverdialect import SqlServerDialect
from automojo.analysis.statistical.types.constants import CHAR, NUM


class DialectDeclaration:
    """
        Resolve a dialect-named type string to an engine declaration dict.

        Promises a *storage* mapping only -- never the dialect's runtime
        semantics (rounding, fixed scale, collation). Unmappable type names
        raise :class:`ValueError` at the point of declaration, so a typo or an
        unsupported type fails loud rather than silently mangling data.
    """

    DIALECTS: dict = {
        "oracle": OracleDialect,
        "postgresql": PostgreSqlDialect,
        "mysql": MySqlDialect,
        "sqlserver": SqlServerDialect,
    }

    _PATTERN = re.compile(r"^\s*([A-Za-z0-9_ ]+?)\s*(?:\(\s*(\d+)\s*(?:,\s*(\d+)\s*)?\))?\s*$")

    @classmethod
    def resolve(cls, name: str, type_string: str, dialect: str) -> dict:
        """
            Resolve a dialect type string to an engine declaration dict.

            :param name: The PDV variable name to declare.
            :param type_string: A dialect type string (for example
                                ``"NUMBER(38,2)"``).
            :param dialect: A registered dialect name (one of
                            ``oracle``, ``postgresql``, ``mysql``,
                            ``sqlserver``).

            :returns: A declaration dictionary compatible with
                      :meth:`RecordFrame.declare`.

            :raises ValueError: When the dialect is unknown, the type string
                                is unparseable, or the type has no canonical
                                num/char/decimal home.
        """
        dialect_cls = cls.DIALECTS.get(dialect)
        if dialect_cls is None:
            err_msg_lines = [
                "Unknown dialect requested for declaration.",
                "    dialect: {}".format(dialect),
                "    known:   {}".format(sorted(cls.DIALECTS.keys())),
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise ValueError(err_msg)

        match = cls._PATTERN.match(type_string)
        if match is None:
            err_msg_lines = [
                "Unable to parse dialect type string.",
                "    name:    {}".format(name),
                "    type:    {}".format(type_string),
                "    dialect: {}".format(dialect),
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise ValueError(err_msg)

        canonical_type = match.group(1).upper()
        raw_precision = match.group(2)
        if raw_precision is None:
            precision: int | None = None
        else:
            precision = int(raw_precision)

        resolved = dialect_cls.resolve_named(type_name=canonical_type)
        if resolved is None:
            err_msg_lines = [
                "Dialect type has no canonical engine mapping.",
                "    name:    {}".format(name),
                "    type:    {}".format(canonical_type),
                "    dialect: {}".format(dialect),
                "    hint:    stringify, register a custom type, or reject.",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise ValueError(err_msg)

        kind, fmt = resolved

        if kind == NUMERIC_SENTINEL:
            stype, length, _ = NumericResolver.resolve(precision=precision)
            rtnval = {"name": name, "stype": stype, "length": length, "fmt": fmt}
        elif kind == CHAR:
            rtnval = {"name": name, "stype": CHAR, "length": precision, "fmt": fmt}
        else:
            rtnval = {"name": name, "stype": NUM, "length": 8, "fmt": fmt}
        return rtnval


def dialect_declare(name: str, type_string: str, dialect: str) -> dict:
    """
        Convenience function that delegates to :meth:`DialectDeclaration.resolve`.

        :param name: The PDV variable name.
        :param type_string: A dialect type string.
        :param dialect: A registered dialect name.

        :returns: A declaration dictionary.
    """
    rtnval = DialectDeclaration.resolve(name=name, type_string=type_string,
                                        dialect=dialect)
    return rtnval
