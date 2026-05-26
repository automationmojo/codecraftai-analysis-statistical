"""
    .. module:: arithmeticops
        :synopsis: The :class:`ArithmeticOps` lookup table -- maps IR
                   arithmetic operator strings to numpy ufuncs for the
                   vectorized executor.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


import numpy as np
from collections.abc import Callable


class ArithmeticOps:
    """
        Lookup table from IR arithmetic operator strings to numpy ufuncs.
    """

    OPERATORS = {
        "+":  np.add,
        "-":  np.subtract,
        "*":  np.multiply,
        "/":  np.divide,
        "%":  np.mod,
        "//": np.floor_divide,
        "**": np.power,
    }

    @classmethod
    def lookup(cls, op: str) -> Callable | None:
        """
            Look up the numpy ufunc for an operator string.

            :param op: The IR operator string.

            :returns: A numpy ufunc, or ``None`` when unsupported.
        """
        rtnval = cls.OPERATORS.get(op)
        return rtnval
