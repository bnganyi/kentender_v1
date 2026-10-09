# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.31 §5.2 / §5.5.2 / §7.1 / §8.2 — publication confirmation,
activation, withdrawal and successors: the Planner's `ConfirmPlanPublication`
(see `test_plan_publication_confirmation` for its own contract),
BeginPlanUpdate / RemovePlanItemInSuccessor / CancelPlanUpdate, owner-supplied
actuals and the NeedPlanningUsageChanged.v1 publisher proved against a genuine
accepted Need (PLN-AC-030/031/032/077/081/086/108/118/119/120/123..130).

Until v1.31 the Accounting Officer recorded Treasury evidence and a post-commit
worker published through a sandbox adapter; that arrangement and its tests are
retired (PLN-CHG-001 v1.31 §5.5.2.0)."""

from __future__ import annotations

import json
from unittest.mock import patch
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.errors import ProcurementPlanningError
from kentender_procurement.procurement_planning.services import (
	budget_gateway,
	dpp_lifecycle,
	dpp_validation,
	needs_intake,
	plan_finance,
	plan_governance,
	plan_json,
	plan_publication,
	plan_read,
	plan_workbench,
	publication_confirmation,
	publication_pipeline,
	schedule,
	treasury,
)
from kentender_procurement.procurement_planning.tests import fixtures as fx


def key() -> str:
	return uuid4().hex


class PublicationCase(IntegrationTestCase):
	MOCK_NEEDS = True

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()
		cls.addClassCleanup(fx.restore_site)

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_planning_rows()
		self.addCleanup(frappe.set_user, "Administrator")
		if self.MOCK_NEEDS:
			needs_patch = patch.object(needs_intake, "current_accepted_sources", return_value=[])
			needs_patch.start()
			self.addCleanup(needs_patch.stop)
		eligible_patch = patch.object(budget_gateway, "eligible_line_ids", return_value={fx.BUDGET_LINE, fx.BUDGET_LINE_2})
		eligible_patch.start()
		self.addCleanup(eligible_patch.stop)

	def complete(self, item_id: str, **overrides) -> None:
		frappe.set_user(fx.PLANNER)
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.save_plan_item(
			plan_item=item_id, values=fx.item_values(**overrides), expected_record_version=item["record_version"], idempotency_key=key(),
		)

	def confirm_funding(self, plan_reference: str) -> None:
		frappe.set_user(fx.PLANNER)
		plan = plan_read.get_annual_plan(plan_reference=plan_reference)
		requested = plan_finance.request_plan_funding_confirmation(
			plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		task = frappe.get_doc("Plan Finance Task", requested["task"])
		frappe.set_user(fx.FINANCE_OFFICER)
		plan_finance.confirm_plan_funding(task=task.name, task_token=task.task_token, idempotency_key=key())
		frappe.set_user(fx.PLANNER)

	def _accept_direct(self, specs: list[dict], *, unit: str = "") -> tuple[dict, list[str], str]:
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			organisation_unit=unit or fx.OU_ALPHA, fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)
		version = opened["record_version"]
		added = []
		for spec in specs:
			result = dpp_lifecycle.save_direct_requirement(
				dpp_version=opened["current_version"], values=fx.direct_values(**spec), expected_record_version=version, idempotency_key=key(),
			)
			version = result["record_version"]
			added.append(result)
		frappe.set_user(fx.HOD)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True, expected_record_version=version, idempotency_key=key(),
		)
		task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
		frappe.set_user(fx.PLANNER)
		accepted = dpp_validation.accept_departmental_plan(
			task=task.name, classifications={a["entry_id"]: "Goods" for a in added}, task_token=task.task_token, idempotency_key=key(),
		)
		entries = [
			frappe.db.get_value("Departmental Plan Entry", {"dpp_version": opened["current_version"], "entry_id": a["entry_id"]}, "name")
			for a in added
		]
		return accepted, entries, opened["departmental_plan"]

	def confirmed_item(self, *, indicative_amount: float = 1000000) -> tuple[dict, str]:
		accepted, entries, _ = self._accept_direct([{"indicative_amount": indicative_amount}])
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		formed = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"], dpp_entries=entries, mode="each",
			expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		item_id = formed["created_items"][0]
		self.complete(item_id)
		self.confirm_funding(accepted["annual_plan"])
		return accepted, item_id

	def two_confirmed_items(self) -> tuple[dict, str, str]:
		accepted, entries, _ = self._accept_direct([
			{"title": "Item A requirement", "budget_line": fx.BUDGET_LINE},
			{"title": "Item B requirement", "budget_line": fx.BUDGET_LINE_2},
		])
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		formed = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"], dpp_entries=entries, mode="each",
			expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		by_title = {plan_read.get_plan_item(plan_item_id=i)["header"]["title"]: i for i in formed["created_items"]}
		item_a, item_b = by_title["Item A requirement"], by_title["Item B requirement"]
		self.complete(item_a, title="Item A package")
		self.complete(item_b, title="Item B package")
		self.confirm_funding(accepted["annual_plan"])
		return accepted, item_a, item_b

	def approve(self, plan_reference: str) -> dict:
		"""Sign, adopt and approve — stops at `Approved — publication pending`
		(§5.5.2: approval only commits; nothing is sent yet)."""
		frappe.set_user(fx.PLANNER)
		plan = plan_read.get_annual_plan(plan_reference=plan_reference)
		frappe.set_user(fx.HOPF)  # v1.18 §6.2: the Head of Procurement Function signs and submits
		submitted = plan_governance.submit_consolidated_plan(
			plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		adopted = plan_governance.adopt_and_submit_plan(task=ao_task.name, task_token=ao_task.task_token, idempotency_key=key())
		statutory_task = frappe.get_doc("Plan Governance Task", adopted["statutory_task"])
		frappe.set_user(fx.STATUTORY)
		result = plan_governance.approve_annual_plan(task=statutory_task.name, task_token=statutory_task.task_token, idempotency_key=key())
		frappe.set_user(fx.PLANNER)
		return result

	def publication_values(self, **overrides) -> dict:
		today = str(frappe.utils.getdate(frappe.utils.nowdate()))
		return {
			"treasury_submitted_on": today, "treasury_reference": "MOH/APP/2101/001", "website_published_on": today,
			"public_plan_url": "https://www.moh.example.test/procurement/annual-procurement-plan", "confirmation_acknowledged": 1, **overrides,
		}

	def confirm_publication(self, plan_version: str, **overrides) -> dict:
		"""The Planner confirms Treasury submission and website publication (PLN-CHG-001 v1.31 §5.5.2.2)."""
		frappe.set_user(fx.PLANNER)
		return publication_confirmation.confirm_plan_publication(
			plan_version=plan_version, values=self.publication_values(**overrides),
			expected_record_version=int(frappe.db.get_value("Annual Plan Version", plan_version, "record_version") or 0), idempotency_key=key(),
		)

	def activate(self, plan_reference: str) -> dict:
		"""Approve, then the Planner confirms publication, which runs the
		existing activation checks (no worker, no adapter, no RQ). Returns the
		approval's identifiers with the confirmation's result."""
		approved = self.approve(plan_reference)
		confirmed = self.confirm_publication(approved["plan_version"])
		frappe.set_user(fx.PLANNER)
		return {**approved, **confirmed}


class TestApprovedPlanPayload(PublicationCase):
	"""PLN-CHG-001 v1.31 §5.5.2 — approval commits only the exact content and its
	document identity; the Planner's confirmation then activates the plan."""

	def test_approval_commits_only_then_the_planners_confirmation_activates_with_the_v1_18_payload(self):
		reservations_before = frappe.db.count("Funding Reservation")
		accepted, item_id = self.confirmed_item()
		approved = self.approve(accepted["annual_plan"])
		version_name = frappe.db.get_value("Plan Publication", approved["publication"], "plan_version")
		# §5.5.2: commit-only — nothing sent, content locked, not yet Active
		self.assertEqual(frappe.db.get_value("Annual Plan Version", version_name, "version_status"), "Approved — publication pending")
		self.assertFalse(frappe.db.get_value("Annual Plan", accepted["annual_plan"], "active_version"))
		publication = frappe.get_doc("Plan Publication", approved["publication"])
		self.assertEqual(publication.publication_state, "Pending")
		self.assertEqual(publication.schema_version, plan_json.SCHEMA_VERSION)

		confirmed = self.confirm_publication(version_name)
		self.assertEqual(confirmed["activation"], "activated")
		self.assertEqual(frappe.db.count("Funding Reservation"), reservations_before)  # PLN-AC-081

		frappe.set_user(fx.PLANNER)
		read = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertIsNotNone(read["active_view"])
		self.assertEqual(read["header"]["badge"], "Active")
		self.assertFalse(read["mutable"])
		self.assertEqual(read["active_view"]["summary"]["plan_items"], 1)
		# PLN-CHG-001 v1.23 — no schedule-health projection survives the
		# forecast deferral (PLN23-AC-001).
		self.assertNotIn("schedule_health_display", read["active_view"]["summary"])
		row = read["active_view"]["items"][0]
		self.assertEqual(row["plan_item_id"], item_id)
		# PLN-CHG-001 v1.23 — the Active row carries planned scope and remaining
		# allowance, not a per-milestone forecast grid (PLN23-AC-001).
		self.assertNotIn("schedule", row)
		self.assertEqual(row["requisition_availability_display"], "1 each · KES 1,000,000")

		publication.reload()
		self.assertEqual(publication.publication_state, "Confirmed")
		self.assertEqual(publication.public_location, self.publication_values()["public_plan_url"])
		snapshot = frappe.get_doc("Approved Plan Snapshot", publication.snapshot)
		content = json.loads(snapshot.content)
		self.assertEqual(content["schemaVersion"], plan_json.SCHEMA_VERSION)
		self.assertEqual(len(content["items"]), 1)
		item = content["items"][0]
		self.assertEqual(item["procurementMethod"], "Open Tender")
		self.assertEqual(item["planHorizon"], "Single year")
		self.assertEqual(item["lottingIndicator"], "Single lot")
		self.assertEqual(item["reservationCategory"], "None")  # the explicit catalogue value, not a blank field
		self.assertNotIn("ocid", json.dumps(content))
		payload = plan_json.build_public_payload(snapshot)
		self.assertEqual(payload["items"][0]["planItemId"], item_id)
		self.assertNotIn("ocid", json.dumps(payload))
		self.assertIsNone(payload["items"][0].get("actual"))  # no operational actual/forecast overwrite in the public payload

		task_read = plan_read.get_publication_task(publication=publication.name)
		self.assertEqual(task_read["publication_state"], "Confirmed")
		self.assertTrue(task_read["confirmation"]["treasury_reference"])

	def test_a_hold_blocks_confirmation_and_a_correction_request_hold_is_ao_only(self):
		accepted, item_id = self.confirmed_item()
		approved = self.approve(accepted["annual_plan"])
		version_name = frappe.db.get_value("Plan Publication", approved["publication"], "plan_version")
		frappe.set_user(fx.PLANNER)
		with self.assertRaises(frappe.DoesNotExistError):
			publication_pipeline.hold_plan_publication(plan_version=version_name, reason="A material defect was found.", hold_kind="Accounting Officer correction request", idempotency_key=key())
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		held = publication_pipeline.hold_plan_publication(plan_version=version_name, reason="A material defect was found.", hold_kind="Accounting Officer correction request", idempotency_key=key())
		self.assertTrue(held["hold"])
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.confirm_publication(version_name)
		self.assertEqual(caught.exception.code, "PLN_PUBLICATION_HELD")
		# a hold is not a withdrawal of approval
		self.assertEqual(frappe.db.get_value("Annual Plan Version", version_name, "version_status"), "Approved — publication pending")


