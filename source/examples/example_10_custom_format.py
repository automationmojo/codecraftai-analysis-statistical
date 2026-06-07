"""
    Example 10 -- register a custom format class.

    Formats and informats are the SAS-faithful extension point for new
    value representations. Add a converter, register it under a name, and
    the engine's :meth:`pdv.put` and :class:`FormatRegistry.apply` will
    route to it just like the built-in DOLLAR / COMMA / DATE converters.

    This example registers a ``PERCENT`` format that renders a float as
    ``NN.N%`` and uses it via ``pdv.put`` and as a declaration's default
    ``fmt``.

    Run with::

        python example_10_custom_format.py
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from typing import Any

from ccai.analysis.statistical import (NUM, ObservationEngine, SetReader,
                                           register_format)


class PercentFormat:
    """
        Render a float in [0, 1] as a percentage with one fractional digit.
        Width is honoured by right-justifying the result.
    """

    def __call__(self, value: Any, width: int | None,
                 decimals: int | None) -> str:
        """
            Render ``value`` as ``NN.N%`` text.

            :param value: The fractional value (for example ``0.205``).
            :param width: Display width; ``None`` falls back to the natural
                          width of the rendered number.
            :param decimals: Decimal places; defaults to ``1``.

            :returns: The rendered text.
        """
        if decimals is None:
            places = 1
        else:
            places = decimals
        scaled = "{:.{}f}%".format(value * 100.0, places)
        if width is None:
            rtnval = scaled
        else:
            rtnval = scaled.rjust(width)
        return rtnval


def render(pdv):
    """
        Apply the custom format via :meth:`pdv.put` and via the slot's
        default ``fmt``.

        :param pdv: The :class:`ObservationEngine` instance.

        :returns: ``None``
    """
    pdv["disc_text"] = pdv.put(name="disc", spec="PERCENT8.1")
    pdv["rate_text"] = pdv.put(name="rate")
    return


def main() -> None:
    """
        Register the custom format and run a small step that uses it both
        ways.

        :returns: ``None``
    """
    register_format(name="PERCENT", fn=PercentFormat())

    rows = [{"disc": 0.205, "rate": 0.0875},
            {"disc": 0.0,   "rate": 0.1500}]
    engine = ObservationEngine(
        reader=SetReader(source=rows),
        logic=render,
        declare=[{"name": "rate", "stype": NUM, "fmt": "PERCENT8.2"}],
    )

    print("# custom PERCENT format applied via pdv.put and slot default fmt")
    for row in engine:
        print(" ", row)
    return


if __name__ == "__main__":
    main()
