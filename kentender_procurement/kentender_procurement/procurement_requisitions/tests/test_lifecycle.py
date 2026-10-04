# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §7 — lifecycle transitions against the real world
(REQ19-AC-019/020/021/024/044/045/047/050/073/092, REQ-SMK-02/03/11)."""

from __future__ import annotations

import frappe

from kentender_procurement.procurement_requisitions.services import lifecycle, records
from kentender_procurement.procurement_requisitions.services.errors import ProcurementRequisitionsError
from kentender_procurement.procurement_requisitions.tests import fixtures as fx
from kentender_procurement.procurement_requisitions.tests.test_draft_commands import RequisitionCase

REASON = "Replace the processor wording with a measurable, supplier-neutral minimum."


class TestRouting(RequisitionCase):
	def test_send_locks_the_exact_content_and_routes_to_the_lead_hod(self):
		_, item_id = fx.active_item()
		requisition = fx.complete_draft(item_id)
		sent = fx.send(requisition)
		root, version, package_version = records.load(requisition)
		self.assertEqual(root.current_state, "Awaiting Department Approval")
		self.assertEqual(version.version_status, "Awaiting Department Approval")
		self.assertTrue(version.content_digest)
		self.assertEqual(version.content_digest, package_version.content_digest)
		self.assertTrue(version.basis_snapshot_json)
		task = frappe.get_doc("Requisition Task", sent["task"])
		self.assertEqual((task.business_role, task.organisation_unit), ("Head of User Department", root.lead_org_unit_id))

	def test_a_review_required_package_cannot_be_sent(self):
		_, item_id = fx.active_item()
		requisition = fx.prepare(item_id)["requisition"]
		fx.fill_request_information(requisition)
		fx.add_laptops(requisition)
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			fx.send(requisition)
		self.assertCode(ctx, "REQ_BLOCKING_FINDINGS")
		self.assertIn("PACKAGE_REVIEW_REQUIRED", [f["code"] for f in ctx.exception.detail["findings"]])

	def test_a_contributor_cannot_route(self):
		_, item_id = fx.active_combined_item()
		requisition = fx.complete_draft(item_id)
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			fx.send(requisition, fx.CONTRIBUTOR)
		self.assertCode(ctx, "REQ_RESPONSIBILITY_REQUIRED")

	def test_the_lead_hod_certifies_and_the_certified_lead_is_frozen(self):
		_, item_id = fx.active_item()
		requisition = fx.complete_draft(item_id)
		fx.send(requisition)
		result = fx.submit_as_hod(requisition)
		root, version, _ = records.load(requisition)
		self.assertEqual(root.current_state, "Submitted to Procurement")
		self.assertEqual(version.certified_lead_org_unit_id, root.lead_org_unit_id)
		self.assertEqual(version.submitted_by, fx.HOD)
		self.assertEqual(frappe.get_doc("Requisition Task", result["task"]).business_role, "Head of Procurement Function")

	def test_a_hod_preparing_directly_submits_without_a_self_review_task(self):
		_, item_id = fx.active_item()
		requisition = fx.complete_draft(item_id, fx.HOD)
		frappe.set_user(fx.HOD)
		lifecycle.submit_requisition_to_procurement(requisition=requisition, expected_record_version=fx.root_version(requisition), idempotency_key=fx.key())
		self.assertEqual(frappe.db.count("Requisition Task", {"requisition": requisition, "business_role": "Head of User Department"}), 0)
		self.assertEqual(frappe.db.get_value("Procurement Requisition", requisition, "current_state"), "Submitted to Procurement")


class TestReturns(RequisitionCase):
	def test_a_hod_return_preserves_the_version_and_opens_a_review_required_copy_at_the_section(self):
		_, item_id = fx.active_item()
		requisition = fx.complete_draft(item_id)
		fx.send(requisition)
		reviewed = frappe.db.get_value("Procurement Requisition", requisition, "current_version")
		frappe.set_user(fx.HOD)
		task = fx.open_task(requisition, "Head of User Department")
		result = lifecycle.return_to_department_author(task=task, reason=REASON, affected_section="Technical requirements", expected_record_version=frappe.db.get_value("Requisition Task", task, "record_version"), idempotency_key=fx.key())
		self.assertEqual(frappe.db.get_value("Requisition Version", reviewed, "version_status"), "Returned")
		root, version, package_version = records.load(requisition)
		self.assertEqual(root.current_state, "Draft")
		self.assertEqual(version.based_on_version, reviewed)
		self.assertEqual(package_version.standard_package_review_state, "Review required")
		view = fx.editor(requisition)
		self.assertEqual(view["returned"]["reason"], REASON)
		self.assertEqual((view["returned"]["task"], view["returned"]["section"]), ("requirements", "technical"))
		self.assertEqual(view["header"]["badge"]["label"], "Draft correction")
		self.assertEqual(result["affected_section"], "Technical requirements")

	def test_a_short_reason_is_refused(self):
		_, item_id = fx.active_item()
		requisition = fx.submitted(item_id)
		frappe.set_user(fx.HOPF)
		task = fx.open_task(requisition, "Head of Procurement Function")
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			lifecycle.return_requisition_to_department(task=task, reason="Too short", expected_record_version=0, idempotency_key=fx.key())
		self.assertCode(ctx, "REQ_CONTROL_INVALID")


class TestLeadChange(RequisitionCase):
	def test_hopf_changes_the_submitting_department_as_a_return_and_the_new_lead_must_certify(self):
		_, item_id = fx.active_combined_item()
		requisition = fx.submitted(item_id)
		submitted_version = frappe.db.get_value("Procurement Requisition", requisition, "current_version")
		frappe.set_user(fx.HOPF)
		task = fx.open_task(requisition, "Head of Procurement Function")
		lifecycle.change_requisition_lead_department(task=task, new_lead_org_unit=fx.ou_beta(), reason="Human Resources is the correct submitting department for this combined purchase.", expected_record_version=frappe.db.get_value("Requisition Task", task, "record_version"), idempotency_key=fx.key())
		self.assertEqual(frappe.db.get_value("Requisition Version", submitted_version, "certified_lead_org_unit_id"), fx.ou_alpha())
		root, version, _ = records.load(requisition)
		self.assertEqual((root.current_state, root.lead_org_unit_id, version.lead_routing_directive), ("Draft", fx.ou_beta(), fx.ou_beta()))
		# the directive fixes the lead: Alpha's HoD can no longer certify
		fx.apply_standard_package(requisition)
		frappe.set_user(fx.HOD)
		with self.assertRaises(frappe.DoesNotExistError):
			lifecycle.submit_requisition_to_procurement(requisition=requisition, expected_record_version=fx.root_version(requisition), idempotency_key=fx.key())
		frappe.set_user(fx.HOD_BETA)
		lifecycle.submit_requisition_to_procurement(requisition=requisition, expected_record_version=fx.root_version(requisition), idempotency_key=fx.key())
		self.assertEqual(records.load(requisition)[1].certified_lead_org_unit_id, fx.ou_beta())

	def test_the_new_lead_must_be_a_different_contributor(self):
		_, item_id = fx.active_item()
		requisition = fx.submitted(item_id)
		frappe.set_user(fx.HOPF)
		task = fx.open_task(requisition, "Head of Procurement Function")
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			lifecycle.change_requisition_lead_department(task=task, new_lead_org_unit=fx.ou_beta(), reason="A department that never contributed to this purchase.", expected_record_version=0, idempotency_key=fx.key())
		self.assertCode(ctx, "REQ_DEPARTMENT_NOT_CONTRIBUTING")


class TestStops(RequisitionCase):
	def test_withdraw_needs_a_reason_uses_nothing_and_frees_the_slot(self):
		_, item_id = fx.active_item()
		requisition = fx.submitted(item_id)
		frappe.set_user(fx.HOD)
		lifecycle.withdraw_requisition(requisition=requisition, reason="The department will restate this requirement later.", expected_record_version=fx.root_version(requisition), idempotency_key=fx.key())
		root = frappe.get_doc("Procurement Requisition", requisition)
		self.assertEqual(root.current_state, "Withdrawn")
		self.assertFalse(root.open_slot_key)
		self.assertEqual(frappe.db.count("Requisition Task", {"requisition": requisition, "status": "Open"}), 0)
		self.assertEqual(frappe.db.count("Funding Reservation", {"caller_reference": root.requisition_reference}), 0)

	def test_a_planning_correction_stops_the_version_closes_tasks_and_holds_the_item(self):
		_, item_id = fx.active_item()
		requisition = fx.submitted(item_id)
		frappe.set_user(fx.HOPF)
		result = lifecycle.request_upstream_plan_correction(requisition=requisition, reason="The approved source allocation refers to the wrong Budget Line.", expected_record_version=fx.root_version(requisition), idempotency_key=fx.key())
		root, version, _ = records.load(requisition)
		self.assertEqual((root.current_state, version.version_status), ("Upstream correction required", "Upstream correction required"))
		self.assertEqual(root.planning_correction_request_id, result["correction_request"])
		self.assertEqual(frappe.db.count("Requisition Task", {"requisition": requisition, "status": "Open"}), 0)
		self.assertTrue(frappe.db.get_value("Plan Item", item_id, "authorisation_hold"))

	def test_if_planning_refuses_the_request_nothing_here_changes(self):
		from unittest.mock import patch

		_, item_id = fx.active_item()
		requisition = fx.submitted(item_id)
		frappe.set_user(fx.HOPF)
		with patch("kentender_procurement.procurement_planning.services.plan_requisition.receive_plan_item_correction_request", side_effect=frappe.ValidationError("Planning unavailable")):
			with self.assertRaises(ProcurementRequisitionsError) as ctx:
				lifecycle.request_upstream_plan_correction(requisition=requisition, reason="The approved source allocation refers to the wrong Budget Line.", expected_record_version=fx.root_version(requisition), idempotency_key=fx.key())
		self.assertCode(ctx, "REQ_OWNER_VALIDATION_UNAVAILABLE")
		root, version, _ = records.load(requisition)
		self.assertEqual((root.current_state, version.version_status), ("Submitted to Procurement", "Submitted to Procurement"))
		self.assertEqual(frappe.db.count("Requisition Task", {"requisition": requisition, "status": "Open"}), 1)
