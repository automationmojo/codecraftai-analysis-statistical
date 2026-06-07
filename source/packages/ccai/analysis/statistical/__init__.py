"""
    ccai.analysis.statistical -- patterns for authoring and porting
    statistical analysis jobs to Python with SAS-comparable results.

    Importing this module bootstraps the storage-type registry, the format /
    informat registries, and the ``decimal`` storage type. The names exposed
    here form the supported public surface; everything else is internal.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


import ccai.analysis.statistical.engine  # noqa: F401  (bootstrap chain)
import ccai.analysis.statistical.database  # noqa: F401  (decimal type)

from ccai.analysis.statistical.columnar.columnarstep import ColumnarStep
from ccai.analysis.statistical.columnar.columnframe import ColumnFrame
from ccai.analysis.statistical.database.databasereader import DatabaseReader
from ccai.analysis.statistical.database.dialectdeclaration import (
    DialectDeclaration, dialect_declare)
from ccai.analysis.statistical.database.mysqldialect import MySqlDialect
from ccai.analysis.statistical.database.oracledialect import OracleDialect
from ccai.analysis.statistical.database.postgresqldialect import PostgreSqlDialect
from ccai.analysis.statistical.database.sqlserverdialect import SqlServerDialect
from ccai.analysis.statistical.engine.observationengine import ObservationEngine
from ccai.analysis.statistical.engine.phase import Phase
from ccai.analysis.statistical.execution.compiledstep import CompiledStep
from ccai.analysis.statistical.formats.formatregistry import (
    FormatRegistry, format_value, register_format)
from ccai.analysis.statistical.formats.informatregistry import (
    InformatRegistry, input_value, register_informat)
from ccai.analysis.statistical.ir.logiccompiler import (
    LogicCompiler, compile_logic)
from ccai.analysis.statistical.ir.unsupportederror import UnsupportedError
from ccai.analysis.statistical.missing.missing import Missing
from ccai.analysis.statistical.missing.missingfactory import MISSING, missing
from ccai.analysis.statistical.readers.mergereader import MergeReader
from ccai.analysis.statistical.readers.reader import Reader
from ccai.analysis.statistical.readers.setreader import SetReader
from ccai.analysis.statistical.report.reportbuilder import (
    ReportBuilder, report)
from ccai.analysis.statistical.types.constants import CHAR, DECIMAL, NUM
from ccai.analysis.statistical.types.typehandler import TypeHandler
from ccai.analysis.statistical.types.typeregistry import (
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
