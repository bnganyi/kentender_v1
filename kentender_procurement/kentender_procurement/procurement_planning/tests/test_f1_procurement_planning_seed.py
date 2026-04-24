# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""F1 / F2 — full planning seed and dependency validation.

Run:
  bench --site <site> run-tests --app kentender_procurement \\
    --module kentender_procurement.procurement_planning.tests.test_f1_procurement_planning_seed
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import cint, flt

from kentender_core.seeds.seed_budget_line_dia import verify_prerequisites_for_dia
from kentender_procurement.demand_intake.seeds.seed_dia_basic import run as run_seed_dia_basic
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_f1 import (
	BID_0004,
	BID_0011,
	BID_0020,
	BID_0030,
	PKG1_CODE,
	PKG2_CODE,
	PKG3_CODE,
	PLAN_CODE,
	TPL_EMG,
	TPL_ICT,
	TPL_MED,
	run as run_f1,
)
from kentender_procurement.procurement_planning.seeds.validate_planning_seed_dependencies import (
	get_validation_report,
)

PKG_CODES = (PKG1_CODE, PKG2_CODE, PKG3_CODE)


def _delete_package_cascade(package_name: str) -> None:
	if not package_name:
		return
	for line in frappe.get_all("Procurement Package Line", filters={"package_id": package_name}, pluck="name"):
		frappe.delete_doc("Procurement Package Line", line, force=True, ignore_permissions=True)
	frappe.delete_doc("Procurement Package", package_name, force=True, ignore_permissions=True)


def _f1_test_cleanup() -> None:
	plan = frappe.db.get_value("Procurement Plan", {"plan_code": PLAN_CODE}, "name")
	if plan:
		for code in PKG_CODES:
			pkg = frappe.db.get_value("Procurement Package", {"plan_id": plan, "package_code": code}, "name")
			_delete_package_cascade(pkg)
	for did in (BID_0011, BID_0020, BID_0030):
		n = frappe.db.get_value("Demand", {"demand_id": did}, "name")
		if n:
			frappe.delete_doc("Demand", n, force=True, ignore_permissions=True)
	for code in (TPL_ICT, TPL_EMG):
		tn = frappe.db.get_value("Procurement Template", {"template_code": code}, "name")
		if tn:
			frappe.delete_doc("Procurement Template", tn, force=True, ignore_permissions=True)


class TestF1ProcurementPlanningSeed(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		_f1_test_cleanup()

	def tearDown(self):
		frappe.set_user("Administrator")
		try:
			_f1_test_cleanup()
			frappe.db.commit()
		finally:
			super().tearDown()

	def test_f2_ok_after_dia_f1_prereq(self):
		if not frappe.db.exists("DocType", "Procurement Plan"):
			self.skipTest("Procurement Plan not installed")
		v = verify_prerequisites_for_dia()
		if not v.get("ok"):
			self.skipTest("Budget: " + str(v.get("missing")))
		if not frappe.db.exists("Demand", {"demand_id": BID_0004}):
			run_seed_dia_basic()
		out = run_f1(ensure_dia=True)
		self.assertEqual(out.get("pack"), "seed_procurement_planning_f1")
		r2 = get_validation_report()
		self.assertTrue(r2.get("ok"), r2)

	def test_f1_packages_and_invariants(self):
		if not frappe.db.exists("DocType", "Procurement Plan"):
			self.skipTest("Procurement Plan not installed")
		v = verify_prerequisites_for_dia()
		if not v.get("ok"):
			self.skipTest("Budget: " + str(v.get("missing")))
		if not frappe.db.exists("Demand", {"demand_id": BID_0004}):
			run_seed_dia_basic()
		one = run_f1(ensure_dia=True)
		self.assertGreaterEqual(len(one.get("created") or []), 1)
		plan = frappe.db.get_value("Procurement Plan", {"plan_code": PLAN_CODE}, "name")
		self.assertTrue(plan)
		pkg1 = frappe.db.get_value("Procurement Package", {"plan_id": plan, "package_code": PKG1_CODE}, "name")
		self.assertTrue(pkg1)
		lines1 = frappe.get_all(
			"Procurement Package Line", filters={"package_id": pkg1, "is_active": 1}, fields=["amount"]
		)
		self.assertEqual(flt(sum(flt(x.amount) for x in lines1)), 5_000_000.0)
		self.assertEqual(
			flt(frappe.db.get_value("Procurement Package", pkg1, "estimated_value")),
			5_000_000.0,
		)
		pkg2 = frappe.db.get_value("Procurement Package", {"plan_id": plan, "package_code": PKG2_CODE}, "name")
		self.assertTrue(pkg2)
		lines2 = frappe.get_all(
			"Procurement Package Line", filters={"package_id": pkg2, "is_active": 1}, fields=["amount"]
		)
		self.assertEqual(flt(sum(flt(x.amount) for x in lines2)), 1_200_000.0)
		pkg3 = frappe.db.get_value("Procurement Package", {"plan_id": plan, "package_code": PKG3_CODE}, "name")
		self.assertTrue(pkg3)
		lines3 = frappe.get_all(
			"Procurement Package Line", filters={"package_id": pkg3, "is_active": 1}, fields=["amount"]
		)
		self.assertEqual(flt(sum(flt(x.amount) for x in lines3)), 4_000_000.0)
		self.assertEqual(cint(frappe.db.get_value("Procurement Package", pkg3, "is_emergency")), 1)
		t3 = frappe.db.get_value(
			"Procurement Template", frappe.db.get_value("Procurement Package", pkg3, "template_id"), "template_code"
		)
		self.assertEqual(t3, TPL_EMG)

		twice = run_f1(ensure_dia=True)
		self.assertEqual(len(twice.get("created") or []), 0, twice)
		self.assertEqual(len(twice.get("skipped_package_codes") or []), 3)
