# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §7 — lifecycle transition tests."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_requisitions.services import draft_commands as cmd
from kentender_procurement.procurement_requisitions.services import lifecycle
from kentender_procurement.procurement_requisitions.services.errors import ProcurementRequisitionsError
from kentender_procurement.procurement_requisitions.tests import fixtures as fx


class RequisitionLifecycleCase(IntegrationTestCase):
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
		self.addCleanup(frappe.set_user, "Administrator")

	def _complete_draft(self, prepared: dict) -> None:
		"""Fills the Draft to zero Blocking findings (single-item, single
		drawdown-line fixture) so `_lock` can succeed."""
		frappe.set_user(fx.AUTHOR)
		package_version = frappe.get_doc("IT Equipment Requirement Package Version", prepared["package_version"])
		version = frappe.get_doc("Requisition Version", prepared["requisition_version"])
		cmd.save_requisition_summary(
			requisition=prepared["requisition"],
			values={"delivery_location": self.location, "latest_delivery_date": "2102-04-30"},
			expected_record_version=version.record_version, idempotency_key=fx.key(),
		)
		added_item = cmd.add_requisition_item(
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

	def setUp_location(self):
		if not frappe.db.exists("Delivery Location", "Test Delivery Location — Requisitions"):
			frappe.get_doc({"doctype": "Delivery Location", "location_name": "Test Delivery Location — Requisitions", "address": "1 Test Street", "status": "Active"}).insert(ignore_permissions=True)
		self.location = "Test Delivery Location — Requisitions"

	def prepare_complete_draft(self):
		self.setUp_location()
		_, item_id = fx.active_item()
		frappe.set_user(fx.AUTHOR)
		prepared = cmd.prepare_it_equipment_requisition(plan_item_id=item_id, idempotency_key=fx.key())
		self._complete_draft(prepared)
		return prepared


class TestSendAndDepartmentDecision(RequisitionLifecycleCase):
	def test_send_for_department_approval_locks_and_creates_a_hod_task(self):
		prepared = self.prepare_complete_draft()
		frappe.set_user(fx.AUTHOR)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		result = lifecycle.send_for_department_approval(requisition=prepared["requisition"], expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertEqual(result["action"], "sent")
		root.reload()
		self.assertEqual(root.current_state, "Awaiting Department Approval")
		version = frappe.get_doc("Requisition Version", result["requisition_version"])
		self.assertEqual(version.version_status, "Awaiting Department Approval")
		self.assertTrue(version.content_digest)
		task = frappe.get_doc("Requisition Task", result["task"])
		self.assertEqual(task.business_role, "Head of User Department")
		self.assertEqual(task.status, "Open")

	def test_send_blocked_by_incomplete_draft(self):
		self.setUp_location()
		_, item_id = fx.active_item()
		frappe.set_user(fx.AUTHOR)
		prepared = cmd.prepare_it_equipment_requisition(plan_item_id=item_id, idempotency_key=fx.key())
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			lifecycle.send_for_department_approval(requisition=prepared["requisition"], expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertEqual(ctx.exception.code, "REQ_BLOCKING_FINDINGS")

	def test_hod_return_preserves_reviewed_version_and_creates_draft_successor(self):
		prepared = self.prepare_complete_draft()
		frappe.set_user(fx.AUTHOR)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		sent = lifecycle.send_for_department_approval(requisition=prepared["requisition"], expected_record_version=root.record_version, idempotency_key=fx.key())
		frappe.set_user(fx.HOD)
		task = frappe.get_doc("Requisition Task", sent["task"])
		result = lifecycle.return_to_department_author(task=task.name, reason="The intended use text needs more operational detail.", expected_record_version=task.record_version, idempotency_key=fx.key())
		self.assertEqual(result["action"], "returned")
		reviewed = frappe.get_doc("Requisition Version", sent["requisition_version"])
		self.assertEqual(reviewed.version_status, "Returned")
		new_draft = frappe.get_doc("Requisition Version", result["requisition_version"])
		self.assertEqual(new_draft.version_status, "Draft")
		self.assertEqual(new_draft.based_on_version, reviewed.name)
		root.reload()
		self.assertEqual(root.current_state, "Draft")
		self.assertEqual(root.current_version, new_draft.name)

	def test_hod_submit_to_procurement_creates_hopf_task(self):
		prepared = self.prepare_complete_draft()
		frappe.set_user(fx.AUTHOR)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		sent = lifecycle.send_for_department_approval(requisition=prepared["requisition"], expected_record_version=root.record_version, idempotency_key=fx.key())
		frappe.set_user(fx.HOD)
		root.reload()
		result = lifecycle.submit_requisition_to_procurement(requisition=prepared["requisition"], expected_record_version=root.record_version, task=sent["task"], idempotency_key=fx.key())
		self.assertEqual(result["action"], "submitted")
		root.reload()
		self.assertEqual(root.current_state, "Submitted to Procurement")
		hopf_task = frappe.get_doc("Requisition Task", result["task"])
		self.assertEqual(hopf_task.business_role, "Head of Procurement Function")


class TestHodDirectSubmit(RequisitionLifecycleCase):
	def test_hod_may_prepare_and_submit_directly_without_a_department_task(self):
		self.setUp_location()
		_, item_id = fx.active_item()
		frappe.set_user(fx.HOD)
		prepared = cmd.prepare_it_equipment_requisition(plan_item_id=item_id, idempotency_key=fx.key())
		self._complete_draft(prepared)
		frappe.set_user(fx.HOD)  # _complete_draft always acts as fx.AUTHOR internally
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		result = lifecycle.submit_requisition_to_procurement(requisition=prepared["requisition"], expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertEqual(result["action"], "submitted")
		root.reload()
		self.assertEqual(root.current_state, "Submitted to Procurement")
		self.assertEqual(frappe.db.count("Requisition Task", {"requisition": root.name, "business_role": "Head of User Department"}), 0)


class TestProcurementReturnAndWithdraw(RequisitionLifecycleCase):
	def _submitted(self):
		prepared = self.prepare_complete_draft()
		frappe.set_user(fx.AUTHOR)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		sent = lifecycle.send_for_department_approval(requisition=prepared["requisition"], expected_record_version=root.record_version, idempotency_key=fx.key())
		frappe.set_user(fx.HOD)
		root.reload()
		submitted = lifecycle.submit_requisition_to_procurement(requisition=prepared["requisition"], expected_record_version=root.record_version, task=sent["task"], idempotency_key=fx.key())
		return prepared, submitted

	def test_hopf_return_preserves_submitted_version_and_creates_draft_successor(self):
		prepared, submitted = self._submitted()
		frappe.set_user(fx.HOPF)
		task = frappe.get_doc("Requisition Task", submitted["task"])
		result = lifecycle.return_requisition_to_department(task=task.name, reason="The warranty period does not match the fixture's stated need.", expected_record_version=task.record_version, idempotency_key=fx.key())
		self.assertEqual(result["action"], "returned")
		reviewed = frappe.get_doc("Requisition Version", submitted["requisition_version"])
		self.assertEqual(reviewed.version_status, "Returned")

	def test_hopf_may_change_lead_department_while_submitted(self):
		prepared, submitted = self._submitted()
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		other_unit = next(iter(frappe.get_all("Requisition Contributing Unit", filters={"parent": root.name}, pluck="organisation_unit")))
		frappe.set_user(fx.HOPF)
		result = lifecycle.change_lead_organisation_unit(
			requisition=prepared["requisition"], new_lead_org_unit=other_unit,
			reason="Reassessed after review — this department bears the larger share.",
			expected_record_version=root.record_version, idempotency_key=fx.key(),
		)
		self.assertEqual(result["action"], "lead_unit_changed")
		root.reload()
		self.assertEqual(root.lead_org_unit, other_unit)

	def test_a_non_contributing_unit_is_refused_as_lead(self):
		prepared, submitted = self._submitted()
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		frappe.set_user(fx.HOPF)
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			lifecycle.change_lead_organisation_unit(
				requisition=prepared["requisition"], new_lead_org_unit="OU-NOT-CONTRIBUTING",
				reason="Attempted change to an unrelated department.",
				expected_record_version=root.record_version, idempotency_key=fx.key(),
			)
		self.assertEqual(ctx.exception.code, "REQ_DEPARTMENT_NOT_CONTRIBUTING")

	def test_hod_may_withdraw_before_authorisation(self):
		prepared, submitted = self._submitted()
		frappe.set_user(fx.HOD)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		result = lifecycle.withdraw_requisition(requisition=prepared["requisition"], expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertEqual(result["action"], "withdrawn")
		root.reload()
		self.assertEqual(root.current_state, "Withdrawn")
		self.assertEqual(frappe.db.count("Requisition Task", {"requisition": root.name, "status": "Open"}), 0)


class TestUpstreamCorrection(RequisitionLifecycleCase):
	def test_hod_may_request_upstream_correction_and_planning_receives_it(self):
		prepared = self.prepare_complete_draft()
		frappe.set_user(fx.HOD)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		result = lifecycle.request_upstream_plan_correction(
			requisition=prepared["requisition"], reason="The Plan Item's warranty period does not match the department's actual need.",
			expected_record_version=root.record_version, idempotency_key=fx.key(),
		)
		self.assertEqual(result["action"], "upstream_correction_requested")
		root.reload()
		self.assertEqual(root.current_state, "Upstream correction required")
		self.assertTrue(frappe.db.exists("Plan Item Correction Request", result["correction_request"]))
		stopped_version = frappe.get_doc("Requisition Version", prepared["requisition_version"])
		self.assertEqual(stopped_version.version_status, "Upstream correction required")
