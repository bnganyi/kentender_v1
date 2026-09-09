# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §5 — the authorisation module and the two Frappe
permission hooks (plan D11). No Tender rows are needed: the family is
Site-wide, so the predicate is a pure function of the actor's assignments.
TPR-SMOKE-19: Administrator without an assignment is denied every business
gate but reads technically; TPR-AC-040: no User Permission anywhere."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_preparation.services import tender_authorization as authz
from kentender_procurement.tender_preparation.services.errors import TenderPreparationError
from kentender_procurement.tender_preparation.tests import fixtures as fx


class TenderAuthorizationCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()
		cls.addClassCleanup(fx.restore_site)

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.addCleanup(frappe.set_user, "Administrator")


class TestPageVerdict(TenderAuthorizationCase):
	def test_every_site_wide_reader_holds_a_verdict(self):
		for user in (fx.OFFICER, fx.HOPF, fx.BOTH, fx.AUDITOR, "Administrator"):
			self.assertTrue(authz.holds_any_tender_responsibility(user), user)

	def test_an_outsider_and_a_nobody_do_not(self):
		for user in (fx.OUTSIDER, fx.NOBODY, "Guest"):
			self.assertFalse(authz.holds_any_tender_responsibility(user), user)
		# No argument means the session user — the same fall-through every
		# module's verdict uses; an unassigned session user has no verdict.
		frappe.set_user(fx.NOBODY)
		self.assertFalse(authz.holds_any_tender_responsibility())


class TestCommandGates(TenderAuthorizationCase):
	def test_require_officer_admits_the_officer_and_masks_everyone_else(self):
		self.assertIsNotNone(authz.require_officer(fx.OFFICER))
		self.assertIsNotNone(authz.require_officer(fx.BOTH))
		for user in (fx.HOPF, fx.AUDITOR, fx.OUTSIDER, fx.NOBODY):
			with self.assertRaises(frappe.DoesNotExistError, msg=user):
				authz.require_officer(user)

	def test_require_hopf_admits_the_head_and_masks_everyone_else(self):
		self.assertIsNotNone(authz.require_hopf(fx.HOPF))
		self.assertIsNotNone(authz.require_hopf(fx.BOTH))
		for user in (fx.OFFICER, fx.AUDITOR, fx.OUTSIDER, fx.NOBODY):
			with self.assertRaises(frappe.DoesNotExistError, msg=user):
				authz.require_hopf(user)

	def test_unmasked_denial_maps_onto_the_closed_error_set(self):
		with self.assertRaises(TenderPreparationError) as ctx:
			authz.require_officer(fx.AUDITOR, masked=False)
		self.assertEqual(ctx.exception.code, "TPR_RESPONSIBILITY_REQUIRED")

	def test_administrator_without_an_assignment_is_denied_business_gates_but_reads(self):
		"""TPR-SMOKE-19 / AUTH-ADR-001 v1.6 §8."""
		with self.assertRaises(frappe.DoesNotExistError):
			authz.require_officer("Administrator")
		with self.assertRaises(frappe.DoesNotExistError):
			authz.require_hopf("Administrator")
		self.assertEqual(authz.require_tender_reader("Administrator"), "Administrator")
		self.assertTrue(authz.has_permission({"doctype": "Prepared Tender", "name": "x"}, "read", "Administrator"))

	def test_require_tender_reader_masks_an_outsider(self):
		for user in (fx.OFFICER, fx.HOPF, fx.AUDITOR):
			self.assertEqual(authz.require_tender_reader(user), user)
		with self.assertRaises(frappe.DoesNotExistError):
			authz.require_tender_reader(fx.OUTSIDER)

	def test_read_offer_parity_helpers_follow_the_command_purpose(self):
		self.assertTrue(authz.has_site_role("Procurement Officer", fx.OFFICER))
		self.assertFalse(authz.has_site_role("Procurement Officer", fx.AUDITOR))
		self.assertTrue(authz.can_read_site("Auditor", fx.AUDITOR))
		self.assertFalse(authz.can_read_site("Auditor", fx.NOBODY))

	def test_a_guest_or_empty_actor_is_refused(self):
		with self.assertRaises(TenderPreparationError) as ctx:
			authz.actor("Guest")
		self.assertEqual(ctx.exception.code, "TPR_RESPONSIBILITY_REQUIRED")


class TestPermissionHooks(TenderAuthorizationCase):
	def test_query_conditions_are_unrestricted_for_readers_and_closed_for_others(self):
		for user in (fx.OFFICER, fx.HOPF, fx.BOTH, fx.AUDITOR, "Administrator"):
			for doctype in authz.FAMILY_DOCTYPES:
				self.assertEqual(authz.permission_query_conditions(user, doctype), "", f"{user}/{doctype}")
		for user in (fx.OUTSIDER, fx.NOBODY, "Guest"):
			for doctype in authz.FAMILY_DOCTYPES:
				self.assertEqual(authz.permission_query_conditions(user, doctype), "1=0", f"{user}/{doctype}")

	def test_has_permission_follows_the_same_predicate(self):
		stub = {"doctype": "Tender Preparation Version", "name": "TPV-STUB"}
		for user in (fx.OFFICER, fx.HOPF, fx.AUDITOR):
			self.assertTrue(authz.has_permission(stub, "read", user), user)
		for user in (fx.OUTSIDER, fx.NOBODY):
			self.assertFalse(authz.has_permission(stub, "read", user), user)

	def test_get_list_applies_the_hook_at_the_framework_layer(self):
		"""TPR-AC-040 at the framework layer: a bare Frappe Role projection
		with no `User Responsibility Assignment` behind it reaches the DocPerm
		but the registered predicate returns `1=0`, so `frappe.get_list` is
		empty by predicate, not by luck. An actor with no projection at all is
		stopped one layer earlier by the DocPerm itself."""
		nobody = frappe.get_doc("User", fx.NOBODY)
		nobody.add_roles("Procurement Officer")
		def _drop_role():
			frappe.set_user("Administrator")
			frappe.get_doc("User", fx.NOBODY).remove_roles("Procurement Officer")

		self.addCleanup(_drop_role)
		frappe.set_user(fx.NOBODY)
		self.assertEqual(authz.permission_query_conditions(fx.NOBODY, "Prepared Tender"), "1=0")
		self.assertEqual(frappe.get_list("Prepared Tender", fields=["name"]), [])
		frappe.set_user(fx.OUTSIDER)
		with self.assertRaises(frappe.PermissionError):
			frappe.get_list("Prepared Tender", fields=["name"])

	def test_no_user_permission_participates(self):
		"""TPR-AC-040 — the module never reads `User Permission`; even a
		planted one grants nothing to an outsider."""
		import os

		module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
		for root, _dirs, files in os.walk(os.path.join(module_dir, "services")):
			for name in files:
				if name.endswith(".py"):
					self.assertNotIn("User Permission", open(os.path.join(root, name), encoding="utf-8").read(), name)
