"""
    Example 07 -- :class:`CompiledStep` vector / hybrid / fallback paths.

    The compiled executor:

        * runs pure-vector arithmetic over numpy arrays (no row loop),
        * splits hybrid logic into a batch pre-pass plus a row-loop residual,
        * falls back to the reference engine for logic outside the IR
          sublanguage.

    Every path produces output bit-equal to the reference engine. A small
    timing block compares the vector path against the reference on 100k
    rows so the speedup is concrete.

    Run with::

        python example_07_compiled_step.py
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


import time

from ccai.analysis.statistical import (CompiledStep, ObservationEngine,
                                           SetReader)


def transform(pdv):
    """
        Pure-vector transform: every statement is a function of the current
        row, so the whole step plans as ``"vector"``.

        :param pdv: The :class:`ObservationEngine` instance.

        :returns: ``None``
    """
    pdv["gross"] = pdv["qty"] * pdv["price"]
    pdv["net"] = pdv["gross"] * (1 - pdv["disc"])
    pdv["tax"] = pdv["net"] * 0.2
    pdv["total"] = pdv["net"] + pdv["tax"]
    return


def mixed(pdv):
    """
        Mixed transform: vector arithmetic followed by a sequential
        spine. Plans as ``"hybrid"``.

        :param pdv: The :class:`ObservationEngine` instance.

        :returns: ``None``
    """
    pdv["gross"] = pdv["qty"] * pdv["price"]
    pdv["net"] = pdv["gross"] * (1 - pdv["disc"])
    pdv["prev_net"] = pdv.lag(pdv["net"])
    if pdv.first["region"]:
        pdv["running"] = 0
    pdv["running"] = pdv["running"] + pdv["net"]
    return


def exotic(pdv):
    """
        Logic outside the IR sublanguage (uses a generator expression and a
        built-in call). Plans as ``"fallback"``.

        :param pdv: The :class:`ObservationEngine` instance.

        :returns: ``None``
    """
    pdv["digit_sum"] = sum(int(c) for c in str(pdv["qty"]))
    return


def _reference(rows, logic, by=None, retain=None):
    """
        Run the reference engine for comparison.

        :param rows: Input rows.
        :param logic: User logic callable.
        :param by: Optional BY-key list.
        :param retain: Optional retain map.

        :returns: A list of output rows.
    """
    by_list = [] if by is None else by
    retain_map = {} if retain is None else retain
    engine = ObservationEngine(
        reader=SetReader(source=list(rows), by=by_list),
        logic=logic, by=by_list, retain=retain_map,
    )
    rtnval = list(engine)
    return rtnval


def main() -> None:
    """
        Demonstrate all three paths and benchmark the vector path against
        the reference engine on 100k rows.

        :returns: ``None``
    """
    small = [
        {"qty": 2, "price": 60.0, "disc": 0.1},
        {"qty": 1, "price": 200.0, "disc": 0.0},
    ]

    vector_step = CompiledStep(logic=transform)
    path_v, _, _ = vector_step.plan(source_cols=list(small[0].keys()))
    print("# vector path:", path_v)
    print("  matches reference:",
          vector_step.run(rows=small) == _reference(small, transform))

    hybrid_rows = [
        {"region": "E", "qty": 2, "price": 60.0, "disc": 0.1},
        {"region": "E", "qty": 1, "price": 200.0, "disc": 0.0},
        {"region": "W", "qty": 3, "price": 50.0, "disc": 0.2},
    ]
    hybrid_step = CompiledStep(logic=mixed, by=["region"],
                               retain={"running": 0})
    path_h, _, _ = hybrid_step.plan(source_cols=list(hybrid_rows[0].keys()))
    print("\n# hybrid path:", path_h)
    print("  matches reference:",
          hybrid_step.run(rows=hybrid_rows) == _reference(
              hybrid_rows, mixed, by=["region"], retain={"running": 0}))

    fallback_step = CompiledStep(logic=exotic)
    path_f, _, _ = fallback_step.plan(source_cols=["qty"])
    print("\n# fallback path:", path_f)
    print("  matches reference:",
          fallback_step.run(rows=hybrid_rows[:1]) == _reference(
              hybrid_rows[:1], exotic))

    row_count = 100_000
    big = [{"qty": i % 7 + 1,
            "price": float(i % 100 + 1),
            "disc": (i % 5) / 10.0}
           for i in range(row_count)]
    ref_start = time.perf_counter()
    ref_rows = _reference(big, transform)
    ref_elapsed = time.perf_counter() - ref_start

    vec_start = time.perf_counter()
    vec_rows = CompiledStep(logic=transform).run(rows=big)
    vec_elapsed = time.perf_counter() - vec_start

    print("\n# benchmark on {} rows".format(row_count))
    print("  reference : {:.3f}s".format(ref_elapsed))
    print("  vector    : {:.3f}s  ({:.1f}x faster)".format(
        vec_elapsed, ref_elapsed / vec_elapsed))
    print("  identical : {}".format(ref_rows == vec_rows))
    return


if __name__ == "__main__":
    main()