class TestWithdrawal(PublicationCase):
	"""PLN-CHG-001 v1.31 §5.5.2.3 / §7.2 — the withdrawal-for-correction recovery
	route for an approved plan with no Current confirmation (PLN18-209)."""

	def test_withdrawal_requires_unconfirmed_content(self):
		accepted, item_id = self.confirmed_item()
		approved = self.activate(accepted["annual_plan"])
		version_name = frappe.db.get_value("Plan Publication", approved["publication"], "plan_version")
		self.assertEqual(approved["activation"], "activated")
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		with self.assertRaises(ProcurementPlanningError) as caught:
			treasury.request_plan_withdrawal(plan_version=version_name, reason="The package needs correction before publication.", idempotency_key=key())
		self.assertEqual(caught.exception.code, "PLN_WITHDRAWAL_NOT_PERMITTED")

	def test_an_unconfirmed_plan_can_be_withdrawn_for_correction_by_the_statutory_authority(self):
		accepted, item_id = self.confirmed_item()
		approved = self.approve(accepted["annual_plan"])
		version_name = frappe.db.get_value("Plan Publication", approved["publication"], "plan_version")
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		requested = treasury.request_plan_withdrawal(plan_version=version_name, reason="A material defect was found in the approved package.", idempotency_key=key())
		self.assertTrue(requested["hold"])
		self.assertTrue(requested["task"])
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.confirm_publication(version_name)
		self.assertEqual(caught.exception.code, "PLN_PUBLICATION_HELD")

		frappe.set_user(fx.STATUTORY)
		task = frappe.get_doc("Plan Governance Task", requested["task"])
		withdrawn = treasury.withdraw_approved_plan_for_correction(task=task.name, task_token=task.task_token, idempotency_key=key())
		self.assertEqual(withdrawn["action"], "withdrawn_for_correction")
		self.assertEqual(frappe.db.get_value("Annual Plan Version", version_name, "version_status"), "Withdrawn for correction")
		self.assertEqual(frappe.db.get_value("Plan Publication Hold", {"plan_version": version_name}, "hold_state"), "Released")
		correction = frappe.get_doc("Annual Plan Version", withdrawn["correction_version"])
		self.assertEqual(correction.version_status, "Draft")
		self.assertEqual(correction.correction_of_plan_version, version_name)
		self.assertEqual(frappe.db.count("Annual Plan Item", {"plan_version": correction.name}), 1)
		self.assertEqual(json.loads(correction.source_cohort), json.loads(frappe.db.get_value("Annual Plan Version", version_name, "source_cohort")))
		self.assertEqual(frappe.db.get_value("Annual Plan", accepted["annual_plan"], "open_successor_version"), correction.name)
		# repeating the withdrawal now finds no valid open request
		with self.assertRaises(ProcurementPlanningError) as caught:
			treasury.withdraw_approved_plan_for_correction(task=task.name, task_token=task.task_token, idempotency_key=key())
		self.assertEqual(caught.exception.code, "PLN_REVIEW_STALE")


