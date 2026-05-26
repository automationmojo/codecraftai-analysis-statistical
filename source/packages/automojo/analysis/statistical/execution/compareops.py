"""
    .. module:: compareops
        :synopsis: The :class:`CompareOps` lookup table -- maps IR comparison
                   operator strings to numpy ufuncs.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


import numpy as np
from collections.abc import Callable


class CompareOps:
    """
        Lookup table from IR comparison operator strings to numpy ufuncs.
    """

    OPERATORS = {
        "==": np.equal,
        "!=": np.not_equal,
        "<":  np.less,
        "<=": np.less_equal,
        ">":  np.greater,
        ">=": np.greater_equal,
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
