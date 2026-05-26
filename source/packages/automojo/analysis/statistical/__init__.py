"""
    automojo.analysis.statistical -- patterns for authoring and porting
    statistical analysis jobs to Python with SAS-comparable results.

    Importing this module bootstraps the storage-type registry, the format /
    informat registries, and the ``decimal`` storage type. The names exposed
    here form the supported public surface; everything else is internal.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


import automojo.analysis.statistical.engine  # noqa: F401  (bootstrap chain)
import automojo.analysis.statistical.database  # noqa: F401  (decimal type)

from automojo.analysis.statistical.columnar.columnarstep import ColumnarStep
from automojo.analysis.statistical.columnar.columnframe import ColumnFrame
from automojo.analysis.statistical.database.databasereader import DatabaseReader
from automojo.analysis.statistical.database.dialectdeclaration import (
    DialectDeclaration, dialect_declare)
from automojo.analysis.statistical.database.mysqldialect import MySqlDialect
from automojo.analysis.statistical.database.oracledialect import OracleDialect
from automojo.analysis.statistical.database.postgresqldialect import PostgreSqlDialect
from automojo.analysis.statistical.database.sqlserverdialect import SqlServerDialect
from automojo.analysis.statistical.engine.observationengine import ObservationEngine
from automojo.analysis.statistical.engine.phase import Phase
from automojo.analysis.statistical.execution.compiledstep import CompiledStep
from automojo.analysis.statistical.formats.formatregistry import (
    FormatRegistry, format_value, register_format)
from automojo.analysis.statistical.formats.informatregistry import (
    InformatRegistry, input_value, register_informat)
from automojo.analysis.statistical.ir.logiccompiler import (
    LogicCompiler, compile_logic)
from automojo.analysis.statistical.ir.unsupportederror import UnsupportedError
from automojo.analysis.statistical.missing.missing import Missing
from automojo.analysis.statistical.missing.missingfactory import MISSING, missing
from automojo.analysis.statistical.readers.mergereader import MergeReader
from automojo.analysis.statistical.readers.reader import Reader
from automojo.analysis.statistical.readers.setreader import SetReader
from automojo.analysis.statistical.report.reportbuilder import (
    ReportBuilder, report)
from automojo.analysis.statistical.types.constants import CHAR, DECIMAL, NUM
from automojo.analysis.statistical.types.typehandler import TypeHandler
from automojo.analysis.statistical.types.typeregistry import (
    TypeRegistry, register_type)


__all__ = [
    "CHAR",
    "ColumnFrame",
    "ColumnarStep",
    "CompiledStep",
    "DECIMAL",
    "DatabaseReader",
    "DialectDeclaration",
    "FormatRegistry",
    "InformatRegistry",
    "LogicCompiler",
    "MISSING",
    "MergeReader",
    "Missing",
    "MySqlDialect",
    "NUM",
    "ObservationEngine",
    "OracleDialect",
    "Phase",
    "PostgreSqlDialect",
    "Reader",
    "ReportBuilder",
    "SetReader",
    "SqlServerDialect",
    "TypeHandler",
    "TypeRegistry",
    "UnsupportedError",
    "compile_logic",
    "dialect_declare",
    "format_value",
    "input_value",
    "missing",
    "register_format",
    "register_informat",
    "register_type",
    "report",
]
