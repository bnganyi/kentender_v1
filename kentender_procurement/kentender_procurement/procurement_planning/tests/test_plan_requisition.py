# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §5.4.5/§5.4.6/§7.4/§8.2 Requisition eligibility, drawdown,
scope lock and correction-lifecycle tests (Phase 2g, plan D9): the published
contract a sibling Requisitions module calls (`GetRequisitionEligiblePlanItem.v2`,
`AuthoriseRequisitionDrawdown`, `ReverseRequisitionDrawdown`, the correction
Receive/Start/Resolve/Close commands). Every test synthesises REQ-shaped
inputs (`requisition_reference`, a minimal `Procurement Requisition` root
where `Resolve`/`Close without change` must call back into it) rather than
depending on Requisitions' own, heavier fixtures — this file is not that
module's own test suite."""

from __future__ import annotations

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
	plan_requisition,
	plan_workbench,
	publication_pipeline,
	scope_lock,
	treasury,
)
from kentender_procurement.procurement_planning.tests import fixtures as fx


def key() -> str:
	return uuid4().hex


class RequisitionCase(IntegrationTestCase):
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
		needs_patch = patch.object(needs_intake, "current_accepted_sources", return_value=[])
		needs_patch.start()
		self.addCleanup(needs_patch.stop)
		eligible_patch = patch.object(
			budget_gateway, "eligible_line_ids", return_value={fx.BUDGET_LINE, fx.BUDGET_LINE_2}
		)
		eligible_patch.start()
		self.addCleanup(eligible_patch.stop)

	def complete_and_confirm(self, item_id: str, **value_overrides) -> None:
		frappe.set_user(fx.PLANNER)
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.save_plan_item(
			plan_item=item_id, values=fx.item_values(**value_overrides),
			expected_record_version=item["record_version"], idempotency_key=key(),
		)
		plan_reference = item["plan_reference"]
		plan = plan_read.get_annual_plan(plan_reference=plan_reference)
		requested = plan_finance.request_plan_funding_confirmation(
			plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		task = frappe.get_doc("Plan Finance Task", requested["task"])
		frappe.set_user(fx.FINANCE_OFFICER)
		plan_finance.confirm_plan_funding(task=task.name, task_token=task.task_token, idempotency_key=key())
		frappe.set_user(fx.PLANNER)

	def confirmed_item(self, *, indicative_amount: float = 1000000) -> tuple[dict, str]:
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			organisation_unit=fx.OU_ALPHA,
			fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
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
		self.complete_and_confirm(item_id)
		return accepted, item_id

	def activate(self, plan_reference: str) -> dict:
		"""§5.5.2 (plan D8): approve only commits; Treasury evidence gates the
		worker; the worker runs inline here (no RQ worker on this bench)."""
		frappe.set_user(fx.PLANNER)
		plan = plan_read.get_annual_plan(plan_reference=plan_reference)
		frappe.set_user(fx.HOPF)  # v1.18 §6.2: the Head of Procurement Function signs and submits
		submitted = plan_governance.submit_consolidated_plan(
			plan_version=plan["version_reference"], expected_record_version=plan["record_version"],
			idempotency_key=key(),
		)
		ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		adopted = plan_governance.adopt_and_submit_plan(
			task=ao_task.name, task_token=ao_task.task_token, idempotency_key=key(),
		)
		statutory_task = frappe.get_doc("Plan Governance Task", adopted["statutory_task"])
		frappe.set_user(fx.STATUTORY)
		approved = plan_governance.approve_annual_plan(
			task=statutory_task.name, task_token=statutory_task.task_token, idempotency_key=key(),
		)
		version_name = frappe.db.get_value("Plan Publication", approved["publication"], "plan_version")
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		treasury.record_treasury_submission(
			plan_version=version_name, submitted_at="2101-11-01 09:00:00", channel="Email", destination="treasury@example.test",
			dispatch_reference="MOH/APP/2101/001", exact_document_confirmed=True, idempotency_key=key(),
		)
		frappe.set_user("Administrator")
		published = publication_pipeline.publish_annual_plan(plan_version=version_name, idempotency_key=key())
		frappe.set_user(fx.PLANNER)
		return published

	def active_item(self, *, indicative_amount: float = 1000000) -> tuple[dict, str]:
		accepted, item_id = self.confirmed_item(indicative_amount=indicative_amount)
		self.activate(accepted["annual_plan"])
		return accepted, item_id

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

	def correcting_active_version(self, plan_reference: str) -> str:
		"""An ordinary successor, carried to Active, standing in for
		§5.4.5's "correcting Active Plan Version" — same stable
		`plan_item_id`, a fresh Version name, per §5.4.4's stable-identity
		carry-forward."""
		frappe.set_user(fx.PLANNER)
		plan_publication.begin_plan_update(plan_reference=plan_reference, idempotency_key=key())
		self.confirm_funding(plan_reference)
		self.activate(plan_reference)
		return frappe.db.get_value("Annual Plan", {"plan_reference": plan_reference}, "active_version")

	def allocation_id_of(self, item_id: str) -> str:
		item_name = plan_read.resolve_item_doc_name(item_id)
		return frappe.db.get_value(
			"Plan Source Allocation", {"plan_item": item_name, "allocation_state": "Active"}, "allocation_id"
		)


class TestEligibility(RequisitionCase):
	def test_a_freshly_activated_item_is_eligible_at_its_full_balance(self):
		accepted, item_id = self.active_item(indicative_amount=1000000)
		read = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)
		self.assertTrue(read["eligible"])
		self.assertEqual(read["plan_reference"], accepted["annual_plan"])
		self.assertEqual(read["total_value"], 1000000)
		self.assertEqual(read["remaining_value"], 1000000)
		self.assertEqual(len(read["sources"]), 1)
		source = read["sources"][0]
		self.assertEqual(source["remaining_quantity"], source["approved_quantity"])
		self.assertEqual(source["remaining_amount"], 1000000)
		self.assertTrue(read["funding_confirmation_references"])
		self.assertTrue(read["evaluated_at"])

	def test_a_draft_item_never_activated_is_not_eligible(self):
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			organisation_unit=fx.OU_ALPHA,
			fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
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
		item_id = formed["created_items"][0]
		read = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)
		self.assertFalse(read["eligible"])
		self.assertEqual(read["remaining_value"], 0)

	def test_active_but_no_longer_current_funding_is_not_eligible(self):
		"""§7.4's own "Finance evidence remains current" condition — proven by
		direct DB construction on the Version's plan-level funding state."""
		accepted, item_id = self.active_item()
		name = plan_read.resolve_item_doc_name(item_id)
		version = frappe.db.get_value("Annual Plan Item", name, "plan_version")
		frappe.db.set_value("Annual Plan Version", version, "funding_state", "Stale", update_modified=False)
		read = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)
		self.assertFalse(read["eligible"])
		frappe.db.set_value("Annual Plan Version", version, "funding_state", "Confirmed", update_modified=False)


