"""
    .. module:: numericresolver
        :synopsis: The :class:`NumericResolver` -- shared by the database read
                   path and the dialect-named declaration path. Routes a
                   numeric column to ``num`` (float64) or ``decimal`` (exact)
                   based on its declared precision.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"



from automojo.analysis.statistical.types.constants import DECIMAL, NUM


class NumericResolver:
    """
        Decide whether a column should be stored as ``num`` (float64) or
        ``decimal`` (exact arbitrary precision) given its declared precision.
        Float64 holds ~15-16 significant digits exactly; beyond that, exactness
        requires Decimal storage.
    """

    FLOAT64_SAFE_DIGITS: int = 15

    @classmethod
    def resolve(cls, precision: int | None) -> tuple[str, int | None, str | None]:
        """
            Pick a storage triple for a numeric column.

            :param precision: The declared precision. ``None`` means
                              "unspecified" and routes to ``num``.

            :returns: A tuple ``(stype, length, fmt)``. ``decimal`` returns
                      ``length=None`` so the storage type's default applies.
        """
        if precision is not None and precision > cls.FLOAT64_SAFE_DIGITS:
            rtnval = (DECIMAL, None, None)
        else:
            rtnval = (NUM, 8, None)
        return rtnval

    @classmethod
    def from_description(cls, description_entry: tuple) -> tuple[str, int | None, str | None]:
        """
            Read-path resolver: pull precision out of a PEP 249 cursor
            ``description`` entry and route it through :meth:`resolve`.

            :param description_entry: One element of ``cursor.description``,
                                      ``(name, type_code, display_size,
                                      internal_size, precision, scale,
                                      null_ok)``.

            :returns: A ``(stype, length, fmt)`` triple.
        """
        precision = description_entry[4]
        rtnval = cls.resolve(precision=precision)
        return rtnval
