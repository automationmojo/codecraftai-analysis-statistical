"""
    .. module:: mergereader
        :synopsis: The :class:`MergeReader` -- the SAS ``MERGE`` analogue. A
                   multi-cursor sub-state-machine that performs positional
                   match-merge over BY-sorted sources with optional ``IN=``
                   flags, retain-on-exhaustion within a BY-group, and
                   later-dataset-wins semantics.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"



from automojo.analysis.statistical.missing.missingfactory import MISSING
from automojo.analysis.statistical.readers.peekable import Peekable
from automojo.analysis.statistical.readers.reader import Reader


class MergeReader(Reader):
    """
        Multi-source match-merge reader. Each input source is expected to be
        sorted by the BY-key. Within a BY-group:

        * rows from each source are combined positionally (not as a Cartesian
          product),
        * the optional ``in_flags`` map yields a ``1``/``0`` flag per source
          telling whether that source contributed a row,
        * once a source's last row in the group has been read, its values
          remain retained for subsequent rows of the group,
        * when both sources contribute on the same row, the later source wins.
    """

    def __init__(self, sources: dict, by: list,
                 in_flags: dict | None = None) -> None:
        """
            Initialize the :class:`MergeReader`.

            :param sources: A mapping of ``{source_name: iterable_of_rows}``.
            :param by: The BY-key column names.
            :param in_flags: Optional mapping ``{source_name: in_flag_name}``;
                             when provided, ``next_obs`` reports a ``1``/``0``
                             flag under the chosen flag name per row.

            :returns: ``None``
        """
        self._cursors: dict = {name: Peekable(source=src)
                               for name, src in sources.items()}
        self._by = list(by)
        if in_flags is None:
            self._in_flags = {}
        else:
            self._in_flags = dict(in_flags)
        self._work: dict = {}
        self._group: tuple | None = None
        self._active = False
        return

    def _key(self, row: dict | None) -> tuple:
        """
            Compute the BY-key tuple for ``row``.

            :param row: A row dictionary.

            :returns: The BY-key tuple.
        """
        rtnval = tuple(row.get(name) for name in self._by)
        return rtnval

    def _min_front(self) -> tuple | None:
        """
            Compute the minimum BY-key across the front of all live cursors.

            :returns: The smallest front key, or ``None`` when every cursor is
                      exhausted.
        """
        front_keys = []
        for cursor in self._cursors.values():
            peeked = cursor.peek()
            if peeked is not None:
                front_keys.append(self._key(row=peeked))

        if len(front_keys) == 0:
            rtnval = None
        else:
            rtnval = min(front_keys)
        return rtnval

    def has_more(self) -> bool:
        """
            Indicate whether additional observations remain.

            :returns: ``True`` when more rows can be emitted.
        """
        if self._active is True:
            rtnval = True
        else:
            rtnval = self._min_front() is not None
        return rtnval

    def next_obs(self) -> tuple[dict, dict, tuple | None, tuple | None]:
        """
            Read the next observation.

            :returns: A tuple ``(row, in_flags, cur_key, next_key)``.
            :raises StopIteration: When no more rows are available.
        """
        if self._active is False:
            group_key = self._min_front()
            if group_key is None:
                raise StopIteration
            self._group = group_key
            self._active = True
            for column in list(self._work.keys()):
                self._work[column] = MISSING

        in_result: dict = {}
        for source_name, cursor in self._cursors.items():
            front = cursor.peek()
            matched = front is not None and self._key(row=front) == self._group
            if source_name in self._in_flags:
                flag_name = self._in_flags[source_name]
                in_result[flag_name] = 1 if matched is True else 0
            if matched is True:
                popped = cursor.pop()
                for column, value in popped.items():
                    self._work[column] = value

        for index, by_name in enumerate(self._by):
            self._work[by_name] = self._group[index]

        cur_key = self._group

        still_in_group = False
        for cursor in self._cursors.values():
            peeked = cursor.peek()
            if peeked is not None and self._key(row=peeked) == self._group:
                still_in_group = True
                break

        if still_in_group is True:
            next_key = self._group
        else:
            self._active = False
            next_key = self._min_front()

        rtnval = (dict(self._work), in_result, cur_key, next_key)
        return rtnval
