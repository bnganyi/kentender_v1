# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import re

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds import constants as C
from kentender_procurement.procurement_planning.api import reference_search


class TestPpBuilderUxRegression(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self._created_docs: list[tuple[str, str]] = []

	def tearDown(self):
		for dt, name in reversed(self._created_docs):
			if not name:
				continue
			if dt == "Procurement Package":
				for ln in frappe.get_all("Procurement Package Line", filters={"package_id": name}, pluck="name"):
					frappe.delete_doc("Procurement Package Line", ln, force=True, ignore_permissions=True)
			if frappe.db.exists(dt, name):
				frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
		frappe.db.commit()
		super().tearDown()

	def _mk_plan(self, fiscal_year: int = 2029):
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": f"UX Plan {frappe.generate_hash()[:5]}",
				"plan_code": f"PP-MOH-{fiscal_year}",
				"fiscal_year": fiscal_year,
				"procuring_entity": C.ENTITY_MOH,
				"currency": "KES",
				"status": "Draft",
				"is_active": 1,
			}
		).insert(ignore_permissions=True)
		self._created_docs.append(("Procurement Plan", plan.name))
		return plan

	def _mk_template(self):
		# Create a local minimal template for deterministic tests.
		risk = frappe.get_doc(
			{
				"doctype": "Risk Profile",
				"profile_code": f"RISK-{frappe.generate_hash()[:4]}",
				"profile_name": "Risk UX",
				"risk_level": "Medium",
				"risks": "[]",
			}
		).insert(ignore_permissions=True)
		self._created_docs.append(("Risk Profile", risk.name))
		kpi = frappe.get_doc(
			{
				"doctype": "KPI Profile",
				"profile_code": f"KPI-{frappe.generate_hash()[:4]}",
				"profile_name": "KPI UX",
				"metrics": "[]",
			}
		).insert(ignore_permissions=True)
		self._created_docs.append(("KPI Profile", kpi.name))
		dec = frappe.get_doc(
			{
				"doctype": "Decision Criteria Profile",
				"profile_code": f"DCP-{frappe.generate_hash()[:4]}",
				"profile_name": "Decision UX",
				"criteria": "[]",
			}
		).insert(ignore_permissions=True)
		self._created_docs.append(("Decision Criteria Profile", dec.name))
		vm = frappe.get_doc(
			{
				"doctype": "Vendor Management Profile",
				"profile_code": f"VM-{frappe.generate_hash()[:4]}",
				"profile_name": "Vendor UX",
				"monitoring_rules": "{}",
				"escalation_rules": "{}",
			}
		).insert(ignore_permissions=True)
		self._created_docs.append(("Vendor Management Profile", vm.name))
		tpl = frappe.get_doc(
			{
				"doctype": "Procurement Template",
				"template_code": f"TPL-UX-{frappe.generate_hash()[:4]}",
				"template_name": "Template UX",
				"category": "Goods",
				"is_active": 1,
				"applicable_requisition_types": '["Goods"]',
				"applicable_demand_types": '["Planned"]',
				"default_method": "Direct",
				"default_contract_type": "Fixed Price",
				"risk_profile_id": risk.name,
				"kpi_profile_id": kpi.name,
				"decision_criteria_profile_id": dec.name,
				"vendor_management_profile_id": vm.name,
				"grouping_strategy": '{"group_by":[]}',
				"override_requires_justification": 1,
				"high_risk_escalation_required": 0,
				"schedule_required": 0,
			}
		).insert(ignore_permissions=True)
		self._created_docs.append(("Procurement Template", tpl.name))
		return tpl

	def _mk_package(self, plan_name: str, tpl_name: str, manual_code: str | None = None):
		plan_currency = frappe.db.get_value("Procurement Plan", plan_name, "currency") or "KES"
		doc = frappe.get_doc(
			{
				"doctype": "Procurement Package",
				"package_name": f"UX Package {frappe.generate_hash()[:4]}",
				"package_code": manual_code,
				"plan_id": plan_name,
				"template_id": tpl_name,
				"procurement_method": "Direct",
				"contract_type": "Fixed Price",
				"currency": plan_currency,
				"risk_profile_id": frappe.db.get_value("Procurement Template", tpl_name, "risk_profile_id"),
				"kpi_profile_id": frappe.db.get_value("Procurement Template", tpl_name, "kpi_profile_id"),
				"vendor_management_profile_id": frappe.db.get_value("Procurement Template", tpl_name, "vendor_management_profile_id"),
				"status": "Draft",
				"is_active": 1,
			}
		).insert(ignore_permissions=True)
		self._created_docs.append(("Procurement Package", doc.name))
		return doc

	def test_package_code_is_generated_server_side(self):
		plan = self._mk_plan(2031)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name, manual_code=None)
		self.assertTrue(pkg.package_code)
		self.assertRegex(pkg.package_code, r"^PKG-[A-Z0-9]+-2031-\d{3}$")

	def test_manual_package_code_is_not_kept_for_new_doc(self):
		plan = self._mk_plan(2032)
		tpl = self._mk_template()
		planner_user = frappe.db.get_value(
			"Has Role",
			{"role": "Procurement Planner", "parenttype": "User"},
			"parent",
		)
		if (
			not planner_user
			or planner_user in ("Administrator", "Guest")
			or not frappe.db.exists("User", planner_user)
		):
			self.skipTest("No non-admin Procurement Planner user available on this site")
		frappe.set_user(planner_user)
		pkg = self._mk_package(plan.name, tpl.name, manual_code="MANUAL-CODE-001")
		frappe.set_user("Administrator")
		self.assertTrue(pkg.package_code)
		self.assertNotEqual(pkg.package_code, "MANUAL-CODE-001")
		self.assertRegex(pkg.package_code, r"^PKG-[A-Z0-9]+-2032-\d{3}$")

	def test_generated_codes_are_unique(self):
		plan = self._mk_plan(2033)
		tpl = self._mk_template()
		a = self._mk_package(plan.name, tpl.name)
		b = self._mk_package(plan.name, tpl.name)
		self.assertNotEqual(a.package_code, b.package_code)

	def test_reference_search_descriptions_use_business_context_not_hash_ids(self):
		plan_rows = reference_search.search_procurement_plan(
			"Procurement Plan", "PP-", "name", 0, 5, {}
		)
		if plan_rows:
			for row in plan_rows:
				# row: name, label, description
				self.assertGreaterEqual(len(row), 3)
				desc = str(row[2] or "")
				# Keep description business-facing; no long random hash-like fragments.
				self.assertIsNone(
					re.search(r"[a-f0-9]{8,}", desc.lower()),
					f"plan description leaks raw id-like token: {desc}",
				)

		tpl_rows = reference_search.search_procurement_template(
			"Procurement Template", "TPL-", "name", 0, 5, {}
		)
		if tpl_rows:
			for row in tpl_rows:
				self.assertGreaterEqual(len(row), 3)
				desc = str(row[2] or "")
				self.assertNotEqual(desc.strip(), "")
				self.assertNotIn(" ", row[0])  # internal name may be hash-ish but not displayed context
