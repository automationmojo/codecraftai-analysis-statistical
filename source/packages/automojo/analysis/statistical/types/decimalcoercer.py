"""
    .. module:: decimalcoercer
        :synopsis: The :class:`DecimalCoercer` callable for the engine's
                   custom ``decimal`` storage type. Used when source precision
                   exceeds float64's safe range (15-16 digits).

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from decimal import Decimal, InvalidOperation
from typing import Any

from automojo.analysis.statistical.missing.missing import Missing
from automojo.analysis.statistical.missing.missingfactory import MISSING


class DecimalCoercer:
    """
        Coerce values into :class:`decimal.Decimal`. Already-Decimal values
        pass through unchanged. Other values are routed through
        ``Decimal(str(value))`` to avoid binary-float artifacts. Permissive:
        unparseable values become :data:`MISSING`.
    """

    def __call__(self, value: Any, length: int) -> Any:
        """
            Coerce ``value`` to ``decimal``.

            :param value: The value to coerce.
            :param length: Storage length (kept for parity; unused).

            :returns: A :class:`Decimal`, the original :class:`Missing` value,
                      or :data:`MISSING` when coercion fails.
        """
        if isinstance(value, Missing):
            rtnval = value
        elif isinstance(value, Decimal):
            rtnval = value
        else:
            try:
                rtnval = Decimal(str(value))
            except (InvalidOperation, TypeError, ValueError):
                rtnval = MISSING
        return rtnval
