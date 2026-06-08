"""
    .. module:: numcoercer
        :synopsis: The :class:`NumCoercer` callable that coerces arbitrary
                   values into the engine's ``num`` storage type.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from typing import Any

from ccai.analysis.statistical.missing.missing import Missing
from ccai.analysis.statistical.missing.missingfactory import MISSING


class NumCoercer:
    """
        Coerce values into the engine's ``num`` storage type. Permissive: a
        value that fails numeric coercion becomes :data:`MISSING` rather than
        raising, matching SAS DATA-step behavior. Native Python numeric types
        are kept (SAS itself uses float64; the engine documents this divergence).
    """

    def __call__(self, value: Any, length: int) -> Any:
        """
            Coerce ``value`` to ``num``.

            :param value: The value to coerce.
            :param length: Storage length (kept for parity with other coercers;
                           unused for numeric storage).

            :returns: The coerced numeric value, or :data:`MISSING`.
        """
        if isinstance(value, Missing):
            rtnval = value
        elif isinstance(value, bool):
            rtnval = 1 if value else 0
        elif isinstance(value, (int, float)):
            rtnval = value
        else:
            try:
                rtnval = float(value)
            except (TypeError, ValueError):
                rtnval = MISSING
        return rtnval