class TestWithdrawalReadModel(PublicationCase):
	"""§10.12 U13-WITHDRAWAL-* — whose action it is, at each point."""

	def unconfirmed_publication(self):
		"""An approved plan nobody has confirmed — the one state the
		withdrawal route exists for."""
		accepted, item_id = self.confirmed_item()
		approved = self.approve(accepted["annual_plan"])
		version_name = frappe.db.get_value("Plan Publication", approved["publication"], "plan_version")
		return accepted, version_name, approved["publication"]

	def test_only_the_accounting_officer_is_offered_the_request(self):
		accepted, version_name, publication = self.unconfirmed_publication()

		frappe.set_user(fx.ACCOUNTING_OFFICER)
		ao_read = plan_read.get_publication_task(publication=publication)
		self.assertTrue(ao_read["can_request_withdrawal"])
		self.assertFalse(ao_read["can_decide_withdrawal"])
		# The fact the whole route depends on, stated rather than assumed.
		self.assertEqual(ao_read["publication_confirmation"], "Confirmed not published")

		frappe.set_user(fx.STATUTORY)
		statutory_read = plan_read.get_publication_task(publication=publication)
		self.assertFalse(statutory_read["can_request_withdrawal"])
		# Nothing has been requested yet, so there is nothing to decide.
		self.assertFalse(statutory_read["can_decide_withdrawal"])

	def test_an_open_request_moves_the_action_to_the_statutory_authority(self):
		accepted, version_name, publication = self.unconfirmed_publication()
		reason = "A material defect was found in the approved package."
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		treasury.request_plan_withdrawal(plan_version=version_name, reason=reason, idempotency_key=key())

		ao_read = plan_read.get_publication_task(publication=publication)
		# The AO has asked; there is nothing more for them to do but wait.
		self.assertFalse(ao_read["can_request_withdrawal"])
		self.assertEqual(ao_read["withdrawal_request"]["reason"], reason)
		self.assertTrue(ao_read["withdrawal_request"]["requested_by_name"])
		self.assertTrue(ao_read["withdrawal_request"]["requested_display"].endswith("EAT"))

		frappe.set_user(fx.STATUTORY)
		statutory_read = plan_read.get_publication_task(publication=publication)
		self.assertTrue(statutory_read["can_decide_withdrawal"])
		self.assertTrue(statutory_read["withdrawal_task"])
		self.assertTrue(statutory_read["withdrawal_task_token"])


