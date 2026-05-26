"""
    .. module:: observationengine
        :synopsis: The :class:`ObservationEngine` -- the implicit-loop iterator
                   over a :class:`Reader`. Owns a :class:`RecordFrame`, drives
                   it through TOP -> READ -> EXECUTE -> BOTTOM, and yields one
                   output row per output buffer position.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from collections import deque
from typing import Any
from collections.abc import Callable, Iterator

from automojo.analysis.statistical.engine.phase import Phase
from automojo.analysis.statistical.engine.recordframe import RecordFrame
from automojo.analysis.statistical.engine.statefulfunctions import StatefulFunctions
from automojo.analysis.statistical.missing.missing import Missing
from automojo.analysis.statistical.readers.reader import Reader
from automojo.analysis.statistical.types.constants import NUM
from automojo.analysis.statistical.types.typeregistry import TypeRegistry


class ObservationEngine(StatefulFunctions):
    """
        The SAS DATA-step implicit-loop iterator. Constructed with a reader
        and a logic callable, it yields one output row at a time. The logic
        callable receives this engine as its single argument (commonly named
        ``pdv``) and uses ``pdv[name]`` / ``pdv[name] = value`` to read/write
        slots, ``pdv.lag(value)``, ``pdv.dif(value)``, ``pdv.first[by_name]``,
        ``pdv.last[by_name]``, ``pdv.output()``, and ``pdv.delete()``.
    """

    def __init__(self, reader: Reader, logic: Callable[[Any], None],
                 by: list | None = None,
                 retain: dict | None = None,
                 declare: list | None = None,
                 keep: list | None = None,
                 drop: list | None = None,
                 rename: dict | None = None) -> None:
        """
            Initialize the :class:`ObservationEngine`.

            :param reader: The :class:`Reader` to drive the loop.
            :param logic: The user logic callable ``(pdv) -> None``.
            :param by: Optional list of BY-key column names.
            :param retain: Optional ``{name: init_value}`` for variables that
                           must survive the top-of-step reset.
            :param declare: Optional list of declaration dicts compatible with
                            :meth:`RecordFrame.declare`.
            :param keep: Optional KEEP projection.
            :param drop: Optional DROP projection.
            :param rename: Optional ``{old: new}`` renaming.

            :returns: ``None``
        """
        self._reader = reader
        self._logic = logic

        if by is None:
            self._by = []
        else:
            self._by = list(by)

        self._frame = RecordFrame()

        if hasattr(reader, "declarations"):
            for declaration in reader.declarations():
                self._frame.declare(**declaration)

        if declare is not None:
            for declaration in declare:
                self._frame.declare(**declaration)

        if retain is not None:
            for name, init_value in retain.items():
                slot = self._frame.slots.get(name)
                if slot is not None:
                    slot.retain = True
                    handler = TypeRegistry.get(name=slot.stype)
                    slot.value = handler.coerce(init_value, slot.length)
                else:
                    if isinstance(init_value, Missing):
                        inferred_type = NUM
                    else:
                        inferred_type = TypeRegistry.infer(value=init_value)
                    self._frame.declare(name=name, stype=inferred_type,
                                        retain=True, init=init_value)

        self._keep = keep
        self._drop = drop
        self._rename = rename

        self._prev_key: tuple | None = None
        self.first: dict = {}
        self.last: dict = {}
        self.in_: dict = {}
        self.n = 0
        self.eof = False
        self._lag_queues: dict = {}
        self._output_buffer: deque = deque()
        self._explicit_output = False
        self._deleted = False
        self.phase = Phase.TOP_OF_STEP
        return

    def __getitem__(self, name: str) -> Any:
        """
            Read a slot value by name.

            :param name: The variable name.

            :returns: The current slot value.
        """
        rtnval = self._frame.get(name=name)
        return rtnval

    def __setitem__(self, name: str, value: Any) -> None:
        """
            Assign a slot value by name.

            :param name: The variable name.
            :param value: The new value.

            :returns: ``None``
        """
        self._frame.set(name=name, value=value)
        return

    @property
    def frame(self) -> RecordFrame:
        """
            The underlying :class:`RecordFrame`.

            :returns: The PDV instance.
        """
        rtnval = self._frame
        return rtnval

    def put(self, name: str, spec: str | None = None) -> str:
        """
            Format a slot value as text (the PUT operation).

            :param name: The variable name.
            :param spec: Optional explicit format spec.

            :returns: The formatted text.
        """
        rtnval = self._frame.formatted(name=name, spec=spec)
        return rtnval

    def output(self) -> None:
        """
            Emit the current row to the output buffer.

            :returns: ``None``
        """
        snapshot = self._frame.snapshot(keep=self._keep, drop=self._drop,
                                        rename=self._rename)
        self._output_buffer.append(snapshot)
        self._explicit_output = True
        return

    def delete(self) -> None:
        """
            Mark the current row for deletion (no output at the BOTTOM phase).

            :returns: ``None``
        """
        self._deleted = True
        return

    def __iter__(self) -> Iterator[dict]:
        """
            The engine itself is its iterator.

            :returns: ``self``.
        """
        rtnval = self
        return rtnval

    def __next__(self) -> dict:
        """
            Yield the next output row, ticking the engine as needed to fill
            the output buffer.

            :returns: An output row dictionary.
            :raises StopIteration: When the reader is exhausted and the buffer
                                   is empty.
        """
        while len(self._output_buffer) == 0:
            self._tick()
        rtnval = self._output_buffer.popleft()
        return rtnval

    def _set_by_flags(self, cur_key: tuple, next_key: tuple | None) -> None:
        """
            Compute ``first.``/``last.`` flags for each BY level.

            :param cur_key: The current row's BY-key tuple.
            :param next_key: The next row's BY-key tuple, or ``None`` at EOF.

            :returns: ``None``
        """
        for index, by_name in enumerate(self._by):
            prefix = cur_key[: index + 1]
            if self._prev_key is None:
                self.first[by_name] = True
            else:
                self.first[by_name] = self._prev_key[: index + 1] != prefix
            if next_key is None:
                self.last[by_name] = True
            else:
                self.last[by_name] = next_key[: index + 1] != prefix
        self._prev_key = cur_key
        return

    def _tick(self) -> None:
        """
            Advance the engine one cycle: TOP -> READ -> EXECUTE -> BOTTOM.

            :returns: ``None``
            :raises StopIteration: When the reader is exhausted.
        """
        if self.phase is Phase.DONE:
            raise StopIteration

        self._frame.reset_non_retained()
        self._explicit_output = False
        self._deleted = False

        if self._reader.has_more() is False:
            self.phase = Phase.DONE
            raise StopIteration

        row, in_flags, cur_key, next_key = self._reader.next_obs()
        self.n += 1
        self._frame.load(row=row)
        self.in_ = in_flags
        self.eof = not self._reader.has_more()
        self._set_by_flags(cur_key=cur_key, next_key=next_key)

        self._logic(self)

        if self._deleted is False and self._explicit_output is False:
            snapshot = self._frame.snapshot(keep=self._keep, drop=self._drop,
                                            rename=self._rename)
            self._output_buffer.append(snapshot)
        return
