"""
    Example 06 -- dialect-named declarations and precision routing.

    Declare PDV slots in your database's own type vocabulary. The package
    routes:

        * ``NUMERIC(8,2)``  (Postgres) -> ``num``   (float64)
        * ``NUMBER(38,2)``  (Oracle)   -> ``decimal`` (exact, arbitrary precision)
        * ``VARCHAR2(3)``   (Oracle)   -> ``char`` with storage length 3
        * ``DATE``          (Oracle)   -> ``num`` with default format ``DATE9.``

    Unmappable dialect names (e.g. ``JSONB`` in Postgres) raise at declare
    time rather than silently mangling data.

    Run with::

        python example_06_dialect_named_declarations.py
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from decimal import Decimal

from ccai.analysis.statistical import (ObservationEngine, SetReader,
                                           dialect_declare)


def format_hired(pdv):
    """
        Render the SAS-encoded ``hired`` date as text via the slot's
        default format.

        :param pdv: The :class:`ObservationEngine` instance.

        :returns: ``None``
    """
    pdv["hire_date_text"] = pdv.put(name="hired")
    return


def main() -> None:
    """
        Build a row stream with a high-precision Decimal value and route it
        through dialect-named declarations.

        :returns: ``None``
    """
    decls = [
        dialect_declare(name="name", type_string="VARCHAR2(3)",
                        dialect="oracle"),
        dialect_declare(name="salary", type_string="NUMBER(38,2)",
                        dialect="oracle"),
        dialect_declare(name="hired", type_string="DATE", dialect="oracle"),
    ]

    print("# resolved declarations")
    for declaration in decls:
        print(" ", declaration)

    rows = [
        {"name": "HELLO",
         "salary": Decimal("12345678901234567890.12"),
         "hired": 0},
    ]
    engine = ObservationEngine(
        reader=SetReader(source=rows),
        logic=format_hired,
        declare=decls,
    )

    print("\n# emitted rows")
    for row in engine:
        print(" ", row)

    print("\n# precision routing across dialects (same logical column)")
    low = dialect_declare(name="p", type_string="NUMERIC(8,2)",
                          dialect="postgresql")
    high = dialect_declare(name="p", type_string="NUMBER(38,2)",
                           dialect="oracle")
    print("  NUMERIC(8,2)  postgresql ->", low)
    print("  NUMBER(38,2)  oracle     ->", high)

    print("\n# unmappable type fails loud at declare time")
    try:
        dialect_declare(name="doc", type_string="JSONB",
                        dialect="postgresql")
    except ValueError as ex:
        first_line = str(ex).splitlines()[0]
        print("  raised:", first_line)
    return


if __name__ == "__main__":
    main()
