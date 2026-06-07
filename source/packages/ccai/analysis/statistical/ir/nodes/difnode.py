"""
    .. module:: difnode
        :synopsis: The :class:`DifNode` -- a call-site-keyed ``DIF_n``.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from dataclasses import dataclass
from typing import Any

from ccai.analysis.statistical.ir.nodes.irnode import IrNode


@dataclass
class DifNode(IrNode):
    """
        A ``DIF_n`` reference.

        :ivar arg: The expression node whose value is differenced.
        :ivar n: The DIF depth.
        :ivar site: An AST-derived call-site identifier.
    """

    arg: Any
    n: int
    site: int