class TestDrawdownAndReversal(RequisitionCase):
	def read_as_planner(self, item_id: str) -> dict:
		"""The published read is Planner/Auditor-scoped (like every other
		Planning read); the drawdown commands below are System-Manager-gated
		(no Requisitions role exists to authorise against, finding —). The
		two identities are deliberately different, so every helper here is
		explicit about which one it needs and leaves `frappe.session.user`
		set to `fx.PLANNER` on return, ready for the next read."""
		frappe.set_user(fx.PLANNER)
		return plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)

	def record(self, item_id: str, allocation_id: str, *, quantity: float, amount: float, ref: str = None):
		read = self.read_as_planner(item_id)
		frappe.set_user(fx.HOPF)
		return plan_requisition.authorise_requisition_drawdown(
			plan_item_id=item_id, requisition_reference=ref or f"REQ-{key()[:8]}",
			requesting_org_unit=fx.OU_ALPHA,
			allocations=[{"plan_source_allocation_id": allocation_id, "quantity": quantity, "amount": amount}],
			expected_record_version=read["record_version"], idempotency_key=key(),
		)

	def test_sequential_partial_drawdowns_reduce_the_remaining_balance(self):
		accepted, item_id = self.active_item(indicative_amount=1000000)
		allocation_id = self.allocation_id_of(item_id)

		first = self.record(item_id, allocation_id, quantity=0.4, amount=400000)
		self.assertEqual(first["action"], "recorded")
		read = self.read_as_planner(item_id)
		self.assertTrue(read["eligible"])
		self.assertAlmostEqual(read["remaining_value"], 600000)

		second = self.record(item_id, allocation_id, quantity=0.6, amount=600000)
		self.assertEqual(second["action"], "recorded")
		read = self.read_as_planner(item_id)
		self.assertFalse(read["eligible"])
		self.assertAlmostEqual(read["remaining_value"], 0)
		self.assertAlmostEqual(read["remaining_quantity"], 0)

	def test_a_drawdown_exceeding_the_balance_is_refused_and_creates_nothing(self):
		accepted, item_id = self.active_item(indicative_amount=1000000)
		allocation_id = self.allocation_id_of(item_id)
		with self.assertRaises(frappe.ValidationError):
			self.record(item_id, allocation_id, quantity=2, amount=1500000)
		self.assertEqual(
			frappe.db.count("Plan Drawdown Reference", {"plan_item_id": item_id}), 0
		)
		read = self.read_as_planner(item_id)
		self.assertAlmostEqual(read["remaining_value"], 1000000)

	def test_a_combined_items_all_or_none_atomicity_across_two_allocations(self):
		"""One allocation's request is fine on its own; the other's exceeds
		its own balance — neither may draw (§7.4: 'atomic ... cannot exceed
		either the source row or Plan Item balance'), proven directly against
		this repo's own two-pass validate-then-write design rather than
		relying on request-level rollback no direct Python call goes through."""
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			organisation_unit=fx.OU_ALPHA,
			fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)
		added_a = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"],
			values=fx.direct_values(title="Combined A", budget_line=fx.BUDGET_LINE, indicative_amount=500000),
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		added_b = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"],
			values=fx.direct_values(title="Combined B", budget_line=fx.BUDGET_LINE_2, indicative_amount=500000),
			expected_record_version=added_a["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.HOD)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True,
			expected_record_version=added_b["record_version"], idempotency_key=key(),
		)
		task = frappe.get_doc(
			"Departmental Plan Validation Task", {"task_reference": submitted["task"]}
		)
		frappe.set_user(fx.PLANNER)
		accepted = dpp_validation.accept_departmental_plan(
			task=task.name,
			classifications={added_a["entry_id"]: "Goods", added_b["entry_id"]: "Goods"},
			task_token=task.task_token, idempotency_key=key(),
		)
		entry_a = frappe.db.get_value(
			"Departmental Plan Entry",
			{"dpp_version": opened["current_version"], "entry_id": added_a["entry_id"]}, "name",
		)
		entry_b = frappe.db.get_value(
			"Departmental Plan Entry",
			{"dpp_version": opened["current_version"], "entry_id": added_b["entry_id"]}, "name",
		)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		formed = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"], dpp_entries=[entry_a, entry_b],
			mode="combined", expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		item_id = formed["created_items"][0]
		self.complete_and_confirm(
			item_id, aggregation_reason="Both laptop batches ship in a single combined tender lot.",
			aggregation_indicator="Aggregated into this package",
		)
		self.activate(accepted["annual_plan"])

		read = self.read_as_planner(item_id)
		self.assertEqual(len(read["sources"]), 2)
		ids = [s["plan_source_allocation_id"] for s in read["sources"]]

		frappe.set_user(fx.HOPF)
		with self.assertRaises(frappe.ValidationError):
			plan_requisition.authorise_requisition_drawdown(
				plan_item_id=item_id, requisition_reference=f"REQ-{key()[:8]}",
				requesting_org_unit=fx.OU_ALPHA,
				allocations=[
					{"plan_source_allocation_id": ids[0], "quantity": 0.1, "amount": 100000},
					{"plan_source_allocation_id": ids[1], "quantity": 0.9, "amount": 900000},
				],
				expected_record_version=read["record_version"], idempotency_key=key(),
			)
		self.assertEqual(
			frappe.db.count("Plan Drawdown Reference", {"plan_item_id": item_id}), 0
		)

	def test_reversal_restores_the_balance_and_is_refused_a_second_time(self):
		accepted, item_id = self.active_item(indicative_amount=1000000)
		allocation_id = self.allocation_id_of(item_id)
		recorded = self.record(item_id, allocation_id, quantity=1, amount=1000000)
		drawdown = recorded["drawdown_references"][0]

		read = self.read_as_planner(item_id)
		self.assertFalse(read["eligible"])

		frappe.set_user(fx.HOPF)
		reversed_result = plan_requisition.reverse_requisition_drawdown(
			drawdown_reference=drawdown["drawdown_reference"],
			expected_record_version=drawdown["record_version"], idempotency_key=key(),
		)
		self.assertEqual(reversed_result["action"], "reversed")
		self.assertEqual(
			frappe.db.get_value("Plan Drawdown Reference", drawdown["drawdown_reference"], "drawdown_state"),
			"Reversed",
		)
		read = self.read_as_planner(item_id)
		self.assertTrue(read["eligible"])
		self.assertAlmostEqual(read["remaining_value"], 1000000)

		frappe.set_user(fx.HOPF)
		with self.assertRaises(frappe.ValidationError):
			plan_requisition.reverse_requisition_drawdown(
				drawdown_reference=drawdown["drawdown_reference"],
				expected_record_version=1, idempotency_key=key(),
			)

	def test_idempotent_replay_of_record_and_reverse(self):
		accepted, item_id = self.active_item(indicative_amount=1000000)
		allocation_id = self.allocation_id_of(item_id)
		read = self.read_as_planner(item_id)
		frappe.set_user(fx.HOPF)
		record_key = key()
		args = dict(
			plan_item_id=item_id, requisition_reference="REQ-REPLAY-1", requesting_org_unit=fx.OU_ALPHA,
			allocations=[{"plan_source_allocation_id": allocation_id, "quantity": 0.5, "amount": 500000}],
			expected_record_version=read["record_version"], idempotency_key=record_key,
		)
		first = plan_requisition.authorise_requisition_drawdown(**args)
		second = plan_requisition.authorise_requisition_drawdown(**args)
		self.assertEqual(first["drawdown_references"], second["drawdown_references"])
		self.assertEqual(frappe.db.count("Plan Drawdown Reference", {"plan_item_id": item_id}), 1)
		self.assertFalse(first["idempotent"])
		self.assertTrue(second["idempotent"])

		drawdown = first["drawdown_references"][0]
		reverse_key = key()
		reverse_args = dict(
			drawdown_reference=drawdown["drawdown_reference"],
			expected_record_version=drawdown["record_version"], idempotency_key=reverse_key,
		)
		r1 = plan_requisition.reverse_requisition_drawdown(**reverse_args)
		r2 = plan_requisition.reverse_requisition_drawdown(**reverse_args)
		self.assertEqual(r1["reversal_reference"], r2["reversal_reference"])
		self.assertFalse(r1["idempotent"])
		self.assertTrue(r2["idempotent"])

	def test_a_plain_planner_is_refused_record_and_reverse(self):
		accepted, item_id = self.active_item()
		allocation_id = self.allocation_id_of(item_id)
		frappe.set_user(fx.PLANNER)
		with self.assertRaises(frappe.DoesNotExistError):
			plan_requisition.authorise_requisition_drawdown(
				plan_item_id=item_id, requisition_reference=f"REQ-{key()[:8]}",
				requesting_org_unit=fx.OU_ALPHA,
				allocations=[{"plan_source_allocation_id": allocation_id, "quantity": 0.1, "amount": 100000}],
				expected_record_version=0, idempotency_key=key(),
			)

		recorded = self.record(item_id, allocation_id, quantity=0.1, amount=100000)
		drawdown = recorded["drawdown_references"][0]
		frappe.set_user(fx.PLANNER)
		with self.assertRaises(frappe.DoesNotExistError):
			plan_requisition.reverse_requisition_drawdown(
				drawdown_reference=drawdown["drawdown_reference"],
				expected_record_version=drawdown["record_version"], idempotency_key=key(),
			)


