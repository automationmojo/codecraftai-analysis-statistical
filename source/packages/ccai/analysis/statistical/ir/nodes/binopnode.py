"""
    .. module:: binopnode
        :synopsis: The :class:`BinOpNode` -- a binary arithmetic expression.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from dataclasses import dataclass
from typing import Any

from ccai.analysis.statistical.ir.nodes.irnode import IrNode


@dataclass
class BinOpNode(IrNode):
    """
        A binary arithmetic node.

        :ivar op: One of ``+``, ``-``, ``*``, ``/``, ``%``, ``//``, ``**``.
        :ivar left: The left operand node.
        :ivar right: The right operand node.
    """

    op: str
    left: Any
    right: Any
