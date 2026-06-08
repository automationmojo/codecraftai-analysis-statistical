"""
    Example 09 -- migration / optimization advisor.

    The advisor uses the same lowerer and scheduler the executor uses, so
    its verdict matches what the executor will actually do. Each line in
    the report tells you whether a statement runs on the fast path or in
    the loop, and (when it's in the loop) *why*: irreducible, tool-limited,
    dependency, or cardinality.

    Run with::

        python example_09_migration_advisor.py
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from ccai.analysis.statistical import report


def transform(pdv):
    """
        Fully vectorizable transform -- report should say ``"vector"`` and
        flag the columnar suggestion.

        :param pdv: The :class:`ObservationEngine` instance.

        :returns: ``None``
    """
    pdv["gross"] = pdv["qty"] * pdv["price"]
    pdv["net"] = pdv["gross"] * (1 - pdv["disc"])
    pdv["tax"] = pdv["net"] * 0.2
    return


def mixed(pdv):
    """
        Hits every loop category: irreducible (lag / first.), tool-limited
        (vectorizable conditional), dependency (reads ``running``).

        :param pdv: The :class:`ObservationEngine` instance.

        :returns: ``None``
    """
    pdv["gross"] = pdv["qty"] * pdv["price"]
    pdv["net"] = pdv["gross"] * (1 - pdv["disc"])
    pdv["prev"] = pdv.lag(pdv["net"])
    if pdv["net"] > 100:
        pdv["band"] = 2
    else:
        pdv["band"] = 1
    if pdv.first["region"]:
        pdv["running"] = 0
    pdv["running"] = pdv["running"] + pdv["net"]
    pdv["flag"] = pdv["running"] > 1000
    return


def exotic(pdv):
    """
        Outside the sublanguage -- expect a ``fallback`` report with a
        concrete cause string.

        :param pdv: The :class:`ObservationEngine` instance.

        :returns: ``None``
    """
    pdv["digit_sum"] = sum(int(c) for c in str(pdv["qty"]))
    return


def main() -> None:
    """
        Print three reports: one per execution path.

        :returns: ``None``
    """
    rule = "=" * 72

    print(report(logic=transform,
                 source_cols=["qty", "price", "disc"]).text)
    print()
    print(rule)
    print()
    print(report(logic=mixed,
                 source_cols=["region", "qty", "price", "disc"],
                 retain={"running"}).text)
    print()
    print(rule)
    print()
    print(report(logic=exotic, source_cols=["qty"]).text)
    return


if __name__ == "__main__":
    main()
