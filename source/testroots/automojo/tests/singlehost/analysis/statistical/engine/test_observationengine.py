"""
    End-to-end tests for :class:`ObservationEngine`. These mirror the reference
    examples in ``source/examples/sasstep.py``; the reference engine is the
    oracle of correctness and the production engine output must match it.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from automojo.analysis.statistical.engine.observationengine import ObservationEngine
from automojo.analysis.statistical.missing.missingfactory import MISSING
from automojo.analysis.statistical.readers.mergereader import MergeReader
from automojo.analysis.statistical.readers.setreader import SetReader
from automojo.analysis.statistical.types.constants import CHAR


def test_by_group_accumulate_with_retain_resets_at_each_group():
    """
        ``total`` is reset by ``if first.customer`` and grows within group,
        producing the running total per row.
    """
    sales = [
        {"region": "East", "customer": "A", "amount": 10},
        {"region": "East", "customer": "A", "amount": 15},
        {"region": "East", "customer": "B", "amount": 7},
        {"region": "West", "customer": "C", "amount": 20},
        {"region": "West", "customer": "C", "amount": 5},
    ]

    def accumulate(pdv):
        if pdv.first["customer"] is True:
            pdv["total"] = 0
        pdv["total"] = pdv["total"] + pdv["amount"]
        if pdv.last["customer"] is True:
            pdv.output()
        return

    reader = SetReader(source=sales, by=["region", "customer"])
    engine = ObservationEngine(reader=reader, logic=accumulate,
                               by=["region", "customer"],
                               retain={"total": 0})
    rows = list(engine)

    totals = [r["total"] for r in rows]
    expected = [10, 25, 7, 20, 25]
    same = totals == expected
    assert same is True
    return


def test_match_merge_in_flags_and_retain_on_exhaustion():
    """
        Reproduces the match-merge fixture: 4 rows out, ``b`` retained while
        A still has rows in id=1, ``a`` retained while B still has rows in
        id=2.
    """
    a_rows = [{"id": 1, "a": 10}, {"id": 1, "a": 20}, {"id": 2, "a": 30}]
    b_rows = [{"id": 1, "b": 100}, {"id": 2, "b": 200}, {"id": 2, "b": 300}]
    reader = MergeReader(sources={"A": a_rows, "B": b_rows}, by=["id"],
                         in_flags={"A": "inA", "B": "inB"})

    def passthrough(pdv):
        pdv["inA"] = pdv.in_["inA"]
        pdv["inB"] = pdv.in_["inB"]
        return

    engine = ObservationEngine(reader=reader, logic=passthrough, by=["id"])
    rows = list(engine)
    summary = [(r["id"], r["a"], r["b"], r["inA"], r["inB"]) for r in rows]
    expected = [(1, 10, 100, 1, 1), (1, 20, 100, 1, 0),
                (2, 30, 200, 1, 1), (2, 30, 300, 0, 1)]
    same = summary == expected
    assert same is True
    return


def test_lag_and_dif_are_call_site_keyed():
    """
        A conditional LAG keeps its own queue: ``lag_odd`` only enqueues when
        the branch executes.
    """
    def lags(pdv):
        pdv["lag_all"] = pdv.lag(pdv["x"])
        pdv["dif_all"] = pdv.dif(pdv["x"])
        if pdv["x"] % 2 == 1:
            pdv["lag_odd"] = pdv.lag(pdv["x"])
        return

    reader = SetReader(source=[{"x": v} for v in (1, 2, 3, 4, 5)])
    engine = ObservationEngine(reader=reader, logic=lags)
    rows = list(engine)

    lag_all = [r["lag_all"] for r in rows]
    expected_lag = [MISSING, 1, 2, 3, 4]
    same_lag = lag_all == expected_lag
    assert same_lag is True

    odd_rows = [r for r in rows if r["x"] % 2 == 1]
    lag_odd = [r["lag_odd"] for r in odd_rows]
    expected_odd = [MISSING, 1, 3]
    same_odd = lag_odd == expected_odd
    assert same_odd is True
    return


def test_typed_char_truncation_and_format_application():
    """
        A CHAR(3) slot silently truncates assigned strings; format application
        renders values without mutating storage.
    """
    def typed(pdv):
        pdv["label"] = pdv["name"]
        pdv["shown_amt"] = pdv.put(name="amt", spec="DOLLAR10.2")
        pdv["shown_dt"] = pdv.put(name="dt", spec="DATE9.")
        return

    rows = [{"name": "HELLO", "amt": 1234.5, "dt": 0},
            {"name": "HI", "amt": 9.0, "dt": 366}]
    reader = SetReader(source=rows)
    engine = ObservationEngine(reader=reader, logic=typed,
                               declare=[{"name": "label", "stype": CHAR,
                                         "length": 3}])
    out = list(engine)

    label_truncated = out[0]["label"] == "HEL"
    label_unpadded = out[1]["label"] == "HI"
    amt_text = out[0]["shown_amt"] == "$1,234.50"
    dt_text = out[1]["shown_dt"] == "01JAN1961"
    assert label_truncated is True
    assert label_unpadded is True
    assert amt_text is True
    assert dt_text is True
    return


def test_keep_drop_rename_projection_is_applied_on_output():
    """
        ``keep`` and ``rename`` apply to the emitted snapshot.
    """
    def doubled(pdv):
        pdv["doubled"] = pdv["x"] * 2
        return

    reader = SetReader(source=[{"x": 5}, {"x": 8}])
    engine = ObservationEngine(reader=reader, logic=doubled,
                               keep=["x", "doubled"],
                               rename={"x": "n"})
    out = list(engine)
    keys_first = list(out[0].keys())
    same_keys = keys_first == ["n", "doubled"]
    same_values = out[0]["n"] == 5 and out[0]["doubled"] == 10
    assert same_keys is True
    assert same_values is True
    return


def test_delete_suppresses_bottom_emission():
    """
        Calling ``pdv.delete()`` prevents the BOTTOM-phase emission.
    """
    def filtering(pdv):
        if pdv["x"] % 2 == 0:
            pdv.delete()
        return

    reader = SetReader(source=[{"x": v} for v in (1, 2, 3, 4, 5)])
    engine = ObservationEngine(reader=reader, logic=filtering)
    out = list(engine)
    xs = [r["x"] for r in out]
    same = xs == [1, 3, 5]
    assert same is True
    return


def test_explicit_output_suppresses_bottom_emission():
    """
        Calling ``pdv.output()`` once prevents the BOTTOM emission; multiple
        ``output()`` calls emit multiple rows.
    """
    def double_emit(pdv):
        pdv.output()
        pdv["x"] = pdv["x"] + 100
        pdv.output()
        return

    reader = SetReader(source=[{"x": 1}])
    engine = ObservationEngine(reader=reader, logic=double_emit)
    out = list(engine)
    xs = [r["x"] for r in out]
    same = xs == [1, 101]
    assert same is True
    return
