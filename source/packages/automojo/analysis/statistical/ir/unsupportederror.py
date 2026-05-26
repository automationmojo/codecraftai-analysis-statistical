"""
    .. module:: unsupportederror
        :synopsis: The :class:`UnsupportedError` exception -- raised when the
                   AST lowerer encounters logic outside the supported
                   sublanguage. Callers fall back to running the original
                   callable on the reference engine when this is raised.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from automojo.errors.exceptions import NotSupportedError


class UnsupportedError(NotSupportedError):
    """
        Raised when an AST shape is outside the IR sublanguage.

        Extends :class:`automojo.errors.exceptions.NotSupportedError` so
        callers across the suite handle "this code path isn't supported here"
        with a single exception family.
    """
