"""
    Bootstrap the engine's core storage types. Importing the ``types`` package
    ensures the ``num`` and ``char`` :class:`TypeHandler` entries are present in
    :class:`TypeRegistry`. Custom storage types (for example ``decimal``) are
    registered by their own packages and are NOT registered here, to preserve
    the SAS-faithful ``num + char`` core.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from automojo.analysis.statistical.missing.missingfactory import MISSING
from automojo.analysis.statistical.types.charcoercer import CharCoercer
from automojo.analysis.statistical.types.constants import CHAR, NUM
from automojo.analysis.statistical.types.numcoercer import NumCoercer
from automojo.analysis.statistical.types.typehandler import TypeHandler
from automojo.analysis.statistical.types.typeregistry import TypeRegistry


def _bootstrap_core_types() -> None:
    """
        Register the engine's core ``num`` and ``char`` storage types.

        :returns: ``None``
    """
    num_handler = TypeHandler(name=NUM, coerce=NumCoercer(),
                              missing_value=MISSING, default_length=8)
    char_handler = TypeHandler(name=CHAR, coerce=CharCoercer(),
                               missing_value="", default_length=1)

    TypeRegistry.register(handler=num_handler)
    TypeRegistry.register(handler=char_handler)
    return


_bootstrap_core_types()
