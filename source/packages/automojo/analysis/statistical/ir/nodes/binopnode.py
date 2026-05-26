"""
    .. module:: binopnode
        :synopsis: The :class:`BinOpNode` -- a binary arithmetic expression.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from dataclasses import dataclass
from typing import Any

from automojo.analysis.statistical.ir.nodes.irnode import IrNode


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
