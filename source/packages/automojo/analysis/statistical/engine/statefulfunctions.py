"""
    .. module:: statefulfunctions
        :synopsis: The :class:`StatefulFunctions` mixin -- hosts the LAG and
                   DIF entry points. State lives in the long-lived engine, so
                   no extra phase is needed; call-site keying preserves SAS
                   LAG-on-the-spot semantics.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


import sys
from typing import Any

from automojo.analysis.statistical.engine.lagqueue import LagQueue
from automojo.analysis.statistical.missing.missing import Missing
from automojo.analysis.statistical.missing.missingfactory import MISSING


class StatefulFunctions:
    """
        Mixin providing the ``lag`` and ``dif`` entry points. The hosting
        engine class must initialize ``self._lag_queues`` (a dict keyed by
        ``(site, depth)``) in its constructor.
    """

    def _site(self, tag: str, depth: int) -> tuple[str, str, int]:
        """
            Compute a call-site identity by walking the stack ``depth`` frames.

            :param tag: A descriptive tag (for example ``"LAG"``).
            :param depth: Stack frames to skip from the caller.

            :returns: A tuple ``(tag, filename, lineno)`` uniquely identifying
                      a textual call-site.
        """
        frame = sys._getframe(depth)
        rtnval = (tag, frame.f_code.co_filename, frame.f_lineno)
        return rtnval

    def lag(self, value: Any, n: int = 1,
            site: tuple | None = None) -> Any:
        """
            Return the value pushed ``n`` calls ago at this call-site.

            :param value: The current row's value to enqueue.
            :param n: The LAG depth (``1`` for ``LAG1``).
            :param site: An explicit call-site identity; ``None`` derives one
                         from the caller's stack frame.

            :returns: The previously enqueued value, or :data:`MISSING` for
                      the first ``n`` calls at the site.
        """
        if site is None:
            site_key = self._site(tag="LAG", depth=2)
        else:
            site_key = site

        queue_key = (site_key, n)
        queue = self._lag_queues.get(queue_key)
        if queue is None:
            queue = LagQueue(depth=n)
            self._lag_queues[queue_key] = queue

        rtnval = queue.push_and_read(value=value)
        return rtnval

    def dif(self, value: Any, n: int = 1) -> Any:
        """
            Return ``value - LAG_n(value)`` at this call-site.

            :param value: The current row's value.
            :param n: The DIF depth.

            :returns: The numeric difference, or :data:`MISSING` when either
                      operand is missing.
        """
        site_key = self._site(tag="DIF", depth=2)
        previous = self.lag(value=value, n=n, site=site_key)
        if isinstance(previous, Missing) or isinstance(value, Missing):
            rtnval = MISSING
        else:
            rtnval = value - previous
        return rtnval
