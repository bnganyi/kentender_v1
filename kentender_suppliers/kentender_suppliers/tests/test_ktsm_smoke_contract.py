# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

"""
Automate [10. Smoke Test Contract.md] PART 1 (server-side).
Playwright: tests/ui/smoke/supplier/
"""

import random

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, getdate, today
from frappe.utils.file_manager import save_file

from kentender_suppliers.api import smw_public, smw_workflow
from kentender_suppliers.services import constants, eligibility, governance
from kentender_suppliers.services.compliance import recompute_and_save_profile, recompute_compliance


def _sg():
	sg = frappe.db.get_value("Supplier Group", {"is_group": 0}, "name")
	if not sg:
		sg = frappe.db.get_value("Supplier Group", {}, "name")
	return sg


def _ensure_doc_type(code: str, name: str, required: int, expires: int = 0):
	if frappe.db.exists("KTSM Document Type", {"document_type_code": code}):
		return frappe.db.get_value("KTSM Document Type", {"document_type_code": code}, "name")
	d = frappe.get_doc(
		{
			"doctype": "KTSM Document Type",
			"document_type_code": code,
			"document_type_name": name,
			"required_for_registration": required,
			"expires": expires,
			"is_active": 1,
		}
	)
	d.insert(ignore_permissions=True)
	return d.name


def _ensure_category(code: str, lname: str) -> str:
	if frappe.db.exists("KTSM Supplier Category", {"category_code": code}):
		return frappe.db.get_value("KTSM Supplier Category", {"category_code": code}, "name")
	cat = frappe.get_doc(
		{
			"doctype": "KTSM Supplier Category",
			"category_name": lname,
			"category_code": code,
			"is_active": 1,
		}
	)
	cat.insert(ignore_permissions=True)
	return cat.name


def _make_supplier_and_profile(code: str) -> tuple[str, str]:
	erp = frappe.get_doc(
		{
			"doctype": "Supplier",
			"supplier_name": f"Smoke {code}",
			"supplier_type": "Company",
			"supplier_group": _sg(),
			"kentender_supplier_code": code,
		}
	)
	erp.insert(ignore_permissions=True)
	p = frappe.get_doc(
		{
			"doctype": "KTSM Supplier Profile",
			"erpnext_supplier": erp.name,
		}
	)
	p.insert(ignore_permissions=True)
	return erp.name, p.name


def _create_user(email: str, first: str) -> str:
	if not frappe.db.exists("User", email):
		u = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": first,
				"send_welcome_email": 0,
				"user_type": "Website User",
			}
		)
		if frappe.db.exists("Role", "KenTender External Supplier"):
			u.append("roles", {"role": "KenTender External Supplier"})
		u.insert(ignore_permissions=True, ignore_links=True)
	return email


def _add_doc(
	profile: str, dt: str, docname: str, uploader: str, external: int = 0
) -> str:
	o = frappe.session.user
	try:
		frappe.set_user(uploader)
		dspec = {
			"doctype": "KTSM Supplier Document",
			"supplier_profile": profile,
			"document_type": dt,
			"document_name": docname,
			"verification_status": "Pending",
			"is_current": 1,
			"external_uploaded": external,
		}
		if frappe.db.get_value("KTSM Document Type", dt, "expires"):
			dspec["expiry_date"] = add_days(today(), 400)
		d = frappe.get_doc(dspec)
		d.insert(ignore_permissions=True)
		b = b"x"
		s = save_file("smoke.txt", b, "KTSM Supplier Document", d.name, is_private=0, decode=False)
		d.db_set("file", s.file_url, update_modified=False)
		return d.name
	finally:
		frappe.set_user(o)


def _unique_ktsm_code() -> str:
	"""Format SUP-KE-YYYY-#### (validator regex)."""
	yr = str(getdate(today()).year)
	for _ in range(200):
		c = f"SUP-KE-{yr}-{random.randint(0, 9999):04d}"
		if not frappe.db.exists("Supplier", {"kentender_supplier_code": c}):
			return c
	raise RuntimeError("Could not allocate a unique kentender_supplier_code for smoke test")


def _reason_codes(r: dict) -> set:
	return {x.get("code") for x in (r.get("reasons") or []) if x.get("code")}


