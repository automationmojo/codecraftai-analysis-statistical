"""
    Columnar tests that consume the :mod:`testbase` ``transform_inputs``
    factory rather than constructing input data inline.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"



from automojo.analysis.statistical.columnar.columnarstep import ColumnarStep
from automojo.analysis.statistical.engine.observationengine import ObservationEngine
from automojo.analysis.statistical.readers.setreader import SetReader


def _transform(pdv):
    """
        Pure-vector transform fixture.
    """
    pdv["gross"] = pdv["qty"] * pdv["price"]
    pdv["net"] = pdv["gross"] * (1 - pdv["disc"])
    pdv["tax"] = pdv["net"] * 0.2
    pdv["total"] = pdv["net"] + pdv["tax"]
    return


def test_columnar_to_dicts_matches_reference_via_factory(transform_inputs: list[dict]):
    """
        ``ColumnFrame.to_dicts()`` is bit-equal to the reference engine on
        the factory-supplied transform inputs.

        :param transform_inputs: Dataset injected by the
                                 ``transform_inputs`` parameter origination.
    """
    frame = ColumnarStep(logic=_transform).run_columnar(data=transform_inputs)
    reference = list(ObservationEngine(reader=SetReader(source=list(transform_inputs)),
                                       logic=_transform))
    same = frame.to_dicts() == reference
    assert same is True
    return
