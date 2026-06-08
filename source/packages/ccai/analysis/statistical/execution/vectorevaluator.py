"""
    .. module:: vectorevaluator
        :synopsis: The :class:`VectorEvaluator` -- evaluates IR expressions
                   over whole-column ``numpy`` arrays for the vectorized
                   execution path.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


import numpy as np
from typing import Any

from ccai.analysis.statistical.execution.arithmeticops import ArithmeticOps
from ccai.analysis.statistical.execution.compareops import CompareOps
from ccai.analysis.statistical.ir.nodes.binopnode import BinOpNode
from ccai.analysis.statistical.ir.nodes.boolopnode import BoolOpNode
from ccai.analysis.statistical.ir.nodes.colnode import ColNode
from ccai.analysis.statistical.ir.nodes.comparenode import CompareNode
from ccai.analysis.statistical.ir.nodes.constnode import ConstNode
from ccai.analysis.statistical.ir.unsupportederror import UnsupportedError


class VectorEvaluator:
    """
        Evaluate IR expressions over column arrays. Used only for the
        vectorizable subset of the IR -- cross-row nodes (Lag/Dif/FirstLast/
        Auto) are never seen here.
    """

    @classmethod
    def evaluate(cls, node: Any, cols: dict) -> Any:
        """
            Evaluate ``node`` against ``cols``.

            :param node: An IR expression node.
            :param cols: A mapping of ``{name: ndarray}``.

            :returns: A numpy array (or scalar for pure ``Const`` nodes).
            :raises UnsupportedError: When ``node`` cannot be vectorized.
        """
        if isinstance(node, ConstNode):
            rtnval = node.value
        elif isinstance(node, ColNode):
            rtnval = cols[node.name]
        elif isinstance(node, BinOpNode):
            left_val = cls.evaluate(node=node.left, cols=cols)
            right_val = cls.evaluate(node=node.right, cols=cols)
            ufunc = ArithmeticOps.lookup(op=node.op)
            rtnval = ufunc(left_val, right_val)
        elif isinstance(node, CompareNode):
            left_val = cls.evaluate(node=node.left, cols=cols)
            right_val = cls.evaluate(node=node.right, cols=cols)
            ufunc = CompareOps.lookup(op=node.op)
            rtnval = ufunc(left_val, right_val)
        elif isinstance(node, BoolOpNode):
            values = [cls.evaluate(node=v, cols=cols) for v in node.values]
            out = values[0]
            for follow in values[1:]:
                if node.op == "and":
                    out = np.logical_and(out, follow)
                else:
                    out = np.logical_or(out, follow)
            rtnval = out
        else:
            err_msg = "Unsupported expression for vectorization: " + repr(node)
            raise UnsupportedError(err_msg)
        return rtnval
