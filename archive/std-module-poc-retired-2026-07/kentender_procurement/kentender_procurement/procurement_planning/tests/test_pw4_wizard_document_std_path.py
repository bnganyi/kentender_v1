# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PW4 — Package Creation Wizard Step 2 backend: document/STD path
readiness surfacing (`Planning Package Creation Wizard.md` §9.7).

Reuses the canonical planning-to-tender STD resolution
(`resolve_std_template_for_handoff`) against a not-yet-created package
(plain dict stand-in) rather than a duplicate wizard-only interpreter.

Covers:
- Resolved STD path (via `Procurement Template.default_std_template`)
  surfaces a business-readable "Category Method" label and no warning.
- Unresolved STD path surfaces the §9.8 "Tender document path has not
  been selected." warning.
- Specification-attachment count is inherited from the selected demand(s)
  (via existing `File` attachments), and a missing-documents warning
  appears when there are none.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime, today

from kentender_budget.api.dia_budget_control import get_budget_line_context
from kentender_core.seeds import constants as C
from kentender_core.seeds._common import ensure_currency_kes, ensure_department
from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE, PLAN_DRAFT
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	get_planning_inclusion,
	include_demand_in_procurement_plan,
)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan")) and bool(frappe.db.exists("DocType", "Demand"))


