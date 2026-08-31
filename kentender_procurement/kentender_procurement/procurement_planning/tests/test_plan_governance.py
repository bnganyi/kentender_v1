# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 §5.2/§6.1/§8 Annual Plan governance tests (Phase 8,
Slice F): SubmitConsolidatedPlan, AdoptAndSubmitPlan, ApproveAnnualPlan,
ReturnPlanVersion (both stages) and SubmitCorrectedPlan."""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.errors import ProcurementPlanningError
from kentender_procurement.procurement_planning.services import (
	dpp_lifecycle,
	dpp_validation,
	needs_intake,
	plan_finance,
	plan_governance,
	plan_read,
	plan_workbench,
)
from kentender_procurement.procurement_planning.tests import fixtures as fx


def key() -> str:
	return uuid4().hex


class TestCapacityResolution(IntegrationTestCase):
	"""§4.12/§6 — the one statutory route resolved from the PE's governed
	`entity_type`, no live governance flow needed to prove it."""

	def _pe(self, code: str, entity_type: str) -> str:
		if not frappe.db.exists("Procuring Entity", code):
			frappe.get_doc(
				{
					"doctype": "Procuring Entity", "entity_code": code, "legal_name": code,
					"entity_name": code, "reporting_currency": "KES", "status": "Active",
					"entity_type": entity_type, "fixture_namespace": "KENTENDER_TEST",
				}
			).insert(ignore_permissions=True)
		return code

	def test_ministry_and_unset_route_to_the_cabinet_secretary(self):
		self.assertEqual(
			plan_governance._capacity_for_pe(self._pe("PE-CAP-MOH", "Ministry")),
			"Responsible Cabinet Secretary",
		)
		self.assertEqual(
			plan_governance._capacity_for_pe(self._pe("PE-CAP-OTHER", "Other")),
			"Responsible Cabinet Secretary",
		)

	def test_county_government_routes_to_the_county_executive_committee_member(self):
		self.assertEqual(
			plan_governance._capacity_for_pe(self._pe("PE-CAP-COUNTY", "County Government")),
			"County Executive Committee Member",
		)

	def test_corporate_entities_route_to_the_governing_body(self):
		self.assertEqual(
			plan_governance._capacity_for_pe(self._pe("PE-CAP-CORP", "State Corporation")),
			"Board of Directors or similar governing body",
		)
		self.assertTrue(plan_governance._is_board_capacity(
			plan_governance._capacity_for_pe(self._pe("PE-CAP-UNI", "Public University"))
		))


class GovernanceCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_planning_rows()
		self.addCleanup(frappe.set_user, "Administrator")
		patched = patch.object(needs_intake, "current_accepted_sources", return_value=[])
		patched.start()
		self.addCleanup(patched.stop)

	def confirmed_item(self, *, indicative_amount: float = 1000000) -> tuple[dict, str]:
		"""One accepted entry, formed, fully completed and Finance-Confirmed
		— ready for SubmitConsolidatedPlan."""
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			procuring_entity=fx.PE, organisation_unit=fx.OU_ALPHA,
			financial_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)
		added = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"],
			values=fx.direct_values(indicative_amount=indicative_amount),
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.HOD)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True,
			expected_record_version=added["record_version"], idempotency_key=key(),
		)
		dpp_task = frappe.get_doc(
			"Departmental Plan Validation Task", {"task_reference": submitted["task"]}
		)
		frappe.set_user(fx.PLANNER)
		accepted = dpp_validation.accept_departmental_plan(
			task=dpp_task.name, classifications={added["entry_id"]: "Goods"},
			task_token=dpp_task.task_token, idempotency_key=key(),
		)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		formed = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"],
			dpp_entries=[plan["unallocated_sources"][0]["dpp_entry"]],
			mode="each", expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		item_id = formed["created_items"][0]
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.save_plan_item(
			plan_item=item_id,
			values={
				"title": "Direct requirement", "description": "Assess and remediate the direct requirement.",
				"strategic_objective": fx.STRATEGY_OBJECTIVE, "aggregation_reason": "",
				"invitation_date": "2098-08-01", "bid_opening_date": "2098-08-15",
				"evaluation_completion_date": "2098-09-01", "award_approval_date": "2098-09-10",
				"award_notification_date": "2098-09-15", "contract_signing_date": "2098-10-01",
				"delivery_completion_date": "2098-10-15",
			},
			expected_record_version=item["record_version"], idempotency_key=key(),
		)
		item = plan_read.get_plan_item(plan_item_id=item_id)
		requested = plan_finance.request_finance_confirmation(
			plan_item=item_id, expected_record_version=item["record_version"], idempotency_key=key(),
		)
		task = frappe.get_doc("Plan Finance Task", requested["task"])
		frappe.set_user(fx.BUDGET_OFFICER)
		read = plan_read.get_finance_task(task=task.name)
		plan_finance.confirm_funding(
			task=task.name, task_token=task.task_token, check_token=read["budget_check_token"],
			idempotency_key=key(),
		)
		return accepted, item_id

	def submit(self, plan_reference: str, *, actor: str = None):
		actor = actor or fx.PLANNER
		frappe.set_user(actor)
		plan = plan_read.get_annual_plan(plan_reference=plan_reference)
		return plan_governance.submit_consolidated_plan(
			plan_version=plan["version_reference"], expected_record_version=plan["record_version"],
			idempotency_key=key(),
		)


class TestSubmitConsolidatedPlan(GovernanceCase):
	def test_submit_creates_the_ao_task_and_freezes_the_snapshot(self):
		accepted, item_id = self.confirmed_item()
		result = self.submit(accepted["annual_plan"])
		self.assertEqual(result["action"], "submitted")
		task = frappe.get_doc("Plan Governance Task", result["task"])
		self.assertEqual(task.stage, "Accounting Officer adoption")
		self.assertEqual(task.status, "Open")
		version = frappe.get_doc("Annual Plan Version", task.plan_version)
		self.assertEqual(version.version_status, "Awaiting Accounting Officer")
		self.assertTrue(version.submitted_snapshot)
		import json

		snapshot = json.loads(version.submitted_snapshot)
		self.assertEqual(len(snapshot), 1)
		self.assertEqual(snapshot[0]["plan_item_id"], item_id)
		self.assertEqual(snapshot[0]["finance_state"], "Confirmed")
		self.assertIn("KES 1,000,000", snapshot[0]["value_display"])

	def test_submit_refuses_an_unconfirmed_item(self):
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			procuring_entity=fx.PE, organisation_unit=fx.OU_ALPHA,
			financial_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)
		added = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"], values=fx.direct_values(),
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.HOD)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True,
			expected_record_version=added["record_version"], idempotency_key=key(),
		)
		dpp_task = frappe.get_doc(
			"Departmental Plan Validation Task", {"task_reference": submitted["task"]}
		)
		frappe.set_user(fx.PLANNER)
		accepted = dpp_validation.accept_departmental_plan(
			task=dpp_task.name, classifications={added["entry_id"]: "Goods"},
			task_token=dpp_task.task_token, idempotency_key=key(),
		)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		formed = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"],
			dpp_entries=[plan["unallocated_sources"][0]["dpp_entry"]],
			mode="each", expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		# complete the item so the isolated gate under test is "not yet
		# Finance-confirmed", not an earlier incompleteness
		item_id = formed["created_items"][0]
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.save_plan_item(
			plan_item=item_id,
			values={
				"title": "Direct requirement", "description": "Assess and remediate the direct requirement.",
				"strategic_objective": fx.STRATEGY_OBJECTIVE, "aggregation_reason": "",
				"invitation_date": "2098-08-01", "bid_opening_date": "2098-08-15",
				"evaluation_completion_date": "2098-09-01", "award_approval_date": "2098-09-10",
				"award_notification_date": "2098-09-15", "contract_signing_date": "2098-10-01",
				"delivery_completion_date": "2098-10-15",
			},
			expected_record_version=item["record_version"], idempotency_key=key(),
		)
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.submit(accepted["annual_plan"])
		self.assertEqual(caught.exception.code, "PLN_ENTRY_INCOMPLETE")
		self.assertIn(item_id, str(caught.exception))


class TestAdoptApproveChain(GovernanceCase):
	def test_adopt_creates_the_statutory_task_and_approve_publishes_pending(self):
		accepted, item_id = self.confirmed_item()
		submitted = self.submit(accepted["annual_plan"])
		ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])

		frappe.set_user(fx.ACCOUNTING_OFFICER)
		adopted = plan_governance.adopt_and_submit_plan(
			task=ao_task.name, task_token=ao_task.task_token, idempotency_key=key(),
		)
		self.assertEqual(adopted["action"], "adopted")
		statutory_task = frappe.get_doc("Plan Governance Task", adopted["statutory_task"])
		self.assertEqual(statutory_task.stage, "Statutory approval")
		self.assertEqual(statutory_task.capacity, "Responsible Cabinet Secretary")
		version = frappe.get_doc("Annual Plan Version", statutory_task.plan_version)
		self.assertEqual(version.version_status, "Awaiting statutory approval")

		frappe.set_user(fx.STATUTORY)
		read = plan_read.get_plan_governance_task(task=statutory_task.name)
		self.assertTrue(read["authority_card"]["ao_adoption_line"])
		approved = plan_governance.approve_annual_plan(
			task=statutory_task.name, task_token=statutory_task.task_token, idempotency_key=key(),
		)
		self.assertEqual(approved["action"], "approved")
		self.assertEqual(
			frappe.db.get_value("Annual Plan Version", version.name, "version_status"),
			"Approved — publication pending",
		)

	def test_a_non_accounting_officer_is_refused(self):
		"""The Planner who submitted holds no Accounting Officer role at all
		— the role gate refuses before segregation is even reached. The real
		segregation proof (a genuine hybrid actor) is the next test."""
		accepted, item_id = self.confirmed_item()
		submitted = self.submit(accepted["annual_plan"])
		ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
		frappe.set_user(fx.PLANNER)
		with self.assertRaises(frappe.DoesNotExistError):
			plan_governance.adopt_and_submit_plan(
				task=ao_task.name, task_token=ao_task.task_token, idempotency_key=key(),
			)

	def test_hybrid_ao_planner_is_blocked_from_adopting_their_own_submission(self):
		accepted, item_id = self.confirmed_item()
		# submit as the hybrid actor instead of the plain Planner
		submitted = self.submit(accepted["annual_plan"], actor=fx.HYBRID_AO)
		ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
		frappe.set_user(fx.HYBRID_AO)
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_governance.adopt_and_submit_plan(
				task=ao_task.name, task_token=ao_task.task_token, idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_SEGREGATION_CONFLICT")

	def test_the_ao_adopter_cannot_also_approve(self):
		accepted, item_id = self.confirmed_item()
		submitted = self.submit(accepted["annual_plan"])
		ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
		frappe.set_user(fx.HYBRID_AO)
		adopted = plan_governance.adopt_and_submit_plan(
			task=ao_task.name, task_token=ao_task.task_token, idempotency_key=key(),
		)
		statutory_task = frappe.get_doc("Plan Governance Task", adopted["statutory_task"])
		frappe.set_user(fx.HYBRID_AO)
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_governance.approve_annual_plan(
				task=statutory_task.name, task_token=statutory_task.task_token, idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_SEGREGATION_CONFLICT")


class TestReturnPlanVersion(GovernanceCase):
	def test_ao_return_preserves_the_submission_and_creates_a_correction_carrying_finance_state(self):
		accepted, item_id = self.confirmed_item()
		submitted = self.submit(accepted["annual_plan"])
		ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_governance.return_plan_version(
				task=ao_task.name, reason="", task_token=ao_task.task_token, idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_ENTRY_INCOMPLETE")

		result = plan_governance.return_plan_version(
			task=ao_task.name,
			reason="Confirm the planned contract-signing date against the delivery completion date.",
			task_token=ao_task.task_token, idempotency_key=key(),
		)
		self.assertEqual(result["action"], "returned")
		submitted_version = frappe.get_doc("Annual Plan Version", ao_task.plan_version)
		self.assertEqual(submitted_version.version_status, "Returned")
		# the submitted snapshot itself is untouched
		self.assertTrue(submitted_version.submitted_snapshot)

		correction = frappe.get_doc("Annual Plan Version", result["correction_version"])
		self.assertEqual(correction.version_status, "Draft")
		self.assertEqual(correction.correction_of_plan_version, submitted_version.name)
		self.assertEqual(correction.version_number, submitted_version.version_number + 1)
		corrected_item = frappe.get_doc(
			"Annual Plan Item", {"plan_version": correction.name, "plan_item_id": item_id}
		)
		self.assertEqual(corrected_item.finance_state, "Confirmed")
		self.assertEqual(
			frappe.db.count("Plan Reservation Reference", {"plan_item": corrected_item.name}), 1
		)
		self.assertEqual(
			frappe.db.get_value("Annual Plan", accepted["annual_plan"], "open_successor_version"),
			correction.name,
		)

	def test_statutory_return_restarts_at_ao_on_resubmission(self):
		accepted, item_id = self.confirmed_item()
		submitted = self.submit(accepted["annual_plan"])
		ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		adopted = plan_governance.adopt_and_submit_plan(
			task=ao_task.name, task_token=ao_task.task_token, idempotency_key=key(),
		)
		statutory_task = frappe.get_doc("Plan Governance Task", adopted["statutory_task"])
		frappe.set_user(fx.STATUTORY)
		returned = plan_governance.return_plan_version(
			task=statutory_task.name,
			reason="Correct the procurement package description before the Plan is resubmitted.",
			task_token=statutory_task.task_token, idempotency_key=key(),
		)
		correction = frappe.get_doc("Annual Plan Version", returned["correction_version"])
		self.assertEqual(correction.version_status, "Draft")

		frappe.set_user(fx.PLANNER)
		resubmitted = plan_governance.submit_corrected_plan(
			plan_version=correction.name, expected_record_version=correction.record_version,
			idempotency_key=key(),
		)
		self.assertEqual(resubmitted["action"], "submitted")
		new_ao_task = frappe.get_doc("Plan Governance Task", resubmitted["task"])
		self.assertEqual(new_ao_task.stage, "Accounting Officer adoption")
		self.assertEqual(
			frappe.db.get_value("Annual Plan Version", correction.name, "version_status"),
			"Awaiting Accounting Officer",
		)
