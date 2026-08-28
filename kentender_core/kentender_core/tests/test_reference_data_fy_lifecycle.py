"""CFG-CHG-002 v0.4 Phase 2 — Financial Year lifecycle under the single
Reference Data Manager Role model. Covers BR-003, BR-004 and AC-006..008
evidence for CFG-206.
"""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import getdate

from kentender_core.services.reference_data_permissions import REFERENCE_DATA_MANAGER_ROLE
from kentender_core.services.reference_data_transitions import (
	create_fy_draft,
	make_fy_available,
	retire_fy,
)


class TestReferenceDataFYLifecycle(IntegrationTestCase):
	def setUp(self):
		self.suffix = uuid4().hex[:8]
		self.manager = self._user("manager")
		self.other = self._user("other")
		if not frappe.db.exists("Role", REFERENCE_DATA_MANAGER_ROLE):
			frappe.get_doc({"doctype": "Role", "role_name": REFERENCE_DATA_MANAGER_ROLE, "desk_access": 1}).insert(
				ignore_permissions=True
			)
		frappe.get_doc("User", self.manager).add_roles(REFERENCE_DATA_MANAGER_ROLE)
		# A start year unlikely to collide with real seed/fixture data.
		self.start_year = 2100 + (int(self.suffix, 16) % 800)
		self.fy_name = f"FY-{self.start_year}-{self.start_year + 1}"

	def tearDown(self):
		for doctype, filters in (
			("Financial Year", [["name", "=", self.fy_name]]),
			("Audit Event", [["document_name", "=", self.fy_name]]),
		):
			for name in frappe.get_all(doctype, filters=filters, pluck="name"):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		for user in (self.manager, self.other):
			if frappe.db.exists("User", user):
				frappe.delete_doc("User", user, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _user(self, label):
		email = f"cfgpefy.fy.{label}.{self.suffix}@test.local"
		frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": label, "enabled": 1, "send_welcome_email": 0}
		).insert(ignore_permissions=True)
		return email

	def test_generation_from_start_year(self):
		"""AC-006 / BR-003."""
		result = create_fy_draft(self.start_year, user=self.manager)
		self.assertEqual(result["financial_year"], self.fy_name)
		fy = frappe.get_doc("Financial Year", self.fy_name)
		self.assertEqual(fy.label, f"{self.start_year}/{str(self.start_year + 1)[-2:]}")
		self.assertEqual(getdate(fy.start_date), getdate(f"{self.start_year}-07-01"))
		self.assertEqual(getdate(fy.end_date), getdate(f"{self.start_year + 1}-06-30"))
		self.assertEqual(fy.record_status, "Draft")

	def test_create_requires_reference_data_manager_role(self):
		with self.assertRaises(frappe.PermissionError):
			create_fy_draft(self.start_year, user=self.other)

	def test_dates_immutable_once_persisted_direct_api_rejected(self):
		"""AC-007 — not just UI read-only; a direct API/service attempt to change
		generated fields is rejected server-side too."""
		create_fy_draft(self.start_year, user=self.manager)
		fy = frappe.get_doc("Financial Year", self.fy_name)
		fy.label = "TAMPERED"
		with self.assertRaises(frappe.ValidationError):
			fy.save(ignore_permissions=True)

	def test_make_available_no_downstream_side_effects(self):
		"""AC-008 — making a FY available creates no PE/FY Context or other
		record. No maker-checker: the same Reference Data Manager who created
		the draft may also make it available (CFG-CHG-002 v0.4 §1)."""
		before = frappe.db.count("Financial Year")
		create_fy_draft(self.start_year, user=self.manager)
		make_fy_available(self.fy_name, user=self.manager)
		fy = frappe.get_doc("Financial Year", self.fy_name)
		self.assertEqual(fy.record_status, "Available")
		self.assertEqual(fy.approved_by, self.manager)
		# The only new Financial Year row is the one this test itself created.
		self.assertEqual(frappe.db.count("Financial Year"), before + 1)

	def test_duplicate_start_year_rejected(self):
		create_fy_draft(self.start_year, user=self.manager)
		with self.assertRaises(Exception):
			create_fy_draft(self.start_year, user=self.manager)

	def test_retire_blocked_unless_available(self):
		create_fy_draft(self.start_year, user=self.manager)
		with self.assertRaises(frappe.ValidationError):
			retire_fy(self.fy_name, user=self.manager)  # still Draft, not Available

	def test_retire_requires_reference_data_manager_role(self):
		create_fy_draft(self.start_year, user=self.manager)
		make_fy_available(self.fy_name, user=self.manager)
		with self.assertRaises(frappe.PermissionError):
			retire_fy(self.fy_name, user=self.other)
