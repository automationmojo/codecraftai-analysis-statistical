"""
    .. module:: dollarinformat
        :synopsis: The :class:`DollarInformat` -- parses dollar-formatted
                   text (for example ``$1,234.50``) into a float.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"




class DollarInformat:
    """
        Parses dollar-formatted text into a float.
    """

    def __call__(self, text: str, width: int | None) -> float:
        """
            Parse ``text``.

            :param text: A dollar-formatted text value.
            :param width: Field width hint (unused).

            :returns: The parsed numeric value.
        """
        cleaned = text.replace("$", "").replace(",", "")
        rtnval = float(cleaned)
        return rtnval
