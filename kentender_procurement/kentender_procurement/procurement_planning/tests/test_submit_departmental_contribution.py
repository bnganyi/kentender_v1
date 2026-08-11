# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-008 / PLN-AC-005 — departmental contribution submit."""

from __future__ import annotations

import uuid

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.mvp1_constants import DEPT_SUBMITTED
from kentender_procurement.procurement_planning.services.add_demand_to_plan import (
	add_demand_to_plan,
)
from kentender_procurement.procurement_planning.services.get_departmental_contribution import (
	get_departmental_contribution,
)
from kentender_procurement.procurement_planning.services.get_plan_builder import (
	get_plan_builder,
)
from kentender_procurement.procurement_planning.services.submit_departmental_contribution import (
	submit_departmental_contribution,
)
from kentender_procurement.procurement_planning.services.validate_plan import validate_plan
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	complete_plan_item_for_signoff,
	create_plan_as_planner,
	ensure_hod_user,
	ensure_planner_user,
	ensure_scope,
	make_approved_demand,
)


def _unique_fy(bucket: int) -> str:
	"""High-year FY unique per call; purge PE+FY before create to avoid collisions."""
	n = int(uuid.uuid4().hex[:5], 16) % 800 + 100
	y = 2500 + bucket * 100 + n
	return f"{y}/{str(y + 1)[-2:]}"


def _purge_pe_fy(financial_year: str) -> None:
	scope = ensure_scope()
	pe = scope["pe"]
	for name in frappe.get_all(
		"Procurement Plan",
		filters={"procuring_entity": pe, "financial_year": financial_year},
		pluck="name",
	):
		frappe.delete_doc("Procurement Plan", name, force=True, ignore_permissions=True)
	# Orphan versions left when plan rows were force-cleared in older runs.
	for name in frappe.get_all(
		"Procurement Plan Version",
		filters={"name": ("like", f"PLN-%{financial_year.replace('/', '-')}-%")},
		pluck="name",
	):
		frappe.delete_doc("Procurement Plan Version", name, force=True, ignore_permissions=True)
	frappe.db.commit()


class TestSubmitDepartmentalContribution(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_scope()

	def _ready_item(self):
		planner = ensure_planner_user()
		hod = ensure_hod_user()
		fy = _unique_fy(0)
		_purge_pe_fy(fy)
		plan = create_plan_as_planner(title="Dept contrib plan", financial_year=fy)
		d = make_approved_demand(title="Dept contrib demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		complete_plan_item_for_signoff(plan_item=added["plan_item"], user=planner)
		validate_plan(plan=plan["plan"], user=planner)
		return planner, hod, plan["plan"], added["plan_item"]

	def test_hod_submits_with_declaration(self) -> None:
		_planner, hod, plan, _item = self._ready_item()
		proj = get_departmental_contribution(plan=plan, user=hod)
		self.assertTrue(proj["can_submit"], proj)
		self.assertEqual(proj["validation_projection"], "Ready")
		result = submit_departmental_contribution(
			plan=plan,
			organisation_unit=proj["organisation_unit"],
			declaration=1,
			submission_note="Ready for consolidation",
			user=hod,
		)
		self.assertTrue(result["ok"], result)
		self.assertEqual(result["contribution_status"], DEPT_SUBMITTED)
		builder = get_plan_builder(plan=plan, user=hod)
		self.assertEqual(builder["departmental_contributions_label"], "Submitted")
		self.assertFalse(builder["can_submit_departmental"])
		self.assertEqual(builder["next_step_kind"], "submit_review")
		self.assertIn("review", builder["next_step_message"].lower())

	def test_missing_declaration_returns_field_error(self) -> None:
		_planner, hod, plan, _item = self._ready_item()
		result = submit_departmental_contribution(plan=plan, declaration=0, user=hod)
		self.assertFalse(result["ok"])
		self.assertIn("declaration", result["errors"])

	def test_incomplete_item_blocks_submit(self) -> None:
		planner = ensure_planner_user()
		hod = ensure_hod_user()
		fy = _unique_fy(1)
		_purge_pe_fy(fy)
		plan = create_plan_as_planner(title="Incomplete contrib plan", financial_year=fy)
		d = make_approved_demand(title="Incomplete contrib demand")
		add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		# No schedule/method completion → Needs attention
		result = submit_departmental_contribution(plan=plan["plan"], declaration=1, user=hod)
		self.assertFalse(result["ok"])
		self.assertIn("form", result["errors"])

	def test_planner_without_hod_denied(self) -> None:
		planner, _hod, plan, _item = self._ready_item()
		with self.assertRaises(frappe.PermissionError):
			submit_departmental_contribution(plan=plan, declaration=1, user=planner)

	def test_builder_next_step_for_planner_when_ready(self) -> None:
		planner, hod, plan, _item = self._ready_item()
		as_planner = get_plan_builder(plan=plan, user=planner)
		self.assertEqual(as_planner["next_step_kind"], "await_hod")
		self.assertIn("Head of User Department", as_planner["next_step_message"])
		self.assertFalse(as_planner["can_submit_departmental"])
		self.assertEqual(
			as_planner["departmental_contributions_label"], "Awaiting HoD sign-off"
		)
		as_hod = get_plan_builder(plan=plan, user=hod)
		self.assertEqual(as_hod["next_step_kind"], "submit_dept")
		self.assertTrue(as_hod["can_submit_departmental"])
		self.assertIn("Submit the departmental contribution", as_hod["next_step_message"])

	def test_already_submitted_blocks_resubmit(self) -> None:
		_planner, hod, plan, _item = self._ready_item()
		first = submit_departmental_contribution(plan=plan, declaration=1, user=hod)
		self.assertTrue(first["ok"], first)
		second = submit_departmental_contribution(plan=plan, declaration=1, user=hod)
		self.assertFalse(second["ok"])
		self.assertIn("form", second["errors"])
