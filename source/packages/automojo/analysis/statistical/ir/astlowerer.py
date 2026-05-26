"""
    .. module:: astlowerer
        :synopsis: The :class:`AstLowerer` -- lowers a ``def logic(pdv): ...``
                   function's AST into IR nodes drawn from a small, closed
                   sublanguage. Anything outside the sublanguage raises
                   :class:`UnsupportedError`; the executor then falls back to
                   running the original callable on the reference engine.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


import ast
import inspect
import textwrap
from typing import Any

from automojo.analysis.statistical.ir.binopmap import BinOpMap
from automojo.analysis.statistical.ir.boolopmap import BoolOpMap
from automojo.analysis.statistical.ir.compareopmap import CompareOpMap
from automojo.analysis.statistical.ir.nodes.assignnode import AssignNode
from automojo.analysis.statistical.ir.nodes.autonode import AutoNode
from automojo.analysis.statistical.ir.nodes.binopnode import BinOpNode
from automojo.analysis.statistical.ir.nodes.boolopnode import BoolOpNode
from automojo.analysis.statistical.ir.nodes.colnode import ColNode
from automojo.analysis.statistical.ir.nodes.comparenode import CompareNode
from automojo.analysis.statistical.ir.nodes.constnode import ConstNode
from automojo.analysis.statistical.ir.nodes.deletenode import DeleteNode
from automojo.analysis.statistical.ir.nodes.difnode import DifNode
from automojo.analysis.statistical.ir.nodes.firstlastnode import FirstLastNode
from automojo.analysis.statistical.ir.nodes.ifnode import IfNode
from automojo.analysis.statistical.ir.nodes.lagnode import LagNode
from automojo.analysis.statistical.ir.nodes.outputnode import OutputNode
from automojo.analysis.statistical.ir.unsupportederror import UnsupportedError


class AstLowerer(ast.NodeVisitor):
    """
        Lower a single-argument ``logic`` function to a list of IR statements.
        The PDV argument name is whatever the user picked (``pdv`` by
        convention); the lowerer matches references to it positionally.
    """

    def __init__(self, pdv_name: str) -> None:
        """
            Initialize the :class:`AstLowerer`.

            :param pdv_name: The PDV argument name as written in the user
                             function signature.

            :returns: ``None``
        """
        self._pdv_name = pdv_name
        return

    def lower_expr(self, node: ast.AST) -> Any:
        """
            Lower a Python expression AST to an IR expression node.

            :param node: An :mod:`ast` expression node.

            :returns: An IR expression node.
            :raises UnsupportedError: When ``node`` is outside the sublanguage.
        """
        if isinstance(node, ast.Constant):
            rtnval = ConstNode(value=node.value)
        elif isinstance(node, ast.Subscript) and self._is_pdv_first_last(node):
            outer = node
            inner = outer.value
            attribute = inner.attr
            key_text = self._index_str(slice_node=outer.slice)
            rtnval = FirstLastNode(which=attribute, by=key_text)
        elif isinstance(node, ast.Subscript) and self._is_pdv(node.value):
            key_text = self._index_str(slice_node=node.slice)
            rtnval = ColNode(name=key_text)
        elif isinstance(node, ast.Attribute) and self._is_pdv(node.value):
            if node.attr == "n" or node.attr == "eof":
                rtnval = AutoNode(name=node.attr)
            else:
                err_msg = "pdv.{} is not in the supported sublanguage".format(node.attr)
                raise UnsupportedError(err_msg)
        elif isinstance(node, ast.BinOp) and BinOpMap.lookup(node.op) is not None:
            op_text = BinOpMap.lookup(op_node=node.op)
            left_ir = self.lower_expr(node=node.left)
            right_ir = self.lower_expr(node=node.right)
            rtnval = BinOpNode(op=op_text, left=left_ir, right=right_ir)
        elif (isinstance(node, ast.Compare)
              and len(node.ops) == 1
              and CompareOpMap.lookup(node.ops[0]) is not None):
            op_text = CompareOpMap.lookup(op_node=node.ops[0])
            left_ir = self.lower_expr(node=node.left)
            right_ir = self.lower_expr(node=node.comparators[0])
            rtnval = CompareNode(op=op_text, left=left_ir, right=right_ir)
        elif isinstance(node, ast.BoolOp) and BoolOpMap.lookup(node.op) is not None:
            op_text = BoolOpMap.lookup(op_node=node.op)
            values_ir = [self.lower_expr(node=v) for v in node.values]
            rtnval = BoolOpNode(op=op_text, values=values_ir)
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            operand_ir = self.lower_expr(node=node.operand)
            rtnval = BinOpNode(op="*", left=ConstNode(value=-1),
                               right=operand_ir)
        elif isinstance(node, ast.Call):
            rtnval = self._lower_call(node=node)
        else:
            err_msg = "Unsupported expression: " + ast.dump(node)
            raise UnsupportedError(err_msg)
        return rtnval

    def _lower_call(self, node: ast.Call) -> Any:
        """
            Lower a function call -- only ``pdv.lag(...)`` and
            ``pdv.dif(...)`` are recognised.

            :param node: An :class:`ast.Call` node.

            :returns: A :class:`LagNode` or :class:`DifNode`.
            :raises UnsupportedError: For any other call shape.
        """
        func = node.func
        if (isinstance(func, ast.Attribute)
                and self._is_pdv(func.value)
                and (func.attr == "lag" or func.attr == "dif")):
            arg_ir = self.lower_expr(node=node.args[0])
            if len(node.args) > 1:
                depth = node.args[1].value
            else:
                depth = 1
            site_id = func.lineno * 1000 + func.col_offset
            if func.attr == "lag":
                rtnval = LagNode(arg=arg_ir, n=depth, site=site_id)
            else:
                rtnval = DifNode(arg=arg_ir, n=depth, site=site_id)
        else:
            err_msg = "Unsupported call: " + ast.dump(func)
            raise UnsupportedError(err_msg)
        return rtnval

    def lower_stmt(self, node: ast.AST) -> Any:
        """
            Lower a Python statement AST to an IR statement node.

            :param node: An :mod:`ast` statement node.

            :returns: An IR statement node, or ``None`` for ``pass``.
            :raises UnsupportedError: When ``node`` is outside the sublanguage.
        """
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Subscript) and self._is_pdv(target.value):
                target_name = self._index_str(slice_node=target.slice)
                expr_ir = self.lower_expr(node=node.value)
                rtnval = AssignNode(target=target_name, expr=expr_ir)
            else:
                err_msg = "Unsupported assign target: " + ast.dump(target)
                raise UnsupportedError(err_msg)
        elif isinstance(node, ast.If):
            test_ir = self.lower_expr(node=node.test)
            body_ir = [self.lower_stmt(node=s) for s in node.body]
            orelse_ir = [self.lower_stmt(node=s) for s in node.orelse]
            body_filtered = [b for b in body_ir if b is not None]
            orelse_filtered = [b for b in orelse_ir if b is not None]
            rtnval = IfNode(test=test_ir, body=body_filtered,
                            orelse=orelse_filtered)
        elif (isinstance(node, ast.Expr)
              and isinstance(node.value, ast.Constant)
              and isinstance(node.value.value, str)):
            rtnval = None
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            func = node.value.func
            if isinstance(func, ast.Attribute) and self._is_pdv(func.value):
                if func.attr == "output":
                    rtnval = OutputNode()
                elif func.attr == "delete":
                    rtnval = DeleteNode()
                else:
                    err_msg = "Unsupported expression-call: " + ast.dump(func)
                    raise UnsupportedError(err_msg)
            else:
                err_msg = "Unsupported expression-call: " + ast.dump(func)
                raise UnsupportedError(err_msg)
        elif isinstance(node, ast.Pass):
            rtnval = None
        elif isinstance(node, ast.Return) and node.value is None:
            rtnval = None
        else:
            err_msg = "Unsupported statement: " + ast.dump(node)
            raise UnsupportedError(err_msg)
        return rtnval

    def _is_pdv(self, node: ast.AST) -> bool:
        """
            Indicate whether ``node`` is a reference to the PDV argument.

            :param node: An :mod:`ast` node.

            :returns: ``True`` when ``node`` is an ``ast.Name`` whose ``id``
                      matches the PDV argument name.
        """
        rtnval = isinstance(node, ast.Name) and node.id == self._pdv_name
        return rtnval

    def _is_pdv_first_last(self, node: ast.AST) -> bool:
        """
            Indicate whether ``node`` is ``pdv.first[X]`` or ``pdv.last[X]``.

            :param node: An :mod:`ast` node.

            :returns: ``True`` when the shape matches.
        """
        if not isinstance(node, ast.Subscript):
            rtnval = False
        elif not isinstance(node.value, ast.Attribute):
            rtnval = False
        elif not self._is_pdv(node.value.value):
            rtnval = False
        elif node.value.attr != "first" and node.value.attr != "last":
            rtnval = False
        else:
            rtnval = True
        return rtnval

    def _index_str(self, slice_node: ast.AST) -> str:
        """
            Extract a string-literal index from a subscript slice.

            :param slice_node: The AST slice node.

            :returns: The string literal value of the index.
            :raises UnsupportedError: When the slice is not a string literal.
        """
        if isinstance(slice_node, ast.Index):
            inner_node = slice_node.value
        else:
            inner_node = slice_node

        if isinstance(inner_node, ast.Constant) and isinstance(inner_node.value, str):
            rtnval = inner_node.value
        else:
            err_msg = "Unsupported dynamic subscript index"
            raise UnsupportedError(err_msg)
        return rtnval


def lower(logic: Any) -> list:
    """
        Lower a ``def logic(pdv): ...`` function's body into IR statements.

        :param logic: The user's logic function.

        :returns: A list of IR statement nodes.
        :raises UnsupportedError: When the function is not a single-argument
                                  ``def`` or its body uses constructs outside
                                  the sublanguage.
    """
    source = textwrap.dedent(inspect.getsource(logic))
    tree = ast.parse(source).body[0]
    if not isinstance(tree, ast.FunctionDef):
        err_msg = "logic must be a top-level function"
        raise UnsupportedError(err_msg)
    if len(tree.args.args) != 1:
        err_msg = "logic must take exactly one positional argument (the PDV)"
        raise UnsupportedError(err_msg)

    pdv_argname = tree.args.args[0].arg
    lowerer = AstLowerer(pdv_name=pdv_argname)
    stmts_with_none = [lowerer.lower_stmt(node=s) for s in tree.body]
    rtnval = [s for s in stmts_with_none if s is not None]
    return rtnval
