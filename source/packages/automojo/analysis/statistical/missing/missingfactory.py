"""
    .. module:: missingfactory
        :synopsis: Module-level constants and helper for obtaining
                   :class:`Missing` instances.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from automojo.analysis.statistical.missing.missing import Missing


MISSING: Missing = Missing("")


def missing(tag: str = "") -> Missing:
    """
        Look up a missing value by tag.

        :param tag: An empty string for the plain missing, ``"_"`` for the
                    underscore missing, or a single letter ``A`` through ``Z``
                    for a special missing.

        :returns: The cached :class:`Missing` instance for the tag.
    """
    if tag.isalpha():
        normalized = tag.upper()
    else:
        normalized = tag

    rtnval = Missing(normalized)
    return rtnval
