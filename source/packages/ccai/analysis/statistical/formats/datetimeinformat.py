"""
    .. module:: datetimeinformat
        :synopsis: The :class:`DatetimeInformat` -- parses
                   ``DDMONYYYY:HH:MM:SS`` text into a SAS datetime
                   (seconds-offset from 1960-01-01 00:00:00).

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from datetime import datetime

from ccai.analysis.statistical.formats.dateformat import DateFormat
from ccai.analysis.statistical.formats.datetimeformat import DatetimeFormat


class DatetimeInformat:
    """
        Parses ``DDMONYYYY:HH:MM:SS`` text into an integer SAS datetime.
    """

    def __call__(self, text: str, width: int | None) -> int:
        """
            Parse ``text`` into a SAS datetime.

            :param text: A string in ``DDMONYYYY:HH:MM:SS`` form.
            :param width: Field width hint (unused).

            :returns: The integer seconds-offset from the SAS epoch.
        """
        day = int(text[0:2])
        month_label = text[2:5].upper()
        year = int(text[5:9])
        hour = int(text[10:12])
        minute = int(text[13:15])
        second = int(text[16:18])

        month = DateFormat.MONTHS.index(month_label) + 1
        when = datetime(year, month, day, hour, minute, second)
        delta = when - DatetimeFormat.SAS_EPOCH
        rtnval = int(delta.total_seconds())
        return rtnval
