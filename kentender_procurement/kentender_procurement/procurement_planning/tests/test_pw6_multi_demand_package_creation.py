# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PW6 — `create_package_with_lines` multi-demand packaging primitive.

Generalizes the single-demand `_create_package_and_line` path to N
inclusions for the Package Creation Wizard (§8.4/§9.6/§12). Verifies one
`Procurement Package` is created with one `Procurement Package Line` per
selected demand, package-level config overrides (owner/priority/target
release date/method override+reason) land on the package, per-line
overrides (lot_group) land on the right line, and every selected
inclusion is marked packaged."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime, today

from kentender_budget.api.dia_budget_control import get_budget_line_context
from kentender_core.seeds import constants as C
from kentender_core.seeds._common import ensure_currency_kes, ensure_department
from kentender_procurement.procurement_planning.pp2_constants import PKG_DRAFT, PLAN_ACTIVE, PLAN_DRAFT
from kentender_procurement.procurement_planning.services.package_creation_service import (
	create_package_with_lines,
)
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	get_planning_inclusion,
	include_demand_in_procurement_plan,
)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan")) and bool(frappe.db.exists("DocType", "Demand"))


class TestPW6MultiDemandPackageCreation(IntegrationTestCase):
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

	def _require_template(self) -> str | None:
		tpl = frappe.get_all("Procurement Template", filters={"is_active": 1}, limit=1, pluck="name")
		if not tpl:
			return None
		row = frappe.db.get_value(
			"Procurement Template",
			tpl[0],
			("risk_profile_id", "kpi_profile_id", "vendor_management_profile_id"),
			as_dict=True,
		)
		if not row or not all(row.values()):
			return None
		return tpl[0]

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
		dept = ensure_department(f"Dept PW6 {frappe.generate_hash(length=4)}", ent)
		return bl_name, ent, dept

	def _mk_plan(self) -> str:
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": f"PW6 plan {frappe.generate_hash(length=4)}",
				"plan_code": f"PP-PW6-{frappe.generate_hash()[:6]}",
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
		did = f"DEM-PW6-{frappe.generate_hash()[:8]}"
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
		jc = f"JRN-PW6-{frappe.generate_hash()[:8]}"
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
			(jc, now, now, jc, f"PW6 test journey {jc}", demand_id),
		)
		self._track("Procurement Journey", jc)
		return jc

	def _include_demand(self, demand, plan_name: str, item_codes: list[str]) -> dict:
		out = include_demand_in_procurement_plan(demand.demand_id, item_codes, plan_name, "Administrator")
		inclusion_code = out.get("inclusion_code")
		if inclusion_code:
			self._track("Procurement Handoff Card", inclusion_code)
		return out

	def _mk_two_demand_inclusions(self, plan_name: str):
		bl_name, entity, dept = self._seed_budget_line()
		if not bl_name:
			self.skipTest("No active Budget Line available")
		demand_a = self._mk_demand(bl_name, entity, dept, title="PW6 Demand Alpha")
		demand_b = self._mk_demand(bl_name, entity, dept, title="PW6 Demand Beta")
		self._mk_journey(demand_a.demand_id)
		self._mk_journey(demand_b.demand_id)
		frappe.db.commit()
		incl_a = self._include_demand(demand_a, plan_name, [f"DEMITEM-PW6-{frappe.generate_hash()[:8]}"])
		incl_b = self._include_demand(demand_b, plan_name, [f"DEMITEM-PW6-{frappe.generate_hash()[:8]}"])
		inclusion_a = get_planning_inclusion(incl_a["inclusion_code"])
		inclusion_b = get_planning_inclusion(incl_b["inclusion_code"])
		return inclusion_a, inclusion_b

	def test_multi_demand_create_produces_one_package_with_n_lines(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		plan_name = self._mk_plan()
		inclusion_a, inclusion_b = self._mk_two_demand_inclusions(plan_name)

		result = create_package_with_lines(
			inclusions=[inclusion_a, inclusion_b],
			actor="Administrator",
			package_overrides={
				"package_name": "PW6 Combined Package",
				"package_owner": "Administrator",
				"package_priority": "High",
				"target_release_date": today(),
			},
			line_overrides_by_inclusion={
				inclusion_a["inclusion_code"]: {"lot_group": "Lot 1"},
				inclusion_b["inclusion_code"]: {"lot_group": "Lot 2"},
			},
		)
		self._track("Procurement Package", result["package_code"])
		for line_code in result["package_line_codes"]:
			self._track("Procurement Package Line", line_code)

		self.assertEqual(len(result["package_line_codes"]), 2)
		self.assertEqual(set(result["inclusion_codes"]), {inclusion_a["inclusion_code"], inclusion_b["inclusion_code"]})

		pkg = frappe.db.get_value(
			"Procurement Package",
			result["package_code"],
			("package_name", "package_owner", "package_priority", "target_release_date", "status"),
			as_dict=True,
		)
		self.assertEqual(pkg.package_name, "PW6 Combined Package")
		self.assertEqual(pkg.package_owner, "Administrator")
		self.assertEqual(pkg.package_priority, "High")
		self.assertEqual(pkg.status, PKG_DRAFT)

		lines = frappe.get_all(
			"Procurement Package Line",
			filters={"package_id": result["package_code"]},
			fields=["package_line_code", "demand_id", "lot_group"],
			order_by="package_line_code asc",
		)
		self.assertEqual(len(lines), 2)
		lot_groups = {line.lot_group for line in lines}
		self.assertEqual(lot_groups, {"Lot 1", "Lot 2"})
		demand_names = {line.demand_id for line in lines}
		self.assertEqual(
			demand_names,
			{
				frappe.db.get_value("Demand", {"demand_id": inclusion_a["demand_code"]}, "name"),
				frappe.db.get_value("Demand", {"demand_id": inclusion_b["demand_code"]}, "name"),
			},
		)

	def test_multi_demand_create_marks_all_inclusions_packaged(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		plan_name = self._mk_plan()
		inclusion_a, inclusion_b = self._mk_two_demand_inclusions(plan_name)

		result = create_package_with_lines(inclusions=[inclusion_a, inclusion_b], actor="Administrator")
		self._track("Procurement Package", result["package_code"])
		for line_code in result["package_line_codes"]:
			self._track("Procurement Package Line", line_code)

		for inclusion_code in (inclusion_a["inclusion_code"], inclusion_b["inclusion_code"]):
			refreshed = get_planning_inclusion(inclusion_code)
			self.assertEqual(refreshed.get("created_package_code"), result["package_code"])
			self.assertEqual(refreshed.get("status"), "Packaged")

	def test_single_inclusion_legacy_shape_unaffected(self):
		"""`_create_package_and_line` (legacy single-demand path) must keep
		returning its original response shape after delegating to
		`create_package_with_lines` — regression guard for the PW6 refactor."""
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		from kentender_procurement.procurement_planning.services.package_creation_service import (
			create_package_from_planning_inclusion,
		)

		plan_name = self._mk_plan()
		inclusion_a, _inclusion_b = self._mk_two_demand_inclusions(plan_name)
		out = create_package_from_planning_inclusion(inclusion_a["inclusion_code"], "Administrator")
		self._track("Procurement Package", out["package_code"])
		for line_code in out["package_line_codes"]:
			self._track("Procurement Package Line", line_code)

		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("inclusion_code"), inclusion_a["inclusion_code"])
		self.assertEqual(out.get("demand_code"), inclusion_a["demand_code"])
		self.assertEqual(len(out.get("package_line_codes") or []), 1)

	def test_two_demands_in_same_plan_get_distinct_inclusion_codes(self):
		"""Regression for the PLANINCL seq bug: a fixed '001' suffix meant a
		second demand's inclusion silently upserted (overwrote) the first
		demand's handoff card. Both demands must keep their own distinct
		Planning Inclusion record under the same plan."""
		if self._skip:
			self.skipTest("PP or Demand not installed")
		plan_name = self._mk_plan()
		inclusion_a, inclusion_b = self._mk_two_demand_inclusions(plan_name)

		self.assertNotEqual(inclusion_a["inclusion_code"], inclusion_b["inclusion_code"])
		self.assertEqual(inclusion_a["demand_code"], get_planning_inclusion(inclusion_a["inclusion_code"])["demand_code"])
		self.assertEqual(inclusion_b["demand_code"], get_planning_inclusion(inclusion_b["inclusion_code"])["demand_code"])
		self.assertNotEqual(inclusion_a["demand_code"], inclusion_b["demand_code"])
