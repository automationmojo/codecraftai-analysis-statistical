"""
    .. module:: missing
        :synopsis: The :class:`Missing` value class. Represents SAS missing
                   values -- plain (.), underscore (._), and special (.A-.Z) --
                   with SAS ordering semantics.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from typing import Any


class Missing:
    """
        A SAS missing value. Three subfamilies exist:

        * underscore missing -- ``._``
        * plain missing      -- ``.``
        * special missing    -- ``.A`` through ``.Z``

        Ordering follows SAS rules: ``._ < . < .A < .B < ... < .Z < every real number``.

        Instances are cached by tag, so ``Missing("A") is Missing("A")``.
    """

    __slots__ = ("tag",)

    _cache: dict = {}

    def __new__(cls, tag: str = ""):
        cached = cls._cache.get(tag)
        if cached is not None:
            return cached
        obj = super().__new__(cls)
        obj.tag = tag
        cls._cache[tag] = obj
        return obj

    def order(self) -> int:
        """
            Return the SAS ordering rank for this missing value.

            :returns: An integer rank: ``-2`` for ``._``, ``-1`` for the plain
                      missing, and ``0..25`` for ``.A..Z``.
        """
        if self.tag == "_":
            rtnval = -2
        elif self.tag == "":
            rtnval = -1
        else:
            rtnval = ord(self.tag) - ord("A")
        return rtnval

    def __repr__(self) -> str:
        rtnval = "._" if self.tag == "_" else ("." + self.tag)
        return rtnval

    def __eq__(self, other: Any) -> bool:
        rtnval = isinstance(other, Missing) and other.tag == self.tag
        return rtnval

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, Missing):
            rtnval = self.order() < other.order()
        else:
            rtnval = True
        return rtnval

    def __le__(self, other: Any) -> bool:
        rtnval = self == other or self < other
        return rtnval

    def __gt__(self, other: Any) -> bool:
        rtnval = not self.__le__(other)
        return rtnval

    def __ge__(self, other: Any) -> bool:
        rtnval = not self.__lt__(other)
        return rtnval

    def __hash__(self) -> int:
        rtnval = hash(("__missing__", self.tag))
        return rtnval
