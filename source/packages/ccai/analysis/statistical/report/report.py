"""
    .. module:: report
        :synopsis: The :class:`Report` -- the result of running the migration
                   / optimization advisor against a single user logic
                   function. Carries an execution-path label, the per-
                   statement :class:`Line` list, and an optional unsupported
                   cause for fallback steps.

    .. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from dataclasses import dataclass, field

from ccai.analysis.statistical.report.line import Line


@dataclass
class Report:
    """
        Migration / optimization advisor result.

        :ivar path: One of ``"vector"``, ``"hybrid"``, ``"fallback"``.
        :ivar lines: Per-statement :class:`Line` entries (empty when ``path``
                     is ``"fallback"``).
        :ivar unsupported: A short description of the unsupported construct
                           when ``path`` is ``"fallback"``.
    """

    path: str
    lines: list[Line] = field(default_factory=list)
    unsupported: str = ""

    @property
    def n_batch(self) -> int:
        """
            Number of statements that ended up on the fast path.

            :returns: The batch-statement count.
        """
        count = 0
        for line in self.lines:
            if line.klass == "batch":
                count += 1
        rtnval = count
        return rtnval

    @property
    def n_total(self) -> int:
        """
            Total statement count.

            :returns: The number of report lines.
        """
        rtnval = len(self.lines)
        return rtnval

    @property
    def text(self) -> str:
        """
            A human-readable rendering of the report.

            :returns: The text rendering.
        """
        rtnval = self._render()
        return rtnval

    def _render(self) -> str:
        """
            Build the text rendering.

            :returns: The text rendering.
        """
        if self.path == "fallback":
            lines_out = [
                "PATH: fallback (row loop, no vectorization)",
                "  cause: {}".format(self.unsupported),
                "  fix:   rewrite in the sublanguage (assignment / if / lag / "
                "dif / first./last. / output) to enable any fast path.",
            ]
        else:
            fraction = "{}/{}".format(self.n_batch, self.n_total)
            if self.n_total == 0:
                pct = 0
            else:
                pct = 100 * self.n_batch // self.n_total
            head = "PATH: {} -- {} statements vectorized ({}%)".format(
                self.path, fraction, pct)
            lines_out = [head]
            for line in self.lines:
                if line.klass == "batch":
                    mark = "FAST"
                else:
                    mark = "loop"
                lines_out.append("  [{}] {:<10} {}".format(mark, line.stmt,
                                                            line.reason))
            advice = self._advice()
            if len(advice) > 0:
                lines_out.append("")
                lines_out.extend(advice)
        rtnval = "\n".join(lines_out)
        return rtnval

    def _advice(self) -> list[str]:
        """
            Synthesize the per-category advice block.

            :returns: A list of advice lines (possibly empty).
        """
        by_category: dict = {}
        for line in self.lines:
            if line.klass == "loop":
                by_category.setdefault(line.category, []).append(line)

        advice: list[str] = []

        dependency_lines = by_category.get("dependency", [])
        if len(dependency_lines) > 0:
            blockers: set = set()
            for line in dependency_lines:
                for blocker in line.blockers:
                    blockers.add(blocker)
            sorted_blockers = sorted(blockers)
            advice.append(
                "  REALIGN: {} statement(s) would vectorize but read "
                "sequential value(s) {}. If those are produced in a separate "
                "upstream step, these move to FAST.".format(
                    len(dependency_lines), sorted_blockers))

        tool_lines = by_category.get("tool-limited", [])
        if len(tool_lines) > 0:
            advice.append(
                "  TOOL:    {} vectorizable conditional(s) run in the loop "
                "today (where()-vectorization not yet built). Not a code "
                "problem.".format(len(tool_lines)))

        irreducible_count = (len(by_category.get("irreducible", []))
                             + len(by_category.get("cardinality", [])))
        if irreducible_count > 0:
            advice.append(
                "  JIT:     {} statement(s) are irreducibly sequential "
                "(inherent cross-row logic / output). Speed here needs the "
                "compiled loop, not realignment.".format(irreducible_count))

        if len(advice) == 0 and self.path == "vector":
            advice.append(
                "  Already fully vectorized; columnar output would remove "
                "the remaining per-row materialization cost.")
        rtnval = advice
        return rtnval
