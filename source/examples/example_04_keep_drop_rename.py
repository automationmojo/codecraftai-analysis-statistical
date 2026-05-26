"""
    Example 04 -- KEEP / DROP / RENAME output projection.

    SAS::

        data out;
            set in;
            keep x doubled;
            rename x = n;
            doubled = x * 2;
        run;

    Projection is applied at emission time, not during logic, so the user
    code reads from the original variable name (``pdv["x"]``).

    Run with::

        python example_04_keep_drop_rename.py
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from automojo.analysis.statistical import ObservationEngine, SetReader


def double_x(pdv):
    """
        Double ``x`` into a new ``doubled`` slot.

        :param pdv: The :class:`ObservationEngine` instance.

        :returns: ``None``
    """
    pdv["doubled"] = pdv["x"] * 2
    return


def main() -> None:
    """
        Configure a step that keeps only ``x`` and ``doubled`` and renames
        ``x`` to ``n`` on output. Print the rows so the projection is
        visible.

        :returns: ``None``
    """
    rows = [{"x": 5}, {"x": 8}]
    engine = ObservationEngine(
        reader=SetReader(source=rows),
        logic=double_x,
        keep=["x", "doubled"],
        rename={"x": "n"},
    )

    print("# keep=['x', 'doubled'], rename={'x': 'n'}")
    for row in engine:
        print(" ", row)
    return


if __name__ == "__main__":
    main()
