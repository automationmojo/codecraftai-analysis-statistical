"""
    Engine tests that consume :mod:`testbase` resource factories rather than
    constructing input data inline. These tests demonstrate the canonical
    factory-driven pattern for the package: scope-level originations supply
    the dataset and each test names the parameter in its signature.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"



from ccai.analysis.statistical.engine.observationengine import ObservationEngine
from ccai.analysis.statistical.readers.mergereader import MergeReader
from ccai.analysis.statistical.readers.setreader import SetReader


def test_by_group_accumulate_via_factory(sales_dataset: list[dict]):
    """
        Run the canonical BY-group accumulation against the factory-supplied
        sales dataset and verify the running totals.

        :param sales_dataset: Dataset injected by the ``sales_dataset``
                              parameter origination.
    """
    def accumulate(pdv):
        if pdv.first["customer"] is True:
            pdv["total"] = 0
        pdv["total"] = pdv["total"] + pdv["amount"]
        if pdv.last["customer"] is True:
            pdv.output()
        return

    reader = SetReader(source=sales_dataset, by=["region", "customer"])
    engine = ObservationEngine(reader=reader, logic=accumulate,
                               by=["region", "customer"],
                               retain={"total": 0})
    rows = list(engine)
    totals = [row["total"] for row in rows]
    expected = [10, 25, 7, 20, 25]
    same = totals == expected
    assert same is True
    return


def test_match_merge_via_factory(merge_sources: dict):
    """
        Run a match-merge against the factory-supplied A/B sources and
        verify the row count and IN= flags.

        :param merge_sources: Source map injected by the ``merge_sources``
                              parameter origination.
    """
    reader = MergeReader(sources=merge_sources, by=["id"],
                         in_flags={"A": "inA", "B": "inB"})

    def passthrough(pdv):
        pdv["inA"] = pdv.in_["inA"]
        pdv["inB"] = pdv.in_["inB"]
        return

    engine = ObservationEngine(reader=reader, logic=passthrough, by=["id"])
    rows = list(engine)
    count_ok = len(rows) == 4
    second_b_retained = rows[1]["b"] == 100
    assert count_ok is True
    assert second_b_retained is True
    return


def test_lag_dif_via_factory(lag_inputs: list[dict]):
    """
        Run LAG / DIF against the factory-supplied sequence and verify the
        first-row missing semantics and stable differences.

        :param lag_inputs: Dataset injected by the ``lag_inputs`` parameter
                           origination.
    """
    from ccai.analysis.statistical.missing.missingfactory import MISSING

    def lags(pdv):
        pdv["lag_all"] = pdv.lag(pdv["x"])
        pdv["dif_all"] = pdv.dif(pdv["x"])
        return

    reader = SetReader(source=lag_inputs)
    engine = ObservationEngine(reader=reader, logic=lags)
    rows = list(engine)

    first_lag_missing = rows[0]["lag_all"] is MISSING
    first_dif_missing = rows[0]["dif_all"] is MISSING
    stable_dif = all(row["dif_all"] == 1 for row in rows[1:])
    assert first_lag_missing is True
    assert first_dif_missing is True
    assert stable_dif is True
    return
