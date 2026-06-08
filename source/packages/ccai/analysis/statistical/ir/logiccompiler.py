"""
    .. module:: logiccompiler
        :synopsis: The :class:`LogicCompiler` -- top-level entry point that
                   lowers a user logic function to IR when possible and
                   returns a runnable callable. On :class:`UnsupportedError`,
                   it returns the original function (the caller falls back to
                   the reference engine).

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from typing import Any
from collections.abc import Callable

from ccai.analysis.statistical.ir.astlowerer import lower
from ccai.analysis.statistical.ir.irinterpreter import ir_logic
from ccai.analysis.statistical.ir.unsupportederror import UnsupportedError


class LogicCompiler:
    """
        Lower-and-wrap pipeline. Returns the IR-interpreted callable when
        lowering succeeds; returns the original function and ``"fallback"``
        otherwise.
    """

    @classmethod
    def compile(cls, logic: Callable[[Any], None]) -> tuple[Callable[[Any], None], str]:
        """
            Compile a user logic function.

            :param logic: The user logic function ``(pdv) -> None``.

            :returns: A tuple ``(runnable, mode)`` where ``mode`` is ``"ir"``
                      when lowering succeeded and ``"fallback"`` when it did
                      not.
        """
        try:
            stmts = lower(logic=logic)
            runnable = ir_logic(stmts=stmts)
            mode = "ir"
        except UnsupportedError:
            runnable = logic
            mode = "fallback"
        rtnval = (runnable, mode)
        return rtnval


def compile_logic(logic: Callable[[Any], None]) -> tuple[Callable[[Any], None], str]:
    """
        Convenience function for :meth:`LogicCompiler.compile`.

        :param logic: The user logic function.

        :returns: A ``(runnable, mode)`` tuple.
    """
    rtnval = LogicCompiler.compile(logic=logic)
    return rtnval
