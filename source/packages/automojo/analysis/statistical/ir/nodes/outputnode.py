"""
    .. module:: outputnode
        :synopsis: The :class:`OutputNode` -- explicit ``pdv.output()``.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from dataclasses import dataclass

from automojo.analysis.statistical.ir.nodes.irnode import IrNode


@dataclass
class OutputNode(IrNode):
    """
        Explicit emit of the current PDV snapshot to the output buffer.
    """
