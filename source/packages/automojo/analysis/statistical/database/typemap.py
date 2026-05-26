"""
    .. module:: typemap
        :synopsis: The :class:`TypeMap` -- a dialect-specific mapping from a
                   driver's column ``type_code`` to engine
                   ``(stype, length, fmt)`` triples (or a callable resolver
                   for precision-aware routing).

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from collections.abc import Callable


TypeMapValue = (
    tuple[str, int | None, str | None]
    | Callable[[tuple], tuple[str, int | None, str | None]]
)


class TypeMap:
    """
        Container for one dialect's ``{type_code: triple|callable}`` mapping.
        A callable value is invoked with the cursor description entry so
        precision-routed types (NUMERIC / NUMBER / DECIMAL) can return the
        correct ``(stype, length, fmt)`` for each column.
    """

    def __init__(self, entries: dict) -> None:
        """
            Initialize the :class:`TypeMap`.

            :param entries: A mapping of ``type_code -> triple_or_callable``.

            :returns: ``None``
        """
        self._entries = dict(entries)
        return

    def resolve(self, description_entry: tuple) -> tuple[str, int | None, str | None] | None:
        """
            Resolve a cursor description entry to an engine type triple.

            :param description_entry: One element of ``cursor.description``.

            :returns: ``(stype, length, fmt)`` for known type codes, or
                      ``None`` when the code is not mapped (the engine will
                      auto-infer in that case).
        """
        type_code = description_entry[1]
        entry = self._entries.get(type_code)
        if entry is None:
            rtnval = None
        elif callable(entry):
            rtnval = entry(description_entry)
        else:
            rtnval = entry
        return rtnval

    @property
    def entries(self) -> dict:
        """
            Direct read access to the underlying mapping.

            :returns: A shallow copy of the entries dictionary.
        """
        rtnval = dict(self._entries)
        return rtnval
