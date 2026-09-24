# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §8 — the Frappe-framework permission hooks themselves.

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

from kentender_procurement.procurement_requisitions.services import draft_commands as cmd, lifecycle
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
		self.addCleanup(fx.wipe_requisition_rows)
		self.addCleanup(frappe.set_user, "Administrator")

	def _prepared(self) -> dict:
		_, item_id = fx.active_item()
		frappe.set_user(fx.AUTHOR)
		return cmd.prepare_it_equipment_requisition(plan_item_id=item_id, idempotency_key=fx.key())

	def _complete_draft(self, prepared: dict) -> None:
		fx.fill_request_information(prepared["requisition"])
		fx.add_laptops(prepared["requisition"])
		fx.apply_standard_package(prepared["requisition"])


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
