"""
    .. module:: datetimeformat
        :synopsis: The :class:`DatetimeFormat` -- SAS ``DATETIMEw.`` format.
                   SAS datetimes are integers (or floats) counting seconds
                   since 1960-01-01 00:00:00.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from datetime import datetime, timedelta
from typing import Any

from ccai.analysis.statistical.formats.dateformat import DateFormat


class DatetimeFormat:
    """
        Renders a SAS datetime (seconds since 1960-01-01 00:00:00) as
        ``DDMONYYYY:HH:MM:SS`` text. ``DATETIME19.`` is the canonical width.
    """

    SAS_EPOCH: datetime = datetime(1960, 1, 1, 0, 0, 0)

    def __call__(self, value: Any, width: int | None,
                 decimals: int | None) -> str:
        """
            Render ``value`` as a ``DATETIME``-style string.

            :param value: The SAS datetime as a seconds-offset.
            :param width: The display width (kept for parity; output is
                          ``DDMONYYYY:HH:MM:SS``).
            :param decimals: Unused (sub-second precision is not modeled).

            :returns: The formatted datetime text.
        """
        seconds = float(value)
        when = self.SAS_EPOCH + timedelta(seconds=seconds)
        month_label = DateFormat.MONTHS[when.month - 1]
        day_label = "{:02d}".format(when.day)
        year_label = "{:04d}".format(when.year)
        time_label = "{:02d}:{:02d}:{:02d}".format(when.hour, when.minute,
                                                   when.second)
        rtnval = "{}{}{}:{}".format(day_label, month_label, year_label,
                                    time_label)
        return rtnval
