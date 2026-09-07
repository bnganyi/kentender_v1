# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §8 — the Frappe-framework permission hooks themselves.

Every other test file proves the *service-layer* gates (a command or read
function masks or refuses correctly); this file proves the two Frappe
hooks those services sit beside actually work at the framework layer —
`frappe.get_list`/`frappe.get_all` filtering through
`permission_query_conditions`, and `frappe.has_permission` on one record —
including the multi-OU EXISTS-over-child-table scope this module needed
(a `Procurement Requisition` has no single `organisation_unit` column) and
delegation from a requisition-family child DocType back to its root.
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_requisitions.services import draft_commands as cmd
from kentender_procurement.procurement_requisitions.tests import fixtures as fx


class RequisitionAuthorizationCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()
		cls.addClassCleanup(fx.restore_site)

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_requisition_rows()
		fx.wipe_planning_rows()
		if not frappe.db.exists("Delivery Location", "Test Delivery Location — Requisitions"):
			frappe.get_doc({"doctype": "Delivery Location", "location_name": "Test Delivery Location — Requisitions", "address": "1 Test Street", "status": "Active"}).insert(ignore_permissions=True)
		self.location = "Test Delivery Location — Requisitions"
		self.addCleanup(frappe.set_user, "Administrator")

	def _prepared(self) -> dict:
		_, item_id = fx.active_item()
		frappe.set_user(fx.AUTHOR)
		return cmd.prepare_it_equipment_requisition(plan_item_id=item_id, idempotency_key=fx.key())

	def _complete_draft(self, prepared: dict) -> None:
		frappe.set_user(fx.AUTHOR)
		package_version = frappe.get_doc("IT Equipment Requirement Package Version", prepared["package_version"])
		version = frappe.get_doc("Requisition Version", prepared["requisition_version"])
		cmd.save_requisition_summary(
			requisition=prepared["requisition"], values={"delivery_location": self.location, "latest_delivery_date": "2102-04-30"},
			expected_record_version=version.record_version, idempotency_key=fx.key(),
		)
		cmd.add_requisition_item(
			requisition=prepared["requisition"],
			values={"plan_item_line_id": "DL-001", "equipment_category": "Laptop", "item_name": "Business laptops", "quantity": 1, "intended_use": "Clinical training"},
			expected_record_version=package_version.record_version, idempotency_key=fx.key(),
		)
		fx.confirm_all_proposed_requirements(prepared["requisition"], package_version)
		cmd.add_acceptance_requirement(
			requisition=prepared["requisition"],
			values={"applies_to_scope": "All items", "check_type": "Quantity", "pass_condition": "Delivered quantities equal the authorised schedule", "evidence_type": "Inspection record"},
			expected_record_version=package_version.record_version, idempotency_key=fx.key(),
		)


class TestPermissionQueryConditions(RequisitionAuthorizationCase):
	def test_an_author_of_the_contributing_unit_sees_it_in_get_list(self):
		prepared = self._prepared()
		frappe.set_user(fx.AUTHOR)
		names = frappe.get_list("Procurement Requisition", pluck="name")
		self.assertIn(prepared["requisition"], names)

	def test_an_unrelated_departmental_author_does_not_see_it(self):
		prepared = self._prepared()
		frappe.set_user(fx.OUTSIDER)  # Departmental Author on OU_BETA only
		names = frappe.get_list("Procurement Requisition", pluck="name")
		self.assertNotIn(prepared["requisition"], names)

	def test_a_site_wide_reader_sees_it_unconditionally(self):
		prepared = self._prepared()
		frappe.set_user(fx.AUDITOR)
		names = frappe.get_list("Procurement Requisition", pluck="name")
		self.assertIn(prepared["requisition"], names)

	def test_an_actor_with_no_requisitions_role_sees_nothing(self):
		"""`fx.FINANCE_OFFICER` holds no DocPerm-granting Frappe Role at all
		on this DocType (none of the five §8 business roles) — Frappe's own
		base permission check refuses the query outright with a
		`PermissionError` before our own `permission_query_conditions` hook
		ever runs; it does not fall through to an empty list."""
		prepared = self._prepared()
		frappe.set_user(fx.FINANCE_OFFICER)
		with self.assertRaises(frappe.PermissionError):
			frappe.get_list("Procurement Requisition", pluck="name")

	def test_a_child_doctype_delegates_to_its_root_via_get_list(self):
		"""`Requisition Task` has no Organisation Unit column of its own;
		its own `permission_query_conditions` registration walks back to the
		owning `Procurement Requisition`'s condition (`_CHILD_LINK`)."""
		prepared = self._prepared()
		frappe.set_user(fx.AUTHOR)
		self._complete_draft(prepared)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		from kentender_procurement.procurement_requisitions.services import lifecycle

		sent = lifecycle.send_for_department_approval(requisition=prepared["requisition"], expected_record_version=root.record_version, idempotency_key=fx.key())
		frappe.set_user(fx.HOD)
		task_names = frappe.get_list("Requisition Task", pluck="name")
		self.assertIn(sent["task"], task_names)
		frappe.set_user(fx.OUTSIDER)
		self.assertNotIn(sent["task"], frappe.get_list("Requisition Task", pluck="name"))


class TestHasPermission(RequisitionAuthorizationCase):
	def test_an_author_of_the_contributing_unit_has_read_permission(self):
		prepared = self._prepared()
		self.assertTrue(frappe.has_permission("Procurement Requisition", doc=prepared["requisition"], user=fx.AUTHOR))

	def test_an_unrelated_actor_does_not(self):
		prepared = self._prepared()
		self.assertFalse(frappe.has_permission("Procurement Requisition", doc=prepared["requisition"], user=fx.OUTSIDER))

	def test_administrator_always_has_permission(self):
		prepared = self._prepared()
		self.assertTrue(frappe.has_permission("Procurement Requisition", doc=prepared["requisition"], user="Administrator"))

	def test_a_site_wide_role_has_permission_on_any_record(self):
		prepared = self._prepared()
		self.assertTrue(frappe.has_permission("Procurement Requisition", doc=prepared["requisition"], user=fx.PLANNER))
