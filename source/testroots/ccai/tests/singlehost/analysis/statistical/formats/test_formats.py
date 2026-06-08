"""
    Tests for the format / informat registries and the built-in converters.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from ccai.analysis.statistical.formats.formatregistry import FormatRegistry
from ccai.analysis.statistical.formats.formatspec import FormatSpec
from ccai.analysis.statistical.formats.informatregistry import InformatRegistry


def test_format_spec_parses_dollar_with_decimals():
    """
        ``DOLLAR8.2`` -> name="DOLLAR", width=8, decimals=2.
    """
    parsed = FormatSpec.parse(spec="DOLLAR8.2")
    name_ok = parsed.name == "DOLLAR"
    width_ok = parsed.width == 8
    decimals_ok = parsed.decimals == 2
    assert name_ok is True
    assert width_ok is True
    assert decimals_ok is True
    return


def test_format_spec_parses_date_with_no_decimals():
    """
        ``DATE9.`` -> name="DATE", width=9, decimals=None.
    """
    parsed = FormatSpec.parse(spec="DATE9.")
    name_ok = parsed.name == "DATE"
    width_ok = parsed.width == 9
    decimals_ok = parsed.decimals is None
    assert name_ok is True
    assert width_ok is True
    assert decimals_ok is True
    return


def test_format_spec_parses_default_spec_for_none():
    """
        ``None`` produces a default spec with empty name and no width.
    """
    parsed = FormatSpec.parse(spec=None)
    name_ok = parsed.name == ""
    width_ok = parsed.width is None
    decimals_ok = parsed.decimals is None
    assert name_ok is True
    assert width_ok is True
    assert decimals_ok is True
    return


def test_dollar_format_applies_thousands_and_decimals():
    """
        ``DOLLAR10.2`` renders ``1234.5`` as ``$1,234.50``.
    """
    rendered = FormatRegistry.apply(value=1234.5, spec="DOLLAR10.2")
    same = rendered == "$1,234.50"
    assert same is True
    return


def test_date_format_uses_sas_epoch():
    """
        ``DATE9.`` renders day-offset 0 as ``01JAN1960``.
    """
    rendered = FormatRegistry.apply(value=0, spec="DATE9.")
    same = rendered == "01JAN1960"
    assert same is True
    return


def test_date_informat_round_trips_with_date_format():
    """
        DATE informat then DATE format reproduces the original text.
    """
    parsed = InformatRegistry.apply(text="01JAN1960", spec="DATE9.")
    same = parsed == 0
    assert same is True
    return


def test_dollar_informat_strips_currency_and_commas():
    """
        DOLLAR informat parses ``$1,234.50`` as ``1234.50``.
    """
    parsed = InformatRegistry.apply(text="$1,234.50", spec="DOLLAR10.2")
    same = parsed == 1234.5
    assert same is True
    return


def test_datetime_format_renders_sas_epoch_zero():
    """
        ``DATETIME19.`` renders second-offset 0 as ``01JAN1960:00:00:00``.
    """
    rendered = FormatRegistry.apply(value=0, spec="DATETIME19.")
    same = rendered == "01JAN1960:00:00:00"
    assert same is True
    return


def test_datetime_informat_round_trips_with_datetime_format():
    """
        DATETIME informat then format reproduces the original text.
    """
    parsed = InformatRegistry.apply(text="01JAN1960:00:00:00",
                                    spec="DATETIME19.")
    rendered = FormatRegistry.apply(value=parsed, spec="DATETIME19.")
    same = rendered == "01JAN1960:00:00:00"
    assert same is True
    return


def test_format_apply_raises_for_unknown_named_spec():
    """
        An unknown *named* format spec raises :class:`KeyError` instead of
        silently falling back to the default display. The empty-named default
        spec still falls back.
    """
    raised = False
    try:
        FormatRegistry.apply(value=1.0, spec="NOTAFORMAT8.2")
    except KeyError:
        raised = True
    fallback = FormatRegistry.apply(value=1.0, spec=None)
    assert raised is True
    assert fallback == "1"
    return


def test_format_apply_returns_missing_text_for_missing_values():
    """
        Applying a format to a :class:`Missing` value yields its canonical
        text form (``.`` / ``._`` / ``.A``).
    """
    from ccai.analysis.statistical.missing.missingfactory import MISSING, missing

    plain = FormatRegistry.apply(value=MISSING, spec="DOLLAR8.2")
    underscore = FormatRegistry.apply(value=missing("_"), spec="DOLLAR8.2")
    alpha = FormatRegistry.apply(value=missing("A"), spec="DOLLAR8.2")

    plain_ok = plain == "."
    underscore_ok = underscore == "._"
    alpha_ok = alpha == ".A"
    assert plain_ok is True
    assert underscore_ok is True
    assert alpha_ok is True
    return
