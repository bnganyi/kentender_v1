# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-SCH Wave 1 — Module Def + Demands MVP-1 DocTypes present with required fields."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase


DEMAND_REQUIRED_FIELDS = {
	"demand_code",
	"procuring_entity",
	"owner_org_unit",
	"title",
	"status",
	"current_stage",
	"approved_baseline_version",
	"approved_baseline_snapshot",
	"planning_usage",
	"fixture_namespace",
	"need_statement",
	"need_rationale",
	"estimate_basis",
}

CHILD_DOCTYPES = {
	"Demand Item": {"demand", "item_code", "description"},
	"Demand Strategy Reference": {"demand", "reference_type", "snapshot_label"},
	"Demand Value Treatment": {"demand", "plan_value_commitment", "treatment"},
	"Demand Funding Allocation": {"demand", "budget", "budget_line", "allocation_amount"},
	"Demand Decision": {"demand", "stage", "decision", "actor"},
	"Planning Consumption": {"demand", "demand_item", "consumed_amount"},
}

FUNDING_EXCEPTION_FIELDS = {
	"demand",
	"exception_type",
	"status",
	"current_owner",
}


class TestDemandsMvp1Schema(IntegrationTestCase):
	def test_demands_module_def_exists(self) -> None:
		frappe.set_user("Administrator")
		self.assertTrue(frappe.db.exists("Module Def", "Demands"))
		mod = frappe.get_doc("Module Def", "Demands")
		self.assertEqual(mod.app_name, "kentender_procurement")

	def test_demand_doctype_and_core_fields(self) -> None:
		frappe.set_user("Administrator")
		self.assertTrue(frappe.db.exists("DocType", "Demand"))
		meta = frappe.get_meta("Demand")
		self.assertEqual(meta.module, "Demands")
		for fieldname in DEMAND_REQUIRED_FIELDS:
			self.assertTrue(meta.has_field(fieldname), f"Demand missing field {fieldname}")
		status = meta.get_field("status")
		self.assertIn("In Review", (status.options or "").split("\n"))
		stage = meta.get_field("current_stage")
		self.assertIn("Request Preparation", (stage.options or "").split("\n"))

	def test_related_doctypes_and_fields(self) -> None:
		frappe.set_user("Administrator")
		for doctype, fields in CHILD_DOCTYPES.items():
			self.assertTrue(frappe.db.exists("DocType", doctype), f"missing {doctype}")
			meta = frappe.get_meta(doctype)
			self.assertEqual(meta.module, "Demands")
			for fieldname in fields:
				self.assertTrue(meta.has_field(fieldname), f"{doctype} missing {fieldname}")

	def test_funding_exception_budget_owned(self) -> None:
		frappe.set_user("Administrator")
		self.assertTrue(frappe.db.exists("DocType", "Funding Exception"))
		meta = frappe.get_meta("Funding Exception")
		self.assertEqual(meta.module, "Kentender Budget")
		for fieldname in FUNDING_EXCEPTION_FIELDS:
			self.assertTrue(meta.has_field(fieldname), f"Funding Exception missing {fieldname}")
		demand = meta.get_field("demand")
		self.assertEqual(demand.fieldtype, "Link")
		self.assertEqual(demand.options, "Demand")

	def test_module_registry_demands_not_retired_dia(self) -> None:
		frappe.set_user("Administrator")
		from kentender_core.module_registry import KT_MODULES

		self.assertIn("demands", KT_MODULES)
		self.assertFalse(KT_MODULES["demands"].get("retired"))
		self.assertEqual(KT_MODULES["demands"].get("form_doctype"), "Demand")
		self.assertNotIn("dia", KT_MODULES)

	def test_consumers_remain_gated_until_live(self) -> None:
		frappe.set_user("Administrator")
		from kentender_procurement.demands import CONSUMERS_LIVE
		from kentender_procurement.procurement_lifecycle.demand_module_gate import (
			demand_consumers_live,
			demand_doctype_available,
		)
		from kentender_procurement.procurement_planning.services.approved_demand_queue import (
			get_approved_demands_for_queue,
		)

		self.assertTrue(demand_doctype_available())
		self.assertFalse(CONSUMERS_LIVE)
		self.assertFalse(demand_consumers_live())
		out = get_approved_demands_for_queue(filters={}, actor="Administrator")
		self.assertEqual(out.get("error_code"), "DEMAND_MODULE_RETIRED")
		self.assertTrue(out.get("skipped"))
