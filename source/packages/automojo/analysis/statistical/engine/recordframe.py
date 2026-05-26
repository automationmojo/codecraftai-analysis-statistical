"""
    .. module:: recordframe
        :synopsis: The :class:`RecordFrame` -- the engine's Program Data
                   Vector. A typed register file for the current observation
                   that owns declaration, coercion, the retain/reset rule, and
                   output projection.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from typing import Any

from automojo.analysis.statistical.engine.slot import Slot
from automojo.analysis.statistical.formats.formatregistry import FormatRegistry
from automojo.analysis.statistical.missing.missing import Missing
from automojo.analysis.statistical.missing.missingfactory import MISSING
from automojo.analysis.statistical.types.constants import CHAR, NUM
from automojo.analysis.statistical.types.typeregistry import TypeRegistry


class RecordFrame:
    """
        The Program Data Vector. Holds one :class:`Slot` per declared variable
        in declaration order and owns the load-bearing top-of-step reset rule:
        non-retained slots reset to missing; retained slots survive.
    """

    def __init__(self) -> None:
        """
            Initialize an empty :class:`RecordFrame`.

            :returns: ``None``
        """
        self._slots: dict = {}
        return

    def declare(self, name: str, stype: str = NUM,
                length: int | None = None, fmt: str | None = None,
                informat: str | None = None, retain: bool = False,
                init: Any = None) -> Slot:
        """
            Declare a variable in the PDV.

            :param name: The variable name.
            :param stype: The storage-type name.
            :param length: The fixed storage length; ``None`` uses the
                           registered default for the storage type.
            :param fmt: Default output format spec.
            :param informat: Default input informat spec.
            :param retain: ``True`` to retain across the top-of-step reset.
            :param init: Optional initial value; coerced through the storage
                         type's handler.

            :returns: The newly created :class:`Slot`.
        """
        handler = TypeRegistry.get(name=stype)
        if length is None:
            effective_length = handler.default_length
        else:
            effective_length = length

        slot = Slot(stype=stype, length=effective_length, fmt=fmt,
                    informat=informat, retain=retain)
        if init is not None:
            slot.value = handler.coerce(init, effective_length)
        self._slots[name] = slot
        return slot

    def get(self, name: str) -> Any:
        """
            Read a variable's current value.

            :param name: The variable name.

            :returns: The stored value, or :data:`MISSING` when undeclared.
        """
        slot = self._slots.get(name)
        if slot is None:
            rtnval = MISSING
        else:
            rtnval = slot.value
        return rtnval

    def set(self, name: str, value: Any) -> None:
        """
            Assign a value to a variable, auto-declaring it when first used.

            :param name: The variable name.
            :param value: The value to assign; coerced through the type
                          handler's ``coerce`` callable.

            :returns: ``None``
        """
        slot = self._slots.get(name)
        if slot is None:
            if isinstance(value, Missing):
                inferred_type = NUM
            else:
                inferred_type = TypeRegistry.infer(value=value)

            if inferred_type == CHAR and isinstance(value, str):
                effective_length = len(value)
            else:
                effective_length = TypeRegistry.get(name=inferred_type).default_length

            slot = self.declare(name=name, stype=inferred_type,
                                length=effective_length)
        handler = TypeRegistry.get(name=slot.stype)
        slot.value = handler.coerce(value, slot.length)
        return

    def mark_retained(self, name: str) -> None:
        """
            Mark an already-declared slot as retained.

            :param name: The variable name.

            :returns: ``None``
        """
        slot = self._slots.get(name)
        if slot is not None:
            slot.retain = True
        return

    def reset_non_retained(self) -> None:
        """
            Apply the top-of-step reset: every non-retained slot returns to
            its storage-type missing sentinel.

            :returns: ``None``
        """
        for slot in self._slots.values():
            if slot.retain is False:
                handler = TypeRegistry.get(name=slot.stype)
                if slot.stype == NUM:
                    slot.value = handler.missing
                else:
                    slot.value = ""
        return

    def load(self, row: dict) -> None:
        """
            Load a source-read row: assign values and mark every loaded slot
            as retained (source variables retain across the reset; the next
            read overwrites them).

            :param row: A ``{var: value}`` row from a reader.

            :returns: ``None``
        """
        for name, value in row.items():
            self.set(name=name, value=value)
            self._slots[name].retain = True
        return

    def formatted(self, name: str, spec: str | None = None) -> str:
        """
            Apply a format spec to the slot's value (the PUT operation).

            :param name: The variable name.
            :param spec: An explicit format spec; ``None`` uses the slot's
                         default format.

            :returns: The formatted text.
        """
        slot = self._slots.get(name)
        if slot is None:
            rtnval = repr(MISSING)
        else:
            if spec is None:
                effective_spec = slot.fmt
            else:
                effective_spec = spec
            rtnval = FormatRegistry.apply(value=slot.value, spec=effective_spec)
        return rtnval

    def snapshot(self, keep: list | None = None,
                 drop: list | None = None,
                 rename: dict | None = None) -> dict:
        """
            Produce an output projection of the current PDV.

            :param keep: Optional whitelist of variable names to include.
            :param drop: Optional blacklist of variable names to exclude.
            :param rename: Optional mapping ``{old_name: new_name}``.

            :returns: A dictionary of the selected variables in declaration
                      order, renamed as requested.
        """
        if rename is None:
            renaming = {}
        else:
            renaming = rename

        out: dict = {}
        for name, slot in self._slots.items():
            if keep is not None and name not in keep:
                continue
            if drop is not None and name in drop:
                continue
            out_name = renaming.get(name, name)
            out[out_name] = slot.value
        return out

    @property
    def slots(self) -> dict:
        """
            Direct access to the underlying slot dictionary for inspection.

            :returns: The internal slot dictionary.
        """
        rtnval = self._slots
        return rtnval
