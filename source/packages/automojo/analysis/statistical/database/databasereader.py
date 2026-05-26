"""
    .. module:: databasereader
        :synopsis: The :class:`DatabaseReader` -- a SAS/ACCESS-engine analogue
                   that wraps any PEP 249 cursor. Streams rows lazily and
                   self-describes its schema through :meth:`declarations` so
                   the engine can type the PDV from the cursor's description.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from typing import Any

from automojo.analysis.statistical.database.cursorrowstream import CursorRowStream
from automojo.analysis.statistical.database.typemap import TypeMap
from automojo.analysis.statistical.readers.setreader import SetReader
from automojo.analysis.statistical.types.constants import CHAR


class DatabaseReader(SetReader):
    """
        A :class:`Reader` over a PEP 249 cursor. Push ``ORDER BY`` / ``WHERE``
        into the SQL: the database sorts and filters more efficiently than the
        engine, and :class:`MergeReader` requires sorted input.

        Unknown driver type codes are skipped at declaration time -- the
        engine will auto-infer storage type from the first row that visits a
        slot.
    """

    DEFAULT_CHAR_LENGTH: int = 200

    def __init__(self, cursor: Any, by: list | None = None,
                 dialect: TypeMap | None = None,
                 char_default_len: int | None = None) -> None:
        """
            Initialize the :class:`DatabaseReader`.

            :param cursor: An already-executed PEP 249 cursor.
            :param by: Optional BY-key column names.
            :param dialect: A :class:`TypeMap` for the source dialect; when
                            ``None``, no declarations are produced and every
                            column auto-infers.
            :param char_default_len: Default length for ``CHAR`` columns whose
                                     driver-reported ``internal_size`` is
                                     missing or non-positive.

            :returns: ``None``
        """
        self._cursor = cursor
        self._dialect = dialect

        if char_default_len is None:
            self._char_default = self.DEFAULT_CHAR_LENGTH
        else:
            self._char_default = char_default_len

        row_stream = CursorRowStream(cursor=cursor)
        super().__init__(source=row_stream, by=by)
        return

    def declarations(self) -> list:
        """
            Build per-column declarations from the cursor's description.

            :returns: A list of declaration dictionaries compatible with
                      :meth:`RecordFrame.declare`.
        """
        decls: list = []
        if self._dialect is not None:
            for entry in self._cursor.description:
                mapped = self._dialect.resolve(description_entry=entry)
                if mapped is None:
                    continue
                stype, length, fmt = mapped
                if stype == CHAR and length is None:
                    internal_size = entry[3]
                    if internal_size is not None and internal_size > 0:
                        effective_length = internal_size
                    else:
                        effective_length = self._char_default
                else:
                    effective_length = length

                decls.append({"name": entry[0], "stype": stype,
                              "length": effective_length, "fmt": fmt})
        rtnval = decls
        return rtnval
