# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P6-006 — Package Detail Overview tab."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PKG_CODE,
	PKG_TITLE,
)
from kentender_procurement.procurement_planning.services.package_detail_view_model import (
	get_pp3_package_detail_view_model,
)

_FORBIDDEN = (
	"PLANINCL",
	"source_object_code",
	"target_object_code",
	"technical_refs_json",
	"audit_event_ref",
	"Planning Inclusion Record",
	"Planning Release Package",
)


class TestPP6PackageOverviewP6006Source(UnitTestCase):
	def test_overview_panel_testids(self) -> None:
		path = (
			Path(__file__).resolve().parents[2]
			/ "public"
			/ "js"
			/ "package_detail_page.js"
		)
		source = path.read_text(encoding="utf-8", errors="replace")
		for tid in (
			"kt-pd-panel-overview",
			"kt-pd-included-demand",
			"kt-pd-lines-table",
		):
			self.assertIn(tid, source, msg=f"missing {tid} (P6-006)")


class TestPP6PackageOverviewP6006API(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Package"):
			self._skip = True
			return
		self._skip = False
		seed_procurement_planning_works_master(checkpoint="PACKAGE_DRAFT", force_reset=True)
		frappe.db.commit()

	def test_overview_fields_without_technical_leakage(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning not installed")
		out = get_pp3_package_detail_view_model(PKG_CODE, "Administrator")
		self.assertTrue(out.get("ok"), out)
		tab = (out.get("tabs") or {}).get("overview") or {}
		self.assertIn(PKG_TITLE, tab.get("source_demand_label") or "")
		self.assertIn("Open Tender", tab.get("package_purpose") or "")
		self.assertEqual(tab.get("status_label"), "Draft Package")
		self.assertEqual(tab.get("funding_label"), "Budget linked")
		self.assertIn("blockers_label", tab)
		self.assertIn("next_action_label", tab)
		serialized = frappe.as_json(tab)
		for token in _FORBIDDEN:
			self.assertNotIn(token, serialized, msg=f"overview leaked {token}")
