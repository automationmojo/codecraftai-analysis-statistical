"""
    .. module:: commaformat
        :synopsis: The :class:`CommaFormat` -- SAS ``COMMAw.d`` format.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from typing import Any


class CommaFormat:
    """
        Renders a numeric value with thousands separators (``1,234.50``).
        Decimals default to ``0`` when not specified.
    """

    def __call__(self, value: Any, width: int | None,
                 decimals: int | None) -> str:
        """
            Render ``value`` with comma grouping.

            :param value: The numeric value to render.
            :param width: The total display width (kept for parity).
            :param decimals: The number of decimal places; ``None`` means ``0``.

            :returns: The comma-formatted text.
        """
        if decimals is None:
            places = 0
        else:
            places = decimals
        rtnval = "{:,.{}f}".format(value, places)
        return rtnval
