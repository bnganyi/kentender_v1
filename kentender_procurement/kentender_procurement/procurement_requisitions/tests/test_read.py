# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §10.1 — the seven read services."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.tests import v16_fixtures as core_fx
from kentender_procurement.procurement_requisitions.services import authorise, draft_commands as cmd, lifecycle, read
from kentender_procurement.procurement_requisitions.tests import fixtures as fx


class RequisitionReadCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()
		# KT-STD-001 §3A.6 — a System-Manager-only user, holding no
		# Requisitions responsibility at all, proves the technical-read path
		# is `is_technical` alone, never a coincidental business grant.
		cls.technical = core_fx.user("req.technical", "Technical Test", roles=("System Manager",))
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

	def _submitted(self) -> tuple[dict, dict]:
		prepared = self._prepared_draft()
		frappe.set_user(fx.HOD)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		submitted = lifecycle.submit_requisition_to_procurement(requisition=prepared["requisition"], expected_record_version=root.record_version, idempotency_key=fx.key())
		return prepared, submitted

	def _authorised(self) -> tuple[dict, dict, dict]:
		prepared, submitted = self._submitted()
		frappe.set_user(fx.HOPF)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		authorised = authorise.authorise_requisition(requisition=prepared["requisition"], task=submitted["task"], expected_record_version=root.record_version, idempotency_key=fx.key())
		return prepared, submitted, authorised


class TestGetRequisitionWorkspace(RequisitionReadCase):
	def test_an_actor_with_no_requisitions_role_at_all_gets_forbidden(self):
		"""`fx.FINANCE_OFFICER` holds only Planning's plan-finance
		responsibility — none of the five Requisitions roles (§8) — unlike
		`fx.OUTSIDER`, which is a Departmental Author on a different OU and
		therefore legitimately holds a Requisitions role, just not one that
		reaches this fixture's own contributing unit."""
		_, item_id = fx.active_item()
		frappe.set_user(fx.FINANCE_OFFICER)
		result = read.get_requisition_workspace()
		self.assertEqual(result["outcome"], "FORBIDDEN")
		self.assertEqual(result["forbidden"]["heading"], "You do not have access to Procurement Requisitions.")
		self.assertIn("Departmental Author, Head of User Department, Head of Procurement Function or Auditor", result["forbidden"]["text"])

	def test_a_true_read_only_role_sees_no_row_for_an_item_it_cannot_prepare(self):
		"""Read-offer parity with `prepare_it_equipment_requisition`'s own
		gate: `fx.AUDITOR` holds no Departmental Author/Head of User
		Department responsibility anywhere, so an item only that role can
		see must never appear as an actionable row — unlike `fx.HOPF` in
		this shared fixture world, who (per the `test_authorise.py`
		segregation-of-duties grant) also happens to hold Head of User
		Department on `OU_ALPHA` and would pass by coincidence."""
		_, item_id = fx.active_item()
		frappe.set_user(fx.AUDITOR)
		result = read.get_requisition_workspace()
		self.assertEqual(result["outcome"], "OK")
		card = result["ready_to_prepare"]
		self.assertNotIn(item_id, [r["plan_item_id"] for r in (card["rows"] if card else [])])

	def test_the_ready_to_prepare_card_shows_one_row_per_eligible_item(self):
		_, item_id = fx.active_item()
		frappe.set_user(fx.HOPF)
		result = read.get_requisition_workspace()
		self.assertEqual(result["outcome"], "OK")
		card = result["ready_to_prepare"]
		# The shared `KENTENDER_TEST` fixture world permanently seeds two of
		# its own eligible Plan Items (`PPI-MOH-2027-001/-002`, outside the
		# `FY_OPEN`/`FY_CLOSED` fiscal years `wipe_planning_rows()` scopes
		# to) alongside whatever this test creates, so the headline count and
		# row count are never asserted as exactly one here — only that this
		# test's own item is present and shaped correctly.
		self.assertRegex(card["headline"], r"^\d+ Plan Items? ready to prepare$")
		row = next(r for r in card["rows"] if r["plan_item_id"] == item_id)
		self.assertIn("Test procurement package", row["supporting"])
		self.assertIn("KES", row["supporting"])
		self.assertEqual(row["route"], ["procurement-requisitions", "new", item_id])

	def test_the_ready_to_prepare_card_is_absent_once_a_requisition_is_open(self):
		prepared = self._prepared_draft()
		item_id = frappe.db.get_value("Procurement Requisition", prepared["requisition"], "plan_item_id")
		frappe.set_user(fx.HOPF)
		result = read.get_requisition_workspace()
		# see the shared-fixture-baseline note above: other items may still
		# be eligible, so only this test's own item's absence is asserted.
		card = result["ready_to_prepare"]
		self.assertNotIn(item_id, [r["plan_item_id"] for r in (card["rows"] if card else [])])

	def test_a_draft_appears_in_your_requisitions_with_a_continue_action(self):
		prepared = self._prepared_draft()
		frappe.set_user(fx.AUTHOR)
		result = read.get_requisition_workspace()
		self.assertEqual(result["outcome"], "OK")
		row = next(r for r in result["requisitions"] if r["requisition"] == prepared["requisition"])
		self.assertEqual(row["status"], "Draft")
		self.assertEqual(row["action_label"], "Continue")
		self.assertEqual(row["route"], ["procurement-requisitions", prepared["requisition"]])
		self.assertEqual(result["count_label"], "1 Requisition")

	def test_an_open_task_reads_as_awaiting_your_approval_for_its_own_holder(self):
		prepared = self._prepared_draft()
		frappe.set_user(fx.AUTHOR)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		sent = lifecycle.send_for_department_approval(requisition=prepared["requisition"], expected_record_version=root.record_version, idempotency_key=fx.key())
		frappe.set_user(fx.HOD)
		result = read.get_requisition_workspace()
		row = next(r for r in result["requisitions"] if r["requisition"] == prepared["requisition"])
		self.assertEqual(row["status"], "Awaiting your approval")
		self.assertEqual(row["action_label"], "Review")
		self.assertEqual(row["route"], ["procurement-requisitions", "department-task", sent["task"]])

	def test_the_same_open_task_reads_as_a_plain_state_for_a_non_holder(self):
		prepared = self._prepared_draft()
		frappe.set_user(fx.AUTHOR)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		lifecycle.send_for_department_approval(requisition=prepared["requisition"], expected_record_version=root.record_version, idempotency_key=fx.key())
		frappe.set_user(fx.AUDITOR)
		result = read.get_requisition_workspace()
		row = next(r for r in result["requisitions"] if r["requisition"] == prepared["requisition"])
		self.assertEqual(row["status"], "Awaiting Department Approval")
		self.assertEqual(row["action_label"], "")


