# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services.command_write_guard import fixture_insert, purge_doc
from kentender_suppliers.api import ktsm_landing
from kentender_suppliers.services import registry_access

OFFICER = "ktsm.workbench.officer@kentender.test"


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
	fixture_insert(prof, reason="workbench fixture: a profile born in a given governance state")
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
		cls.draft_profile = _ensure_profile("SUP-KE-2099-1004", "Draft", "Pending", "Incomplete")
		if frappe.db.exists("User", OFFICER):
			frappe.delete_doc("User", OFFICER, force=True, ignore_permissions=True)
		officer = frappe.get_doc(
			{"doctype": "User", "email": OFFICER, "first_name": "Officer", "send_welcome_email": 0, "user_type": "System User"}
		)
		officer.append("roles", {"role": registry_access.REGISTRY_OFFICER})
		officer.insert(ignore_permissions=True, ignore_links=True)
		cls.addClassCleanup(cls._remove_officer)

	@classmethod
	def _remove_officer(cls):
		frappe.set_user("Administrator")
		if frappe.db.exists("User", OFFICER):
			frappe.delete_doc("User", OFFICER, force=True, ignore_permissions=True)
		frappe.db.commit()

	def tearDown(self):
		frappe.set_user("Administrator")

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
		frappe.set_user(OFFICER)
		payload = ktsm_landing.create_supplier_builder_profile(
			supplier_name="Builder Flow Co", supplier_type="Company"
		)
		frappe.set_user("Administrator")
		self.assertTrue(payload.get("ok"), payload)
		self.assertTrue(payload.get("profile_name"))
		self.assertTrue(payload.get("supplier_code"))
		pname = payload.get("profile_name")
		self.addCleanup(self._remove_builder_profile, pname)
		self.assertTrue(frappe.db.exists("KTSM Supplier Profile", pname))

	@staticmethod
	def _remove_builder_profile(pname: str) -> None:
		frappe.set_user("Administrator")
		erp = frappe.db.get_value("KTSM Supplier Profile", pname, "erpnext_supplier")
		purge_doc("KTSM Supplier Profile", pname)
		if erp:
			frappe.delete_doc("Supplier", erp, force=True, ignore_permissions=True)

	def test_get_builder_payload_contract(self):
		payload = ktsm_landing.get_builder_payload(self.submitted_profile)
		self.assertTrue(payload.get("ok"), payload)
		self.assertIn("identity", payload)
		self.assertIn("profile", payload)
		self.assertIn("documents", payload)
		self.assertIn("categories", payload)
		self.assertIn("readiness", payload)

	def test_update_builder_identity_contract(self):
		frappe.set_user(OFFICER)
		before = ktsm_landing.get_builder_payload(self.draft_profile)
		new_name = (before.get("identity") or {}).get("supplier_name", "").removesuffix(" Updated") + " Updated"
		resp = ktsm_landing.update_builder_identity(
			self.draft_profile, new_name, "Company"
		)
		self.assertTrue(resp.get("ok"), resp)
		after = ktsm_landing.get_builder_payload(self.draft_profile)
		self.assertEqual((after.get("identity") or {}).get("supplier_name"), new_name)
		# Once submitted the identity is no longer a builder edit (RG-11).
		with self.assertRaises(frappe.PermissionError):
			ktsm_landing.update_builder_identity(self.submitted_profile, "Changed After Submit", "Company")

	def test_builder_api_requires_internal_role(self):
		orig_user = frappe.session.user
		try:
			frappe.set_user("Guest")
			with self.assertRaises(Exception):
				ktsm_landing.create_supplier_builder_profile("Denied Co", "Company")
		finally:
			frappe.set_user(orig_user)
