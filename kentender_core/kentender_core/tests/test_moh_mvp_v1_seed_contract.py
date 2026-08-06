# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""MOH_MVP_V1 canonical demo seed — identity + idempotency contract."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds.moh_mvp_v1 import constants as C
from kentender_core.seeds.moh_mvp_v1.orchestrator import run_moh_mvp_v1, validate_moh_mvp_v1


class TestMohMvpV1SeedContract(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.first = run_moh_mvp_v1(reset=True, force=True, validate=True)

	def test_first_run_ok(self):
		self.assertTrue(self.first.get("ok"), msg=self.first.get("validate"))

	def test_idempotent_second_run(self):
		frappe.set_user("Administrator")
		second = run_moh_mvp_v1(reset=True, force=True, validate=True)
		self.assertTrue(second.get("ok"), msg=second.get("validate"))
		report = validate_moh_mvp_v1()
		self.assertTrue(report.get("ok"), msg=report.get("failures"))

	def test_canonical_references_unique(self):
		self.assertEqual(
			frappe.db.count("Strategic Plan", {"plan_code": C.PLAN_CODE, "version_number": 1}),
			1,
		)
		self.assertEqual(
			frappe.db.count("Budget", {"generated_reference": C.BUD_ACTIVE}),
			1,
		)
		self.assertEqual(
			frappe.db.count("Budget Line", {"generated_reference": C.BL_DHI_2027}),
			1,
		)

	def test_state_department_owners_on_lines(self):
		dhi = frappe.db.get_value(
			"Budget Line",
			{"generated_reference": C.BL_DHI_2027},
			["owner_state_department", "owner_directorate"],
			as_dict=True,
		)
		hwd = frappe.db.get_value(
			"Budget Line",
			{"generated_reference": C.BL_HWD_2027},
			["owner_state_department", "owner_directorate"],
			as_dict=True,
		)
		self.assertEqual(dhi.owner_state_department, C.SD_MEDICAL)
		self.assertEqual(dhi.owner_directorate, C.DIR_DHP)
		self.assertEqual(hwd.owner_state_department, C.SD_PUBLIC)
		self.assertEqual(hwd.owner_directorate, C.DIR_HRMD)

	def test_canonical_users_enabled(self):
		for email in C.CANONICAL_USERS:
			self.assertTrue(frappe.db.get_value("User", email, "enabled"), msg=email)