class TestHeldCorrectionAndReassessment(PublicationCase):
	def active(self) -> tuple[dict, str]:
		accepted, item_id = self.confirmed_item()
		self.activate(accepted["annual_plan"])
		return accepted, item_id

	def test_a_held_version_takes_one_linked_correction_and_is_never_treated_as_active(self):
		"""v1.18 §5.5.2.3 / §7.2 `BeginHeldPlanCorrection` (PLN18-208; the held state itself is produced in 2f)."""
		accepted, item_id = self.active()
		version_name = accepted["annual_plan_version"]
		plan_name = frappe.db.get_value("Annual Plan Version", version_name, "annual_plan")
		# simulate the 2f outcome: publication acknowledged, activation checks failed
		frappe.db.set_value("Annual Plan Version", version_name, {"version_status": "Published — activation held", "activated_at": None}, update_modified=False)
		frappe.db.set_value("Annual Plan", plan_name, {"active_version": None, "open_successor_version": None}, update_modified=False)
		frappe.set_user(fx.PLANNER)
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_governance.begin_held_plan_correction(plan_version=version_name, reason="short", idempotency_key=key())
		self.assertEqual(caught.exception.code, "PLN_ENTRY_INCOMPLETE")
		started = plan_governance.begin_held_plan_correction(plan_version=version_name, reason="Activation checks found the reservation basis missing; correct and resubmit.", idempotency_key=key())
		self.assertEqual(started["action"], "held_correction_started")
		self.assertEqual(started["active_predecessor"], "")
		correction = frappe.get_doc("Annual Plan Version", started["correction_version"])
		self.assertEqual(correction.correction_of_plan_version, version_name)
		self.assertIsNone(correction.based_on_version)
		self.assertEqual(correction.version_status, "Draft")
		self.assertTrue(json.loads(correction.source_cohort))
		self.assertEqual(frappe.db.count("Annual Plan Item", {"plan_version": correction.name}), 1)
		self.assertEqual(frappe.db.get_value("Annual Plan Version", version_name, "version_status"), "Published — activation held")
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_governance.begin_held_plan_correction(plan_version=version_name, reason="Activation checks found the reservation basis missing; correct and resubmit again.", idempotency_key=key())
		self.assertEqual(caught.exception.code, "PLN_STALE_WRITE")

	def test_active_reassessment_appends_new_finance_evidence_without_touching_the_baseline(self):
		"""v1.18 §5.3.4 — a changed approved amount on an unchanged Active Plan is reassessed, never re-approved."""
		accepted, item_id = self.active()
		version_name = accepted["annual_plan_version"]
		before_evidence = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])["funding_evidence"]
		self.assertTrue(before_evidence["current"])
		self.assertTrue(before_evidence["at_approval"])
		line_version = frappe.db.get_value("Procurement Budget Line Version", {"budget_line": fx.BUDGET_LINE, "budget_version": ("in", frappe.get_all("Procurement Budget Version", filters={"status": "Active"}, pluck="name"))}, "name")
		previous = frappe.db.get_value("Procurement Budget Line Version", line_version, "approved_amount")
		frappe.db.set_value("Procurement Budget Line Version", line_version, "approved_amount", 95_000_000, update_modified=False)
		self.addCleanup(frappe.db.set_value, "Procurement Budget Line Version", line_version, "approved_amount", previous, update_modified=False)
		frappe.set_user(fx.PLANNER)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertFalse(plan["funding_evidence"]["current"])
		self.assertEqual(plan["version_status"], "Active")
		requested = plan_finance.request_plan_funding_confirmation(plan_version=version_name, expected_record_version=plan["record_version"], idempotency_key=key())
		self.assertEqual(requested["action"], "reassessment_requested")
		self.assertTrue(requested["reassessment"])
		task = frappe.get_doc("Plan Finance Task", requested["task"])
		frappe.set_user(fx.FINANCE_OFFICER)
		self.assertTrue(plan_read.get_finance_task(task=task.name)["is_reassessment"])
		plan_finance.confirm_plan_funding(task=task.name, task_token=task.task_token, idempotency_key=key())
		version = frappe.get_doc("Annual Plan Version", version_name)
		self.assertEqual(version.version_status, "Active")
		self.assertEqual(version.funding_state, "Confirmed")
		after = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])["funding_evidence"]
		self.assertTrue(after["current"])
		self.assertEqual(after["at_approval"]["decision"], before_evidence["at_approval"]["decision"])
		self.assertNotEqual(after["current_confirmation"]["decision"], after["at_approval"]["decision"])
		self.assertEqual(frappe.db.count("Plan Finance Decision", {"decision": "Confirm plan funding", "task": ("in", frappe.get_all("Plan Finance Task", filters={"plan_version": version_name}, pluck="name"))}), 2)

