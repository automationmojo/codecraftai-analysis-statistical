"""
    Scope-level originations for the analysis-statistical singlehost tests.

    Originations attach :mod:`testbase` resource factories at this scope so
    every descendant test module can consume them by parameter name. Tests
    can still construct fixtures inline; consuming the factory is the
    canonical pattern for shared, scope-managed test data.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from ccai import testbase

from ccai.testshared.factories.sasdatasets import (
    create_lag_inputs,
    create_merge_sources,
    create_sales_dataset,
    create_transform_inputs,
)


testbase.originate.parameter(create_sales_dataset, identifier="sales_dataset")
testbase.originate.parameter(create_merge_sources, identifier="merge_sources")
testbase.originate.parameter(create_lag_inputs, identifier="lag_inputs")
testbase.originate.parameter(create_transform_inputs, identifier="transform_inputs")
