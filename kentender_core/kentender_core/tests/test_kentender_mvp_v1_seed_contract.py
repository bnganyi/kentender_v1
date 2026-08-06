# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""KENTENDER_MVP_V1 canonical demo seed — identity + isolation contract."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds.kentender_mvp_v1 import constants as C
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
			frappe.db.count("Budget", {"generated_reference": C.BUD_ACTIVE}),
			1,
		)
		self.assertEqual(
			frappe.db.count("Budget", {"generated_reference": C.CGK_BUD_ACTIVE}),
			1,
		)
		self.assertEqual(
			frappe.db.count("Budget Line", {"generated_reference": C.BL_DHI_2027}),
			1,
		)

	def test_org_unit_owners_on_lines(self):
		dhi = frappe.db.get_value(
			"Budget Line",
			{"generated_reference": C.BL_DHI_2027},
			["owner_org_unit"],
			as_dict=True,
		)
		hwd = frappe.db.get_value(
			"Budget Line",
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

	def test_kisumu_budget_present(self):
		line = frappe.db.get_value(
			"Budget Line",
			{"generated_reference": C.CGK_BL_COLDCHAIN},
			["owner_org_unit", "approved_amount"],
			as_dict=True,
		)
		self.assertTrue(line)
		self.assertEqual(line.owner_org_unit, C.OU_CGK_HEALTH)

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
