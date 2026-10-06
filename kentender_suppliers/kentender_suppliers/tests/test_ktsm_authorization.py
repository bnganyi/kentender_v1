# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

"""AUD-XC-004/018/019/020: who may read or change the KTSM supplier registry."""

import frappe
from frappe.exceptions import PermissionError
from frappe.tests import IntegrationTestCase

from kentender_suppliers.api import ktsm_landing, smw_public, smw_workflow
from kentender_suppliers.patches.v1_0 import restore_ktsm_roles_and_supplier_code
from kentender_suppliers.services import eligibility, registry_access

PW = "Kt-Auth-Test-1!"
_USERS = {
	"plain": ("ktsm.auth.plain@kentender.test", "System User", []),
	"supplier": ("ktsm.auth.supplier@kentender.test", "Website User", ["KenTender External Supplier"]),
	"approver": ("ktsm.auth.approver@kentender.test", "System User", [registry_access.APPROVER]),
	"compliance": ("ktsm.auth.compliance@kentender.test", "System User", [registry_access.COMPLIANCE]),
	"registry": ("ktsm.auth.registry@kentender.test", "System User", [registry_access.REGISTRY_OFFICER]),
	"sysmgr": ("ktsm.auth.sysmgr@kentender.test", "System User", ["System Manager"]),
}


def _make_user(email: str, user_type: str, roles: list[str]) -> None:
	if frappe.db.exists("User", email):
		frappe.delete_doc("User", email, force=True, ignore_permissions=True)
	doc = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": email.split("@")[0],
			"send_welcome_email": 0,
			"user_type": user_type,
			"new_password": PW,
		}
	)
	for role in roles:
		if frappe.db.exists("Role", role):
			doc.append("roles", {"role": role})
	doc.insert(ignore_permissions=True, ignore_links=True)


def _as(user_key: str):
	frappe.set_user(_USERS[user_key][0])


def _profile(code: str, approval: str = "Active", operational: str = "Active") -> tuple[str, str, str]:
	sg = frappe.db.get_value("Supplier Group", {"is_group": 0}, "name") or frappe.db.get_value(
		"Supplier Group", {}, "name"
	)
	erp = frappe.get_doc(
		{
			"doctype": "Supplier",
			"supplier_name": f"Auth {code}",
			"supplier_type": "Company",
			"supplier_group": sg,
			"kentender_supplier_code": code,
		}
	)
	erp.insert(ignore_permissions=True)
	prof = frappe.get_doc({"doctype": "KTSM Supplier Profile", "erpnext_supplier": erp.name})
	prof.insert(ignore_permissions=True)
	return erp.name, prof.name, code


