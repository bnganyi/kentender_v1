# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §10.1 — the `kt_my_work_providers` rows for open
department-approval and procurement-authorisation tasks."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_requisitions.services import draft_commands as cmd, lifecycle, my_work_provider
from kentender_procurement.procurement_requisitions.tests import fixtures as fx


class RequisitionMyWorkCase(IntegrationTestCase):
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

	def _prepared_draft(self) -> dict:
		_, item_id = fx.active_item()
		frappe.set_user(fx.AUTHOR)
		prepared = cmd.prepare_it_equipment_requisition(plan_item_id=item_id, idempotency_key=fx.key())
		self._complete_draft(prepared)
		return prepared


class TestDepartmentApprovalRows(RequisitionMyWorkCase):
	def test_a_sent_requisition_appears_for_its_hod(self):
		prepared = self._prepared_draft()
		frappe.set_user(fx.AUTHOR)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		sent = lifecycle.send_for_department_approval(requisition=prepared["requisition"], expected_record_version=root.record_version, idempotency_key=fx.key())
		rows = my_work_provider.my_work_rows(user=fx.HOD)
		self.assertIn(sent["task"], [r["task_id"] for r in rows["assigned"]])

	def test_it_does_not_appear_for_an_unrelated_hod(self):
		prepared = self._prepared_draft()
		frappe.set_user(fx.AUTHOR)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		sent = lifecycle.send_for_department_approval(requisition=prepared["requisition"], expected_record_version=root.record_version, idempotency_key=fx.key())
		rows = my_work_provider.my_work_rows(user=fx.OUTSIDER)
		self.assertNotIn(sent["task"], [r["task_id"] for r in rows["assigned"]])

	def test_guest_gets_no_rows(self):
		rows = my_work_provider.my_work_rows(user="Guest")
		self.assertEqual(rows, {"assigned": [], "claimable": [], "waiting": []})


class TestProcurementAuthorisationRows(RequisitionMyWorkCase):
	def test_a_submitted_requisition_appears_for_hopf(self):
		prepared = self._prepared_draft()
		frappe.set_user(fx.HOD)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		submitted = lifecycle.submit_requisition_to_procurement(requisition=prepared["requisition"], expected_record_version=root.record_version, idempotency_key=fx.key())
		rows = my_work_provider.my_work_rows(user=fx.HOPF)
		self.assertIn(submitted["task"], [r["task_id"] for r in rows["assigned"]])

	def test_it_does_not_appear_for_a_non_hopf_actor(self):
		prepared = self._prepared_draft()
		frappe.set_user(fx.HOD)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		submitted = lifecycle.submit_requisition_to_procurement(requisition=prepared["requisition"], expected_record_version=root.record_version, idempotency_key=fx.key())
		rows = my_work_provider.my_work_rows(user=fx.AUTHOR)
		self.assertNotIn(submitted["task"], [r["task_id"] for r in rows["assigned"]])
