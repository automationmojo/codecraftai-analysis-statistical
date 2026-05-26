"""
    .. module:: firstlastnode
        :synopsis: The :class:`FirstLastNode` -- a BY-group boundary test
                   (``pdv.first['x']`` / ``pdv.last['x']``).

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from dataclasses import dataclass

from automojo.analysis.statistical.ir.nodes.irnode import IrNode


@dataclass
class FirstLastNode(IrNode):
    """
        Read a BY-group boundary flag.

        :ivar which: Either ``"first"`` or ``"last"``.
        :ivar by: The BY-key variable name being tested.
    """

    which: str
    by: str
