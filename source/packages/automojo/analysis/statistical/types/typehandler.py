"""
    .. module:: typehandler
        :synopsis: The :class:`TypeHandler` class -- a per-storage-type entry
                   that the engine uses to coerce values, find missing
                   sentinels, and determine default storage lengths.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from typing import Any
from collections.abc import Callable


class TypeHandler:
    """
        A storage-type entry. Each registered storage type (``num``, ``char``,
        ``decimal``, ...) contributes one :class:`TypeHandler` to the
        :class:`automojo.analysis.statistical.types.typeregistry.TypeRegistry`.
    """

    def __init__(self, name: str, coerce: Callable[[Any, int], Any],
                 missing_value: Any, default_length: int) -> None:
        """
            Initialize the :class:`TypeHandler`.

            :param name: The canonical name of the storage type.
            :param coerce: A callable ``(value, length) -> stored_value``.
            :param missing_value: The sentinel value for "missing" at this type.
            :param default_length: The default storage length when none is
                                   provided on declaration.

            :returns: ``None``
        """
        self.name = name
        self.coerce = coerce
        self.missing = missing_value
        self.default_length = default_length
        return
