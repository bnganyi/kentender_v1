# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-003 — PP3 Evidence view-model service/API contract."""

from __future__ import annotations

import re

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.evidence_view_model import (
	get_pp_evidence_view_model,
)
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PKG_CODE,
)
from kentender_procurement.procurement_planning.services.evidence_view_model import (
	get_evidence_view_model,
)

_PROHIBITED_TEXT_RE = re.compile(
	r"(source_object_code|target_object_code|technical_refs_json|audit_event_ref|PLANINCL-|PKGREL-|PKGCONSUME-)",
	re.IGNORECASE,
)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Package"))


class TestPP3EvidenceViewModelP2003(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self._cleanup: list[tuple[str, str]] = []
		if not _pp_ok():
			self._skip = True
			return
		self._skip = False
		seed = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		if not seed.get("ok"):
			self.skipTest(f"WORKS master seed unavailable: {seed}")
		if not frappe.db.exists("Procurement Package", {"package_code": PKG_CODE}):
			self.skipTest("WORKS master package missing for evidence tests")

	def tearDown(self):
		if getattr(self, "_skip", True):
			return
		frappe.set_user("Administrator")
		for doctype, name in reversed(self._cleanup):
			if frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _ensure_supplier(self) -> str:
		email = f"p2003.supplier.{frappe.generate_hash(length=6)}@moh.test"
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "P2003",
				"last_name": "Supplier",
				"send_welcome_email": 0,
			}
		)
		user.insert(ignore_permissions=True)
		user.add_roles("Supplier")
		self._cleanup.append(("User", email))
		return email

	def test_guest_denied_api(self) -> None:
		frappe.set_user("Guest")
		out = get_pp_evidence_view_model(package_code=PKG_CODE)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")

	def test_supplier_denied_api(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		supplier = self._ensure_supplier()
		frappe.set_user(supplier)
		out = get_pp_evidence_view_model(package_code=PKG_CODE)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")

	def test_required_envelope_and_contract(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		out = get_evidence_view_model(package_code=PKG_CODE, actor="Administrator")
		self.assertTrue(out.get("ok"), msg=out)
		self.assertIsInstance(out.get("title"), str)
		self.assertTrue(str(out.get("title") or "").strip())
		self.assertIn("timeline", out)
		self.assertIn("records", out)
		self.assertIn("technical_details", out)
		self.assertIsInstance(out.get("timeline"), list)
		self.assertIsInstance(out.get("records"), list)
		technical = out.get("technical_details") or {}
		self.assertFalse(technical.get("visible_by_default"))
		self.assertTrue(technical.get("requires_permission"))

	def test_business_labels_and_records_contract(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		out = get_evidence_view_model(package_code=PKG_CODE, actor="Administrator")
		self.assertTrue(out.get("ok"), msg=out)

		for row in out.get("timeline") or []:
			label = str(row.get("label") or "").strip()
			self.assertTrue(label)
			self.assertNotRegex(label, _PROHIBITED_TEXT_RE.pattern)
			self.assertIn(str(row.get("status") or ""), ("complete", "in_progress", "blocked"))

		for rec in out.get("records") or []:
			label = str(rec.get("label") or "").strip()
			self.assertTrue(label)
			self.assertNotRegex(label, _PROHIBITED_TEXT_RE.pattern)
			self.assertTrue(str(rec.get("type") or "").strip())

	def test_api_matches_service_output(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		service_out = get_evidence_view_model(package_code=PKG_CODE, actor="Administrator")
		api_out = get_pp_evidence_view_model(package_code=PKG_CODE)
		self.assertEqual(service_out, api_out)
