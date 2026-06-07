"""
    .. module:: colnode
        :synopsis: The :class:`ColNode` -- a read of a current-row PDV
                   variable by name.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from dataclasses import dataclass

from ccai.analysis.statistical.ir.nodes.irnode import IrNode


@dataclass
class ColNode(IrNode):
    """
        Read a PDV variable by name (the IR-level ``pdv['x']`` expression).
    """

    name: str
