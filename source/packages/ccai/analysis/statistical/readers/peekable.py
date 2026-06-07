"""
    .. module:: peekable
        :synopsis: The :class:`Peekable` adaptor -- an iterator with a one-row
                   look-ahead. Used by :class:`SetReader` and
                   :class:`MergeReader` to compute next-key for BY-group
                   semantics.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from collections import deque
from typing import Any
from collections.abc import Iterable


class Peekable:
    """
        Iterator adaptor that supports peeking at the next element without
        consuming it.
    """

    def __init__(self, source: Iterable) -> None:
        """
            Initialize the :class:`Peekable`.

            :param source: An iterable of values to wrap.

            :returns: ``None``
        """
        self._iterator = iter(source)
        self._buffer: deque = deque()
        self._eof = False
        return

    def _fill(self) -> None:
        """
            Ensure the look-ahead buffer is populated, if possible.

            :returns: ``None``
        """
        if len(self._buffer) == 0 and self._eof is False:
            try:
                next_value = next(self._iterator)
                self._buffer.append(next_value)
            except StopIteration:
                self._eof = True
        return

    def peek(self) -> Any | None:
        """
            Return the next value without consuming it.

            :returns: The next value, or ``None`` when no values remain.
        """
        self._fill()
        if len(self._buffer) == 0:
            rtnval = None
        else:
            rtnval = self._buffer[0]
        return rtnval

    def pop(self) -> Any:
        """
            Consume and return the next value.

            :returns: The next value.
            :raises StopIteration: When no values remain.
        """
        self._fill()
        if len(self._buffer) == 0:
            raise StopIteration
        rtnval = self._buffer.popleft()
        return rtnval
