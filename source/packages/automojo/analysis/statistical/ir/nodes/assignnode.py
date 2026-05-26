"""
    .. module:: assignnode
        :synopsis: The :class:`AssignNode` -- the IR's only mutating
                   statement (``pdv['target'] = expr``).

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from dataclasses import dataclass
from typing import Any

from automojo.analysis.statistical.ir.nodes.irnode import IrNode


@dataclass
class AssignNode(IrNode):
    """
        Assignment statement.

        :ivar target: The PDV variable name to assign.
        :ivar expr: The expression node producing the new value.
    """

    target: str
    expr: Any
