"""
    .. module:: formatregistry
        :synopsis: Process-wide registry of format converters
                   (``value -> text``). Formats are the SAS-faithful extension
                   point for new value representations -- dates, currency, and
                   so on -- without inventing new storage types.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


import os
from typing import Any
from collections.abc import Callable

from automojo.analysis.statistical.formats.formatspec import FormatSpec
from automojo.analysis.statistical.missing.missing import Missing


class FormatRegistry:
    """
        Registry of format converters. Each entry is a callable
        ``(value, width, decimals) -> text``.
    """

    _formats: dict = {}

    @classmethod
    def register(cls, name: str,
                 fn: Callable[[Any, int | None, int | None], str]) -> None:
        """
            Register a format converter under ``name``.

            :param name: The format name (case-insensitive).
            :param fn: The converter callable.

            :returns: ``None``
        """
        cls._formats[name.upper()] = fn
        return

    @classmethod
    def get(cls, name: str) -> Callable[[Any, int | None, int | None], str] | None:
        """
            Look up a registered converter by name.

            :param name: The format name (case-insensitive).

            :returns: The converter callable, or ``None`` when unregistered.
        """
        rtnval = cls._formats.get(name.upper())
        return rtnval

    @classmethod
    def apply(cls, value: Any, spec: str | None) -> str:
        """
            Apply a format spec to a value (the PUT operation).

            :param value: The value to format. ``Missing`` values render as
                          their canonical text form (``.`` / ``._`` / ``.A``).
            :param spec: The format spec string, or ``None`` for the default.

            :returns: The formatted text representation of ``value``.
        """
        if isinstance(value, Missing):
            rtnval = repr(value)
        else:
            parsed = FormatSpec.parse(spec=spec)
            fn = cls._formats.get(parsed.name)
            if fn is None:
                if parsed.name == "":
                    rtnval = cls._default_display(value=value)
                else:
                    err_msg_lines = [
                        "No format converter is registered for the requested name.",
                        "    requested: {}".format(parsed.name),
                        "    spec:      {}".format(spec),
                        "    registered: {}".format(sorted(cls._formats.keys())),
                    ]
                    err_msg = os.linesep.join(err_msg_lines)
                    raise KeyError(err_msg)
            else:
                rtnval = fn(value, parsed.width, parsed.decimals)
        return rtnval

    @classmethod
    def _default_display(cls, value: Any) -> str:
        """
            Default text representation when no format is registered.

            :param value: The value to display.

            :returns: A text representation; integer-valued floats render
                      without a trailing ``.0``.
        """
        if isinstance(value, float) and value.is_integer():
            rtnval = str(int(value))
        else:
            rtnval = str(value)
        return rtnval


def register_format(name: str,
                    fn: Callable[[Any, int | None, int | None], str]) -> None:
    """
        Convenience helper that registers ``fn`` under ``name`` with
        :class:`FormatRegistry`.

        :param name: The format name.
        :param fn: The converter callable.

        :returns: ``None``
    """
    FormatRegistry.register(name=name, fn=fn)
    return


def format_value(value: Any, spec: str | None) -> str:
    """
        Apply a format spec to a value (the PUT operation).

        :param value: The value to format.
        :param spec: The format spec string, or ``None``.

        :returns: The formatted text.
    """
    rtnval = FormatRegistry.apply(value=value, spec=spec)
    return rtnval
