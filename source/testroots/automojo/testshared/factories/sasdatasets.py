"""
    Shared :mod:`testbase` resource factories that supply representative
    SAS-style row datasets to tests across the analysis-statistical test
    tree. Tests consume these by name in their function signature once the
    factories are originated in the tree's scope ``__init__.py``.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from collections.abc import Generator

from automojo import testbase


@testbase.register.resource_factory()
def create_sales_dataset(constraints=None) -> Generator[list[dict], None, None]:
    """
        Yield the canonical BY-group accumulation fixture: five rows across
        two regions and three customers.

        :param constraints: Optional constraint dictionary (unused; declared
                            for parity with the :mod:`testbase` factory API).

        :returns: A generator yielding the dataset rows.
    """
    if constraints is None:
        constraint_map = {}
    else:
        constraint_map = constraints
    _ = constraint_map

    dataset = [
        {"region": "East", "customer": "A", "amount": 10},
        {"region": "East", "customer": "A", "amount": 15},
        {"region": "East", "customer": "B", "amount": 7},
        {"region": "West", "customer": "C", "amount": 20},
        {"region": "West", "customer": "C", "amount": 5},
    ]
    yield dataset


@testbase.register.resource_factory()
def create_merge_sources(constraints=None) -> Generator[dict, None, None]:
    """
        Yield the canonical match-merge fixture: two sorted source lists
        sharing an ``id`` key.

        :param constraints: Optional constraint dictionary (unused).

        :returns: A generator yielding ``{"A": [...], "B": [...]}``.
    """
    if constraints is None:
        constraint_map = {}
    else:
        constraint_map = constraints
    _ = constraint_map

    sources = {
        "A": [{"id": 1, "a": 10}, {"id": 1, "a": 20}, {"id": 2, "a": 30}],
        "B": [{"id": 1, "b": 100}, {"id": 2, "b": 200}, {"id": 2, "b": 300}],
    }
    yield sources


@testbase.register.resource_factory()
def create_lag_inputs(constraints=None) -> Generator[list[dict], None, None]:
    """
        Yield the canonical LAG / DIF fixture: five sequential integers.

        :param constraints: Optional constraint dictionary (unused).

        :returns: A generator yielding the dataset rows.
    """
    if constraints is None:
        constraint_map = {}
    else:
        constraint_map = constraints
    _ = constraint_map

    dataset = [{"x": value} for value in (1, 2, 3, 4, 5)]
    yield dataset


@testbase.register.resource_factory()
def create_transform_inputs(constraints=None) -> Generator[list[dict], None, None]:
    """
        Yield the canonical fully-vectorizable transform fixture: rows with
        ``qty``, ``price``, ``disc`` columns.

        :param constraints: Optional constraint dictionary (unused).

        :returns: A generator yielding the dataset rows.
    """
    if constraints is None:
        constraint_map = {}
    else:
        constraint_map = constraints
    _ = constraint_map

    dataset = [
        {"qty": 2, "price": 60.0, "disc": 0.1},
        {"qty": 1, "price": 200.0, "disc": 0.0},
    ]
    yield dataset
