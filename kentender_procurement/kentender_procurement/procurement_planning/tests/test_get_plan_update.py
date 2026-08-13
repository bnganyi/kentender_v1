# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-UI-10 — get_plan_update / save_plan_update / successor routes."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.mvp1_constants import DRAFT_CHANGE_ADDED
from kentender_procurement.procurement_planning.services.add_demand_to_plan import (
	add_demand_to_plan,
)
from kentender_procurement.procurement_planning.services.get_plan_implementation import (
	get_plan_implementation,
)
from kentender_procurement.procurement_planning.services.get_plan_item_editor import (
	get_plan_item_editor,
)
from kentender_procurement.procurement_planning.services.get_plan_update import (
	get_plan_update,
	save_plan_update,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	ROLE_VIEWER,
)
from kentender_procurement.procurement_planning.services.submit_plan_for_review import (
	submit_plan_for_review,
)
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	approve_plan_via_gate05,
	create_plan_as_planner,
	ensure_planner_user,
	ensure_scope,
	make_approved_demand,
	purge_pe_fy,
	unique_test_fy,
)
from kentender_procurement.procurement_planning.tests._gate02_helpers import (
	PE_MOH,
	ensure_user_with_roles,
)


class TestGetPlanUpdate(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_scope()

	def _approved_then_successor(self, *, bucket: int, title: str):
		planner = ensure_planner_user()
		fy = unique_test_fy(base_year=3500, bucket=bucket)
		purge_pe_fy(fy)
		plan = create_plan_as_planner(title=title, financial_year=fy)
		d1 = make_approved_demand(title=f"{title} base")
		add_demand_to_plan(plan=plan["plan"], demand=d1["demand"], user=planner)
		approve_plan_via_gate05(plan=plan["plan"], version=plan["version"])
		d2 = make_approved_demand(title=f"{title} extra")
		added = add_demand_to_plan(plan=plan["plan"], demand=d2["demand"], user=planner)
		return planner, plan, added

	def test_draft_plan_is_not_an_update_surface(self) -> None:
		planner = ensure_planner_user()
		fy = unique_test_fy(base_year=3500, bucket=0)
		purge_pe_fy(fy)
		plan = create_plan_as_planner(title="Draft not update", financial_year=fy)
		with self.assertRaises(frappe.ValidationError):
			get_plan_update(plan=plan["plan"], user=planner)

	def test_approved_without_successor_is_not_an_update_surface(self) -> None:
		planner = ensure_planner_user()
		fy = unique_test_fy(base_year=3500, bucket=1)
		purge_pe_fy(fy)
		plan = create_plan_as_planner(title="Approved no draft", financial_year=fy)
		d = make_approved_demand(title="Approved no draft demand")
		add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		approve_plan_via_gate05(plan=plan["plan"], version=plan["version"])
		with self.assertRaises(frappe.ValidationError):
			get_plan_update(plan=plan["plan"], user=planner)

	def test_successor_dto_splits_changed_and_unchanged(self) -> None:
		planner, plan, added = self._approved_then_successor(
			bucket=2, title="Update overview"
		)
		dto = get_plan_update(plan=plan["plan"], user=planner)
		self.assertTrue(dto["ok"], dto)
		self.assertTrue(dto["changed_items"])
		self.assertEqual(dto["changed_items"][0]["change_label"], DRAFT_CHANGE_ADDED)
		self.assertEqual(dto["changed_items"][0]["plan_item"], added["plan_item"])
		self.assertGreaterEqual(dto["unchanged_count"], 1)
		self.assertTrue(dto["unchanged_items"])
		self.assertIn("procurement-plan-update", dto["update_route"])
		self.assertIn("procurement-plan-approved", dto["approved_route"])
		self.assertEqual(dto["change_type_label"], "Additional approved need")
		self.assertFalse(dto["can_submit"])
		self.assertTrue(dto["can_save"])
		self.assertTrue(dto["can_validate"])
		self.assertFalse(dto["no_changes_remain"])
		self.assertEqual(dto["update_reason"], "")
		self.assertIn("remains active", dto["banner_copy"].lower())
		self.assertIn("procurement-plan-update", added["builder_route"])
		iv = added["item_version"]
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Item Version", iv, "draft_change_label"),
			DRAFT_CHANGE_ADDED,
		)
		impl = get_plan_implementation(plan=plan["plan"], user=planner)
		self.assertIn("procurement-plan-update", impl["update_route"])
		editor = get_plan_item_editor(plan_item=added["plan_item"], user=planner)
		self.assertIn("procurement-plan-update", editor["builder_route"])

	def test_save_plan_update_requires_reason_and_persists(self) -> None:
		planner, plan, _added = self._approved_then_successor(
			bucket=3, title="Save update reason"
		)
		blank = save_plan_update(plan=plan["plan"], update_reason="  ", user=planner)
		self.assertFalse(blank["ok"], blank)
		self.assertIn("update_reason", blank["errors"])
		token = frappe.db.get_value(
			"Procurement Plan",
			plan["plan"],
			"open_draft_version",
		)
		token = frappe.db.get_value(
			"Procurement Plan Version", token, "concurrency_token"
		)
		saved = save_plan_update(
			plan=plan["plan"],
			update_reason="Late approved training need",
			concurrency_token=token,
			user=planner,
		)
		self.assertTrue(saved["ok"], saved)
		dto = get_plan_update(plan=plan["plan"], user=planner)
		self.assertEqual(dto["update_reason"], "Late approved training need")

	def test_submit_successor_requires_planner_reason(self) -> None:
		planner, plan, _added = self._approved_then_successor(
			bucket=4, title="Submit needs reason"
		)
		draft = frappe.db.get_value(
			"Procurement Plan", plan["plan"], "open_draft_version"
		)
		token = frappe.db.get_value(
			"Procurement Plan Version", draft, "concurrency_token"
		)
		blocked = submit_plan_for_review(
			plan=plan["plan"], concurrency_token=token, user=planner
		)
		self.assertFalse(blocked["ok"], blocked)
		self.assertTrue(
			"update_reason" in blocked.get("errors", {})
			or "reason" in str(blocked.get("errors", {})).lower()
		)

	def test_viewer_cannot_save_or_submit(self) -> None:
		planner, plan, _added = self._approved_then_successor(
			bucket=5, title="Viewer update"
		)
		viewer = ensure_user_with_roles(
			"pln.ui10.viewer@test.local",
			roles=(ROLE_VIEWER,),
			pe=PE_MOH,
			org_unit=None,
			include_descendants=0,
		)
		dto = get_plan_update(plan=plan["plan"], user=viewer)
		self.assertTrue(dto["ok"], dto)
		self.assertFalse(dto["can_save"])
		self.assertFalse(dto["can_submit"])
		self.assertFalse(dto["can_cancel"])
		self.assertFalse(dto["can_validate"])
		self.assertTrue(dto["changed_items"])
		self.assertFalse(dto["changed_items"][0]["can_remove_from_draft"])
		with self.assertRaises(frappe.PermissionError):
			save_plan_update(
				plan=plan["plan"],
				update_reason="Should not save",
				user=viewer,
			)
