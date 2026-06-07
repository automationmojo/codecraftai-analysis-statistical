"""
    .. module:: dateformat
        :synopsis: The :class:`DateFormat` -- SAS ``DATE9.`` style format.
                   SAS dates are integers counting days since 1960-01-01.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from datetime import date, timedelta
from typing import Any


class DateFormat:
    """
        Renders a SAS date (an integer day-offset from 1960-01-01) as
        ``DDMONYYYY`` text (for example ``01JAN1960``).
    """

    SAS_EPOCH: date = date(1960, 1, 1)
    MONTHS: tuple = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                     "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")

    def __call__(self, value: Any, width: int | None,
                 decimals: int | None) -> str:
        """
            Render ``value`` as a ``DATE``-style string.

            :param value: The SAS date as an integer day-offset.
            :param width: The display width (kept for parity; output is always
                          ``DDMONYYYY``).
            :param decimals: Unused.

            :returns: The formatted date text.
        """
        days = int(value)
        when = self.SAS_EPOCH + timedelta(days=days)
        month_label = self.MONTHS[when.month - 1]
        day_label = "{:02d}".format(when.day)
        year_label = "{:04d}".format(when.year)
        rtnval = "{}{}{}".format(day_label, month_label, year_label)
        return rtnval
