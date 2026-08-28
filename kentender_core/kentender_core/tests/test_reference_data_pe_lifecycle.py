"""CFG-CHG-002 v0.4 Phase 1 — Procuring Entity / Procuring Entity Version
lifecycle under the single Reference Data Manager Role model. Covers
CFG-PEFY-BR-001/002/014/015 and CFG-PEFY-AC-001..005.
"""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services.reference_data_permissions import REFERENCE_DATA_MANAGER_ROLE
from kentender_core.services.reference_data_queries import get_procuring_entity
from kentender_core.services.reference_data_transitions import (
	activate_pe,
	create_pe_draft,
	propose_amendment,
	retire_pe,
	suspend_pe,
	update_pe_draft,
)


class TestReferenceDataPELifecycle(IntegrationTestCase):
	def setUp(self):
		self.suffix = uuid4().hex[:8]
		self.manager = self._user("manager")
		self.other = self._user("other")
		self.entity_code = f"PE-TEST-{self.suffix}".upper()
		self.pe_type = self._pe_type()

		if not frappe.db.exists("Role", REFERENCE_DATA_MANAGER_ROLE):
			frappe.get_doc({"doctype": "Role", "role_name": REFERENCE_DATA_MANAGER_ROLE, "desk_access": 1}).insert(
				ignore_permissions=True
			)
		frappe.get_doc("User", self.manager).add_roles(REFERENCE_DATA_MANAGER_ROLE)

	def tearDown(self):
		for doctype, filters in (
			("Procuring Entity Version", [["procuring_entity", "like", f"PE-TEST-{self.suffix}%"]]),
			("Procuring Entity", [["entity_code", "like", f"PE-TEST-{self.suffix}%"]]),
			("Audit Event", [["document_name", "like", f"PE-TEST-{self.suffix}%"]]),
			("PE Type", [["name", "like", f"%{self.suffix}%"]]),
		):
			for name in frappe.get_all(doctype, filters=filters, pluck="name"):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		for user in (self.manager, self.other):
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

	def _create(self):
		return create_pe_draft(
			{
				"entity_code": self.entity_code,
				"legal_name": "Test Entity",
				"display_name": "Test Entity",
				"pe_type_code": self.pe_type,
			},
			user=self.manager,
		)

	def test_draft_and_activate(self):
		result = self._create()
		self.assertEqual(result["pe"], self.entity_code)
		pe = frappe.get_doc("Procuring Entity", self.entity_code)
		self.assertEqual(pe.status, "Draft")
		version = frappe.get_doc("Procuring Entity Version", pe.current_version_id)
		self.assertEqual(version.version_state, "Draft")

		activate_pe(self.entity_code, user=self.manager)
		pe.reload()
		version.reload()
		self.assertEqual(pe.status, "Active")
		self.assertEqual(version.version_state, "Active")

	def test_draft_stays_editable_before_activate(self):
		"""A Draft PE is a dead end without this — Create draft and Activate are
		separate steps (§6.1), so the draft must be correctable in between."""
		self._create()

		update_pe_draft(
			self.entity_code,
			{"legal_name": "Corrected Entity", "display_name": "Corrected Entity", "pe_type_code": self.pe_type},
			user=self.manager,
		)

		pe = frappe.get_doc("Procuring Entity", self.entity_code)
		version = frappe.get_doc("Procuring Entity Version", pe.current_version_id)
		self.assertEqual(version.legal_name, "Corrected Entity")
		self.assertEqual(version.version_state, "Draft")
		self.assertEqual(pe.status, "Draft")

		activate_pe(self.entity_code, user=self.manager)
		version.reload()
		self.assertEqual(version.legal_name, "Corrected Entity")

	def test_cannot_edit_once_active(self):
		self._create()
		activate_pe(self.entity_code, user=self.manager)

		with self.assertRaises(frappe.ValidationError):
			update_pe_draft(self.entity_code, {"legal_name": "Too Late"}, user=self.manager)

	def test_edit_draft_requires_reference_data_manager_role(self):
		self._create()

		with self.assertRaises(frappe.PermissionError):
			update_pe_draft(self.entity_code, {"legal_name": "Sneaky"}, user=self.other)

	def test_create_requires_reference_data_manager_role(self):
		with self.assertRaises(frappe.PermissionError):
			create_pe_draft(
				{
					"entity_code": self.entity_code,
					"legal_name": "Test Entity",
					"display_name": "Test Entity",
					"pe_type_code": self.pe_type,
				},
				user=self.other,
			)

	def test_activate_requires_reference_data_manager_role_no_maker_checker(self):
		"""CFG-CHG-002 v0.4 §1 — no maker-checker chain for reference data: the
		same Reference Data Manager who created the draft may also activate it."""
		self._create()
		activate_pe(self.entity_code, user=self.manager)  # must not raise
		pe = frappe.get_doc("Procuring Entity", self.entity_code)
		self.assertEqual(pe.status, "Active")

	def test_duplicate_code_rejected(self):
		self._create()
		with self.assertRaises(frappe.ValidationError):
			create_pe_draft(
				{
					"entity_code": self.entity_code,
					"legal_name": "Dup",
					"display_name": "Dup",
					"pe_type_code": self.pe_type,
				},
				user=self.manager,
			)

	def test_active_pe_has_exactly_one_active_version(self):
		self._create()
		activate_pe(self.entity_code, user=self.manager)
		versions = frappe.get_all(
			"Procuring Entity Version",
			filters={"procuring_entity": self.entity_code, "version_state": "Active"},
		)
		self.assertEqual(len(versions), 1)

	def test_suspend_then_retire(self):
		self._create()
		activate_pe(self.entity_code, user=self.manager)

		with self.assertRaises(frappe.ValidationError):
			suspend_pe(self.entity_code, "", user=self.manager)  # empty reason rejected

		suspend_pe(self.entity_code, "Under review", user=self.manager)
		pe = frappe.get_doc("Procuring Entity", self.entity_code)
		self.assertEqual(pe.status, "Suspended")

		with self.assertRaises(frappe.PermissionError):
			retire_pe(self.entity_code, "No longer needed", frappe.utils.today(), user=self.other)

		retire_pe(self.entity_code, "No longer needed", frappe.utils.today(), user=self.manager)
		pe.reload()
		self.assertEqual(pe.status, "Retired")

	def test_propose_amendment_can_be_activated(self):
		"""An amendment's new Draft version must become the PE's current_version_id
		immediately, or activate_pe (which always acts on pe.current_version_id)
		can never progress it."""
		self._create()
		activate_pe(self.entity_code, user=self.manager)

		propose_amendment(self.entity_code, "Legal name correction", user=self.manager)
		pe = frappe.get_doc("Procuring Entity", self.entity_code)
		amended_version = frappe.get_doc("Procuring Entity Version", pe.current_version_id)
		self.assertEqual(amended_version.version_no, 2)
		self.assertEqual(amended_version.version_state, "Draft")

		activate_pe(self.entity_code, user=self.manager)
		amended_version.reload()
		pe.reload()
		self.assertEqual(amended_version.version_state, "Active")
		self.assertEqual(pe.status, "Active")

		prior = frappe.get_all(
			"Procuring Entity Version",
			filters={"procuring_entity": self.entity_code, "version_no": 1},
			fields=["version_state"],
		)[0]
		self.assertEqual(prior.version_state, "Superseded")

	def test_referenced_pe_never_physically_deleted_by_lifecycle(self):
		"""BR-015 — the lifecycle service itself never calls delete_doc; only test
		teardown (owned-fixture cleanup) deletes these rows."""
		self._create()
		activate_pe(self.entity_code, user=self.manager)
		self.assertTrue(frappe.db.exists("Procuring Entity", self.entity_code))

	def test_available_actions_reflect_real_state_not_stale(self):
		"""Live bug: the detail page kept offering a stale action after a real
		transition went through, because available-actions logic didn't look at
		the version's own state."""
		self._create()
		detail = get_procuring_entity(self.entity_code, user=self.manager)
		self.assertEqual(detail["available_actions"], ["Edit draft", "Activate procuring entity"])

		activate_pe(self.entity_code, user=self.manager)
		detail = get_procuring_entity(self.entity_code, user=self.manager)
		self.assertEqual(detail["status"], "Active")
		self.assertNotIn("Activate procuring entity", detail["available_actions"])
		self.assertIn("Propose amendment", detail["available_actions"])

	def test_non_manager_has_no_read_access(self):
		self._create()
		with self.assertRaises(frappe.PermissionError):
			get_procuring_entity(self.entity_code, user=self.other)
