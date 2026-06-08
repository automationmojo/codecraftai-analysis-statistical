"""
    .. module:: outputnode
        :synopsis: The :class:`OutputNode` -- explicit ``pdv.output()``.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from dataclasses import dataclass

from ccai.analysis.statistical.ir.nodes.irnode import IrNode


@dataclass
class OutputNode(IrNode):
    """
        Explicit emit of the current PDV snapshot to the output buffer.
    """
