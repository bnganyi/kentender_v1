# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-005 / PLN-AC-004 / PLN-AC-012 / PLN-AC-016."""

from __future__ import annotations

import uuid

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.services.add_demand_to_plan import (
	add_demand_to_plan,
)
from kentender_procurement.procurement_planning.services.update_plan_item import (
	update_plan_item,
)
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	create_plan_as_planner,
	ensure_planner_user,
	ensure_scope,
	make_approved_demand,
)


def _unique_fy() -> str:
	n = int(uuid.uuid4().hex[:5], 16) % 800 + 100
	y = 2600 + n
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
	fy_token = financial_year.replace("/", "-")
	for name in frappe.get_all(
		"Procurement Plan Version",
		filters={"name": ("like", f"PLN-%{fy_token}%")},
		pluck="name",
	):
		frappe.delete_doc("Procurement Plan Version", name, force=True, ignore_permissions=True)
	frappe.db.commit()


class TestUpdatePlanItem(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_scope()

	def _item(self):
		planner = ensure_planner_user()
		fy = _unique_fy()
		_purge_pe_fy(fy)
		plan = create_plan_as_planner(title="Update item plan", financial_year=fy)
		d = make_approved_demand(title="Editor demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		return planner, added["plan_item"]

	def test_saves_method_schedule_and_lotting(self) -> None:
		planner, item = self._item()
		result = update_plan_item(
			plan_item=item,
			user=planner,
			fields={
				"requirement_description": "Upgrade national DHI stack",
				"procurement_category": "ICT",
				"procurement_method": "Open tender",
				"arrangement": "Single year",
				"lotting_decision": "Multiple lots",
				"expected_lot_count": 2,
				"lot_basis": "Split by region for delivery capacity",
				"ms_invitation_published": "2027-09-15",
				"ms_tender_opening": "2027-10-20",
				"ms_evaluation_completed": "2027-11-15",
				"ms_award_approval": "2027-12-15",
				"ms_contract_signature": "2028-01-15",
				"ms_delivery_completion": "2028-03-31",
			},
		)
		self.assertTrue(result["ok"], result)

	def test_preference_designation_reserved_lots(self) -> None:
		planner, item = self._item()
		from kentender_procurement.procurement_planning.services.get_plan_item_editor import (
			get_plan_item_editor,
		)

		before = get_plan_item_editor(plan_item=item, user=planner)
		half = max(1.0, float(before["confirmed_estimate"] or 0) / 2.0)
		result = update_plan_item(
			plan_item=item,
			user=planner,
			fields={
				"preference_reservation_scheme": "AGPO reservation",
				"reservation_scope": "Reserved lot(s)",
				"eligible_groups": [
					"Women-owned enterprises",
					"Youth-owned enterprises",
				],
				"planned_reserved_value": half,
			},
		)
		self.assertTrue(result["ok"], result)
		proj = get_plan_item_editor(plan_item=item, user=planner)
		self.assertTrue(proj["preference_reservation"]["assigned"])
		self.assertEqual(proj["preference_reservation"]["scheme"], "AGPO reservation")
		self.assertEqual(proj["preference_reservation"]["planned_reserved_value"], half)

	def test_preference_entire_item_derives_value(self) -> None:
		planner, item = self._item()
		from kentender_procurement.procurement_planning.services.get_plan_item_editor import (
			get_plan_item_editor,
		)

		before = get_plan_item_editor(plan_item=item, user=planner)
		item_value = before["confirmed_estimate"]
		result = update_plan_item(
			plan_item=item,
			user=planner,
			fields={
				"preference_reservation_scheme": "AGPO reservation",
				"reservation_scope": "Entire Plan Item",
				"eligible_groups": ["Enterprises owned by PWDs"],
				"planned_reserved_value": 1,
			},
		)
		self.assertTrue(result["ok"], result)
		after = get_plan_item_editor(plan_item=item, user=planner)
		self.assertEqual(after["preference_reservation"]["planned_reserved_value"], item_value)

	def test_preference_clear_removes_designation(self) -> None:
		planner, item = self._item()
		update_plan_item(
			plan_item=item,
			user=planner,
			fields={
				"preference_reservation_scheme": "Local preference",
				"reservation_scope": "Reserved lot(s)",
				"eligible_groups": ["Women-owned enterprises"],
				"planned_reserved_value": 1000,
			},
		)
		cleared = update_plan_item(
			plan_item=item,
			user=planner,
			fields={"preference_reservation_scheme": ""},
		)
		self.assertTrue(cleared["ok"], cleared)
		from kentender_procurement.procurement_planning.services.get_plan_item_editor import (
			get_plan_item_editor,
		)

		proj = get_plan_item_editor(plan_item=item, user=planner)
		self.assertFalse(proj["preference_reservation"]["assigned"])

	def test_preference_rejects_over_item_value(self) -> None:
		planner, item = self._item()
		from kentender_procurement.procurement_planning.services.get_plan_item_editor import (
			get_plan_item_editor,
		)

		before = get_plan_item_editor(plan_item=item, user=planner)
		too_high = before["confirmed_estimate"] + 1000
		result = update_plan_item(
			plan_item=item,
			user=planner,
			fields={
				"preference_reservation_scheme": "AGPO reservation",
				"reservation_scope": "Reserved lot(s)",
				"eligible_groups": ["Women-owned enterprises"],
				"planned_reserved_value": too_high,
			},
		)
		# Draft save still persists; field is flagged for correction before sign-off.
		self.assertTrue(result["ok"], result)
		self.assertIn("planned_reserved_value", result["field_issues"])

	def test_retired_statutory_fields_not_writable(self) -> None:
		planner, item = self._item()
		result = update_plan_item(
			plan_item=item,
			user=planner,
			fields={
				"statutory_treatment": "Open competition",
				"value_treatment_note": "should not stick",
				"planned_treatment_value": 99,
			},
		)
		self.assertTrue(result["ok"], result)
		import frappe

		iv = frappe.db.get_value(
			"Procurement Plan Item", item, "draft_item_version"
		)
		row = frappe.db.get_value(
			"Procurement Plan Item Version",
			iv,
			["statutory_treatment", "value_treatment_note", "planned_treatment_value"],
			as_dict=True,
		)
		self.assertFalse(row.statutory_treatment)
		self.assertFalse(row.value_treatment_note)
		self.assertEqual(float(row.planned_treatment_value or 0), 0.0)

	def test_alternative_method_requires_grounds(self) -> None:
		planner, item = self._item()
		result = update_plan_item(
			plan_item=item,
			user=planner,
			fields={"procurement_method": "Direct procurement"},
		)
		self.assertTrue(result["ok"], result)
		self.assertIn("method_override_grounds", result["field_issues"])

	def test_multi_year_requires_justification_and_schedule(self) -> None:
		planner, item = self._item()
		result = update_plan_item(
			plan_item=item,
			user=planner,
			fields={"arrangement": "Multi-year"},
		)
		self.assertTrue(result["ok"], result)
		self.assertIn("multi_year_justification", result["field_issues"])
		self.assertIn("annual_funding_schedule", result["field_issues"])

	def test_out_of_order_milestones_save_with_field_issues(self) -> None:
		planner, item = self._item()
		result = update_plan_item(
			plan_item=item,
			user=planner,
			fields={
				"ms_invitation_published": "2027-09-15",
				"ms_tender_opening": "2027-10-20",
				"ms_evaluation_completed": "2027-10-10",
				"ms_award_approval": "2027-12-15",
				"ms_contract_signature": "2028-01-15",
				"ms_delivery_completion": "2028-03-31",
			},
		)
		self.assertTrue(result["ok"], result)
		self.assertIn("ms_evaluation_completed", result["field_issues"])
		self.assertIn("chronolog", result["field_issues"]["ms_evaluation_completed"].lower())
		import frappe

		iv = frappe.db.get_value("Procurement Plan Item", item, "draft_item_version")
		saved = frappe.db.get_value(
			"Procurement Plan Item Version",
			iv,
			"ms_evaluation_completed",
		)
		self.assertEqual(str(saved), "2027-10-10")
		from kentender_procurement.procurement_planning.services.get_plan_item_editor import (
			get_plan_item_editor,
		)

		proj = get_plan_item_editor(plan_item=item, user=planner)
		self.assertIn("ms_evaluation_completed", proj["field_issues"])
		self.assertIn("chronolog", proj["attention_message"].lower())