class TestKTSMFullSmoke(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		frappe.set_user("Administrator")
		cls._dt_reg = _ensure_doc_type("SMOKE-DOC-REG", "SMOKE Registration", 1, 0)
		cls._dt_tax = _ensure_doc_type("SMOKE-DOC-TAX", "SMOKE Tax", 1, 1)
		cls._cat = _ensure_category("CAT-MED-EQUIP", "SMOKE Med Equip")
		cls._comp_user = _create_user("smoke.compliance@kentender.test", "Compliance")
		cls._ext_a = _create_user("smoke.a@kentender.test", "A")
		cls._ext_b = _create_user("smoke.b@kentender.test", "B")

	# -- SCENARIO 1 --

	def test_01_register_guest_and_incomplete(self):
		frappe.set_user("Guest")
		em = f"smoke.guest.{frappe.generate_hash(6)}@kentender.test"
		# "Contact" as contact name can break Frappe's linked Contact (reserved name)
		r = smw_public.ktsm_register("Smoke Reg LLC", em, "Registrant", "Company")
		self.assertTrue(r.get("ok"), r)
		self.assertEqual(r.get("approval_status"), "Draft")
		self.assertEqual(r.get("operational_status"), "Pending")
		self.assertEqual(r.get("compliance_status"), "Incomplete")
		code = r.get("supplier_code")
		prof = eligibility.get_profile_name_for_supplier_code(code)
		self.assertTrue(prof)
		acc = frappe.get_all("KTSM Supplier API Access", {"supplier_profile": prof}, pluck="name", limit=1)
		self.assertTrue(acc, "API access grant (Pending) expected by smoke contract")
		self.assertEqual(
			frappe.db.get_value("KTSM Supplier API Access", acc[0], "access_status"),
			"Pending",
		)
		frappe.set_user("Administrator")

	# 2-6: lifecycle (upload → submit as external → start review → approve as admin → category → eligible)

	def test_02_through_06_lifecycle_approve_and_eligible(self):
		c0 = _unique_ktsm_code()
		_erp, prof = _make_supplier_and_profile(c0)
		frappe.db.set_value("KTSM Supplier Profile", prof, "external_user", self._ext_a)
		self.assertEqual(recompute_compliance(prof), "Incomplete")
		d1 = _add_doc(prof, self._dt_reg, "REG doc", self._ext_a, 1)
		_add_doc(prof, self._dt_tax, "TAX doc", self._ext_a, 1)
		dtax = frappe.get_all(
			"KTSM Supplier Document",
			filters={"supplier_profile": prof, "document_type": self._dt_tax},
			pluck="name",
			order_by="modified desc",
			limit=1,
		)[0]
		frappe.db.set_value("KTSM Supplier Document", dtax, "expiry_date", add_days(today(), 365))
		frappe.set_user(self._comp_user)
		governance.verify_document(d1)
		governance.verify_document(dtax)
		frappe.set_user("Administrator")
		self.assertEqual(recompute_compliance(prof), "Complete")
		frappe.set_user(self._ext_a)
		governance.submit_for_review(prof)
		frappe.set_user("Administrator")
		governance.start_review(prof)
		governance.approve_supplier(prof)
		# category for scenario 6
		ca = frappe.get_doc(
			{
				"doctype": "KTSM Category Assignment",
				"supplier_profile": prof,
				"category": self._cat,
				"qualification_status": "Requested",
			}
		)
		ca.insert(ignore_permissions=True)
		governance.start_category_review(ca.name)
		governance.qualify_supplier_category(
			ca.name, qualified_until=getdate(add_days(today(), 365))
		)
		out = eligibility.check_supplier_eligibility(c0, "CAT-MED-EQUIP")
		self.assertTrue(out.get("eligible"), out)
		self.assertEqual(_reason_codes(out), set())

	# 7, 8, 9, 10, 11, 12, 14

	def test_07_suspended_ineligible(self):
		c0 = _unique_ktsm_code()
		_, prof = _make_supplier_and_profile(c0)
		governance.suspend_supplier(prof, "sc7")
		r = eligibility.check_supplier_eligibility(c0, None)
		self.assertFalse(r.get("eligible"))
		self.assertIn(constants.SUSPENDED, _reason_codes(r))

	def test_08_expired_compliance_ineligible(self):
		c0 = _unique_ktsm_code()
		_, prof = _make_supplier_and_profile(c0)
		fk = _add_doc(prof, self._dt_reg, "E", "Administrator", 0)
		frappe.db.set_value("KTSM Document Type", self._dt_reg, "expires", 1)
		frappe.db.set_value("KTSM Supplier Document", fk, "verification_status", "Verified")
		frappe.db.set_value("KTSM Supplier Document", fk, "expiry_date", add_days(today(), -1))
		try:
			r = eligibility.check_supplier_eligibility(c0, None)
			self.assertFalse(r.get("eligible"))
			self.assertIn(constants.COMPLIANCE_EXPIRED, _reason_codes(r))
		finally:
			frappe.db.set_value("KTSM Document Type", self._dt_reg, "expires", 0)

	def test_09_category_not_assigned(self):
		c0 = _unique_ktsm_code()
		_, prof = _make_supplier_and_profile(c0)
		frappe.db.set_value("KTSM Supplier Profile", prof, "approval_status", "Approved")
		frappe.db.set_value("KTSM Supplier Profile", prof, "operational_status", "Active")
		# verified current docs for every required reg type
		for dt in (self._dt_reg, self._dt_tax):
			nm = _add_doc(prof, dt, f"V-{random.randint(100, 999)}", "Administrator", 0)
			if frappe.db.get_value("KTSM Document Type", dt, "expires"):
				frappe.db.set_value(
					"KTSM Supplier Document", nm, "expiry_date", add_days(today(), 200)
				)
			frappe.db.set_value("KTSM Supplier Document", nm, "verification_status", "Verified")
		recompute_and_save_profile(prof)
		self.assertEqual(
			recompute_compliance(prof), "Complete", "Setup for category-only ineligibility"
		)
		r = eligibility.check_supplier_eligibility(c0, "CAT-MED-EQUIP")
		self.assertFalse(r.get("eligible"), r)
		self.assertIn(constants.CATEGORY_NOT_ASSIGNED, _reason_codes(r))

	def test_10_multiblocker(self):
		c0 = _unique_ktsm_code()
		_, prof = _make_supplier_and_profile(c0)
		governance.suspend_supplier(prof, "sc10s")
		fk = _add_doc(prof, self._dt_reg, "E2", "Administrator", 0)
		frappe.db.set_value("KTSM Document Type", self._dt_reg, "expires", 1)
		frappe.db.set_value("KTSM Supplier Document", fk, "verification_status", "Verified")
		frappe.db.set_value("KTSM Supplier Document", fk, "expiry_date", add_days(today(), -1))
		try:
			r = eligibility.check_supplier_eligibility(c0, None)
			codes = _reason_codes(r)
			self.assertIn(constants.SUSPENDED, codes)
			self.assertIn(constants.COMPLIANCE_EXPIRED, codes)
		finally:
			frappe.db.set_value("KTSM Document Type", self._dt_reg, "expires", 0)

	def test_11_external_get_me_isolation(self):
		c0 = _unique_ktsm_code()
		_erp, prof = _make_supplier_and_profile(c0)
		frappe.db.set_value("KTSM Supplier Profile", prof, "external_user", self._ext_a)
		frappe.set_user(self._ext_a)
		me = smw_public.ktsm_get_me()
		self.assertEqual(me.get("supplier_code"), c0)
		_erp2, _p2 = _make_supplier_and_profile(_unique_ktsm_code())
		oc = frappe.db.get_value("Supplier", _erp2, "kentender_supplier_code")
		self.assertNotEqual(c0, oc)
		from frappe.exceptions import PermissionError, ValidationError

		with self.assertRaises((PermissionError, ValidationError)):
			smw_public.ktsm_get_status(oc)
		frappe.set_user("Administrator")

	def test_12_external_cannot_approve(self):
		c0 = _unique_ktsm_code()
		_erp, prof = _make_supplier_and_profile(c0)
		frappe.db.set_value("KTSM Supplier Profile", prof, "external_user", self._ext_a)
		# get into under review for approve
		frappe.db.set_value("KTSM Supplier Profile", prof, "submitted_by", "Administrator")
		frappe.db.set_value("KTSM Supplier Profile", prof, "approval_status", "Under Review")
		frappe.set_user(self._ext_a)
		with self.assertRaises(Exception):
			smw_workflow.ktsm_approve_supplier(prof)
		frappe.set_user("Administrator")

	def test_14_status_history_on_submit(self):
		c0 = _unique_ktsm_code()
		_erp, prof = _make_supplier_and_profile(c0)
		frappe.db.set_value("KTSM Supplier Profile", prof, "external_user", self._ext_a)
		for dt in (self._dt_reg, self._dt_tax):
			nm = _add_doc(prof, dt, f"hist-{random.randint(100, 999)}", "Administrator", 0)
			if frappe.db.get_value("KTSM Document Type", dt, "expires"):
				frappe.db.set_value("KTSM Supplier Document", nm, "expiry_date", add_days(today(), 200))
			frappe.db.set_value("KTSM Supplier Document", nm, "verification_status", "Verified")
		self.assertEqual(recompute_compliance(prof), "Complete")
		frappe.set_user(self._ext_a)
		governance.submit_for_review(prof)
		frappe.set_user("Administrator")
		rows = frappe.get_all(
			"KTSM Status History",
			filters={"supplier_profile": prof, "new_status": "Submitted", "status_type": "Approval"},
			limit=5,
		)
		self.assertTrue(len(rows) >= 1, "Status history for submit")
