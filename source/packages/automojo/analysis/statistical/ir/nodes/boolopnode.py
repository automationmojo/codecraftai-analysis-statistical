"""
    .. module:: boolopnode
        :synopsis: The :class:`BoolOpNode` -- a chained boolean expression.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from dataclasses import dataclass, field

from automojo.analysis.statistical.ir.nodes.irnode import IrNode


@dataclass
class BoolOpNode(IrNode):
    """
        A boolean ``and`` / ``or`` chain.

        :ivar op: Either ``"and"`` or ``"or"``.
        :ivar values: The operand nodes in order.
    """

    op: str
    values: list = field(default_factory=list)
