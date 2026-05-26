"""
    .. module:: compareopmap
        :synopsis: The :class:`CompareOpMap` -- lookup from Python AST
                   comparison-operator classes to their string codes.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


import ast


class CompareOpMap:
    """
        Lookup table from AST comparison-operator classes to operator strings.
    """

    OPERATORS = {
        ast.Eq: "==",
        ast.NotEq: "!=",
        ast.Lt: "<",
        ast.LtE: "<=",
        ast.Gt: ">",
        ast.GtE: ">=",
    }

    @classmethod
    def lookup(cls, op_node: ast.AST) -> str | None:
        """
            Look up the operator string for a comparison AST operator node.

            :param op_node: An instance of an AST comparison-operator class.

            :returns: The operator string, or ``None`` when unsupported.
        """
        rtnval = cls.OPERATORS.get(type(op_node))
        return rtnval
