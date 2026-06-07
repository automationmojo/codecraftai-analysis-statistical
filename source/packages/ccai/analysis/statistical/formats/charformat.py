"""
    .. module:: charformat
        :synopsis: The :class:`CharFormat` -- SAS ``$w.`` character format.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from typing import Any


class CharFormat:
    """
        Renders a value as a fixed-width string. Shorter values are
        left-justified and space-padded; longer values are truncated.
    """

    def __call__(self, value: Any, width: int | None,
                 decimals: int | None) -> str:
        """
            Render ``value`` at the given character width.

            :param value: The value to render.
            :param width: The display width; ``None`` means the natural width
                          of the value.
            :param decimals: Unused.

            :returns: The formatted text.
        """
        text = str(value)
        if width is None:
            chosen_width = len(text)
        else:
            chosen_width = width
        padded = text.ljust(chosen_width)
        rtnval = padded[:chosen_width]
        return rtnval
