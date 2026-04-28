# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from kentender_suppliers.api import ktsm_landing


def _supplier_group():
	sg = frappe.db.get_value("Supplier Group", {"is_group": 0}, "name")
	if not sg:
		sg = frappe.db.get_value("Supplier Group", {}, "name")
	return sg


def _ensure_profile(code: str, approval: str, operational: str, compliance: str) -> str:
	existing = frappe.db.get_value("Supplier", {"kentender_supplier_code": code}, "name")
	if existing:
		prof = frappe.db.get_value(
			"KTSM Supplier Profile", {"erpnext_supplier": existing}, "name"
		)
		if prof:
			frappe.db.set_value("KTSM Supplier Profile", prof, "approval_status", approval)
			frappe.db.set_value("KTSM Supplier Profile", prof, "operational_status", operational)
			frappe.db.set_value("KTSM Supplier Profile", prof, "compliance_status", compliance)
			return prof

	erp = frappe.get_doc(
		{
			"doctype": "Supplier",
			"supplier_name": f"Workbench {code}",
			"supplier_type": "Company",
			"supplier_group": _supplier_group(),
			"kentender_supplier_code": code,
		}
	)
	erp.insert(ignore_permissions=True)
	prof = frappe.get_doc(
		{
			"doctype": "KTSM Supplier Profile",
			"erpnext_supplier": erp.name,
			"approval_status": approval,
			"operational_status": operational,
			"compliance_status": compliance,
		}
	)
	prof.insert(ignore_permissions=True)
	return prof.name


class TestKTSMWorkbenchApi(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.submitted_profile = _ensure_profile(
			"SUP-KE-2099-1001", "Submitted", "Pending", "Incomplete"
		)
		cls.approved_profile = _ensure_profile(
			"SUP-KE-2099-1002", "Approved", "Active", "Complete"
		)
		cls.blocked_profile = _ensure_profile(
			"SUP-KE-2099-1003", "Approved", "Suspended", "Incomplete"
		)

	def test_get_suppliers_contract(self):
		payload = ktsm_landing.get_suppliers({"q": "SUP-KE-2099"})
		self.assertTrue(payload.get("ok"), payload)
		self.assertIsInstance(payload.get("rows"), list)
		self.assertGreaterEqual(len(payload.get("rows") or []), 3)
		first = (payload.get("rows") or [{}])[0]
		self.assertIn("supplier_code", first)
		self.assertIn("supplier_name", first)
		self.assertIn("approval_status", first)
		self.assertIn("compliance_status", first)
		self.assertNotIn("supplier_profile", first)

	def test_get_supplier_detail_contract(self):
		payload = ktsm_landing.get_supplier_detail("SUP-KE-2099-1001")
		self.assertTrue(payload.get("ok"), payload)
		detail = payload.get("detail") or {}
		self.assertEqual(detail.get("supplier_code"), "SUP-KE-2099-1001")
		self.assertIn("sections", detail)
		self.assertIn("actions", detail)
		self.assertNotIn("supplier_profile", detail)

	def test_get_suppliers_pending_review_kpi_filter(self):
		payload = ktsm_landing.get_suppliers({"kpi": "pending_review"})
		self.assertTrue(payload.get("ok"), payload)
		for row in payload.get("rows") or []:
			self.assertIn(
				row.get("approval_status"), {"Submitted", "Under Review"}, row
			)

	def test_kentender_supplier_code_pattern_allows_sequence_beyond_9999(self):
		from kentender_suppliers.validators.supplier_hooks import KENTENDER_SUPPLIER_CODE_PATTERN

		self.assertTrue(KENTENDER_SUPPLIER_CODE_PATTERN.match("SUP-KE-2026-0001"))
		self.assertTrue(KENTENDER_SUPPLIER_CODE_PATTERN.match("SUP-KE-2026-10000"))

	def test_create_supplier_builder_profile_contract(self):
		payload = ktsm_landing.create_supplier_builder_profile(
			supplier_name="Builder Flow Co", supplier_type="Company"
		)
		self.assertTrue(payload.get("ok"), payload)
		self.assertTrue(payload.get("profile_name"))
		self.assertTrue(payload.get("supplier_code"))
		pname = payload.get("profile_name")
		self.assertTrue(frappe.db.exists("KTSM Supplier Profile", pname))

	def test_get_builder_payload_contract(self):
		payload = ktsm_landing.get_builder_payload(self.submitted_profile)
		self.assertTrue(payload.get("ok"), payload)
		self.assertIn("identity", payload)
		self.assertIn("profile", payload)
		self.assertIn("documents", payload)
		self.assertIn("categories", payload)
		self.assertIn("readiness", payload)

	def test_update_builder_identity_contract(self):
		before = ktsm_landing.get_builder_payload(self.submitted_profile)
		new_name = (before.get("identity") or {}).get("supplier_name", "") + " Updated"
		resp = ktsm_landing.update_builder_identity(
			self.submitted_profile, new_name, "Company"
		)
		self.assertTrue(resp.get("ok"), resp)
		after = ktsm_landing.get_builder_payload(self.submitted_profile)
		self.assertEqual((after.get("identity") or {}).get("supplier_name"), new_name)

	def test_builder_api_requires_internal_role(self):
		orig_user = frappe.session.user
		try:
			frappe.set_user("Guest")
			with self.assertRaises(Exception):
				ktsm_landing.create_supplier_builder_profile("Denied Co", "Company")
		finally:
			frappe.set_user(orig_user)
