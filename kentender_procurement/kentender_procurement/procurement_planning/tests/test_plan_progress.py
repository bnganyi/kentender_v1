# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.23 §10.13 / §10.15 — procurement progress (U14) and plan
correction requests (U16) read-model tests.

These pin what the two reads must say, and just as firmly what they must not:
no completion field anywhere until an owning module supplies completion
evidence, no forecast tier at all, no unit ever summed with a different one,
and one effective hold that a single disposition cannot clear.
"""

from __future__ import annotations

import frappe

from kentender_procurement.procurement_planning.services import (
	plan_read,
	plan_requisition,
	progress_read,
	schedule,
)
from kentender_procurement.procurement_planning.tests import fixtures as fx
from kentender_procurement.procurement_planning.tests.test_plan_requisition import RequisitionCase, key


class ProgressCase(RequisitionCase):
	def progress(self, plan_reference: str = "") -> dict:
		frappe.set_user(fx.PLANNER)
		return progress_read.get_procurement_progress(plan_reference=plan_reference)

	def draw(self, item_id: str, *, reference: str, quantity=None, amount=None) -> dict:
		"""An authorised Requisition drawdown — the only thing that counts as
		coverage (§5.4.6)."""
		frappe.set_user(fx.PLANNER)
		read = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)
		allocation = read["sources"][0]
		frappe.set_user(fx.HOPF)
		result = plan_requisition.authorise_requisition_drawdown(
			plan_item_id=item_id, requisition_reference=reference, requesting_org_unit=fx.OU_ALPHA,
			allocations=[{
				"plan_source_allocation_id": allocation["plan_source_allocation_id"],
				"quantity": allocation["remaining_quantity"] if quantity is None else quantity,
				"amount": allocation["remaining_amount"] if amount is None else amount,
			}],
			expected_record_version=read["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.PLANNER)
		return result

	def request_correction(self, item_id: str, *, reference: str, reason: str, accepted: dict | None = None) -> str:
		"""The inbound half, plus the minimal Requisitions root that a later
		disposition calls back into — this module's tests synthesise the
		REQ-shaped record rather than depending on that module's fixtures."""
		if accepted and not frappe.db.exists("Procurement Requisition", {"requisition_reference": reference}):
			root = frappe.get_doc({
				"doctype": "Procurement Requisition", "requisition_reference": reference,
				"plan_id": accepted["annual_plan"], "plan_version_id": accepted["annual_plan_version"],
				"plan_item_id": item_id, "current_state": "Upstream correction required", "record_version": 0,
			}).insert(ignore_permissions=True)
			self.addCleanup(frappe.db.delete, "Procurement Requisition", {"name": root.name})
		frappe.set_user(fx.HOD)
		result = plan_requisition.receive_plan_item_correction_request(
			plan_item_id=item_id, requisition_reference=reference, requisition_version=f"{reference}-V1",
			reason=reason, idempotency_key=key(),
		)
		frappe.set_user(fx.PLANNER)
		return result["correction_request"]


