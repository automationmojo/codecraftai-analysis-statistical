"""
    Bootstrap the engine's built-in formats and informats. Importing the
    ``formats`` package ensures the canonical built-ins are registered with
    :class:`FormatRegistry` and :class:`InformatRegistry`. Additional format /
    informat classes can be registered by callers at any time.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from automojo.analysis.statistical.formats.charformat import CharFormat
from automojo.analysis.statistical.formats.commaformat import CommaFormat
from automojo.analysis.statistical.formats.commainformat import CommaInformat
from automojo.analysis.statistical.formats.dateformat import DateFormat
from automojo.analysis.statistical.formats.dateinformat import DateInformat
from automojo.analysis.statistical.formats.datetimeformat import DatetimeFormat
from automojo.analysis.statistical.formats.datetimeinformat import DatetimeInformat
from automojo.analysis.statistical.formats.dollarformat import DollarFormat
from automojo.analysis.statistical.formats.dollarinformat import DollarInformat
from automojo.analysis.statistical.formats.formatregistry import FormatRegistry
from automojo.analysis.statistical.formats.informatregistry import InformatRegistry


def _bootstrap_builtin_formats() -> None:
    """
        Register the engine's built-in format and informat converters.

        :returns: ``None``
    """
    FormatRegistry.register(name="DOLLAR", fn=DollarFormat())
    FormatRegistry.register(name="COMMA", fn=CommaFormat())
    FormatRegistry.register(name="DATE", fn=DateFormat())
    FormatRegistry.register(name="DATETIME", fn=DatetimeFormat())
    FormatRegistry.register(name="$", fn=CharFormat())

    InformatRegistry.register(name="DATE", fn=DateInformat())
    InformatRegistry.register(name="DATETIME", fn=DatetimeInformat())
    InformatRegistry.register(name="DOLLAR", fn=DollarInformat())
    InformatRegistry.register(name="COMMA", fn=CommaInformat())
    return


_bootstrap_builtin_formats()
