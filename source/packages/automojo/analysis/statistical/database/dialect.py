"""
    .. module:: dialect
        :synopsis: The :class:`Dialect` base class. A dialect bundles a
                   :class:`TypeMap` (used by the read path) and a NAME_TABLE
                   (used by dialect-named declarations).

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"



from automojo.analysis.statistical.database.typemap import TypeMap


NUMERIC_SENTINEL: str = "numeric"


class Dialect:
    """
        Base class for a database dialect. Subclasses set:

        * ``NAME`` -- canonical dialect identifier (lowercase).
        * ``TYPE_MAP`` -- a :class:`TypeMap` keyed by driver type-code.
        * ``NAME_TABLE`` -- a ``{canonical_typename: (kind, fmt)}`` mapping
          for dialect-named declaration; ``kind`` is one of
          :data:`NUMERIC_SENTINEL`, ``"num"``, or ``"char"``.
    """

    NAME: str = ""
    TYPE_MAP: TypeMap | None = None
    NAME_TABLE: dict = {}

    @classmethod
    def resolve_named(cls, type_name: str) -> tuple[str, str | None] | None:
        """
            Look up a canonical dialect type name in this dialect's
            ``NAME_TABLE``.

            :param type_name: Upper-cased canonical dialect type name (for
                              example ``"NUMBER"``, ``"VARCHAR2"``).

            :returns: The ``(kind, fmt)`` tuple, or ``None`` when the name is
                      not present in this dialect.
        """
        rtnval = cls.NAME_TABLE.get(type_name)
        return rtnval
