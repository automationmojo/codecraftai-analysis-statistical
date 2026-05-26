"""
    .. module:: charcoercer
        :synopsis: The :class:`CharCoercer` callable that coerces arbitrary
                   values into the engine's ``char`` storage type, applying
                   fixed-length silent truncation.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from typing import Any

from automojo.analysis.statistical.missing.missing import Missing


class CharCoercer:
    """
        Coerce values into the engine's ``char`` storage type. ``char`` missing
        is the empty string. Non-string values fall through to a default text
        representation (integers and integer-valued floats render without a
        trailing ``.0``). Storage is fixed-length: longer strings are silently
        truncated, matching SAS DATA-step behavior.
    """

    def __call__(self, value: Any, length: int) -> str:
        """
            Coerce ``value`` to ``char`` at the given storage length.

            :param value: The value to coerce.
            :param length: Storage length in characters.

            :returns: The truncated string representation of ``value``.
        """
        if isinstance(value, Missing):
            rtnval = ""
        elif isinstance(value, str):
            rtnval = value[:length]
        else:
            displayed = self._default_display(value)
            rtnval = displayed[:length]
        return rtnval

    def _default_display(self, value: Any) -> str:
        """
            Render a non-string value to its default text representation.

            :param value: A non-string, non-missing value.

            :returns: The text form of ``value``.
        """
        if isinstance(value, float) and value.is_integer():
            rtnval = str(int(value))
        else:
            rtnval = str(value)
        return rtnval
