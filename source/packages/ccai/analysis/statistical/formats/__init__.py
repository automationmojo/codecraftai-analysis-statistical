"""
    Bootstrap the engine's built-in formats and informats. Importing the
    ``formats`` package ensures the canonical built-ins are registered with
    :class:`FormatRegistry` and :class:`InformatRegistry`. Additional format /
    informat classes can be registered by callers at any time.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from ccai.analysis.statistical.formats.charformat import CharFormat
from ccai.analysis.statistical.formats.commaformat import CommaFormat
from ccai.analysis.statistical.formats.commainformat import CommaInformat
from ccai.analysis.statistical.formats.dateformat import DateFormat
from ccai.analysis.statistical.formats.dateinformat import DateInformat
from ccai.analysis.statistical.formats.datetimeformat import DatetimeFormat
from ccai.analysis.statistical.formats.datetimeinformat import DatetimeInformat
from ccai.analysis.statistical.formats.dollarformat import DollarFormat
from ccai.analysis.statistical.formats.dollarinformat import DollarInformat
from ccai.analysis.statistical.formats.formatregistry import FormatRegistry
from ccai.analysis.statistical.formats.informatregistry import InformatRegistry


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