class TestOwnerSuppliedActuals(PublicationCase):
	"""PLN-CHG-001 v1.23 §5.5.1A — actual milestone dates come only from the
	module that owns the real event, are stored per procurement proceeding, and
	never collapse onto the Plan Item. The forecast facility this used to sit
	beside is deferred in full (PLN23-CHG-001)."""

	def active(self) -> tuple[dict, str]:
		accepted, item_id = self.confirmed_item()
		self.activate(accepted["annual_plan"])
		return accepted, item_id

	def test_an_actual_is_recorded_per_proceeding_and_is_never_typed_by_a_user(self):
		accepted, item_id = self.active()
		schedule.record_tender_milestone_actual(
			plan_item_id=item_id, milestone="invitation", actual_date="2101-09-03",
			source_event_id="TPR-TEST-1", producer="tender_preparation",
		)
		events = frappe.get_all(
			"Milestone Actual Event",
			filters={"plan_item_id": item_id, "milestone": "invitation"},
			fields=["actual_date", "event_id"],
		)
		self.assertEqual(len(events), 1)
		self.assertEqual(str(events[0].actual_date), "2101-09-03")

		# A replayed event id changes nothing (PLN18-AC-099).
		again = schedule.record_tender_milestone_actual(
			plan_item_id=item_id, milestone="invitation", actual_date="2101-09-03",
			source_event_id="TPR-TEST-1", producer="tender_preparation",
		)
		self.assertTrue(again.get("idempotent"))
		self.assertEqual(frappe.db.count("Milestone Actual Event", {"plan_item_id": item_id, "milestone": "invitation"}), 1)

		# A different date under a new event id is a conflicting fact for the
		# same proceeding, not a silent overwrite.
		with self.assertRaises(ProcurementPlanningError) as guarded:
			schedule.record_tender_milestone_actual(
				plan_item_id=item_id, milestone="invitation", actual_date="2101-09-04",
				source_event_id="TPR-TEST-2", producer="tender_preparation",
			)
		self.assertEqual(guarded.exception.code, "PLN_ACTUAL_NOT_WRITABLE")

		# An unauthenticated event with no producer event id is refused.
		with self.assertRaises(ProcurementPlanningError) as guarded:
			schedule.record_tender_milestone_actual(
				plan_item_id=item_id, milestone="invitation", actual_date="2101-09-04",
				source_event_id="", producer="tender_preparation",
			)
		self.assertEqual(guarded.exception.code, "PLN_ACTUAL_NOT_WRITABLE")

	def test_no_planner_save_path_accepts_an_actual_or_a_forecast_date(self):
		"""PLN18-AC-120 and PLN23-AC-001 together: the Planner can type neither."""
		accepted, item_id = self.confirmed_item()
		frappe.set_user(fx.PLANNER)
		for field, expected in (
			("actual_invitation_date", "PLN_ACTUAL_NOT_WRITABLE"),
			("forecast_invitation_date", "PLN_SCHEDULE_INVALID"),
		):
			with self.assertRaises(ProcurementPlanningError) as caught:
				plan_workbench.save_plan_item(
					plan_item=item_id, values={field: "2101-09-03"},
					expected_record_version=0, idempotency_key=key(),
				)
			self.assertEqual(caught.exception.code, expected)

	def test_the_forecast_facility_has_no_runtime_entry_point(self):
		"""PLN23-AC-001 — no route, endpoint, scheduler job or notice producer."""
		from kentender_procurement.procurement_planning import api
		from kentender_procurement.procurement_planning.services import notifications

		for withdrawn in ("preview_forecast_cascade", "confirm_forecast_cascade"):
			self.assertFalse(hasattr(api, withdrawn), f"{withdrawn} is exposed again")
		for withdrawn in ("check_approaching_milestones", "seed_forecast_from_baseline", "schedule_health"):
			self.assertFalse(hasattr(schedule, withdrawn), f"schedule.{withdrawn} is back")
		for withdrawn in ("upsert_milestone_notice", "clear_milestone_notice", "notify_approaching_milestone"):
			self.assertFalse(hasattr(notifications, withdrawn), f"notifications.{withdrawn} is back")
		self.assertFalse(frappe.db.exists("DocType", "Plan Item Forecast Revision"))
		self.assertFalse(frappe.db.exists("DocType", "Milestone Notice"))

		from kentender_procurement import hooks

		scheduled = [job for jobs in getattr(hooks, "scheduler_events", {}).values() for job in jobs]
		self.assertEqual([j for j in scheduled if "schedule" in j or "milestone" in j], [])