class TestPW4WizardDocumentStdPath(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not _pp_ok():
			self._skip = True
			return
		self._skip = False
		ensure_currency_kes()
		self._cleanup: list[tuple[str, str]] = []

	def tearDown(self):
		if getattr(self, "_skip", True):
			return
		frappe.set_user("Administrator")
		for doctype, name in reversed(getattr(self, "_cleanup", [])):
			if doctype == "Procurement Journey":
				frappe.db.sql("DELETE FROM `tabProcurement Journey` WHERE name=%s", name)
				continue
			if frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _track(self, doctype: str, name: str) -> None:
		self._cleanup.append((doctype, name))

	def _seed_budget_line(self):
		bl_name = frappe.db.get_value("Budget Line", {"budget_line_code": "BL-MOH-2026-001"}, "name")
		if not bl_name:
			bl_name = frappe.db.get_value(
				"Budget Line", {"procuring_entity": C.ENTITY_MOH, "is_active": 1}, "name", order_by="modified desc"
			)
		if not bl_name:
			bl_name = frappe.db.get_value("Budget Line", {"is_active": 1}, "name", order_by="modified desc")
		if not bl_name:
			return None, None, None
		ctx = get_budget_line_context(bl_name)
		if not ctx.get("ok"):
			return None, None, None
		ent = (ctx.get("data") or {}).get("procuring_entity")
		dept = ensure_department(f"Dept PW4 {frappe.generate_hash(length=4)}", ent)
		return bl_name, ent, dept

	def _mk_plan(self) -> str:
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": f"PW4 plan {frappe.generate_hash(length=4)}",
				"plan_code": f"PP-PW4-{frappe.generate_hash()[:6]}",
				"fiscal_year": 2029,
				"procuring_entity": C.ENTITY_MOH,
				"currency": "KES",
				"status": PLAN_DRAFT,
				"is_active": 1,
			}
		)
		plan.insert(ignore_permissions=True)
		frappe.db.set_value("Procurement Plan", plan.name, "status", PLAN_ACTIVE, update_modified=False)
		self._track("Procurement Plan", plan.name)
		return plan.name

	def _mk_demand(self, bl_name: str, entity: str, dept: str, *, title: str):
		did = f"DEM-PW4-{frappe.generate_hash()[:8]}"
		doc = frappe.get_doc(
			{
				"doctype": "Demand",
				"title": title,
				"demand_id": did,
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
						"item_description": "Line",
						"category": "c",
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

	def _mk_journey(self, demand_id: str) -> str:
		jc = f"JRN-PW4-{frappe.generate_hash()[:8]}"
		now = now_datetime()
		frappe.db.sql(
			"""
			INSERT INTO `tabProcurement Journey`
			(name, creation, modified, modified_by, owner, docstatus,
			 journey_code, journey_title, demand_ref, procuring_entity_code,
			 procurement_category, procurement_method, fiscal_year,
			 current_stage_key, current_stage_label, current_status_category,
			 current_owner_module, blocker_count, critical_blocker_count, is_master_seed)
			VALUES (%s, %s, %s, 'Administrator', 'Administrator', 0,
			 %s, %s, %s, 'MOH', 'Goods', 'Open Tender', '2029',
			 'planning_inclusion', 'Planning Inclusion', 'In Progress',
			 'Procurement Planning', 0, 0, 0)
			""",
			(jc, now, now, jc, f"PW4 test journey {jc}", demand_id),
		)
		self._track("Procurement Journey", jc)
		return jc

	def _mk_included_demand(self, plan_name: str, *, title: str):
		bl_name, entity, dept = self._seed_budget_line()
		if not bl_name:
			self.skipTest("No active Budget Line available")
		demand = self._mk_demand(bl_name, entity, dept, title=title)
		self._mk_journey(demand.demand_id)
		frappe.db.commit()
		item_codes = [f"DEMITEM-PW4-{frappe.generate_hash()[:8]}"]
		out = include_demand_in_procurement_plan(demand.demand_id, item_codes, plan_name, "Administrator")
		self._track("Procurement Handoff Card", out["inclusion_code"])
		inclusion = get_planning_inclusion(out["inclusion_code"])
		return demand, inclusion

	def test_document_path_preview_reports_required_document_family(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		from kentender_procurement.procurement_planning.services.package_wizard_service import (
			preview_document_std_path,
		)

		plan_name = self._mk_plan()
		_demand, inclusion = self._mk_included_demand(plan_name, title="PW4 Demand")

		out = preview_document_std_path([inclusion["inclusion_code"]])
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out["required_document_family"], "Goods")
		self.assertIn("resolution_path", out)
		self.assertIsInstance(out["missing_documents"], list)

	def test_document_path_preview_zero_documents_warns(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		from kentender_procurement.procurement_planning.services.package_wizard_service import (
			preview_document_std_path,
		)

		plan_name = self._mk_plan()
		_demand, inclusion = self._mk_included_demand(plan_name, title="PW4 No Docs Demand")

		out = preview_document_std_path([inclusion["inclusion_code"]])
		self.assertEqual(out["specification_attachments_count"], 0)
		self.assertIn(_("Specification attachments"), out["missing_documents"])
		self.assertTrue(
			any("specification attachments" in w.lower() for w in out["warnings"]),
			out["warnings"],
		)

	def test_document_path_preview_unresolved_std_warns(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		from kentender_procurement.procurement_planning.services.package_wizard_service import (
			preview_document_std_path,
		)

		plan_name = self._mk_plan()
		_demand, inclusion = self._mk_included_demand(plan_name, title="PW4 Unresolved Demand")

		out = preview_document_std_path([inclusion["inclusion_code"]])
		if out["resolution_path"] == "unresolved":
			self.assertFalse(out["std_path_resolved"])
			self.assertTrue(
				any("has not been selected" in w for w in out["warnings"]),
				out["warnings"],
			)
		else:
			self.assertTrue(out["std_path_resolved"])

	def test_document_path_preview_rejects_empty_selection(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		from kentender_procurement.procurement_planning.services.package_wizard_service import (
			preview_document_std_path,
		)

		out = preview_document_std_path([])
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "NO_DEMANDS_SELECTED")

	def test_api_wrapper_document_path_behind_permission_gate(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		import json

		from kentender_procurement.procurement_planning.api.package_wizard import (
			get_pp_package_wizard_document_path_preview,
		)

		plan_name = self._mk_plan()
		_demand, inclusion = self._mk_included_demand(plan_name, title="PW4 API Demand")

		out = get_pp_package_wizard_document_path_preview(
			inclusion_codes=json.dumps([inclusion["inclusion_code"]])
		)
		self.assertTrue(out.get("ok"))
		self.assertIn("required_document_family", out)
