"""
    Example 02 -- match-merge with ``IN=`` flags.

    Renders the SAS step::

        data merged;
            merge A (in=inA) B (in=inB);
            by id;
        run;

    The fixture intentionally has uneven cardinalities per BY-group so the
    retain-on-exhaustion and "later dataset wins" semantics are visible.

    Run with::

        python example_02_match_merge.py
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from ccai.analysis.statistical import MergeReader, ObservationEngine


def passthrough(pdv):
    """
        Copy the engine-tracked ``IN=`` flags into output columns so they
        appear in the printed rows.

        :param pdv: The :class:`ObservationEngine` instance.

        :returns: ``None``
    """
    pdv["inA"] = pdv.in_["inA"]
    pdv["inB"] = pdv.in_["inB"]
    return


def main() -> None:
    """
        Drive the engine over the match-merge fixture and print the rows.

        :returns: ``None``
    """
    a_rows = [
        {"id": 1, "a": 10},
        {"id": 1, "a": 20},
        {"id": 2, "a": 30},
    ]
    b_rows = [
        {"id": 1, "b": 100},
        {"id": 2, "b": 200},
        {"id": 2, "b": 300},
    ]

    reader = MergeReader(
        sources={"A": a_rows, "B": b_rows},
        by=["id"],
        in_flags={"A": "inA", "B": "inB"},
    )
    engine = ObservationEngine(reader=reader, logic=passthrough, by=["id"])

    print("# match-merge with IN= flags")
    print("  id   a    b    inA  inB")
    for row in engine:
        print("   {id}  {a:>3}  {b:>3}    {inA}    {inB}".format(**row))
    return


if __name__ == "__main__":
    main()
