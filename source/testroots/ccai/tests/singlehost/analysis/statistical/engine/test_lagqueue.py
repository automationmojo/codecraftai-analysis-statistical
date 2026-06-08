"""
    Direct tests for :class:`LagQueue`. The LAG/DIF stack-frame keying is
    exercised through :class:`ObservationEngine` elsewhere; these tests
    pin the queue behaviour itself so a regression in fixed-depth FIFO
    semantics surfaces immediately.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from ccai.analysis.statistical.engine.lagqueue import LagQueue
from ccai.analysis.statistical.missing.missingfactory import MISSING


def test_lagqueue_first_read_returns_missing_at_depth_one():
    """
        The first ``push_and_read`` against a depth-1 queue returns the
        pre-seeded plain MISSING.
    """
    queue = LagQueue(depth=1)
    rtnval = queue.push_and_read(value=10)
    same = rtnval is MISSING
    assert same is True
    return


def test_lagqueue_returns_the_value_pushed_one_step_back():
    """
        At depth 1 the second read returns the first value pushed.
    """
    queue = LagQueue(depth=1)
    queue.push_and_read(value=10)
    second = queue.push_and_read(value=20)
    same = second == 10
    assert same is True
    return


def test_lagqueue_depth_three_returns_third_prior_value():
    """
        A depth-3 queue returns the value pushed three steps ago after the
        seed window has been consumed.
    """
    queue = LagQueue(depth=3)
    queue.push_and_read(value=1)
    queue.push_and_read(value=2)
    queue.push_and_read(value=3)
    fourth = queue.push_and_read(value=4)
    fifth = queue.push_and_read(value=5)
    fourth_ok = fourth == 1
    fifth_ok = fifth == 2
    assert fourth_ok is True
    assert fifth_ok is True
    return


def test_lagqueue_seeds_missing_for_every_slot_until_first_real_value():
    """
        For depth ``n``, the first ``n`` reads return :data:`MISSING`.
    """
    queue = LagQueue(depth=2)
    first = queue.push_and_read(value=100)
    second = queue.push_and_read(value=200)
    third = queue.push_and_read(value=300)
    first_ok = first is MISSING
    second_ok = second is MISSING
    third_ok = third == 100
    assert first_ok is True
    assert second_ok is True
    assert third_ok is True
    return
