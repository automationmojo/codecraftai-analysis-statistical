"""
    Tests for the IR pipeline: :class:`AstLowerer`, :class:`Classifier`,
    :class:`IrInterpreter`, :class:`LogicCompiler`.

    The IR-interpreted callable is the oracle equivalence check: for every
    supported logic shape its output must match the reference engine running
    the original function.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from automojo.analysis.statistical.engine.observationengine import ObservationEngine
from automojo.analysis.statistical.ir.astlowerer import lower
from automojo.analysis.statistical.ir.classifier import Classifier
from automojo.analysis.statistical.ir.logiccompiler import compile_logic
from automojo.analysis.statistical.ir.nodes.assignnode import AssignNode
from automojo.analysis.statistical.ir.nodes.firstlastnode import FirstLastNode
from automojo.analysis.statistical.ir.nodes.ifnode import IfNode
from automojo.analysis.statistical.ir.nodes.lagnode import LagNode
from automojo.analysis.statistical.ir.unsupportederror import UnsupportedError
from automojo.analysis.statistical.readers.setreader import SetReader


def _pure_arithmetic(pdv):
    """
        Fully-vectorizable logic. No cross-row state.
    """
    pdv["gross"] = pdv["qty"] * pdv["price"]
    pdv["net"] = pdv["gross"] * (1 - pdv["disc"])
    return


def _mixed(pdv):
    """
        Mixed: arithmetic vectorizable, lag sequential, retain sequential.
    """
    pdv["gross"] = pdv["qty"] * pdv["price"]
    pdv["net"] = pdv["gross"] * (1 - pdv["disc"])
    pdv["prev_net"] = pdv.lag(pdv["net"])
    if pdv["net"] > 100:
        pdv["band"] = 1
    else:
        pdv["band"] = 0
    if pdv.first["region"]:
        pdv["running"] = 0
    pdv["running"] = pdv["running"] + pdv["net"]
    return


def _exotic(pdv):
    """
        Logic outside the sublanguage (comprehension + built-in call).
    """
    pdv["x"] = sum(int(c) for c in str(pdv["qty"]))
    return


def test_lowerer_produces_expected_top_level_shapes():
    """
        Every top-level statement in ``_mixed`` lowers to an :class:`AssignNode`
        or :class:`IfNode`, in source order.
    """
    stmts = lower(logic=_mixed)
    kinds = [type(s).__name__ for s in stmts]
    expected = ["AssignNode", "AssignNode", "AssignNode",
                "IfNode", "IfNode", "AssignNode"]
    same = kinds == expected
    assert same is True
    return


def test_lowerer_captures_lag_call_site():
    """
        A ``pdv.lag(...)`` call lowers to a :class:`LagNode`.
    """
    stmts = lower(logic=_mixed)
    third = stmts[2]
    is_assign = isinstance(third, AssignNode)
    lag_present = isinstance(third.expr, LagNode)
    assert is_assign is True
    assert lag_present is True
    return


def test_lowerer_captures_first_last():
    """
        ``pdv.first['region']`` lowers to a :class:`FirstLastNode`.
    """
    stmts = lower(logic=_mixed)
    fifth = stmts[4]
    is_if = isinstance(fifth, IfNode)
    is_first_last = isinstance(fifth.test, FirstLastNode)
    by_ok = fifth.test.by == "region"
    assert is_if is True
    assert is_first_last is True
    assert by_ok is True
    return


def test_lowerer_rejects_logic_outside_sublanguage():
    """
        ``_exotic`` uses a generator expression -- not in the sublanguage.
    """
    raised = False
    try:
        lower(logic=_exotic)
    except UnsupportedError:
        raised = True
    assert raised is True
    return


def test_classifier_marks_pure_arithmetic_as_vector():
    """
        Every statement in ``_pure_arithmetic`` classifies as vector.
    """
    stmts = lower(logic=_pure_arithmetic)
    summary = Classifier.summarize(stmts=stmts)
    same = summary["vector"] == summary["total"]
    assert same is True
    return


def test_classifier_marks_lag_assignment_as_sequential():
    """
        The lag assignment in ``_mixed`` is sequential.
    """
    stmts = lower(logic=_mixed)
    classified = Classifier.classify(stmts=stmts)
    lag_assign_classification = classified[2][1]
    same = lag_assign_classification == "seq"
    assert same is True
    return


def test_ir_interpreted_logic_matches_reference_engine_output():
    """
        Running the IR-interpreted callable produces output bit-equal to
        running the original ``_mixed`` against the reference engine.
    """
    rows = [{"region": "E", "qty": 2, "price": 60, "disc": 0.1},
            {"region": "E", "qty": 1, "price": 200, "disc": 0.0},
            {"region": "W", "qty": 3, "price": 50, "disc": 0.2}]

    ref = list(ObservationEngine(reader=SetReader(source=list(rows),
                                                  by=["region"]),
                                 logic=_mixed, by=["region"],
                                 retain={"running": 0}))
    compiled, mode = compile_logic(logic=_mixed)
    got = list(ObservationEngine(reader=SetReader(source=list(rows),
                                                  by=["region"]),
                                 logic=compiled, by=["region"],
                                 retain={"running": 0}))
    mode_ok = mode == "ir"
    output_ok = ref == got
    assert mode_ok is True
    assert output_ok is True
    return


def test_logic_compiler_falls_back_for_unsupported_logic():
    """
        ``_exotic`` cannot be lowered; the compiler returns the original
        function with ``mode == "fallback"``.
    """
    compiled, mode = compile_logic(logic=_exotic)
    rows = [{"qty": 12}, {"qty": 7}]
    out = list(ObservationEngine(reader=SetReader(source=rows),
                                 logic=compiled))
    mode_ok = mode == "fallback"
    rows_emitted = len(out) == 2
    assert mode_ok is True
    assert rows_emitted is True
    return
