"""
    .. module:: irnode
        :synopsis: The :class:`IrNode` -- a tagging base class for every IR
                   node so callers can do uniform ``isinstance`` checks and
                   so future visitors can dispatch generically.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


class IrNode:
    """
        Base class for every IR node. Holds no state of its own; subclasses
        are dataclasses that record the specific shape of a sublanguage
        construct.
    """
