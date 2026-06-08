"""
    Tests for :class:`DialectDeclaration` across all four supported dialects.
    Verifies that the NAME_TABLE entries route to the expected canonical
    engine triples and that unknown / unmappable types raise loudly.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from ccai.analysis.statistical.database.dialectdeclaration import (
    DialectDeclaration, dialect_declare)


def test_postgres_numeric_low_precision_routes_to_num():
    """
        ``NUMERIC(8,2)`` in PostgreSQL routes to ``num``.
    """
    decl = DialectDeclaration.resolve(name="p", type_string="NUMERIC(8,2)",
                                      dialect="postgresql")
    same = decl["stype"] == "num"
    assert same is True
    return


def test_postgres_numeric_high_precision_routes_to_decimal():
    """
        ``NUMERIC(38,2)`` in PostgreSQL routes to ``decimal``.
    """
    decl = DialectDeclaration.resolve(name="p", type_string="NUMERIC(38,2)",
                                      dialect="postgresql")
    same = decl["stype"] == "decimal"
    assert same is True
    return


def test_mysql_decimal_routes_by_precision():
    """
        MySQL ``DECIMAL`` routes to ``num`` at low precision and ``decimal``
        at high precision.
    """
    low = DialectDeclaration.resolve(name="p", type_string="DECIMAL(10,2)",
                                     dialect="mysql")
    high = DialectDeclaration.resolve(name="p", type_string="DECIMAL(38,2)",
                                      dialect="mysql")
    low_ok = low["stype"] == "num"
    high_ok = high["stype"] == "decimal"
    assert low_ok is True
    assert high_ok is True
    return


def test_sqlserver_money_routes_to_decimal_when_no_precision_given():
    """
        SQL Server ``MONEY`` declared without precision routes through the
        numeric resolver. With no precision specified, defaults to ``num``.
    """
    decl = DialectDeclaration.resolve(name="amt", type_string="MONEY",
                                      dialect="sqlserver")
    same = decl["stype"] == "num"
    assert same is True
    return


def test_oracle_date_attaches_default_date_format():
    """
        Oracle ``DATE`` produces a num slot with the ``DATE9.`` format
        attached.
    """
    decl = DialectDeclaration.resolve(name="hired", type_string="DATE",
                                      dialect="oracle")
    same_stype = decl["stype"] == "num"
    same_fmt = decl["fmt"] == "DATE9."
    assert same_stype is True
    assert same_fmt is True
    return


def test_oracle_timestamp_attaches_datetime_format():
    """
        Oracle ``TIMESTAMP`` produces a num slot with ``DATETIME19.``
        attached.
    """
    decl = DialectDeclaration.resolve(name="ts", type_string="TIMESTAMP",
                                      dialect="oracle")
    same_fmt = decl["fmt"] == "DATETIME19."
    assert same_fmt is True
    return


def test_oracle_clob_routes_to_char():
    """
        Oracle ``CLOB`` routes to ``char`` (default length).
    """
    decl = DialectDeclaration.resolve(name="doc", type_string="CLOB",
                                      dialect="oracle")
    same = decl["stype"] == "char"
    assert same is True
    return


def test_dialect_declare_convenience_function_matches_class_method():
    """
        The module-level :func:`dialect_declare` helper produces the same
        declaration as :meth:`DialectDeclaration.resolve`.
    """
    direct = DialectDeclaration.resolve(name="x", type_string="VARCHAR(20)",
                                        dialect="postgresql")
    convenience = dialect_declare(name="x", type_string="VARCHAR(20)",
                                  dialect="postgresql")
    same = direct == convenience
    assert same is True
    return


def test_unparseable_type_string_raises_value_error():
    """
        A malformed type string raises :class:`ValueError`.
    """
    raised = False
    try:
        DialectDeclaration.resolve(name="x", type_string="!!!",
                                   dialect="postgresql")
    except ValueError:
        raised = True
    assert raised is True
    return
