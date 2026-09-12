# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §4.12/§5.2/§6.1/§8.2 — Annual Plan governance:
SubmitConsolidatedPlan, AdoptAndSubmitPlan, ApproveAnnualPlan,
ReturnPlanVersion (both stages) and SubmitCorrectedPlan, with the statutory
route resolved from the site's configured `statutory_approval_route`
(PLN-AC-025..029, 041, 050, 057, 084, 085, 098)."""

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
	plan_read,
	plan_workbench,
)
from kentender_procurement.procurement_planning.tests import fixtures as fx


def key() -> str:
	return uuid4().hex


class TestCapacityResolution(IntegrationTestCase):
	"""§4.12 — exactly one route, configured per site; never None."""

	def _with_route(self, route: str):
		single = frappe.get_doc("Site Procuring Entity")
		before = single.statutory_approval_route
		single.statutory_approval_route = route
		single.save(ignore_permissions=True)
		self.addCleanup(self._restore, before)

	def _restore(self, before: str):
		single = frappe.get_doc("Site Procuring Entity")
		single.statutory_approval_route = before
		single.save(ignore_permissions=True)

	def test_each_configured_route_resolves_to_its_capacity(self):
		for route, capacity in (
			("Cabinet Secretary", "Responsible Cabinet Secretary"),
			("County Executive Committee Member", "County Executive Committee Member"),
			("Board of Directors", "Board of Directors"),
			("Council", "Council"),
		):
			with self.subTest(route=route):
				self._with_route(route)
				self.assertEqual(plan_governance.capacity_for_site(), capacity)
		self.assertTrue(plan_governance.is_collective_capacity("Board of Directors"))
		self.assertTrue(plan_governance.is_collective_capacity("Council"))
		self.assertFalse(plan_governance.is_collective_capacity("Responsible Cabinet Secretary"))

	def test_an_unconfigured_route_blocks_with_the_configuration_code(self):
		with patch.object(plan_governance, "statutory_route", return_value=""):
			with self.assertRaises(ProcurementPlanningError) as caught:
				plan_governance.capacity_for_site()
		self.assertEqual(caught.exception.code, "PLN_STATUTORY_ROUTE_UNCONFIGURED")


class GovernanceCase(IntegrationTestCase):
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
		for target, attr, value in (
			(needs_intake, "current_accepted_sources", []),
			(budget_gateway, "eligible_line_ids", {fx.BUDGET_LINE, fx.BUDGET_LINE_2}),
		):
			patched = patch.object(target, attr, return_value=value)
			patched.start()
			self.addCleanup(patched.stop)

	def formed_item(self, *, indicative_amount: float = 1000000) -> tuple[dict, str]:
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			organisation_unit=fx.OU_ALPHA, fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)
		added = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"], values=fx.direct_values(indicative_amount=indicative_amount),
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.HOD)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True,
			expected_record_version=added["record_version"], idempotency_key=key(),
		)
		dpp_task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
		frappe.set_user(fx.PLANNER)
		accepted = dpp_validation.accept_departmental_plan(
			task=dpp_task.name, classifications={added["entry_id"]: "Goods"}, task_token=dpp_task.task_token, idempotency_key=key(),
		)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		formed = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"], dpp_entries=[plan["unallocated_sources"][0]["dpp_entry"]],
			mode="each", expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		return accepted, formed["created_items"][0]

	def complete(self, item_id: str, **overrides) -> None:
		frappe.set_user(fx.PLANNER)
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.save_plan_item(
			plan_item=item_id, values=fx.item_values(**overrides), expected_record_version=item["record_version"], idempotency_key=key(),
		)

	def confirm_funding(self, plan_reference: str, *, planner: str = fx.PLANNER) -> None:
		frappe.set_user(planner)
		plan = plan_read.get_annual_plan(plan_reference=plan_reference)
		requested = plan_finance.request_plan_funding_confirmation(
			plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		task = frappe.get_doc("Plan Finance Task", requested["task"])
		frappe.set_user(fx.FINANCE_OFFICER)
		plan_finance.confirm_plan_funding(task=task.name, task_token=task.task_token, idempotency_key=key())
		frappe.set_user(planner)

	def confirmed_item(self, *, indicative_amount: float = 1000000, planner: str = fx.PLANNER) -> tuple[dict, str]:
		accepted, item_id = self.formed_item(indicative_amount=indicative_amount)
		self.complete(item_id)
		self.confirm_funding(accepted["annual_plan"], planner=planner)
		return accepted, item_id

	def submit(self, plan_reference: str, *, actor: str = None):
		frappe.set_user(actor or fx.HOPF)  # v1.18 §6.2: Sign and submit Annual Plan
		plan = plan_read.get_annual_plan(plan_reference=plan_reference)
		return plan_governance.submit_consolidated_plan(
			plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=key(),
		)


class TestSubmitConsolidatedPlan(GovernanceCase):
	def test_submit_creates_the_ao_task_and_freezes_the_ten_column_snapshot(self):
		accepted, item_id = self.confirmed_item()
		result = self.submit(accepted["annual_plan"])
		self.assertEqual(result["action"], "submitted")
		task = frappe.get_doc("Plan Governance Task", result["task"])
		self.assertEqual(task.stage, "Accounting Officer adoption")
		self.assertEqual(task.status, "Open")
		version = frappe.get_doc("Annual Plan Version", task.plan_version)
		self.assertEqual(version.version_status, "Awaiting Accounting Officer")
		snapshot = json.loads(version.submitted_snapshot)
		self.assertEqual(len(snapshot["rows"]), 1)
		row = snapshot["rows"][0]
		self.assertEqual(row["plan_item_id"], item_id)
		self.assertEqual(row["funding"], "Within budget")
		self.assertEqual(row["reservation_category"], "None")
		self.assertEqual(row["procurement_method"], "Open Tender")
		self.assertIn("KES 1,000,000", row["value_display"])
		self.assertIn(snapshot["reservation_target_percent"], (0, None))  # the v1.18 test world publishes no annual target; the value is frozen as read
		# the frozen baseline is locked once the Version leaves Draft (invariant 12b)
		item = plan_read.get_plan_item(plan_item_id=item_id)
		self.assertTrue(item["baseline"]["locked"])
		frappe.set_user(fx.PLANNER)
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.save_plan_item(
				plan_item=item_id, values={"baseline_invitation_date": "2101-10-01"},
				expected_record_version=item["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_BASELINE_LOCKED")

	def test_submit_refuses_a_plan_without_current_funding_confirmation(self):
		accepted, item_id = self.formed_item()
		self.complete(item_id)
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.submit(accepted["annual_plan"])
		self.assertEqual(caught.exception.code, "PLN_FINANCE_STALE")

	def test_submit_refuses_an_unconfigured_statutory_route(self):
		accepted, item_id = self.confirmed_item()
		with patch.object(plan_governance, "statutory_route", return_value=""):
			with self.assertRaises(ProcurementPlanningError) as caught:
				self.submit(accepted["annual_plan"])
		self.assertEqual(caught.exception.code, "PLN_STATUTORY_ROUTE_UNCONFIGURED")


class TestPreparationSignature(GovernanceCase):
	"""PLN-CHG-001 v1.18 §6.2 / D6 — Sign and submit Annual Plan (PLN18-208)."""

	def test_the_head_of_procurement_function_signs_the_exact_snapshot(self):
		accepted, item_id = self.confirmed_item()
		frappe.set_user(fx.HOPF)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertTrue(plan["can_sign_and_submit"])
		self.assertFalse(plan["mutable"])  # the signer does not edit
		result = self.submit(accepted["annual_plan"])
		self.assertTrue(result["preparation_signature"])
		signature = frappe.get_doc("Plan Preparation Signature", result["preparation_signature"])
		version = frappe.get_doc("Annual Plan Version", accepted["annual_plan_version"])
		self.assertEqual(signature.actor, fx.HOPF)
		self.assertEqual(signature.capacity, "Head of Procurement Function")
		self.assertEqual(signature.snapshot_hash, version.snapshot_hash)
		self.assertEqual(signature.submitted_snapshot_id, version.submitted_snapshot_id)
		self.assertEqual(version.preparation_signature, signature.name)
		self.assertIn("assignment_id", signature.authority_snapshot)
		self.assertEqual(json.loads(version.source_cohort), [frappe.db.get_value("Plan Source Allocation", {"plan_item_id": item_id}, "source_key")])
		self.assertEqual(version.version_status, "Awaiting Accounting Officer")  # no extra HOPF approval state
		read = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertEqual(read["preparation_signature"]["actor"], fx.HOPF)

	def test_the_planner_cannot_sign_and_the_planner_offer_is_gone(self):
		accepted, item_id = self.confirmed_item()
		frappe.set_user(fx.PLANNER)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertFalse(plan["can_submit"])
		self.assertFalse(plan["can_sign_and_submit"])
		with self.assertRaises(frappe.DoesNotExistError):
			self.submit(accepted["annual_plan"], actor=fx.PLANNER)

	def test_the_signer_cannot_adopt_the_plan_they_signed(self):
		"""§6.4 — signing the formal submission is on the incompatible-action chain."""
		accepted, item_id = self.confirmed_item()
		submitted = self.submit(accepted["annual_plan"], actor=fx.HYBRID_HOPF_AO)
		ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
		frappe.set_user(fx.HYBRID_HOPF_AO)
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_governance.adopt_and_submit_plan(task=ao_task.name, task_token=ao_task.task_token, idempotency_key=key())
		self.assertEqual(caught.exception.code, "PLN_SEGREGATION_CONFLICT")
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		self.assertEqual(plan_governance.adopt_and_submit_plan(task=ao_task.name, task_token=ao_task.task_token, idempotency_key=key())["action"], "adopted")


class TestLateActivationExplanation(GovernanceCase):
	def test_an_initial_plan_adopted_after_the_year_began_needs_the_accounting_officers_explanation(self):
		"""v1.18 §4.7 / §7.2 — AO-owned, append-only, recorded at late adoption or later."""
		accepted, item_id = self.confirmed_item()
		submitted = self.submit(accepted["annual_plan"])
		ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		with patch.object(plan_governance, "nowdate", return_value="2101-08-01"):
			with self.assertRaises(ProcurementPlanningError) as caught:
				plan_governance.adopt_and_submit_plan(task=ao_task.name, task_token=ao_task.task_token, idempotency_key=key())
			self.assertEqual(caught.exception.code, "PLN_LATE_EXPLANATION_REQUIRED")
			adopted = plan_governance.adopt_and_submit_plan(
				task=ao_task.name, task_token=ao_task.task_token, idempotency_key=key(),
				late_activation_explanation="Consolidation waited for the supplementary budget approved in July 2101.",
			)
		self.assertTrue(adopted["late_activation_explanation"])
		first = frappe.get_doc("Late Activation Explanation", adopted["late_activation_explanation"])
		self.assertEqual(first.actor, fx.ACCOUNTING_OFFICER)
		corrected = plan_governance.record_late_activation_explanation(
			plan_version=accepted["annual_plan_version"], reason="Consolidation waited for the supplementary budget approved on 14 July 2101.",
			supersedes=first.name, idempotency_key=key(),
		)
		self.assertEqual(corrected["action"], "late_explanation_recorded")
		self.assertEqual(frappe.db.get_value("Late Activation Explanation", corrected["explanation"], "supersedes"), first.name)
		self.assertEqual(frappe.db.count("Late Activation Explanation", {"plan_version": accepted["annual_plan_version"]}), 2)  # append-only
		frappe.set_user(fx.STATUTORY)
		task = frappe.get_doc("Plan Governance Task", adopted["statutory_task"])
		read = plan_read.get_plan_governance_task(task=task.name)
		self.assertIn("14 July 2101", read["late_activation_reason"])
		self.assertEqual(len(read["late_activation_explanations"]), 2)


class TestAdoptApproveChain(GovernanceCase):
	def test_adopt_creates_the_statutory_task_and_approve_activates_the_plan(self):
		accepted, item_id = self.confirmed_item()
		submitted = self.submit(accepted["annual_plan"])
		ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])

		frappe.set_user(fx.ACCOUNTING_OFFICER)
		read = plan_read.get_plan_governance_task(task=ao_task.name)
		self.assertTrue(read["can_decide"])
		self.assertIn("Reserved share", read["advisory_line"])
		adopted = plan_governance.adopt_and_submit_plan(task=ao_task.name, task_token=ao_task.task_token, idempotency_key=key())
		self.assertEqual(adopted["action"], "adopted")
		statutory_task = frappe.get_doc("Plan Governance Task", adopted["statutory_task"])
		self.assertEqual(statutory_task.stage, "Statutory approval")
		self.assertEqual(statutory_task.capacity, "Responsible Cabinet Secretary")
		version = frappe.get_doc("Annual Plan Version", statutory_task.plan_version)
		self.assertEqual(version.version_status, "Awaiting statutory approval")

		frappe.set_user(fx.STATUTORY)
		read = plan_read.get_plan_governance_task(task=statutory_task.name)
		self.assertTrue(read["authority_card"]["ao_adoption_line"])
		self.assertFalse(read["authority_card"]["is_board"])
		approved = plan_governance.approve_annual_plan(task=statutory_task.name, task_token=statutory_task.task_token, idempotency_key=key())
		self.assertEqual(approved["action"], "approved")
		self.assertEqual(approved["publication_result"], "Acknowledged")
		self.assertEqual(frappe.db.get_value("Annual Plan Version", version.name, "version_status"), "Active")
		self.assertEqual(frappe.db.get_value("Annual Plan", accepted["annual_plan"], "active_version"), version.name)
		publication = frappe.get_doc("Annual Plan Publication", {"plan_version": version.name})
		self.assertEqual(publication.result, "Acknowledged")
		self.assertTrue(publication.external_reference)
		self.assertIn("Invitation to treat", publication.legal_character)
		# PLN-AC-123: forecasts seeded from baseline on activation
		item = plan_read.get_plan_item(plan_item_id=item_id)
		self.assertTrue(item["is_active"])
		for row in item["schedule"]:
			self.assertEqual(row["forecast"], row["baseline"])
			self.assertEqual(row["actual"], "")

	def test_a_board_route_requires_a_resolution_reference(self):
		single = frappe.get_doc("Site Procuring Entity")
		before = single.statutory_approval_route
		single.statutory_approval_route = "Board of Directors"
		single.save(ignore_permissions=True)

		def _restore():
			doc = frappe.get_doc("Site Procuring Entity")
			doc.statutory_approval_route = before
			doc.save(ignore_permissions=True)

		self.addCleanup(_restore)
		accepted, item_id = self.confirmed_item()
		submitted = self.submit(accepted["annual_plan"])
		ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		adopted = plan_governance.adopt_and_submit_plan(task=ao_task.name, task_token=ao_task.task_token, idempotency_key=key())
		statutory_task = frappe.get_doc("Plan Governance Task", adopted["statutory_task"])
		self.assertEqual(statutory_task.capacity, "Board of Directors")
		frappe.set_user(fx.STATUTORY)
		self.assertTrue(plan_read.get_plan_governance_task(task=statutory_task.name)["authority_card"]["is_board"])
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_governance.approve_annual_plan(task=statutory_task.name, task_token=statutory_task.task_token, idempotency_key=key())
		self.assertEqual(caught.exception.code, "PLN_COLLECTIVE_RESOLUTION_REQUIRED")  # v1.18 §8
		approved = plan_governance.approve_annual_plan(
			task=statutory_task.name, task_token=statutory_task.task_token, collective_resolution_reference="BOARD/RES/2101/07", idempotency_key=key(),
		)
		self.assertEqual(approved["action"], "approved")

	def test_a_council_route_is_a_collective_capacity_too(self):
		single = frappe.get_doc("Site Procuring Entity")
		before = single.statutory_approval_route
		single.statutory_approval_route = "Council"
		single.save(ignore_permissions=True)

		def _restore():
			doc = frappe.get_doc("Site Procuring Entity")
			doc.statutory_approval_route = before
			doc.save(ignore_permissions=True)

		self.addCleanup(_restore)
		accepted, item_id = self.confirmed_item()
		submitted = self.submit(accepted["annual_plan"])
		ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		adopted = plan_governance.adopt_and_submit_plan(task=ao_task.name, task_token=ao_task.task_token, idempotency_key=key())
		statutory_task = frappe.get_doc("Plan Governance Task", adopted["statutory_task"])
		self.assertEqual(statutory_task.capacity, "Council")
		self.assertTrue(plan_governance.is_collective_capacity(statutory_task.capacity))
		frappe.set_user(fx.STATUTORY)
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_governance.approve_annual_plan(task=statutory_task.name, task_token=statutory_task.task_token, idempotency_key=key())
		self.assertEqual(caught.exception.code, "PLN_COLLECTIVE_RESOLUTION_REQUIRED")
		approved = plan_governance.approve_annual_plan(
			task=statutory_task.name, task_token=statutory_task.task_token, collective_resolution_reference="COUNCIL/RES/2101/03", idempotency_key=key(),
		)
		self.assertEqual(approved["action"], "approved")
		decision = frappe.get_all("Plan Governance Decision", filters={"task": statutory_task.name}, fields=["collective_resolution_reference"])[0]
		self.assertEqual(decision.collective_resolution_reference, "COUNCIL/RES/2101/03")

	def test_a_non_accounting_officer_is_refused(self):
		accepted, item_id = self.confirmed_item()
		submitted = self.submit(accepted["annual_plan"])
		ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
		frappe.set_user(fx.PLANNER)
		with self.assertRaises(frappe.DoesNotExistError):
			plan_governance.adopt_and_submit_plan(task=ao_task.name, task_token=ao_task.task_token, idempotency_key=key())

	def test_hybrid_ao_planner_is_blocked_from_adopting_their_own_submission(self):
		# the hybrid drafted and requested Finance as Planner; the HOPF signs (v1.18 §6.2)
		accepted, item_id = self.confirmed_item(planner=fx.HYBRID_AO)
		submitted = self.submit(accepted["annual_plan"])
		ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
		frappe.set_user(fx.HYBRID_AO)
		self.assertFalse(plan_read.get_plan_governance_task(task=ao_task.name)["can_decide"])
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_governance.adopt_and_submit_plan(task=ao_task.name, task_token=ao_task.task_token, idempotency_key=key())
		self.assertEqual(caught.exception.code, "PLN_SEGREGATION_CONFLICT")

	def test_the_ao_adopter_cannot_also_approve(self):
		accepted, item_id = self.confirmed_item()
		submitted = self.submit(accepted["annual_plan"])
		ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
		frappe.set_user(fx.HYBRID_AO)
		adopted = plan_governance.adopt_and_submit_plan(task=ao_task.name, task_token=ao_task.task_token, idempotency_key=key())
		statutory_task = frappe.get_doc("Plan Governance Task", adopted["statutory_task"])
		frappe.set_user(fx.HYBRID_AO)
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_governance.approve_annual_plan(task=statutory_task.name, task_token=statutory_task.task_token, idempotency_key=key())
		self.assertEqual(caught.exception.code, "PLN_SEGREGATION_CONFLICT")

	def test_the_finance_confirmer_cannot_adopt(self):
		"""§6.1 — confirm funding, then adopt, on one evidence chain."""
		accepted, item_id = self.formed_item()
		self.complete(item_id)
		frappe.set_user(fx.PLANNER)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		requested = plan_finance.request_plan_funding_confirmation(
			plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		task = frappe.get_doc("Plan Finance Task", requested["task"])
		frappe.set_user(fx.HYBRID_AO)
		fx._grant(fx.HYBRID_AO, "Finance Confirmation Officer")
		plan_finance.confirm_plan_funding(task=task.name, task_token=task.task_token, idempotency_key=key())
		submitted = self.submit(accepted["annual_plan"])
		ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
		frappe.set_user(fx.HYBRID_AO)
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_governance.adopt_and_submit_plan(task=ao_task.name, task_token=ao_task.task_token, idempotency_key=key())
		self.assertEqual(caught.exception.code, "PLN_SEGREGATION_CONFLICT")


class TestCorrectionCohort(GovernanceCase):
	def test_a_correction_cannot_absorb_an_unrelated_later_source(self):
		"""v1.18 §5.4.2 — the returned Version's stable source cohort is fixed."""
		accepted, item_id = self.confirmed_item()
		submitted = self.submit(accepted["annual_plan"])
		ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		returned = plan_governance.return_plan_version(task=ao_task.name, reason="Re-scope the package before resubmission.", task_token=ao_task.task_token, idempotency_key=key())
		correction = frappe.get_doc("Annual Plan Version", returned["correction_version"])
		self.assertEqual(json.loads(correction.source_cohort), json.loads(frappe.db.get_value("Annual Plan Version", accepted["annual_plan_version"], "source_cohort")))
		# a different department's accepted requirement arrives while the correction is open
		frappe.set_user(fx.OUTSIDER)
		opened = dpp_lifecycle.open_departmental_plan(organisation_unit=fx.OU_BETA, fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS)
		added = dpp_lifecycle.save_direct_requirement(dpp_version=opened["current_version"], values=fx.direct_values(title="A later unrelated requirement"), expected_record_version=opened["record_version"], idempotency_key=key())
		frappe.set_user("Administrator")
		fx._grant(fx.OUTSIDER, "Head of User Department", fx.OU_BETA)
		frappe.set_user(fx.OUTSIDER)
		later = dpp_lifecycle.submit_departmental_plan(dpp_version=opened["current_version"], certification_confirmed=True, expected_record_version=added["record_version"], idempotency_key=key())
		task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": later["task"]})
		frappe.set_user(fx.PLANNER)
		dpp_validation.accept_departmental_plan(task=task.name, classifications={added["entry_id"]: "Goods"}, task_token=task.task_token, idempotency_key=key())
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		stranger = next(row["dpp_entry"] for row in plan["unallocated_sources"] if row["title"] == "A later unrelated requirement")
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.form_plan_items(plan_version=correction.name, dpp_entries=[stranger], mode="each", expected_record_version=plan["record_version"], idempotency_key=key())
		self.assertEqual(caught.exception.code, "PLN_CORRECTION_COHORT_VIOLATION")


