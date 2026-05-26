"""
    .. module:: autonode
        :synopsis: The :class:`AutoNode` -- engine-managed automatic
                   variables (``_N_`` / ``eof``).

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from dataclasses import dataclass

from automojo.analysis.statistical.ir.nodes.irnode import IrNode


@dataclass
class AutoNode(IrNode):
    """
        Read an engine-managed automatic value such as ``_N_`` or ``eof``.
    """

    name: str
