"""
    Tests for :class:`ReportBuilder` -- the migration / optimization advisor.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from ccai.analysis.statistical.report.reportbuilder import ReportBuilder


def _transform(pdv):
    """
        Fully vectorizable.
    """
    pdv["gross"] = pdv["qty"] * pdv["price"]
    pdv["net"] = pdv["gross"] * (1 - pdv["disc"])
    pdv["tax"] = pdv["net"] * 0.2
    return


def _mixed(pdv):
    """
        Mixed: batch + irreducible + tool-limited + dependency.
    """
    pdv["gross"] = pdv["qty"] * pdv["price"]
    pdv["net"] = pdv["gross"] * (1 - pdv["disc"])
    pdv["prev"] = pdv.lag(pdv["net"])
    if pdv["net"] > 100:
        pdv["band"] = 2
    else:
        pdv["band"] = 1
    if pdv.first["region"]:
        pdv["running"] = 0
    pdv["running"] = pdv["running"] + pdv["net"]
    pdv["flag"] = pdv["running"] > 1000
    return


def _exotic(pdv):
    """
        Outside the sublanguage -- fallback.
    """
    pdv["x"] = sum(int(c) for c in str(pdv["qty"]))
    return


def test_pure_transform_reports_path_vector():
    """
        Fully vectorizable logic reports ``path == "vector"`` and every line
        on the fast path.
    """
    report = ReportBuilder.report(logic=_transform,
                                  source_cols=["qty", "price", "disc"])
    path_ok = report.path == "vector"
    all_batch = report.n_batch == report.n_total
    assert path_ok is True
    assert all_batch is True
    return


def test_mixed_logic_reports_path_hybrid():
    """
        Mixed logic reports ``path == "hybrid"``.
    """
    report = ReportBuilder.report(logic=_mixed,
                                  source_cols=["region", "qty", "price", "disc"],
                                  retain={"running"})
    same = report.path == "hybrid"
    assert same is True
    return


def test_mixed_logic_has_each_loop_category_represented():
    """
        ``_mixed`` includes statements in every loop category:
        irreducible (lag, first.), tool-limited (vectorizable conditional),
        and dependency (reads ``running``).
    """
    report = ReportBuilder.report(logic=_mixed,
                                  source_cols=["region", "qty", "price", "disc"],
                                  retain={"running"})
    categories = {line.category for line in report.lines}
    has_irreducible = "irreducible" in categories
    has_tool_limited = "tool-limited" in categories
    has_dependency = "dependency" in categories
    assert has_irreducible is True
    assert has_tool_limited is True
    assert has_dependency is True
    return


def test_exotic_logic_reports_fallback_path_with_cause():
    """
        Logic outside the sublanguage reports the fallback path with a cause.
    """
    report = ReportBuilder.report(logic=_exotic, source_cols=["qty"])
    path_ok = report.path == "fallback"
    has_cause = len(report.unsupported) > 0
    assert path_ok is True
    assert has_cause is True
    return


def test_report_text_renders_without_error():
    """
        The human-readable rendering produces non-empty text for each path.
    """
    a = ReportBuilder.report(logic=_transform,
                             source_cols=["qty", "price", "disc"]).text
    b = ReportBuilder.report(logic=_mixed,
                             source_cols=["region", "qty", "price", "disc"],
                             retain={"running"}).text
    c = ReportBuilder.report(logic=_exotic, source_cols=["qty"]).text
    a_ok = len(a) > 0
    b_ok = len(b) > 0
    c_ok = len(c) > 0
    assert a_ok is True
    assert b_ok is True
    assert c_ok is True
    return
