"""
    Example 08 -- columnar pipeline and pandas export.

    Two vectorizable steps chain array-to-array via :class:`ColumnarStep`,
    paying zero per-row materialization between stages. The final
    :class:`ColumnFrame` is exported to a :class:`pandas.DataFrame` only
    when a downstream consumer needs it.

    Pandas is an optional dependency; the script prints a notice and skips
    the export when it is not importable.

    Run with::

        python example_08_columnar_pipeline.py
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from automojo.analysis.statistical import ColumnarStep


def stage_one(pdv):
    """
        Vector arithmetic stage: gross, net, tax, total.

        :param pdv: The :class:`ObservationEngine` instance.

        :returns: ``None``
    """
    pdv["gross"] = pdv["qty"] * pdv["price"]
    pdv["net"] = pdv["gross"] * (1 - pdv["disc"])
    pdv["tax"] = pdv["net"] * 0.2
    pdv["total"] = pdv["net"] + pdv["tax"]
    return


def stage_two(pdv):
    """
        Second stage: read columns produced by stage one and derive
        margins. Still vector-classified.

        :param pdv: The :class:`ObservationEngine` instance.

        :returns: ``None``
    """
    pdv["margin"] = pdv["net"] / pdv["gross"]
    pdv["after_tax_pct"] = pdv["total"] / pdv["gross"]
    return


def main() -> None:
    """
        Run the two-stage pipeline and show the columnar result. Optionally
        export to a pandas DataFrame.

        :returns: ``None``
    """
    rows = [
        {"qty": 2, "price": 60.0, "disc": 0.1},
        {"qty": 1, "price": 200.0, "disc": 0.0},
        {"qty": 3, "price": 50.0, "disc": 0.2},
    ]

    frame_one = ColumnarStep(logic=stage_one).run_columnar(data=rows)
    frame_two = ColumnarStep(logic=stage_two).run_columnar(data=frame_one)

    print("# columns produced by the pipeline:", frame_two.columns)
    print("# first row (materialized on demand):", frame_two[0])
    print("# row count:", len(frame_two))

    try:
        import pandas  # noqa: F401 -- presence check
    except ImportError:
        print("\n# pandas not installed -- skipping to_pandas() export")
        return

    df = frame_two.to_pandas()
    print("\n# pandas DataFrame head:")
    print(df.head().to_string(index=False))
    return


if __name__ == "__main__":
    main()
