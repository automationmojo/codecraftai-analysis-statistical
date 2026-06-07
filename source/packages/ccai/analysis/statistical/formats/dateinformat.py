"""
    .. module:: dateinformat
        :synopsis: The :class:`DateInformat` -- parses ``DDMONYYYY`` style
                   text into a SAS date (integer day-offset from 1960-01-01).

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from datetime import date

from ccai.analysis.statistical.formats.dateformat import DateFormat


class DateInformat:
    """
        Parses ``DDMONYYYY`` text into an integer SAS date.
    """

    def __call__(self, text: str, width: int | None) -> int:
        """
            Parse ``text`` into a SAS date.

            :param text: A string in ``DDMONYYYY`` form (for example
                         ``01JAN1960``).
            :param width: Field width hint (unused).

            :returns: The integer day-offset from the SAS epoch.
        """
        day = int(text[0:2])
        month_label = text[2:5].upper()
        year = int(text[5:9])

        month = DateFormat.MONTHS.index(month_label) + 1
        when = date(year, month, day)
        delta = when - DateFormat.SAS_EPOCH
        rtnval = delta.days
        return rtnval
