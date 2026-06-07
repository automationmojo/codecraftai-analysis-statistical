"""
    Bootstrap the engine's ``decimal`` storage type. Importing the database
    subpackage registers :class:`DecimalCoercer` under :data:`DECIMAL` so
    precision-routed columns have a place to land. SAS-core ``num + char``
    fidelity is unaffected -- ``decimal`` is opt-in (declared, never inferred).
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from ccai.analysis.statistical.missing.missingfactory import MISSING
from ccai.analysis.statistical.types.constants import DECIMAL
from ccai.analysis.statistical.types.decimalcoercer import DecimalCoercer
from ccai.analysis.statistical.types.typehandler import TypeHandler
from ccai.analysis.statistical.types.typeregistry import TypeRegistry


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
