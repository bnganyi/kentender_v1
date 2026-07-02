# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Planning Hub v4 static shell — asset contract."""

from __future__ import annotations

import subprocess
from pathlib import Path

import frappe
from frappe.tests import UnitTestCase


class TestPlanningHubV4ShellContract(UnitTestCase):
	def test_planning_hub_page_assets_exist(self) -> None:
		root = Path(frappe.get_app_path("kentender_procurement")) / "public"
		js_path = root / "js" / "planning_hub_page.js"
		js = js_path.read_text(encoding="utf-8")
		css = (root / "css" / "planning_hub_page.css").read_text(encoding="utf-8")
		subprocess.check_call(["node", "--check", str(js_path)])
		self.assertIn('data-testid="kt-pph-hub"', js)
		self.assertIn('data-testid="kt-pph-toolbar"', js)
		self.assertIn('data-testid="kt-pph-header"', js)
		self.assertNotIn('data-testid="kt-pph-sidebar"', js)
		# v4 hero + KPI + ledger contract
		self.assertIn('data-testid="kt-pph-stats"', js)
		self.assertIn("blocked_items", js)
		self.assertIn("kt-pph-stat-blocked", js)
		self.assertIn("get_pp_planning_hub_shell_data", js)
		self.assertIn("Procurement Planning Hub", js)
		self.assertIn("Procurement Plans Ledger", js)
		self.assertIn("kt-pph-shell", css)
		self.assertIn("planning-hub", (Path(frappe.get_app_path("kentender_procurement")) / "hooks.py").read_text(encoding="utf-8"))

	def test_planning_workspace_redirects_to_hub(self) -> None:
		source = (Path(frappe.get_app_path("kentender_procurement")) / "public" / "js" / "planning_workspace.js").read_text(
			encoding="utf-8"
		)
		self.assertIn('frappe.set_route("planning-hub")', source)
		self.assertIn('"Procurement Planning"', source)
		self.assertIn("_hasWorkbenchDeepLink", source)
		self.assertIn("plan|queue|item|package_code", source)
