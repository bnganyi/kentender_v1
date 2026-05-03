# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""B3 — release_procurement_package_to_tender service + hook.

Run:
    bench --site <site> run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3
"""

from __future__ import annotations

import json
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from frappe.utils import today

from kentender_core.seeds import constants as C
from kentender_core.seeds._common import ensure_currency_kes, ensure_department
from kentender_procurement.procurement_planning.services.tendering_handoff import (
	build_release_payload,
)
from kentender_procurement.tender_management.services.officer_tender_config import (
	TENDER_STATUS_CONFIGURED,
)
from kentender_procurement.tender_management.services.release_procurement_package_to_tender import (
	hook_release_procurement_package_to_tender,
	release_procurement_package_to_tender,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)


class _ReleaseProcurementPackageHandoffFixtures(IntegrationTestCase):
	"""Shared plan/template/package + seed line fixtures for B3/B5 handoff tests."""

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self._created: list[tuple[str, str]] = []

	def tearDown(self):
		for dt, name in reversed(self._created):
			if not name:
				continue
			if dt == "Procurement Tender":
				if frappe.db.exists(dt, name):
					frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
				continue
			if dt == "Procurement Package":
				for ln in frappe.get_all(
					"Procurement Package Line", filters={"package_id": name}, pluck="name"
				):
					frappe.delete_doc("Procurement Package Line", ln, force=True, ignore_permissions=True)
			if dt == "Demand":
				if frappe.db.exists(dt, name):
					frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
				continue
			if dt == "Procuring Department":
				if frappe.db.exists(dt, name):
					frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
				continue
			if frappe.db.exists(dt, name):
				frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
		frappe.db.commit()
		super().tearDown()

	def _mk_plan(self, fiscal_year: int = 2029):
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": f"B3 Plan {frappe.generate_hash()[:5]}",
				"plan_code": f"PP-B3-{fiscal_year}-{frappe.generate_hash()[:4]}",
				"fiscal_year": fiscal_year,
				"procuring_entity": C.ENTITY_MOH,
				"currency": "KES",
				"status": "Draft",
				"is_active": 1,
			}
		).insert(ignore_permissions=True)
		self._created.append(("Procurement Plan", plan.name))
		return plan

	def _mk_template(self):
		risk = frappe.get_doc(
			{
				"doctype": "Risk Profile",
				"profile_code": f"RISK-B3-{frappe.generate_hash()[:4]}",
				"profile_name": "Risk B3",
				"risk_level": "Medium",
				"risks": "[]",
			}
		).insert(ignore_permissions=True)
		self._created.append(("Risk Profile", risk.name))
		kpi = frappe.get_doc(
			{
				"doctype": "KPI Profile",
				"profile_code": f"KPI-B3-{frappe.generate_hash()[:4]}",
				"profile_name": "KPI B3",
				"metrics": "[]",
			}
		).insert(ignore_permissions=True)
		self._created.append(("KPI Profile", kpi.name))
		dec = frappe.get_doc(
			{
				"doctype": "Decision Criteria Profile",
				"profile_code": f"DCP-B3-{frappe.generate_hash()[:4]}",
				"profile_name": "Decision B3",
				"criteria": "[]",
			}
		).insert(ignore_permissions=True)
		self._created.append(("Decision Criteria Profile", dec.name))
		vm = frappe.get_doc(
			{
				"doctype": "Vendor Management Profile",
				"profile_code": f"VM-B3-{frappe.generate_hash()[:4]}",
				"profile_name": "Vendor B3",
				"monitoring_rules": "{}",
				"escalation_rules": "{}",
			}
		).insert(ignore_permissions=True)
		self._created.append(("Vendor Management Profile", vm.name))
		tpl = frappe.get_doc(
			{
				"doctype": "Procurement Template",
				"template_code": f"TPL-B3-{frappe.generate_hash()[:4]}",
				"template_name": "Template B3",
				"category": "Goods",
				"default_std_template": TEMPLATE_CODE,
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
		).insert(ignore_permissions=True)
		self._created.append(("Procurement Template", tpl.name))
		return tpl

	def _mk_package(self, plan_name: str, tpl_name: str):
		plan_currency = frappe.db.get_value("Procurement Plan", plan_name, "currency") or "KES"
		doc = frappe.get_doc(
			{
				"doctype": "Procurement Package",
				"package_name": f"B3 Package {frappe.generate_hash()[:4]}",
				"plan_id": plan_name,
				"template_id": tpl_name,
				"procurement_method": "Direct Procurement",
				"contract_type": "Fixed Price",
				"currency": plan_currency,
				"risk_profile_id": frappe.db.get_value("Procurement Template", tpl_name, "risk_profile_id"),
				"kpi_profile_id": frappe.db.get_value("Procurement Template", tpl_name, "kpi_profile_id"),
				"decision_criteria_profile_id": frappe.db.get_value(
					"Procurement Template", tpl_name, "decision_criteria_profile_id"
				),
				"vendor_management_profile_id": frappe.db.get_value(
					"Procurement Template", tpl_name, "vendor_management_profile_id"
				),
				"status": "Draft",
				"is_active": 1,
			}
		).insert(ignore_permissions=True)
		self._created.append(("Procurement Package", doc.name))
		return doc

	def _add_seed_budget_line_and_demand(self, pkg_name: str) -> None:
		"""One active package line + Demand for XMV B5 (requires seed budget line)."""
		bl = frappe.db.get_value("Budget Line", {"budget_line_code": "BL-MOH-2026-001"}, "name")
		if not bl:
			self.skipTest("Seed Budget Line BL-MOH-2026-001 required for release handoff tests")
		ensure_currency_kes()
		pe = frappe.db.get_value("Budget Line", bl, "procuring_entity") or C.ENTITY_MOH
		dept = ensure_department(f"B3LN{frappe.generate_hash()[:5]}", pe)
		self._created.append(("Procuring Department", dept))
		d = frappe.get_doc(
			{
				"doctype": "Demand",
				"title": f"B3 demand {frappe.generate_hash()[:4]}",
				"procuring_entity": pe,
				"requesting_department": dept,
				"request_date": today(),
				"required_by_date": today(),
				"specification_summary": "B3 package line",
				"delivery_location": "HQ",
				"requested_delivery_period_days": 30,
				"budget_line": bl,
				"items": [
					{
						"item_description": "Line item",
						"category": "Goods",
						"uom": "ea",
						"quantity": 1,
						"estimated_unit_cost": 1000,
					}
				],
			}
		)
		d.insert(ignore_permissions=True)
		frappe.db.set_value("Demand", d.name, "status", "Approved")
		self._created.append(("Demand", d.name))
		ln = frappe.get_doc(
			{
				"doctype": "Procurement Package Line",
				"package_id": pkg_name,
				"demand_id": d.name,
				"budget_line_id": bl,
				"amount": 1000,
				"is_active": 1,
			}
		).insert(ignore_permissions=True)
		self._created.append(("Procurement Package Line", ln.name))


class TestReleaseProcurementPackageToTenderB3(_ReleaseProcurementPackageHandoffFixtures):
	def test_hooks_list_includes_b3_handler(self):
		hooks = frappe.get_hooks("release_procurement_package_to_tender") or []
		self.assertTrue(
			any(
				"release_procurement_package_to_tender.hook_release_procurement_package_to_tender" in h
				for h in hooks
			),
			f"Expected B3 hook path in hooks, got {hooks!r}",
		)

	def test_wrong_package_status_returns_not_ok(self):
		upsert_std_template()
		plan = self._mk_plan()
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		out = release_procurement_package_to_tender(pkg.name)
		self.assertFalse(out.get("ok"))
		self.assertIn("Ready for Tender", str(out.get("message", "")))

	def test_creates_tender_then_idempotent(self):
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		pkg.reload()

		out1 = release_procurement_package_to_tender(pkg.name)
		self.assertTrue(out1.get("ok"), out1)
		self.assertFalse(out1.get("existing"))
		tname = out1.get("tender")
		self.assertTrue(tname)
		self._created.append(("Procurement Tender", tname))

		t = frappe.get_doc("Procurement Tender", tname)
		self.assertEqual(t.procurement_package, pkg.name)
		self.assertEqual(t.procurement_plan, plan.name)
		self.assertEqual(t.procurement_template, tpl.name)
		self.assertEqual(t.std_template, TEMPLATE_CODE)
		self.assertEqual(t.tender_status, TENDER_STATUS_CONFIGURED)
		cfg = json.loads(t.configuration_json or "{}")
		self.assertIn("TENDER.TENDER_NAME", cfg)

		out2 = release_procurement_package_to_tender(pkg.name)
		self.assertTrue(out2.get("ok"), out2)
		self.assertTrue(out2.get("existing"))
		self.assertEqual(out2.get("tender"), tname)

	def test_plan_not_approved_blocks_new_tender(self):
		upsert_std_template()
		plan = self._mk_plan()
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		out = release_procurement_package_to_tender(pkg.name)
		self.assertFalse(out.get("ok"))
		self.assertIn("Approved", str(out.get("message", "")))

	def test_hook_does_not_raise_with_valid_payload(self):
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		pkg = frappe.get_doc("Procurement Package", pkg.name)
		payload = build_release_payload(pkg)
		hook_release_procurement_package_to_tender(payload)
		tn = frappe.db.get_value(
			"Procurement Tender",
			{"procurement_package": pkg.name},
			"name",
		)
		self.assertTrue(tn)
		self._created.append(("Procurement Tender", tn))

	def test_hook_missing_package_logs_only(self):
		hook_release_procurement_package_to_tender({"plan_id": "x"})
		# no exception

	def test_release_package_to_tender_fails_if_no_tender_after_handoff(self):
		"""B4: workflow must not mark package Released if handoff did not link a tender (PT-HANDOFF-AC-009)."""
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		from kentender_procurement.procurement_planning.api import workflow as wf_mod
		from kentender_procurement.procurement_planning.api.workflow import release_package_to_tender
		from kentender_procurement.tender_management.services.planning_tender_handoff_xmv import (
			XmvReleaseValidationResult,
		)

		with patch(
			"kentender_procurement.procurement_planning.services.package_completeness.get_package_completeness_blockers",
			return_value=[],
		):
			with patch.object(
				wf_mod,
				"validate_package_for_release_xmv",
				return_value=XmvReleaseValidationResult(critical=[], warnings=[]),
			):
				with patch.object(wf_mod, "package_has_release_tender", return_value=False):
					with self.assertRaises(frappe.ValidationError) as ctx:
						release_package_to_tender(package_id=pkg.name)
		self.assertIn("No Procurement Tender was linked", str(ctx.exception))
		self.assertEqual(
			frappe.db.get_value("Procurement Package", pkg.name, "status"),
			"Ready for Tender",
			"package must stay Ready for Tender when handoff guard fails",
		)
		for tn in frappe.get_all("Procurement Tender", filters={"procurement_package": pkg.name}, pluck="name"):
			self._created.append(("Procurement Tender", tn))
