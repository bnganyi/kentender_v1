# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §9.1 / §9.1B — the Planning provider contract the
Requisitions rebuild consumes (REQ plan D1/D6/D8):

- `GetRequisitionEligiblePlanItem` carries the exact pinned identities, the
  County treatment, the verified reservation-rule snapshot, the scope lock and
  the item-specific hold, the separate date boundaries, and exact decimal
  strings (closes PLN FU-V125-03);
- `AuthoriseRequisitionDrawdown` takes every allocation in one call, records
  each row against its own allocation's department, returns the exact
  allocation→drawdown mapping, refuses float input and never commits;
- `ListRequisitionDrawdowns` is the published read revocation uses instead of
  reading `Plan Drawdown Reference` directly;
- terminal dispositions emit `PlanItemCorrectionOutcome.v1` to the registered
  consumer — Planning never imports the Requisitions lifecycle.
"""

from __future__ import annotations

import ast
import inspect
from unittest.mock import patch

import frappe

from kentender_procurement.procurement_planning.errors import ProcurementPlanningError
from kentender_procurement.procurement_planning.services import outcome_event, plan_requisition
from kentender_procurement.procurement_planning.tests import fixtures as fx
from kentender_procurement.procurement_planning.tests.test_plan_requisition import RequisitionCase, key


class TestProjectionCarriesV111Facts(RequisitionCase):
	def test_exact_identities_treatment_rule_hold_scope_and_dates(self):
		accepted, item_id = self.active_item(indicative_amount=1000000)
		read = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)

		item_name = frappe.db.get_value("Annual Plan Item", {"plan_item_id": item_id, "item_state": "Active"}, "name")
		self.assertEqual(read["plan_item_version_id"], item_name)
		self.assertEqual(read["plan_version_id"], read["version_reference"])
		self.assertTrue(read["plan_id"])
		self.assertIn("strategic_objective_id", read)
		self.assertIs(read["county_resident_reservation"], False)

		rule = read["reservation_rule"]
		for field in ("snapshot_id", "version_number", "verification_status", "available", "applies_to_designation"):
			self.assertIn(field, rule)
		self.assertIn("available", read["county_rule"])

		self.assertEqual(read["scope"], {"locked": False, "locked_since": "", "first_authorised_requisition": ""})
		self.assertEqual(read["hold"]["held"], False)
		self.assertEqual(read["hold"]["unresolved_requests"], [])

		self.assertIn("plan_completion_boundary", read)
		self.assertIn("estimated_completion_date", read)

		# The business reference the Requisitions screens show beneath the
		# purchase title (REQ-DES-01), on the single read and the list.
		reference = frappe.db.get_value("Plan Item", item_id, "plan_item_reference")
		self.assertTrue(reference)
		self.assertEqual(read["plan_item_reference"], reference)
		listed = next(r for r in plan_requisition.list_requisition_eligible_plan_items() if r["plan_item_id"] == item_id)
		self.assertEqual(listed["plan_item_reference"], reference)

	def test_money_and_quantity_are_exact_decimal_strings(self):
		_, item_id = self.active_item(indicative_amount=1000000)
		read = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)
		self.assertEqual(read["total_value"], "1000000.00")
		self.assertEqual(read["remaining_value"], "1000000.00")
		self.assertIsInstance(read["total_quantity"], str)
		source = read["sources"][0]
		self.assertEqual(source["allocated_amount"], "1000000.00")
		self.assertEqual(source["remaining_amount"], "1000000.00")
		self.assertIsInstance(source["approved_quantity"], str)
		self.assertIsInstance(source["remaining_quantity"], str)

	def test_an_open_correction_request_is_exposed_as_the_item_hold(self):
		_, item_id = self.active_item()
		frappe.set_user(fx.HOD)
		received = plan_requisition.receive_plan_item_correction_request(
			plan_item_id=item_id, requisition_reference="REQ-V111-HOLD", requisition_version="RQV-V111-HOLD",
			reason="The approved source allocation names the wrong Budget Line for this purchase.", idempotency_key=key(),
		)
		frappe.set_user(fx.HOPF)
		read = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)
		self.assertTrue(read["hold"]["held"])
		self.assertEqual([r["correction_request"] for r in read["hold"]["unresolved_requests"]], [received["correction_request"]])
		self.assertEqual(read["hold"]["unresolved_requests"][0]["status"], "Open")


class TestOneCallDrawdown(RequisitionCase):
	def _authorise(self, item_id, allocations, **extra):
		read = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)
		frappe.set_user(fx.HOPF)
		return plan_requisition.authorise_requisition_drawdown(
			plan_item_id=item_id, requisition_reference=extra.pop("requisition_reference", f"REQ-{key()[:8]}"),
			allocations=allocations, expected_record_version=read["record_version"], idempotency_key=key(), **extra,
		)

	def test_one_call_records_each_row_against_its_own_allocation_department(self):
		_, item_id = self.active_item(indicative_amount=1000000)
		allocation_id = self.allocation_id_of(item_id)
		result = self._authorise(
			item_id,
			[{"plan_source_allocation_id": allocation_id, "quantity": "1", "amount": "400000.00"}],
			requisition_version="RQV-V111-1", correlation_id="CORR-V111-1",
		)
		self.assertEqual([m["plan_source_allocation_id"] for m in result["drawdowns"]], [allocation_id])
		row = frappe.get_doc("Plan Drawdown Reference", result["drawdowns"][0]["drawdown_reference"])
		self.assertEqual(row.requesting_org_unit, fx.OU_ALPHA)
		self.assertEqual(row.requisition_version, "RQV-V111-1")

	def test_a_float_amount_is_refused_without_rounding(self):
		_, item_id = self.active_item(indicative_amount=1000000)
		allocation_id = self.allocation_id_of(item_id)
		with self.assertRaises(ProcurementPlanningError) as caught:
			self._authorise(item_id, [{"plan_source_allocation_id": allocation_id, "quantity": "1", "amount": 400000.0}])
		self.assertEqual(caught.exception.code, "PLN_MONEY_PRECISION_INVALID")
		self.assertEqual(frappe.db.count("Plan Drawdown Reference", {"plan_item_id": item_id}), 0)

	def test_the_owner_call_never_commits(self):
		_, item_id = self.active_item(indicative_amount=1000000)
		allocation_id = self.allocation_id_of(item_id)
		with patch.object(frappe.db, "commit", side_effect=AssertionError("Planning committed inside the caller's transaction")):
			result = self._authorise(item_id, [{"plan_source_allocation_id": allocation_id, "quantity": "1", "amount": "1000.00"}])
		self.assertTrue(result["ok"])

	def test_list_requisition_drawdowns_is_the_published_read_for_reversal(self):
		_, item_id = self.active_item(indicative_amount=1000000)
		allocation_id = self.allocation_id_of(item_id)
		reference = f"REQ-{key()[:8]}"
		self._authorise(item_id, [{"plan_source_allocation_id": allocation_id, "quantity": "1", "amount": "1000.00"}], requisition_reference=reference)
		rows = plan_requisition.list_requisition_drawdowns(requisition_reference=reference)
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0]["plan_source_allocation_id"], allocation_id)
		self.assertEqual(rows[0]["drawdown_state"], "Active")
		self.assertEqual(rows[0]["amount"], "1000.00")
		self.assertIn("record_version", rows[0])

		frappe.set_user(fx.AUTHOR)
		with self.assertRaises(frappe.DoesNotExistError):
			plan_requisition.list_requisition_drawdowns(requisition_reference=reference)


class TestCorrectionOutcomeEvent(RequisitionCase):
	def _request(self, item_id, reference):
		frappe.set_user(fx.HOD)
		received = plan_requisition.receive_plan_item_correction_request(
			plan_item_id=item_id, requisition_reference=reference, requisition_version=f"{reference}-V1",
			reason="The approved source allocation names the wrong Budget Line for this purchase.", idempotency_key=key(),
		)
		frappe.set_user(fx.PLANNER)
		return frappe.get_doc("Plan Item Correction Request", received["correction_request"])

	def test_resolve_emits_the_v1_payload_with_exact_replacement_lineage(self):
		accepted, item_id = self.active_item()
		doc = self._request(item_id, "REQ-V111-RES")
		correcting_version = self.correcting_active_version(accepted["annual_plan"])
		doc.reload()
		with patch.object(outcome_event, "deliver") as deliver:
			plan_requisition.resolve_plan_item_correction_request(
				correction_request=doc.name, correcting_plan_version=correcting_version,
				expected_record_version=doc.record_version, idempotency_key=key(),
			)
		event = deliver.call_args.args[0]
		self.assertEqual(event["schema_version"], 1)
		self.assertTrue(event["event_id"])
		self.assertEqual(event["producer"], "Procurement Planning")
		self.assertGreaterEqual(event["producer_sequence"], 1)
		self.assertEqual(event["correction_request_id"], doc.name)
		self.assertEqual(event["requesting_requisition_id"], "REQ-V111-RES")
		self.assertEqual(event["requesting_requisition_version_id"], "REQ-V111-RES-V1")
		self.assertEqual(event["plan_item_id"], item_id)
		self.assertEqual(event["requested_plan_version_id"], doc.plan_version)
		self.assertEqual(event["requested_plan_item_version_id"], doc.plan_item)
		self.assertEqual(event["outcome"], "Resolved")
		self.assertEqual(event["correcting_plan_version_id"], correcting_version)
		lineage = event["replacement_lineage"]
		self.assertEqual(lineage["plan_item_id"], item_id)
		self.assertTrue(lineage["plan_item_version_id"])
		self.assertTrue(lineage["allocation_ids"])
		self.assertEqual(event["actor"], fx.PLANNER)
		self.assertTrue(event["decision_at"])
		self.assertFalse(event["item_hold_state"])
		self.assertEqual(event["unresolved_request_count"], 0)
		self.assertIn("eligibility_revision", event)

	def test_close_without_change_emits_the_reason_and_no_lineage(self):
		_, item_id = self.active_item()
		doc = self._request(item_id, "REQ-V111-NOC")
		reason = "The approved source allocation and Budget Line are correct. No Planning change is required."
		with patch.object(outcome_event, "deliver") as deliver:
			plan_requisition.close_plan_item_correction_without_change(
				correction_request=doc.name, reason=reason, expected_record_version=doc.record_version, idempotency_key=key(),
			)
		event = deliver.call_args.args[0]
		self.assertEqual(event["outcome"], "Closed without change")
		self.assertEqual(event["reason"], reason)
		self.assertIsNone(event["correcting_plan_version_id"])
		self.assertIsNone(event["replacement_lineage"])

	def test_outcomes_are_ordered_per_request(self):
		_, item_id = self.active_item()
		doc = self._request(item_id, "REQ-V111-SEQ")
		plan_requisition.start_plan_item_correction(correction_request=doc.name, expected_record_version=doc.record_version, idempotency_key=key())
		doc.reload()
		with patch.object(outcome_event, "deliver") as deliver:
			plan_requisition.close_plan_item_correction_without_change(
				correction_request=doc.name, reason="Closed after review: the approved facts are already correct.",
				expected_record_version=doc.record_version, idempotency_key=key(),
			)
		# Start is disposition 1; the terminal close is 2.
		self.assertEqual(deliver.call_args.args[0]["producer_sequence"], 2)

	def test_planning_never_imports_the_requisitions_lifecycle(self):
		tree = ast.parse(inspect.getsource(plan_requisition))
		imported = {
			(node.module or "") for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
		}
		self.assertFalse(any("procurement_requisitions" in module for module in imported), imported)
