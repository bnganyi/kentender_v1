# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Regression guard — Workbench root must stay a faithful static design render.

No active-plan banner, gate, or backend fetch may be mounted around the
`needs_planning_default.html` iframe until wiring is explicitly requested.
"""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase


def _router_path() -> Path:
	return (
		Path(__file__).resolve().parents[2]
		/ "public"
		/ "js"
		/ "pp2_planning_router.js"
	)


def _design_source_path() -> Path:
	return (
		Path(__file__).resolve().parents[4]
		/ "docs"
		/ "prompts"
		/ "procurement planning v4"
		/ "workbench"
		/ "1. Needs planning - default"
		/ "code.html"
	)


def _deployed_design_path() -> Path:
	return (
		Path(__file__).resolve().parents[2]
		/ "public"
		/ "workbench_design"
		/ "needs_planning_default.html"
	)


class TestPP4WorkbenchStaticLayoutGuard(UnitTestCase):
	def test_render_function_only_contains_the_design_iframe(self) -> None:
		source = _router_path().read_text(encoding="utf-8", errors="replace")
		fn_block = source.split("function renderPlanningWorkbenchV4(root) {", 1)[1].split(
			"\n\t}\n", 1
		)[0]
		self.assertIn('data-testid="pp4-workbench-design-iframe"', fn_block)
		self.assertNotIn("pp3-active-plan-host", fn_block)
		self.assertNotIn("pp3-planning-work-unavailable", fn_block)
		self.assertNotIn("pp4-active-plan-context", fn_block)

	def test_mount_does_not_fetch_active_plan_for_static_workbench_root(self) -> None:
		source = _router_path().read_text(encoding="utf-8", errors="replace")
		mount_block = source.split("function mount() {", 1)[1].split("\n\tfunction scheduleBoot", 1)[0]
		self.assertNotIn("fetchActivePlanPayload()", mount_block)
		self.assertNotIn("applyPP4ActivePlanGate", mount_block)
		self.assertNotIn("pp4RouteToPlanningHub", mount_block)

	def test_deployed_design_asset_only_suppresses_duplicate_desk_sidebar(self) -> None:
		"""Deployed copy must match the design pixel-for-pixel except for the
		design's own left nav `<aside>`, which duplicates Frappe Desk's native
		module sidebar and is intentionally suppressed for the embedded/iframe
		copy only. The pristine design source is left untouched."""
		design_source = _design_source_path()
		deployed = _deployed_design_path()
		self.assertTrue(design_source.exists(), msg=f"missing {design_source}")
		self.assertTrue(deployed.exists(), msg=f"missing {deployed}")

		source_html = design_source.read_text(encoding="utf-8")
		deployed_html = deployed.read_text(encoding="utf-8")

		self.assertIn("Global Procurement", source_html)
		self.assertNotIn(
			"Global Procurement",
			deployed_html,
			"Deployed workbench design must not duplicate Desk's own left-hand navigation.",
		)
		self.assertNotIn('<aside class="h-screen w-64 fixed left-0 top-0', deployed_html)
		self.assertNotIn("ml-64", deployed_html)

		# Everything else (header, KPI cards, tabs, table) must remain byte-identical.
		main_marker = '<main class="'
		source_main = source_html.split(main_marker, 1)[1]
		deployed_main = deployed_html.split(main_marker, 1)[1]
		# Strip only the leading class attribute value (ml-64 vs not) before comparing.
		source_main_body = source_main.split(">", 1)[1]
		deployed_main_body = deployed_main.split(">", 1)[1]
		self.assertEqual(
			source_main_body,
			deployed_main_body,
			"Main content must stay pixel-identical to the design once past the <main> tag.",
		)