class TestProjectionFieldCompleteness(RequisitionCase):
	def test_every_req_chg_001_v16_field_is_present(self):
		"""REQ-AC-056 — every field REQ-CHG-001 v1.6 §5.1/§5A depends on is
		explicitly enumerated in the projection; none is left to a second,
		undocumented query back into Planning."""
		accepted, item_id = self.active_item(indicative_amount=1000000)
		read = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)
		for field in (
			"title", "reservation_category", "lotting_indicator", "lot_count", "plan_horizon",
			"contributing_org_unit_ids", "strategic_objective_path",
			"currency", "award_packages",
		):
			self.assertIn(field, read, f"{field} missing from the projection")
		self.assertEqual(read["currency"], "KES")
		self.assertEqual(read["award_packages"], 1)
		self.assertEqual(read["contributing_org_unit_ids"], [fx.OU_ALPHA])
		self.assertEqual(read["strategic_objective_path"], read["objective_path"])
		for source in read["sources"]:
			self.assertIn("plan_item_line_id", source)
			self.assertIn("source_line_id", source)
			self.assertEqual(source["plan_item_line_id"], source["plan_source_allocation_id"])
			self.assertTrue(source["source_line_id"])

	def test_contributing_org_unit_ids_deduplicates_across_two_allocations_in_one_unit(self):
		"""The combined-item fixture's two sources both belong to OU_ALPHA
		(this repo's DPP-level fixture has no second-department combine
		recipe); the aggregate must still be a de-duplicated sorted list of
		one, not a two-element list repeating the same unit."""
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			organisation_unit=fx.OU_ALPHA,
			fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)
		added_a = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"],
			values=fx.direct_values(title="Dedup A", budget_line=fx.BUDGET_LINE, indicative_amount=500000),
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		added_b = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"],
			values=fx.direct_values(title="Dedup B", budget_line=fx.BUDGET_LINE_2, indicative_amount=500000),
			expected_record_version=added_a["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.HOD)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True,
			expected_record_version=added_b["record_version"], idempotency_key=key(),
		)
		task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
		frappe.set_user(fx.PLANNER)
		accepted = dpp_validation.accept_departmental_plan(
			task=task.name,
			classifications={added_a["entry_id"]: "Goods", added_b["entry_id"]: "Goods"},
			task_token=task.task_token, idempotency_key=key(),
		)
		entry_a = frappe.db.get_value("Departmental Plan Entry", {"dpp_version": opened["current_version"], "entry_id": added_a["entry_id"]}, "name")
		entry_b = frappe.db.get_value("Departmental Plan Entry", {"dpp_version": opened["current_version"], "entry_id": added_b["entry_id"]}, "name")
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		formed = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"], dpp_entries=[entry_a, entry_b],
			mode="combined", expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		item_id = formed["created_items"][0]
		self.complete_and_confirm(item_id, aggregation_reason="Same-unit combine for the dedup test.", aggregation_indicator="Aggregated into this package")
		self.activate(accepted["annual_plan"])
		frappe.set_user(fx.PLANNER)
		read = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)
		self.assertEqual(len(read["sources"]), 2)
		self.assertEqual(read["contributing_org_unit_ids"], [fx.OU_ALPHA])


class TestRequisitionCallerReadGate(RequisitionCase):
	def test_head_of_procurement_function_may_read(self):
		accepted, item_id = self.active_item()
		frappe.set_user(fx.HOPF)
		read = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)
		self.assertTrue(read["eligible"])

	def test_departmental_author_of_a_contributing_unit_may_read(self):
		accepted, item_id = self.active_item()
		frappe.set_user(fx.AUTHOR)  # OU_ALPHA — the item's own contributing unit
		read = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)
		self.assertTrue(read["eligible"])

	def test_departmental_author_of_an_unrelated_unit_is_refused(self):
		"""OUTSIDER holds Departmental Author on OU_BETA only — never one of
		this item's contributing units."""
		accepted, item_id = self.active_item()
		frappe.set_user(fx.OUTSIDER)
		with self.assertRaises(frappe.DoesNotExistError):
			plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)


