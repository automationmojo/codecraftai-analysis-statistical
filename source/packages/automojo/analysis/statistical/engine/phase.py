"""
    .. module:: phase
        :synopsis: The :class:`Phase` enum -- explicit states of the SAS
                   DATA-step implicit loop. Makes the engine state machine
                   inspectable.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from enum import Enum, auto


class Phase(Enum):
    """
        States of the implicit DATA-step loop.

        * ``TOP_OF_STEP`` -- about to reset non-retained slots and read.
        * ``READ``        -- pulling the next observation from the reader.
        * ``EXECUTE``     -- running user logic over the current PDV.
        * ``BOTTOM``      -- emitting the row if not explicitly deleted /
                             explicitly output.
        * ``DONE``        -- reader is exhausted; iteration ends.
    """

    TOP_OF_STEP = auto()
    READ = auto()
    EXECUTE = auto()
    BOTTOM = auto()
    DONE = auto()
