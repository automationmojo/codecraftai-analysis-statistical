"""
    .. module:: compiledstep
        :synopsis: The :class:`CompiledStep` -- top-level execution
                   coordinator. Plans an execution path (``vector`` |
                   ``hybrid`` | ``fallback``) and runs rows through it.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


import numpy as np
from typing import Any
from collections.abc import Callable

from automojo.analysis.statistical.engine.observationengine import ObservationEngine
from automojo.analysis.statistical.execution.columnbuilder import ColumnBuilder
from automojo.analysis.statistical.execution.scheduler import Scheduler
from automojo.analysis.statistical.execution.vectorevaluator import VectorEvaluator
from automojo.analysis.statistical.ir.astlowerer import lower
from automojo.analysis.statistical.ir.irinterpreter import ir_logic
from automojo.analysis.statistical.ir.unsupportederror import UnsupportedError
from automojo.analysis.statistical.readers.setreader import SetReader


class CompiledStep:
    """
        Coordinates execution of a user logic function. On construction it
        attempts to lower the function to IR. At ``run`` time it decides
        among three execution paths:

        * ``"vector"``   -- no row loop; every column computed as an array.
        * ``"hybrid"``   -- batch-compute what can be batched, then run the
                            sequential residual through the reference engine.
        * ``"fallback"`` -- lowering failed, so run the original callable
                            through the reference engine.
    """

    def __init__(self, logic: Callable[[Any], None],
                 by: list | None = None,
                 retain: dict | None = None) -> None:
        """
            Initialize the :class:`CompiledStep`.

            :param logic: The user logic callable.
            :param by: Optional BY-key column names.
            :param retain: Optional RETAIN map for the reference engine.

            :returns: ``None``
        """
        self._logic = logic
        if by is None:
            self._by = []
        else:
            self._by = list(by)
        if retain is None:
            self._retain = {}
        else:
            self._retain = dict(retain)
        try:
            self.stmts = lower(logic=logic)
            self.mode = "ir"
        except UnsupportedError:
            self.stmts = None
            self.mode = "fallback"
        return

    def plan(self, source_cols: list[str]) -> tuple[str, list | None, list | None]:
        """
            Pick an execution path for the given source columns.

            :param source_cols: The names of the source columns.

            :returns: A tuple ``(path, batch, loop)``. ``path`` is one of
                      ``"vector"``, ``"hybrid"``, ``"fallback"``. ``batch``
                      and ``loop`` are ``None`` on the fallback path.
        """
        if self.mode == "fallback":
            rtnval = ("fallback", None, None)
        else:
            batch, loop = Scheduler.schedule(stmts=self.stmts,
                                             source_cols=source_cols)
            if len(loop) == 0:
                rtnval = ("vector", batch, loop)
            else:
                rtnval = ("hybrid", batch, loop)
        return rtnval

    def run(self, rows: list[dict]) -> list[dict]:
        """
            Run the step over ``rows`` and return the output rows.

            :param rows: The input row list.

            :returns: The output row list.
        """
        if len(rows) == 0:
            rtnval: list[dict] = []
        else:
            source_cols = list(rows[0].keys())
            path, batch, loop = self.plan(source_cols=source_cols)

            if path == "fallback":
                reader = SetReader(source=rows, by=self._by)
                engine = ObservationEngine(reader=reader, logic=self._logic,
                                           by=self._by, retain=self._retain)
                rtnval = list(engine)
            else:
                cols = ColumnBuilder.build(rows=rows)
                row_count = len(rows)
                for stmt in batch:
                    evaluated = VectorEvaluator.evaluate(node=stmt.expr,
                                                         cols=cols)
                    if np.ndim(evaluated) == 0:
                        broadcast = np.full(row_count, evaluated)
                    else:
                        broadcast = evaluated
                    cols[stmt.target] = broadcast

                if path == "vector":
                    column_order = list(cols.keys())
                    out_rows: list[dict] = []
                    for index in range(row_count):
                        materialized = {name: ColumnBuilder.to_scalar(value=cols[name][index])
                                        for name in column_order}
                        out_rows.append(materialized)
                    rtnval = out_rows
                else:
                    column_order = list(cols.keys())

                    def augmented_rows():
                        for index in range(row_count):
                            row = {name: ColumnBuilder.to_scalar(value=cols[name][index])
                                   for name in column_order}
                            yield row

                    reader = SetReader(source=augmented_rows(), by=self._by)
                    engine = ObservationEngine(reader=reader,
                                               logic=ir_logic(stmts=loop),
                                               by=self._by,
                                               retain=self._retain)
                    rtnval = list(engine)
        return rtnval
