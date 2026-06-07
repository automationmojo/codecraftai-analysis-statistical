"""
    .. module:: deletenode
        :synopsis: The :class:`DeleteNode` -- explicit ``pdv.delete()``.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from dataclasses import dataclass

from ccai.analysis.statistical.ir.nodes.irnode import IrNode


@dataclass
class DeleteNode(IrNode):
    """
        Suppress this row's BOTTOM emission.
    """
