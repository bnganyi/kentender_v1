# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 §5.2/§8 Annual Plan workbench tests (Phase 6, Slice D)."""

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
	plan_read,
	plan_workbench,
)
from kentender_procurement.procurement_planning.tests import fixtures as fx


def key() -> str:
	return uuid4().hex


class PlanWorkbenchCase(IntegrationTestCase):
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
		for target, value in (
			(budget_gateway, "eligible_line_ids"),
			(needs_intake, "current_accepted_sources"),
		):
			patched = patch.object(
				target, value,
				return_value={fx.BUDGET_LINE, fx.BUDGET_LINE_2} if value == "eligible_line_ids" else [],
			)
			patched.start()
			self.addCleanup(patched.stop)

	def accept_one(self, **overrides) -> tuple[dict, str, str]:
		"""One accepted, unallocated direct entry. Returns (acceptance result,
		dpp_entry doc name, dpp root doc name)."""
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			procuring_entity=fx.PE, organisation_unit=fx.OU_ALPHA,
			financial_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)
		added = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"], values=fx.direct_values(**overrides),
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.HOD)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True,
			expected_record_version=added["record_version"], idempotency_key=key(),
		)
		task = frappe.get_doc(
			"Departmental Plan Validation Task", {"task_reference": submitted["task"]}
		)
		frappe.set_user(fx.PLANNER)
		accepted = dpp_validation.accept_departmental_plan(
			task=task.name, classifications={added["entry_id"]: "Goods"},
			task_token=task.task_token, idempotency_key=key(),
		)
		dpp_entry = frappe.db.get_value(
			"Departmental Plan Entry",
			{"dpp_version": opened["current_version"], "entry_id": added["entry_id"]},
			"name",
		)
		return accepted, dpp_entry, opened["departmental_plan"]

	def accept_two(
		self, spec_a: dict, spec_b: dict, class_a="Goods", class_b="Goods"
	) -> tuple[dict, str, str]:
		"""Two accepted, unallocated direct entries in one DPP. Returns
		(acceptance result, entry_a doc name, entry_b doc name)."""
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			procuring_entity=fx.PE, organisation_unit=fx.OU_ALPHA,
			financial_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)
		added_a = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"], values=fx.direct_values(**spec_a),
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		added_b = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"], values=fx.direct_values(**spec_b),
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
			classifications={added_a["entry_id"]: class_a, added_b["entry_id"]: class_b},
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
		return accepted, entry_a, entry_b

	def one_item(self, **overrides) -> tuple[dict, str]:
		"""One accepted entry, already formed into its own Plan Item. Returns
		(acceptance result, plan_item_id)."""
		accepted, entry, _ = self.accept_one(**overrides)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		formed = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"], dpp_entries=[entry],
			mode="each", expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		return accepted, formed["created_items"][0]


class TestFormPlanItemsSingle(PlanWorkbenchCase):
	def test_single_source_forms_one_item_and_allocates_it(self):
		accepted, dpp_entry, _ = self.accept_one()
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertEqual(plan["summary"]["accepted_entries"], 1)
		self.assertEqual(plan["summary"]["allocated"], 0)
		self.assertEqual(len(plan["unallocated_sources"]), 1)

		result = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"], dpp_entries=[dpp_entry],
			mode="each", expected_record_version=plan["record_version"],
			idempotency_key=key(),
		)
		self.assertEqual(result["action"], "formed")
		self.assertTrue(result["single"])
		item_id = result["created_items"][0]

		refreshed = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertEqual(refreshed["summary"]["allocated"], 1)
		self.assertEqual(refreshed["summary"]["plan_items"], 1)
		self.assertEqual(refreshed["unallocated_sources"], [])

		item = plan_read.get_plan_item(plan_item_id=item_id)
		self.assertFalse(item["combined"])
		self.assertEqual(len(item["sources"]), 1)
		self.assertEqual(item["item"]["title"], "Direct requirement")
		self.assertEqual(item["item"]["requirement_type"], "Goods")
		self.assertFalse(item["source_correction_required"])

	def test_forming_the_same_entry_twice_is_refused(self):
		accepted, dpp_entry, _ = self.accept_one()
		plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"], dpp_entries=[dpp_entry],
			mode="each", expected_record_version=0, idempotency_key=key(),
		)
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.form_plan_items(
				plan_version=accepted["annual_plan_version"], dpp_entries=[dpp_entry],
				mode="each", expected_record_version=1, idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_SOURCE_UNAVAILABLE")

	def test_stale_record_version_is_refused(self):
		accepted, dpp_entry, _ = self.accept_one()
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.form_plan_items(
				plan_version=accepted["annual_plan_version"], dpp_entries=[dpp_entry],
				mode="each", expected_record_version=99, idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_STALE_WRITE")

	def test_formation_replays_idempotently(self):
		accepted, dpp_entry, _ = self.accept_one()
		idem = key()
		first = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"], dpp_entries=[dpp_entry],
			mode="each", expected_record_version=0, idempotency_key=idem,
		)
		second = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"], dpp_entries=[dpp_entry],
			mode="each", expected_record_version=0, idempotency_key=idem,
		)
		self.assertTrue(second["idempotent"])
		self.assertEqual(second["created_items"], first["created_items"])
		self.assertEqual(frappe.db.count("Annual Plan Item", {"fixture_namespace": fx.NS}), 1)

	def test_non_planner_is_refused(self):
		accepted, dpp_entry, _ = self.accept_one()
		frappe.set_user(fx.OUTSIDER)
		with self.assertRaises(frappe.DoesNotExistError):
			plan_workbench.form_plan_items(
				plan_version=accepted["annual_plan_version"], dpp_entries=[dpp_entry],
				mode="each", expected_record_version=0, idempotency_key=key(),
			)


