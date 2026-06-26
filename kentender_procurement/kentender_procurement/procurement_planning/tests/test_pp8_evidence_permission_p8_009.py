# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P8-009 — Evidence technical details permission-aware."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PKG_CODE,
)
from kentender_procurement.procurement_planning.services.evidence_view_model import (
	get_evidence_view_model,
)


class TestPP8EvidencePermissionP8009(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self._cleanup: list[tuple[str, str]] = []
		if not frappe.db.exists("DocType", "Procurement Package"):
			self._skip = True
			return
		self._skip = False
		seed = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER", force_reset=True)
		if not seed.get("ok"):
			self.skipTest(f"WORKS master seed unavailable: {seed}")

	def tearDown(self):
		if getattr(self, "_skip", True):
			return
		frappe.set_user("Administrator")
		for doctype, name in reversed(self._cleanup):
			if frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _ensure_planner(self) -> str:
		email = f"p8009.planner.{frappe.generate_hash(length=6)}@moh.test"
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "P8009",
				"last_name": "Planner",
				"send_welcome_email": 0,
			}
		)
		user.insert(ignore_permissions=True)
		user.add_roles("Procurement Planner")
		self._cleanup.append(("User", email))
		return email

	def test_pp8_009_technical_panel_collapsed_and_permission_gated(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		out = get_evidence_view_model(package_code=PKG_CODE, actor="Administrator")
		self.assertTrue(out.get("ok"), out)
		technical = out.get("technical_details") or {}
		self.assertFalse(technical.get("visible_by_default"))
		self.assertTrue(technical.get("requires_permission"))

	def test_pp8_009_planner_cannot_view_technical_payload(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		planner = self._ensure_planner()
		out = get_evidence_view_model(package_code=PKG_CODE, actor=planner)
		self.assertTrue(out.get("ok"), out)
		technical = out.get("technical_details") or {}
		self.assertFalse(technical.get("may_view_technical"))

	def test_pp8_009_administrator_can_view_technical_codes(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		out = get_evidence_view_model(package_code=PKG_CODE, actor="Administrator")
		self.assertTrue(out.get("ok"), out)
		technical = out.get("technical_details") or {}
		self.assertTrue(technical.get("may_view_technical"))
		self.assertTrue(technical.get("codes"))
