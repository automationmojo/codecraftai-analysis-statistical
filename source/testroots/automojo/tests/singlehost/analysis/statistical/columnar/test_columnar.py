"""
    Tests for :class:`ColumnFrame` and :class:`ColumnarStep`.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from automojo.analysis.statistical.columnar.columnarstep import ColumnarStep
from automojo.analysis.statistical.columnar.columnframe import ColumnFrame
from automojo.analysis.statistical.engine.observationengine import ObservationEngine
from automojo.analysis.statistical.readers.setreader import SetReader


def _transform(pdv):
    """
        Fully vectorizable transform.
    """
    pdv["gross"] = pdv["qty"] * pdv["price"]
    pdv["net"] = pdv["gross"] * (1 - pdv["disc"])
    pdv["tax"] = pdv["net"] * 0.2
    pdv["total"] = pdv["net"] + pdv["tax"]
    return


def _second_stage(pdv):
    """
        Vectorizable continuation that reads only step-1 outputs.
    """
    pdv["margin"] = pdv["net"] / pdv["gross"]
    pdv["after_tax_pct"] = pdv["total"] / pdv["gross"]
    return


def _reference(rows, logic, by=None, retain=None):
    by_list = [] if by is None else by
    retain_map = {} if retain is None else retain
    reader = SetReader(source=list(rows), by=by_list)
    engine = ObservationEngine(reader=reader, logic=logic, by=by_list,
                               retain=retain_map)
    rtnval = list(engine)
    return rtnval


def test_columnar_to_dicts_matches_reference_engine():
    """
        ``ColumnFrame.to_dicts()`` over a pure-vector transform is bit-equal
        to the reference engine's row output.
    """
    rows = [{"qty": 2, "price": 60.0, "disc": 0.1},
            {"qty": 1, "price": 200.0, "disc": 0.0}]
    frame = ColumnarStep(logic=_transform).run_columnar(data=rows)
    same = frame.to_dicts() == _reference(rows, _transform)
    assert same is True
    return


def test_columnar_preserves_column_order():
    """
        Column order on output is source columns followed by assigned columns
        in program order.
    """
    rows = [{"qty": 2, "price": 60.0, "disc": 0.1}]
    frame = ColumnarStep(logic=_transform).run_columnar(data=rows)
    expected = ["qty", "price", "disc", "gross", "net", "tax", "total"]
    same = frame.columns == expected
    assert same is True
    return


def test_columnar_chains_array_to_array_across_two_steps():
    """
        Two vectorizable steps chain with no per-row materialization between
        them; the second sees the columns the first produced.
    """
    rows = [{"qty": 2, "price": 60.0, "disc": 0.1},
            {"qty": 1, "price": 200.0, "disc": 0.0}]
    stage_one = ColumnarStep(logic=_transform).run_columnar(data=rows)
    stage_two = ColumnarStep(logic=_second_stage).run_columnar(data=stage_one)
    has_margin = "margin" in stage_two.columns
    has_after_tax = "after_tax_pct" in stage_two.columns
    assert has_margin is True
    assert has_after_tax is True
    return


def test_columnframe_indexing_and_iteration_match():
    """
        Iterating the frame produces the same rows as integer indexing.
    """
    rows = [{"qty": 2, "price": 60.0, "disc": 0.1},
            {"qty": 1, "price": 200.0, "disc": 0.0}]
    frame = ColumnarStep(logic=_transform).run_columnar(data=rows)
    iterated = list(frame)
    indexed = [frame[i] for i in range(len(frame))]
    same = iterated == indexed
    assert same is True
    return


def test_columnframe_array_access_returns_underlying_array():
    """
        ``frame['name']`` returns the column array; mutating it would mutate
        the frame (deliberately -- no defensive copy).
    """
    rows = [{"qty": 2, "price": 60.0, "disc": 0.1},
            {"qty": 1, "price": 200.0, "disc": 0.0}]
    frame = ColumnarStep(logic=_transform).run_columnar(data=rows)
    same_first = float(frame["gross"][0]) == 120.0
    same_second = float(frame["gross"][1]) == 200.0
    assert same_first is True
    assert same_second is True
    return


def test_columnframe_from_dicts_handles_empty_input():
    """
        An empty input yields an empty :class:`ColumnFrame`.
    """
    frame = ColumnFrame.from_dicts(rows=[])
    same_len = len(frame) == 0
    same_cols = frame.columns == []
    assert same_len is True
    assert same_cols is True
    return
