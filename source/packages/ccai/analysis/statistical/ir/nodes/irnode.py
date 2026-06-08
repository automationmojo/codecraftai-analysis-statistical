"""
    .. module:: irnode
        :synopsis: The :class:`IrNode` -- a tagging base class for every IR
                   node so callers can do uniform ``isinstance`` checks and
                   so future visitors can dispatch generically.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


class IrNode:
    """
        Base class for every IR node. Holds no state of its own; subclasses
        are dataclasses that record the specific shape of a sublanguage
        construct.
    """
