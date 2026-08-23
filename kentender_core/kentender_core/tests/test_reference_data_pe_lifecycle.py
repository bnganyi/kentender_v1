"""CFG-CHG-002 Phase 1 — Procuring Entity / Procuring Entity Version lifecycle.
Covers BR-001, BR-002, BR-014, BR-015 and AC-001..005 evidence for CFG-109.
"""

from __future__ import annotations

import json
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime

from kentender_core.services import reference_data_permissions as perm
from kentender_core.services.reference_data_transitions import (
	approve_activate_pe,
	create_pe_draft,
	propose_amendment,
	retire_pe,
	submit_pe,
	suspend_pe,
)


class TestReferenceDataPELifecycle(IntegrationTestCase):
	def setUp(self):
		self.suffix = uuid4().hex[:8]
		self.steward = self._user("steward")
		self.approver = self._user("approver")
		self.entity_code = f"PE-TEST-{self.suffix}".upper()
		self.pe_type = self._pe_type()
		self.anchor_pe = frappe.get_all("Procuring Entity", pluck="name", limit=1)[0]

		# Steward needs *some* active assignment carrying PE_CREATE_DRAFT to create a
		# brand-new PE at all (see reference_data_permissions.require_pe_create_capability
		# docstring for why this can't be scoped to the not-yet-existing PE).
		self.steward_profile = self._profile("STEWARD", [perm.PE_CREATE_DRAFT, perm.PE_PROPOSE_AMENDMENT])
		self.approver_profile = self._profile("APPROVER", [perm.PE_APPROVE_ACTIVATE, perm.PE_SUSPEND, perm.PE_RETIRE])
		self._assign(self.steward, self.steward_profile, self.anchor_pe)
		self.sod_rule = self._sod_rule()

	def tearDown(self):
		for doctype, filters in (
			("Procuring Entity Version", [["procuring_entity", "like", f"PE-TEST-{self.suffix}%"]]),
			("Procuring Entity", [["entity_code", "like", f"PE-TEST-{self.suffix}%"]]),
			("Audit Event", [["document_name", "like", f"PE-TEST-{self.suffix}%"]]),
			("Operational Scope Assignment", [["name", "like", f"%{self.suffix}%"]]),
			("Separation of Duties Rule", [["name", "like", f"%{self.suffix}%"]]),
			("Capability Profile", [["name", "like", f"%{self.suffix}%"]]),
			("PE Type", [["name", "like", f"%{self.suffix}%"]]),
		):
			for name in frappe.get_all(doctype, filters=filters, pluck="name"):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		for user in (self.steward, self.approver):
			if frappe.db.exists("User", user):
				frappe.delete_doc("User", user, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _user(self, label):
		email = f"cfgpefy.{label}.{self.suffix}@test.local"
		frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": label, "enabled": 1, "send_welcome_email": 0}
		).insert(ignore_permissions=True)
		return email

	def _pe_type(self):
		code = f"TESTTYPE_{self.suffix}".upper()
		frappe.get_doc(
			{"doctype": "PE Type", "type_code": code, "label": "Test Type", "status": "Active"}
		).insert(ignore_permissions=True)
		return code

	def _profile(self, label, capabilities):
		doc = frappe.get_doc(
			{
				"doctype": "Capability Profile",
				"profile_id": f"CAP-{label}-{self.suffix}",
				"profile_name": f"Test {label}",
				"capabilities": json.dumps(capabilities),
				"allows_entity_wide": 1,
				"status": "Active",
				"concurrency_token": uuid4().hex,
			}
		)
		doc.insert(ignore_permissions=True)
		return doc.name

	def _assign(self, user, profile, pe):
		doc = frappe.get_doc(
			{
				"doctype": "Operational Scope Assignment",
				"assignment_id": f"OSA-{uuid4().hex[:10]}-{self.suffix}",
				"user_id": user,
				"capability_profile_id": profile,
				"procuring_entity_id": pe,
				"effective_from": add_days(now_datetime(), -1),
				"status": "Active",
				"assigned_by": "Administrator",
				"assigned_at": now_datetime(),
				"concurrency_token": uuid4().hex,
			}
		)
		doc.insert(ignore_permissions=True)
		return doc.name

	def _sod_rule(self):
		doc = frappe.get_doc(
			{
				"doctype": "Separation of Duties Rule",
				"rule_id": f"SOD-{self.suffix}",
				"rule_name": "Test PE create vs approve",
				"first_capability": perm.PE_CREATE_DRAFT,
				"second_capability": perm.PE_APPROVE_ACTIVATE,
				"enforcement_level": "Workflow instance",
				"status": "Active",
				"effective_from": add_days(now_datetime(), -1),
			}
		)
		doc.insert(ignore_permissions=True)
		return doc.name

	def _create_and_scope(self):
		result = create_pe_draft(
			{
				"entity_code": self.entity_code,
				"legal_name": "Test Entity",
				"display_name": "Test Entity",
				"pe_type_code": self.pe_type,
			},
			user=self.steward,
		)
		# Now the PE exists — grant PE-scoped assignments for submit/approve, the
		# bootstrapping step a real access administrator would perform next.
		self._assign(self.steward, self.steward_profile, self.entity_code)
		self._assign(self.approver, self.approver_profile, self.entity_code)
		return result

	def test_draft_submit_approve_activate(self):
		result = self._create_and_scope()
		self.assertEqual(result["pe"], self.entity_code)
		pe = frappe.get_doc("Procuring Entity", self.entity_code)
		self.assertEqual(pe.status, "Draft")
		version = frappe.get_doc("Procuring Entity Version", pe.current_version_id)
		self.assertEqual(version.version_state, "Draft")

		submit_pe(self.entity_code, user=self.steward)
		version.reload()
		self.assertEqual(version.version_state, "Under Review")

		approve_activate_pe(self.entity_code, user=self.approver)
		pe.reload()
		version.reload()
		self.assertEqual(pe.status, "Active")
		self.assertEqual(version.version_state, "Active")

	def test_creator_cannot_approve_own_proposal_sod(self):
		self._create_and_scope()
		submit_pe(self.entity_code, user=self.steward)
		with self.assertRaises(frappe.PermissionError):
			approve_activate_pe(self.entity_code, user=self.steward)

	def test_duplicate_code_rejected(self):
		self._create_and_scope()
		with self.assertRaises(frappe.ValidationError):
			create_pe_draft(
				{
					"entity_code": self.entity_code,
					"legal_name": "Dup",
					"display_name": "Dup",
					"pe_type_code": self.pe_type,
				},
				user=self.steward,
			)

	def test_active_pe_has_exactly_one_active_version(self):
		self._create_and_scope()
		submit_pe(self.entity_code, user=self.steward)
		approve_activate_pe(self.entity_code, user=self.approver)
		versions = frappe.get_all(
			"Procuring Entity Version",
			filters={"procuring_entity": self.entity_code, "version_state": "Active"},
		)
		self.assertEqual(len(versions), 1)

	def test_suspend_then_retire_requires_reason_and_capability(self):
		self._create_and_scope()
		submit_pe(self.entity_code, user=self.steward)
		approve_activate_pe(self.entity_code, user=self.approver)

		with self.assertRaises(frappe.ValidationError):
			suspend_pe(self.entity_code, "", user=self.approver)  # empty reason rejected

		suspend_pe(self.entity_code, "Under review", user=self.approver)
		pe = frappe.get_doc("Procuring Entity", self.entity_code)
		self.assertEqual(pe.status, "Suspended")

		with self.assertRaises(frappe.PermissionError):
			retire_pe(self.entity_code, "No longer needed", frappe.utils.today(), user=self.steward)

		retire_pe(self.entity_code, "No longer needed", frappe.utils.today(), user=self.approver)
		pe.reload()
		self.assertEqual(pe.status, "Retired")

	def test_propose_amendment_can_be_submitted_and_approved(self):
		"""An amendment's new Draft version must become the PE's current_version_id
		immediately, or submit_pe/approve_activate_pe (which always act on
		pe.current_version_id) can never progress it — discovered wiring the UI's
		"Propose amendment" action, not covered by the original Phase 1 tests."""
		self._create_and_scope()
		submit_pe(self.entity_code, user=self.steward)
		approve_activate_pe(self.entity_code, user=self.approver)

		propose_amendment(self.entity_code, "Legal name correction", user=self.steward)
		pe = frappe.get_doc("Procuring Entity", self.entity_code)
		amended_version = frappe.get_doc("Procuring Entity Version", pe.current_version_id)
		self.assertEqual(amended_version.version_no, 2)
		self.assertEqual(amended_version.version_state, "Draft")

		submit_pe(self.entity_code, user=self.steward)
		amended_version.reload()
		self.assertEqual(amended_version.version_state, "Under Review")

		approve_activate_pe(self.entity_code, user=self.approver)
		amended_version.reload()
		pe.reload()
		self.assertEqual(amended_version.version_state, "Active")
		self.assertEqual(pe.status, "Active")

	def test_referenced_pe_never_physically_deleted_by_lifecycle(self):
		"""BR-015 — the lifecycle service itself never calls delete_doc; only test
		teardown (owned-fixture cleanup) deletes these rows."""
		self._create_and_scope()
		submit_pe(self.entity_code, user=self.steward)
		approve_activate_pe(self.entity_code, user=self.approver)
		self.assertTrue(frappe.db.exists("Procuring Entity", self.entity_code))
