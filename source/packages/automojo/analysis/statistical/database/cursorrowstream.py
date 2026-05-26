"""
    .. module:: cursorrowstream
        :synopsis: The :class:`CursorRowStream` -- lazily streams an already-
                   executed PEP 249 cursor as ``{column: value}`` dicts, in
                   ``fetchmany`` batches, so a query is never loaded all at
                   once.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from typing import Any
from collections.abc import Iterator


class CursorRowStream:
    """
        Lazy iterator over an already-executed PEP 249 cursor. Pulls rows in
        ``fetchmany`` batches of ``arraysize`` so memory usage stays bounded
        regardless of result-set size.
    """

    def __init__(self, cursor: Any, arraysize: int = 500) -> None:
        """
            Initialize the :class:`CursorRowStream`.

            :param cursor: An already-executed PEP 249 cursor.
            :param arraysize: The ``fetchmany`` batch size.

            :returns: ``None``
        """
        self._cursor = cursor
        self._arraysize = arraysize
        self._columns = [d[0] for d in cursor.description]
        return

    def __iter__(self) -> Iterator[dict]:
        """
            Yield rows as ``{column: value}`` dicts.

            :returns: An iterator over row dictionaries.
        """
        while True:
            batch = self._cursor.fetchmany(self._arraysize)
            if batch is None or len(batch) == 0:
                break
            for row in batch:
                paired = dict(zip(self._columns, row, strict=False))
                yield paired
        return
