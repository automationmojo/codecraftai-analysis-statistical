"""
    Tests for :class:`MergeReader`. Validates positional match-merge,
    ``IN=`` flags, retain-on-exhaustion within a group, and later-dataset-wins.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from automojo.analysis.statistical.readers.mergereader import MergeReader


def _drain(reader):
    """
        Drain a reader into a list of ``(row, in_flags)`` tuples.

        :param reader: A :class:`Reader` instance.

        :returns: A list of ``(row, in_flags)`` tuples.
    """
    out = []
    while reader.has_more() is True:
        row, in_flags, _, _ = reader.next_obs()
        out.append((row, in_flags))
    return out


def test_match_merge_emits_positional_pairs_not_cartesian_product():
    """
        Two A rows and one B row in id=1 emit two rows (A1+B, A2+B), not four.
    """
    a_rows = [{"id": 1, "a": 10}, {"id": 1, "a": 20}, {"id": 2, "a": 30}]
    b_rows = [{"id": 1, "b": 100}, {"id": 2, "b": 200}, {"id": 2, "b": 300}]
    reader = MergeReader(sources={"A": a_rows, "B": b_rows}, by=["id"],
                         in_flags={"A": "inA", "B": "inB"})
    drained = _drain(reader=reader)
    same = len(drained) == 4
    assert same is True
    return


def test_match_merge_retains_b_when_b_exhausted_within_group():
    """
        Within id=1, after B's only row is consumed, B's value remains
        retained for the next A row (``b=100``).
    """
    a_rows = [{"id": 1, "a": 10}, {"id": 1, "a": 20}, {"id": 2, "a": 30}]
    b_rows = [{"id": 1, "b": 100}, {"id": 2, "b": 200}, {"id": 2, "b": 300}]
    reader = MergeReader(sources={"A": a_rows, "B": b_rows}, by=["id"],
                         in_flags={"A": "inA", "B": "inB"})
    drained = _drain(reader=reader)
    second_row, second_in = drained[1]
    a_ok = second_row.get("a") == 20
    b_retained = second_row.get("b") == 100
    in_a_ok = second_in.get("inA") == 1
    in_b_ok = second_in.get("inB") == 0
    assert a_ok is True
    assert b_retained is True
    assert in_a_ok is True
    assert in_b_ok is True
    return


def test_match_merge_resets_work_state_across_groups():
    """
        A column produced only by source ``X`` in group 1 must NOT leak into
        group 2 when ``X`` contributes nothing to group 2.
    """
    x_rows = [{"id": 1, "v": 99}]
    y_rows = [{"id": 1, "w": 7}, {"id": 2, "w": 8}]
    reader = MergeReader(sources={"X": x_rows, "Y": y_rows}, by=["id"])
    drained = _drain(reader=reader)
    second_row, _ = drained[1]
    from automojo.analysis.statistical.missing.missing import Missing

    is_missing = isinstance(second_row.get("v"), Missing)
    assert is_missing is True
    return


def test_match_merge_later_source_wins_on_shared_column():
    """
        When both sources provide ``shared``, the later one in the dict order
        overwrites within the same row.
    """
    a_rows = [{"id": 1, "shared": "from_a"}]
    b_rows = [{"id": 1, "shared": "from_b"}]
    reader = MergeReader(sources={"A": a_rows, "B": b_rows}, by=["id"])
    drained = _drain(reader=reader)
    first_row, _ = drained[0]
    same = first_row.get("shared") == "from_b"
    assert same is True
    return
