# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

"""AUD-XC-004/018/019/020: who may read or change the KTSM supplier registry."""

import random

import frappe
from frappe.exceptions import PermissionError
from frappe.tests import IntegrationTestCase

from kentender_core.services.command_write_guard import fixture_insert, purge_doc
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
	"planner": ("ktsm.auth.planner@kentender.test", "System User", ["Procurement Planner"]),
	"auditor": ("ktsm.auth.auditor@kentender.test", "System User", [registry_access.AUDITOR]),
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
			purge_doc("KTSM Category Assignment", name)
		for name in frappe.get_all("KTSM Status History", {"supplier_profile": cls.prof}, pluck="name"):
			frappe.delete_doc("KTSM Status History", name, force=True, ignore_permissions=True)
		purge_doc("KTSM Supplier Profile", cls.prof)
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
			purge_doc("KTSM Category Assignment", name)
		frappe.db.set_value("KTSM Supplier Profile", self.prof, "operational_status", "Pending")

	def _assignment(self, status: str = "Requested") -> str:
		return fixture_insert(
			frappe.get_doc(
				{
					"doctype": "KTSM Category Assignment",
					"supplier_profile": self.prof,
					"category": self.cat,
					"qualification_status": status,
				}
			)
		).name

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

	def test_the_administrator_user_decides_nothing_either(self):
		"""RG-10: Frappe returns every Role for the literal Administrator user, so a bare role test passes for
		it. The registry gate refuses it for every mutation and still lets it read."""
		frappe.set_user("Administrator")
		a = self._assignment("Under Review")
		for capability in registry_access.CAPABILITIES:
			if capability == "read_registry":
				continue
			self.assertFalse(registry_access.has_capability(capability, "Administrator"), capability)
		self.assertTrue(registry_access.has_capability("read_registry", "Administrator"))
		for i, call in enumerate(
			(
				lambda: smw_workflow.ktsm_approve_supplier(self.prof),
				lambda: smw_workflow.ktsm_return_supplier(self.prof, "x"),
				lambda: smw_workflow.ktsm_reject_supplier(self.prof, "x"),
				lambda: smw_workflow.ktsm_start_review(self.prof),
				lambda: smw_workflow.ktsm_suspend(self.prof, "x"),
				lambda: smw_workflow.ktsm_reinstate(self.prof, "x"),
				lambda: smw_workflow.ktsm_blacklist(self.prof, "x"),
				lambda: smw_workflow.ktsm_verify_document("none"),
				lambda: smw_workflow.ktsm_qualify_category(a),
				lambda: ktsm_landing.perform_action("blacklist", self.code, "x"),
			)
		):
			with self.assertRaises(PermissionError, msg=f"Administrator call #{i}"):
				call()
		self.assertEqual(frappe.db.get_value("KTSM Supplier Profile", self.prof, "operational_status"), "Pending")

	# -- RG-11: builder writes ----------------------------------------------------

	def _builder_profile(self) -> tuple[str, str, str]:
		erp, prof, code = _profile(f"SUP-KE-2097-{random.randint(1000, 9999)}")
		self.addCleanup(self._remove_builder_profile, erp, prof)
		return erp, prof, code

	@staticmethod
	def _remove_builder_profile(erp: str, prof: str) -> None:
		frappe.set_user("Administrator")
		purge_doc("KTSM Supplier Profile", prof)
		frappe.delete_doc("Supplier", erp, force=True, ignore_permissions=True)

	def test_the_builder_writes_need_the_write_capability_not_the_read_grant(self):
		erp, prof, _code = self._builder_profile()
		before_profiles = frappe.db.count("KTSM Supplier Profile")
		for who in ("auditor", "sysmgr", "plain", "supplier"):
			_as(who)
			with self.assertRaises(PermissionError, msg=f"{who} create"):
				ktsm_landing.create_supplier_builder_profile("Nobody Ltd")
			with self.assertRaises(PermissionError, msg=f"{who} rename"):
				ktsm_landing.update_builder_identity(prof, "Renamed By " + who)
			with self.assertRaises(PermissionError, msg=f"{who} submit"):
				smw_workflow.ktsm_submit_for_review(prof)
		frappe.set_user("Administrator")
		with self.assertRaises(PermissionError, msg="Administrator rename"):
			ktsm_landing.update_builder_identity(prof, "Renamed By Administrator")
		self.assertEqual(frappe.db.count("KTSM Supplier Profile"), before_profiles)
		self.assertEqual(frappe.db.get_value("Supplier", erp, "supplier_name"), f"Auth {_code}")

	def test_a_planner_may_prepare_a_draft_but_not_rename_a_registered_supplier(self):
		erp, prof, code = self._builder_profile()
		_as("planner")
		out = ktsm_landing.update_builder_identity(prof, "Draft Rename Ltd")
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(frappe.db.get_value("Supplier", erp, "supplier_name"), "Draft Rename Ltd")
		frappe.set_user("Administrator")
		frappe.db.set_value("KTSM Supplier Profile", prof, "approval_status", "Approved")
		_as("planner")
		with self.assertRaises(PermissionError):
			ktsm_landing.update_builder_identity(prof, "Registered Supplier Renamed")
		self.assertEqual(frappe.db.get_value("Supplier", erp, "supplier_name"), "Draft Rename Ltd")

	# -- RG-30: technical roles do not act for a supplier --------------------------

	def test_system_manager_and_administrator_cannot_act_for_a_supplier_through_the_external_api(self):
		_erp, prof, code = self._builder_profile()
		for who in ("sysmgr", "Administrator"):
			if who == "Administrator":
				frappe.set_user("Administrator")
			else:
				_as(who)
			for i, call in enumerate(
				(
					lambda: smw_public.ktsm_update_profile(code, "High"),
					lambda: smw_public.ktsm_supplier_submit(code),
					lambda: smw_public.ktsm_upload_document(code, "X"),
				)
			):
				with self.assertRaises(PermissionError, msg=f"{who} call #{i}"):
					call()
		self.assertEqual(frappe.db.get_value("KTSM Supplier Profile", prof, "approval_status"), "Draft")

	def test_the_suppliers_own_account_and_a_registry_preparer_still_may(self):
		_erp, prof, code = self._builder_profile()
		frappe.db.set_value("KTSM Supplier Profile", prof, "external_user", _USERS["supplier"][0])
		_as("supplier")
		self.assertEqual(smw_public.ktsm_update_profile(code, "High").get("ok") is not False, True)
		_as("registry")
		smw_public.ktsm_update_profile(code, "Low")
		self.assertEqual(frappe.db.get_value("KTSM Supplier Profile", prof, "risk_level"), "Low")

	# -- RG-13: the registry state is command-only --------------------------------

	def test_registry_state_cannot_be_written_over_rest_by_a_technical_user(self):
		from kentender_core.services.command_write_guard import CommandWriteError

		_erp, prof, _code = self._builder_profile()
		frappe.db.set_value("KTSM Supplier Profile", prof, {"approval_status": "Approved", "operational_status": "Active"})
		assignment = self._assignment("Qualified")
		for who in ("sysmgr", "Administrator"):
			if who == "Administrator":
				frappe.set_user("Administrator")
			else:
				_as(who)
			# PUT an Approved profile back to Draft (the NEW status "Draft" was not in the old locked list).
			doc = frappe.get_doc("KTSM Supplier Profile", prof)
			doc.approval_status = "Draft"
			with self.assertRaises((CommandWriteError, PermissionError), msg=f"{who} approved -> draft"):
				doc.save()
			# POST a profile that is born Approved.
			sg = frappe.db.get_value("Supplier", _erp, "supplier_group")
			erp2 = frappe.get_doc({"doctype": "Supplier", "supplier_name": f"Born Approved {who}", "supplier_group": sg, "supplier_type": "Company"})
			frappe.set_user("Administrator")
			erp2.insert(ignore_permissions=True)
			self.addCleanup(frappe.delete_doc, "Supplier", erp2.name, force=True, ignore_permissions=True)
			(frappe.set_user("Administrator") if who == "Administrator" else _as(who))
			with self.assertRaises((CommandWriteError, PermissionError), msg=f"{who} born approved"):
				frappe.get_doc({"doctype": "KTSM Supplier Profile", "erpnext_supplier": erp2.name, "approval_status": "Approved"}).insert(
					ignore_permissions=True
				)
			# Category qualification, document verification and API access.
			row = frappe.get_doc("KTSM Category Assignment", assignment)
			row.qualification_status = "Requested"
			with self.assertRaises((CommandWriteError, PermissionError), msg=f"{who} category"):
				row.save()
			with self.assertRaises((CommandWriteError, PermissionError), msg=f"{who} api access"):
				frappe.get_doc(
					{"doctype": "KTSM Supplier API Access", "supplier_profile": prof, "external_user": "Administrator", "access_status": "Active"}
				).insert(ignore_permissions=True)
			with self.assertRaises((CommandWriteError, PermissionError), msg=f"{who} delete profile"):
				frappe.delete_doc("KTSM Supplier Profile", prof, force=True, ignore_permissions=True)
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_value("KTSM Supplier Profile", prof, "approval_status"), "Approved")
		self.assertEqual(frappe.db.get_value("KTSM Category Assignment", assignment, "qualification_status"), "Qualified")
		self.assertFalse(frappe.db.exists("KTSM Supplier API Access", {"supplier_profile": prof}))

	def test_a_registry_officer_may_still_edit_descriptive_fields_but_not_the_status(self):
		from kentender_core.services.command_write_guard import CommandWriteError

		_erp, prof, _code = self._builder_profile()
		_as("registry")
		doc = frappe.get_doc("KTSM Supplier Profile", prof)
		doc.risk_level = "High"
		doc.save()
		self.assertEqual(frappe.db.get_value("KTSM Supplier Profile", prof, "risk_level"), "High")
		doc.approval_status = "Approved"
		with self.assertRaises(CommandWriteError):
			doc.save()

	def test_the_governance_commands_still_move_the_state(self):
		_erp, prof, _code = self._builder_profile()
		_as("approver")
		smw_workflow.ktsm_suspend(prof, "audit")
		self.assertEqual(frappe.db.get_value("KTSM Supplier Profile", prof, "operational_status"), "Suspended")

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

	def test_ktsm_register_is_post_only_and_rate_limited(self):
		self.assertEqual(frappe.allowed_http_methods_for_whitelisted_func[smw_public.ktsm_register], ["POST"])
		self.assertIn(smw_public.ktsm_register, frappe.guest_methods)
		# The sixth call from one address within the hour is refused (limit=5), behaviourally.
		previous = (getattr(frappe.local, "request", None), getattr(frappe.local, "request_ip", None), frappe.form_dict.get("cmd"))
		frappe.local.request = frappe._dict(method="POST", path="/api/method/ktsm_register", headers={})
		frappe.local.request_ip = "203.0.113.77"
		cmd = f"kt.rg12.ratelimit.{frappe.generate_hash(length=6)}"
		codes = []

		def _restore():
			frappe.local.request, frappe.local.request_ip = previous[0], previous[1]
			if previous[2] is None:
				frappe.form_dict.pop("cmd", None)
			else:
				frappe.form_dict.cmd = previous[2]
			for code in codes:
				self._remove_registration(code)

		self.addCleanup(_restore)
		frappe.set_user("Guest")
		frappe.form_dict.cmd = cmd  # after set_user, which replaces the form dict
		try:
			for i in range(5):
				out = smw_public.ktsm_register(f"Rate Co {i}", f"rate{i}.{frappe.generate_hash(length=4)}@kentender.test")
				codes.append(out["supplier_code"])
			with self.assertRaises(frappe.RateLimitExceededError):
				smw_public.ktsm_register("Rate Co 6", "rate6@kentender.test")
		finally:
			frappe.set_user("Administrator")

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

	def test_ktsm_register_creates_no_login_and_no_api_access_before_the_address_is_verified(self):
		"""RG-12: a disabled User for an unverified address could never be enabled and stopped the real
		owner of the address from signing up. Nothing but the Draft profile exists until verification."""
		email = f"ktsm.auth.new.{frappe.generate_hash(length=6)}@kentender.test"
		frappe.set_user("Guest")
		try:
			out = smw_public.ktsm_register("New Reg Co", email, "N", "Company")
		finally:
			frappe.set_user("Administrator")
		try:
			self.assertTrue(out.get("ok"), out)
			self.assertFalse(frappe.db.exists("User", email))
			prof = eligibility.get_profile_name_for_supplier_code(out["supplier_code"])
			self.assertTrue(prof)
			self.assertFalse(frappe.db.exists("KTSM Supplier API Access", {"supplier_profile": prof}))
			self.assertEqual(frappe.db.get_value("KTSM Supplier Profile", prof, "approval_status"), "Draft")
			self.assertEqual(out.get("api_access"), "skipped")
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
					purge_doc(dt, n) if dt != "KTSM Status History" else frappe.delete_doc(dt, n, force=True, ignore_permissions=True)
			purge_doc("KTSM Supplier Profile", prof)
		if erp:
			frappe.delete_doc("Supplier", erp, force=True, ignore_permissions=True)
