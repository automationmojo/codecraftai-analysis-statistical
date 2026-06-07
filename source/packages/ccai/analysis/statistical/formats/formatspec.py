"""
    .. module:: formatspec
        :synopsis: The :class:`FormatSpec` class -- a parsed SAS-style format
                   specification such as ``DOLLAR8.2``, ``DATE9.``, ``8.2``,
                   or ``$10.``.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


import re


class FormatSpec:
    """
        A parsed SAS-style format specification.

        A format string has the shape ``[$|name][width][.decimals]``. Examples:

        * ``DOLLAR8.2`` -> name="DOLLAR", width=8, decimals=2
        * ``DATE9.``    -> name="DATE",   width=9, decimals=None
        * ``8.2``       -> name="",       width=8, decimals=2
        * ``$10.``      -> name="$",      width=10, decimals=None
    """

    _PATTERN = re.compile(r"^(\$?[A-Za-z]*)(\d+)?\.?(\d+)?$")

    def __init__(self, name: str, width: int | None,
                 decimals: int | None) -> None:
        """
            Initialize a :class:`FormatSpec`.

            :param name: The format name (upper-cased; ``""`` for the default).
            :param width: Display width if specified; ``None`` otherwise.
            :param decimals: Number of decimal places if specified; ``None``
                             otherwise.

            :returns: ``None``
        """
        self.name = name
        self.width = width
        self.decimals = decimals
        return

    @classmethod
    def parse(cls, spec: str | None) -> "FormatSpec":
        """
            Parse a format specification string into a :class:`FormatSpec`.

            :param spec: The spec string (for example ``"DOLLAR8.2"``).
                         ``None`` and the empty string produce a default spec.

            :returns: A :class:`FormatSpec` instance.
        """
        if spec is None or spec == "":
            rtnval = cls(name="", width=None, decimals=None)
        else:
            match = cls._PATTERN.match(spec)
            if match is None:
                rtnval = cls(name="", width=None, decimals=None)
            else:
                raw_name = match.group(1)
                raw_width = match.group(2)
                raw_decimals = match.group(3)

                name = raw_name.upper()
                width = int(raw_width) if raw_width is not None else None
                decimals = int(raw_decimals) if raw_decimals is not None else None

                rtnval = cls(name=name, width=width, decimals=decimals)
        return rtnval