class TestProcurementProgress(ProgressCase):
	def test_a_freshly_activated_plan_shows_planned_scope_and_nothing_started(self):
		accepted, item_id = self.active_item(indicative_amount=1000000)
		read = self.progress(accepted["annual_plan"])

		self.assertEqual(read["outcome"], "OK")
		self.assertEqual(read["plan_reference"], accepted["annual_plan"])
		self.assertEqual(read["status"], "Current plan")
		row = next(r for r in read["items"] if r["plan_item_id"] == item_id)
		self.assertEqual(row["planned_display"], "1 Each / KES 1,000,000")
		self.assertEqual(row["covered_display"], "0 Each / KES 0")
		self.assertEqual(row["not_covered_display"], "1 Each / KES 1,000,000")
		# Nothing has started, and that is stated rather than left blank.
		self.assertEqual(row["procurement_stage"], "Not started")
		self.assertEqual(row["proceedings"], [])
		self.assertIsNone(row["hold"])
		self.assertFalse(row["fully_covered"])

	def test_quantity_and_value_are_always_shown_together(self):
		accepted, item_id = self.active_item(indicative_amount=1000000)
		row = next(r for r in self.progress(accepted["annual_plan"])["items"] if r["plan_item_id"] == item_id)
		for field in ("planned_display", "covered_display", "not_covered_display"):
			with self.subTest(field=field):
				# The unit and the money are both present: a bare "remaining"
				# number would hide which of the two is short (§10.13).
				self.assertIn("Each", row[field])
				self.assertIn("KES", row[field])

	def test_no_completion_or_forecast_field_exists_anywhere_in_the_payload(self):
		accepted, item_id = self.active_item()
		self.draw(item_id, reference="REQ-PROGRESS-COMPLETION")
		serialised = frappe.as_json(self.progress(accepted["annual_plan"]))
		# PLN22-AC-009 / PLN23-CHG-001: not a placeholder, not an empty
		# column — the concepts are absent.
		self.assertNotIn("completion", serialised.lower().replace("delivery_completion", ""))
		self.assertNotIn("forecast", serialised.lower())

	def test_an_authorised_drawdown_is_the_only_thing_that_counts_as_coverage(self):
		accepted, item_id = self.active_item(indicative_amount=1000000)
		self.draw(item_id, reference="REQ-PROGRESS-001", quantity=1, amount=400000)
		row = next(r for r in self.progress(accepted["annual_plan"])["items"] if r["plan_item_id"] == item_id)
		self.assertEqual(row["covered_display"], "1 Each / KES 400,000")
		self.assertEqual(row["not_covered_display"], "0 Each / KES 600,000")

	def test_a_reversed_drawdown_covers_nothing(self):
		accepted, item_id = self.active_item(indicative_amount=1000000)
		drawn = self.draw(item_id, reference="REQ-PROGRESS-002", quantity=1, amount=1000000)
		frappe.set_user(fx.HOPF)
		plan_requisition.reverse_requisition_drawdown(
			drawdown_reference=drawn["drawdown_references"][0]["drawdown_reference"],
			expected_record_version=drawn["drawdown_references"][0]["record_version"],
			idempotency_key=key(),
		)
		row = next(r for r in self.progress(accepted["annual_plan"])["items"] if r["plan_item_id"] == item_id)
		self.assertEqual(row["covered_display"], "0 Each / KES 0")

	def test_a_year_with_no_active_plan_is_a_state_not_an_error(self):
		frappe.set_user(fx.PLANNER)
		read = progress_read.get_procurement_progress(plan_reference="PLN-DOES-NOT-EXIST")
		self.assertEqual(read["outcome"], "NO_ACTIVE_PLAN")