class TestListRequisitionEligiblePlanItems(RequisitionCase):
	"""REQ-CHG-001 v1.6 §10.1 `GetRequisitionWorkspace`'s eligible-item list."""

	def test_hopf_sees_the_eligible_item_site_wide(self):
		accepted, item_id = self.active_item()
		frappe.set_user(fx.HOPF)
		rows = plan_requisition.list_requisition_eligible_plan_items()
		self.assertIn(item_id, [r["plan_item_id"] for r in rows])
		row = next(r for r in rows if r["plan_item_id"] == item_id)
		self.assertEqual(row["contributing_org_unit_ids"], [fx.OU_ALPHA])
		self.assertGreater(row["remaining_value"], 0)

	def test_author_of_a_contributing_unit_sees_it_too(self):
		accepted, item_id = self.active_item()
		frappe.set_user(fx.AUTHOR)
		rows = plan_requisition.list_requisition_eligible_plan_items()
		self.assertIn(item_id, [r["plan_item_id"] for r in rows])

	def test_author_of_an_unrelated_unit_does_not_see_it(self):
		accepted, item_id = self.active_item()
		frappe.set_user(fx.OUTSIDER)  # Departmental Author on OU_BETA only
		rows = plan_requisition.list_requisition_eligible_plan_items()
		self.assertNotIn(item_id, [r["plan_item_id"] for r in rows])

	def test_an_item_with_no_remaining_balance_is_excluded(self):
		accepted, item_id = self.active_item(indicative_amount=1_000_000)
		read = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)
		allocation = read["sources"][0]
		frappe.set_user(fx.HOPF)
		plan_requisition.authorise_requisition_drawdown(
			plan_item_id=item_id, requisition_reference="REQ-EXHAUST-001", requesting_org_unit=fx.OU_ALPHA,
			allocations=[{"plan_source_allocation_id": allocation["plan_source_allocation_id"], "quantity": allocation["remaining_quantity"], "amount": allocation["remaining_amount"]}],
			expected_record_version=read["record_version"], idempotency_key=key(),
		)
		rows = plan_requisition.list_requisition_eligible_plan_items()
		self.assertNotIn(item_id, [r["plan_item_id"] for r in rows])


