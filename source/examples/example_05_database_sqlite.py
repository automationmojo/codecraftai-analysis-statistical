"""
    Example 05 -- database source via SQLite.

    Wraps any PEP 249 cursor with :class:`DatabaseReader` and drives the
    same accumulation logic from Example 01 against rows pulled from a
    database. The ``ORDER BY`` is pushed into SQL so the engine sees rows
    in BY-group order (required for ``first.``/``last.`` semantics).

    Run with::

        python example_05_database_sqlite.py
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


import sqlite3

from ccai.analysis.statistical import DatabaseReader, ObservationEngine


def accumulate(pdv):
    """
        Per-customer running total emitted at the last row of each customer.

        :param pdv: The :class:`ObservationEngine` instance.

        :returns: ``None``
    """
    if pdv.first["customer"] is True:
        pdv["total"] = 0
    pdv["total"] = pdv["total"] + pdv["amount"]
    if pdv.last["customer"] is True:
        pdv.output()
    return


def main() -> None:
    """
        Build an in-memory SQLite table, push ``ORDER BY`` into the SELECT,
        and stream the result through the engine.

        :returns: ``None``
    """
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        "CREATE TABLE sales (region TEXT, customer TEXT, amount REAL);"
        "INSERT INTO sales VALUES "
        "('East','A',10),('East','A',15),('East','B',7),"
        "('West','C',20),('West','C',5);"
    )

    cursor = conn.cursor()
    cursor.execute(
        "SELECT region, customer, amount FROM sales "
        "ORDER BY region, customer"
    )

    engine = ObservationEngine(
        reader=DatabaseReader(cursor=cursor, by=["region", "customer"]),
        logic=accumulate,
        by=["region", "customer"],
        retain={"total": 0},
    )

    print("# sqlite -> by-group accumulate")
    for row in engine:
        print("  region={region}  customer={customer}  total={total}".format(**row))

    conn.close()
    return


if __name__ == "__main__":
    main()
