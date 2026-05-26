"""
    .. module:: binopmap
        :synopsis: The :class:`BinOpMap` -- lookup from Python AST operator
                   classes to their string operator codes used by IR
                   :class:`BinOpNode` instances.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


import ast


class BinOpMap:
    """
        Lookup table from AST binary-operator classes to operator strings.
    """

    OPERATORS = {
        ast.Add: "+",
        ast.Sub: "-",
        ast.Mult: "*",
        ast.Div: "/",
        ast.Mod: "%",
        ast.FloorDiv: "//",
        ast.Pow: "**",
    }

    @classmethod
    def lookup(cls, op_node: ast.AST) -> str | None:
        """
            Look up the operator string for a binary AST operator node.

            :param op_node: An instance of an AST operator class
                            (for example :class:`ast.Add`).

            :returns: The operator string, or ``None`` when unsupported.
        """
        rtnval = cls.OPERATORS.get(type(op_node))
        return rtnval