class TestGetEligiblePlanItemDetail(RequisitionReadCase):
	def test_returns_the_projection_and_compatibility(self):
		_, item_id = fx.active_item()
		frappe.set_user(fx.HOPF)
		result = read.get_eligible_plan_item_detail(plan_item_id=item_id)
		self.assertEqual(result["outcome"], "OK")
		self.assertTrue(result["is_compatible"])
		self.assertTrue(result["projection"]["eligible"])
		self.assertIn("Test — Planning Alpha", result["contributing_departments_label"])
		self.assertTrue(result["business_need"])
		self.assertTrue(result["expected_operational_result"])
		self.assertTrue(result["strategic_objective_title"])
		self.assertEqual(result["open_requisition"], "")

	def test_can_prepare_is_read_offer_parity_with_the_command_gate(self):
		_, item_id = fx.active_item()
		frappe.set_user(fx.AUTHOR)
		self.assertTrue(read.get_eligible_plan_item_detail(plan_item_id=item_id)["can_prepare"])
		frappe.set_user(fx.AUDITOR)
		self.assertFalse(read.get_eligible_plan_item_detail(plan_item_id=item_id)["can_prepare"])

	def test_a_dangling_strategic_objective_reference_degrades_to_an_empty_title(self):
		"""A Plan Item's frozen `strategic_objective` snapshot can outlive
		the Strategy Node it once pointed to (confirmed live on a real
		fixture item while browser-verifying the Start screen) — the read
		must degrade to an empty title, never re-echo the id as if it were
		one (the Vue layer's own job is to then omit the "— title" suffix
		entirely rather than render "id — id")."""
		from kentender_procurement.procurement_requisitions.services import read as read_module

		self.assertEqual(read_module._objective_label("DOES-NOT-EXIST"), "")
		self.assertEqual(read_module._objective_label(""), "")


