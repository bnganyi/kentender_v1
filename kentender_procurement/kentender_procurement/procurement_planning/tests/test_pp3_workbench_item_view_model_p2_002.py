# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-002 — Workbench item view-model service/API contract."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from kentender_budget.api.dia_budget_control import get_budget_line_context
from kentender_core.seeds import constants as C
from kentender_core.seeds._common import ensure_currency_kes, ensure_department
from kentender_procurement.procurement_planning.api.workbench_item import (
	get_pp_workbench_item_view_model,
)
from kentender_procurement.procurement_planning.services.workbench_item_view_model import (
	get_workbench_item_view_model,
)

_SUPPORTED_QUEUES = (
	"needs_planning",
	"draft_packages",
	"needs_review",
	"ready_release",
	"blocked",
	"recently_released",
)

_REQUIRED_ITEM_FIELDS = (
	"work_item_id",
	"title",
	"subtitle",
	"state_label",
	"queue",
	"underlying_object_type",
	"underlying_object_code",
	"active_plan_label",
	"blockers",
	"next_action_label",
	"primary_action",
	"secondary_actions",
	"technical_hidden_by_default",
)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan"))


class TestPP3WorkbenchItemViewModelP2002(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self._cleanup: list[tuple[str, str]] = []
		if not _pp_ok() or not frappe.db.exists("DocType", "Demand"):
			self._skip = True
			return
		self._skip = False
		ensure_currency_kes()

	def tearDown(self):
		if getattr(self, "_skip", True):
			return
		frappe.set_user("Administrator")
		for doctype, name in reversed(self._cleanup):
			if frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _track(self, doctype: str, name: str) -> None:
		self._cleanup.append((doctype, name))

	def _seed_budget_line(self) -> tuple[str | None, str | None, str | None]:
		bl_name = frappe.db.get_value("Budget Line", {"budget_line_code": "BL-MOH-2026-001"}, "name")
		if not bl_name:
			bl_name = frappe.db.get_value(
				"Budget Line",
				{"procuring_entity": C.ENTITY_MOH, "is_active": 1},
				"name",
				order_by="modified desc",
			)
		if not bl_name:
			bl_name = frappe.db.get_value(
				"Budget Line",
				{"is_active": 1},
				"name",
				order_by="modified desc",
			)
		if not bl_name:
			return None, None, None
		ctx = get_budget_line_context(bl_name)
		if not ctx.get("ok"):
			return None, None, None
		ent = (ctx.get("data") or {}).get("procuring_entity")
		dept = ensure_department(f"Dept P2002 {frappe.generate_hash(length=4)}", ent)
		return bl_name, ent, dept

	def _mk_demand(
		self,
		bl_name: str,
		entity: str,
		dept: str,
		*,
		demand_id: str | None = None,
	) -> frappe.model.document.Document:
		doc = frappe.get_doc(
			{
				"doctype": "Demand",
				"title": f"P2-002 demand {frappe.generate_hash(length=4)}",
				"demand_id": demand_id or f"DEM-P2002-{frappe.generate_hash()[:8]}",
				"procuring_entity": entity,
				"requesting_department": dept,
				"request_date": today(),
				"required_by_date": today(),
				"requisition_type": "Goods",
				"priority_level": "Normal",
				"demand_type": "Planned",
				"specification_summary": "Scope",
				"budget_line": bl_name,
				"items": [
					{
						"item_description": "P2-002 line",
						"category": "Goods",
						"uom": "ea",
						"quantity": 1,
						"estimated_unit_cost": 100,
					}
				],
			}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		frappe.db.set_value("Demand", doc.name, "status", "Approved", update_modified=False)
		doc.reload()
		self._track("Demand", doc.name)
		return doc

	def test_guest_denied_api(self) -> None:
		frappe.set_user("Guest")
		out = get_pp_workbench_item_view_model(queue="needs_planning")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")

	def test_supported_queue_coverage(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning not installed")
		for queue in _SUPPORTED_QUEUES:
			out = get_workbench_item_view_model(queue=queue, actor="Administrator", limit=5, start=0)
			self.assertTrue(out.get("ok"), msg=f"{queue}: {out}")
			self.assertEqual(out.get("queue"), queue)
			self.assertIn("items", out)
			self.assertIsInstance(out.get("items"), list)

	def test_needs_planning_item_contract_fields(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning not installed")
		bl_name, entity, dept = self._seed_budget_line()
		if not bl_name:
			self.skipTest("No active Budget Line available for P2-002")
		demand = self._mk_demand(bl_name, entity, dept)
		frappe.db.commit()

		out = get_workbench_item_view_model(queue="needs_planning", actor="Administrator", limit=200, start=0)
		self.assertTrue(out.get("ok"), msg=out)
		items = out.get("items") or []
		matched = None
		for item in items:
			if str(item.get("underlying_object_code") or "").strip() == demand.demand_id:
				matched = item
				break
		self.assertIsNotNone(matched, msg="Expected seeded demand item in needs_planning queue")
		for field in _REQUIRED_ITEM_FIELDS:
			self.assertIn(field, matched)
		self.assertEqual(matched.get("queue"), "needs_planning")
		self.assertEqual(matched.get("underlying_object_type"), "approved_demand")
		self.assertEqual((matched.get("primary_action") or {}).get("action"), "include_in_plan")
		self.assertTrue(matched.get("technical_hidden_by_default"))

	def test_api_matches_service_output(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning not installed")
		service_out = get_workbench_item_view_model(
			queue="needs_planning",
			actor="Administrator",
			limit=5,
			start=0,
		)
		api_out = get_pp_workbench_item_view_model(queue="needs_planning", limit=5, start=0)
		self.assertEqual(service_out, api_out)