class TestProcurementStageAndOwnerEvidence(ProgressCase):
	def coverage_row(self, item_id: str, *, quantity: float, value: float, publication_state: str = "") -> list[dict]:
		return [{
			"allocation": frappe.db.get_value(
				"Plan Source Allocation",
				{"plan_item": plan_read.resolve_item_doc_name(item_id), "allocation_state": "Active"}, "name",
			),
			"requisition_reference": "REQ-PROGRESS-STAGE", "requisition_version": "REQ-PROGRESS-STAGE-V1",
			"covered_quantity": quantity, "covered_value": value,
			"authorisation_state": "Authorised", "publication_state": publication_state,
		}]

	def test_the_stage_is_the_owning_modules_own_word_and_never_a_completion_claim(self):
		accepted, item_id = self.active_item()
		frappe.set_user("Administrator")
		schedule.record_tender_milestone_actual(
			plan_item_id=item_id, milestone="invitation", actual_date="2102-05-04",
			source_event_id="EVT-PROGRESS-1", producer="tender_preparation",
			proceeding_type="Tender", proceeding_id="TND-PROGRESS-1", producer_sequence=1,
			coverage=self.coverage_row(item_id, quantity=1, value=1000000, publication_state="Published"),
		)
		row = next(r for r in self.progress(accepted["annual_plan"])["items"] if r["plan_item_id"] == item_id)
		self.assertEqual(row["procurement_stage"], "Published")
		self.assertEqual(len(row["proceedings"]), 1)
		self.assertEqual(row["proceedings"][0]["proceeding_id"], "TND-PROGRESS-1")
		self.assertEqual(row["proceedings"][0]["covered_display"], "1 / KES 1,000,000")

	def test_owner_supplied_actuals_appear_with_the_approved_date_and_the_days_between(self):
		accepted, item_id = self.active_item()
		baseline = frappe.db.get_value(
			"Annual Plan Item", plan_read.resolve_item_doc_name(item_id), "baseline_invitation_date"
		)
		frappe.set_user("Administrator")
		schedule.record_tender_milestone_actual(
			plan_item_id=item_id, milestone="invitation", actual_date=frappe.utils.add_days(baseline, 3),
			source_event_id="EVT-PROGRESS-2", producer="tender_preparation",
			proceeding_type="Tender", proceeding_id="TND-PROGRESS-2", producer_sequence=1,
			coverage=self.coverage_row(item_id, quantity=1, value=1000000, publication_state="Published"),
		)
		row = next(r for r in self.progress(accepted["annual_plan"])["items"] if r["plan_item_id"] == item_id)
		milestones = row["proceedings"][0]["milestones"]
		invitation = next(m for m in milestones if m["milestone"] == "invitation")
		self.assertEqual(invitation["label"], "Invitation or advertisement")
		self.assertEqual(invitation["days_after_approved"], "3")
		self.assertTrue(invitation["actual_display"])
		# A supported milestone the owner has not reported says so plainly,
		# once, in its own row — it is not a column of placeholders.
		later = next(m for m in milestones if m["milestone"] == "bid_opening")
		self.assertEqual(later["actual_display"], progress_read.NO_DATE_RECORDED)
		# Elapsed durations need both endpoints, and there is only one actual.
		self.assertEqual(row["proceedings"][0]["durations"], [])

	def test_a_proceeding_no_owner_has_reported_on_carries_no_dated_table_at_all(self):
		accepted, item_id = self.active_item()
		item_name = plan_read.resolve_item_doc_name(item_id)
		frappe.get_doc({
			"doctype": "Proceeding Coverage", "proceeding_type": "Requisition", "proceeding_id": "REQ-NO-DATES",
			"requisition_reference": "REQ-NO-DATES", "plan_item_id": item_id,
			"plan_item": item_id, "plan_version": frappe.db.get_value("Annual Plan Item", item_name, "plan_version"),
			"allocation": frappe.db.get_value(
				"Plan Source Allocation", {"plan_item": item_name, "allocation_state": "Active"}, "name"
			),
			"covered_quantity": 1, "covered_value": 1000000, "authorisation_state": "Authorised",
			"fixture_namespace": fx.NS,
		}).insert(ignore_permissions=True)
		row = next(r for r in self.progress(accepted["annual_plan"])["items"] if r["plan_item_id"] == item_id)
		self.assertEqual(row["proceedings"][0]["milestones"], [])
		self.assertEqual(row["proceedings"][0]["durations"], [])


class TestProgressHold(ProgressCase):
	def test_the_hold_names_the_purchase_it_affects_and_counts_the_open_requests(self):
		accepted, item_id = self.active_item()
		self.request_correction(item_id, reference="REQ-HOLD-1", reason="The authorised warranty period is wrong for this department.")
		self.request_correction(item_id, reference="REQ-HOLD-2", reason="The description overstates the scope that was actually approved.")

		row = next(r for r in self.progress(accepted["annual_plan"])["items"] if r["plan_item_id"] == item_id)
		self.assertEqual(row["hold"]["open_requests"], 2)
		self.assertEqual(row["hold"]["text"], "New requisitions are on hold while these requests remain unresolved.")


