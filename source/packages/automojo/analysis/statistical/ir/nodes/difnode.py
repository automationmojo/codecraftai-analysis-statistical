"""
    .. module:: difnode
        :synopsis: The :class:`DifNode` -- a call-site-keyed ``DIF_n``.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from dataclasses import dataclass
from typing import Any

from automojo.analysis.statistical.ir.nodes.irnode import IrNode


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
