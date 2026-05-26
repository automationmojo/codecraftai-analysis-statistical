"""
    .. module:: ifnode
        :synopsis: The :class:`IfNode` -- a structured if/else statement.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from dataclasses import dataclass, field
from typing import Any

from automojo.analysis.statistical.ir.nodes.irnode import IrNode


@dataclass
class IfNode(IrNode):
    """
        A two-branch if/else.

        :ivar test: The condition expression.
        :ivar body: Statements to run when the test is truthy.
        :ivar orelse: Statements to run when the test is falsy.
    """

    test: Any
    body: list = field(default_factory=list)
    orelse: list = field(default_factory=list)
