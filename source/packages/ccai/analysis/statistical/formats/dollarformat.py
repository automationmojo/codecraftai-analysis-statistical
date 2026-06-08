"""
    .. module:: dollarformat
        :synopsis: The :class:`DollarFormat` -- SAS ``DOLLARw.d`` format.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from typing import Any


class DollarFormat:
    """
        Renders a numeric value as a dollar-formatted string with thousands
        separators (``$1,234.50``). Decimals default to ``0`` when not
        specified.
    """

    def __call__(self, value: Any, width: int | None,
                 decimals: int | None) -> str:
        """
            Render ``value`` as dollar text.

            :param value: The numeric value to render.
            :param width: The total display width (kept for parity; the
                          underlying format string is data-driven).
            :param decimals: The number of decimal places; ``None`` means ``0``.

            :returns: The dollar-formatted text.
        """
        if decimals is None:
            places = 0
        else:
            places = decimals
        rtnval = "${:,.{}f}".format(value, places)
        return rtnval
