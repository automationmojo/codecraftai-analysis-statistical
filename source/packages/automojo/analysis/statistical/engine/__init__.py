"""
    The engine subpackage. Importing it guarantees the core ``num`` / ``char``
    storage types and the built-in formats and informats are registered.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


import automojo.analysis.statistical.formats  # noqa: F401  (bootstrap built-ins)
import automojo.analysis.statistical.types  # noqa: F401  (bootstrap core types)
