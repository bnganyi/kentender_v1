# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""KENTENDER_MVP_V1 canonical demo seed — identity + isolation contract."""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_core.seeds.kentender_mvp_v1.clear import (
	purge_dem_test_users,
	purge_kentender_playwright_data,
)
from kentender_core.seeds.kentender_mvp_v1.orchestrator import (
	run_kentender_mvp_v1,
	validate_kentender_mvp_v1,
)
from kentender_core.services.org_scope_access import can_access_owned_record


class TestKentenderMvpV1SeedContract(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.first = run_kentender_mvp_v1(reset=True, force=True, validate=True)

	def test_first_run_ok(self):
		self.assertTrue(self.first.get("ok"), msg=self.first.get("validate"))

	def test_idempotent_second_run(self):
		frappe.set_user("Administrator")
		second = run_kentender_mvp_v1(reset=True, force=True, validate=True)
		self.assertTrue(second.get("ok"), msg=second.get("validate"))
		report = validate_kentender_mvp_v1()
		self.assertTrue(report.get("ok"), msg=report.get("failures"))

	def test_failed_seed_rolls_back_the_full_reset(self):
		with patch(
			"kentender_core.seeds.kentender_mvp_v1.orchestrator.upsert_planning",
			side_effect=RuntimeError("forced planning seed failure"),
		):
			with self.assertRaisesRegex(RuntimeError, "forced planning seed failure"):
				run_kentender_mvp_v1(reset=True, force=True, validate=True)
		self.assertTrue(
			frappe.db.exists("Procurement Plan", {"plan_code": C.PROCUREMENT_PLAN_CODE})
		)
		self.assertTrue(frappe.db.exists("Demand", {"demand_code": C.DEMAND_CODE}))

	def test_validation_failure_raises(self):
		failed = {
			"ok": False,
			"summary": "1 failed",
			"failures": [{"name": "forced.contract.failure"}],
		}
		with patch(
			"kentender_core.seeds.kentender_mvp_v1.orchestrator._validate",
			return_value=failed,
		):
			with self.assertRaisesRegex(frappe.ValidationError, "forced.contract.failure"):
				validate_kentender_mvp_v1()

	def test_canonical_references_unique(self):
		self.assertEqual(
			frappe.db.count("Strategic Plan", {"plan_code": C.PLAN_CODE, "version_number": 1}),
			1,
		)
		self.assertEqual(
			frappe.db.count("Strategic Plan", {"plan_code": C.CGK_PLAN_CODE, "version_number": 1}),
			1,
		)
		self.assertEqual(
			frappe.db.count("Procurement Budget", {"generated_reference": C.BUD_ACTIVE}),
			1,
		)
		# BUD-CHG-001 v1.3: one site is one Procuring Entity — there is no
		# second-PE (Kisumu) Budget baseline any more (§1.1/§15.6).
		self.assertEqual(
			frappe.db.count("Procurement Budget", {"generated_reference": C.CGK_BUD_ACTIVE}),
			0,
		)
		self.assertEqual(
			frappe.db.count("Procurement Budget Line", {"generated_reference": C.BL_DHI_2027}),
			1,
		)

	def test_org_unit_owners_on_lines(self):
		dhi = frappe.db.get_value(
			"Procurement Budget Line",
			{"generated_reference": C.BL_DHI_2027},
			["owner_org_unit"],
			as_dict=True,
		)
		hwd = frappe.db.get_value(
			"Procurement Budget Line",
			{"generated_reference": C.BL_HWD_2027},
			["owner_org_unit"],
			as_dict=True,
		)
		self.assertEqual(dhi.owner_org_unit, C.OU_DIR_DHP)
		self.assertEqual(hwd.owner_org_unit, C.OU_DIR_HRMD)

	def test_org_unit_parent_same_pe(self):
		child = frappe.db.get_value(
			"Organisation Unit",
			C.OU_DIR_DHP,
			["procuring_entity", "parent_org_unit"],
			as_dict=True,
		)
		parent_pe = frappe.db.get_value(
			"Organisation Unit", child.parent_org_unit, "procuring_entity"
		)
		self.assertEqual(child.procuring_entity, parent_pe)

	def test_unit_isolation_api(self):
		pe_moh = frappe.db.get_value("Procuring Entity", {"entity_code": C.PE_MOH}, "name")
		self.assertTrue(
			can_access_owned_record(
				procuring_entity=pe_moh,
				owner_org_unit=C.OU_DIR_DHP,
				user=C.USER_MEDICAL,
				require_write=True,
			)
		)
		self.assertFalse(
			can_access_owned_record(
				procuring_entity=pe_moh,
				owner_org_unit=C.OU_DIR_HRMD,
				user=C.USER_MEDICAL,
				require_write=True,
			)
		)

	def test_cross_entity_denial(self):
		pe_moh = frappe.db.get_value("Procuring Entity", {"entity_code": C.PE_MOH}, "name")
		pe_cgk = frappe.db.get_value("Procuring Entity", {"entity_code": C.PE_CGKIS}, "name")
		self.assertFalse(
			can_access_owned_record(
				procuring_entity=pe_moh,
				owner_org_unit=C.OU_DIR_DHP,
				user=C.USER_KISUMU_OFFICER,
				require_write=False,
			)
		)
		self.assertFalse(
			can_access_owned_record(
				procuring_entity=pe_cgk,
				owner_org_unit=C.OU_CGK_HEALTH,
				user=C.USER_MEDICAL,
				require_write=False,
			)
		)

	def test_canonical_users_enabled(self):
		for email in C.CANONICAL_USERS:
			self.assertTrue(frappe.db.get_value("User", email, "enabled"), msg=email)

	def test_canonical_plan_approval_actor_and_namespace(self):
		version = frappe.db.get_value(
			"Procurement Plan Version",
			{"version_code": C.PROCUREMENT_PLAN_VERSION_CODE},
			["approved_by", "fixture_namespace"],
			as_dict=True,
		)
		self.assertEqual(version.approved_by, C.USER_HOP)
		self.assertEqual(version.fixture_namespace, C.FIXTURE_NS)

	def test_reset_is_fixture_scoped(self):
		"""Non-fixture PE-MOH plans must survive reset (Contract §8.3)."""
		frappe.set_user("Administrator")
		pe = frappe.db.get_value("Procuring Entity", {"entity_code": C.PE_MOH}, "name")
		stray = "MOH-SP-NONFIXTURE-9998"
		if not frappe.db.exists("Strategic Plan", {"plan_code": stray}):
			frappe.get_doc(
				{
					"doctype": "Strategic Plan",
					"plan_code": stray,
					"version_number": 1,
					"title": "Non-fixture leftover",
					"plan_type": "Entity Strategic Plan",
					"procuring_entity": pe,
					"start_date": "2026-07-01",
					"end_date": "2030-06-30",
					"status": "Draft",
				}
			).insert(ignore_permissions=True)

		run_kentender_mvp_v1(reset=True, force=True, validate=False)
		self.assertTrue(
			frappe.db.exists("Strategic Plan", {"plan_code": stray}),
			msg="non-fixture plan must survive fixture-scoped reset",
		)
		# Cleanup stray so other suites stay clean
		name = frappe.db.get_value("Strategic Plan", {"plan_code": stray}, "name")
		if name:
			frappe.delete_doc("Strategic Plan", name, force=1, ignore_permissions=True)

	def test_dedicated_purge_removes_playwright_runtime_data(self):
		"""The operator purge drops owned browser graphs and preserves canonical data."""
		frappe.set_user("Administrator")
		code = "PLN-MOH-PW-LEFTOVER-001"
		email = "pln.ui.viewer@example.test"
		named_dem_email = "dem-contract-named@example.com"
		pattern_dem_email = "dem-contract-pattern@example.com"
		for name in frappe.get_all(
			"Procurement Plan", filters={"plan_code": code}, pluck="name"
		):
			frappe.delete_doc("Procurement Plan", name, force=1, ignore_permissions=True)
		pe = frappe.db.get_value("Procuring Entity", {"entity_code": C.PE_MOH}, "name") or C.PE_MOH
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_code": code,
				"title": "Playwright leftover plan",
				"procuring_entity": pe,
				"financial_year": "2099/00",
				"period_start": "2099-07-01",
				"period_end": "2100-06-30",
				"currency": "KES",
				"plan_type": "Annual",
				"lifecycle_state": "Open",
				"fixture_namespace": C.PLAYWRIGHT_FIXTURE_NS,
			}
		).insert(ignore_permissions=True)
		version = frappe.get_doc(
			{
				"doctype": "Procurement Plan Version",
				"plan": plan.name,
				"version_number": 1,
				"version_code": f"{code}-V1",
				"status": "Draft",
				"fixture_namespace": C.PLAYWRIGHT_FIXTURE_NS,
			}
		).insert(ignore_permissions=True)
		demand = frappe.get_doc(
			{
				"doctype": "Demand",
				"demand_code": "DEM-G01-PWLEFT",
				"title": "Playwright leftover demand",
				"procuring_entity": C.PE_MOH,
				"owner_org_unit": C.OU_DIR_DHP,
				"requester": C.USER_MEDICAL,
				"demand_route": "Standard",
				"status": "Approved",
				"current_stage": "Complete",
				"currency": "KES",
				"planning_ready": 1,
				"fixture_namespace": C.PLAYWRIGHT_FIXTURE_NS,
			}
		).insert(ignore_permissions=True)
		demand_item = frappe.get_doc(
			{
				"doctype": "Demand Item",
				"demand": demand.name,
				"item_code": "DI-DEM-G01-PWLEFT-1",
				"description": "Playwright item",
				"quantity": 1,
				"confirmed_quantity": 1,
				"requester_estimate": 1_000_000,
				"confirmed_estimate": 1_000_000,
				"currency": "KES",
				"fixture_namespace": C.PLAYWRIGHT_FIXTURE_NS,
			}
		).insert(ignore_permissions=True)
		item = frappe.get_doc(
			{
				"doctype": "Procurement Plan Item",
				"plan": plan.name,
				"plan_item_code": "PPI-PW-LEFTOVER-001",
				"procuring_entity": C.PE_MOH,
				"owner_org_unit": C.OU_DIR_DHP,
				"delivery_org_unit": C.OU_DIR_DHP,
				"baseline_state": "Proposed",
				"fixture_namespace": C.PLAYWRIGHT_FIXTURE_NS,
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Procurement Plan Item Version",
				"plan_item": item.name,
				"plan_version": version.name,
				"item_version_code": "PPI-PW-LEFTOVER-001-1",
				"requirement_title": "Playwright item",
				"confirmed_estimate": 1_000_000,
				"currency": "KES",
				"fixture_namespace": C.PLAYWRIGHT_FIXTURE_NS,
			}
		).insert(ignore_permissions=True)
		validation = frappe.get_doc(
			{
				"doctype": "Plan Validation Result",
				"plan_version": version.name,
				"plan_item": item.name,
				"result_status": "Ready",
				"issue_code": "PW_LEFTOVER",
				"business_message": "Playwright validation",
				"severity": "Info",
				"fixture_namespace": C.PLAYWRIGHT_FIXTURE_NS,
			}
		).insert(ignore_permissions=True)
		consumption = frappe.get_doc(
			{
				"doctype": "Planning Consumption",
				"demand": demand.name,
				"demand_item": demand_item.name,
				"plan_item_code": item.plan_item_code,
				"consumed_quantity": 1,
				"consumed_amount": 1_000_000,
				"currency": "KES",
				"consumed_by": C.USER_PLANNING_OFFICER,
				"consumed_at": C.FIXTURE_NOW_STR,
				"fixture_namespace": C.PLAYWRIGHT_FIXTURE_NS,
			}
		).insert(ignore_permissions=True)
		for test_email in (email, named_dem_email, pattern_dem_email):
			if frappe.db.exists("User", test_email):
				continue
			frappe.get_doc(
				{
					"doctype": "User",
					"email": test_email,
					"first_name": "Playwright",
					"last_name": "Leftover",
					"send_welcome_email": 0,
					"user_type": "System User",
				}
			).insert(ignore_permissions=True)
		strategy = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"plan_code": "MOH-SP-PW-LEFTOVER-001",
				"version_number": 1,
				"title": "Playwright Create leftover strategy",
				"procuring_entity": pe,
				"plan_type": "Entity Strategic Plan",
				"scope_type": "Procuring Entity",
				"scope_id": pe,
				"status": "Draft",
				"start_date": "2099-07-01",
				"end_date": "2100-06-30",
			}
		).insert(ignore_permissions=True)
		strategy_audit = frappe.get_doc(
			{
				"doctype": "Strategy Audit Event",
				"entity_type": "Strategic Plan",
				"entity_name": strategy.name,
				"plan_version": strategy.name,
				"event_type": "Created",
				"new_state": "Draft",
				"actor": C.USER_STR_REVIEWER,
				"event_at": C.FIXTURE_NOW_STR,
				"summary": "Playwright strategy created",
			}
		).insert(ignore_permissions=True)
		leftover_fy = "2099-2100"
		if not frappe.db.exists("Fiscal Year", leftover_fy):
			frappe.get_doc(
				{
					"doctype": "Fiscal Year",
					"year": leftover_fy,
					"year_start_date": "2099-07-01",
					"year_end_date": "2100-06-30",
				}
			).insert(ignore_permissions=True)
		budget = frappe.get_doc(
			{
				"doctype": "Procurement Budget",
				"generated_reference": "MOH-BUD-PW-LEFTOVER-001",
				"fiscal_year": leftover_fy,
				"currency": "KES",
			}
		).insert(ignore_permissions=True)
		canonical_budget = frappe.db.get_value(
			"Procurement Budget", {"generated_reference": C.BUD_ACTIVE}, "name"
		)
		canonical_line = frappe.db.get_value(
			"Procurement Budget Line", {"generated_reference": C.BL_DHI_2027}, "name"
		)
		revision = frappe.get_doc(
			{
				"doctype": "Budget Revision",
				"budget": canonical_budget,
				"generated_reference": "BR-MOH-PW-LEFTOVER-001",
				"status": "Draft",
				"revision_type": "Line amendment",
				"external_approval_reference": "MOF/UI/REV-01",
				"approval_date": "2027-12-01",
				"effective_date": "2027-12-15",
				"reason": "Playwright draft revision",
				"lines": [
					{
						"budget_line": canonical_line,
						"line_code": C.BL_DHI_2027,
						"line_title": "Playwright revision line",
						"before_amount": C.PLAN_AMOUNT_V1,
						"change_amount": 1_000_000,
						"after_amount": C.PLAN_AMOUNT_V1 + 1_000_000,
						"impact_status": "Increase",
					}
				],
			}
		).insert(ignore_permissions=True)
		budget_audit = frappe.get_doc(
			{
				"doctype": "Budget Audit Event",
				"budget": canonical_budget,
				"budget_line": canonical_line,
				"event_type": "Line changed",
				"event_at": C.FIXTURE_NOW_STR,
				"actor": C.USER_BUD_OFFICER,
				"actor_kind": "user",
				"record_code": revision.generated_reference,
				"record_doctype": "Budget Revision",
				"change_summary": "Playwright revision created",
			}
		).insert(ignore_permissions=True)

		purge_dem_test_users(users=[named_dem_email], commit=False)
		self.assertFalse(frappe.db.exists("User", named_dem_email))
		self.assertTrue(
			frappe.db.exists("User", pattern_dem_email),
			msg="exact dem-* purge must preserve unrequested test users",
		)
		purge_kentender_playwright_data(commit=False)
		self.assertFalse(
			frappe.db.exists("Procurement Plan", {"plan_code": code}),
			msg="Playwright leftover Procurement Plan must be deleted on reseed",
		)
		self.assertFalse(frappe.db.exists("Plan Validation Result", validation.name))
		self.assertFalse(frappe.db.exists("Planning Consumption", consumption.name))
		self.assertFalse(frappe.db.exists("Demand", demand.name))
		self.assertFalse(
			frappe.db.exists("User", email),
			msg="explicit @example.test Playwright helpers must be deleted",
		)
		self.assertFalse(
			frappe.db.exists("User", pattern_dem_email),
			msg="reserved dem-* test users must be deleted",
		)
		self.assertFalse(frappe.db.exists("Strategic Plan", strategy.name))
		self.assertFalse(frappe.db.exists("Strategy Audit Event", strategy_audit.name))
		self.assertFalse(frappe.db.exists("Procurement Budget", budget.name))
		self.assertFalse(frappe.db.exists("Budget Revision", revision.name))
		self.assertFalse(frappe.db.exists("Budget Audit Event", budget_audit.name))
		self.assertTrue(
			frappe.db.exists("Procurement Plan", {"plan_code": C.PROCUREMENT_PLAN_CODE})
		)
		self.assertTrue(frappe.db.get_value("User", C.USER_PLANNING_OFFICER, "enabled"))

	def test_reset_preserves_unrelated_moh_plan_and_demand(self):
		"""Contract §8.3: PE ownership alone never makes a row disposable."""
		frappe.set_user("Administrator")
		plan_code = "PLN-MOH-BUSINESS-KEEP-001"
		demand_code = "DMD-MOH-BUSINESS-KEEP-001"
		for doctype, filters in (
			("Procurement Plan", {"plan_code": plan_code}),
			("Demand", {"demand_code": demand_code}),
		):
			for name in frappe.get_all(doctype, filters=filters, pluck="name"):
				frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_code": plan_code,
				"title": "Unrelated Ministry operational plan",
				"procuring_entity": C.PE_MOH,
				"financial_year": "2098/99",
				"period_start": "2098-07-01",
				"period_end": "2099-06-30",
				"currency": "KES",
				"plan_type": "Annual",
				"lifecycle_state": "Open",
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Demand",
				"demand_code": demand_code,
				"title": "Unrelated Ministry operational demand",
				"procuring_entity": C.PE_MOH,
				"owner_org_unit": C.OU_DIR_DHP,
				"requester": C.USER_MEDICAL,
				"demand_route": "Standard",
				"status": "Draft",
				"current_stage": "Request Preparation",
				"currency": "KES",
			}
		).insert(ignore_permissions=True)

		run_kentender_mvp_v1(reset=True, force=True, validate=True)
		self.assertTrue(frappe.db.exists("Procurement Plan", {"plan_code": plan_code}))
		self.assertTrue(frappe.db.exists("Demand", {"demand_code": demand_code}))

		for doctype, filters in (
			("Demand", {"demand_code": demand_code}),
			("Procurement Plan", {"plan_code": plan_code}),
		):
			name = frappe.db.get_value(doctype, filters, "name")
			if name:
				frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)
