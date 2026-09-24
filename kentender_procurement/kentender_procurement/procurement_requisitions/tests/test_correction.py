# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §7.4A/§7.4B/§9.1B — Planning correction outcomes and the
explicit follow-ups (REQ19-AC-044/059/064/065/066/067/068/076, REQ-SMK-11)."""

from __future__ import annotations

import frappe

from kentender_procurement.procurement_planning.services import plan_requisition
from kentender_procurement.procurement_requisitions.services import correction, read, records
from kentender_procurement.procurement_requisitions.services.errors import ProcurementRequisitionsError
from kentender_procurement.procurement_requisitions.tests import fixtures as fx
from kentender_procurement.procurement_requisitions.tests.test_draft_commands import RequisitionCase

NO_CHANGE = "The approved source allocation and Budget Line are correct. No Planning change is required."


def _close(request_name: str) -> None:
	frappe.set_user(fx.PLANNER)
	doc = frappe.get_doc("Plan Item Correction Request", request_name)
	plan_requisition.close_plan_item_correction_without_change(correction_request=doc.name, reason=NO_CHANGE, expected_record_version=doc.record_version, idempotency_key=fx.key())


class TestOutcomeConsumer(RequisitionCase):
	def test_closed_without_change_is_recorded_and_the_stopped_version_never_restarts(self):
		_, item_id = fx.active_item()
		requisition, request = fx.stop_for_planning_correction(item_id)
		before = records.load(requisition)[1]
		_close(request)
		outcome = frappe.get_doc("Requisition Correction Outcome", {"correction_request_id": request, "status": "Recorded"})
		self.assertEqual((outcome.outcome, outcome.reason, outcome.requisition), ("Closed without change", NO_CHANGE, requisition))
		after = records.load(requisition)[1]
		self.assertEqual((after.name, after.version_status, after.content_digest), (before.name, "Upstream correction required", before.content_digest))
		view = read.get_requisition_record(requisition=requisition, user=fx.HOD)
		self.assertEqual(view["kind"], "stopped")
		self.assertEqual(view["status_label"], "Planning request closed without change")
		self.assertEqual(view["unchanged_notice"], "The approved Planning facts have not changed. This requisition will not restart.")

	def test_a_resolved_outcome_carries_the_exact_replacement_lineage(self):
		accepted, item_id = fx.active_item()
		requisition, request = fx.stop_for_planning_correction(item_id)
		correcting = fx.correcting_active_version(accepted["annual_plan"])
		frappe.set_user(fx.PLANNER)
		doc = frappe.get_doc("Plan Item Correction Request", request)
		plan_requisition.resolve_plan_item_correction_request(correction_request=doc.name, correcting_plan_version=correcting, expected_record_version=doc.record_version, idempotency_key=fx.key())
		outcome = frappe.get_doc("Requisition Correction Outcome", {"correction_request_id": request, "status": "Recorded"})
		self.assertEqual((outcome.outcome, outcome.correcting_plan_version_id), ("Resolved", correcting))
		self.assertIn("allocation_ids", outcome.replacement_lineage_json)

	def test_a_duplicate_is_a_no_op_and_a_changed_payload_is_quarantined(self):
		_, item_id = fx.active_item()
		requisition, request = fx.stop_for_planning_correction(item_id)
		_close(request)
		recorded = frappe.get_doc("Requisition Correction Outcome", {"correction_request_id": request, "status": "Recorded"})
		facts = plan_requisition.correction_request_facts(correction_request=request)[0]
		event = {
			"event_id": recorded.event_id, "schema_version": 1, "producer": "Procurement Planning", "producer_sequence": recorded.producer_sequence,
			"correction_request_id": request, "requesting_requisition_id": facts["requisition_reference"], "requesting_requisition_version_id": facts["requisition_version"],
			"plan_item_id": item_id, "requested_plan_version_id": facts["plan_version_id"], "requested_plan_item_version_id": facts["plan_item_version_id"],
			"outcome": "Closed without change", "reason": NO_CHANGE, "correcting_plan_version_id": None, "replacement_lineage": None,
			"actor": recorded.decided_by, "decision_at": recorded.decision_at, "item_hold_state": bool(recorded.item_hold_state),
			"unresolved_request_count": recorded.unresolved_request_count, "eligibility_revision": recorded.eligibility_revision,
		}
		self.assertEqual(correction.record_plan_item_correction_outcome(event=event)["action"], "duplicate")
		changed = correction.record_plan_item_correction_outcome(event={**event, "reason": NO_CHANGE + " Changed."})
		self.assertEqual((changed["action"], changed["code"]), ("quarantined", "REQ_CORRECTION_EVENT_INVALID"))
		unknown = correction.record_plan_item_correction_outcome(event={**event, "event_id": "EVT-UNKNOWN", "correction_request_id": "PCR-99999"})
		self.assertEqual(unknown["action"], "quarantined")
		self.assertEqual(frappe.db.count("Requisition Correction Outcome", {"requisition": requisition, "status": "Recorded"}), 1)
		self.assertEqual(records.load(requisition)[1].version_status, "Upstream correction required")

	def test_an_open_request_offers_no_fresh_start(self):
		_, item_id = fx.active_item()
		requisition, request = fx.stop_for_planning_correction(item_id)
		view = read.get_requisition_record(requisition=requisition, user=fx.HOD)
		self.assertEqual((view["status_label"], view["actions"]["start_new_requisition"]), ("Awaiting Planning correction", False))
		frappe.set_user(fx.AUTHOR)
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			correction.prepare_requisition_after_plan_correction(requisition=requisition, idempotency_key=fx.key())
		self.assertCode(ctx, "REQ_CORRECTION_OUTCOME_PENDING")


class TestFreshStart(RequisitionCase):
	def test_after_no_change_an_explicit_fresh_root_links_back_and_copies_no_decision(self):
		_, item_id = fx.active_item()
		requisition, request = fx.stop_for_planning_correction(item_id)
		_close(request)
		frappe.set_user(fx.AUTHOR)
		fresh = correction.prepare_requisition_after_plan_correction(requisition=requisition, idempotency_key=fx.key())
		self.assertEqual(fresh["action"], "created")
		new_root = frappe.get_doc("Procurement Requisition", fresh["requisition"])
		self.assertEqual((new_root.prior_requisition_id, new_root.planning_correction_request_id, new_root.current_state), (requisition, request, "Draft"))
		self.assertEqual(frappe.db.count("Requisition Decision", {"requisition_version": new_root.current_version}), 0)
		self.assertEqual(frappe.db.get_value("Procurement Requisition", requisition, "current_state"), "Upstream correction required")
		again = fx.prepare(item_id, fx.HOD)
		self.assertEqual((again["action"], again["requisition"]), ("existing", fresh["requisition"]))
