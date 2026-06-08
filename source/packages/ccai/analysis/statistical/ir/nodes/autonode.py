"""
    .. module:: autonode
        :synopsis: The :class:`AutoNode` -- engine-managed automatic
                   variables (``_N_`` / ``eof``).

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from dataclasses import dataclass

from ccai.analysis.statistical.ir.nodes.irnode import IrNode


@dataclass
class AutoNode(IrNode):
    """
        Read an engine-managed automatic value such as ``_N_`` or ``eof``.
    """

    name: str
