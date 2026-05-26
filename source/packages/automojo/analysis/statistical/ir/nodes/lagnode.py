"""
    .. module:: lagnode
        :synopsis: The :class:`LagNode` -- a call-site-keyed ``LAG_n``.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from dataclasses import dataclass
from typing import Any

from automojo.analysis.statistical.ir.nodes.irnode import IrNode


@dataclass
class LagNode(IrNode):
    """
        A ``LAG_n`` reference.

        :ivar arg: The expression node whose value is pushed onto the queue.
        :ivar n: The LAG depth.
        :ivar site: A call-site identifier derived from the AST position
                    (``lineno * 1000 + col_offset``) so two LAGs on different
                    lines never share a queue.
    """

    arg: Any
    n: int
    site: int
