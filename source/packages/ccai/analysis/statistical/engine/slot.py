"""
    .. module:: slot
        :synopsis: The :class:`Slot` class -- a single typed register in the
                   Program Data Vector. Carries
                   ``(stype, length, fmt, informat, value, retain)`` for one
                   variable.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"



from ccai.analysis.statistical.types.constants import NUM
from ccai.analysis.statistical.types.typeregistry import TypeRegistry


class Slot:
    """
        A typed register in the Program Data Vector.

        Holds the engine state for a single variable: its storage type, fixed
        storage length, its output format and input informat (both optional),
        the retain flag, and the current value.
    """

    __slots__ = ("stype", "length", "fmt", "informat", "value", "retain")

    def __init__(self, stype: str, length: int, fmt: str | None = None,
                 informat: str | None = None, retain: bool = False) -> None:
        """
            Initialize the :class:`Slot`.

            :param stype: The storage-type name (for example ``NUM``).
            :param length: The fixed storage length.
            :param fmt: Default output format spec for this slot.
            :param informat: Default input informat spec for this slot.
            :param retain: ``True`` when the slot value must survive the
                           top-of-step reset.

            :returns: ``None``
        """
        self.stype = stype
        self.length = length
        self.fmt = fmt
        self.informat = informat
        self.retain = retain
        handler = TypeRegistry.get(name=stype)
        if stype == NUM:
            self.value = handler.missing
        else:
            self.value = ""
        return
