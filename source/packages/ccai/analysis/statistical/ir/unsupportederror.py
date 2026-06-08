"""
    .. module:: unsupportederror
        :synopsis: The :class:`UnsupportedError` exception -- raised when the
                   AST lowerer encounters logic outside the supported
                   sublanguage. Callers fall back to running the original
                   callable on the reference engine when this is raised.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from ccai.errors.exceptions import NotSupportedError


class UnsupportedError(NotSupportedError):
    """
        Raised when an AST shape is outside the IR sublanguage.

        Extends :class:`ccai.errors.exceptions.NotSupportedError` so
        callers across the suite handle "this code path isn't supported here"
        with a single exception family.
    """
