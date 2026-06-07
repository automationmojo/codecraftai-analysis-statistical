"""
    Tests for :class:`SetReader`. Verifies single-source iteration with and
    without BY-keys and that ``next_key`` is reported for BY-grouped sources.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from ccai.analysis.statistical.readers.setreader import SetReader


def test_set_reader_emits_every_row_in_order():
    """
        Every row is emitted exactly once in source order.
    """
    rows = [{"x": 1}, {"x": 2}, {"x": 3}]
    reader = SetReader(source=list(rows))
    out = []
    while reader.has_more() is True:
        row, in_flags, cur_key, next_key = reader.next_obs()
        out.append(row)
    same = out == rows
    assert same is True
    return


def test_set_reader_reports_no_in_flags():
    """
        Single-source readers report an empty ``in_flags`` map.
    """
    reader = SetReader(source=[{"x": 1}])
    _, in_flags, _, _ = reader.next_obs()
    empty = len(in_flags) == 0
    assert empty is True
    return


def test_set_reader_by_key_is_tuple_of_named_columns():
    """
        With ``by=['region', 'customer']`` the cur_key is the tuple of those
        column values.
    """
    rows = [{"region": "East", "customer": "A", "x": 1},
            {"region": "East", "customer": "B", "x": 2}]
    reader = SetReader(source=rows, by=["region", "customer"])
    _, _, cur_key, next_key = reader.next_obs()
    cur_ok = cur_key == ("East", "A")
    next_ok = next_key == ("East", "B")
    assert cur_ok is True
    assert next_ok is True
    return


def test_set_reader_next_key_is_none_at_eof():
    """
        ``next_key`` is ``None`` on the last row of the source.
    """
    rows = [{"k": 1}, {"k": 2}]
    reader = SetReader(source=rows, by=["k"])
    reader.next_obs()
    _, _, _, next_key = reader.next_obs()
    none = next_key is None
    assert none is True
    return
