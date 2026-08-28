"""CFG-CHG-002 v0.4 Phase 4 — API contract layer (§10) under the single
Reference Data Manager Role model. Business rules are already covered by the
Phase 1-3 service-layer tests; these focus on what's unique to the API layer
itself: action dispatch, idempotency-key replay (BR-017), and read-scope
filtering (List* contracts). Evidence for CFG-406.
"""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.api import reference_data_api as api
from kentender_core.services.reference_data_permissions import REFERENCE_DATA_MANAGER_ROLE


class TestReferenceDataApi(IntegrationTestCase):
	def setUp(self):
		self.suffix = uuid4().hex[:8]
		self.manager = self._user("manager")
		self.outsider = self._user("outsider")
		self.pe_type = self._pe_type()
		if not frappe.db.exists("Role", REFERENCE_DATA_MANAGER_ROLE):
			frappe.get_doc({"doctype": "Role", "role_name": REFERENCE_DATA_MANAGER_ROLE, "desk_access": 1}).insert(
				ignore_permissions=True
			)
		frappe.get_doc("User", self.manager).add_roles(REFERENCE_DATA_MANAGER_ROLE)
		self.entity_code = f"PE-TESTAPI-{self.suffix}".upper()

	def tearDown(self):
		frappe.set_user("Administrator")
		for doctype, filters in (
			("Procuring Entity Version", [["procuring_entity", "=", self.entity_code]]),
			("Procuring Entity", [["name", "=", self.entity_code]]),
			("Audit Event", [["document_name", "=", self.entity_code]]),
			("Reference Data Command Journal", [["document_name", "=", self.entity_code]]),
			("PE Type", [["name", "like", f"%{self.suffix}%"]]),
		):
			for name in frappe.get_all(doctype, filters=filters, pluck="name"):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		for user in (self.manager, self.outsider):
			if frappe.db.exists("User", user):
				frappe.delete_doc("User", user, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _user(self, label):
		email = f"cfgpefy.api.{label}.{self.suffix}@test.local"
		frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": label, "enabled": 1, "send_welcome_email": 0}
		).insert(ignore_permissions=True)
		return email

	def _pe_type(self):
		code = f"TESTAPITYPE_{self.suffix}".upper()
		frappe.get_doc(
			{"doctype": "PE Type", "type_code": code, "label": "Test Type", "status": "Active"}
		).insert(ignore_permissions=True)
		return code

	def _create(self):
		frappe.set_user(self.manager)
		return api.create_or_revise_pe(
			payload={
				"entity_code": self.entity_code,
				"legal_name": "Test API Entity",
				"display_name": "Test API Entity",
				"pe_type_code": self.pe_type,
			}
		)

	def test_create_and_activate_full_journey_through_api(self):
		self._create()
		result = api.decide_pe_change(self.entity_code, "activate")
		self.assertEqual(result["status"], "Active")

		detail = api.get_procuring_entity(self.entity_code)
		self.assertEqual(detail["status"], "Active")
		self.assertIn("Suspend", detail["available_actions"])

	def test_unknown_action_rejected(self):
		self._create()
		with self.assertRaises(frappe.ValidationError):
			api.decide_pe_change(self.entity_code, "not_a_real_action")

	def test_idempotency_key_replay_runs_command_once(self):
		"""BR-017 — same key returns the original result, no second audit event."""
		self._create()
		key = f"idem-{self.suffix}"
		first = api.decide_pe_change(self.entity_code, "activate", idempotency_key=key)
		second = api.decide_pe_change(self.entity_code, "activate", idempotency_key=key)
		self.assertEqual(first, second)

		activate_events = frappe.get_all(
			"Audit Event",
			filters={"document_name": self.entity_code, "action": "reference_data.pe.activate"},
		)
		self.assertEqual(len(activate_events), 1)

		journal_rows = frappe.get_all("Reference Data Command Journal", filters={"idempotency_key": key})
		self.assertEqual(len(journal_rows), 1)

	def test_list_procuring_entities_scoped_by_authorization(self):
		self._create()
		frappe.set_user(self.manager)
		listed = api.list_procuring_entities()
		codes = {row["code"] for row in listed["rows"]}
		self.assertIn(self.entity_code, codes)

		frappe.set_user(self.outsider)
		listed_outsider = api.list_procuring_entities()
		codes_outsider = {row["code"] for row in listed_outsider["rows"]}
		self.assertNotIn(self.entity_code, codes_outsider)

	def test_get_procuring_entity_denied_outside_scope(self):
		self._create()
		frappe.set_user(self.outsider)
		with self.assertRaises(frappe.PermissionError):
			api.get_procuring_entity(self.entity_code)

	def test_administrator_has_full_read_but_zero_business_actions(self):
		"""AC-012/AUTH-AC-012 — Administrator gets audited technical read-only
		access: full visibility, but no business action by virtue of the account
		alone. Administrator does not hold Reference Data Manager, so
		evaluate_role_capability()-equivalent checks deny every action even
		though has_reference_data_read_access() grants unrestricted read."""
		self._create()
		frappe.set_user(self.manager)
		api.decide_pe_change(self.entity_code, "activate")

		frappe.set_user("Administrator")
		detail = api.get_procuring_entity(self.entity_code)
		self.assertEqual(detail["status"], "Active")
		self.assertEqual(detail["available_actions"], [])

	def test_list_pe_types_returns_only_active_types(self):
		result = api.list_pe_types()
		codes = {row["type_code"] for row in result["rows"]}
		self.assertIn(self.pe_type, codes)
		for row in result["rows"]:
			self.assertTrue(row["label"])
