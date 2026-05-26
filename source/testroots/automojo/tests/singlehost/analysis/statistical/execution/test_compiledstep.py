"""
    Tests for :class:`CompiledStep`. Validates the three execution paths
    (``vector``, ``hybrid``, ``fallback``) and forward-dataflow demotion of a
    vectorizable statement that reads a loop-only value.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from automojo.analysis.statistical.engine.observationengine import ObservationEngine
from automojo.analysis.statistical.execution.compiledstep import CompiledStep
from automojo.analysis.statistical.readers.setreader import SetReader


def _transform(pdv):
    """
        Fully vectorizable.
    """
    pdv["gross"] = pdv["qty"] * pdv["price"]
    pdv["net"] = pdv["gross"] * (1 - pdv["disc"])
    pdv["tax"] = pdv["net"] * 0.2
    pdv["total"] = pdv["net"] + pdv["tax"]
    return


def _mixed(pdv):
    """
        Vector arithmetic plus a sequential spine.
    """
    pdv["gross"] = pdv["qty"] * pdv["price"]
    pdv["net"] = pdv["gross"] * (1 - pdv["disc"])
    pdv["prev_net"] = pdv.lag(pdv["net"])
    if pdv.first["region"]:
        pdv["running"] = 0
    pdv["running"] = pdv["running"] + pdv["net"]
    return


def _exotic(pdv):
    """
        Outside the sublanguage -- fallback path.
    """
    pdv["x"] = sum(int(c) for c in str(pdv["qty"]))
    return


def _demoted(pdv):
    """
        ``flag`` is vectorizable in isolation, but it reads ``running`` --
        which is sequentially produced -- so it must be demoted into the loop.
    """
    pdv["gross"] = pdv["qty"] * pdv["price"]
    if pdv.first["region"]:
        pdv["running"] = 0
    pdv["running"] = pdv["running"] + pdv["gross"]
    pdv["flag"] = pdv["running"] > 100
    return


def _reference(rows, logic, by=None, retain=None):
    if by is None:
        by_list = []
    else:
        by_list = by
    if retain is None:
        retain_map = {}
    else:
        retain_map = retain
    reader = SetReader(source=list(rows), by=by_list)
    engine = ObservationEngine(reader=reader, logic=logic, by=by_list,
                               retain=retain_map)
    rtnval = list(engine)
    return rtnval


def test_pure_arithmetic_plans_as_vector():
    """
        A pure arithmetic step plans as ``"vector"``.
    """
    step = CompiledStep(logic=_transform)
    path, _, _ = step.plan(source_cols=["qty", "price", "disc"])
    same = path == "vector"
    assert same is True
    return


def test_vector_output_matches_reference_engine():
    """
        The vector-path output is bit-equal to the reference engine.
    """
    rows = [{"qty": 2, "price": 60.0, "disc": 0.1},
            {"qty": 1, "price": 200.0, "disc": 0.0}]
    step = CompiledStep(logic=_transform)
    same = step.run(rows=rows) == _reference(rows, _transform)
    assert same is True
    return


def test_mixed_plans_as_hybrid():
    """
        A step with vector arithmetic and a sequential spine plans as
        ``"hybrid"``.
    """
    step = CompiledStep(logic=_mixed, by=["region"], retain={"running": 0})
    path, _, _ = step.plan(source_cols=["region", "qty", "price", "disc"])
    same = path == "hybrid"
    assert same is True
    return


def test_hybrid_output_matches_reference_engine():
    """
        The hybrid-path output is bit-equal to the reference engine.
    """
    rows = [{"region": "E", "qty": 2, "price": 60.0, "disc": 0.1},
            {"region": "E", "qty": 1, "price": 200.0, "disc": 0.0},
            {"region": "W", "qty": 3, "price": 50.0, "disc": 0.2}]
    step = CompiledStep(logic=_mixed, by=["region"], retain={"running": 0})
    same = step.run(rows=rows) == _reference(rows, _mixed, by=["region"],
                                             retain={"running": 0})
    assert same is True
    return


def test_unsupported_logic_plans_as_fallback():
    """
        Logic outside the sublanguage plans as ``"fallback"``.
    """
    step = CompiledStep(logic=_exotic)
    path, _, _ = step.plan(source_cols=["qty"])
    same = path == "fallback"
    assert same is True
    return


def test_fallback_output_matches_reference_engine():
    """
        The fallback-path output is bit-equal to the reference engine.
    """
    rows = [{"qty": 12}, {"qty": 7}]
    step = CompiledStep(logic=_exotic)
    same = step.run(rows=rows) == _reference(rows, _exotic)
    assert same is True
    return


def test_demoted_statement_moves_into_loop():
    """
        The vectorizable ``flag`` assignment reads ``running`` (sequential),
        so the scheduler demotes it into the loop.
    """
    step = CompiledStep(logic=_demoted, by=["region"], retain={"running": 0})
    _, batch, loop = step.plan(source_cols=["region", "qty", "price"])
    flag_targets = [s.target for s in loop
                    if getattr(s, "target", None) is not None]
    flag_in_loop = "flag" in flag_targets
    assert flag_in_loop is True
    return