class TestBeginAndCancelPlanUpdate(PublicationCase):
	def test_begin_plan_update_creates_a_draft_successor_copying_the_item_and_is_idempotent(self):
		accepted, item_id = self.confirmed_item()
		self.activate(accepted["annual_plan"])
		plan_name = frappe.db.get_value("Annual Plan", {"plan_reference": accepted["annual_plan"]})
		active_version = frappe.db.get_value("Annual Plan", plan_name, "active_version")

		frappe.set_user(fx.PLANNER)
		begun = plan_publication.begin_plan_update(plan_reference=accepted["annual_plan"], idempotency_key=key())
		self.assertEqual(begun["action"], "created")
		successor = begun["successor_version"]
		self.assertEqual(frappe.db.get_value("Annual Plan Version", successor, "based_on_version"), active_version)
		self.assertEqual(frappe.db.get_value("Annual Plan Version", successor, "funding_state"), "Not requested")
		copies = frappe.get_all("Annual Plan Item", filters={"plan_item_id": item_id}, fields=["name", "plan_version", "item_state", "baseline_invitation_date"])
		self.assertEqual(len(copies), 2)
		by_version = {c.plan_version: c for c in copies}
		self.assertEqual(by_version[active_version].item_state, "Active")
		self.assertEqual(by_version[successor].item_state, "Draft")
		self.assertEqual(str(by_version[successor].baseline_invitation_date), "2101-09-01")

		read = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertTrue(read["mutable"])
		self.assertTrue(read["is_successor"])
		item_read = plan_read.get_plan_item(plan_item_id=item_id)
		self.assertTrue(item_read["mutable"])
		self.assertEqual(frappe.db.get_value("Annual Plan Item", plan_read.resolve_item_doc_name(item_id), "plan_version"), successor)

		again = plan_publication.begin_plan_update(plan_reference=accepted["annual_plan"], idempotency_key=key())
		self.assertEqual(again["action"], "reused")
		self.assertEqual(frappe.db.count("Annual Plan Version", {"annual_plan": plan_name}), 2)

	def test_cancel_plan_update_leaves_the_active_version_and_budget_untouched(self):
		accepted, item_id = self.confirmed_item()
		self.activate(accepted["annual_plan"])
		plan_name = frappe.db.get_value("Annual Plan", {"plan_reference": accepted["annual_plan"]})
		reservations = frappe.db.count("Funding Reservation")
		frappe.set_user(fx.PLANNER)
		begun = plan_publication.begin_plan_update(plan_reference=accepted["annual_plan"], idempotency_key=key())
		successor = begun["successor_version"]
		open_read = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		cancelled = plan_publication.cancel_plan_update(
			plan_reference=accepted["annual_plan"], expected_record_version=open_read["record_version"], idempotency_key=key(),
		)
		self.assertEqual(cancelled["action"], "cancelled")
		self.assertEqual(frappe.db.get_value("Annual Plan Version", successor, "version_status"), "Cancelled")
		self.assertFalse(frappe.db.get_value("Annual Plan", plan_name, "open_successor_version"))
		self.assertEqual(frappe.db.count("Funding Reservation"), reservations)  # PLN-AC-086
		self.assertEqual(frappe.db.get_value("Annual Plan Item", {"plan_item_id": item_id, "item_state": "Active"}, "item_state"), "Active")
		reopened = plan_publication.begin_plan_update(plan_reference=accepted["annual_plan"], idempotency_key=key())
		self.assertEqual(reopened["action"], "created")


class TestRemoveItemInSuccessorAndReActivation(PublicationCase):
	def test_removal_supersedes_the_predecessor_item_on_activation(self):
		accepted, item_a_id, item_b_id = self.two_confirmed_items()
		self.activate(accepted["annual_plan"])
		plan_name = frappe.db.get_value("Annual Plan", {"plan_reference": accepted["annual_plan"]})
		predecessor_version = frappe.db.get_value("Annual Plan", plan_name, "active_version")
		predecessor_item_a = frappe.db.get_value("Annual Plan Item", {"plan_item_id": item_a_id, "plan_version": predecessor_version}, "name")

		frappe.set_user(fx.PLANNER)
		begun = plan_publication.begin_plan_update(plan_reference=accepted["annual_plan"], idempotency_key=key())
		successor = begun["successor_version"]
		item_a_read = plan_read.get_plan_item(plan_item_id=item_a_id)
		removed = plan_publication.remove_plan_item_in_successor(
			plan_item=item_a_id, expected_record_version=item_a_read["record_version"], idempotency_key=key(),
		)
		self.assertEqual(removed["action"], "removed")
		successor_item_a = frappe.db.get_value("Annual Plan Item", {"plan_item_id": item_a_id, "plan_version": successor}, "name")
		self.assertEqual(frappe.db.get_value("Annual Plan Item", successor_item_a, "item_state"), "Removed in successor")
		self.assertEqual(frappe.db.get_value("Annual Plan Item", predecessor_item_a, "item_state"), "Active")

		self.confirm_funding(accepted["annual_plan"])
		self.activate(accepted["annual_plan"])
		self.assertEqual(frappe.db.get_value("Annual Plan Item", predecessor_item_a, "item_state"), "Superseded")
		self.assertEqual(frappe.db.get_value("Plan Source Allocation", {"plan_item": successor_item_a}, "allocation_state"), "Removed in successor")
		self.assertEqual(frappe.db.get_value("Annual Plan Version", predecessor_version, "version_status"), "Superseded")
		self.assertEqual(frappe.db.get_value("Annual Plan Version", successor, "version_status"), "Active")
		read = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertEqual(read["active_view"]["summary"]["plan_items"], 1)
		self.assertEqual(read["active_view"]["items"][0]["plan_item_id"], item_b_id)


