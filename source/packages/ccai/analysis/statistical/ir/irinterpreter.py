"""
    .. module:: irinterpreter
        :synopsis: The :class:`IrInterpreter` -- a faithful row-loop
                   interpreter over an IR statement list. Used to validate
                   the classifier and lowerer against the reference engine
                   without building a fast path.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from typing import Any
from collections.abc import Callable

from ccai.analysis.statistical.ir.nodes.assignnode import AssignNode
from ccai.analysis.statistical.ir.nodes.autonode import AutoNode
from ccai.analysis.statistical.ir.nodes.binopnode import BinOpNode
from ccai.analysis.statistical.ir.nodes.boolopnode import BoolOpNode
from ccai.analysis.statistical.ir.nodes.colnode import ColNode
from ccai.analysis.statistical.ir.nodes.comparenode import CompareNode
from ccai.analysis.statistical.ir.nodes.constnode import ConstNode
from ccai.analysis.statistical.ir.nodes.deletenode import DeleteNode
from ccai.analysis.statistical.ir.nodes.difnode import DifNode
from ccai.analysis.statistical.ir.nodes.firstlastnode import FirstLastNode
from ccai.analysis.statistical.ir.nodes.ifnode import IfNode
from ccai.analysis.statistical.ir.nodes.lagnode import LagNode
from ccai.analysis.statistical.ir.nodes.outputnode import OutputNode
from ccai.analysis.statistical.ir.unsupportederror import UnsupportedError
from ccai.analysis.statistical.missing.missing import Missing
from ccai.analysis.statistical.missing.missingfactory import MISSING


_ARITH = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "/": lambda a, b: a / b,
    "%": lambda a, b: a % b,
    "//": lambda a, b: a // b,
    "**": lambda a, b: a ** b,
}

_CMP = {
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    "<":  lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">":  lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
}


class IrInterpreter:
    """
        Faithful row-level interpreter over IR. Used by :class:`LogicCompiler`
        to produce a callable that the reference engine can drive in place of
        the original Python function.
    """

    @classmethod
    def eval_expr(cls, node: Any, pdv: Any) -> Any:
        """
            Evaluate an IR expression against an engine PDV.

            :param node: An IR expression node.
            :param pdv: The :class:`ObservationEngine` instance.

            :returns: The evaluated value.
            :raises UnsupportedError: For unrecognised expression nodes.
        """
        if isinstance(node, ConstNode):
            rtnval = node.value
        elif isinstance(node, ColNode):
            rtnval = pdv[node.name]
        elif isinstance(node, AutoNode):
            rtnval = getattr(pdv, node.name)
        elif isinstance(node, FirstLastNode):
            if node.which == "first":
                rtnval = pdv.first[node.by]
            else:
                rtnval = pdv.last[node.by]
        elif isinstance(node, LagNode):
            current = cls.eval_expr(node=node.arg, pdv=pdv)
            rtnval = pdv.lag(value=current, n=node.n, site=node.site)
        elif isinstance(node, DifNode):
            site_key = ("DIF", node.site)
            current = cls.eval_expr(node=node.arg, pdv=pdv)
            previous = pdv.lag(value=current, n=node.n, site=site_key)
            if isinstance(previous, Missing) or isinstance(current, Missing):
                rtnval = MISSING
            else:
                rtnval = current - previous
        elif isinstance(node, BinOpNode):
            left_val = cls.eval_expr(node=node.left, pdv=pdv)
            right_val = cls.eval_expr(node=node.right, pdv=pdv)
            rtnval = _ARITH[node.op](left_val, right_val)
        elif isinstance(node, CompareNode):
            left_val = cls.eval_expr(node=node.left, pdv=pdv)
            right_val = cls.eval_expr(node=node.right, pdv=pdv)
            rtnval = _CMP[node.op](left_val, right_val)
        elif isinstance(node, BoolOpNode):
            evaluated = [cls.eval_expr(node=v, pdv=pdv) for v in node.values]
            if node.op == "and":
                rtnval = all(evaluated)
            else:
                rtnval = any(evaluated)
        else:
            err_msg = "Unsupported IR expression: " + repr(node)
            raise UnsupportedError(err_msg)
        return rtnval

    @classmethod
    def run_stmts(cls, stmts: list, pdv: Any) -> None:
        """
            Execute IR statements against an engine PDV.

            :param stmts: A list of IR statement nodes.
            :param pdv: The :class:`ObservationEngine` instance.

            :returns: ``None``
        """
        for stmt in stmts:
            if isinstance(stmt, AssignNode):
                value = cls.eval_expr(node=stmt.expr, pdv=pdv)
                pdv[stmt.target] = value
            elif isinstance(stmt, IfNode):
                truth = cls.eval_expr(node=stmt.test, pdv=pdv)
                if bool(truth) is True:
                    cls.run_stmts(stmts=stmt.body, pdv=pdv)
                else:
                    cls.run_stmts(stmts=stmt.orelse, pdv=pdv)
            elif isinstance(stmt, OutputNode):
                pdv.output()
            elif isinstance(stmt, DeleteNode):
                pdv.delete()
        return


def ir_logic(stmts: list) -> Callable[[Any], None]:
    """
        Turn a list of IR statements into a ``logic(pdv)`` callable.

        :param stmts: The IR statements.

        :returns: A callable suitable for :class:`ObservationEngine`.
    """
    def runner(pdv: Any) -> None:
        IrInterpreter.run_stmts(stmts=stmts, pdv=pdv)
        return
    rtnval = runner
    return rtnval