class TestReturnPlanVersion(GovernanceCase):
	def test_ao_return_preserves_the_submission_and_carries_the_confirmation_forward(self):
		accepted, item_id = self.confirmed_item()
		submitted = self.submit(accepted["annual_plan"])
		ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_governance.return_plan_version(task=ao_task.name, reason="", task_token=ao_task.task_token, idempotency_key=key())
		self.assertEqual(caught.exception.code, "PLN_ENTRY_INCOMPLETE")

		result = plan_governance.return_plan_version(
			task=ao_task.name, reason="Confirm the planned contract-signing date against the delivery completion date.",
			task_token=ao_task.task_token, idempotency_key=key(),
		)
		self.assertEqual(result["action"], "returned")
		submitted_version = frappe.get_doc("Annual Plan Version", ao_task.plan_version)
		self.assertEqual(submitted_version.version_status, "Returned")
		self.assertTrue(submitted_version.submitted_snapshot)

		correction = frappe.get_doc("Annual Plan Version", result["correction_version"])
		self.assertEqual(correction.version_status, "Draft")
		self.assertEqual(correction.correction_of_plan_version, submitted_version.name)
		self.assertEqual(correction.version_number, submitted_version.version_number + 1)
		# PLN-AC-087 — the unchanged plan carries its confirmation forward
		self.assertEqual(correction.funding_state, "Confirmed")
		corrected_item = frappe.get_doc("Annual Plan Item", {"plan_version": correction.name, "plan_item_id": item_id})
		self.assertEqual(corrected_item.item_state, "Draft")
		self.assertEqual(str(corrected_item.baseline_invitation_date), "2101-09-01")
		self.assertFalse(corrected_item.forecast_invitation_date)
		self.assertEqual(frappe.db.get_value("Annual Plan", accepted["annual_plan"], "open_successor_version"), correction.name)
		frappe.set_user(fx.PLANNER)
		read = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertTrue(read["is_correction"])
		frappe.set_user(fx.HOPF)
		self.assertTrue(plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])["can_sign_and_submit"])

	def test_statutory_return_restarts_at_ao_on_resubmission(self):
		accepted, item_id = self.confirmed_item()
		submitted = self.submit(accepted["annual_plan"])
		ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		adopted = plan_governance.adopt_and_submit_plan(task=ao_task.name, task_token=ao_task.task_token, idempotency_key=key())
		statutory_task = frappe.get_doc("Plan Governance Task", adopted["statutory_task"])
		frappe.set_user(fx.STATUTORY)
		returned = plan_governance.return_plan_version(
			task=statutory_task.name, reason="Correct the procurement package description before the Plan is resubmitted.",
			task_token=statutory_task.task_token, idempotency_key=key(),
		)
		correction = frappe.get_doc("Annual Plan Version", returned["correction_version"])
		self.assertEqual(correction.version_status, "Draft")

		frappe.set_user(fx.HOPF)  # v1.18 §6.2: Sign and submit Annual Plan
		resubmitted = plan_governance.submit_corrected_plan(
			plan_version=correction.name, expected_record_version=correction.record_version, idempotency_key=key(),
		)
		self.assertEqual(resubmitted["action"], "submitted")
		new_ao_task = frappe.get_doc("Plan Governance Task", resubmitted["task"])
		self.assertEqual(new_ao_task.stage, "Accounting Officer adoption")
		self.assertEqual(frappe.db.get_value("Annual Plan Version", correction.name, "version_status"), "Awaiting Accounting Officer")

	def test_a_corrected_plan_with_changed_totals_repeats_finance(self):
		"""PLN-AC-087 — Finance repeats only when the per-line totals changed."""
		accepted, item_id = self.confirmed_item()
		submitted = self.submit(accepted["annual_plan"])
		ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		returned = plan_governance.return_plan_version(
			task=ao_task.name, reason="Re-scope the package before resubmission.", task_token=ao_task.task_token, idempotency_key=key(),
		)
		correction = frappe.get_doc("Annual Plan Version", returned["correction_version"])
		frappe.set_user(fx.PLANNER)
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.dissolve_plan_item(plan_item=item_id, expected_record_version=item["record_version"], idempotency_key=key())
		self.assertEqual(frappe.db.get_value("Annual Plan Version", correction.name, "funding_state"), "Stale")
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		reformed = plan_workbench.form_plan_items(
			plan_version=correction.name, dpp_entries=[plan["unallocated_sources"][0]["dpp_entry"]],
			mode="each", expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		self.complete(reformed["created_items"][0])
		correction.reload()
		frappe.set_user(fx.HOPF)  # v1.18 §6.2: Sign and submit Annual Plan
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_governance.submit_corrected_plan(
				plan_version=correction.name, expected_record_version=correction.record_version, idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_FINANCE_STALE")
		# v1.18 §5.3.2 — the same source re-formed leaves every per-line amount
		# unchanged: the earlier confirmation is reused, no second review
		frappe.set_user(fx.PLANNER)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		reused = plan_finance.request_plan_funding_confirmation(plan_version=correction.name, expected_record_version=plan["record_version"], idempotency_key=key())
		self.assertEqual(reused["action"], "confirmation_reused")
		frappe.set_user(fx.HOPF)
		correction.reload()
		resubmitted = plan_governance.submit_corrected_plan(
			plan_version=correction.name, expected_record_version=correction.record_version, idempotency_key=key(),
		)
		self.assertEqual(resubmitted["action"], "submitted")

	def test_a_corrected_plan_whose_financial_basis_changed_needs_a_new_finance_review(self):
		"""v1.18 §5.3.2/§5.3.4 — a changed approved amount changes the basis; the correction repeats Finance."""
		accepted, item_id = self.confirmed_item()
		submitted = self.submit(accepted["annual_plan"])
		ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		returned = plan_governance.return_plan_version(
			task=ao_task.name, reason="Re-scope the package before resubmission.", task_token=ao_task.task_token, idempotency_key=key(),
		)
		correction = frappe.get_doc("Annual Plan Version", returned["correction_version"])
		line_version = frappe.db.get_value("Procurement Budget Line Version", {"budget_line": fx.BUDGET_LINE, "budget_version": ("in", frappe.get_all("Procurement Budget Version", filters={"status": "Active"}, pluck="name"))}, "name")
		previous = frappe.db.get_value("Procurement Budget Line Version", line_version, "approved_amount")
		frappe.db.set_value("Procurement Budget Line Version", line_version, "approved_amount", 90_000_000, update_modified=False)
		self.addCleanup(frappe.db.set_value, "Procurement Budget Line Version", line_version, "approved_amount", previous, update_modified=False)
		frappe.set_user(fx.HOPF)  # v1.18 §6.2: Sign and submit Annual Plan
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_governance.submit_corrected_plan(plan_version=correction.name, expected_record_version=correction.record_version, idempotency_key=key())
		self.assertEqual(caught.exception.code, "PLN_FINANCE_STALE")
		frappe.set_user(fx.PLANNER)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		requested = plan_finance.request_plan_funding_confirmation(plan_version=correction.name, expected_record_version=plan["record_version"], idempotency_key=key())
		self.assertEqual(requested["action"], "requested")
		task = frappe.get_doc("Plan Finance Task", requested["task"])
		frappe.set_user(fx.FINANCE_OFFICER)
		plan_finance.confirm_plan_funding(task=task.name, task_token=task.task_token, idempotency_key=key())
		frappe.set_user(fx.HOPF)
		correction.reload()
		resubmitted = plan_governance.submit_corrected_plan(plan_version=correction.name, expected_record_version=correction.record_version, idempotency_key=key())
		self.assertEqual(resubmitted["action"], "submitted")