class RealNeedsCase(PublicationCase):
	"""A Planning case whose accepted Needs are genuine, created through
	NDS's own real command chain. No tests of its own."""

	MOCK_NEEDS = False

	def setUp(self):
		super().setUp()
		from kentender_core.services import site_configuration

		self._needs_open = frappe.get_all("Fiscal Year", filters={site_configuration.FLAG_OPEN: 1}, pluck="name")
		if not frappe.db.get_value("Fiscal Year", fx.FY_OPEN, site_configuration.FLAG_OPEN):
			site_configuration.open_needs_submission(fiscal_year=fx.FY_OPEN, reason="Planning test: Need-origin fixtures")
		self.addCleanup(self._restore_needs_flag)
		self._wipe_need_fixture()
		# This bench commits test writes: take the genuine Needs, and the plans
		# built on them, away again afterwards too (cleanups run last-first),
		# or the next module's department starts with a stranger's Need in it.
		self.addCleanup(self._wipe_need_fixture)
		self.addCleanup(fx.wipe_planning_rows)

	def _restore_needs_flag(self):
		from kentender_core.services import site_configuration

		frappe.set_user("Administrator")
		for year in self._needs_open:
			if year != fx.FY_OPEN and not frappe.db.get_value("Fiscal Year", year, site_configuration.FLAG_OPEN):
				site_configuration.open_needs_submission(fiscal_year=year, reason="test cleanup: restore the previously open year")

	def _wipe_need_fixture(self) -> None:
		needs = frappe.get_all("Departmental Need", filters={"organisation_unit": fx.OU_ALPHA, "name": ("!=", fx.NEED)}, pluck="name")
		versions = frappe.get_all("Departmental Need Revision", filters={"departmental_need": ("in", needs or ("",))}, pluck="name")
		frappe.db.delete("Need Planning Usage Projection", {"name": ("in", versions or ("",))})
		frappe.db.delete("Need Planning Disposition Projection", {"departmental_need": ("in", needs or ("",))})
		frappe.db.delete("Need Planning Intake Projection", {"departmental_need": ("in", needs or ("",))})
		frappe.db.delete("Departmental Need Decision", {"departmental_need": ("in", needs or ("",))})
		frappe.db.delete("Departmental Need Review Task", {"departmental_need": ("in", needs or ("",))})
		frappe.db.delete("Departmental Need Event", {"departmental_need": ("in", needs or ("",))})
		frappe.db.delete("Departmental Need Revision", {"name": ("in", versions or ("",))})
		frappe.db.delete("Departmental Need", {"name": ("in", needs or ("",))})

	def _accepted_need(self, title: str) -> str:
		from kentender_procurement.departmental_needs.services import lifecycle as need_lifecycle

		frappe.set_user(fx.AUTHOR)
		created = need_lifecycle.create_need(
			organisation_unit=fx.OU_ALPHA, financial_year=fx.FY_OPEN, title=title,
			description="A fixture Need for the usage-publishing round trip.",
			expected_operational_result="Planning can source a real accepted Need end to end.",
			indicative_quantity=5, unit=fx.UNIT, estimated_total_cost=1000000, required_by_date="2102-01-01", idempotency_key=key(),
		)
		submitted = need_lifecycle.submit_need(need=created["need"], expected_version=created["record_version"], idempotency_key=key())
		frappe.set_user(fx.HOD)
		token = frappe.db.get_value("Departmental Need Review Task", submitted["task"], "decision_token")
		need_lifecycle.review_need(
			need=created["need"], decision="accept", task=submitted["task"], expected_version=submitted["record_version"],
			decision_token=token, idempotency_key=key(),
		)
		return created["need"]

	def _dpp_with_needs(self, needs: list[str]) -> tuple[dict, dict[str, str]]:
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			organisation_unit=fx.OU_ALPHA, fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)
		entries = {}
		for need in needs:
			dpp_entry = frappe.db.get_value("Departmental Plan Entry", {"dpp_version": opened["current_version"], "need": need}, "name")
			self.assertTrue(dpp_entry, "the accepted Need was not projected into the Draft DPP Version")
			entries[need] = dpp_entry
		return opened, entries


