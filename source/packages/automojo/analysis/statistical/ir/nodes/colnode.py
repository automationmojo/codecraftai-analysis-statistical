"""
    .. module:: colnode
        :synopsis: The :class:`ColNode` -- a read of a current-row PDV
                   variable by name.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from dataclasses import dataclass

from automojo.analysis.statistical.ir.nodes.irnode import IrNode


@dataclass
class ColNode(IrNode):
    """
        Read a PDV variable by name (the IR-level ``pdv['x']`` expression).
    """

    name: str
