"""
    .. module:: scheduler
        :synopsis: The :class:`Scheduler` -- forward dataflow pass that
                   splits IR statements into ``(batch, loop)``. A statement
                   is BATCH iff it is classified vector AND all its inputs
                   are batch-available at that point in the program.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from typing import Any

from automojo.analysis.statistical.ir.classifier import Classifier
from automojo.analysis.statistical.ir.nodes.assignnode import AssignNode
from automojo.analysis.statistical.ir.nodes.binopnode import BinOpNode
from automojo.analysis.statistical.ir.nodes.boolopnode import BoolOpNode
from automojo.analysis.statistical.ir.nodes.colnode import ColNode
from automojo.analysis.statistical.ir.nodes.comparenode import CompareNode
from automojo.analysis.statistical.ir.nodes.constnode import ConstNode
from automojo.analysis.statistical.ir.nodes.ifnode import IfNode


class Scheduler:
    """
        Forward dataflow pass over a classified IR. Locally-vectorizable
        statements that read a value produced by a sequential statement are
        demoted into the loop (the value isn't batch-available before the
        loop runs).
    """

    @classmethod
    def reads(cls, node: Any) -> set[str]:
        """
            Collect the column names an IR expression reads.

            :param node: An IR expression node.

            :returns: A set of column names.
        """
        if isinstance(node, ColNode):
            rtnval = {node.name}
        elif isinstance(node, ConstNode):
            rtnval = set()
        elif isinstance(node, BinOpNode):
            rtnval = cls.reads(node=node.left) | cls.reads(node=node.right)
        elif isinstance(node, CompareNode):
            rtnval = cls.reads(node=node.left) | cls.reads(node=node.right)
        elif isinstance(node, BoolOpNode):
            collected: set[str] = set()
            for value in node.values:
                collected = collected | cls.reads(node=value)
            rtnval = collected
        else:
            rtnval = set()
        return rtnval

    @classmethod
    def assigned(cls, stmt: Any) -> set[str]:
        """
            Collect the column names an IR statement assigns.

            :param stmt: An IR statement node.

            :returns: A set of column names.
        """
        if isinstance(stmt, AssignNode):
            rtnval = {stmt.target}
        elif isinstance(stmt, IfNode):
            collected: set[str] = set()
            for nested in stmt.body + stmt.orelse:
                collected = collected | cls.assigned(stmt=nested)
            rtnval = collected
        else:
            rtnval = set()
        return rtnval

    @classmethod
    def schedule(cls, stmts: list, source_cols: list[str]) -> tuple[list, list]:
        """
            Split ``stmts`` into ``(batch, loop)``.

            :param stmts: A list of IR statement nodes.
            :param source_cols: The names of columns available before the
                                first statement runs.

            :returns: A tuple ``(batch, loop)`` of IR statement lists.
        """
        available = set(source_cols)
        batch: list = []
        loop: list = []
        for stmt in stmts:
            if (isinstance(stmt, AssignNode)
                    and Classifier.expr_is_sequential(node=stmt.expr) is False
                    and cls.reads(node=stmt.expr).issubset(available)):
                batch.append(stmt)
                available.add(stmt.target)
            else:
                loop.append(stmt)
                available = available - cls.assigned(stmt=stmt)
        rtnval = (batch, loop)
        return rtnval
