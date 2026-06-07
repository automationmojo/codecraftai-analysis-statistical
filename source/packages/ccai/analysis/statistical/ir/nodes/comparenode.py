"""
    .. module:: comparenode
        :synopsis: The :class:`CompareNode` -- a single-operator comparison
                   expression.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from dataclasses import dataclass
from typing import Any

from ccai.analysis.statistical.ir.nodes.irnode import IrNode


@dataclass
class CompareNode(IrNode):
    """
        A two-operand comparison.

        :ivar op: One of ``==``, ``!=``, ``<``, ``<=``, ``>``, ``>=``.
        :ivar left: The left operand node.
        :ivar right: The right operand node.
    """

    op: str
    left: Any
    right: Any
