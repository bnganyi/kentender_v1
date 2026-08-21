# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-GATE-C02 — contribution / Departmental Submission must be absent."""

from __future__ import annotations

import importlib
import inspect

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning import mvp1_constants
from kentender_procurement.procurement_planning.services import planning_permissions
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	add_demand_to_plan,
)
from kentender_procurement.procurement_planning.services.submit_plan_for_review import (
	submit_plan_for_review,
)
from kentender_procurement.procurement_planning.services.validate_plan import validate_plan
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	complete_plan_item_for_signoff,
	confirm_included_items_funding,
	create_plan_as_planner,
	ensure_planner_user,
	ensure_scope,
	make_approved_demand,
	purge_pe_fy,
	unique_test_fy,
)


class TestPlanningContributionAbsent(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_scope()

	def test_doctype_and_constants_gone(self) -> None:
		self.assertFalse(frappe.db.exists("DocType", "Departmental Submission"))
		self.assertNotIn("Departmental Submission", mvp1_constants.MVP1_DOCTYPES)
		self.assertFalse(hasattr(mvp1_constants, "DOCTYPE_DEPT_SUBMISSION"))
		self.assertFalse(hasattr(planning_permissions, "CAP_DEPT_CONTRIB_TASK"))
		self.assertFalse(hasattr(planning_permissions, "DEPT_CONTRIB_TASK_ROLES"))
		self.assertFalse(
			hasattr(planning_permissions, "assert_can_submit_departmental_contribution")
		)

	def test_contribution_services_not_importable(self) -> None:
		with self.assertRaises(ModuleNotFoundError):
			importlib.import_module(
				"kentender_procurement.procurement_planning.services.get_departmental_contribution"
			)
		with self.assertRaises(ModuleNotFoundError):
			importlib.import_module(
				"kentender_procurement.procurement_planning.services.submit_departmental_contribution"
			)

	def test_api_module_has_no_contribution_methods(self) -> None:
		from kentender_procurement.procurement_planning import api as planning_api

		self.assertFalse(hasattr(planning_api, "get_departmental_contribution"))
		self.assertFalse(hasattr(planning_api, "submit_departmental_contribution"))
		src = inspect.getsource(planning_api)
		self.assertNotIn("get_departmental_contribution", src)
		self.assertNotIn("submit_departmental_contribution", src)

	def test_submit_for_review_without_contribution_rows(self) -> None:
		planner = ensure_planner_user()
		fy = unique_test_fy(base_year=2900, bucket=0)
		purge_pe_fy(fy)
		plan = create_plan_as_planner(title="C02 no contrib submit", financial_year=fy)
		d = make_approved_demand(title="C02 no contrib demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		complete_plan_item_for_signoff(plan_item=added["plan_item"], user=planner)
		confirm_included_items_funding(plan=plan["plan"], planner=planner)
		validate_plan(plan=plan["plan"], user=planner)
		token = frappe.db.get_value(
			"Procurement Plan Version", plan["version"], "concurrency_token"
		)
		result = submit_plan_for_review(
			plan=plan["plan"], concurrency_token=token, user=planner
		)
		self.assertTrue(result["ok"], result)

	def test_statutory_fields_purged_from_meta(self) -> None:
		meta = frappe.get_meta("Procurement Plan Item Version")
		for fieldname in (
			"statutory_treatment",
			"statutory_target_groups",
			"planned_treatment_value",
			"value_treatment_note",
			"section_retired_statutory",
		):
			self.assertIsNone(meta.get_field(fieldname), fieldname)