class TestPlanCorrectionRequests(ProgressCase):
	def read(self, item_id: str) -> dict:
		frappe.set_user(fx.PLANNER)
		return progress_read.get_plan_correction_requests(plan_item_id=item_id)

	def test_the_required_change_leads_and_the_identifiers_stay_in_the_detail(self):
		accepted, item_id = self.active_item()
		reason = "The authorised warranty period does not match the department's actual need."
		request = self.request_correction(item_id, reference="REQ-COR-1", reason=reason)

		read = self.read(item_id)
		self.assertEqual(read["outcome"], "OK")
		row = read["requests"][0]
		self.assertEqual(row["change_required"], reason)
		self.assertEqual(row["status"], "Needs review")
		self.assertEqual(row["action"], "Review issue")
		# The person, in the capacity they raised it in — no department is
		# inferred from the role.
		self.assertTrue(row["requested_from"].endswith(" · Head of User Department"))
		self.assertIn(frappe.db.get_value("User", fx.HOD, "full_name"), row["requested_from"])
		# PLN22-AC-011 — every identifier is kept, and kept in the detail.
		self.assertEqual(row["detail"]["request"], request)
		self.assertEqual(row["detail"]["requisition_reference"], "REQ-COR-1")
		self.assertTrue(row["detail"]["requested_display"].endswith("EAT"))

	def test_one_hold_covers_every_unresolved_request_and_states_what_is_left(self):
		accepted, item_id = self.active_item()
		first = self.request_correction(item_id, reference="REQ-COR-2", accepted=accepted, reason="The authorised warranty period is wrong for this department.")
		self.request_correction(item_id, reference="REQ-COR-3", accepted=accepted, reason="The description overstates the scope that was actually approved.")

		self.assertEqual(self.read(item_id)["hold"]["remaining"], "2 issues still need attention")

		frappe.set_user(fx.PLANNER)
		doc = frappe.get_doc("Plan Item Correction Request", first)
		plan_requisition.close_plan_item_correction_without_change(
			correction_request=doc.name, reason="The reviewed allocation is correct; no plan change is required.",
			expected_record_version=doc.record_version, idempotency_key=key(),
		)
		# §10.15 U16-MULTIPLE — one disposition never clears another's hold.
		after = self.read(item_id)
		self.assertTrue(after["hold"]["active"])
		self.assertEqual(after["hold"]["remaining"], "1 issue still needs attention")

	def test_the_hold_lifts_only_when_every_request_is_terminal(self):
		accepted, item_id = self.active_item()
		request = self.request_correction(item_id, reference="REQ-COR-4", accepted=accepted, reason="The authorised warranty period is wrong for this department.")
		frappe.set_user(fx.PLANNER)
		doc = frappe.get_doc("Plan Item Correction Request", request)
		plan_requisition.close_plan_item_correction_without_change(
			correction_request=doc.name, reason="The reviewed allocation is correct; no plan change is required.",
			expected_record_version=doc.record_version, idempotency_key=key(),
		)
		read = self.read(item_id)
		self.assertFalse(read["hold"]["active"])
		self.assertEqual(read["requests"][0]["status"], "Closed without a plan change")
		self.assertTrue(read["requests"][0]["terminal"])

	def test_completion_is_offered_only_once_a_later_version_is_active(self):
		accepted, item_id = self.active_item()
		self.request_correction(item_id, reference="REQ-COR-5", reason="The authorised warranty period is wrong for this department.")

		# The version the request was raised against is not a correction of
		# itself, so the control is absent and the reason is stated.
		before = self.read(item_id)
		self.assertFalse(before["requests"][0]["can_record_completed"])
		self.assertTrue(before["requests"][0]["completion_blocked_reason"])
		self.assertTrue(before["requests"][0]["can_start"])

		self.correcting_active_version(accepted["annual_plan"])

		after = self.read(item_id)
		self.assertTrue(after["requests"][0]["can_record_completed"])
		self.assertEqual(after["requests"][0]["completion_blocked_reason"], "")
		self.assertTrue(after["correcting_plan"]["available"])
		self.assertTrue(after["correcting_plan"]["activated_display"].endswith("EAT"))

	def test_the_permanent_scope_restriction_is_a_separate_fact_from_the_hold(self):
		accepted, item_id = self.active_item()
		self.draw(item_id, reference="REQ-COR-LOCK", quantity=1, amount=1000000)
		request = self.request_correction(item_id, reference="REQ-COR-6", accepted=accepted, reason="The authorised warranty period is wrong for this department.")

		held = self.read(item_id)
		self.assertTrue(held["hold"]["active"])
		self.assertTrue(held["scope_lock"]["locked"])
		self.assertIn("separate purchase in a plan update", held["scope_lock"]["text"])

		frappe.set_user(fx.PLANNER)
		doc = frappe.get_doc("Plan Item Correction Request", request)
		plan_requisition.close_plan_item_correction_without_change(
			correction_request=doc.name, reason="The reviewed allocation is correct; no plan change is required.",
			expected_record_version=doc.record_version, idempotency_key=key(),
		)
		# §5.4.6 — the restriction outlives every request outcome.
		released = self.read(item_id)
		self.assertFalse(released["hold"]["active"])
		self.assertTrue(released["scope_lock"]["locked"])

	def test_an_item_nobody_has_asked_about_reads_as_having_no_issues(self):
		accepted, item_id = self.active_item()
		read = self.read(item_id)
		self.assertEqual(read["requests"], [])
		self.assertFalse(read["hold"]["active"])
