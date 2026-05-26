==============================
automojo-analysis-statistical
==============================

Patterns for authoring and porting statistical analysis jobs to Python whose
results are *directly comparable* to the equivalent SAS jobs. Built around a
reference SAS DATA-step execution model (the correctness oracle), an IR
front end for inspectable user logic, a hybrid columnar / sequential
executor for speed, and database source readers that follow the
SAS/ACCESS-engine pattern.

Public namespace: ``automojo.analysis.statistical``.

Documentation
=============
- `Architecture / design <specs/DESIGN.md>`_
- `Build roadmap <specs/ROADMAP.md>`_
- `Overview & mental model <userguide/20-00-overview-and-mental-model.rst>`_
- `Porting SAS jobs to Python <userguide/20-07-porting-sas-jobs-to-python.rst>`_

Quick example
=============

.. code-block:: python

    from automojo.analysis.statistical import (ObservationEngine, SetReader)

    sales = [{"region": "East", "customer": "A", "amount": 10},
             {"region": "East", "customer": "A", "amount": 15},
             {"region": "East", "customer": "B", "amount": 7}]

    def accumulate(pdv):
        if pdv.first["customer"] is True:
            pdv["total"] = 0
        pdv["total"] = pdv["total"] + pdv["amount"]
        if pdv.last["customer"] is True:
            pdv.output()
        return

    rows = list(ObservationEngine(
        reader=SetReader(source=sales, by=["region", "customer"]),
        logic=accumulate, by=["region", "customer"],
        retain={"total": 0}))

Tests
=====

This package uses ``testbase`` exclusively. After ``rehome-repository`` and
``setup-environment`` complete::

    source .venv/bin/activate
    testbase testing run --root source/testroots/automojo \
        --includes=automojo.tests.singlehost --output=./.output
