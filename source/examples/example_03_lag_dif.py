"""
    Example 03 -- LAG and DIF stateful functions.

    SAS::

        prev = lag(amount);
        delta = dif(amount);

    Both functions are call-site keyed: a conditional LAG only enqueues when
    its branch executes, so the queue for that call site is independent of
    every other call site.

    Run with::

        python example_03_lag_dif.py
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from ccai.analysis.statistical import ObservationEngine, SetReader


def lags(pdv):
    """
        Compute an unconditional LAG/DIF and a *conditional* LAG that only
        enqueues on odd-valued rows.

        :param pdv: The :class:`ObservationEngine` instance.

        :returns: ``None``
    """
    pdv["lag_all"] = pdv.lag(pdv["x"])
    pdv["dif_all"] = pdv.dif(pdv["x"])
    if pdv["x"] % 2 == 1:
        pdv["lag_odd"] = pdv.lag(pdv["x"])
    return


def main() -> None:
    """
        Run a five-row stream and show how each lag queue evolves.

        :returns: ``None``
    """
    rows = [{"x": value} for value in (1, 2, 3, 4, 5)]
    engine = ObservationEngine(reader=SetReader(source=rows), logic=lags)

    print("# lag / dif (call-site-keyed)")
    print("  x   lag_all   dif_all   lag_odd")
    for row in engine:
        lag_odd = row.get("lag_odd", "(unset)")
        print("  {x}   {lag_all}        {dif_all}        {lag_odd}".format(
            x=row["x"], lag_all=row["lag_all"], dif_all=row["dif_all"],
            lag_odd=lag_odd))
    return


if __name__ == "__main__":
    main()
