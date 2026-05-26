"""
    .. module:: constnode
        :synopsis: The :class:`ConstNode` -- a literal value in the IR.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from dataclasses import dataclass
from typing import Any

from automojo.analysis.statistical.ir.nodes.irnode import IrNode


@dataclass
class ConstNode(IrNode):
    """
        A literal constant. ``value`` carries the Python value the AST
        produced.
    """

    value: Any
