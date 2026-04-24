# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""C4 — PP3 planning slice integration test.

Run:
  bench --site <site> run-tests --app kentender_procurement \\
    --module kentender_procurement.procurement_planning.tests.test_c4_pp3_slice
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_core.seeds.seed_budget_line_dia import verify_prerequisites_for_dia
from kentender_procurement.demand_intake.seeds.seed_dia_basic import run as run_seed_dia_basic
from kentender_procurement.demand_intake.seeds.seed_dia_empty import run as run_seed_dia_empty
from kentender_procurement.procurement_planning.seeds.seed_planning_pp3_slice import (
	DEMAND_0004,
	DEMAND_0011,
	PP3_PACKAGE_CODE,
	PP3_PACKAGE_NAME,
	PP3_PLAN_CODE,
	PP3_TEMPLATE_CODE,
	run as run_seed_planning_pp3_slice,
)


def _delete_pp3_artifacts(*, restore_demand_0004_total: float | None) -> None:
	pkg = frappe.db.get_value("Procurement Package", {"package_code": PP3_PACKAGE_CODE}, "name")
	if pkg:
		for line in frappe.get_all(
			"Procurement Package Line", filters={"package_id": pkg}, pluck="name"
		):
			frappe.delete_doc("Procurement Package Line", line, force=True, ignore_permissions=True)
		frappe.delete_doc("Procurement Package", pkg, force=True, ignore_permissions=True)

	n11 = frappe.db.get_value("Demand", {"demand_id": DEMAND_0011}, "name")
	if n11:
		frappe.delete_doc("Demand", n11, force=True, ignore_permissions=True)

	if restore_demand_0004_total is not None:
		n4 = frappe.db.get_value("Demand", {"demand_id": DEMAND_0004}, "name")
		if n4:
			frappe.db.set_value(
				"Demand",
				n4,
				"total_amount",
				restore_demand_0004_total,
				update_modified=False,
			)

	tpl = frappe.db.get_value("Procurement Template", {"template_code": PP3_TEMPLATE_CODE}, "name")
	if tpl:
		frappe.delete_doc("Procurement Template", tpl, force=True, ignore_permissions=True)

	pl = frappe.db.get_value("Procurement Plan", {"plan_code": PP3_PLAN_CODE}, "name")
	if pl:
		frappe.delete_doc("Procurement Plan", pl, force=True, ignore_permissions=True)

	for doctype, code in (
		("Vendor Management Profile", "VM-STANDARD"),
		("Decision Criteria Profile", "CRIT-STANDARD"),
		("KPI Profile", "KPI-STANDARD"),
		("Risk Profile", "RISK-STANDARD"),
	):
		n = frappe.db.get_value(doctype, {"profile_code": code}, "name")
		if n:
			frappe.delete_doc(doctype, n, force=True, ignore_permissions=True)


class TestC4Pp3PlanningSlice(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self._restore_0004_total: float | None = None
		n4 = frappe.db.get_value("Demand", {"demand_id": DEMAND_0004}, "name")
		if n4:
			self._restore_0004_total = flt(frappe.db.get_value("Demand", n4, "total_amount"))
		_delete_pp3_artifacts(restore_demand_0004_total=None)

	def tearDown(self):
		frappe.set_user("Administrator")
		try:
			_delete_pp3_artifacts(restore_demand_0004_total=self._restore_0004_total)
			frappe.db.commit()
		finally:
			super().tearDown()

	def test_pp3_slice_creates_package_and_lines(self):
		if not frappe.db.exists("DocType", "Demand"):
			self.skipTest("Demand DocType not installed")
		v = verify_prerequisites_for_dia()
		if not v.get("ok"):
			self.skipTest("Budget lines missing: " + str(v.get("missing")))

		if not frappe.db.exists("Demand", {"demand_id": DEMAND_0004}):
			run_seed_dia_basic()

		name4 = frappe.db.get_value("Demand", {"demand_id": DEMAND_0004}, "name")
		self.assertTrue(name4, "DIA-MOH-2026-0004 required")

		out = run_seed_planning_pp3_slice()
		self.assertFalse(out.get("skipped"), out)
		pkg_name = out.get("package")
		self.assertTrue(pkg_name)
		self.assertEqual(out.get("package_code"), PP3_PACKAGE_CODE)
		self.assertEqual(out.get("lines_created"), 2)
		self.assertEqual(flt(out.get("estimated_value")), 5_000_000.0)

		pkg = frappe.get_doc("Procurement Package", pkg_name)
		self.assertEqual(pkg.package_code, PP3_PACKAGE_CODE)
		self.assertEqual(pkg.package_name, PP3_PACKAGE_NAME)
		self.assertEqual(pkg.procurement_method, "Open Tender")
		self.assertEqual(pkg.contract_type, "Fixed Price")
		self.assertEqual(flt(pkg.estimated_value), 5_000_000.0)

		tpl = frappe.get_doc("Procurement Template", pkg.template_id)
		self.assertEqual(tpl.template_code, PP3_TEMPLATE_CODE)
		self.assertEqual(pkg.risk_profile_id, tpl.risk_profile_id)
		self.assertEqual(pkg.kpi_profile_id, tpl.kpi_profile_id)
		self.assertEqual(pkg.decision_criteria_profile_id, tpl.decision_criteria_profile_id)
		self.assertEqual(pkg.vendor_management_profile_id, tpl.vendor_management_profile_id)

		lines = frappe.get_all(
			"Procurement Package Line",
			filters={"package_id": pkg_name, "is_active": 1},
			fields=["demand_id", "amount"],
		)
		self.assertEqual(len(lines), 2)
		demands = {r.demand_id for r in lines}
		n4 = frappe.db.get_value("Demand", {"demand_id": DEMAND_0004}, "name")
		n11 = frappe.db.get_value("Demand", {"demand_id": DEMAND_0011}, "name")
		self.assertEqual(demands, {n4, n11})

	def test_pp3_slice_idempotent_skip(self):
		if not frappe.db.exists("DocType", "Demand"):
			self.skipTest("Demand DocType not installed")
		v = verify_prerequisites_for_dia()
		if not v.get("ok"):
			self.skipTest("Budget lines missing: " + str(v.get("missing")))
		if not frappe.db.exists("Demand", {"demand_id": DEMAND_0004}):
			run_seed_dia_basic()
		name4 = frappe.db.get_value("Demand", {"demand_id": DEMAND_0004}, "name")
		self.assertTrue(name4)
		run_seed_planning_pp3_slice()
		second = run_seed_planning_pp3_slice()
		self.assertTrue(second.get("skipped"))
		self.assertEqual(second.get("package_code"), PP3_PACKAGE_CODE)
