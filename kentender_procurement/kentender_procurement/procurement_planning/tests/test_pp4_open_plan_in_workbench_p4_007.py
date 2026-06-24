# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-007 — Open in Workbench action."""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase


def _pkg_public(*parts: str) -> Path:
	return Path(__file__).resolve().parents[2].joinpath("public", *parts)


class TestPP4OpenPlanInWorkbenchP4007(UnitTestCase):
	def test_plan_summary_exposes_open_in_workbench_button(self) -> None:
		path = _pkg_public("js", "pp3_planning_plan_summary.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn('data-testid="pp3-open-plan-in-workbench"', source)
		self.assertIn("/desk/procurement-planning", source)
		self.assertIn("open_workbench", source)
