"""
    .. module:: classifier
        :synopsis: The :class:`Classifier` -- marks each IR statement as
                   vectorizable (``"vector"``) or sequential (``"seq"``).
                   Statements that touch cross-row state, change output
                   cardinality, or depend on sequentially-produced values fall
                   into ``"seq"``.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from typing import Any

from ccai.analysis.statistical.ir.nodes.assignnode import AssignNode
from ccai.analysis.statistical.ir.nodes.autonode import AutoNode
from ccai.analysis.statistical.ir.nodes.binopnode import BinOpNode
from ccai.analysis.statistical.ir.nodes.boolopnode import BoolOpNode
from ccai.analysis.statistical.ir.nodes.colnode import ColNode
from ccai.analysis.statistical.ir.nodes.comparenode import CompareNode
from ccai.analysis.statistical.ir.nodes.constnode import ConstNode
from ccai.analysis.statistical.ir.nodes.deletenode import DeleteNode
from ccai.analysis.statistical.ir.nodes.difnode import DifNode
from ccai.analysis.statistical.ir.nodes.firstlastnode import FirstLastNode
from ccai.analysis.statistical.ir.nodes.ifnode import IfNode
from ccai.analysis.statistical.ir.nodes.lagnode import LagNode
from ccai.analysis.statistical.ir.nodes.outputnode import OutputNode


CROSS_ROW_NODES: tuple = (LagNode, DifNode, FirstLastNode, AutoNode)


class Classifier:
    """
        Walks a list of IR statements and labels each as ``"vector"`` (a
        pure function of the current row) or ``"seq"`` (depends on prior-row
        state or affects output cardinality).
    """

    @classmethod
    def expr_is_sequential(cls, node: Any) -> bool:
        """
            Indicate whether an IR expression reads any cross-row state.

            :param node: An IR expression node.

            :returns: ``True`` when the expression reads cross-row state.
        """
        if isinstance(node, CROSS_ROW_NODES):
            rtnval = True
        elif isinstance(node, (ConstNode, ColNode)):
            rtnval = False
        elif isinstance(node, BinOpNode):
            rtnval = (cls.expr_is_sequential(node=node.left)
                      or cls.expr_is_sequential(node=node.right))
        elif isinstance(node, CompareNode):
            rtnval = (cls.expr_is_sequential(node=node.left)
                      or cls.expr_is_sequential(node=node.right))
        elif isinstance(node, BoolOpNode):
            rtnval = False
            for value in node.values:
                if cls.expr_is_sequential(node=value) is True:
                    rtnval = True
                    break
        else:
            rtnval = True
        return rtnval

    @classmethod
    def classify(cls, stmts: list) -> list[tuple[Any, str]]:
        """
            Classify each statement in ``stmts``.

            :param stmts: A list of IR statement nodes.

            :returns: A list of ``(statement, classification)`` tuples.
        """
        out: list[tuple[Any, str]] = []
        for stmt in stmts:
            if isinstance(stmt, (OutputNode, DeleteNode)):
                out.append((stmt, "seq"))
            elif isinstance(stmt, AssignNode):
                if cls.expr_is_sequential(node=stmt.expr) is True:
                    out.append((stmt, "seq"))
                else:
                    out.append((stmt, "vector"))
            elif isinstance(stmt, IfNode):
                test_seq = cls.expr_is_sequential(node=stmt.test)
                nested = (cls.classify(stmts=stmt.body)
                          + cls.classify(stmts=stmt.orelse))
                has_seq_child = False
                for _, kind in nested:
                    if kind == "seq":
                        has_seq_child = True
                        break
                if test_seq is True or has_seq_child is True:
                    out.append((stmt, "seq"))
                else:
                    out.append((stmt, "vector"))
            else:
                out.append((stmt, "seq"))
        return out

    @classmethod
    def summarize(cls, stmts: list) -> dict:
        """
            Summarize a classification.

            :param stmts: A list of IR statement nodes.

            :returns: A dictionary with totals and a per-statement detail
                      list.
        """
        classified = cls.classify(stmts=stmts)
        vector_count = sum(1 for _, kind in classified if kind == "vector")
        total = len(classified)
        rtnval = {
            "total": total,
            "vector": vector_count,
            "seq": total - vector_count,
            "detail": [(type(s).__name__, kind) for s, kind in classified],
        }
        return rtnval
