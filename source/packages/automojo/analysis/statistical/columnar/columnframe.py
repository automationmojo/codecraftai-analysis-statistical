"""
    .. module:: columnframe
        :synopsis: The :class:`ColumnFrame` -- a column-oriented result
                   wrapper. Holds results as ``{name: ndarray}`` and
                   materializes rows lazily, so a pipeline of vectorizable
                   steps stays columnar end to end.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


import numpy as np
from typing import Any
from collections.abc import Iterator

from automojo.analysis.statistical.execution.columnbuilder import ColumnBuilder


class ColumnFrame:
    """
        Column-oriented result. Pay O(columns) array operations rather than
        O(rows) dict allocations. Row dicts are produced on demand via
        iteration, integer index, or :meth:`to_dicts`.
    """

    def __init__(self, columns: dict, row_count: int, order: list[str]) -> None:
        """
            Initialize the :class:`ColumnFrame`.

            :param columns: A mapping of ``{name: ndarray}``.
            :param row_count: The number of rows represented.
            :param order: The output column order.

            :returns: ``None``
        """
        self._cols = columns
        self._row_count = row_count
        self._order = list(order)
        return

    @property
    def columns(self) -> list[str]:
        """
            The output column order.

            :returns: A copy of the column-order list.
        """
        rtnval = list(self._order)
        return rtnval

    def __len__(self) -> int:
        """
            Return the number of rows.

            :returns: The row count.
        """
        rtnval = self._row_count
        return rtnval

    def array(self, name: str) -> Any:
        """
            Return the underlying array for a column.

            :param name: The column name.

            :returns: The ``ndarray`` for that column.
        """
        rtnval = self._cols[name]
        return rtnval

    def __getitem__(self, key: Any) -> Any:
        """
            Indexing by column name returns the array. Indexing by integer
            returns a row dict.

            :param key: A column name or row index.

            :returns: The array or row dict.
            :raises TypeError: For unsupported key types.
        """
        if isinstance(key, str):
            rtnval = self._cols[key]
        elif isinstance(key, int):
            rtnval = {name: ColumnBuilder.to_scalar(value=self._cols[name][key])
                      for name in self._order}
        else:
            raise TypeError(key)
        return rtnval

    def __iter__(self) -> Iterator[dict]:
        """
            Iterate rows on demand.

            :returns: A row-dict iterator.
        """
        for index in range(self._row_count):
            row = {name: ColumnBuilder.to_scalar(value=self._cols[name][index])
                   for name in self._order}
            yield row
        return

    def to_dicts(self) -> list[dict]:
        """
            Materialize every row as a dict.

            :returns: A list of row dictionaries.
        """
        rtnval = list(self)
        return rtnval

    def head(self, k: int = 5) -> list[dict]:
        """
            Return the first ``k`` rows.

            :param k: The number of rows to return.

            :returns: A list of row dictionaries.
        """
        bound = min(k, self._row_count)
        rtnval = [self[i] for i in range(bound)]
        return rtnval

    def to_pandas(self):
        """
            Convert to a :class:`pandas.DataFrame`. Requires ``pandas``.

            :returns: A pandas DataFrame.
        """
        import pandas as pd
        rtnval = pd.DataFrame({name: self._cols[name] for name in self._order})
        return rtnval

    def to_arrow(self):
        """
            Convert to a :class:`pyarrow.Table`. Requires ``pyarrow``.

            :returns: A pyarrow Table.
        """
        import pyarrow as pa
        rtnval = pa.table({name: self._cols[name] for name in self._order})
        return rtnval

    @classmethod
    def from_dicts(cls, rows: list[dict]) -> "ColumnFrame":
        """
            Build a :class:`ColumnFrame` from a list of row dicts.

            :param rows: A list of row dictionaries.

            :returns: A new :class:`ColumnFrame`.
        """
        if len(rows) == 0:
            rtnval = cls(columns={}, row_count=0, order=[])
        else:
            order = list(rows[0].keys())
            cols = {name: np.array([row.get(name) for row in rows])
                    for name in order}
            rtnval = cls(columns=cols, row_count=len(rows), order=order)
        return rtnval