class TestFormPlanItemsCombine(PlanWorkbenchCase):
	def test_each_mode_creates_two_separate_items(self):
		accepted, entry_a, entry_b = self.accept_two(
			{"title": "Requirement A"}, {"title": "Requirement B", "budget_line": fx.BUDGET_LINE_2},
		)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		result = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"], dpp_entries=[entry_a, entry_b],
			mode="each", expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		self.assertFalse(result["single"])
		self.assertEqual(len(result["created_items"]), 2)
		refreshed = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertEqual(refreshed["summary"]["plan_items"], 2)
		self.assertEqual(refreshed["summary"]["allocated"], 2)

	def test_combined_mode_creates_one_item_across_two_budget_lines(self):
		accepted, entry_a, entry_b = self.accept_two(
			{"title": "Clinical training laptops", "budget_line": fx.BUDGET_LINE},
			{"title": "Clinical deployment laptops", "budget_line": fx.BUDGET_LINE_2},
		)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		result = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"], dpp_entries=[entry_a, entry_b],
			mode="combined", expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		self.assertTrue(result["single"])
		item = plan_read.get_plan_item(plan_item_id=result["created_items"][0])
		self.assertTrue(item["combined"])
		self.assertEqual(len(item["sources"]), 2)
		self.assertIn("2 sources", item["sources_caption"])

	def test_combined_mode_rejects_incompatible_classifications(self):
		accepted, entry_a, entry_b = self.accept_two(
			{"title": "Requirement A"}, {"title": "Requirement B"},
			class_a="Goods", class_b="Consulting services",
		)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.form_plan_items(
				plan_version=accepted["annual_plan_version"], dpp_entries=[entry_a, entry_b],
				mode="combined", expected_record_version=plan["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_SOURCE_INCOMPATIBLE")
		self.assertEqual(frappe.db.count("Annual Plan Item", {"fixture_namespace": fx.NS}), 0)

	def test_missing_formation_choice_for_several_sources_is_refused(self):
		accepted, entry_a, entry_b = self.accept_two(
			{"title": "Requirement A"}, {"title": "Requirement B"},
		)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.form_plan_items(
				plan_version=accepted["annual_plan_version"], dpp_entries=[entry_a, entry_b],
				mode="bogus", expected_record_version=plan["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_ENTRY_INCOMPLETE")


class TestSavePlanItem(PlanWorkbenchCase):
	def test_save_updates_allow_listed_fields_and_snapshots_objective(self):
		_, item_id = self.one_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		result = plan_workbench.save_plan_item(
			plan_item=item_id,
			values={
				"title": "Renamed procurement package",
				"description": "A sufficiently long procurement description for the package.",
				"strategic_objective": fx.STRATEGY_OBJECTIVE,
				"aggregation_reason": "",
				"invitation_date": "2098-08-01", "bid_opening_date": "2098-08-15",
				"evaluation_completion_date": "2098-09-01", "award_approval_date": "2098-09-10",
				"award_notification_date": "2098-09-15", "contract_signing_date": "2098-10-01",
				"delivery_completion_date": "2098-10-15",
			},
			expected_record_version=item["record_version"], idempotency_key=key(),
		)
		self.assertEqual(result["action"], "saved")
		refreshed = plan_read.get_plan_item(plan_item_id=item_id)
		self.assertEqual(refreshed["item"]["title"], "Renamed procurement package")
		self.assertEqual(refreshed["item"]["strategic_objective"], fx.STRATEGY_OBJECTIVE)
		self.assertEqual(refreshed["item"]["objective_path"], fx.STRATEGY_OBJECTIVE_PATH)
		self.assertEqual(refreshed["schedule"]["delivery_completion_date"], "2098-10-15")

	def test_save_rejects_unknown_field(self):
		_, item_id = self.one_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.save_plan_item(
				plan_item=item_id, values={"title": "x" * 10, "description": "y" * 20, "lotting": "no"},
				expected_record_version=item["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_ENTRY_INCOMPLETE")

	def test_save_rejects_out_of_order_schedule(self):
		_, item_id = self.one_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.save_plan_item(
				plan_item=item_id,
				values={
					"title": "Valid title", "description": "A valid procurement description text.",
					"invitation_date": "2098-09-01", "bid_opening_date": "2098-08-01",
				},
				expected_record_version=item["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_SCHEDULE_INVALID")

	def test_save_rejects_delivery_after_required_by(self):
		_, item_id = self.one_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.save_plan_item(
				plan_item=item_id,
				values={
					"title": "Valid title", "description": "A valid procurement description text.",
					"delivery_completion_date": "2099-06-01",
				},
				expected_record_version=item["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_SCHEDULE_INVALID")

	def test_save_rejects_ineligible_objective(self):
		_, item_id = self.one_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.save_plan_item(
				plan_item=item_id,
				values={
					"title": "Valid title", "description": "A valid procurement description text.",
					"strategic_objective": "NOT-A-REAL-OBJECTIVE",
				},
				expected_record_version=item["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_OBJECTIVE_INELIGIBLE")


class TestDissolvePlanItem(PlanWorkbenchCase):
	def test_dissolve_returns_the_source_to_the_unallocated_pool(self):
		accepted, item_id = self.one_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		result = plan_workbench.dissolve_plan_item(
			plan_item=item_id, expected_record_version=item["record_version"], idempotency_key=key(),
		)
		self.assertEqual(result["action"], "dissolved")
		refreshed = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertEqual(refreshed["summary"]["plan_items"], 0)
		self.assertEqual(len(refreshed["unallocated_sources"]), 1)

	def test_dissolving_twice_is_blocked(self):
		accepted, item_id = self.one_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.dissolve_plan_item(
			plan_item=item_id, expected_record_version=item["record_version"], idempotency_key=key(),
		)
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.dissolve_plan_item(
				plan_item=item_id, expected_record_version=item["record_version"] + 1,
				idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_DISSOLUTION_BLOCKED")

	def test_source_can_be_re_formed_after_dissolution(self):
		accepted, item_id = self.one_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.dissolve_plan_item(
			plan_item=item_id, expected_record_version=item["record_version"], idempotency_key=key(),
		)
		refreshed = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		dpp_entry = refreshed["unallocated_sources"][0]["dpp_entry"]
		result = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"], dpp_entries=[dpp_entry],
			mode="each", expected_record_version=refreshed["record_version"], idempotency_key=key(),
		)
		self.assertEqual(result["action"], "formed")


class TestSourceCorrectionRequired(PlanWorkbenchCase):
	def test_a_dpp_successor_acceptance_flags_the_allocated_item(self):
		accepted, item_id = self.one_item()
		self.assertFalse(plan_read.get_plan_item(plan_item_id=item_id)["source_correction_required"])
		dpp_entry_name = frappe.get_all(
			"Plan Source Allocation",
			filters={"plan_item_id": item_id},
			pluck="dpp_entry",
		)[0]
		entry_id = frappe.db.get_value("Departmental Plan Entry", dpp_entry_name, "entry_id")
		dpp_root = frappe.db.get_value(
			"Departmental Plan", {"dpp_reference": accepted["dpp_reference"]}
		)

		# a DPP update, resubmitted and re-accepted, copies the entry onto a
		# new document under the same stable entry_id (§12.7)
		frappe.set_user(fx.HOD)
		update = dpp_lifecycle.create_departmental_plan_update(
			departmental_plan=dpp_root,
			expected_record_version=frappe.db.get_value("Departmental Plan", dpp_root, "record_version"),
			idempotency_key=key(),
		)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=update["current_version"], certification_confirmed=True,
			expected_record_version=update["record_version"], idempotency_key=key(),
		)
		task2 = frappe.get_doc(
			"Departmental Plan Validation Task", {"task_reference": submitted["task"]}
		)
		frappe.set_user(fx.PLANNER)
		dpp_validation.accept_departmental_plan(
			task=task2.name, classifications={entry_id: "Goods"},
			task_token=task2.task_token, idempotency_key=key(),
		)

		flagged = plan_read.get_plan_item(plan_item_id=item_id)
		self.assertTrue(flagged["source_correction_required"])
		plan_flagged = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertTrue(plan_flagged["plan_items"][0]["source_correction_required"])

		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.save_plan_item(
				plan_item=item_id,
				values={"title": flagged["item"]["title"], "description": flagged["item"]["description"]},
				expected_record_version=flagged["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_SOURCE_CORRECTION_REQUIRED")

		# recovery: dissolve, then re-form from the now-current source
		plan_workbench.dissolve_plan_item(
			plan_item=item_id, expected_record_version=flagged["record_version"], idempotency_key=key(),
		)
		refreshed_plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertEqual(len(refreshed_plan["unallocated_sources"]), 1)
		current_entry = refreshed_plan["unallocated_sources"][0]["dpp_entry"]
		reformed = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"], dpp_entries=[current_entry],
			mode="each", expected_record_version=refreshed_plan["record_version"], idempotency_key=key(),
		)
		new_item = plan_read.get_plan_item(plan_item_id=reformed["created_items"][0])
		self.assertFalse(new_item["source_correction_required"])
