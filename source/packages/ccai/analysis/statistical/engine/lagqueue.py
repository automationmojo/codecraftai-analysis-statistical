"""
    .. module:: lagqueue
        :synopsis: The :class:`LagQueue` class -- a fixed-depth FIFO that
                   powers SAS-style ``LAG_n`` and ``DIF_n`` semantics. Each
                   call-site keeps its own queue, so a conditional LAG only
                   sees values pushed when its branch executed.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from collections import deque
from typing import Any

from ccai.analysis.statistical.missing.missingfactory import MISSING


class LagQueue:
    """
        Fixed-depth FIFO used by LAG/DIF. Pre-seeded with ``MISSING`` so the
        first ``depth`` reads return missing (the SAS convention).
    """

    def __init__(self, depth: int) -> None:
        """
            Initialize the :class:`LagQueue`.

            :param depth: The LAG depth.

            :returns: ``None``
        """
        self.depth = depth
        seed = [MISSING] * depth
        self._buffer: deque = deque(seed, maxlen=depth)
        return

    def push_and_read(self, value: Any) -> Any:
        """
            Push ``value`` onto the back of the queue and return the value
            previously at the front.

            :param value: The new value to enqueue.

            :returns: The value at depth ``depth`` behind.
        """
        front = self._buffer[0]
        self._buffer.append(value)
        rtnval = front
        return rtnval
