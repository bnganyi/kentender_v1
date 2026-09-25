# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §5.2/§8 Annual Plan workbench tests (Phase 6, Slice D)."""

from __future__ import annotations

from decimal import Decimal
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
	readiness,
	workspace,
)
from kentender_procurement.procurement_planning.tests import fixtures as fx


#: §10.7 — a combined purchase must say why it was combined, at the moment it
#: is combined. 20–500 characters, the same range the readiness gate requires.
COMBINATION_REASON = (
	"Both departments require the same specification for the same programme; combining secures "
	"better unit pricing and one delivery schedule."
)


def key() -> str:
	return uuid4().hex


class PlanWorkbenchCase(IntegrationTestCase):
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
			organisation_unit=fx.OU_ALPHA,
			fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
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
			organisation_unit=fx.OU_ALPHA,
			fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
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
		self.assertEqual(item["identity"]["title"], "Direct requirement")
		self.assertEqual(item["identity"]["requirement_type"], "Goods")
		self.assertEqual(item["identity"]["procurement_category"], "Goods")
		self.assertEqual(item["classification"]["procurement_method"], "Open Tender")
		self.assertIn("Open Tender", item["classification"]["admissible_methods"])
		self.assertEqual(item["preference"]["plan_horizon"], "Single year")
		self.assertEqual(item["preference"]["lotting_indicator"], "Single lot")
		self.assertEqual(item["preference"]["reservation_category"], "")
		self.assertEqual(item["baseline"]["periods"]["tendering_period_days"], 21)
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
			mode="combined", combination_reason=COMBINATION_REASON,
			expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		self.assertTrue(result["single"])
		item = plan_read.get_plan_item(plan_item_id=result["created_items"][0])
		self.assertTrue(item["combined"])
		self.assertEqual(len(item["sources"]), 2)
		self.assertIn("2 sources", item["sources_caption"])

	def test_a_combined_purchase_carries_the_reason_it_was_combined(self):
		"""§10.7 U08-COMBINE — the reason is captured where the Planner is
		asked for it, so the purchase is complete the moment it exists rather
		than arriving with a readiness blocker already on it."""
		accepted, entry_a, entry_b = self.accept_two(
			{"title": "Clinical training laptops"}, {"title": "Clinical deployment laptops"},
		)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		result = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"], dpp_entries=[entry_a, entry_b],
			mode="combined", combination_reason=COMBINATION_REASON,
			combined_title="Clinical training and deployment laptops for digital health rollout",
			expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		item = plan_read.get_plan_item(plan_item_id=result["created_items"][0])
		self.assertEqual(item["identity"]["aggregation_reason"], COMBINATION_REASON)
		self.assertEqual(item["identity"]["title"], "Clinical training and deployment laptops for digital health rollout")

	def test_combining_without_a_reason_is_refused(self):
		accepted, entry_a, entry_b = self.accept_two(
			{"title": "Requirement A"}, {"title": "Requirement B"},
		)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		for offered in ("", "Too short"):
			with self.subTest(reason=offered):
				with self.assertRaises(ProcurementPlanningError) as caught:
					plan_workbench.form_plan_items(
						plan_version=accepted["annual_plan_version"], dpp_entries=[entry_a, entry_b],
						mode="combined", combination_reason=offered,
						expected_record_version=plan["record_version"], idempotency_key=key(),
					)
				self.assertEqual(caught.exception.code, "PLN_ENTRY_INCOMPLETE")
		self.assertEqual(frappe.db.count("Annual Plan Item", {"fixture_namespace": fx.NS}), 0)

	def test_keeping_them_separate_never_invents_a_combination_reason(self):
		accepted, entry_a, entry_b = self.accept_two(
			{"title": "Requirement A"}, {"title": "Requirement B"},
		)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		result = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"], dpp_entries=[entry_a, entry_b],
			mode="each", combination_reason=COMBINATION_REASON,
			expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		for plan_item_id in result["created_items"]:
			with self.subTest(plan_item_id=plan_item_id):
				item = plan_read.get_plan_item(plan_item_id=plan_item_id)
				self.assertEqual(item["identity"]["aggregation_reason"], "")

	def test_the_combination_rule_names_what_actually_differs(self):
		"""The rule a screen reads is the rule the command enforces: same
		budget, requirement type, unit and kind of requirement (invariant 8)."""
		same = frappe._dict({"budget_line": fx.BUDGET_LINE, "classification": "Goods", "unit": "Each", "source_origin": "Direct requirement"})
		other_unit = frappe._dict({**same, "unit": "Programme"})
		other_type = frappe._dict({**same, "classification": "Works"})
		self.assertEqual(plan_workbench.combination_conflicts([same, frappe._dict(same)]), [])
		self.assertEqual(plan_workbench.combination_conflicts([same, other_unit]), ["They are measured in different units."])
		self.assertEqual(plan_workbench.combination_conflicts([same, other_type]), ["They are different requirement types."])

	def test_combined_mode_rejects_incompatible_classifications(self):
		accepted, entry_a, entry_b = self.accept_two(
			{"title": "Requirement A"}, {"title": "Requirement B"},
			class_a="Goods", class_b="Consulting services",
		)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.form_plan_items(
				plan_version=accepted["annual_plan_version"], dpp_entries=[entry_a, entry_b],
				mode="combined", combination_reason=COMBINATION_REASON,
				expected_record_version=plan["record_version"], idempotency_key=key(),
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
	def test_save_updates_allow_listed_fields_derives_baseline_and_snapshots_objective(self):
		_, item_id = self.one_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		result = plan_workbench.save_plan_item(
			plan_item=item_id,
			values=fx.item_values(title="Renamed procurement package", description="A sufficiently long procurement description for the package."),
			expected_record_version=item["record_version"], idempotency_key=key(),
		)
		self.assertEqual(result["action"], "saved")
		refreshed = plan_read.get_plan_item(plan_item_id=item_id)
		self.assertEqual(refreshed["identity"]["title"], "Renamed procurement package")
		self.assertEqual(refreshed["classification"]["strategic_objective"], fx.STRATEGY_OBJECTIVE)
		self.assertEqual(refreshed["classification"]["objective_path"], fx.STRATEGY_OBJECTIVE_PATH)
		# PLN-AC-115 — the seven baseline dates are derived from the anchor
		rows = {r["milestone"]: r["date"] for r in refreshed["baseline"]["rows"]}
		self.assertEqual(rows["invitation"], "2101-09-01")
		self.assertEqual(rows["bid_opening"], "2101-09-22")
		self.assertEqual(rows["evaluation_completion"], "2101-10-22")
		self.assertEqual(rows["award_approval"], "2101-10-27")
		self.assertEqual(rows["award_notification"], "2101-10-29")
		self.assertEqual(rows["contract_signing"], "2101-11-12")
		self.assertEqual(rows["delivery_completion"], "2102-04-30")
		self.assertTrue(refreshed["baseline"]["delivery_boundary_ok"])
		self.assertEqual(refreshed["blockers"], [])
		self.assertEqual(refreshed["preference"]["reservation_category"], "None")

	def test_save_rejects_unknown_and_derived_fields(self):
		_, item_id = self.one_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.save_plan_item(
				plan_item=item_id, values={"title": "x" * 10, "description": "y" * 20, "priority": "High"},
				expected_record_version=item["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_ENTRY_INCOMPLETE")
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.save_plan_item(
				plan_item=item_id, values={"baseline_bid_opening_date": "2101-10-01"},
				expected_record_version=item["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_SCHEDULE_INVALID")

	def test_governed_periods_are_enforced_server_side(self):
		"""PLN-AC-114 — floors and ceilings bound to their input."""
		_, item_id = self.one_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		for field, value, code in (
			("tendering_period_days", 6, "PLN_PROFILE_PERIOD_INVALID"),
			("evaluation_period_days", 31, "PLN_PROFILE_PERIOD_INVALID"),
			("standstill_period_days", 13, "PLN_PROFILE_PERIOD_INVALID"),
		):
			with self.subTest(field=field):
				with self.assertRaises(ProcurementPlanningError) as caught:
					plan_workbench.save_plan_item(
						plan_item=item_id, values=fx.item_values(**{field: value}),
						expected_record_version=item["record_version"], idempotency_key=key(),
					)
				self.assertEqual(caught.exception.code, code)
				self.assertEqual(caught.exception.detail.get("field"), field)

	def test_delivery_boundary_is_a_readiness_blocker_not_a_save_error(self):
		"""Invariant 12a — an anchor too close to the required-by date saves
		but blocks readiness with the exact code."""
		_, item_id = self.one_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.save_plan_item(
			plan_item=item_id, values=fx.item_values(baseline_invitation_date="2102-04-01"),
			expected_record_version=item["record_version"], idempotency_key=key(),
		)
		refreshed = plan_read.get_plan_item(plan_item_id=item_id)
		self.assertFalse(refreshed["baseline"]["delivery_boundary_ok"])
		self.assertIn("PLN_DELIVERY_BOUNDARY_INSUFFICIENT", [b["code"] for b in refreshed["blockers"]])

	def test_a_method_outside_the_resolved_band_is_refused(self):
		"""PLN-AC-070/091 — Low Value Procurement is not admissible for KES 1,000,000 of goods."""
		_, item_id = self.one_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		self.assertNotIn("Low Value Procurement", item["classification"]["admissible_methods"])
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.save_plan_item(
				plan_item=item_id, values=fx.item_values(procurement_method="Low Value Procurement"),
				expected_record_version=item["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_METHOD_NOT_ADMISSIBLE")
		self.assertEqual(caught.exception.detail["failed_conditions"], ["G-VALUE"])  # v1.18: the profile's known-fact limit
		saved = plan_workbench.save_plan_item(
			plan_item=item_id, values=fx.item_values(procurement_method="Request for Proposals"),
			expected_record_version=item["record_version"], idempotency_key=key(),
		)
		self.assertEqual(saved["action"], "saved")
		self.assertTrue(plan_read.get_plan_item(plan_item_id=item_id)["classification"]["value_band"])

	def test_plan_contents_and_reservation_rules(self):
		"""Invariants 24, 24aa, 24b."""
		_, item_id = self.one_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.save_plan_item(
				plan_item=item_id, values=fx.item_values(plan_horizon="Multi-year"),
				expected_record_version=item["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_MULTI_YEAR_UNSUPPORTED")  # v1.18 §4.6: fixed literal
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.save_plan_item(
				plan_item=item_id, values=fx.item_values(lotting_indicator="Packaged into lots"),
				expected_record_version=item["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_PLAN_CONTENTS_INCOMPLETE")
		# v1.18 §5.5.3.2 — a governed designation needs no reason and has no ranking; an ungoverned one is refused
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.save_plan_item(
				plan_item=item_id, values=fx.item_values(reservation_category="Friends of the Planner"),
				expected_record_version=item["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_RESERVATION_REQUIRED")
		saved = plan_workbench.save_plan_item(
			plan_item=item_id,
			values=fx.item_values(reservation_category="Women", lotting_indicator="Packaged into lots", lot_count=3),
			expected_record_version=item["record_version"], idempotency_key=key(),
		)
		self.assertEqual(saved["action"], "saved")
		refreshed = plan_read.get_plan_item(plan_item_id=item_id)
		self.assertEqual(refreshed["preference"]["lot_count"], 3)
		self.assertEqual(refreshed["preference"]["reservation_category"], "Women")

	def test_save_rejects_ineligible_objective(self):
		_, item_id = self.one_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.save_plan_item(
				plan_item=item_id, values=fx.item_values(strategic_objective="NOT-A-REAL-OBJECTIVE"),
				expected_record_version=item["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_OBJECTIVE_INELIGIBLE")


class TestProfilesEvidenceAndFeasibility(PlanWorkbenchCase):
	"""PLN-CHG-001 v1.18 §5.5.1 / §5.5.3.3 (PLN18-206)."""

	def test_a_formed_item_carries_the_profile_defaults_and_its_stable_root(self):
		_, item_id = self.one_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		self.assertTrue(frappe.db.exists("Plan Item", item_id))
		self.assertEqual(frappe.db.get_value("Annual Plan Item", {"plan_item_id": item_id}, "plan_item"), item_id)
		self.assertTrue(item["baseline"]["profile"]["found"])
		self.assertEqual(item["baseline"]["periods"]["tendering_period_days"], 21)
		self.assertEqual(item["baseline"]["estimated_delivery_period_days"], fx.DELIVERY_DEFAULT_DAYS)
		self.assertEqual(item["baseline"]["floors"], {"tendering_period_days": 7, "standstill_period_days": 14})
		self.assertEqual(item["baseline"]["ceilings"], {"evaluation_period_days": 30})
		self.assertTrue(item["classification"]["method_profile"]["found"])
		self.assertIn("Open Tender", item["classification"]["admissible_methods"])
		self.assertNotIn("Low Value Procurement", item["classification"]["admissible_methods"])
		self.assertEqual(item["scope_lock"], {"locked": False, "since": "", "first_requisition": "", "held": False, "open_requests": 0})

	def test_an_unset_strategic_objective_is_the_items_own_blocker_too(self):
		"""`get_plan_item`'s own `objective_eligible` had drifted from
		`plan_readiness`'s (found live 23 Sep 2026): an unset objective read as
		vacuously eligible here, so a freshly formed item carried no blocker
		and no flagged field on its own editor page, though the plan-level
		readiness this item's blockers are meant to mirror already refused it
		a Send to Finance and named "Choose a strategic objective" as its
		current work. Both reads must agree that unset is not eligible."""
		accepted, item_id = self.one_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		self.assertEqual(item["classification"]["strategic_objective"], "")
		self.assertTrue(
			any(b["code"] == "PLN_OBJECTIVE_INELIGIBLE" and b.get("field") == "strategic_objective" for b in item["blockers"]),
		)
		# The same fact, agreed on the plan-level read this item's own
		# blockers are meant to mirror.
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		objective_check = next(c for c in plan["readiness"] if c["check"] == "Every Plan Item has a Strategic Objective")
		self.assertEqual(objective_check["result"], "1 to fix")
		self.assertFalse(plan["can_request_funding"])

	def test_a_complete_item_reads_ready_on_the_annual_plan_screen_too(self):
		"""`get_annual_plan`'s own `_item_rows` fetched `Annual Plan Item` with
		an explicit field list that left out `strategic_objective`,
		`baseline_invitation_date` and `estimate_basis` (found live 23 Sep
		2026): `frappe.get_all` returns nothing for a field it was never
		asked for, so `_current_work` read every one of those as unset
		regardless of the real value, and a fully complete purchase went on
		showing "Choose a strategic objective" forever — disagreeing with
		its own editor, which reads the whole document and saw nothing
		wrong. A save with every field set must read Ready in both places."""
		accepted, item_id = self.one_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.save_plan_item(
			plan_item=item_id, values=fx.item_values(),
			expected_record_version=item["record_version"], idempotency_key=key(),
		)
		refreshed = plan_read.get_plan_item(plan_item_id=item_id)
		self.assertEqual(refreshed["blockers"], [])
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		row = next(r for r in plan["plan_items"] if r["plan_item_id"] == item_id)
		self.assertEqual(row["current_work"], "Ready")

	def test_an_infeasible_but_dated_schedule_is_not_ready_either(self):
		"""`_current_work` used to check only whether `baseline_invitation_date`
		was set, never whether the resulting completion actually meets the
		departmental deadline — so a purchase with a date entered but an
		infeasible delivery estimate read "Ready" on this screen while Plan
		checks' Schedule count still counted it (found live 23 Sep 2026).
		Current work must name the same blocker Plan checks counts, and the
		count's own wording must be grammatical and point back to it."""
		accepted, item_id = self.one_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.save_plan_item(
			plan_item=item_id, values=fx.item_values(estimated_delivery_period_days=3650),
			expected_record_version=item["record_version"], idempotency_key=key(),
		)
		refreshed = plan_read.get_plan_item(plan_item_id=item_id)
		self.assertIn("PLN_DELIVERY_BOUNDARY_INSUFFICIENT", [b["code"] for b in refreshed["blockers"]])
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		row = next(r for r in plan["plan_items"] if r["plan_item_id"] == item_id)
		self.assertEqual(row["current_work"], "Review the dates against the departmental deadline")
		schedule_check = next(c for c in plan["plan_checks"] if c["label"] == "Schedule")
		self.assertEqual(schedule_check["result"], "1 purchase does not yet meet its departmental deadline — see Current work above")

	def test_the_schedule_check_counts_distinct_purchases_not_blockers(self):
		"""A purchase missing both its invitation date and its delivery
		period carries two schedule-coded blockers at once; the Schedule
		count must read the distinct purchases affected, not the blocker
		entries (found live 23 Sep 2026: a plan with one such purchase read
		"2 purchases do not meet their departmental deadlines")."""
		accepted, item_id = self.one_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.save_plan_item(
			plan_item=item_id,
			values=fx.item_values(baseline_invitation_date="", estimated_delivery_period_days=""),
			expected_record_version=item["record_version"], idempotency_key=key(),
		)
		refreshed = plan_read.get_plan_item(plan_item_id=item_id)
		codes = [b["code"] for b in refreshed["blockers"]]
		self.assertIn("PLN_SCHEDULE_INVALID", codes)
		self.assertIn("PLN_DELIVERY_PERIOD_REQUIRED", codes)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		schedule_check = next(c for c in plan["plan_checks"] if c["label"] == "Schedule")
		self.assertEqual(schedule_check["result"], "1 purchase does not yet meet its departmental deadline — see Current work above")

	def test_the_item_editor_read_model_carries_a_total_quantity_and_a_restrictions_line(self):
		"""PLN18-305 (U09 Plan Item editor): `get_plan_item()` needs one
		aggregate quantity display (the single-source case already has its own
		via `sources[0]`, but a combined item's own "Quantity" fact in Package
		details has no per-source string to reuse) and the Reservation and
		structure card's own "Mandatory restrictions" fact — a static line for
		now since no restriction-computation mechanism exists yet in this
		cycle (matching the spec's own "read-only example text")."""
		_, item_id = self.one_item()
		single = plan_read.get_plan_item(plan_item_id=item_id)
		self.assertEqual(single["total_quantity_display"], single["sources"][0]["quantity_display"])
		self.assertEqual(single["preference"]["mandatory_restrictions_line"], "No additional restriction applies")

	def test_a_combined_item_sums_quantity_across_its_sources(self):
		accepted, entry_a, entry_b = self.accept_two(
			{"title": "Clinical training laptops", "quantity": 100, "budget_line": fx.BUDGET_LINE},
			{"title": "Clinical deployment laptops", "quantity": 150, "budget_line": fx.BUDGET_LINE_2},
		)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		formed = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"], dpp_entries=[entry_a, entry_b],
			mode="combined", combination_reason=COMBINATION_REASON,
			expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		combined = plan_read.get_plan_item(plan_item_id=formed["created_items"][0])
		self.assertEqual(combined["total_quantity_display"], "250 each")

	def test_a_method_without_a_schedule_profile_permits_draft_work_but_blocks_submission(self):
		_, item_id = self.one_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		saved = plan_workbench.save_plan_item(
			plan_item=item_id, values=fx.item_values(procurement_method="Design Competition"),
			expected_record_version=item["record_version"], idempotency_key=key(),
		)
		self.assertEqual(saved["action"], "saved")
		refreshed = plan_read.get_plan_item(plan_item_id=item_id)
		self.assertFalse(refreshed["baseline"]["profile"]["found"])
		self.assertIn("PLN_REFERENCE_UNAVAILABLE", [b["code"] for b in refreshed["blockers"]])
		self.assertIsNone(frappe.db.get_value("Annual Plan Item", {"plan_item_id": item_id}, "schedule_profile_version"))

	def test_a_declaration_method_needs_its_evidence_before_submission(self):
		_, item_id = self.one_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		saved = plan_workbench.save_plan_item(
			plan_item=item_id, values=fx.item_values(procurement_method="Direct Procurement"),
			expected_record_version=item["record_version"], idempotency_key=key(),
		)
		self.assertEqual(saved["action"], "saved")
		refreshed = plan_read.get_plan_item(plan_item_id=item_id)
		codes = [b["code"] for b in refreshed["blockers"]]
		self.assertIn("PLN_METHOD_EVIDENCE_REQUIRED", codes)
		self.assertIn("PLN_REFERENCE_UNAVAILABLE", codes)  # Direct Procurement has no schedule profile in the fixture
		self.assertEqual(refreshed["classification"]["method_profile"]["missing_evidence"], ["CIRCUMSTANCES"])
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.save_plan_item(
				plan_item=item_id, values={"method_condition_evidence": [{"evidence_reference": "no id"}]},
				expected_record_version=saved["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_ENTRY_INCOMPLETE")
		evidenced = plan_workbench.save_plan_item(
			plan_item=item_id,
			values={"method_condition_evidence": [{"condition_id": "CIRCUMSTANCES", "evidence_reference": "MER-PLNT-001", "authorisation_reference": "AO/2101/DP/1"}]},
			expected_record_version=saved["record_version"], idempotency_key=key(),
		)
		self.assertEqual(evidenced["action"], "saved")
		refreshed = plan_read.get_plan_item(plan_item_id=item_id)
		self.assertNotIn("PLN_METHOD_EVIDENCE_REQUIRED", [b["code"] for b in refreshed["blockers"]])
		self.assertTrue(refreshed["classification"]["method_profile"]["evidence_complete"])

	def test_estimate_basis_and_delivery_period_are_required_and_zero_is_explicit(self):
		_, item_id = self.one_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		values = fx.item_values(estimate_basis="", estimate_basis_reference="", estimated_delivery_period_days="")
		saved = plan_workbench.save_plan_item(plan_item=item_id, values=values, expected_record_version=item["record_version"], idempotency_key=key())
		refreshed = plan_read.get_plan_item(plan_item_id=item_id)
		fields = {(b["code"], b["field"]) for b in refreshed["blockers"]}
		self.assertIn(("PLN_PLAN_CONTENTS_INCOMPLETE", "estimate_basis"), fields)
		self.assertIn(("PLN_PLAN_CONTENTS_INCOMPLETE", "estimate_basis_reference"), fields)
		self.assertIn(("PLN_DELIVERY_PERIOD_REQUIRED", "estimated_delivery_period_days"), fields)
		self.assertIsNone(refreshed["baseline"]["estimated_delivery_period_days"])
		zero = plan_workbench.save_plan_item(plan_item=item_id, values=fx.item_values(estimated_delivery_period_days=0), expected_record_version=saved["record_version"], idempotency_key=key())
		refreshed = plan_read.get_plan_item(plan_item_id=item_id)
		self.assertEqual(refreshed["baseline"]["estimated_delivery_period_days"], 0)
		self.assertEqual(refreshed["baseline"]["estimated_completion_date"], "2101-11-12")
		self.assertNotIn("PLN_DELIVERY_PERIOD_REQUIRED", [b["code"] for b in refreshed["blockers"]])
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.save_plan_item(plan_item=item_id, values=fx.item_values(estimated_delivery_period_days=-1), expected_record_version=zero["record_version"], idempotency_key=key())
		self.assertEqual(caught.exception.code, "PLN_DELIVERY_PERIOD_REQUIRED")

	def test_version_details_project_name_and_change_reason(self):
		accepted, item_id = self.one_item()
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.save_plan_version_details(
				plan_version=accepted["annual_plan_version"], values={"project_name": "x" * 161},
				expected_record_version=plan["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_ENTRY_INCOMPLETE")
		saved = plan_workbench.save_plan_version_details(
			plan_version=accepted["annual_plan_version"], values={"project_name": "Digital health rollout", "change_reason": ""},
			expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		self.assertEqual(saved["action"], "details_saved")
		self.assertEqual(frappe.db.get_value("Annual Plan Version", accepted["annual_plan_version"], "project_name"), "Digital health rollout")
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.save_plan_version_details(
				plan_version=accepted["annual_plan_version"], values={"budget": "x"},
				expected_record_version=saved["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_ENTRY_INCOMPLETE")


class TestScopeLock(PlanWorkbenchCase):
	"""PLN-CHG-001 v1.18 §5.4.6 — the stable item's procurement-scope lock."""

	def lock(self, item_id: str) -> None:
		frappe.db.set_value("Plan Item", item_id, {"scope_locked_since": "2101-10-01 09:00:00", "first_authorised_requisition": "REQ-TEST-1"}, update_modified=False)

	def test_a_locked_item_keeps_its_package_but_its_schedule_stays_editable(self):
		_, item_id = self.one_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.save_plan_item(plan_item=item_id, values=fx.item_values(), expected_record_version=item["record_version"], idempotency_key=key())
		self.lock(item_id)
		item = plan_read.get_plan_item(plan_item_id=item_id)
		self.assertTrue(item["scope_lock"]["locked"])
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.save_plan_item(
				plan_item=item_id, values=fx.item_values(title="A wider procurement package"),
				expected_record_version=item["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_ITEM_SCOPE_LOCKED")
		self.assertEqual(caught.exception.detail["fields"], ["title"])
		unchanged = {k: v for k, v in fx.item_values().items() if k not in ("title", "description")}
		saved = plan_workbench.save_plan_item(
			plan_item=item_id, values={**unchanged, "baseline_invitation_date": "2101-10-01"},
			expected_record_version=item["record_version"], idempotency_key=key(),
		)
		self.assertEqual(saved["action"], "saved")

	def test_a_locked_item_cannot_be_dissolved_or_its_source_re_formed(self):
		accepted, item_id = self.one_item()
		self.lock(item_id)
		item = plan_read.get_plan_item(plan_item_id=item_id)
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.dissolve_plan_item(plan_item=item_id, expected_record_version=item["record_version"], idempotency_key=key())
		self.assertEqual(caught.exception.code, "PLN_ITEM_SCOPE_LOCKED")
		entry = frappe.db.get_value("Plan Source Allocation", {"plan_item_id": item_id}, "dpp_entry")
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.form_plan_items(
				plan_version=accepted["annual_plan_version"], dpp_entries=[entry], mode="each",
				expected_record_version=plan["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_ITEM_SCOPE_LOCKED")
		self.assertEqual(caught.exception.detail["plan_item_ids"], [item_id])


class TestReservationAllocations(PlanWorkbenchCase):
	"""The reserved-procurement target is a share of what the plan actually
	plans to buy, not of the approved budget ceiling.

	Corrected 24 Sep 2026 on the owner's written ruling
	(`docs/mvp-1-r1/99_other/thirty_percent_reservation_rule.pdf`). The
	approved budget authorises spending; it does not oblige it. Measuring the
	30% against it turned unused budget headroom into a compulsory
	procurement target: a plan of KES 464,980 against a KES 160,000,000
	ceiling was asked for KES 48,000,000 of reserved allocation, which it
	could not reach even if every purchase in it were designated. The
	ceiling's own job — the plan must fit inside it — belongs to the
	affordability check and is untouched.
	"""

	def _published(self, plan, **over):
		reference = {**readiness.reference_for(plan.fiscal_year)}
		reference["reservation"] = {**reference["reservation"], "target_percent": 30.0, "published": True, **over}
		reference["verification_status"] = fx.VERIFICATION_FIXTURE
		return reference

	def test_required_and_shortfall_are_a_share_of_the_planned_value(self):
		accepted, item_id = self.one_item()
		version = frappe.get_doc("Annual Plan Version", accepted["annual_plan_version"])
		plan = frappe.get_doc("Annual Plan", version.annual_plan)
		reference = self._published(plan)
		share = readiness.reservation_allocations(version.name, plan.fiscal_year, reference)
		self.assertEqual(share["eligible_value"], "1000000.00")
		self.assertEqual(share["plan_total"], "1000000.00")
		self.assertEqual(share["required"], "300000.00")  # 30% of the plan, not of the budget
		self.assertEqual(share["qualifying"], "0.00")
		self.assertEqual(share["remaining"], "300000.00")
		self.assertEqual(share["qualifying_share_percent"], "0.00")
		self.assertFalse(share["met"])
		self.assertTrue(share["mandatory"] and share["verified"])

	def test_the_canonical_fixture_calculates_exactly(self):
		"""PLN25-AC-005 / BUD20-AC-004: 30% of KES 130,000,000 = 39,000,000;
		KES 50,000,000 designated Youth is 38.46% and leaves nothing
		remaining. The KES 160,000,000 Budget ceiling is not an input."""
		rows = [
			readiness.measure_row("PPI-A", "Digital health infrastructure", Decimal("80000000"), "None"),
			readiness.measure_row("PPI-B", "Clinical training laptops", Decimal("50000000"), "Youth"),
		]
		measure = readiness.reservation_measure(rows, 30)
		self.assertEqual(measure["eligible"], Decimal("130000000.00"))
		self.assertEqual(measure["required"], Decimal("39000000.00"))
		self.assertEqual(measure["qualifying"], Decimal("50000000.00"))
		self.assertEqual(measure["remaining"], Decimal("0.00"))
		self.assertEqual(measure["share"], Decimal("38.46"))
		self.assertEqual([r["qualifying"] for r in rows], [Decimal("0"), Decimal("50000000")])
		base = readiness.reservation_measure([readiness.measure_row("PPI-A", "A", Decimal("80000000"), "None"), readiness.measure_row("PPI-B", "B", Decimal("50000000"), "None")], 30)
		self.assertEqual(base["remaining"], Decimal("39000000.00"))

	def test_an_excluded_purchase_leaves_the_denominator_with_its_reason(self):
		"""PLN25-AC-003: the denominator is the sum of the purchases the rule
		includes; an exclusion keeps its row and its reason, never vanishes."""
		rows = [
			readiness.measure_row("PPI-A", "A", Decimal("100"), "Youth"),
			{**readiness.measure_row("PPI-B", "B", Decimal("900"), "None"), "applicability": "Excluded", "reason": "Excluded by the rule"},
		]
		measure = readiness.reservation_measure(rows, 30)
		self.assertEqual(measure["eligible"], Decimal("100.00"))
		self.assertEqual(measure["required"], Decimal("30.00"))
		self.assertEqual(len(rows), 2)

	def test_every_current_purchase_is_accounted_for_with_the_exact_basis(self):
		"""PLN25-AC-003: every current Plan Item is included or excluded with a
		reason, and the calculation names the exact Plan Version and rule
		Version it was made under."""
		accepted, item_id = self.one_item()
		version = frappe.get_doc("Annual Plan Version", accepted["annual_plan_version"])
		plan = frappe.get_doc("Annual Plan", version.annual_plan)
		reference = self._published(plan)
		share = readiness.reservation_allocations(version.name, plan.fiscal_year, reference)
		self.assertEqual([r["plan_item_id"] for r in share["items"]], [item_id])
		row = share["items"][0]
		self.assertEqual(row["applicability"], "Included")
		self.assertTrue(row["reason"])
		self.assertEqual(row["designation"], "None")
		self.assertEqual(row["value"], "1000000.00")
		self.assertEqual(row["qualifying"], "0.00")
		self.assertEqual(share["plan_basis"], f"{plan.plan_reference}, Version {version.version_number}")
		self.assertEqual(share["rule_reference"], reference["reference"])
		self.assertTrue(share["rule_version"])
		self.assertEqual(share["mandatory_restrictions"], "No additional restriction applies")

	def test_the_approved_budget_is_not_an_input(self):
		"""PLN25-AC-001/002, BUD20-AC-003: the calculation reads no Budget at
		all — no basis block, no share of the annual budget — so unused
		Budget headroom can never enter the denominator."""
		accepted, item_id = self.one_item()
		version = frappe.get_doc("Annual Plan Version", accepted["annual_plan_version"])
		plan = frappe.get_doc("Annual Plan", version.annual_plan)
		reference = self._published(plan)
		from kentender_procurement.procurement_planning.services import budget_gateway

		self.assertFalse(hasattr(budget_gateway, "annual_budget_basis"))
		share = readiness.reservation_allocations(version.name, plan.fiscal_year, reference)
		self.assertEqual(share["required"], "300000.00")
		for gone in ("basis", "percent_of_annual", "shortfall"):
			self.assertNotIn(gone, share)
		# PLN25-AC-006: Planning makes no actual-achievement figure.
		self.assertFalse([k for k in share if "actual" in k])
		with patch.object(readiness, "reference_for", return_value=reference):
			report = plan_read.plan_readiness(version, plan, stage="submission")
		self.assertIn("PLN_RESERVATION_SHORTFALL", [b["code"] for b in report["blockers"]])
		row = next(c for c in report["checks"] if c["check"] == "Planned reservation allocation")
		self.assertNotIn("budget", row["result"].lower())

	def test_only_the_four_base_designations_are_offered_and_accepted(self):
		"""None, Youth, Women and Persons with disabilities. County is a
		separate measure; the catalogue's other entries are not Planning
		designations."""
		accepted, item_id = self.one_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		self.assertEqual(item["preference"]["reservation_categories"], list(readiness.BASE_RESERVATION_CATEGORIES))
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.save_plan_item(
				plan_item=item_id, values=fx.item_values(reservation_category="Micro, small and medium enterprise"),
				expected_record_version=item["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_RESERVATION_REQUIRED")
		plan_workbench.save_plan_item(
			plan_item=item_id, values=fx.item_values(reservation_category="Persons with disabilities"),
			expected_record_version=item["record_version"], idempotency_key=key(),
		)
		self.assertEqual(plan_read.get_plan_item(plan_item_id=item_id)["preference"]["reservation_category"], "Persons with disabilities")

	def test_a_designated_purchase_can_actually_clear_the_target(self):
		accepted, item_id = self.one_item()
		version = frappe.get_doc("Annual Plan Version", accepted["annual_plan_version"])
		plan = frappe.get_doc("Annual Plan", version.annual_plan)
		reference = self._published(plan)
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.save_plan_item(
			plan_item=item_id, values=fx.item_values(reservation_category="Youth"),
			expected_record_version=item["record_version"], idempotency_key=key(),
		)
		share = readiness.reservation_allocations(version.name, plan.fiscal_year, reference)
		self.assertEqual(share["qualifying"], "1000000.00")
		self.assertEqual(share["qualifying_items"], [item_id])
		self.assertEqual(share["remaining"], "0.00")
		self.assertTrue(share["met"])
		self.assertEqual(share["qualifying_share_percent"], "100.00")

	def test_the_county_target_uses_the_same_planned_value(self):
		accepted, item_id = self.one_item()
		version = frappe.get_doc("Annual Plan Version", accepted["annual_plan_version"])
		plan = frappe.get_doc("Annual Plan", version.annual_plan)
		reference = self._published(plan, county_target_percent=20.0)
		with patch.object(frappe.db, "get_single_value", return_value=True):
			share = readiness.reservation_allocations(version.name, plan.fiscal_year, reference)
		self.assertEqual(share["county"]["required"], "200000.00")  # 20% of the plan
		self.assertEqual(share["county"]["remaining"], "200000.00")

	def test_the_shortfall_blocks_submission_only_but_is_still_reported_on_a_draft(self):
		"""A Draft may be incomplete, so the shortfall never refuses a
		funding request. It must still be visible while the plan is being
		prepared: the Plan checks row reads it from the calculation, not
		from the blocker list, which is how it came to claim "Required
		allocation met" over a KES 48,000,000 shortfall (found live 23 Sep
		2026)."""
		accepted, item_id = self.one_item()
		version = frappe.get_doc("Annual Plan Version", accepted["annual_plan_version"])
		plan = frappe.get_doc("Annual Plan", version.annual_plan)
		reference = self._published(plan)
		with patch.object(readiness, "reference_for", return_value=reference):
			self.assertIn("PLN_RESERVATION_SHORTFALL", [b["code"] for b in plan_read.plan_readiness(version, plan, stage="submission")["blockers"]])
			report = plan_read.plan_readiness(version, plan)
			self.assertNotIn("PLN_RESERVATION_SHORTFALL", [b["code"] for b in report["blockers"]])
			row = next(c for c in plan_read._plan_checks(version, plan, report) if c["label"] == "Reserved procurement")
		self.assertEqual(row["result"], "KES 300,000 more qualifying allocation required")
		self.assertEqual(row["kind"], "critical")
		self.assertEqual(row["action"], "Review reserved procurement")

	def test_an_unverified_rule_is_named_as_that_and_never_as_a_shortfall(self):
		accepted, item_id = self.one_item()
		version = frappe.get_doc("Annual Plan Version", accepted["annual_plan_version"])
		plan = frappe.get_doc("Annual Plan", version.annual_plan)
		pending = {**self._published(plan), "verification_status": "Production verification pending"}
		with patch.object(readiness, "reference_for", return_value=pending):
			codes = [b["code"] for b in plan_read.plan_readiness(version, plan, stage="submission")["blockers"]]
			row = next(c for c in plan_read._plan_checks(version, plan, plan_read.plan_readiness(version, plan)) if c["label"] == "Reserved procurement")
		self.assertIn("PLN_REFERENCE_UNAVAILABLE", codes)
		self.assertNotIn("PLN_RESERVATION_SHORTFALL", codes)
		self.assertEqual(row["result"], "The reserved-procurement rule is missing or unverified")
		self.assertEqual(row["kind"], "critical")

	def test_a_mandatory_shortfall_is_the_workspaces_second_quieter_issue(self):
		"""PLN v1.27 §10.3 (D2): the missing method is the dominant pre-Finance
		issue; the reservation shortfall follows it, quieter, and blocks only
		signature. The v1.24 sentence "Resolve this before sending the plan
		to Finance" contradicted §5.5.3.1 and is retired."""
		accepted, item_id = self.one_item()
		# as §10.3's BASE fixture: everything complete except the method
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.save_plan_item(
			plan_item=item_id, values=fx.item_values(procurement_method=""),
			expected_record_version=item["record_version"], idempotency_key=key(),
		)
		version = frappe.get_doc("Annual Plan Version", accepted["annual_plan_version"])
		plan = frappe.get_doc("Annual Plan", version.annual_plan)
		reference = self._published(plan)
		with patch.object(readiness, "reference_for", return_value=reference):
			issues = workspace.get_planning_workspace(financial_year=fx.FY_OPEN, user=fx.PLANNER)["issues"]
		self.assertEqual([i["tone"] for i in issues], ["dominant", "quiet"])
		self.assertEqual(issues[0]["strong"], "1 purchase needs a procurement method.")
		self.assertEqual(issues[0]["text"], "1 purchase needs a procurement method. Choose it before sending the plan to Finance.")
		self.assertEqual(issues[0]["action"], "Choose a procurement method")
		self.assertEqual(issues[0]["route"], ["procurement-plan-item", item_id])
		self.assertEqual(
			issues[1]["text"],
			"Reserved procurement is below the required allocation by KES 300,000. "
			"Resolve this before the plan can be signed and submitted.",
		)
		self.assertEqual(issues[1]["strong"], "KES 300,000")
		self.assertEqual(issues[1]["action"], "Review reserved procurement")


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
		# new document under the same stable entry_id (§12.7) — and here the
		# department changes its funding, so the allocated copy is stale
		frappe.set_user(fx.HOD)
		update = dpp_lifecycle.create_departmental_plan_update(
			departmental_plan=dpp_root,
			expected_record_version=frappe.db.get_value("Departmental Plan", dpp_root, "record_version"),
			idempotency_key=key(),
		)
		changed = dpp_lifecycle.save_direct_requirement(
			dpp_version=update["current_version"], entry_id=entry_id,
			values=fx.direct_values(indicative_amount=2000000),
			expected_record_version=update["record_version"], idempotency_key=key(),
		)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=update["current_version"], certification_confirmed=True,
			expected_record_version=changed["record_version"], idempotency_key=key(),
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
				values={"title": flagged["identity"]["title"], "description": flagged["identity"]["description"]},
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

	def test_an_unchanged_successor_copy_is_the_same_source(self):
		"""§7.1 — a DPP update that only *adds* a requirement copies the
		existing entries verbatim. The allocated predecessor copy and the
		current copy are one source: no correction flag, nothing re-offered as
		unallocated, no duplicate item formable (agreed 2026-09-11)."""
		accepted, item_id = self.one_item()
		allocated_entry = frappe.get_all("Plan Source Allocation", filters={"plan_item_id": item_id}, pluck="dpp_entry")[0]
		dpp_root = frappe.db.get_value("Departmental Plan", {"dpp_reference": accepted["dpp_reference"]})

		frappe.set_user(fx.HOD)
		update = dpp_lifecycle.create_departmental_plan_update(
			departmental_plan=dpp_root,
			expected_record_version=frappe.db.get_value("Departmental Plan", dpp_root, "record_version"),
			idempotency_key=key(),
		)
		added = dpp_lifecycle.save_direct_requirement(
			dpp_version=update["current_version"], values=fx.direct_values(title="Late requirement"),
			expected_record_version=update["record_version"], idempotency_key=key(),
		)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=update["current_version"], certification_confirmed=True,
			expected_record_version=added["record_version"], idempotency_key=key(),
		)
		task2 = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
		frappe.set_user(fx.PLANNER)
		copied_entry_id = frappe.db.get_value("Departmental Plan Entry", allocated_entry, "entry_id")
		dpp_validation.accept_departmental_plan(
			task=task2.name, classifications={copied_entry_id: "Goods", added["entry_id"]: "Goods"},
			task_token=task2.task_token, idempotency_key=key(),
		)
		current_copy = frappe.db.get_value(
			"Departmental Plan Entry", {"dpp_version": update["current_version"], "entry_id": copied_entry_id}, "name",
		)
		self.assertNotEqual(current_copy, allocated_entry)

		self.assertFalse(plan_read.get_plan_item(plan_item_id=item_id)["source_correction_required"])
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertFalse(plan["plan_items"][0]["source_correction_required"])
		self.assertEqual(plan["summary"]["accepted_entries"], 2)
		self.assertEqual(plan["summary"]["allocated"], 1)
		self.assertEqual([row["entry_id"] for row in plan["unallocated_sources"]], [added["entry_id"]])
		self.assertNotIn("PLN_SOURCE_CORRECTION_REQUIRED", [b["code"] for b in plan["blockers"]])

		# the current copy cannot be formed into a second item
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_workbench.form_plan_items(
				plan_version=accepted["annual_plan_version"], dpp_entries=[current_copy],
				mode="each", expected_record_version=plan["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_SOURCE_UNAVAILABLE")

		# the workspace offers only the genuinely new entry for consolidation
		# — as the open Draft's own current issue (§7.1), not a second,
		# separate "actionable" card repeating the same route.
		from kentender_procurement.procurement_planning.services import workspace

		issues = workspace.get_planning_workspace(financial_year=fx.FY_OPEN, user=fx.PLANNER)["issues"]
		consolidate = [i for i in issues if "ready to consolidate into this plan" in i["text"]]
		self.assertEqual(len(consolidate), 1)
		self.assertIn("1 accepted departmental entry", consolidate[0]["text"])
