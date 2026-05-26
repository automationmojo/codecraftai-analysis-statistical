"""
    .. module:: typeregistry
        :synopsis: The :class:`TypeRegistry` -- a process-wide registry of
                   :class:`TypeHandler` entries, plus type inference and
                   register/lookup APIs used across the engine.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


import os
from typing import Any

from automojo.analysis.statistical.types.constants import CHAR, NUM
from automojo.analysis.statistical.types.typehandler import TypeHandler


class TypeRegistry:
    """
        Process-wide registry of storage-type handlers. SAS core storage is
        ``num`` + ``char``; custom storage types (for example ``decimal``) are
        declare-only opt-ins and must be registered explicitly.
    """

    _handlers: dict = {}

    @classmethod
    def register(cls, handler: TypeHandler) -> None:
        """
            Register a :class:`TypeHandler` under its name.

            :param handler: The handler to register.

            :returns: ``None``
        """
        cls._handlers[handler.name] = handler
        return

    @classmethod
    def get(cls, name: str) -> TypeHandler:
        """
            Return the :class:`TypeHandler` for ``name``.

            :param name: The canonical storage-type name.

            :returns: The registered :class:`TypeHandler`.
            :raises KeyError: When ``name`` is not registered.
        """
        handler = cls._handlers.get(name)
        if handler is None:
            err_msg_lines = [
                "No TypeHandler is registered for the requested name.",
                "    name: {}".format(name),
                "    registered: {}".format(sorted(cls._handlers.keys())),
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise KeyError(err_msg)
        return handler

    @classmethod
    def has(cls, name: str) -> bool:
        """
            Indicate whether a handler is registered under ``name``.

            :param name: The canonical storage-type name.

            :returns: ``True`` when registered.
        """
        rtnval = name in cls._handlers
        return rtnval

    @classmethod
    def names(cls) -> list:
        """
            Return the set of registered handler names.

            :returns: A sorted list of registered storage-type names.
        """
        rtnval = sorted(cls._handlers.keys())
        return rtnval

    @classmethod
    def infer(cls, value: Any) -> str:
        """
            Infer the engine storage type for an arbitrary Python value.

            :param value: The value to inspect.

            :returns: ``CHAR`` when the value is a :class:`str`; otherwise
                      ``NUM``. Custom storage types are never inferred.
        """
        if isinstance(value, str):
            rtnval = CHAR
        else:
            rtnval = NUM
        return rtnval


def register_type(handler: TypeHandler) -> None:
    """
        Convenience function that registers ``handler`` with
        :class:`TypeRegistry`.

        :param handler: The handler to register.

        :returns: ``None``
    """
    TypeRegistry.register(handler)
    return