class TestPlanItemCorrectionRequest(RequisitionCase):
	"""REQ-CHG-001 v1.6 §7.4A — the inbound half of a Requisition's
	upstream-correction route."""

	def test_head_of_user_department_of_a_contributing_unit_may_request(self):
		accepted, item_id = self.active_item()
		item_name = plan_read.resolve_item_doc_name(item_id)
		frappe.set_user(fx.HOD)  # OU_ALPHA — the item's own contributing unit
		result = plan_requisition.receive_plan_item_correction_request(
			plan_item_id=item_id, requisition_reference="REQ-TEST-CORR-1", requisition_version="RQV-TEST-1",
			reason="The authorised warranty period does not match the department's actual need.",
			idempotency_key=key(),
		)
		self.assertTrue(result["ok"])
		self.assertEqual(result["status"], "Open")
		doc = frappe.get_doc("Plan Item Correction Request", result["correction_request"])
		self.assertEqual(doc.plan_item, item_name)
		self.assertEqual(doc.requested_role, "Head of User Department")
		self.assertEqual(doc.status, "Open")

	def test_head_of_procurement_function_may_request(self):
		accepted, item_id = self.active_item()
		frappe.set_user(fx.HOPF)
		result = plan_requisition.receive_plan_item_correction_request(
			plan_item_id=item_id, requisition_reference="REQ-TEST-CORR-2", requisition_version="RQV-TEST-2",
			reason="The Plan Item's Strategic Objective is materially wrong for this request.",
			idempotency_key=key(),
		)
		doc = frappe.get_doc("Plan Item Correction Request", result["correction_request"])
		self.assertEqual(doc.requested_role, "Head of Procurement Function")

	def test_an_unrelated_department_head_is_refused(self):
		accepted, item_id = self.active_item()
		frappe.set_user(fx.OUTSIDER)  # HoD-equivalent authority does not exist for OUTSIDER at all — Author only, OU_BETA
		with self.assertRaises(frappe.DoesNotExistError):
			plan_requisition.receive_plan_item_correction_request(
				plan_item_id=item_id, requisition_reference="REQ-TEST-CORR-3", requisition_version="RQV-TEST-3",
				reason="An unrelated actor attempting a correction request should be refused outright.",
				idempotency_key=key(),
			)

	def test_a_short_reason_is_rejected(self):
		accepted, item_id = self.active_item()
		frappe.set_user(fx.HOD)
		with self.assertRaises(frappe.ValidationError):
			plan_requisition.receive_plan_item_correction_request(
				plan_item_id=item_id, requisition_reference="REQ-TEST-CORR-4", requisition_version="RQV-TEST-4",
				reason="Too short.", idempotency_key=key(),
			)

	def test_replay_returns_the_same_request(self):
		accepted, item_id = self.active_item()
		frappe.set_user(fx.HOD)
		idem = key()
		args = dict(
			plan_item_id=item_id, requisition_reference="REQ-TEST-CORR-5", requisition_version="RQV-TEST-5",
			reason="A repeated call with the same idempotency key must replay, not duplicate.",
			idempotency_key=idem,
		)
		first = plan_requisition.receive_plan_item_correction_request(**args)
		second = plan_requisition.receive_plan_item_correction_request(**args)
		self.assertEqual(first["correction_request"], second["correction_request"])
		self.assertFalse(first["idempotent"])
		self.assertTrue(second["idempotent"])

	def test_planner_starts_then_resolves_and_it_reaches_my_work_until_a_terminal_outcome(self):
		accepted, item_id = self.active_item()
		frappe.set_user(fx.HOD)
		received = plan_requisition.receive_plan_item_correction_request(
			plan_item_id=item_id, requisition_reference="REQ-TEST-CORR-6", requisition_version="RQV-TEST-6",
			reason="Open, then resolved — confirms the My Work row disappears only once terminal.",
			idempotency_key=key(),
		)
		from kentender_procurement.procurement_planning.services import my_work_provider

		self.assertTrue(any(r["task_id"] == received["correction_request"] for r in my_work_provider.my_work_rows(user=fx.PLANNER)["assigned"]))
		self.assertEqual(my_work_provider.my_work_rows(user=fx.AUTHOR)["assigned"], [])

		frappe.set_user(fx.PLANNER)
		doc = frappe.get_doc("Plan Item Correction Request", received["correction_request"])
		started = plan_requisition.start_plan_item_correction(
			correction_request=doc.name, expected_record_version=doc.record_version, idempotency_key=key(),
		)
		self.assertEqual(started["action"], "started")
		self.assertEqual(frappe.db.get_value("Plan Item Correction Request", doc.name, "status"), "In progress")
		# §7.2 StartPlanItemCorrection: the hold remains, and the task is still
		# the Planner's — In progress is not a terminal outcome.
		self.assertTrue(frappe.db.get_value("Plan Item", item_id, "authorisation_hold"))
		self.assertTrue(any(r["task_id"] == received["correction_request"] for r in my_work_provider.my_work_rows(user=fx.PLANNER)["assigned"]))

		# §5.4.5's neutral REQ notification is this file's only real caller of
		# the sibling module's contract; a minimal Requisition root stands in
		# for the REQ-owned document (this file never builds REQ's own,
		# heavier fixtures — mirrors the existing opaque-string treatment
		# `requisition_reference`/`requisition_version` already get above).
		req_root = frappe.get_doc(
			{
				"doctype": "Procurement Requisition", "requisition_reference": "REQ-TEST-CORR-6",
				"plan_id": accepted["annual_plan"], "plan_version_id": accepted["annual_plan_version"],
				"plan_item_id": item_id, "current_state": "Upstream correction required", "record_version": 0,
			}
		).insert(ignore_permissions=True)
		self.addCleanup(frappe.db.delete, "Procurement Requisition", {"name": req_root.name})

		correcting_version = self.correcting_active_version(accepted["annual_plan"])
		doc.reload()
		resolved = plan_requisition.resolve_plan_item_correction_request(
			correction_request=doc.name, correcting_plan_version=correcting_version,
			expected_record_version=doc.record_version, idempotency_key=key(),
		)
		self.assertEqual(resolved["action"], "resolved")
		self.assertEqual(resolved["replacement_plan_item_id"], item_id)
		self.assertEqual(frappe.db.get_value("Plan Item Correction Request", doc.name, "status"), "Resolved")
		self.assertFalse(frappe.db.get_value("Plan Item", item_id, "authorisation_hold"))
		self.assertFalse(any(r["task_id"] == received["correction_request"] for r in my_work_provider.my_work_rows(user=fx.PLANNER)["assigned"]))

		disposition = frappe.get_doc("Plan Item Correction Disposition", {"correction_request": doc.name, "action": "Resolve"})
		self.assertEqual(disposition.correcting_plan_version, correcting_version)
		req_root.reload()
		self.assertEqual(req_root.upstream_correction_outcome, "Resolved")
		self.assertIn(correcting_version, req_root.upstream_correction_reference)

	def test_resolve_requires_the_correcting_version_to_be_active(self):
		accepted, item_id = self.active_item()
		frappe.set_user(fx.HOD)
		received = plan_requisition.receive_plan_item_correction_request(
			plan_item_id=item_id, requisition_reference="REQ-TEST-CORR-NA", requisition_version="RQV-TEST-NA",
			reason="Resolve must be refused while no correcting Version is Active yet.",
			idempotency_key=key(),
		)
		frappe.set_user(fx.PLANNER)
		doc = frappe.get_doc("Plan Item Correction Request", received["correction_request"])
		frappe.set_user(fx.PLANNER)
		plan_publication.begin_plan_update(plan_reference=accepted["annual_plan"], idempotency_key=key())
		draft_successor = frappe.db.get_value("Annual Plan", {"plan_reference": accepted["annual_plan"]}, "open_successor_version")
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_requisition.resolve_plan_item_correction_request(
				correction_request=doc.name, correcting_plan_version=draft_successor,
				expected_record_version=doc.record_version, idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_CORRECTION_NOT_ACTIVE")

	def test_a_departmental_author_cannot_resolve_or_close(self):
		accepted, item_id = self.active_item()
		frappe.set_user(fx.HOD)
		received = plan_requisition.receive_plan_item_correction_request(
			plan_item_id=item_id, requisition_reference="REQ-TEST-CORR-7", requisition_version="RQV-TEST-7",
			reason="Only a Procurement Planner may dispose of this — an Author must be refused.",
			idempotency_key=key(),
		)
		frappe.set_user(fx.AUTHOR)
		with self.assertRaises(frappe.DoesNotExistError):
			plan_requisition.start_plan_item_correction(
				correction_request=received["correction_request"], expected_record_version=0, idempotency_key=key(),
			)
		with self.assertRaises(frappe.DoesNotExistError):
			plan_requisition.resolve_plan_item_correction_request(
				correction_request=received["correction_request"], correcting_plan_version="whatever",
				expected_record_version=0, idempotency_key=key(),
			)
		with self.assertRaises(frappe.DoesNotExistError):
			plan_requisition.close_plan_item_correction_without_change(
				correction_request=received["correction_request"], reason="An Author attempting to close a request without change.",
				expected_record_version=0, idempotency_key=key(),
			)

	def test_close_without_change_requires_a_reason_and_never_restarts_the_requisition(self):
		accepted, item_id = self.active_item()
		frappe.set_user(fx.HOD)
		received = plan_requisition.receive_plan_item_correction_request(
			plan_item_id=item_id, requisition_reference="REQ-TEST-CORR-8", requisition_version="RQV-TEST-8",
			reason="Closed without change once the Planner confirms nothing needs correcting.",
			idempotency_key=key(),
		)
		req_root = frappe.get_doc(
			{
				"doctype": "Procurement Requisition", "requisition_reference": "REQ-TEST-CORR-8",
				"plan_id": accepted["annual_plan"], "plan_version_id": accepted["annual_plan_version"],
				"plan_item_id": item_id, "current_state": "Upstream correction required", "record_version": 0,
			}
		).insert(ignore_permissions=True)
		self.addCleanup(frappe.db.delete, "Procurement Requisition", {"name": req_root.name})

		frappe.set_user(fx.PLANNER)
		doc = frappe.get_doc("Plan Item Correction Request", received["correction_request"])
		with self.assertRaises(frappe.ValidationError):
			plan_requisition.close_plan_item_correction_without_change(
				correction_request=doc.name, reason="Too short.", expected_record_version=doc.record_version, idempotency_key=key(),
			)
		closed = plan_requisition.close_plan_item_correction_without_change(
			correction_request=doc.name, reason="The Plan Item already reflects the department's confirmed requirement.",
			expected_record_version=doc.record_version, idempotency_key=key(),
		)
		self.assertEqual(closed["action"], "closed_without_change")
		self.assertEqual(frappe.db.get_value("Plan Item Correction Request", doc.name, "status"), "Closed without change")
		self.assertFalse(frappe.db.get_value("Plan Item", item_id, "authorisation_hold"))
		disposition = frappe.get_doc("Plan Item Correction Disposition", {"correction_request": doc.name, "action": "Close without change"})
		self.assertTrue(disposition.reason)
		req_root.reload()
		self.assertEqual(req_root.upstream_correction_outcome, "Closed without change")
		self.assertEqual(req_root.current_state, "Upstream correction required")  # never silently restarted

		doc.reload()
		with self.assertRaises(frappe.ValidationError) as caught:
			plan_requisition.start_plan_item_correction(
				correction_request=doc.name, expected_record_version=doc.record_version, idempotency_key=key(),
			)
		self.assertNotEqual(getattr(caught.exception, "code", None), "PLN_STALE_WRITE")


class TestScopeLockEngagesOnAuthorisation(RequisitionCase):
	"""PLN-CHG-001 v1.18 §5.4.6 (plan D9) — the scope lock is evidence, not a
	flag: it engages the first time a Requisition drawdown is actually
	authorised against the stable item, and never before. This is the core
	regression named in the tracker: the lock was previously wired into
	every read-side guard (`scope_lock.require_unlocked`,
	`locked_items_for_sources`) but nothing ever set it, so those guards
	were structurally unreachable until Phase 2g added the writer."""

	def test_the_first_drawdown_locks_scope_and_a_second_sequential_drawdown_does_not_relock(self):
		accepted, item_id = self.active_item(indicative_amount=1000000)
		allocation_id = self.allocation_id_of(item_id)
		self.assertFalse(scope_lock.status(item_id)["locked"])

		frappe.set_user(fx.HOPF)
		first_ref = f"REQ-{key()[:8]}"
		read = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)
		plan_requisition.authorise_requisition_drawdown(
			plan_item_id=item_id, requisition_reference=first_ref, requesting_org_unit=fx.OU_ALPHA,
			allocations=[{"plan_source_allocation_id": allocation_id, "quantity": 0.4, "amount": 400000}],
			expected_record_version=read["record_version"], idempotency_key=key(),
		)
		state = scope_lock.status(item_id)
		self.assertTrue(state["locked"])
		self.assertEqual(state["first_requisition"], first_ref)
		since = state["since"]

		# a second, unrelated Requisition reference drawing the remaining
		# balance within the same original scope does not move the lock
		frappe.set_user(fx.PLANNER)
		read = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)
		frappe.set_user(fx.HOPF)
		plan_requisition.authorise_requisition_drawdown(
			plan_item_id=item_id, requisition_reference=f"REQ-{key()[:8]}", requesting_org_unit=fx.OU_ALPHA,
			allocations=[{"plan_source_allocation_id": allocation_id, "quantity": 0.6, "amount": 600000}],
			expected_record_version=read["record_version"], idempotency_key=key(),
		)
		state = scope_lock.status(item_id)
		self.assertEqual(state["first_requisition"], first_ref)
		self.assertEqual(state["since"], since)

	def test_a_locked_item_cannot_be_dissolved_but_a_new_need_forms_its_own_separate_item(self):
		accepted, item_id = self.active_item(indicative_amount=1000000)
		allocation_id = self.allocation_id_of(item_id)
		frappe.set_user(fx.HOPF)
		read = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)
		plan_requisition.authorise_requisition_drawdown(
			plan_item_id=item_id, requisition_reference=f"REQ-{key()[:8]}", requesting_org_unit=fx.OU_ALPHA,
			allocations=[{"plan_source_allocation_id": allocation_id, "quantity": 0.4, "amount": 400000}],
			expected_record_version=read["record_version"], idempotency_key=key(),
		)
		self.assertTrue(scope_lock.status(item_id)["locked"])

		# the locked item's Draft successor copy cannot be dissolved
		frappe.set_user(fx.PLANNER)
		plan_publication.begin_plan_update(plan_reference=accepted["annual_plan"], idempotency_key=key())
		successor_version = frappe.db.get_value("Annual Plan", {"plan_reference": accepted["annual_plan"]}, "open_successor_version")
		item_read = plan_read.get_plan_item(plan_item_id=item_id)
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.dissolve_plan_item(
				plan_item=item_id, expected_record_version=item_read["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_ITEM_SCOPE_LOCKED")
		plan_publication.cancel_plan_update(
			plan_reference=accepted["annual_plan"],
			expected_record_version=frappe.db.get_value("Annual Plan Version", successor_version, "record_version"),
			idempotency_key=key(),
		)

		# the remaining original allowance still draws (§5.4.6: "does not
		# cancel the existing allowance or prohibit ... sequential drawdowns")
		frappe.set_user(fx.PLANNER)
		read = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)
		self.assertTrue(read["eligible"])
		frappe.set_user(fx.HOPF)
		remaining = plan_requisition.authorise_requisition_drawdown(
			plan_item_id=item_id, requisition_reference=f"REQ-{key()[:8]}", requesting_org_unit=fx.OU_ALPHA,
			allocations=[{"plan_source_allocation_id": allocation_id, "quantity": 0.6, "amount": 600000}],
			expected_record_version=read["record_version"], idempotency_key=key(),
		)
		self.assertEqual(remaining["action"], "recorded")

		# a different, unrelated Need forms its own separate Plan Item —
		# "other items, new Needs ... remain possible" (§5.4.6). The
		# original DPP root is already Accepted, so a further requirement
		# arrives through CreateDepartmentalPlanUpdate, never a second
		# OpenDepartmentalPlan (that command is for initial intake only).
		frappe.set_user(fx.AUTHOR)
		dpp_root = frappe.get_doc("Departmental Plan", accepted["dpp_reference"])
		opened = dpp_lifecycle.create_departmental_plan_update(
			departmental_plan=dpp_root.name, expected_record_version=dpp_root.record_version, idempotency_key=key(),
		)
		added = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"], values=fx.direct_values(title="A later, unrelated requirement"),
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.HOD)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True, expected_record_version=added["record_version"], idempotency_key=key(),
		)
		dpp_task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
		frappe.set_user(fx.PLANNER)
		# the copied-forward original entry needs reclassifying alongside the
		# new one — accepting a submission classifies every entry it carries
		submitted_entry_ids = frappe.get_all("Departmental Plan Entry", filters={"dpp_version": opened["current_version"]}, pluck="entry_id")
		new_accepted = dpp_validation.accept_departmental_plan(
			task=dpp_task.name, classifications={eid: "Goods" for eid in submitted_entry_ids}, task_token=dpp_task.task_token, idempotency_key=key(),
		)
		# the new entry is accepted as pending against the SAME Plan (§5.4.3);
		# the Active Plan has no open Draft any more (cancelled above), so
		# forming it into an item needs a fresh ordinary Plan-update Draft.
		self.assertEqual(new_accepted["annual_plan"], accepted["annual_plan"])
		plan_publication.begin_plan_update(plan_reference=new_accepted["annual_plan"], idempotency_key=key())
		plan = plan_read.get_annual_plan(plan_reference=new_accepted["annual_plan"])
		self.assertTrue(plan["mutable"])
		formed = plan_workbench.form_plan_items(
			plan_version=plan["version_reference"], dpp_entries=[plan["unallocated_sources"][0]["dpp_entry"]],
			mode="each", expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		new_item_id = formed["created_items"][0]
		self.assertNotEqual(new_item_id, item_id)
		self.assertFalse(scope_lock.status(new_item_id)["locked"])


class TestCorrectionRequestHoldsNewAuthorisation(RequisitionCase):
	"""PLN-CHG-001 v1.18 §5.4.5 / PLN-RI-029 — an unresolved correction
	request holds new drawdown authorisations for its own stable item only;
	release requires every relevant request to reach a terminal
	disposition, and then re-evaluates ordinary eligibility."""

	def _req_root(self, accepted, item_id, reference: str):
		root = frappe.get_doc(
			{
				"doctype": "Procurement Requisition", "requisition_reference": reference,
				"plan_id": accepted["annual_plan"], "plan_version_id": accepted["annual_plan_version"],
				"plan_item_id": item_id, "current_state": "Upstream correction required", "record_version": 0,
			}
		).insert(ignore_permissions=True)
		self.addCleanup(frappe.db.delete, "Procurement Requisition", {"name": root.name})
		return root

	def test_the_hold_blocks_a_new_drawdown_until_disposed_and_release_reevaluates_eligibility(self):
		accepted, item_id = self.active_item(indicative_amount=1000000)
		allocation_id = self.allocation_id_of(item_id)
		self._req_root(accepted, item_id, "REQ-HOLD-1")
		self._req_root(accepted, item_id, "REQ-HOLD-2")
		frappe.set_user(fx.HOD)
		plan_requisition.receive_plan_item_correction_request(
			plan_item_id=item_id, requisition_reference="REQ-HOLD-1", requisition_version="RQV-HOLD-1",
			reason="The authorised warranty period does not match the department's actual need.",
			idempotency_key=key(),
		)
		self.assertTrue(scope_lock.status(item_id)["held"])

		frappe.set_user(fx.PLANNER)
		read = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)
		frappe.set_user(fx.HOPF)
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_requisition.authorise_requisition_drawdown(
				plan_item_id=item_id, requisition_reference=f"REQ-{key()[:8]}", requesting_org_unit=fx.OU_ALPHA,
				allocations=[{"plan_source_allocation_id": allocation_id, "quantity": 0.5, "amount": 500000}],
				expected_record_version=read["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_ITEM_AUTHORISATION_HELD")
		self.assertEqual(frappe.db.count("Plan Drawdown Reference", {"plan_item_id": item_id}), 0)
		self.assertFalse(scope_lock.status(item_id)["locked"])  # a held item never reaches the lock

		# a second, independent request keeps the hold in force after the
		# first is disposed of
		frappe.set_user(fx.HOPF)
		second = plan_requisition.receive_plan_item_correction_request(
			plan_item_id=item_id, requisition_reference="REQ-HOLD-2", requisition_version="RQV-HOLD-2",
			reason="The Plan Item's Strategic Objective is materially wrong for this request too.",
			idempotency_key=key(),
		)
		self.assertEqual(scope_lock.status(item_id)["open_requests"], 2)

		frappe.set_user(fx.PLANNER)
		first_doc = frappe.get_doc("Plan Item Correction Request", {"requisition_reference": "REQ-HOLD-1"})
		plan_requisition.close_plan_item_correction_without_change(
			correction_request=first_doc.name, reason="The department confirmed the existing warranty period is in fact correct.",
			expected_record_version=first_doc.record_version, idempotency_key=key(),
		)
		state = scope_lock.status(item_id)
		self.assertTrue(state["held"])
		self.assertEqual(state["open_requests"], 1)

		frappe.set_user(fx.PLANNER)
		read = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)
		frappe.set_user(fx.HOPF)
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_requisition.authorise_requisition_drawdown(
				plan_item_id=item_id, requisition_reference=f"REQ-{key()[:8]}", requesting_org_unit=fx.OU_ALPHA,
				allocations=[{"plan_source_allocation_id": allocation_id, "quantity": 0.5, "amount": 500000}],
				expected_record_version=read["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_ITEM_AUTHORISATION_HELD")

		frappe.set_user(fx.PLANNER)
		second_doc = frappe.get_doc("Plan Item Correction Request", second["correction_request"])
		plan_requisition.close_plan_item_correction_without_change(
			correction_request=second_doc.name, reason="The Strategic Objective was reviewed and confirmed correct as recorded.",
			expected_record_version=second_doc.record_version, idempotency_key=key(),
		)
		state = scope_lock.status(item_id)
		self.assertFalse(state["held"])
		self.assertEqual(state["open_requests"], 0)

		frappe.set_user(fx.PLANNER)
		read = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)
		self.assertTrue(read["eligible"])
		frappe.set_user(fx.HOPF)
		released = plan_requisition.authorise_requisition_drawdown(
			plan_item_id=item_id, requisition_reference=f"REQ-{key()[:8]}", requesting_org_unit=fx.OU_ALPHA,
			allocations=[{"plan_source_allocation_id": allocation_id, "quantity": 0.5, "amount": 500000}],
			expected_record_version=read["record_version"], idempotency_key=key(),
		)
		self.assertEqual(released["action"], "recorded")
		self.assertTrue(scope_lock.status(item_id)["locked"])


