"""
    .. module:: columnarstep
        :synopsis: The :class:`ColumnarStep` -- runs a logic step but returns
                   a :class:`ColumnFrame`, allowing zero-materialization
                   chaining across pure-vector pipeline stages.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


import numpy as np
from typing import Any

from ccai.analysis.statistical.columnar.columnframe import ColumnFrame
from ccai.analysis.statistical.execution.columnbuilder import ColumnBuilder
from ccai.analysis.statistical.execution.compiledstep import CompiledStep
from ccai.analysis.statistical.execution.vectorevaluator import VectorEvaluator


class ColumnarStep(CompiledStep):
    """
        A :class:`CompiledStep` that returns a :class:`ColumnFrame`. Accepts
        either a row iterable or a :class:`ColumnFrame` -- when chained from
        another columnar step, no per-row materialization happens between
        stages.
    """

    def run_columnar(self, data: Any) -> ColumnFrame:
        """
            Run the step and return a :class:`ColumnFrame`.

            :param data: Either a :class:`ColumnFrame` or an iterable of row
                         dicts.

            :returns: A :class:`ColumnFrame` of the output.
        """
        if isinstance(data, ColumnFrame):
            order = data.columns
            cols = {name: data.array(name) for name in order}
            row_count = len(data)
            row_buffer: list[dict] = None
        else:
            row_buffer = list(data)
            if len(row_buffer) == 0:
                rtnval = ColumnFrame(columns={}, row_count=0, order=[])
                return rtnval
            order = list(row_buffer[0].keys())
            cols = ColumnBuilder.build(rows=row_buffer)
            row_count = len(row_buffer)

        path, batch, _ = self.plan(source_cols=order)

        if path == "vector":
            order_out = list(order)
            for stmt in batch:
                evaluated = VectorEvaluator.evaluate(node=stmt.expr,
                                                     cols=cols)
                if np.ndim(evaluated) == 0:
                    broadcast = np.full(row_count, evaluated)
                else:
                    broadcast = evaluated
                cols[stmt.target] = broadcast
                if stmt.target not in order_out:
                    order_out.append(stmt.target)
            rtnval = ColumnFrame(columns=cols, row_count=row_count,
                                 order=order_out)
        else:
            if row_buffer is None:
                materialized = list(data)
            else:
                materialized = row_buffer
            rtnval = ColumnFrame.from_dicts(rows=self.run(rows=materialized))
        return rtnval
