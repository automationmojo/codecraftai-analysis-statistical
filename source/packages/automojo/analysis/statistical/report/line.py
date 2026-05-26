"""
    .. module:: line
        :synopsis: The :class:`Line` -- one row of a migration / optimization
                   report (one IR statement, one classification, one reason).

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from dataclasses import dataclass, field


@dataclass
class Line:
    """
        One report row.

        :ivar index: 0-based statement index.
        :ivar stmt: A short text label for the statement (``"assign"``,
                    ``"if"``, ``"output"``, ``"delete"``).
        :ivar klass: ``"batch"`` (vectorized) or ``"loop"`` (sequential).
        :ivar category: One of ``"batch"``, ``"irreducible"``,
                        ``"tool-limited"``, ``"dependency"``, ``"cardinality"``.
        :ivar reason: A human-readable explanation.
        :ivar blockers: Identifiers that prevent vectorization (sequential
                        inputs, or cross-row sources).
    """

    index: int
    stmt: str
    klass: str
    category: str
    reason: str
    blockers: list = field(default_factory=list)
