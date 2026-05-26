"""
    Tests for :class:`Missing` and the :func:`missing` factory: ordering and
    identity caching. The Missing family must satisfy
    ``._ < . < .A < .B < ... < .Z < every real number``.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from automojo.analysis.statistical.missing.missing import Missing
from automojo.analysis.statistical.missing.missingfactory import MISSING, missing


def test_missing_instances_are_cached_by_tag():
    """
        :func:`missing` returns the same object for the same tag.
    """
    a_one = missing("A")
    a_two = missing("A")
    same = a_one is a_two
    assert same is True
    return


def test_missing_factory_uppercases_alpha_tags():
    """
        Alpha tags are normalized to upper-case before lookup.
    """
    upper = missing("A")
    lower = missing("a")
    same = upper is lower
    assert same is True
    return


def test_underscore_missing_sorts_before_plain_missing():
    """
        Underscore missing sorts below the plain missing.
    """
    less = missing("_") < MISSING
    assert less is True
    return


def test_plain_missing_sorts_before_special_missings():
    """
        Plain missing sorts below ``.A``.
    """
    less = missing("A") > MISSING
    assert less is True
    return


def test_special_missings_sort_alphabetically():
    """
        ``.A`` sorts below ``.B``.
    """
    less = missing("A") < missing("B")
    assert less is True
    return


def test_all_missings_sort_below_any_real_number():
    """
        Every form of missing sorts below the smallest finite number used here.
    """
    candidates = [missing("_"), MISSING, missing("A"), missing("Z")]
    all_below = True
    for candidate in candidates:
        if not (candidate < 0):
            all_below = False
            break
    assert all_below is True
    return


def test_sorted_order_matches_sas_specification():
    """
        Sorting a mixed list reproduces the SAS-ordered sequence.
    """
    values = [3, missing("A"), missing("_"), 1, MISSING, missing("B")]
    expected = [missing("_"), MISSING, missing("A"), missing("B"), 1, 3]
    ordered = sorted(values)
    same = ordered == expected
    assert same is True
    return


def test_missing_equality_compares_tag():
    """
        Two missings are equal iff their tags are equal.
    """
    same = missing("A") == missing("A")
    different = missing("A") == missing("B")
    assert same is True
    assert different is False
    return


def test_missing_is_constructable_directly():
    """
        :class:`Missing` is publicly constructable and returns the cached
        instance for an existing tag.
    """
    direct = Missing("A")
    via_factory = missing("A")
    same = direct is via_factory
    assert same is True
    return