class TestGetRequisitionEditor(RequisitionReadCase):
	def test_outsider_is_masked_as_not_found(self):
		prepared = self._prepared_draft()
		frappe.set_user(fx.OUTSIDER)
		with self.assertRaises(frappe.DoesNotExistError):
			read.get_requisition_editor(requisition=prepared["requisition"])

	def test_author_sees_a_complete_draft_with_zero_blocking_findings(self):
		prepared = self._prepared_draft()
		frappe.set_user(fx.AUTHOR)
		result = read.get_requisition_editor(requisition=prepared["requisition"])
		self.assertEqual(result["outcome"], "OK")
		self.assertEqual(result["validation"]["blocking_count"], 0)
		self.assertTrue(result["permitted_actions"]["can_edit"])
		self.assertTrue(result["permitted_actions"]["can_send_for_department_approval"])
		self.assertTrue(result["business_need"])
		self.assertTrue(result["expected_operational_result"])
		self.assertEqual(result["delivery_location_label"], self.location)
		self.assertTrue(any(loc["name"] == self.location for loc in result["delivery_locations"]))
		self.assertEqual(len(result["drawdown_context"]), 1)
		drawdown_row = result["drawdown_context"][0]
		self.assertEqual(drawdown_row["organisation_unit_label"], "Test — Planning Alpha")
		self.assertTrue(drawdown_row["source_title"])
		self.assertGreater(drawdown_row["remaining_value"], 0)

	def test_a_read_only_site_wide_role_cannot_edit(self):
		"""`fx.AUDITOR` reads unconditionally (Site-wide) but holds no
		Author/HoD responsibility for any Organisation Unit — unlike
		`fx.HOPF` in this shared fixture world, which the segregation-of-
		duties test in `test_authorise.py` deliberately also grants Head
		of User Department on `OU_ALPHA`, so it is not a usable "reads but
		cannot edit" example here."""
		prepared = self._prepared_draft()
		frappe.set_user(fx.AUDITOR)
		result = read.get_requisition_editor(requisition=prepared["requisition"])
		self.assertEqual(result["outcome"], "OK")
		self.assertFalse(result["permitted_actions"]["can_edit"])

	def test_can_request_upstream_correction_is_read_offer_parity_with_the_command_gate(self):
		"""§7.4A step 1: only Head of User Department or Head of Procurement
		Function may request an upstream correction — a plain Departmental
		Author must never be offered the action, even while the Draft is
		otherwise fully editable by them."""
		prepared = self._prepared_draft()
		frappe.set_user(fx.AUTHOR)
		author_result = read.get_requisition_editor(requisition=prepared["requisition"])
		self.assertTrue(author_result["permitted_actions"]["can_edit"])
		self.assertFalse(author_result["permitted_actions"]["can_request_upstream_correction"])
		frappe.set_user(fx.HOD)
		hod_result = read.get_requisition_editor(requisition=prepared["requisition"])
		self.assertTrue(hod_result["permitted_actions"]["can_request_upstream_correction"])


