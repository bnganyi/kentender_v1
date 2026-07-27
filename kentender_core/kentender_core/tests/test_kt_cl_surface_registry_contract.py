# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Contract: kt_cl_surface_registry.js covers every A2 screen ID with chrome metadata."""

from __future__ import annotations

import re
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

_A2_SCREEN_IDS: tuple[str, ...] = (
	"UI-00",
	"UI-M01",
	"UI-01",
	"CFG-01",
	"CFG-02",
	"CFG-03",
	"CFG-04",
	"CFG-05",
	"CFG-06",
	"CFG-07",
	"CFG-08",
	"CFG-09",
	"WF-01",
	"WF-02",
	"WF-03",
	"WF-04",
	"PUB-A1",
	"PUB-A2",
	"PUB-A3",
	"BW-A1",
)


def _registry_source() -> str:
	return (
		Path(frappe.get_app_path("kentender_core"))
		/ "public"
		/ "js"
		/ "kt_cl_surface_registry.js"
	).read_text(encoding="utf-8")


class TestKtClSurfaceRegistryContract(IntegrationTestCase):
	def test_every_a2_screen_id_has_registry_entry(self) -> None:
		source = _registry_source()
		for screen_id in _A2_SCREEN_IDS:
			self.assertIn(
				f'"{screen_id}"',
				source,
				msg=f"A2 screen {screen_id} missing from kt_cl_surface_registry.js",
			)

	def test_each_surface_has_required_chrome_fields(self) -> None:
		source = _registry_source()
		# Structural markers present for the resolver and chrome contract.
		self.assertIn("routePrefixes", source)
		self.assertIn("sidebarWorkspaceKey", source)
		self.assertIn("pageHeader", source)
		self.assertIn("toolbar", source)
		self.assertIn("resolveFromRoute", source)
		self.assertIn("allIds", source)

	def test_ui00_targets_dashboard_page(self) -> None:
		source = _registry_source()
		# UI-00 block must include the live Desk page slug.
		ui00_match = re.search(
			r'"UI-00"\s*:\s*\{(?P<body>.*?)(?=\n\t\t"[A-Z]|\n\t\};)',
			source,
			re.DOTALL,
		)
		self.assertIsNotNone(ui00_match, msg="UI-00 surface block not found")
		body = ui00_match.group("body")
		self.assertIn("it-tender-configuration-dashboard", body)
		self.assertIn("Tender Configurations", body)
		self.assertIn("sidebarWorkspaceKey", body)

	def test_chrome_helper_uses_toolbar_trail_not_composite_title(self) -> None:
		source = _registry_source()
		self.assertIn("breadcrumbs: toolbarTrail", source)
		self.assertIn("hideBreadcrumbs: true", source)
		self.assertIn("showUserMeta: true", source)
		self.assertIn("showSearch: false", source)
		self.assertIn("crumbDashboard", source)
		self.assertIn('["Workspaces", "Procurement Home"]', source)
		self.assertIn('["tender-management-v2"]', source)
		self.assertNotIn("pageTitle: pageTitle", source)

	def test_cfg05_cfg06_trails_include_step_leaf(self) -> None:
		"""CFG-05/06 must not reuse trailConfigHome (stale “Configuration Home” current)."""
		source = _registry_source()
		self.assertIn("trailCfg05SystemInventory", source)
		self.assertIn("trailCfg06PriceSchedule", source)
		self.assertIn('crumb(__("System Inventory & Bidder Background"))', source)
		self.assertIn('crumb(__("Price Schedule"))', source)
		cfg05 = re.search(
			r'"CFG-05"\s*:\s*\{(?P<body>.*?)(?=\n\t\t"[A-Z]|\n\t\};)',
			source,
			re.DOTALL,
		)
		self.assertIsNotNone(cfg05, msg="CFG-05 surface block not found")
		self.assertIn("trailCfg05SystemInventory()", cfg05.group("body"))
		self.assertNotIn("trailConfigHome", cfg05.group("body"))
		cfg06 = re.search(
			r'"CFG-06"\s*:\s*\{(?P<body>.*?)(?=\n\t\t"[A-Z]|\n\t\};)',
			source,
			re.DOTALL,
		)
		self.assertIsNotNone(cfg06, msg="CFG-06 surface block not found")
		self.assertIn("trailCfg06PriceSchedule()", cfg06.group("body"))
		self.assertNotIn("trailConfigHome", cfg06.group("body"))

	def test_ui00_dashboard_page_js_wired(self) -> None:
		page_js = frappe.get_hooks("page_js", app_name="kentender_procurement", default={})
		self.assertIn("it-tender-configuration-dashboard", page_js)
		wired = page_js["it-tender-configuration-dashboard"]
		flat = wired if isinstance(wired, str) else (wired[0] if wired else "")
		self.assertIn(
			"it_tender_configurations_dashboard_page.js",
			str(flat),
			msg="UI-00 must use the Civic Ledger dashboard page script, not the retired stub",
		)
		path = (
			Path(frappe.get_app_path("kentender_procurement"))
			/ "public"
			/ "js"
			/ "it_tender_configurations_dashboard_page.js"
		)
		self.assertTrue(path.is_file(), msg=f"Missing UI-00 page script: {path}")
		text = path.read_text(encoding="utf-8")
		self.assertIn("mountContent", text)
		self.assertIn("UI-00", text)
		self.assertIn("kt-cl-ui00-root", text)

	def test_ui01_overview_page_js_wired(self) -> None:
		page_js = frappe.get_hooks("page_js", app_name="kentender_procurement", default={})
		self.assertIn("it-tender-configuration-overview", page_js)
		wired = page_js["it-tender-configuration-overview"]
		flat = wired if isinstance(wired, str) else (wired[0] if wired else "")
		self.assertIn(
			"it_tender_configuration_overview_page.js",
			str(flat),
			msg="UI-01 must use the overview stub page script, not the retired stub",
		)
