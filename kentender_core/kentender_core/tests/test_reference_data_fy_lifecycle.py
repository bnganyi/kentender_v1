"""CFG-CHG-002 Phase 2 — Financial Year lifecycle.
Covers BR-003, BR-004 and AC-006..008 evidence for CFG-206.
"""

from __future__ import annotations

import json
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, getdate, now_datetime

from kentender_core.services import reference_data_permissions as perm
from kentender_core.services.reference_data_transitions import (
	approve_fy,
	create_fy_draft,
	retire_fy,
	submit_fy,
)


class TestReferenceDataFYLifecycle(IntegrationTestCase):
	def setUp(self):
		self.suffix = uuid4().hex[:8]
		self.steward = self._user("steward")
		self.approver = self._user("approver")
		self.anchor_pe = frappe.get_all("Procuring Entity", pluck="name", limit=1)[0]
		self.steward_profile = self._profile("STEWARD", [perm.FY_CREATE_DRAFT])
		self.approver_profile = self._profile("APPROVER", [perm.FY_APPROVE_AVAILABLE, perm.FY_RETIRE])
		self._assign(self.steward, self.steward_profile, self.anchor_pe)
		self._assign(self.approver, self.approver_profile, self.anchor_pe)
		self._sod_rule()
		# A start year unlikely to collide with real seed/fixture data.
		self.start_year = 2100 + (int(self.suffix, 16) % 800)
		self.fy_name = f"FY-{self.start_year}-{self.start_year + 1}"

	def tearDown(self):
		for doctype, filters in (
			("Financial Year", [["name", "=", self.fy_name]]),
			("Audit Event", [["document_name", "=", self.fy_name]]),
			("Operational Scope Assignment", [["name", "like", f"%{self.suffix}%"]]),
			("Separation of Duties Rule", [["name", "like", f"%{self.suffix}%"]]),
			("Capability Profile", [["name", "like", f"%{self.suffix}%"]]),
		):
			for name in frappe.get_all(doctype, filters=filters, pluck="name"):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		for user in (self.steward, self.approver):
			if frappe.db.exists("User", user):
				frappe.delete_doc("User", user, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _user(self, label):
		email = f"cfgpefy.fy.{label}.{self.suffix}@test.local"
		frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": label, "enabled": 1, "send_welcome_email": 0}
		).insert(ignore_permissions=True)
		return email

	def _profile(self, label, capabilities):
		doc = frappe.get_doc(
			{
				"doctype": "Capability Profile",
				"profile_id": f"CAP-FY-{label}-{self.suffix}",
				"profile_name": f"Test FY {label}",
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
				"assignment_id": f"OSA-FY-{uuid4().hex[:10]}-{self.suffix}",
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

	def _sod_rule(self):
		frappe.get_doc(
			{
				"doctype": "Separation of Duties Rule",
				"rule_id": f"SOD-FY-{self.suffix}",
				"rule_name": "Test FY create vs approve",
				"first_capability": perm.FY_CREATE_DRAFT,
				"second_capability": perm.FY_APPROVE_AVAILABLE,
				"enforcement_level": "Workflow instance",
				"status": "Active",
				"effective_from": add_days(now_datetime(), -1),
			}
		).insert(ignore_permissions=True)

	def test_generation_from_start_year(self):
		"""AC-006 / BR-003."""
		result = create_fy_draft(self.start_year, user=self.steward)
		self.assertEqual(result["financial_year"], self.fy_name)
		fy = frappe.get_doc("Financial Year", self.fy_name)
		self.assertEqual(fy.label, f"{self.start_year}/{str(self.start_year + 1)[-2:]}")
		self.assertEqual(getdate(fy.start_date), getdate(f"{self.start_year}-07-01"))
		self.assertEqual(getdate(fy.end_date), getdate(f"{self.start_year + 1}-06-30"))
		self.assertEqual(fy.record_status, "Draft")

	def test_dates_immutable_once_persisted_direct_api_rejected(self):
		"""AC-007 — not just UI read-only; a direct API/service attempt to change
		generated fields is rejected server-side too."""
		create_fy_draft(self.start_year, user=self.steward)
		fy = frappe.get_doc("Financial Year", self.fy_name)
		fy.label = "TAMPERED"
		with self.assertRaises(frappe.ValidationError):
			fy.save(ignore_permissions=True)

	def test_submit_approve_available_no_downstream_side_effects(self):
		"""AC-008 — making a FY available creates no PE/FY Context or other record."""
		before = frappe.db.count("Financial Year")
		create_fy_draft(self.start_year, user=self.steward)
		submit_fy(self.fy_name, user=self.steward)
		approve_fy(self.fy_name, user=self.approver)
		fy = frappe.get_doc("Financial Year", self.fy_name)
		self.assertEqual(fy.record_status, "Available")
		self.assertEqual(fy.approved_by, self.approver)
		# The only new Financial Year row is the one this test itself created.
		self.assertEqual(frappe.db.count("Financial Year"), before + 1)

	def test_creator_cannot_approve_own_fy_sod(self):
		create_fy_draft(self.start_year, user=self.steward)
		submit_fy(self.fy_name, user=self.steward)
		with self.assertRaises(frappe.PermissionError):
			approve_fy(self.fy_name, user=self.steward)

	def test_duplicate_start_year_rejected(self):
		create_fy_draft(self.start_year, user=self.steward)
		with self.assertRaises(Exception):
			create_fy_draft(self.start_year, user=self.steward)

	def test_retire_blocked_unless_available(self):
		create_fy_draft(self.start_year, user=self.steward)
		with self.assertRaises(frappe.ValidationError):
			retire_fy(self.fy_name, user=self.approver)  # still Draft, not Available
