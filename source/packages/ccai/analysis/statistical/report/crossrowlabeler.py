"""
    .. module:: crossrowlabeler
        :synopsis: The :class:`CrossRowLabeler` -- walks an IR expression and
                   produces short human-readable labels for every cross-row
                   source it touches (``lag(n=N)``, ``dif(n=N)``,
                   ``first.X`` / ``last.X``, ``_NAME_``).

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from typing import Any

from ccai.analysis.statistical.ir.nodes.autonode import AutoNode
from ccai.analysis.statistical.ir.nodes.binopnode import BinOpNode
from ccai.analysis.statistical.ir.nodes.boolopnode import BoolOpNode
from ccai.analysis.statistical.ir.nodes.comparenode import CompareNode
from ccai.analysis.statistical.ir.nodes.difnode import DifNode
from ccai.analysis.statistical.ir.nodes.firstlastnode import FirstLastNode
from ccai.analysis.statistical.ir.nodes.lagnode import LagNode


class CrossRowLabeler:
    """
        Produce short human-readable cross-row source labels for an IR
        expression tree.
    """

    @classmethod
    def labels(cls, node: Any) -> list[str]:
        """
            Walk ``node`` and return labels for cross-row leaves.

            :param node: An IR expression node.

            :returns: A list of label strings.
        """
        out: list[str] = []
        cls._walk(node=node, out=out)
        rtnval = out
        return rtnval

    @classmethod
    def _walk(cls, node: Any, out: list[str]) -> None:
        """
            Recursive walker.

            :param node: An IR expression node.
            :param out: The accumulating output list.

            :returns: ``None``
        """
        if isinstance(node, LagNode):
            out.append("lag(n={})".format(node.n))
        elif isinstance(node, DifNode):
            out.append("dif(n={})".format(node.n))
        elif isinstance(node, FirstLastNode):
            out.append("{}.{}".format(node.which, node.by))
        elif isinstance(node, AutoNode):
            out.append("_{}_".format(node.name))
        elif isinstance(node, BinOpNode):
            cls._walk(node=node.left, out=out)
            cls._walk(node=node.right, out=out)
        elif isinstance(node, CompareNode):
            cls._walk(node=node.left, out=out)
            cls._walk(node=node.right, out=out)
        elif isinstance(node, BoolOpNode):
            for value in node.values:
                cls._walk(node=value, out=out)
        return
