"""
    .. module:: constnode
        :synopsis: The :class:`ConstNode` -- a literal value in the IR.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from dataclasses import dataclass
from typing import Any

from ccai.analysis.statistical.ir.nodes.irnode import IrNode


@dataclass
class ConstNode(IrNode):
    """
        A literal constant. ``value`` carries the Python value the AST
        produced.
    """

    value: Any
