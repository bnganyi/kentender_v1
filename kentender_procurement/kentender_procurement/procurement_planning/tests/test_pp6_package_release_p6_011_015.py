# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P6-011 / P6-012 / P6-013 / P6-015 — Package Detail Release tab."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PKGREL_CODE,
	PKG_CODE,
)
from kentender_procurement.procurement_planning.services.package_detail_view_model import (
	get_pp3_package_detail_view_model,
)

_FORBIDDEN_RELEASE_UI = (
	PKGREL_CODE,
	"source_object_code",
	"target_object_code",
	"locked_summary_json",
	"passed_forward_summary_json",
	"technical_refs_json",
	"Planning Release Package",
	"pp2-planning-handoff",
)


class TestPP6PackageReleaseP6011Source(UnitTestCase):
	def test_release_panel_testids(self) -> None:
		path = (
			Path(__file__).resolve().parents[2]
			/ "public"
			/ "js"
			/ "package_detail_page.js"
		)
		source = path.read_text(encoding="utf-8", errors="replace")
		for tid in (
			"kt-pd-panel-release",
			"kt-pd-release-action",
			"kt-pd-open-tender",
		):
			self.assertIn(tid, source, msg=f"missing {tid} (P6-011+)")
		self.assertNotIn("pp2-planning-handoff-stack", source)
		self.assertNotIn("Planning Release Package", source)


class TestPP6PackageReleaseP6011API(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Package"):
			self._skip = True
			return
		self._skip = False

	def _seed(self, checkpoint: str) -> None:
		seed_procurement_planning_works_master(checkpoint=checkpoint, force_reset=True)
		frappe.db.commit()

	def test_draft_release_blocked_with_navigation_hints(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning not installed")
		self._seed("PACKAGE_DRAFT")
		out = get_pp3_package_detail_view_model(PKG_CODE, "Administrator")
		tab = (out.get("tabs") or {}).get("release") or {}
		self.assertFalse(tab.get("released"))
		self.assertEqual(tab.get("ready_label"), "No")
		self.assertTrue(tab.get("blockers"), tab)
		self.assertTrue(tab.get("protected_values"))
		self.assertTrue(tab.get("sent_values"))
		self.assertTrue(tab.get("warning"))
		serialized = frappe.as_json(tab)
		for token in _FORBIDDEN_RELEASE_UI:
			self.assertNotIn(token, serialized, msg=f"release tab leaked {token}")

	def test_released_package_shows_tender_created_summary(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning not installed")
		self._seed("RELEASED_TO_TENDER")
		out = get_pp3_package_detail_view_model(PKG_CODE, "Administrator")
		tab = (out.get("tabs") or {}).get("release") or {}
		self.assertTrue(tab.get("released"), tab)
		self.assertIn("Tender created", tab.get("subheadline") or "")
		serialized = frappe.as_json(tab)
		for token in _FORBIDDEN_RELEASE_UI:
			self.assertNotIn(token, serialized, msg=f"released view leaked {token}")