class TestKTSMAuthorization(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		# The roles are projected by an idempotent patch; a site can lack them.
		restore_ktsm_roles_and_supplier_code.execute()
		for email, utype, roles in _USERS.values():
			_make_user(email, utype, roles)
		cls._erp, cls.prof, cls.code = _profile("SUP-KE-2098-9001")
		cat = frappe.db.get_value("KTSM Supplier Category", {}, "name")
		if not cat:
			cat = frappe.get_doc(
				{"doctype": "KTSM Supplier Category", "category_name": "Auth Cat", "category_code": "AUTH-CAT", "is_active": 1}
			).insert(ignore_permissions=True).name
			cls._cat_created = cat
		cls.cat = cat
		cls.addClassCleanup(cls._purge)

	@classmethod
	def _purge(cls):
		frappe.set_user("Administrator")
		for name in frappe.get_all("KTSM Category Assignment", {"supplier_profile": cls.prof}, pluck="name"):
			frappe.delete_doc("KTSM Category Assignment", name, force=True, ignore_permissions=True)
		for name in frappe.get_all("KTSM Status History", {"supplier_profile": cls.prof}, pluck="name"):
			frappe.delete_doc("KTSM Status History", name, force=True, ignore_permissions=True)
		frappe.delete_doc("KTSM Supplier Profile", cls.prof, force=True, ignore_permissions=True)
		frappe.delete_doc("Supplier", cls._erp, force=True, ignore_permissions=True)
		if getattr(cls, "_cat_created", None):
			frappe.delete_doc("KTSM Supplier Category", cls._cat_created, force=True, ignore_permissions=True)
		for email, _t, _r in _USERS.values():
			if frappe.db.exists("User", email):
				frappe.delete_doc("User", email, force=True, ignore_permissions=True)
		frappe.db.commit()

	def tearDown(self):
		frappe.set_user("Administrator")
		for name in frappe.get_all("KTSM Category Assignment", {"supplier_profile": self.prof}, pluck="name"):
			frappe.delete_doc("KTSM Category Assignment", name, force=True, ignore_permissions=True)
		frappe.db.set_value("KTSM Supplier Profile", self.prof, "operational_status", "Pending")

	def _assignment(self, status: str = "Requested") -> str:
		return frappe.get_doc(
			{
				"doctype": "KTSM Category Assignment",
				"supplier_profile": self.prof,
				"category": self.cat,
				"qualification_status": status,
			}
		).insert(ignore_permissions=True).name

	def test_restore_patch_is_idempotent_and_keeps_roles(self):
		restore_ktsm_roles_and_supplier_code.execute()
		restore_ktsm_roles_and_supplier_code.execute()
		for role in (registry_access.APPROVER, registry_access.COMPLIANCE, registry_access.REGISTRY_OFFICER):
			self.assertEqual(frappe.db.count("Role", {"name": role}), 1)
		self.assertTrue(frappe.db.has_column("Supplier", "kentender_supplier_code"))

	# -- XC-004: state changes ------------------------------------------------

	def test_state_changes_refuse_plain_internal_and_supplier_accounts(self):
		a = self._assignment("Under Review")
		calls = [
			lambda: smw_workflow.ktsm_suspend(self.prof, "x"),
			lambda: smw_workflow.ktsm_reinstate(self.prof, "x"),
			lambda: smw_workflow.ktsm_set_expired(self.prof, "x"),
			lambda: smw_workflow.ktsm_qualify_category(a),
			lambda: smw_workflow.ktsm_reject_category(a, "x"),
			lambda: smw_workflow.ktsm_start_category_review(a),
			lambda: ktsm_landing.perform_action("suspend", self.code, "x"),
		]
		for who in ("plain", "supplier"):
			_as(who)
			for i, call in enumerate(calls):
				with self.assertRaises(PermissionError, msg=f"{who} call #{i}"):
					call()
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_value("KTSM Supplier Profile", self.prof, "operational_status"), "Pending")
		self.assertEqual(frappe.db.get_value("KTSM Category Assignment", a, "qualification_status"), "Under Review")

	def test_technical_role_decides_nothing(self):
		_as("sysmgr")
		with self.assertRaises(PermissionError):
			smw_workflow.ktsm_suspend(self.prof, "x")
		with self.assertRaises(PermissionError):
			smw_workflow.ktsm_approve_supplier(self.prof)

	def test_approver_may_suspend_and_reinstate(self):
		_as("approver")
		smw_workflow.ktsm_suspend(self.prof, "audit")
		self.assertEqual(frappe.db.get_value("KTSM Supplier Profile", self.prof, "operational_status"), "Suspended")
		smw_workflow.ktsm_reinstate(self.prof, "cleared")
		self.assertEqual(frappe.db.get_value("KTSM Supplier Profile", self.prof, "operational_status"), "Active")

	def test_category_review_split_between_roles(self):
		a = self._assignment("Requested")
		_as("registry")
		smw_workflow.ktsm_start_category_review(a)
		with self.assertRaises(PermissionError):
			smw_workflow.ktsm_qualify_category(a)
		_as("compliance")
		smw_workflow.ktsm_qualify_category(a)
		self.assertEqual(frappe.db.get_value("KTSM Category Assignment", a, "qualification_status"), "Qualified")

	# -- XC-019: bare technical roles ----------------------------------------

	def test_system_manager_cannot_approve_return_reject_or_verify(self):
		_as("sysmgr")
		for call in (
			lambda: smw_workflow.ktsm_approve_supplier(self.prof),
			lambda: smw_workflow.ktsm_return_supplier(self.prof, "x"),
			lambda: smw_workflow.ktsm_reject_supplier(self.prof, "x"),
			lambda: smw_workflow.ktsm_start_review(self.prof),
			lambda: smw_workflow.ktsm_verify_document("none"),
			lambda: smw_workflow.ktsm_blacklist(self.prof, "x"),
		):
			with self.assertRaises(PermissionError):
				call()

	# -- XC-018: reads ----------------------------------------------------------

	def test_registry_reads_refuse_plain_internal_and_supplier_accounts(self):
		for who in ("plain", "supplier"):
			_as(who)
			for i, call in enumerate(
				(
					ktsm_landing.get_landing,
					lambda: ktsm_landing.get_suppliers({}),
					lambda: ktsm_landing.get_supplier_detail(self.code),
					lambda: eligibility.check_supplier_eligibility(self.code),
					lambda: eligibility.check_multiple_suppliers([self.code]),
					lambda: smw_workflow.ktsm_check_eligibility(self.code),
				)
			):
				with self.assertRaises(PermissionError, msg=f"{who} read #{i}"):
					call()

	def test_registry_reads_allowed_for_registry_roles_and_technical_readers(self):
		for who in ("registry", "approver", "sysmgr"):
			_as(who)
			self.assertTrue(ktsm_landing.get_landing().get("ok"))
			self.assertTrue(ktsm_landing.get_supplier_detail(self.code).get("ok"))
			self.assertIn("eligible", eligibility.check_supplier_eligibility(self.code))

	def test_supplier_may_read_own_eligibility_through_external_api(self):
		frappe.db.set_value("KTSM Supplier Profile", self.prof, "external_user", _USERS["supplier"][0])
		try:
			_as("supplier")
			self.assertIn("eligible", smw_public.ktsm_get_status(self.code))
		finally:
			frappe.set_user("Administrator")
			frappe.db.set_value("KTSM Supplier Profile", self.prof, "external_user", None)

	# -- XC-020: public registration -------------------------------------------

	def test_ktsm_register_is_rate_limited(self):
		# frappe.rate_limiter.rate_limit wraps the function with functools.wraps
		self.assertTrue(hasattr(smw_public.ktsm_register, "__wrapped__"))

	def test_ktsm_register_never_binds_an_existing_login(self):
		victim = _USERS["plain"][0]
		before = frappe.db.count("KTSM Supplier Profile")
		frappe.set_user("Guest")
		try:
			out = smw_public.ktsm_register("Impostor Co", victim, "I", "Company")
		finally:
			frappe.set_user("Administrator")
		try:
			self.assertTrue(out.get("ok"), out)
			prof = eligibility.get_profile_name_for_supplier_code(out["supplier_code"])
			self.assertFalse(frappe.db.get_value("KTSM Supplier Profile", prof, "external_user"))
			self.assertEqual(out.get("api_access"), "skipped")
		finally:
			self._remove_registration(out.get("supplier_code"))
		self.assertEqual(frappe.db.count("KTSM Supplier Profile"), before)

	def test_ktsm_register_creates_new_login_disabled_until_verified(self):
		email = f"ktsm.auth.new.{frappe.generate_hash(length=6)}@kentender.test"
		frappe.set_user("Guest")
		try:
			out = smw_public.ktsm_register("New Reg Co", email, "N", "Company")
		finally:
			frappe.set_user("Administrator")
		try:
			self.assertTrue(out.get("ok"), out)
			self.assertEqual(frappe.db.get_value("User", email, "enabled"), 0)
		finally:
			self._remove_registration(out.get("supplier_code"))
			if frappe.db.exists("User", email):
				frappe.delete_doc("User", email, force=True, ignore_permissions=True)

	@staticmethod
	def _remove_registration(code: str | None) -> None:
		if not code:
			return
		prof = eligibility.get_profile_name_for_supplier_code(code)
		erp = frappe.db.get_value("Supplier", {"kentender_supplier_code": code}, "name")
		if prof:
			for dt in ("KTSM Supplier API Access", "KTSM Status History"):
				for n in frappe.get_all(dt, {"supplier_profile": prof}, pluck="name"):
					frappe.delete_doc(dt, n, force=True, ignore_permissions=True)
			frappe.delete_doc("KTSM Supplier Profile", prof, force=True, ignore_permissions=True)
		if erp:
			frappe.delete_doc("Supplier", erp, force=True, ignore_permissions=True)
