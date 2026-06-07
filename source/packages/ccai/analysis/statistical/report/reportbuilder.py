"""
    .. module:: reportbuilder
        :synopsis: The :class:`ReportBuilder` -- produces a :class:`Report`
                   for a user logic function. Uses the same lowerer the
                   executor uses, then narrates per-statement reasons.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from typing import Any
from collections.abc import Callable

from ccai.analysis.statistical.execution.scheduler import Scheduler
from ccai.analysis.statistical.ir.astlowerer import lower
from ccai.analysis.statistical.ir.nodes.assignnode import AssignNode
from ccai.analysis.statistical.ir.nodes.deletenode import DeleteNode
from ccai.analysis.statistical.ir.nodes.ifnode import IfNode
from ccai.analysis.statistical.ir.nodes.outputnode import OutputNode
from ccai.analysis.statistical.ir.unsupportederror import UnsupportedError
from ccai.analysis.statistical.report.crossrowlabeler import CrossRowLabeler
from ccai.analysis.statistical.report.line import Line
from ccai.analysis.statistical.report.report import Report


class ReportBuilder:
    """
        Build :class:`Report` instances. Uses the same scheduler the executor
        does, so what the advisor says matches what the executor actually
        runs.
    """

    @classmethod
    def report(cls, logic: Callable[[Any], None],
               source_cols: list[str],
               retain: set[str] | None = None) -> Report:
        """
            Build a :class:`Report` for ``logic`` over ``source_cols``.

            :param logic: The user logic callable.
            :param source_cols: The names of the source columns.
            :param retain: Optional set of retained column names; these are
                           treated as loop-produced for blocker computation.

            :returns: A :class:`Report` instance.
        """
        if retain is None:
            retained: set[str] = set()
        else:
            retained = set(retain)

        try:
            stmts = lower(logic=logic)
        except UnsupportedError as ex:
            cause = str(ex)[:70]
            rtnval = Report(path="fallback", lines=[], unsupported=cause)
            return rtnval

        available = set(source_cols) - retained
        lines: list[Line] = []
        for index, stmt in enumerate(stmts):
            cls._narrate(index=index, stmt=stmt, available=available,
                         lines=lines)

        all_batch = True
        for line in lines:
            if line.klass != "batch":
                all_batch = False
                break

        if all_batch is True and len(lines) > 0:
            path = "vector"
        else:
            path = "hybrid"

        rtnval = Report(path=path, lines=lines)
        return rtnval

    @classmethod
    def _narrate(cls, index: int, stmt: Any, available: set[str],
                 lines: list[Line]) -> None:
        """
            Add a :class:`Line` for ``stmt`` to ``lines`` and update
            ``available``.

            :param index: The statement index.
            :param stmt: The IR statement node.
            :param available: The mutable available-columns set.
            :param lines: The accumulating output list.

            :returns: ``None``
        """
        if isinstance(stmt, AssignNode):
            cross_row = CrossRowLabeler.labels(node=stmt.expr)
            if len(cross_row) > 0:
                reason = "reads cross-row state: " + ", ".join(cross_row)
                lines.append(Line(index=index, stmt="assign", klass="loop",
                                  category="irreducible", reason=reason,
                                  blockers=list(cross_row)))
                available.discard(stmt.target)
            else:
                read_names = Scheduler.reads(node=stmt.expr)
                blockers = sorted(read_names - available)
                if len(blockers) > 0:
                    reason = "depends on sequential value(s): {}".format(blockers)
                    lines.append(Line(index=index, stmt="assign", klass="loop",
                                      category="dependency", reason=reason,
                                      blockers=blockers))
                    available.discard(stmt.target)
                else:
                    lines.append(Line(index=index, stmt="assign", klass="batch",
                                      category="batch",
                                      reason="pure current-row arithmetic"))
                    available.add(stmt.target)
        elif isinstance(stmt, IfNode):
            cross_row = CrossRowLabeler.labels(node=stmt.test)
            read_names = Scheduler.reads(node=stmt.test)
            dep_blockers = sorted(read_names - available)
            if len(cross_row) > 0:
                reason = "conditional on cross-row state: " + ", ".join(cross_row)
                lines.append(Line(index=index, stmt="if", klass="loop",
                                  category="irreducible", reason=reason,
                                  blockers=list(cross_row)))
            elif len(dep_blockers) > 0:
                reason = "conditional on sequential value(s): {}".format(dep_blockers)
                lines.append(Line(index=index, stmt="if", klass="loop",
                                  category="dependency", reason=reason,
                                  blockers=dep_blockers))
            else:
                lines.append(Line(index=index, stmt="if", klass="loop",
                                  category="tool-limited",
                                  reason="vectorizable conditional (runs in loop for now)"))
            for assigned_name in Scheduler.assigned(stmt=stmt):
                available.discard(assigned_name)
        elif isinstance(stmt, (OutputNode, DeleteNode)):
            label = type(stmt).__name__.lower().replace("node", "")
            lines.append(Line(index=index, stmt=label, klass="loop",
                              category="cardinality",
                              reason="changes output cardinality"))
        return


def report(logic: Callable[[Any], None], source_cols: list[str],
           retain: set[str] | None = None) -> Report:
    """
        Convenience function for :meth:`ReportBuilder.report`.

        :param logic: The user logic callable.
        :param source_cols: The source column names.
        :param retain: Optional retained column names.

        :returns: A :class:`Report` instance.
    """
    rtnval = ReportBuilder.report(logic=logic, source_cols=source_cols,
                                  retain=retain)
    return rtnval
