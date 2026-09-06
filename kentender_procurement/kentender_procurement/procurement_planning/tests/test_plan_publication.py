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
	plan_publication,
	plan_read,
	plan_workbench,
	schedule,
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

	def activate(self, plan_reference: str) -> dict:
		frappe.set_user(fx.PLANNER)
		plan = plan_read.get_annual_plan(plan_reference=plan_reference)
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


class TestActivationAndRetryPublication(PublicationCase):
	def test_approval_activates_the_plan_with_an_ocds_payload_and_seeded_forecasts(self):
		reservations_before = frappe.db.count("Funding Reservation")
		accepted, item_id = self.confirmed_item()
		approved = self.activate(accepted["annual_plan"])
		self.assertEqual(approved["publication_result"], "Acknowledged")
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
		self.assertFalse(row["schedule"][-1]["can_shift"])
		self.assertIn("Acknowledged", read["active_view"]["governance_card"]["publication_line"])

		publication = frappe.get_doc("Annual Plan Publication", {"plan_version": read["version_reference"]})
		self.assertEqual(publication.attempt_number, 1)
		self.assertEqual(publication.result, "Acknowledged")
		self.assertIn("Invitation to treat", publication.legal_character)
		payload = json.loads(publication.payload)
		self.assertEqual(len(payload["releases"]), 1)
		release = payload["releases"][0]
		self.assertTrue(release["ocid"].startswith("ocds-"))
		self.assertEqual(release["tender"]["procurementMethod"], "Open Tender")
		self.assertEqual(release["planning"]["kentender"]["planHorizon"], "Single year")
		self.assertEqual(release["planning"]["kentender"]["lottingIndicator"], "Single lot")
		self.assertEqual(release["planning"]["kentender"]["reservationCategory"], "None")
		self.assertEqual(release["tender"]["tenderPeriod"]["startDate"], "2101-09-01")
		self.assertEqual(payload["plan"]["approvedBy"], "Cabinet Secretary")
		frappe.set_user(fx.PLANNER)
		task_read = plan_read.get_publication_task(publication=publication.name)
		self.assertEqual(task_read["result"], "Acknowledged")
		self.assertFalse(task_read["can_retry"])

	def test_a_failed_attempt_is_recovered_by_a_system_manager_retry(self):
		accepted, item_id = self.confirmed_item()
		with patch.object(plan_publication, "_transmit", return_value=("Failed", "")):
			approved = self.activate(accepted["annual_plan"])
		self.assertEqual(approved["publication_result"], "Failed")
		plan_name = frappe.db.get_value("Annual Plan", {"plan_reference": accepted["annual_plan"]})
		self.assertFalse(frappe.db.get_value("Annual Plan", plan_name, "active_version"))
		failed_version = frappe.db.get_value("Annual Plan Version", {"annual_plan": plan_name}, "name")
		self.assertEqual(frappe.db.get_value("Annual Plan Version", failed_version, "version_status"), "Publication failed")
		publication = frappe.get_doc("Annual Plan Publication", {"plan_version": failed_version})
		self.assertEqual(publication.result, "Failed")
		self.assertFalse(publication.external_reference)
		self.assertFalse(frappe.db.get_value("Annual Plan Item", {"plan_version": failed_version}, "forecast_invitation_date"))

		frappe.set_user(fx.PLANNER)
		with self.assertRaises(frappe.DoesNotExistError):
			plan_publication.retry_publication(publication=publication.name, idempotency_key=key())
		frappe.set_user("Administrator")
		self.assertTrue(plan_read.get_publication_task(publication=publication.name)["can_retry"])
		retry_key = key()
		retried = plan_publication.retry_publication(publication=publication.name, idempotency_key=retry_key)
		self.assertEqual(retried["result"], "Acknowledged")
		replayed = plan_publication.retry_publication(publication=publication.name, idempotency_key=retry_key)
		self.assertTrue(replayed["idempotent"])
		self.assertEqual(replayed["publication"], retried["publication"])
		self.assertEqual(frappe.db.get_value("Annual Plan Version", failed_version, "version_status"), "Active")
		self.assertEqual(frappe.db.count("Annual Plan Publication", {"plan_version": failed_version}), 2)
		second = frappe.get_doc("Annual Plan Publication", retried["publication"])
		self.assertEqual(second.payload_hash, publication.payload_hash)  # PLN-AC-043: the same payload