class TestPlanItemNoticesCarryTheSpecCopy(RequisitionCase):
	"""PLN-CHG-001 v1.18 §9.7 (PLN18-211): the exact domain-specific copy for
	a scope-locked or correction-held item is computed server-side in
	`plan_read.get_plan_item`'s `notices`, not left to the client."""

	def test_no_notices_for_an_ordinary_active_item(self):
		accepted, item_id = self.active_item()
		frappe.set_user(fx.PLANNER)
		read = plan_read.get_plan_item(plan_item_id=item_id)
		self.assertEqual(read["notices"], [])

	def test_a_scope_locked_item_carries_the_exact_9_7_copy(self):
		accepted, item_id = self.active_item(indicative_amount=1000000)
		allocation_id = self.allocation_id_of(item_id)
		frappe.set_user(fx.HOPF)
		eligible = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)
		plan_requisition.authorise_requisition_drawdown(
			plan_item_id=item_id, requisition_reference=f"REQ-{key()[:8]}", requesting_org_unit=fx.OU_ALPHA,
			allocations=[{"plan_source_allocation_id": allocation_id, "quantity": 0.4, "amount": 400000}],
			expected_record_version=eligible["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.PLANNER)
		read = plan_read.get_plan_item(plan_item_id=item_id)
		notices = {n["kind"]: n for n in read["notices"]}
		self.assertIn("scope_locked", notices)
		self.assertEqual(notices["scope_locked"]["heading"], "Additional requirements need a separate Plan Item")
		self.assertIn("already has an authorised Requisition", notices["scope_locked"]["text"])
		self.assertNotIn("correction_hold", notices)

	def test_a_held_item_carries_the_exact_9_7_copy(self):
		accepted, item_id = self.active_item()
		frappe.set_user(fx.HOD)
		plan_requisition.receive_plan_item_correction_request(
			plan_item_id=item_id, requisition_reference="REQ-NOTICE-1", requisition_version="RQV-NOTICE-1",
			reason="The authorised warranty period does not match the department's actual need.",
			idempotency_key=key(),
		)
		frappe.set_user(fx.PLANNER)
		read = plan_read.get_plan_item(plan_item_id=item_id)
		notices = {n["kind"]: n for n in read["notices"]}
		self.assertIn("correction_hold", notices)
		self.assertEqual(notices["correction_hold"]["heading"], "New Requisition authorisations are on hold")
		self.assertIn("unresolved correction request", notices["correction_hold"]["text"])
		self.assertNotIn("scope_locked", notices)


class TestRequestShapedEndpoints(RequisitionCase):
	"""Tracker rule 6 (the NDS-914 class): the three §7.4 endpoints driven
	exactly the way `frappe.handler` does — form_dict carrying cmd +
	csrf_token, list payloads as JSON strings."""

	API = "kentender_procurement.procurement_planning.api"

	def call(self, method: str, **args):
		from frappe.handler import execute_cmd

		frappe.local.form_dict = frappe._dict(
			cmd=f"{self.API}.{method}",
			csrf_token="irrelevant-but-present-on-every-post",
			**args,
		)
		self.addCleanup(setattr, frappe.local, "form_dict", frappe._dict())
		if not hasattr(frappe.local, "request"):
			frappe.local.request = frappe._dict(
				method="POST", path=f"/api/method/{self.API}.{method}", headers={}
			)
			self.addCleanup(delattr, frappe.local, "request")
		return execute_cmd(f"{self.API}.{method}")

	def test_the_full_drawdown_journey_over_the_request_path(self):
		import json

		accepted, item_id = self.active_item(indicative_amount=1000000)
		allocation_id = self.allocation_id_of(item_id)

		frappe.set_user(fx.PLANNER)
		read = self.call("get_requisition_eligible_plan_item", plan_item_id=item_id)
		self.assertTrue(read["eligible"])

		frappe.set_user(fx.HOPF)
		recorded = self.call(
			"authorise_requisition_drawdown", plan_item_id=item_id,
			requisition_reference="REQ-HTTP-1", requesting_org_unit=fx.OU_ALPHA,
			allocations=json.dumps(
				[{"plan_source_allocation_id": allocation_id, "quantity": 0.5, "amount": 500000}]
			),
			expected_record_version=str(read["record_version"]), idempotency_key=key(),
		)
		self.assertEqual(recorded["action"], "recorded")
		drawdown = recorded["drawdown_references"][0]

		frappe.set_user(fx.PLANNER)
		read = self.call("get_requisition_eligible_plan_item", plan_item_id=item_id)
		self.assertAlmostEqual(read["remaining_value"], 500000)

		frappe.set_user(fx.HOPF)
		reversed_result = self.call(
			"reverse_requisition_drawdown",
			drawdown_reference=drawdown["drawdown_reference"],
			expected_record_version=str(drawdown["record_version"]), idempotency_key=key(),
		)
		self.assertEqual(reversed_result["action"], "reversed")

		frappe.set_user(fx.PLANNER)
		read = self.call("get_requisition_eligible_plan_item", plan_item_id=item_id)
		self.assertAlmostEqual(read["remaining_value"], 1000000)


class TestOpenSuccessorKeepsTheActiveItemEligible(RequisitionCase):
	"""PLN-CHG-001 v1.14 invariant 18 / §4.4 — "An Active item remains
	eligible until an acknowledged successor changes it" and "the Active
	predecessor remains operational until the correction or successor is
	approved, published and acknowledged".

	Reproduces the live 2026-09-11 defect: with PLN-MOH-2027-001-V2 opened as
	a Draft successor, Grace Wanjiku's (Departmental Author, OU-MOH-00187)
	Requisitions workspace returned `Not found` because the eligibility
	contract resolved `PPI-MOH-2027-001` to the successor's Draft copy (no
	Active allocation → no contributing unit → OU-scoped reader refused),
	the Planning editor's "open successor wins" precedence."""

	def active_item_with_open_successor(self) -> tuple[dict, str, str, str]:
		accepted, item_id = self.active_item(indicative_amount=1000000)
		active_name = frappe.db.get_value("Annual Plan Item", {"plan_item_id": item_id, "item_state": "Active"}, "name")
		frappe.set_user(fx.PLANNER)
		begun = plan_publication.begin_plan_update(plan_reference=accepted["annual_plan"], idempotency_key=key())
		draft_name = frappe.db.get_value("Annual Plan Item", {"plan_item_id": item_id, "plan_version": begun["successor_version"]}, "name")
		self.assertEqual(frappe.db.get_value("Annual Plan Item", draft_name, "item_state"), "Draft")
		return accepted, item_id, active_name, draft_name

	def test_a_contributing_departmental_author_still_reads_the_active_copy(self):
		accepted, item_id, active_name, draft_name = self.active_item_with_open_successor()
		frappe.set_user(fx.AUTHOR)  # OU_ALPHA — the Active copy's own contributing unit
		read = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)
		self.assertTrue(read["eligible"])
		self.assertEqual(read["version_reference"], frappe.db.get_value("Annual Plan Item", active_name, "plan_version"))
		self.assertEqual(read["contributing_org_unit_ids"], [fx.OU_ALPHA])
		self.assertEqual(read["remaining_value"], 1000000)
		self.assertEqual(len(read["sources"]), 1)

	def test_the_workspace_listing_and_the_detail_name_the_same_item(self):
		accepted, item_id, active_name, draft_name = self.active_item_with_open_successor()
		frappe.set_user(fx.AUTHOR)
		rows = plan_requisition.list_requisition_eligible_plan_items()
		self.assertIn(item_id, [r["plan_item_id"] for r in rows])
		for row in rows:
			# the exact loop Requisitions' `_ready_to_prepare_card` runs
			plan_requisition.get_requisition_eligible_plan_item(plan_item_id=row["plan_item_id"])

	def test_a_drawdown_posts_against_the_active_copy_not_the_draft_successor(self):
		accepted, item_id, active_name, draft_name = self.active_item_with_open_successor()
		frappe.set_user(fx.PLANNER)
		read = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)
		allocation_id = read["sources"][0]["plan_source_allocation_id"]
		frappe.set_user(fx.HOPF)
		result = plan_requisition.authorise_requisition_drawdown(
			plan_item_id=item_id, requisition_reference=f"REQ-{key()[:8]}", requesting_org_unit=fx.OU_ALPHA,
			allocations=[{"plan_source_allocation_id": allocation_id, "quantity": 0.4, "amount": 400000}],
			expected_record_version=read["record_version"], idempotency_key=key(),
		)
		self.assertEqual(result["action"], "recorded")
		drawdown = frappe.get_doc("Plan Drawdown Reference", result["drawdown_references"][0]["drawdown_reference"])
		self.assertEqual(drawdown.plan_item, active_name)
		self.assertEqual(frappe.db.count("Plan Drawdown Reference", {"plan_item": draft_name}), 0)
		frappe.set_user(fx.PLANNER)
		self.assertAlmostEqual(plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)["remaining_value"], 600000)

	def test_a_correction_request_is_gated_on_the_active_copys_contributing_units(self):
		accepted, item_id, active_name, draft_name = self.active_item_with_open_successor()
		frappe.set_user(fx.HOD)  # OU_ALPHA
		result = plan_requisition.receive_plan_item_correction_request(
			plan_item_id=item_id, requisition_reference="REQ-TEST-CORR-S", requisition_version="RQV-TEST-S",
			reason="The authorised warranty period does not match the department's actual need.",
			idempotency_key=key(),
		)
		self.assertTrue(result["ok"])
		self.assertEqual(frappe.get_doc("Plan Item Correction Request", result["correction_request"]).plan_item, active_name)
