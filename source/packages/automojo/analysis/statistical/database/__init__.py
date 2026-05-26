"""
    Bootstrap the engine's ``decimal`` storage type. Importing the database
    subpackage registers :class:`DecimalCoercer` under :data:`DECIMAL` so
    precision-routed columns have a place to land. SAS-core ``num + char``
    fidelity is unaffected -- ``decimal`` is opt-in (declared, never inferred).
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from automojo.analysis.statistical.missing.missingfactory import MISSING
from automojo.analysis.statistical.types.constants import DECIMAL
from automojo.analysis.statistical.types.decimalcoercer import DecimalCoercer
from automojo.analysis.statistical.types.typehandler import TypeHandler
from automojo.analysis.statistical.types.typeregistry import TypeRegistry


def _bootstrap_decimal_type() -> None:
    """
        Register the ``decimal`` storage type.

        :returns: ``None``
    """
    handler = TypeHandler(name=DECIMAL, coerce=DecimalCoercer(),
                          missing_value=MISSING, default_length=16)
    TypeRegistry.register(handler=handler)
    return


_bootstrap_decimal_type()
