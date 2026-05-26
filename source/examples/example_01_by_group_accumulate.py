"""
    Example 01 -- BY-group accumulation.

    The canonical SAS DATA step rendered in Python:

        data totals;
            set sales;
            by region customer;
            retain total 0;
            if first.customer then total = 0;
            total = total + amount;
            if last.customer then output;
        run;

    Run with::

        python example_01_by_group_accumulate.py
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from automojo.analysis.statistical import ObservationEngine, SetReader


def accumulate(pdv):
    """
        Reset ``total`` at each customer boundary, accumulate within the
        group, and emit a single row per customer.

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
        Drive the engine over a small sales fixture and print the results.

        :returns: ``None``
    """
    sales = [
        {"region": "East", "customer": "A", "amount": 10},
        {"region": "East", "customer": "A", "amount": 15},
        {"region": "East", "customer": "B", "amount": 7},
        {"region": "West", "customer": "C", "amount": 20},
        {"region": "West", "customer": "C", "amount": 5},
    ]

    engine = ObservationEngine(
        reader=SetReader(source=sales, by=["region", "customer"]),
        logic=accumulate,
        by=["region", "customer"],
        retain={"total": 0},
    )

    print("# customer totals")
    for row in engine:
        print("  region={region}  customer={customer}  total={total}".format(**row))
    return


if __name__ == "__main__":
    main()