class TestGetDepartmentApprovalTask(RequisitionReadCase):
	def _sent(self) -> tuple[dict, dict]:
		prepared = self._prepared_draft()
		frappe.set_user(fx.AUTHOR)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		sent = lifecycle.send_for_department_approval(requisition=prepared["requisition"], expected_record_version=root.record_version, idempotency_key=fx.key())
		return prepared, sent

	def test_hod_reads_the_locked_version(self):
		prepared, sent = self._sent()
		frappe.set_user(fx.HOD)
		result = read.get_department_approval_task(task=sent["task"])
		self.assertEqual(result["outcome"], "OK")
		self.assertTrue(result["can_act"])
		self.assertEqual(result["requisition"]["requisition"], prepared["requisition"])

	def test_an_unrelated_hod_is_masked_as_not_found(self):
		_prepared, sent = self._sent()
		frappe.set_user(fx.OUTSIDER)
		with self.assertRaises(frappe.DoesNotExistError):
			read.get_department_approval_task(task=sent["task"])

	def test_the_task_carries_drawdown_context_digest_and_who_prepared_it(self):
		prepared, sent = self._sent()
		frappe.set_user(fx.HOD)
		result = read.get_department_approval_task(task=sent["task"])
		self.assertTrue(result["version"]["content_digest"])
		self.assertTrue(result["package"]["content_digest"])
		self.assertEqual(len(result["drawdown_context"]), 1)
		self.assertTrue(result["drawdown_context"][0]["organisation_unit_label"])
		self.assertEqual(result["prepared_by"]["role"], "Departmental Author")
		self.assertTrue(result["prepared_by"]["name"])
		self.assertIn("Head of User Department for", result["deciding_actor"]["role"])
		self.assertTrue(result["deciding_actor"]["name"])

	def test_administrator_reads_the_task_with_every_decision_capability_false(self):
		_prepared, sent = self._sent()
		frappe.set_user("Administrator")
		result = read.get_department_approval_task(task=sent["task"])
		self.assertEqual(result["outcome"], "OK")
		self.assertFalse(result["can_certify"])
		self.assertFalse(result["can_return"])
		self.assertEqual(result["deciding_actor"], {})

	def test_a_system_manager_only_user_reads_the_task_with_every_decision_capability_false(self):
		_prepared, sent = self._sent()
		frappe.set_user(self.technical)
		result = read.get_department_approval_task(task=sent["task"])
		self.assertEqual(result["outcome"], "OK")
		self.assertFalse(result["can_certify"])
		self.assertFalse(result["can_return"])
		self.assertEqual(result["deciding_actor"], {})

	def test_an_auditor_reads_the_task_with_every_decision_capability_false(self):
		_prepared, sent = self._sent()
		frappe.set_user(fx.AUDITOR)
		result = read.get_department_approval_task(task=sent["task"])
		self.assertEqual(result["outcome"], "OK")
		self.assertFalse(result["can_certify"])
		self.assertFalse(result["can_return"])
		self.assertEqual(result["deciding_actor"], {})

	def test_technical_read_never_relaxes_the_decide_command_gate(self):
		prepared, sent = self._sent()
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		for principal in (self.technical, fx.AUDITOR):
			frappe.set_user(principal)
			with self.assertRaises(frappe.DoesNotExistError):
				lifecycle.submit_requisition_to_procurement(
					requisition=prepared["requisition"], task=sent["task"],
					expected_record_version=root.record_version, idempotency_key=fx.key(),
				)
			with self.assertRaises(frappe.DoesNotExistError):
				lifecycle.return_to_department_author(
					task=sent["task"], reason="A reason long enough to pass the control validation check.",
					expected_record_version=root.record_version, idempotency_key=fx.key(),
				)

