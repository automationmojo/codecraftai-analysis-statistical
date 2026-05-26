"""
    .. module:: columnbuilder
        :synopsis: The :class:`ColumnBuilder` -- turns a list of row dicts
                   into a ``{name: ndarray}`` column dictionary.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


import numpy as np
from typing import Any


class ColumnBuilder:
    """
        Build a column-oriented view of a list of row dicts.
    """

    @classmethod
    def build(cls, rows: list[dict]) -> dict:
        """
            Build the ``{name: ndarray}`` view.

            :param rows: A non-empty list of row dictionaries (assumed to have
                         consistent keys; the first row defines column order).

            :returns: A dictionary of column arrays.
        """
        if len(rows) == 0:
            rtnval: dict = {}
        else:
            first = rows[0]
            cols: dict = {}
            for column_name in first:
                values = [row.get(column_name) for row in rows]
                cols[column_name] = np.array(values)
            rtnval = cols
        return rtnval

    @classmethod
    def to_scalar(cls, value: Any) -> Any:
        """
            Convert a numpy scalar back to a native Python value.

            :param value: A numpy or native value.

            :returns: A native Python value if applicable; otherwise the
                      original input.
        """
        if hasattr(value, "item"):
            rtnval = value.item()
        else:
            rtnval = value
        return rtnval
