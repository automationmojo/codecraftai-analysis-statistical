"""
    .. module:: boolopmap
        :synopsis: The :class:`BoolOpMap` -- lookup from Python AST boolean
                   operator classes to their string codes.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


import ast


class BoolOpMap:
    """
        Lookup table from AST boolean-operator classes to operator strings.
    """

    OPERATORS = {
        ast.And: "and",
        ast.Or: "or",
    }

    @classmethod
    def lookup(cls, op_node: ast.AST) -> str | None:
        """
            Look up the operator string for a boolean AST operator node.

            :param op_node: An instance of an AST boolean-operator class.

            :returns: The operator string, or ``None`` when unsupported.
        """
        rtnval = cls.OPERATORS.get(type(op_node))
        return rtnval
