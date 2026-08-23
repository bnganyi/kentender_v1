"""CFG-CHG-002 Phase 4 — API contract layer (§10). Business rules are already
covered by the Phase 1-3 service-layer tests; these focus on what's unique to
the API layer itself: action dispatch, idempotency-key replay (BR-017), and
read-scope filtering (List* contracts). Evidence for CFG-406.
"""

from __future__ import annotations

import json
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime

from kentender_core.api import reference_data_api as api
from kentender_core.services import reference_data_permissions as perm


class TestReferenceDataApi(IntegrationTestCase):
	def setUp(self):
		self.suffix = uuid4().hex[:8]
		self.steward = self._user("steward")
		self.approver = self._user("approver")
		self.outsider = self._user("outsider")
		self.pe_type = self._pe_type()
		self.anchor_pe = frappe.get_all("Procuring Entity", pluck="name", limit=1)[0]
		self.steward_profile = self._profile("STEWARD", [perm.PE_CREATE_DRAFT, perm.PE_PROPOSE_AMENDMENT])
		self.approver_profile = self._profile("APPROVER", [perm.PE_APPROVE_ACTIVATE, perm.PE_SUSPEND, perm.PE_RETIRE])
		self._assign(self.steward, self.steward_profile, self.anchor_pe)
		self._sod_rule(perm.PE_CREATE_DRAFT, perm.PE_APPROVE_ACTIVATE)
		self.entity_code = f"PE-TESTAPI-{self.suffix}".upper()

	def tearDown(self):
		frappe.set_user("Administrator")
		for doctype, filters in (
			("Procuring Entity Version", [["procuring_entity", "=", self.entity_code]]),
			("Procuring Entity", [["name", "=", self.entity_code]]),
			("Audit Event", [["document_name", "=", self.entity_code]]),
			("Reference Data Command Journal", [["document_name", "=", self.entity_code]]),
			("Operational Scope Assignment", [["name", "like", f"%{self.suffix}%"]]),
			("Separation of Duties Rule", [["name", "like", f"%{self.suffix}%"]]),
			("Capability Profile", [["name", "like", f"%{self.suffix}%"]]),
			("PE Type", [["name", "like", f"%{self.suffix}%"]]),
		):
			for name in frappe.get_all(doctype, filters=filters, pluck="name"):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		for user in (self.steward, self.approver, self.outsider):
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

	def _profile(self, label, capabilities):
		doc = frappe.get_doc(
			{
				"doctype": "Capability Profile",
				"profile_id": f"CAP-API-{label}-{self.suffix}",
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
		frappe.get_doc(
			{
				"doctype": "Operational Scope Assignment",
				"assignment_id": f"OSA-API-{uuid4().hex[:10]}-{self.suffix}",
				"user_id": user,
				"capability_profile_id": profile,
				"procuring_entity_id": pe,
				"effective_from": add_days(now_datetime(), -1),
				"status": "Active",
				"assigned_by": "Administrator",
				"assigned_at": now_datetime(),
				"concurrency_token": uuid4().hex,
			}
		).insert(ignore_permissions=True)

	def _sod_rule(self, first, second):
		frappe.get_doc(
			{
				"doctype": "Separation of Duties Rule",
				"rule_id": f"SOD-API-{self.suffix}",
				"rule_name": "Test API create vs approve",
				"first_capability": first,
				"second_capability": second,
				"enforcement_level": "Workflow instance",
				"status": "Active",
				"effective_from": add_days(now_datetime(), -1),
			}
		).insert(ignore_permissions=True)

	def _create_and_scope(self):
		frappe.set_user(self.steward)
		result = api.create_or_revise_pe(
			payload={
				"entity_code": self.entity_code,
				"legal_name": "Test API Entity",
				"display_name": "Test API Entity",
				"pe_type_code": self.pe_type,
			}
		)
		self._assign(self.steward, self.steward_profile, self.entity_code)
		self._assign(self.approver, self.approver_profile, self.entity_code)
		return result

	def test_create_dispatch_and_full_journey_through_api(self):
		self._create_and_scope()
		frappe.set_user(self.steward)
		api.decide_pe_change(self.entity_code, "submit")

		frappe.set_user(self.approver)
		result = api.decide_pe_change(self.entity_code, "approve_activate")
		self.assertEqual(result["status"], "Active")

		detail = api.get_procuring_entity(self.entity_code)
		self.assertEqual(detail["status"], "Active")
		# Approver already spent their capability on approve; suspend is still theirs to use.
		self.assertIn("Suspend", detail["available_actions"])

	def test_unknown_action_rejected(self):
		self._create_and_scope()
		frappe.set_user(self.steward)
		with self.assertRaises(frappe.ValidationError):
			api.decide_pe_change(self.entity_code, "not_a_real_action")

	def test_idempotency_key_replay_runs_command_once(self):
		"""BR-017 — same key returns the original result, no second audit event."""
		self._create_and_scope()
		frappe.set_user(self.steward)
		api.decide_pe_change(self.entity_code, "submit")

		frappe.set_user(self.approver)
		key = f"idem-{self.suffix}"
		first = api.decide_pe_change(self.entity_code, "approve_activate", idempotency_key=key)
		second = api.decide_pe_change(self.entity_code, "approve_activate", idempotency_key=key)
		self.assertEqual(first, second)

		approve_events = frappe.get_all(
			"Audit Event",
			filters={"document_name": self.entity_code, "action": perm.PE_APPROVE_ACTIVATE},
		)
		self.assertEqual(len(approve_events), 1)

		journal_rows = frappe.get_all("Reference Data Command Journal", filters={"idempotency_key": key})
		self.assertEqual(len(journal_rows), 1)

	def test_list_procuring_entities_scoped_by_authorization(self):
		self._create_and_scope()
		frappe.set_user(self.steward)
		listed = api.list_procuring_entities()
		codes = {row["code"] for row in listed["rows"]}
		self.assertIn(self.entity_code, codes)

		frappe.set_user(self.outsider)
		listed_outsider = api.list_procuring_entities()
		codes_outsider = {row["code"] for row in listed_outsider["rows"]}
		self.assertNotIn(self.entity_code, codes_outsider)

	def test_get_procuring_entity_denied_outside_scope(self):
		self._create_and_scope()
		frappe.set_user(self.outsider)
		with self.assertRaises(frappe.PermissionError):
			api.get_procuring_entity(self.entity_code)

	def test_administrator_has_full_read_but_zero_business_actions(self):
		"""AC-019 — System Administrator (Administrator/System Manager in this
		codebase) gets audited technical read-only access: full visibility, but no
		business action or approval by virtue of the role alone. Administrator holds
		no Capability Profile, so evaluate_capability() denies every action even
		though _authorized_pes() grants unrestricted read."""
		self._create_and_scope()
		frappe.set_user(self.steward)
		api.decide_pe_change(self.entity_code, "submit")
		frappe.set_user(self.approver)
		api.decide_pe_change(self.entity_code, "approve_activate")

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
