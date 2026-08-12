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

	def test_preference_writes_ignored_from_editor(self) -> None:
		"""C02: preference keys no longer mutate Plan Item Version via update_plan_item."""
		planner, item = self._item()
		from kentender_procurement.procurement_planning.services.get_plan_item_editor import (
			get_plan_item_editor,
		)

		before = get_plan_item_editor(plan_item=item, user=planner)
		assigned_before = before["preference_reservation"]["assigned"]
		result = update_plan_item(
			plan_item=item,
			user=planner,
			fields={
				"preference_reservation_scheme": "AGPO reservation",
				"reservation_scope": "Reserved lot(s)",
				"eligible_groups": ["Women-owned enterprises"],
				"planned_reserved_value": 9999,
			},
		)
		self.assertTrue(result["ok"], result)
		after = get_plan_item_editor(plan_item=item, user=planner)
		self.assertEqual(after["preference_reservation"]["assigned"], assigned_before)
		self.assertNotEqual(after["preference_reservation"].get("scheme"), "AGPO reservation")

	def test_retired_statutory_fields_absent_from_meta(self) -> None:
		meta = frappe.get_meta("Procurement Plan Item Version")
		for fieldname in (
			"statutory_treatment",
			"statutory_target_groups",
			"planned_treatment_value",
			"value_treatment_note",
		):
			self.assertIsNone(meta.get_field(fieldname), fieldname)

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