class TestGetProcurementAuthorisationTask(RequisitionReadCase):
	def test_hopf_reads_the_submission_with_fresh_affordability(self):
		prepared, submitted = self._submitted()
		frappe.set_user(fx.HOPF)
		result = read.get_procurement_authorisation_task(task=submitted["task"])
		self.assertEqual(result["outcome"], "OK")
		self.assertEqual(result["validation"]["blocking_count"], 0)
		self.assertTrue(result["budget_affordability"])
		self.assertTrue(all(a["sufficient"] for a in result["budget_affordability"]))
		# Found live: the card rendered the Budget Line's own internal
		# docname (a hash) instead of its human reference — every row must
		# carry a real, non-hash-looking label.
		for row in result["budget_affordability"]:
			self.assertTrue(row["budget_line_label"])
			self.assertNotEqual(row["budget_line_label"], row["budget_line"])

	def test_compatibility_rows_carry_display_labels_not_raw_identifiers(self):
		prepared, submitted = self._submitted()
		frappe.set_user(fx.HOPF)
		result = read.get_procurement_authorisation_task(task=submitted["task"])
		by_test = {row["test"]: row for row in result["compatibility"]}
		self.assertEqual(by_test["Requirement type"]["actual"], "Straightforward IT equipment")
		self.assertEqual(by_test["Award package"]["actual"], "One")
		self.assertTrue(all(row["ok"] for row in result["compatibility"]))

	def test_the_task_carries_availability_and_policy_justification(self):
		prepared, submitted = self._submitted()
		frappe.set_user(fx.HOPF)
		result = read.get_procurement_authorisation_task(task=submitted["task"])
		self.assertTrue(result["planning_availability"]["eligible"])
		self.assertGreater(result["planning_availability"]["remaining_amount"], 0)
		self.assertTrue(result["objective_label"])
		# This fixture's own `_submitted()` helper submits directly from
		# Draft (REQ-AC-021's HoD-preparing-directly path), which records no
		# `Requisition Decision` — "submitted_by" degrades to empty rather
		# than guessing an actor, never a fabricated name.
		self.assertEqual(result["submitted_by"], {})
		# This fixture's own single-source item has exactly one contributing
		# department, so the lead cannot be changed (§13.11: the action only
		# appears when more than one department contributed).
		self.assertFalse(result["can_change_lead_unit"])

	def test_submitted_by_names_the_hod_who_actually_submitted_from_a_department_task(self):
		prepared = self._prepared_draft()
		frappe.set_user(fx.AUTHOR)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		sent = lifecycle.send_for_department_approval(requisition=prepared["requisition"], expected_record_version=root.record_version, idempotency_key=fx.key())
		frappe.set_user(fx.HOD)
		root.reload()
		submitted = lifecycle.submit_requisition_to_procurement(requisition=prepared["requisition"], task=sent["task"], expected_record_version=root.record_version, idempotency_key=fx.key())
		frappe.set_user(fx.HOPF)
		result = read.get_procurement_authorisation_task(task=submitted["task"])
		self.assertTrue(result["submitted_by"]["name"])
		self.assertTrue(result["submitted_by"]["decided_at"])

	def test_a_departmental_author_is_masked_as_not_found(self):
		prepared, submitted = self._submitted()
		frappe.set_user(fx.AUTHOR)
		with self.assertRaises(frappe.DoesNotExistError):
			read.get_procurement_authorisation_task(task=submitted["task"])

	def test_administrator_reads_the_task_with_every_decision_capability_false(self):
		_prepared, submitted = self._submitted()
		frappe.set_user("Administrator")
		result = read.get_procurement_authorisation_task(task=submitted["task"])
		self.assertEqual(result["outcome"], "OK")
		self.assertFalse(result["can_authorise"])
		self.assertFalse(result["can_return"])
		self.assertFalse(result["can_change_lead_unit"])

	def test_a_system_manager_only_user_reads_the_task_with_every_decision_capability_false(self):
		_prepared, submitted = self._submitted()
		frappe.set_user(self.technical)
		result = read.get_procurement_authorisation_task(task=submitted["task"])
		self.assertEqual(result["outcome"], "OK")
		self.assertFalse(result["can_authorise"])
		self.assertFalse(result["can_return"])
		self.assertFalse(result["can_change_lead_unit"])

	def test_an_auditor_reads_the_task_with_every_decision_capability_false(self):
		_prepared, submitted = self._submitted()
		frappe.set_user(fx.AUDITOR)
		result = read.get_procurement_authorisation_task(task=submitted["task"])
		self.assertEqual(result["outcome"], "OK")
		self.assertFalse(result["can_authorise"])
		self.assertFalse(result["can_return"])
		self.assertFalse(result["can_change_lead_unit"])

	def test_technical_read_never_relaxes_the_decide_command_gate(self):
		prepared, submitted = self._submitted()
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		for principal in (self.technical, fx.AUDITOR):
			frappe.set_user(principal)
			with self.assertRaises(frappe.DoesNotExistError):
				authorise.authorise_requisition(
					requisition=prepared["requisition"], task=submitted["task"],
					expected_record_version=root.record_version, idempotency_key=fx.key(),
				)
			with self.assertRaises(frappe.DoesNotExistError):
				lifecycle.return_requisition_to_department(
					task=submitted["task"], reason="A reason long enough to pass the control validation check.",
					expected_record_version=root.record_version, idempotency_key=fx.key(),
				)


