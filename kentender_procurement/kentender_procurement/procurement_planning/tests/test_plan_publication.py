# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §4.13/§5.2/§7.1/§8.2 — publication, activation, the
forecast cascade and successors: PublishAnnualPlan (a system action inside
ApproveAnnualPlan) / RetryPublication, BeginPlanUpdate /
RemovePlanItemInSuccessor / CancelPlanUpdate, PreviewForecastCascade /
ConfirmForecastCascade, CheckApproachingMilestones, and the
NeedPlanningUsageChanged.v1 publisher proved against a genuine accepted Need
(PLN-AC-030/031/032/077/081/086/108/118/119/120/123..130)."""

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
		# `Annual Plan Publication Destination` is a shared site-configuration
		# row, not wiped per test; a prior test that changed `sandbox_outcome`
		# and errored before resetting it would otherwise leak into every
		# later test in the run. Reset it deterministically here instead.
		frappe.db.set_value("Annual Plan Publication Destination", {"adapter": publication_pipeline.DESTINATION_ADAPTER}, "sandbox_outcome", "Acknowledge")
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

	def record_treasury(self, plan_version: str) -> dict:
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		result = treasury.record_treasury_submission(
			plan_version=plan_version, submitted_at="2101-11-01 09:00:00", channel="Email", destination="treasury@example.test",
			dispatch_reference="MOH/APP/2101/001", exact_document_confirmed=True, idempotency_key=key(),
		)
		frappe.set_user(fx.PLANNER)
		return result

	def activate(self, plan_reference: str) -> dict:
		"""Approve, record Treasury evidence, then run the publication worker
		inline (D8: no RQ worker on this bench — the same call `ApproveAnnualPlan`
		would `frappe.enqueue` post-commit in production). Returns the worker's
		result dict (`result`: Acknowledged/Failed/Indeterminate)."""
		approved = self.approve(plan_reference)
		version = frappe.db.get_value("Plan Publication", approved["publication"], "plan_version")
		self.record_treasury(version)
		frappe.set_user("Administrator")
		published = publication_pipeline.publish_annual_plan(plan_version=version, idempotency_key=key())
		frappe.set_user(fx.PLANNER)
		return published


class TestActivationAndRetryPublication(PublicationCase):
	"""PLN-CHG-001 v1.18 §5.5.2 / §7.2 — the asynchronous publication
	pipeline (plan D8, PLN18-209): approval only commits; a separate worker
	transmits under a Treasury-evidence gate; acknowledgement is a distinct
	authenticated event that runs activation; retry and reconciliation are
	technical actions on the frozen manifest, never a new approval."""

	def test_approval_commits_only_then_the_worker_publishes_and_activates_with_the_v1_18_payload(self):
		reservations_before = frappe.db.count("Funding Reservation")
		accepted, item_id = self.confirmed_item()
		approved = self.approve(accepted["annual_plan"])
		version_name = frappe.db.get_value("Plan Publication", approved["publication"], "plan_version")
		# §5.5.2: commit-only — no external send, content locked, not yet Active
		self.assertEqual(frappe.db.get_value("Annual Plan Version", version_name, "version_status"), "Approved — publication pending")
		self.assertFalse(frappe.db.get_value("Annual Plan", accepted["annual_plan"], "active_version"))
		publication = frappe.get_doc("Plan Publication", approved["publication"])
		self.assertEqual(publication.publication_state, "Pending")
		self.assertEqual(publication.schema_version, plan_json.SCHEMA_VERSION)

		# the worker refuses to transmit before Treasury evidence exists
		frappe.set_user("Administrator")
		with self.assertRaises(ProcurementPlanningError) as caught:
			publication_pipeline.publish_annual_plan(plan_version=version_name, idempotency_key=key())
		self.assertEqual(caught.exception.code, "PLN_TREASURY_EVIDENCE_REQUIRED")
		self.record_treasury(version_name)
		frappe.set_user("Administrator")  # PublishAnnualPlan is a system worker, never a business user action
		published = publication_pipeline.publish_annual_plan(plan_version=version_name, idempotency_key=key())
		self.assertEqual(published["result"], "Acknowledged")
		self.assertEqual(frappe.db.count("Funding Reservation"), reservations_before)  # PLN-AC-081

		read = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertIsNotNone(read["active_view"])
		self.assertEqual(read["header"]["badge"], "Active")
		self.assertFalse(read["mutable"])
		self.assertEqual(read["active_view"]["summary"]["plan_items"], 1)
		self.assertEqual(read["active_view"]["summary"]["schedule_health_display"], "0 of 1 item behind baseline")
		row = read["active_view"]["items"][0]
		self.assertEqual(row["plan_item_id"], item_id)
		self.assertEqual(len(row["schedule"]), 7)
		self.assertTrue(all(r["forecast"] == r["baseline"] and r["actual"] == "" for r in row["schedule"]))
		self.assertTrue(row["schedule"][0]["can_shift"])
		self.assertTrue(row["schedule"][-1]["can_shift"])  # v1.18 §5.5.1: a final-milestone single-row change is allowed with a reason
		self.assertIn("Acknowledged", read["active_view"]["governance_card"]["publication_line"])

		publication.reload()
		self.assertEqual(publication.publication_state, "Acknowledged")
		self.assertTrue(publication.external_reference)
		ack = frappe.get_doc("Publication Acknowledgement", {"publication": publication.name})
		self.assertTrue(ack.matched)
		self.assertEqual(ack.package_hash, publication.package_hash)
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

		frappe.set_user(fx.PLANNER)
		task_read = plan_read.get_publication_task(publication=publication.name)
		self.assertEqual(task_read["publication_state"], "Acknowledged")
		self.assertFalse(task_read["can_retry"])
		self.assertTrue(task_read["treasury_evidence"]["recorded"])

	def test_a_failed_attempt_is_recovered_by_a_technical_retry(self):
		accepted, item_id = self.confirmed_item()
		approved = self.approve(accepted["annual_plan"])
		version_name = frappe.db.get_value("Plan Publication", approved["publication"], "plan_version")
		self.record_treasury(version_name)
		frappe.db.set_value("Annual Plan Publication Destination", frappe.get_doc("Plan Publication", approved["publication"]).destination, "sandbox_outcome", "Fail")
		frappe.set_user("Administrator")
		published = publication_pipeline.publish_annual_plan(plan_version=version_name, idempotency_key=key())
		self.assertEqual(published["result"], "Failed")
		self.assertFalse(frappe.db.get_value("Annual Plan", accepted["annual_plan"], "active_version"))
		self.assertEqual(frappe.db.get_value("Annual Plan Version", version_name, "version_status"), "Publication failed")
		publication = frappe.get_doc("Plan Publication", approved["publication"])
		self.assertEqual(publication.publication_state, "Failed")
		self.assertFalse(frappe.db.get_value("Annual Plan Item", {"plan_version": version_name}, "forecast_invitation_date"))

		frappe.set_user(fx.PLANNER)
		with self.assertRaises(frappe.DoesNotExistError):
			publication_pipeline.retry_publication(publication=publication.name, idempotency_key=key())
		frappe.set_user("Administrator")
		self.assertTrue(plan_read.get_publication_task(publication=publication.name)["can_retry"])
		frappe.db.set_value("Annual Plan Publication Destination", publication.destination, "sandbox_outcome", "Acknowledge")
		retry_key = key()
		retried = publication_pipeline.retry_publication(publication=publication.name, idempotency_key=retry_key)
		self.assertEqual(retried["result"], "Acknowledged")
		replayed = publication_pipeline.retry_publication(publication=publication.name, idempotency_key=retry_key)
		self.assertTrue(replayed["idempotent"])
		self.assertEqual(replayed["publication"], retried["publication"])
		self.assertEqual(frappe.db.get_value("Annual Plan Version", version_name, "version_status"), "Active")
		self.assertEqual(frappe.db.count("Publication Attempt", {"publication": publication.name}), 2)
		# PLN-AC-043: the same frozen manifest is resent, never a new package
		publication.reload()
		self.assertEqual(publication.package_hash, frappe.get_doc("Plan Publication", retried["publication"]).package_hash)

	def test_an_indeterminate_result_must_be_reconciled_before_retry(self):
		accepted, item_id = self.confirmed_item()
		approved = self.approve(accepted["annual_plan"])
		version_name = frappe.db.get_value("Plan Publication", approved["publication"], "plan_version")
		self.record_treasury(version_name)
		destination = frappe.get_doc("Plan Publication", approved["publication"]).destination
		frappe.db.set_value("Annual Plan Publication Destination", destination, "sandbox_outcome", "Indeterminate")
		frappe.set_user("Administrator")
		published = publication_pipeline.publish_annual_plan(plan_version=version_name, idempotency_key=key())
		self.assertEqual(published["result"], "Indeterminate")
		# still not confirmed failed — the Version stays as it was, awaiting reconciliation
		self.assertEqual(frappe.db.get_value("Annual Plan Version", version_name, "version_status"), "Approved — publication pending")
		with self.assertRaises(ProcurementPlanningError) as caught:
			publication_pipeline.retry_publication(publication=approved["publication"], idempotency_key=key())
		self.assertEqual(caught.exception.code, "PLN_REVIEW_STALE")  # only a confirmed Failed publication may retry
		frappe.db.set_value("Annual Plan Publication Destination", destination, "sandbox_outcome", "Acknowledge")
		reconciled = publication_pipeline.reconcile_publication(publication=approved["publication"], idempotency_key=key())
		self.assertEqual(reconciled["outcome"], "Acknowledged")
		self.assertEqual(frappe.db.get_value("Annual Plan Version", version_name, "version_status"), "Active")

	def test_a_hold_blocks_the_worker_and_a_correction_request_hold_is_ao_only(self):
		accepted, item_id = self.confirmed_item()
		approved = self.approve(accepted["annual_plan"])
		version_name = frappe.db.get_value("Plan Publication", approved["publication"], "plan_version")
		self.record_treasury(version_name)
		frappe.set_user(fx.PLANNER)
		with self.assertRaises(frappe.DoesNotExistError):
			publication_pipeline.hold_plan_publication(plan_version=version_name, reason="A material defect was found.", hold_kind="Accounting Officer correction request", idempotency_key=key())
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		held = publication_pipeline.hold_plan_publication(plan_version=version_name, reason="A material defect was found.", hold_kind="Accounting Officer correction request", idempotency_key=key())
		self.assertTrue(held["hold"])
		frappe.set_user("Administrator")
		with self.assertRaises(ProcurementPlanningError) as caught:
			publication_pipeline.publish_annual_plan(plan_version=version_name, idempotency_key=key())
		self.assertEqual(caught.exception.code, "PLN_PUBLICATION_HELD")
		# a hold is not a withdrawal of approval
		self.assertEqual(frappe.db.get_value("Annual Plan Version", version_name, "version_status"), "Approved — publication pending")

	def test_a_duplicate_acknowledgement_is_idempotent_and_a_mismatched_hash_never_activates(self):
		accepted, item_id = self.confirmed_item()
		approved = self.approve(accepted["annual_plan"])
		version_name = frappe.db.get_value("Plan Publication", approved["publication"], "plan_version")
		self.record_treasury(version_name)
		publication = frappe.get_doc("Plan Publication", approved["publication"])
		frappe.set_user("Administrator")
		with self.assertRaises(ProcurementPlanningError) as caught:
			publication_pipeline.receive_publication_acknowledgement(event_id="EVT-BAD-HASH", publication=publication.name, package_hash="not-the-right-hash")
		self.assertEqual(caught.exception.code, "PLN_PUBLICATION_ACK_MISMATCH")
		self.assertEqual(frappe.db.get_value("Annual Plan Version", version_name, "version_status"), "Approved — publication pending")
		first = publication_pipeline.receive_publication_acknowledgement(event_id="EVT-GOOD-1", publication=publication.name, package_hash=publication.package_hash)
		self.assertEqual(frappe.db.get_value("Annual Plan Version", version_name, "version_status"), "Active")
		replay = publication_pipeline.receive_publication_acknowledgement(event_id="EVT-GOOD-1", publication=publication.name, package_hash=publication.package_hash)
		self.assertTrue(replay["idempotent"])
		self.assertEqual(replay["acknowledgement"], first["acknowledgement"])
		# the mismatched attempt and the matched one are distinct events, not duplicates of each other;
		# only replaying the SAME event id (EVT-GOOD-1) is idempotent
		self.assertEqual(frappe.db.count("Publication Acknowledgement", {"publication": publication.name}), 2)
		self.assertEqual(frappe.db.count("Publication Acknowledgement", {"publication": publication.name, "event_id": "EVT-GOOD-1"}), 1)


class TestTreasuryAndWithdrawal(PublicationCase):
	"""PLN-CHG-001 v1.18 §5.5.2.2 / §5.5.2.3 / §7.2 — Treasury submission
	evidence and the withdrawal-for-correction recovery route (PLN18-209)."""

	def test_correcting_treasury_evidence_appends_and_holds_an_in_flight_attempt(self):
		accepted, item_id = self.confirmed_item()
		approved = self.approve(accepted["annual_plan"])
		version_name = frappe.db.get_value("Plan Publication", approved["publication"], "plan_version")
		first = self.record_treasury(version_name)
		destination = frappe.get_doc("Plan Publication", approved["publication"]).destination
		frappe.db.set_value("Annual Plan Publication Destination", destination, "sandbox_outcome", "Indeterminate")
		frappe.set_user("Administrator")
		publication_pipeline.publish_annual_plan(plan_version=version_name, idempotency_key=key())
		self.assertEqual(frappe.db.get_value("Plan Publication", approved["publication"], "publication_state"), "Indeterminate")

		frappe.set_user(fx.ACCOUNTING_OFFICER)
		corrected = treasury.correct_treasury_submission_evidence(
			prior_evidence=first["evidence"], reason="The dispatch reference was recorded incorrectly.",
			submitted_at="2101-11-02 09:00:00", channel="Email", destination="treasury@example.test",
			dispatch_reference="MOH/APP/2101/002", idempotency_key=key(),
		)
		self.assertEqual(corrected["action"], "treasury_evidence_corrected")
		self.assertTrue(corrected["hold"])  # the in-flight indeterminate attempt is held pending reconciliation
		self.assertEqual(frappe.db.get_value("Treasury Submission Evidence", first["evidence"], "evidence_state"), "Superseded")
		self.assertEqual(frappe.db.get_value("Treasury Submission Evidence", first["evidence"], "superseded_by"), corrected["evidence"])
		self.assertEqual(frappe.db.count("Treasury Submission Evidence", {"plan_version": version_name}), 2)  # append-only
		frappe.set_user("Administrator")
		with self.assertRaises(ProcurementPlanningError) as caught:
			publication_pipeline.publish_annual_plan(plan_version=version_name, idempotency_key=key())
		self.assertEqual(caught.exception.code, "PLN_PUBLICATION_HELD")

	def test_a_held_in_flight_attempt_is_distinct_from_its_indeterminate_result_on_the_plan_read(self):
		"""PLN-CHG-001 v1.18 §9.6 (PLN18-211): "Confirmed unpublished with
		material defect: Publication on hold" is a workspace-visible label,
		not only a fact on the drill-in publication screen — a hold never
		rewrites `publication_state` itself (§5.5.2.3), so `get_annual_plan`
		must surface it as its own field."""
		accepted, item_id = self.confirmed_item()
		approved = self.approve(accepted["annual_plan"])
		version_name = frappe.db.get_value("Plan Publication", approved["publication"], "plan_version")
		first = self.record_treasury(version_name)
		destination = frappe.get_doc("Plan Publication", approved["publication"]).destination
		frappe.db.set_value("Annual Plan Publication Destination", destination, "sandbox_outcome", "Indeterminate")
		frappe.set_user("Administrator")
		publication_pipeline.publish_annual_plan(plan_version=version_name, idempotency_key=key())

		frappe.set_user(fx.PLANNER)
		before = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertEqual(before["latest_publication"]["result"], "Indeterminate")
		self.assertFalse(before["latest_publication"]["held"])

		frappe.set_user(fx.ACCOUNTING_OFFICER)
		corrected = treasury.correct_treasury_submission_evidence(
			prior_evidence=first["evidence"], reason="The dispatch reference was recorded incorrectly.",
			submitted_at="2101-11-02 09:00:00", channel="Email", destination="treasury@example.test",
			dispatch_reference="MOH/APP/2101/002", idempotency_key=key(),
		)
		self.assertTrue(corrected["hold"])

		frappe.set_user(fx.PLANNER)
		after = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertEqual(after["latest_publication"]["result"], "Indeterminate")  # unchanged by the hold
		self.assertTrue(after["latest_publication"]["held"])
		self.assertEqual(after["latest_publication"]["hold_kind"], "Accounting Officer correction request")
		self.assertTrue(after["latest_publication"]["hold_reason"])

	def test_withdrawal_requires_confirmed_unpublished_content(self):
		accepted, item_id = self.confirmed_item()
		approved = self.activate(accepted["annual_plan"])
		version_name = frappe.db.get_value("Plan Publication", approved["publication"], "plan_version")
		self.assertEqual(approved["result"], "Acknowledged")
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		with self.assertRaises(ProcurementPlanningError) as caught:
			treasury.request_plan_withdrawal(plan_version=version_name, reason="The package needs correction before publication.", idempotency_key=key())
		self.assertEqual(caught.exception.code, "PLN_WITHDRAWAL_NOT_PERMITTED")

	def test_a_failed_publication_can_be_withdrawn_for_correction_by_the_statutory_authority(self):
		accepted, item_id = self.confirmed_item()
		approved = self.approve(accepted["annual_plan"])
		version_name = frappe.db.get_value("Plan Publication", approved["publication"], "plan_version")
		self.record_treasury(version_name)
		destination = frappe.get_doc("Plan Publication", approved["publication"]).destination
		frappe.db.set_value("Annual Plan Publication Destination", destination, "sandbox_outcome", "Fail")
		frappe.set_user("Administrator")
		publication_pipeline.publish_annual_plan(plan_version=version_name, idempotency_key=key())
		self.assertEqual(frappe.db.get_value("Annual Plan Version", version_name, "version_status"), "Publication failed")

		frappe.set_user(fx.ACCOUNTING_OFFICER)
		requested = treasury.request_plan_withdrawal(plan_version=version_name, reason="A material defect was found in the approved package.", idempotency_key=key())
		self.assertTrue(requested["hold"])
		self.assertTrue(requested["task"])
		frappe.set_user("Administrator")
		with self.assertRaises(ProcurementPlanningError) as caught:
			publication_pipeline.publish_annual_plan(plan_version=version_name, idempotency_key=key())
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


class TestForecastCascade(PublicationCase):
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

	def test_preview_proposes_every_later_milestone_and_confirm_writes_one_cascade(self):
		accepted, item_id = self.active()
		frappe.set_user(fx.PLANNER)
		preview = schedule.preview_forecast_cascade(plan_item=item_id, milestone="bid_opening", new_forecast_date="2101-10-06")
		self.assertEqual(preview["delta_days"], 14)
		self.assertEqual([r["milestone"] for r in preview["rows"]], list(schedule.MILESTONES[1:]))
		self.assertTrue(all(r["included"] for r in preview["rows"]))
		self.assertEqual(preview["rows"][0]["proposed_forecast"], "2101-10-06")
		# no write from a preview (invariant 1)
		self.assertEqual(frappe.db.count("Plan Item Forecast Revision"), 0)

		result = schedule.confirm_forecast_cascade(
			plan_item=item_id, milestone="bid_opening", new_forecast_date="2101-10-06", included_milestones=None,
			reason="Tender Preparation confirmed the issue date will slip two weeks pending template release.",
			expected_record_version=preview["record_version"], idempotency_key=key(),
		)
		self.assertEqual(result["action"], "forecast_shifted")
		self.assertTrue(result["cascade_id"])
		self.assertEqual(len(result["revisions"]), 6)
		item = frappe.get_doc("Annual Plan Item", plan_read.resolve_item_doc_name(item_id))
		self.assertEqual(str(item.forecast_bid_opening_date), "2101-10-06")
		self.assertEqual(str(item.baseline_bid_opening_date), "2101-09-22")  # baseline untouched (PLN-AC-118)
		self.assertEqual(str(item.forecast_delivery_completion_date), "2102-05-14")
		read = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertEqual(read["active_view"]["summary"]["schedule_health_display"], "1 of 1 item behind baseline")
		self.assertTrue(read["active_view"]["items"][0]["behind_baseline"])
		revisions = frappe.get_all("Plan Item Forecast Revision", filters={"plan_item": item.name}, fields=["cascade_id", "milestone"])
		self.assertEqual({r.cascade_id for r in revisions}, {result["cascade_id"]})

	def test_excluding_every_downstream_row_writes_a_standalone_revision(self):
		accepted, item_id = self.active()
		frappe.set_user(fx.PLANNER)
		preview = schedule.preview_forecast_cascade(plan_item=item_id, milestone="award_approval", new_forecast_date="2101-10-28")
		result = schedule.confirm_forecast_cascade(
			plan_item=item_id, milestone="award_approval", new_forecast_date="2101-10-28", included_milestones=["award_approval"],
			reason="Award approval alone moves one day; the notification date still follows it.",
			expected_record_version=preview["record_version"], idempotency_key=key(),
		)
		self.assertEqual(result["cascade_id"], "")  # PLN-AC-127
		self.assertEqual(len(result["revisions"]), 1)
		item = frappe.get_doc("Annual Plan Item", plan_read.resolve_item_doc_name(item_id))
		self.assertEqual(str(item.forecast_award_approval_date), "2101-10-28")
		self.assertEqual(str(item.forecast_award_notification_date), "2101-10-29")

	def test_governed_gaps_and_reasons_are_enforced_on_confirmation(self):
		accepted, item_id = self.active()
		frappe.set_user(fx.PLANNER)
		preview = schedule.preview_forecast_cascade(plan_item=item_id, milestone="contract_signing", new_forecast_date="2101-11-05")
		with self.assertRaises(ProcurementPlanningError) as caught:
			schedule.confirm_forecast_cascade(
				plan_item=item_id, milestone="contract_signing", new_forecast_date="2101-11-05", included_milestones=["contract_signing"],
				reason="Signing pulled forward inside the standstill period, which is not allowed.",
				expected_record_version=preview["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_PROFILE_PERIOD_INVALID")  # PLN18 §8: labelled parameters
		self.assertEqual(caught.exception.detail["period"], "standstill_period_days")
		with self.assertRaises(ProcurementPlanningError) as caught:
			schedule.confirm_forecast_cascade(
				plan_item=item_id, milestone="bid_opening", new_forecast_date="2101-10-06", included_milestones=None,
				reason="short", expected_record_version=preview["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_FORECAST_REASON_REQUIRED")

	def test_a_milestone_with_an_actual_is_never_proposed_and_actuals_are_never_typed(self):
		accepted, item_id = self.active()
		# the only writer of an actual is the inbound projection contract (§18)
		schedule.record_tender_milestone_actual(plan_item_id=item_id, milestone="invitation", actual_date="2101-09-03", source_event_id="TPR-TEST-1", producer="tender_preparation")
		# PLN-CHG-001 v1.18 §4.8 / plan D10: same value again is a no-op; a
		# different value never overwrites unless it supersedes the earlier event
		again = schedule.record_tender_milestone_actual(plan_item_id=item_id, milestone="invitation", actual_date="2101-09-03", source_event_id="TPR-TEST-1", producer="tender_preparation")
		self.assertTrue(again["idempotent"])
		with self.assertRaises(ProcurementPlanningError) as guarded:
			schedule.record_tender_milestone_actual(plan_item_id=item_id, milestone="invitation", actual_date="2101-09-04", source_event_id="TPR-TEST-2", producer="tender_preparation")
		self.assertEqual(guarded.exception.code, "PLN_ACTUAL_NOT_WRITABLE")
		with self.assertRaises(ProcurementPlanningError) as guarded:
			schedule.record_tender_milestone_actual(plan_item_id=item_id, milestone="invitation", actual_date="2101-09-04", source_event_id="", producer="tender_preparation")
		self.assertEqual(guarded.exception.code, "PLN_ACTUAL_NOT_WRITABLE")
		frappe.set_user(fx.PLANNER)
		item = plan_read.get_plan_item(plan_item_id=item_id)
		self.assertEqual(item["schedule"][0]["actual"], "2101-09-03")
		self.assertEqual(item["schedule"][0]["variance_baseline_days"], 2)
		self.assertFalse(item["schedule"][0]["can_shift"])
		with self.assertRaises(ProcurementPlanningError) as caught:
			schedule.preview_forecast_cascade(plan_item=item_id, milestone="invitation", new_forecast_date="2101-09-10")
		self.assertEqual(caught.exception.code, "PLN_CASCADE_INCLUDES_ACTUAL_MILESTONE")
		preview = schedule.preview_forecast_cascade(plan_item=item_id, milestone="bid_opening", new_forecast_date="2101-09-29")
		self.assertNotIn("invitation", [r["milestone"] for r in preview["rows"]])
		# PLN-AC-119 — no save path accepts a typed actual, even for Administrator
		frappe.set_user("Administrator")
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.save_plan_item(
				plan_item=item_id, values={"actual_bid_opening_date": "2101-09-25"}, expected_record_version=item["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_ACTUAL_NOT_WRITABLE")

	def test_the_daily_nudge_raises_once_per_milestone_per_day(self):
		accepted, item_id = self.active()
		frappe.db.delete("Notification Log", {"for_user": fx.PLANNER})
		item_name = plan_read.resolve_item_doc_name(item_id)
		root = frappe.db.get_value("Annual Plan Item", item_name, "plan_item")
		frappe.db.delete("Milestone Notice", {"plan_item": root})
		first = schedule.check_approaching_milestones(today="2101-08-25")
		self.assertIn((item_id, "invitation"), first["raised"])
		count = frappe.db.count("Notification Log", {"for_user": fx.PLANNER, "email_header": ("like", f"pln:milestone:{item_id}:invitation:%")})
		self.assertEqual(count, 1)
		notice = frappe.get_doc("Milestone Notice", {"plan_item": root, "milestone": "invitation", "proceeding_id": "", "recipient": fx.PLANNER})
		self.assertEqual(notice.notice_status, "Approaching")
		self.assertEqual(len(json.loads(notice.history)), 1)
		schedule.check_approaching_milestones(today="2101-08-25")
		self.assertEqual(frappe.db.count("Notification Log", {"for_user": fx.PLANNER, "email_header": ("like", f"pln:milestone:{item_id}:invitation:%")}), 1)
		self.assertEqual(frappe.db.count("Milestone Notice", {"plan_item": root, "milestone": "invitation", "proceeding_id": "", "recipient": fx.PLANNER}), 1)
		notice.reload()
		self.assertEqual(len(json.loads(notice.history)), 1)  # same status again — no duplicate history entry
		self.assertEqual(frappe.db.count("Plan Governance Task", {"plan_version": accepted["annual_plan_version"], "status": "Open"}), 0)
		# PLN-CHG-001 v1.18 §5.5.1B: Overdue detection (added Phase 2g) now
		# also flags every OTHER Active item on this shared site whose own
		# forecast lies before this artificial "today" — assert this test's
		# own item specifically, not the whole-site list.
		self.assertNotIn((item_id, "invitation"), schedule.check_approaching_milestones(today="2101-06-01")["raised"])
		schedule.check_approaching_milestones(today="2101-09-04")  # past the forecast date: Overdue
		notice.reload()
		self.assertEqual(notice.notice_status, "Overdue")
		self.assertEqual(len(json.loads(notice.history)), 2)
		schedule.record_tender_milestone_actual(plan_item_id=item_id, milestone="invitation", actual_date="2101-09-03", source_event_id="TPR-NUDGE-1", producer="tender_preparation")
		notice.reload()
		self.assertEqual(notice.notice_status, "Cleared")


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
		copies = frappe.get_all("Annual Plan Item", filters={"plan_item_id": item_id}, fields=["name", "plan_version", "item_state", "forecast_invitation_date", "baseline_invitation_date"])
		self.assertEqual(len(copies), 2)
		by_version = {c.plan_version: c for c in copies}
		self.assertEqual(by_version[active_version].item_state, "Active")
		self.assertEqual(by_version[successor].item_state, "Draft")
		self.assertFalse(by_version[successor].forecast_invitation_date)
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


class TestNeedOriginUsagePublishing(PublicationCase):
	"""§7.1's outbound event proved against a genuine accepted Need created
	through NDS's own real command chain, so the Need-origin DPP intake, the
	not-proceeding outcome and the activation publisher round-trip for real."""

	MOCK_NEEDS = False

	def setUp(self):
		super().setUp()
		from kentender_core.services import site_configuration

		self._needs_open = frappe.get_all("Fiscal Year", filters={site_configuration.FLAG_OPEN: 1}, pluck="name")
		if not frappe.db.get_value("Fiscal Year", fx.FY_OPEN, site_configuration.FLAG_OPEN):
			site_configuration.open_needs_submission(fiscal_year=fx.FY_OPEN, reason="Planning test: Need-origin fixtures")
		self.addCleanup(self._restore_needs_flag)
		self._wipe_need_fixture()

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
			indicative_quantity=5, unit=fx.UNIT, required_by_date="2102-01-01", idempotency_key=key(),
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
		self.assertEqual(approved["result"], "Acknowledged")

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
