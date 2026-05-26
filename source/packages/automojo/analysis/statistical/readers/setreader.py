"""
    .. module:: setreader
        :synopsis: The :class:`SetReader` -- the SAS ``SET`` analogue. Reads
                   from a single source iterable in order, optionally grouped
                   by a BY-key.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from collections.abc import Iterable

from automojo.analysis.statistical.readers.peekable import Peekable
from automojo.analysis.statistical.readers.reader import Reader


class SetReader(Reader):
    """
        Single-source reader. Emits each input row once, in order, with
        ``in_flags`` empty. When ``by`` is supplied, the BY-key tuple is
        produced from the named columns and a one-row look-ahead provides
        ``next_key`` so the engine can compute ``first.``/``last.`` flags.
    """

    def __init__(self, source: Iterable, by: list | None = None) -> None:
        """
            Initialize the :class:`SetReader`.

            :param source: An iterable of ``{var: value}`` dictionaries.
            :param by: An optional list of BY-key column names.

            :returns: ``None``
        """
        if by is None:
            self._by = []
        else:
            self._by = list(by)
        self._source = Peekable(source=source)
        return

    def _key(self, row: dict | None) -> tuple | None:
        """
            Compute the BY-key tuple for ``row``.

            :param row: A row dictionary or ``None``.

            :returns: A tuple of BY-key values, or ``None`` when ``row`` is
                      ``None``.
        """
        if row is None:
            rtnval = None
        else:
            rtnval = tuple(row.get(name) for name in self._by)
        return rtnval

    def has_more(self) -> bool:
        """
            Indicate whether additional observations are available.

            :returns: ``True`` when at least one more row remains.
        """
        rtnval = self._source.peek() is not None
        return rtnval

    def next_obs(self) -> tuple[dict, dict, tuple | None, tuple | None]:
        """
            Read the next observation.

            :returns: A tuple ``(row, in_flags, cur_key, next_key)``.
        """
        row = self._source.pop()
        in_flags: dict = {}
        cur_key = self._key(row=row)
        next_key = self._key(row=self._source.peek())
        rtnval = (row, in_flags, cur_key, next_key)
        return rtnval
