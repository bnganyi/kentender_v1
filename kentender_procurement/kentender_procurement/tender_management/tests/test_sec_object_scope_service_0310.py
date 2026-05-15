# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""SEC-0310 — ``ObjectScopeService`` object scope checks.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_sec_object_scope_service_0310
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.security.authorization.decision_engine import (
	AuthorizationDecisionEngine,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import (
	DenialCode,
)
from kentender_procurement.tender_management.security.authorization.object_scope import (
	ObjectScopeService,
)
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService


class TestSecObjectScopeService0310(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		ObjectScopeService.clear_committee_registry()

	def tearDown(self) -> None:
		ObjectScopeService.clear_committee_registry()
		frappe.set_user("Administrator")
		super().tearDown()

	def _ensure_user(self, email: str) -> str:
		"""Create a **System User**; return Frappe ``User.name`` (may differ from email)."""
		self._cleanup_user(email)
		u = frappe.new_doc("User")
		u.email = email
		u.first_name = "SEC0310"
		u.user_type = "System User"
		u.enabled = 1
		u.new_password = "Test@1234"
		u.send_welcome_email = 0
		u.insert(ignore_permissions=True)
		uname = u.name
		frappe.db.set_value("User", uname, "user_type", "System User")
		return uname

	def _cleanup_user(self, email: str) -> None:
		name = frappe.db.get_value("User", {"email": email}, "name")
		if name:
			frappe.delete_doc("User", name, force=True, ignore_permissions=True)
		elif frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)

	def _minimal_tender(self, ref: str) -> str:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = f"SEC-0310 {ref}"
		doc.tender_reference = ref
		doc.insert(ignore_permissions=True)
		return doc.name

	def _delete_tender(self, name: str) -> None:
		if frappe.db.exists("TM2 Tender", name):
			for row in frappe.get_all(
				"Tender STD Instance",
				filters={"tm2_tender": name},
				pluck="name",
			):
				frappe.delete_doc("Tender STD Instance", row, force=True, ignore_permissions=True)
			frappe.delete_doc("TM2 Tender", name, force=True, ignore_permissions=True)

	def test_sec_0310_tender_owner_passes_stranger_denied(self) -> None:
		tn = self._minimal_tender(ref="scope-owner")
		try:
			owner = frappe.db.get_value("TM2 Tender", tn, "owner")
			self.assertTrue(owner)
			self.assertTrue(ObjectScopeService.check_tender_scope(owner, tn).allowed)
			other_email = "sec0310_stranger@example.com"
			other = self._ensure_user(other_email)
			self.assertFalse(ObjectScopeService.check_tender_scope(other, tn).allowed)
		finally:
			self._cleanup_user(other_email)
			self._delete_tender(tn)

	def test_sec_0310_committee_unassigned_denied_registered_allowed(self) -> None:
		tn = self._minimal_tender(ref="scope-committee")
		member_email = "sec0310_committee@example.com"
		member = self._ensure_user(member_email)
		try:
			self.assertFalse(
				ObjectScopeService.check_committee_scope(member, tn, "opening").allowed,
			)
			ObjectScopeService.register_committee_members(tn, "opening", [member])
			self.assertTrue(
				ObjectScopeService.check_committee_scope(member, tn, "opening").allowed,
			)
			self.assertFalse(
				ObjectScopeService.check_committee_scope(member, tn, "evaluation").allowed,
			)
		finally:
			ObjectScopeService.unregister_committee(tn, "opening")
			self._cleanup_user(member_email)
			self._delete_tender(tn)

	def test_sec_0310_std_template_non_governor_denied(self) -> None:
		if not frappe.db.exists("STD Template", TEMPLATE_CODE):
			self.skipTest("STD Template fixture not present on site.")
		other_email = "sec0310_tpl@example.com"
		other = self._ensure_user(other_email)
		try:
			self.assertFalse(
				ObjectScopeService.check_std_template_scope(other, TEMPLATE_CODE).allowed,
			)
			self.assertTrue(
				ObjectScopeService.check_std_template_scope("Administrator", TEMPLATE_CODE).allowed,
			)
		finally:
			self._cleanup_user(other_email)

	def test_sec_0310_std_instance_tender_owner_in_scope(self) -> None:
		tn = self._minimal_tender(ref="scope-inst")
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tn,
				ignore_permissions=True,
				record_template_usage=False,
			)
			owner = frappe.db.get_value("TM2 Tender", tn, "owner")
			self.assertTrue(ObjectScopeService.check_std_instance_scope(owner, si.name).allowed)
		finally:
			self._delete_tender(tn)

	def test_sec_0310_assert_tender_scope_raises(self) -> None:
		tn = self._minimal_tender(ref="scope-assert")
		other_email = "sec0310_assert@example.com"
		other = self._ensure_user(other_email)
		try:
			with self.assertRaises(frappe.ValidationError):
				ObjectScopeService.assert_tender_scope(other, tn)
		finally:
			self._cleanup_user(other_email)
			self._delete_tender(tn)

	def test_sec_0310_decision_engine_enforces_tender_scope(self) -> None:
		tn = self._minimal_tender(ref="scope-engine")
		other_email = "sec0310_eng@example.com"
		other = self._ensure_user(other_email)
		try:
			res = AuthorizationDecisionEngine.evaluate(
				other,
				"PUBLISH_TENDER",
				"TM2 Tender",
				tn,
				context={
					"granted_permissions": ["PERM_TENDER_PUBLISH"],
					"enforce_object_scope": True,
					"object_scope_kind": "tender",
				},
			)
			self.assertFalse(res["allowed"])
			self.assertEqual(res.get("denial_code"), DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED)
		finally:
			self._cleanup_user(other_email)
			self._delete_tender(tn)