class TestNeedOriginUsagePublishing(RealNeedsCase):
	"""§7.1's outbound event proved against a genuine accepted Need created
	through NDS's own real command chain, so the Need-origin DPP intake, the
	not-proceeding outcome and the activation publisher round-trip for real."""

	def test_activation_publishes_fully_included_then_removal_publishes_not_included(self):
		need = self._accepted_need("Need-origin fixture requirement")
		accepted_version = frappe.db.get_value("Departmental Need", need, "current_accepted_revision")
		opened, entries = self._dpp_with_needs([need])
		entry_id = frappe.db.get_value("Departmental Plan Entry", entries[need], "entry_id")
		funded = dpp_lifecycle.save_need_funding(
			dpp_version=opened["current_version"], entry_id=entry_id, budget_line=fx.BUDGET_LINE, indicative_amount=500000,
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.HOD)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True, expected_record_version=funded["record_version"], idempotency_key=key(),
		)
		dpp_task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
		frappe.set_user(fx.PLANNER)
		accepted = dpp_validation.accept_departmental_plan(
			task=dpp_task.name, classifications={entry_id: "Goods"}, task_token=dpp_task.task_token, idempotency_key=key(),
		)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		formed = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"], dpp_entries=[entries[need]], mode="each",
			expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		item_id = formed["created_items"][0]
		self.complete(item_id)
		self.confirm_funding(accepted["annual_plan"])
		approved = self.activate(accepted["annual_plan"])
		self.assertEqual(approved["activation"], "activated")

		projection = frappe.db.get_value("Need Planning Usage Projection", accepted_version, ["usage", "active_plan", "active_plan_item"], as_dict=True)
		self.assertEqual(projection.usage, "Fully included")
		self.assertEqual(projection.active_plan, accepted["annual_plan"])
		self.assertEqual(projection.active_plan_item, item_id)

		frappe.set_user(fx.PLANNER)
		plan_publication.begin_plan_update(plan_reference=accepted["annual_plan"], idempotency_key=key())
		item_read = plan_read.get_plan_item(plan_item_id=item_id)
		plan_publication.remove_plan_item_in_successor(plan_item=item_id, expected_record_version=item_read["record_version"], idempotency_key=key())
		self.confirm_funding(accepted["annual_plan"])
		self.activate(accepted["annual_plan"])
		projection = frappe.db.get_value("Need Planning Usage Projection", accepted_version, ["usage", "active_plan"], as_dict=True)
		self.assertEqual(projection.usage, "Not included")
		self.assertFalse(projection.active_plan)

	def test_a_not_proceeding_need_reaches_departmental_needs_and_forms_no_item(self):
		"""PLN-AC-092/093 — accounted for, excluded from totals, outcome published."""
		need = self._accepted_need("Need the department reconsidered")
		accepted_version = frappe.db.get_value("Departmental Need", need, "current_accepted_revision")
		opened, entries = self._dpp_with_needs([need])
		entry_id = frappe.db.get_value("Departmental Plan Entry", entries[need], "entry_id")
		frappe.set_user(fx.HOD)
		# an unaccounted Need blocks submission (PLN-AC-093)
		with self.assertRaises(ProcurementPlanningError) as caught:
			dpp_lifecycle.submit_departmental_plan(
				dpp_version=opened["current_version"], certification_confirmed=True, expected_record_version=opened["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_ENTRY_INCOMPLETE")
		frappe.set_user(fx.AUTHOR)
		marked = dpp_lifecycle.set_need_planning_disposition(
			dpp_version=opened["current_version"], entry_id=entry_id, disposition="Do not proceed",
			reason="The department will defer this requirement to the following financial year.",
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		self.assertEqual(marked["action"], "need_not_proceeding")
		added = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"], values=fx.direct_values(), expected_record_version=marked["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.HOD)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True, expected_record_version=added["record_version"], idempotency_key=key(),
		)
		dpp_task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
		frappe.set_user(fx.PLANNER)
		read = plan_read.get_dpp_validation_task if False else None
		accepted = dpp_validation.accept_departmental_plan(
			task=dpp_task.name, classifications={added["entry_id"]: "Goods"}, task_token=dpp_task.task_token, idempotency_key=key(),
		)
		# v1.18 §5.1.4 — the accepted disposition reaches Needs as NeedPlanningDispositionChanged.v1;
		# the usage projection keeps its Active-inclusion meaning and is untouched by a DPP exclusion
		disposition = frappe.db.get_value(
			"Need Planning Disposition Projection", {"departmental_need": need, "need_revision": accepted_version},
			["disposition", "reason", "producer_sequence", "dpp_submission"], as_dict=True,
		)
		self.assertEqual(disposition.disposition, "Not proceeding")
		self.assertIn("defer", disposition.reason)
		self.assertEqual(int(disposition.producer_sequence), 1)
		self.assertTrue(disposition.dpp_submission)
		usage = frappe.db.get_value("Need Planning Usage Projection", accepted_version, "usage")
		self.assertNotEqual(usage, "Not proceeding")
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertEqual(len(plan["unallocated_sources"]), 1)
		self.assertEqual(plan["unallocated_sources"][0]["source_origin"], "Direct departmental requirement")
		self.assertEqual(plan["summary"]["accepted_entries"], 1)