class TestForecastCascade(PublicationCase):
	def active(self) -> tuple[dict, str]:
		accepted, item_id = self.confirmed_item()
		self.activate(accepted["annual_plan"])
		return accepted, item_id

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
		self.assertEqual(caught.exception.code, "PLN_STANDSTILL_BELOW_MINIMUM")  # PLN-AC-128
		with self.assertRaises(ProcurementPlanningError) as caught:
			schedule.confirm_forecast_cascade(
				plan_item=item_id, milestone="bid_opening", new_forecast_date="2101-10-06", included_milestones=None,
				reason="short", expected_record_version=preview["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_FORECAST_REASON_REQUIRED")

	def test_a_milestone_with_an_actual_is_never_proposed_and_actuals_are_never_typed(self):
		accepted, item_id = self.active()
		# the only writer of an actual is the inbound projection contract (§18)
		schedule.record_tender_milestone_actual(plan_item_id=item_id, milestone="invitation", actual_date="2101-09-03", source_event_id="TPR-TEST-1")
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
		first = schedule.check_approaching_milestones(today="2101-08-25")
		self.assertIn((item_id, "invitation"), first["raised"])
		count = frappe.db.count("Notification Log", {"for_user": fx.PLANNER, "email_header": ("like", f"pln:milestone:{item_id}:invitation:%")})
		self.assertEqual(count, 1)
		schedule.check_approaching_milestones(today="2101-08-25")
		self.assertEqual(frappe.db.count("Notification Log", {"for_user": fx.PLANNER, "email_header": ("like", f"pln:milestone:{item_id}:invitation:%")}), 1)
		self.assertEqual(frappe.db.count("Plan Governance Task", {"plan_version": accepted["annual_plan_version"], "status": "Open"}), 0)
		self.assertEqual(schedule.check_approaching_milestones(today="2101-06-01")["raised"], [])


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
		versions = frappe.get_all("Departmental Need Version", filters={"departmental_need": ("in", needs or ("",))}, pluck="name")
		frappe.db.delete("Need Planning Usage Projection", {"name": ("in", versions or ("",))})
		frappe.db.delete("Departmental Need Decision", {"departmental_need": ("in", needs or ("",))})
		frappe.db.delete("Departmental Need Review Task", {"departmental_need": ("in", needs or ("",))})
		frappe.db.delete("Departmental Need Event", {"departmental_need": ("in", needs or ("",))})
		frappe.db.delete("Departmental Need Version", {"name": ("in", versions or ("",))})
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
		accepted_version = frappe.db.get_value("Departmental Need", need, "current_accepted_version")
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
		self.assertEqual(approved["publication_result"], "Acknowledged")

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
		accepted_version = frappe.db.get_value("Departmental Need", need, "current_accepted_version")
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
		marked = dpp_lifecycle.save_need_funding(
			dpp_version=opened["current_version"], entry_id=entry_id,
			not_proceeding_reason="The department will defer this requirement to the following financial year.",
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
		projection = frappe.db.get_value("Need Planning Usage Projection", accepted_version, ["usage", "not_proceeding_reason"], as_dict=True)
		self.assertEqual(projection.usage, "Not proceeding")
		self.assertIn("defer", projection.not_proceeding_reason)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertEqual(len(plan["unallocated_sources"]), 1)
		self.assertEqual(plan["unallocated_sources"][0]["source_origin"], "Direct departmental requirement")
		self.assertEqual(plan["summary"]["accepted_entries"], 1)
