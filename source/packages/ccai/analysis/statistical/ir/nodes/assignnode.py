"""
    .. module:: assignnode
        :synopsis: The :class:`AssignNode` -- the IR's only mutating
                   statement (``pdv['target'] = expr``).

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from dataclasses import dataclass
from typing import Any

from ccai.analysis.statistical.ir.nodes.irnode import IrNode


@dataclass
class AssignNode(IrNode):
    """
        Assignment statement.

        :ivar target: The PDV variable name to assign.
        :ivar expr: The expression node producing the new value.
    """

    target: str
    expr: Any
