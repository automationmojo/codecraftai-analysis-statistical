"""
    Oracle-equivalence tests. Every production engine output is compared
    row-for-row against the reference implementation in ``source/examples/``.
    The reference modules are the documented correctness oracle; any
    divergence is a correctness regression even when the production engine
    matches its own hand-coded test expectations.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


import sqlite3

from ccai.testshared.referenceloader import ReferenceLoader

from ccai.analysis.statistical.columnar.columnarstep import ColumnarStep
from ccai.analysis.statistical.database.databasereader import DatabaseReader
from ccai.analysis.statistical.engine.observationengine import (
    ObservationEngine as ProductionEngine)
from ccai.analysis.statistical.execution.compiledstep import CompiledStep
from ccai.analysis.statistical.ir.logiccompiler import compile_logic
from ccai.analysis.statistical.readers.mergereader import MergeReader as ProdMerge
from ccai.analysis.statistical.readers.setreader import SetReader as ProdSet


def _normalize_value(value):
    """
        Normalize a value for cross-engine comparison. Missing-value
        instances from the production engine and the reference engine are
        different classes; reduce both to a canonical
        ``("__missing__", tag)`` sentinel so equality compares on tag rather
        than class identity.

        :param value: Any cell value emitted by either engine.

        :returns: A value safe to compare across engines.
    """
    if value.__class__.__name__ == "Missing":
        rtnval = ("__missing__", getattr(value, "tag", ""))
    else:
        rtnval = value
    return rtnval


def _normalize_row(row):
    """
        Apply :func:`_normalize_value` to every cell in ``row``.

        :param row: An emitted row dictionary.

        :returns: A normalized row dictionary.
    """
    rtnval = {key: _normalize_value(value=value) for key, value in row.items()}
    return rtnval


def _rows_equal(left, right):
    """
        Row-list equality that ignores the ``Missing`` class identity gap
        between the production engine and the reference engine.

        :param left: First row list.
        :param right: Second row list.

        :returns: ``True`` when normalized lists are equal.
    """
    left_norm = [_normalize_row(row=r) for r in left]
    right_norm = [_normalize_row(row=r) for r in right]
    rtnval = left_norm == right_norm
    return rtnval


def _accumulate(pdv):
    """
        Canonical BY-group accumulation. Used against both engines so the
        sublanguage shape is identical.
    """
    if pdv.first["customer"] is True:
        pdv["total"] = 0
    pdv["total"] = pdv["total"] + pdv["amount"]
    if pdv.last["customer"] is True:
        pdv.output()
    return


def _transform(pdv):
    """
        Pure-vector transform.
    """
    pdv["gross"] = pdv["qty"] * pdv["price"]
    pdv["net"] = pdv["gross"] * (1 - pdv["disc"])
    pdv["tax"] = pdv["net"] * 0.2
    pdv["total"] = pdv["net"] + pdv["tax"]
    return


def _mixed(pdv):
    """
        Mixed vector / sequential logic.
    """
    pdv["gross"] = pdv["qty"] * pdv["price"]
    pdv["net"] = pdv["gross"] * (1 - pdv["disc"])
    pdv["prev_net"] = pdv.lag(pdv["net"])
    if pdv.first["region"]:
        pdv["running"] = 0
    pdv["running"] = pdv["running"] + pdv["net"]
    return


def _passthrough(pdv):
    """
        Match-merge passthrough that copies IN= flags into output columns.
    """
    pdv["inA"] = pdv.in_["inA"]
    pdv["inB"] = pdv.in_["inB"]
    return


def test_engine_by_group_accumulate_matches_reference():
    """
        The production :class:`ObservationEngine` produces row-for-row the
        same output as the reference engine on a BY-group accumulation.
    """
    sales = [
        {"region": "East", "customer": "A", "amount": 10},
        {"region": "East", "customer": "A", "amount": 15},
        {"region": "East", "customer": "B", "amount": 7},
        {"region": "West", "customer": "C", "amount": 20},
        {"region": "West", "customer": "C", "amount": 5},
    ]
    reference = ReferenceLoader.load()["engine"]

    ref_rows = list(reference.ObservationEngine(
        reference.SetReader(list(sales), by=["region", "customer"]),
        _accumulate, by=["region", "customer"], retain={"total": 0}))

    prod_rows = list(ProductionEngine(
        reader=ProdSet(source=list(sales), by=["region", "customer"]),
        logic=_accumulate, by=["region", "customer"],
        retain={"total": 0}))

    same = _rows_equal(left=prod_rows, right=ref_rows)
    assert same is True
    return


def test_engine_match_merge_matches_reference():
    """
        Match-merge output is row-for-row equal between engines.
    """
    a_rows = [{"id": 1, "a": 10}, {"id": 1, "a": 20}, {"id": 2, "a": 30}]
    b_rows = [{"id": 1, "b": 100}, {"id": 2, "b": 200}, {"id": 2, "b": 300}]
    reference = ReferenceLoader.load()["engine"]

    ref_reader = reference.MergeReader(
        {"A": list(a_rows), "B": list(b_rows)}, by=["id"],
        in_flags={"A": "inA", "B": "inB"})
    ref_rows = list(reference.ObservationEngine(
        ref_reader, _passthrough, by=["id"]))

    prod_reader = ProdMerge(
        sources={"A": list(a_rows), "B": list(b_rows)}, by=["id"],
        in_flags={"A": "inA", "B": "inB"})
    prod_rows = list(ProductionEngine(reader=prod_reader,
                                      logic=_passthrough, by=["id"]))

    same = _rows_equal(left=prod_rows, right=ref_rows)
    assert same is True
    return


def test_ir_compiled_logic_matches_reference_engine():
    """
        Compiling user logic through the production IR and running it
        through the production engine yields the same output as running
        the original function through the reference engine.
    """
    rows = [{"region": "E", "qty": 2, "price": 60, "disc": 0.1},
            {"region": "E", "qty": 1, "price": 200, "disc": 0.0},
            {"region": "W", "qty": 3, "price": 50, "disc": 0.2}]
    reference = ReferenceLoader.load()["engine"]

    ref_rows = list(reference.ObservationEngine(
        reference.SetReader(list(rows), by=["region"]),
        _mixed, by=["region"], retain={"running": 0}))

    compiled, mode = compile_logic(logic=_mixed)
    prod_rows = list(ProductionEngine(
        reader=ProdSet(source=list(rows), by=["region"]),
        logic=compiled, by=["region"], retain={"running": 0}))

    mode_ok = mode == "ir"
    output_ok = _rows_equal(left=prod_rows, right=ref_rows)
    assert mode_ok is True
    assert output_ok is True
    return


def test_compiledstep_vector_path_matches_reference():
    """
        :class:`CompiledStep` vector path is row-for-row equal to the
        reference engine.
    """
    rows = [{"qty": 2, "price": 60.0, "disc": 0.1},
            {"qty": 1, "price": 200.0, "disc": 0.0}]
    reference = ReferenceLoader.load()["engine"]

    ref_rows = list(reference.ObservationEngine(
        reference.SetReader(list(rows)), _transform))
    prod_rows = CompiledStep(logic=_transform).run(rows=list(rows))

    same = _rows_equal(left=prod_rows, right=ref_rows)
    assert same is True
    return


def test_compiledstep_hybrid_path_matches_reference():
    """
        :class:`CompiledStep` hybrid path is row-for-row equal to the
        reference engine.
    """
    rows = [{"region": "E", "qty": 2, "price": 60.0, "disc": 0.1},
            {"region": "E", "qty": 1, "price": 200.0, "disc": 0.0},
            {"region": "W", "qty": 3, "price": 50.0, "disc": 0.2}]
    reference = ReferenceLoader.load()["engine"]

    ref_rows = list(reference.ObservationEngine(
        reference.SetReader(list(rows), by=["region"]),
        _mixed, by=["region"], retain={"running": 0}))
    prod_rows = CompiledStep(logic=_mixed, by=["region"],
                             retain={"running": 0}).run(rows=list(rows))

    same = _rows_equal(left=prod_rows, right=ref_rows)
    assert same is True
    return


def test_columnar_to_dicts_matches_reference():
    """
        :class:`ColumnarStep` ``to_dicts()`` is row-for-row equal to the
        reference engine on a pure-vector transform.
    """
    rows = [{"qty": 2, "price": 60.0, "disc": 0.1},
            {"qty": 1, "price": 200.0, "disc": 0.0}]
    reference = ReferenceLoader.load()["engine"]

    ref_rows = list(reference.ObservationEngine(
        reference.SetReader(list(rows)), _transform))
    prod_frame = ColumnarStep(logic=_transform).run_columnar(data=list(rows))

    same = _rows_equal(left=prod_frame.to_dicts(), right=ref_rows)
    assert same is True
    return


def test_database_reader_matches_reference_engine_over_sqlite():
    """
        :class:`DatabaseReader` consumed by the production engine produces
        the same accumulation as the reference engine reading the same
        sqlite rows.
    """
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        "CREATE TABLE sales (region TEXT, customer TEXT, amount REAL);"
        "INSERT INTO sales VALUES ('East','A',10),('East','A',15),"
        "('East','B',7),('West','C',20),('West','C',5);"
    )
    cur_prod = conn.cursor()
    cur_prod.execute("SELECT region, customer, amount FROM sales "
                     "ORDER BY region, customer")
    prod_rows = list(ProductionEngine(
        reader=DatabaseReader(cursor=cur_prod,
                              by=["region", "customer"]),
        logic=_accumulate, by=["region", "customer"],
        retain={"total": 0}))

    cur_ref = conn.cursor()
    cur_ref.execute("SELECT region, customer, amount FROM sales "
                    "ORDER BY region, customer")
    reference = ReferenceLoader.load()
    ref_rows = list(reference["engine"].ObservationEngine(
        reference["db"].DatabaseReader(cur_ref,
                                       by=["region", "customer"]),
        _accumulate, by=["region", "customer"],
        retain={"total": 0}))
    conn.close()

    same = _rows_equal(left=prod_rows, right=ref_rows)
    assert same is True
    return
