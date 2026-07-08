# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tracker B2 — Procurement Template.default_std_template Link + validation.

Run:
    bench --site <site> run-tests --app kentender_procurement \\
        --module kentender_procurement.procurement_planning.tests.test_procurement_template_default_std_b2
"""

from __future__ import annotations

import frappe
from frappe.exceptions import ValidationError
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE


class TestProcurementTemplateDefaultStdB2(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self._created: list[tuple[str, str]] = []

	def tearDown(self):
		for dt, name in reversed(self._created):
			if name and frappe.db.exists(dt, name):
				frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
		frappe.db.commit()
		super().tearDown()

	def _mk_minimal_template_dict(self, **extra):
		risk = frappe.get_doc(
			{
				"doctype": "Risk Profile",
				"profile_code": f"RISK-B2-{frappe.generate_hash()[:4]}",
				"profile_name": "Risk B2",
				"risk_level": "Medium",
				"risks": "[]",
			}
		).insert(ignore_permissions=True)
		self._created.append(("Risk Profile", risk.name))
		kpi = frappe.get_doc(
			{
				"doctype": "KPI Profile",
				"profile_code": f"KPI-B2-{frappe.generate_hash()[:4]}",
				"profile_name": "KPI B2",
				"metrics": "[]",
			}
		).insert(ignore_permissions=True)
		self._created.append(("KPI Profile", kpi.name))
		dec = frappe.get_doc(
			{
				"doctype": "Decision Criteria Profile",
				"profile_code": f"DCP-B2-{frappe.generate_hash()[:4]}",
				"profile_name": "Decision B2",
				"criteria": "[]",
			}
		).insert(ignore_permissions=True)
		self._created.append(("Decision Criteria Profile", dec.name))
		vm = frappe.get_doc(
			{
				"doctype": "Vendor Management Profile",
				"profile_code": f"VM-B2-{frappe.generate_hash()[:4]}",
				"profile_name": "Vendor B2",
				"monitoring_rules": "{}",
				"escalation_rules": "{}",
			}
		).insert(ignore_permissions=True)
		self._created.append(("Vendor Management Profile", vm.name))
		base = {
			"doctype": "Procurement Template",
			"template_code": f"TPL-B2-{frappe.generate_hash()[:6]}",
			"template_name": "Template B2",
			"category": "Goods",
			"is_active": 1,
			"applicable_requisition_types": '["Goods"]',
			"applicable_demand_types": '["Planned"]',
			"default_method": "Direct Procurement",
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
		base.update(extra)
		return base

	def test_meta_includes_default_std_template(self):
		meta = frappe.get_meta("Procurement Template")
		df = meta.get_field("default_std_template")
		self.assertIsNotNone(df, "default_std_template must exist on Procurement Template (B2 schema)")
		self.assertEqual(df.fieldtype, "Link")
		self.assertEqual(df.options, "STD Template")

	def test_invalid_default_std_template_raises(self):
		doc = frappe.get_doc(self._mk_minimal_template_dict(default_std_template="STD-TPL-NOT-REAL-99999"))
		with self.assertRaises(ValidationError):
			doc.insert(ignore_permissions=True)

	def test_omitted_default_std_template_inserts(self):
		doc = frappe.get_doc(self._mk_minimal_template_dict())
		doc.insert(ignore_permissions=True)
		self._created.append(("Procurement Template", doc.name))
		self.assertFalse(doc.default_std_template)

	def test_valid_default_std_template_when_std_exists(self):
		if not frappe.db.exists("STD Template", TEMPLATE_CODE):
			self.skipTest("No Works POC STD Template on site; run STD loader seed first.")
		doc = frappe.get_doc(self._mk_minimal_template_dict(default_std_template=TEMPLATE_CODE))
		doc.insert(ignore_permissions=True)
		self._created.append(("Procurement Template", doc.name))
		self.assertEqual(doc.default_std_template, TEMPLATE_CODE)
