"""
    .. module:: deletenode
        :synopsis: The :class:`DeleteNode` -- explicit ``pdv.delete()``.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from dataclasses import dataclass

from automojo.analysis.statistical.ir.nodes.irnode import IrNode


@dataclass
class DeleteNode(IrNode):
    """
        Suppress this row's BOTTOM emission.
    """