class TestGetAuthorisedRequisitionHandoff(RequisitionReadCase):
	def test_before_authorisation_it_fails(self):
		prepared, submitted = self._submitted()
		frappe.set_user(fx.HOPF)
		from kentender_procurement.procurement_requisitions.services.errors import ProcurementRequisitionsError

		with self.assertRaises(ProcurementRequisitionsError):
			read.get_authorised_requisition_handoff(requisition=prepared["requisition"])

	def test_after_authorisation_it_returns_the_exact_payload(self):
		prepared, submitted, authorised = self._authorised()
		frappe.set_user(fx.HOPF)
		result = read.get_authorised_requisition_handoff(requisition=prepared["requisition"])
		self.assertEqual(result["outcome"], "OK")
		self.assertEqual(result["handoff"], authorised["handoff"])
		self.assertEqual(result["handoff_version"], "1.3")
		self.assertEqual(result["payload"]["requisition_reference"], prepared["requisition_reference"])

	def test_the_view_carries_reservation_and_budget_line_labels_and_who_authorised_it(self):
		prepared, submitted, authorised = self._authorised()
		frappe.set_user(fx.HOPF)
		result = read.get_authorised_requisition_handoff(requisition=prepared["requisition"])
		self.assertTrue(result["drawdown_display"])
		for row in result["drawdown_display"]:
			self.assertTrue(row["reservation_label"])
			self.assertTrue(row["budget_line_label"])
		self.assertEqual(result["package_summary"]["items"], 1)
		self.assertTrue(result["authorised_by"]["name"])
		self.assertEqual(result["authorised_by"]["role"], "Head of Procurement Function")
		self.assertTrue(result["can_revoke"])

	def test_a_read_only_auditor_is_never_offered_revoke(self):
		prepared, submitted, authorised = self._authorised()
		frappe.set_user(fx.AUDITOR)
		result = read.get_authorised_requisition_handoff(requisition=prepared["requisition"])
		self.assertFalse(result["can_revoke"])


class TestGetRequisitionHistory(RequisitionReadCase):
	def test_history_records_every_stage(self):
		"""Goes through the Author -> HoD department-approval path (not the
		HoD-direct shortcut `_submitted()` uses) so a "Submit to Procurement"
		decision actually exists to assert on, alongside the authorisation
		decision — the HoD-direct path records no department decision at
		all, by design (REQ-AC-021: no internal task, nothing to decide)."""
		prepared = self._prepared_draft()
		frappe.set_user(fx.AUTHOR)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		sent = lifecycle.send_for_department_approval(requisition=prepared["requisition"], expected_record_version=root.record_version, idempotency_key=fx.key())
		frappe.set_user(fx.HOD)
		root.reload()
		submitted = lifecycle.submit_requisition_to_procurement(requisition=prepared["requisition"], task=sent["task"], expected_record_version=root.record_version, idempotency_key=fx.key())
		frappe.set_user(fx.HOPF)
		root.reload()
		authorised = authorise.authorise_requisition(requisition=prepared["requisition"], task=submitted["task"], expected_record_version=root.record_version, idempotency_key=fx.key())

		frappe.set_user(fx.AUDITOR)
		result = read.get_requisition_history(requisition=prepared["requisition"])
		self.assertEqual(result["outcome"], "OK")
		self.assertEqual(len(result["versions"]), 1)  # locked in place through every stage; no return happened
		decisions = {d["decision"] for d in result["decisions"]}
		self.assertIn("Submit to Procurement", decisions)
		self.assertIn("Authorise for Tender Preparation", decisions)
		self.assertEqual(len(result["drawdown_lines"]), 1)
		self.assertTrue(result["drawdown_lines"][0]["reservation_id"])
		self.assertTrue(result["handoff"])
