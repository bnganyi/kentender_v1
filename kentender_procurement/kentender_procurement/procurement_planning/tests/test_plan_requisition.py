# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §7.4/§8.2 Requisition eligibility tests (Phase 10,
Slice H): GetRequisitionEligiblePlanItem.v2, RecordRequisitionDrawdown and
ReverseRequisitionDrawdown — the published contract a sibling Requisitions
module would call; this repo owns no such module (§2.1), so every test here
is that contract's only real caller today."""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.services import (
	budget_gateway,
	dpp_lifecycle,
	dpp_validation,
	needs_intake,
	plan_finance,
	plan_governance,
	plan_read,
	plan_requisition,
	plan_workbench,
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
		frappe.set_user(fx.PLANNER)
		plan = plan_read.get_annual_plan(plan_reference=plan_reference)
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
		result = plan_governance.approve_annual_plan(
			task=statutory_task.name, task_token=statutory_task.task_token, idempotency_key=key(),
		)
		frappe.set_user(fx.PLANNER)
		return result

	def active_item(self, *, indicative_amount: float = 1000000) -> tuple[dict, str]:
		accepted, item_id = self.confirmed_item(indicative_amount=indicative_amount)
		self.activate(accepted["annual_plan"])
		return accepted, item_id

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
		return plan_requisition.record_requisition_drawdown(
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
			plan_requisition.record_requisition_drawdown(
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
		first = plan_requisition.record_requisition_drawdown(**args)
		second = plan_requisition.record_requisition_drawdown(**args)
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
			plan_requisition.record_requisition_drawdown(
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
			"multi_year_justification", "contributing_org_unit_ids", "strategic_objective_path",
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
		plan_requisition.record_requisition_drawdown(
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

	def test_planner_resolves_and_it_reaches_my_work_only_while_open(self):
		accepted, item_id = self.active_item()
		frappe.set_user(fx.HOD)
		received = plan_requisition.receive_plan_item_correction_request(
			plan_item_id=item_id, requisition_reference="REQ-TEST-CORR-6", requisition_version="RQV-TEST-6",
			reason="Open, then resolved — confirms the My Work row disappears once resolved.",
			idempotency_key=key(),
		)
		from kentender_procurement.procurement_planning.services import my_work_provider

		self.assertTrue(any(r["task_id"] == received["correction_request"] for r in my_work_provider.my_work_rows(user=fx.PLANNER)["assigned"]))
		self.assertEqual(my_work_provider.my_work_rows(user=fx.AUTHOR)["assigned"], [])

		frappe.set_user(fx.PLANNER)
		doc = frappe.get_doc("Plan Item Correction Request", received["correction_request"])
		resolved = plan_requisition.resolve_plan_item_correction_request(
			correction_request=doc.name, resolution_note="Corrected via a Plan successor.",
			expected_record_version=doc.record_version, idempotency_key=key(),
		)
		self.assertEqual(resolved["action"], "resolved")
		self.assertFalse(any(r["task_id"] == received["correction_request"] for r in my_work_provider.my_work_rows(user=fx.PLANNER)["assigned"]))

	def test_a_departmental_author_cannot_resolve(self):
		accepted, item_id = self.active_item()
		frappe.set_user(fx.HOD)
		received = plan_requisition.receive_plan_item_correction_request(
			plan_item_id=item_id, requisition_reference="REQ-TEST-CORR-7", requisition_version="RQV-TEST-7",
			reason="Only a Procurement Planner may resolve — an Author must be refused.",
			idempotency_key=key(),
		)
		frappe.set_user(fx.AUTHOR)
		with self.assertRaises(frappe.DoesNotExistError):
			plan_requisition.resolve_plan_item_correction_request(
				correction_request=received["correction_request"], resolution_note="Attempted resolution.",
				expected_record_version=0, idempotency_key=key(),
			)


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
			"record_requisition_drawdown", plan_item_id=item_id,
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
