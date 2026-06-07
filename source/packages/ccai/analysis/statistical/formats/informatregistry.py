"""
    .. module:: informatregistry
        :synopsis: Process-wide registry of informat converters
                   (``text -> value``). Informats are the SAS-faithful entry
                   point for parsing raw text into typed values.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from typing import Any
from collections.abc import Callable

from ccai.analysis.statistical.formats.formatspec import FormatSpec


class InformatRegistry:
    """
        Registry of informat converters. Each entry is a callable
        ``(text, width) -> value``.
    """

    _informats: dict = {}

    @classmethod
    def register(cls, name: str,
                 fn: Callable[[str, int | None], Any]) -> None:
        """
            Register an informat converter under ``name``.

            :param name: The informat name (case-insensitive).
            :param fn: The converter callable.

            :returns: ``None``
        """
        cls._informats[name.upper()] = fn
        return

    @classmethod
    def get(cls, name: str) -> Callable[[str, int | None], Any] | None:
        """
            Look up a registered converter by name.

            :param name: The informat name (case-insensitive).

            :returns: The converter callable, or ``None`` when unregistered.
        """
        rtnval = cls._informats.get(name.upper())
        return rtnval

    @classmethod
    def apply(cls, text: str, spec: str | None) -> Any:
        """
            Apply an informat to raw text (the INPUT operation).

            :param text: The text to parse.
            :param spec: The informat spec string, or ``None``.

            :returns: The parsed value, or the original text when the name is
                      not registered.
        """
        parsed = FormatSpec.parse(spec=spec)
        fn = cls._informats.get(parsed.name)
        if fn is None:
            rtnval = text
        else:
            rtnval = fn(text, parsed.width)
        return rtnval


def register_informat(name: str,
                      fn: Callable[[str, int | None], Any]) -> None:
    """
        Convenience helper that registers ``fn`` under ``name`` with
        :class:`InformatRegistry`.

        :param name: The informat name.
        :param fn: The converter callable.

        :returns: ``None``
    """
    InformatRegistry.register(name=name, fn=fn)
    return


def input_value(text: str, spec: str | None) -> Any:
    """
        Apply an informat to raw text.

        :param text: The text to parse.
        :param spec: The informat spec, or ``None``.

        :returns: The parsed value.
    """
    rtnval = InformatRegistry.apply(text=text, spec=spec)
    return rtnval
