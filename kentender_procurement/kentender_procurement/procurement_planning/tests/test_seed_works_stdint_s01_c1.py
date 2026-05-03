# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""C1 — WORKS S01 deterministic seed: idempotency, line codes, amount roll-up, collision.

Run::

	bench --site <site> run-tests --app kentender_procurement \\
	  --module kentender_procurement.procurement_planning.tests.test_seed_works_stdint_s01_c1
"""

from __future__ import annotations

import frappe
from frappe.exceptions import ValidationError
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_core.seeds import constants as C
from kentender_core.seeds.seed_budget_line_dia import verify_prerequisites_for_dia
from kentender_procurement.demand_intake.seeds.seed_dia_basic import run as run_seed_dia_basic
from kentender_procurement.procurement_planning.seeds import seed_works_stdint_s01 as sws
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_f1 import (
	TPL_MED,
	run as run_f1,
)


def _delete_tenders_for_package(package_name: str) -> None:
	for t in frappe.get_all("Procurement Tender", filters={"procurement_package": package_name}, pluck="name"):
		frappe.delete_doc("Procurement Tender", t, force=True, ignore_permissions=True)


def _delete_package_cascade_by_code(package_code: str) -> None:
	name = frappe.db.get_value("Procurement Package", {"package_code": package_code}, "name")
	if not name:
		return
	_delete_tenders_for_package(name)
	for line in frappe.get_all("Procurement Package Line", filters={"package_id": name}, pluck="name"):
		frappe.delete_doc("Procurement Package Line", line, force=True, ignore_permissions=True)
	frappe.delete_doc("Procurement Package", name, force=True, ignore_permissions=True)


def _c1_works_seed_cleanup() -> None:
	_delete_package_cascade_by_code(sws.PKG_CODE)
	for did in (sws.DEMAND_1, sws.DEMAND_2):
		n = frappe.db.get_value("Demand", {"demand_id": did}, "name")
		if n:
			frappe.delete_doc("Demand", n, force=True, ignore_permissions=True)
	tn = frappe.db.get_value("Procurement Template", {"template_code": sws.TPL_CODE}, "name")
	if tn:
		frappe.delete_doc("Procurement Template", tn, force=True, ignore_permissions=True)
	pn = frappe.db.get_value("Procurement Plan", {"plan_code": sws.PLAN_CODE}, "name")
	if pn:
		frappe.delete_doc("Procurement Plan", pn, force=True, ignore_permissions=True)


class TestSeedWorksStdintS01C1(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		_c1_works_seed_cleanup()
		frappe.db.commit()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		try:
			_c1_works_seed_cleanup()
			frappe.db.commit()
		finally:
			super().tearDown()

	def _skip_if_no_pp(self) -> None:
		if not frappe.db.exists("DocType", "Procurement Plan"):
			self.skipTest("Procurement Plan not installed")

	def _ensure_budget_and_dia(self) -> None:
		v = verify_prerequisites_for_dia()
		if not v.get("ok"):
			self.skipTest("Budget / DIA prerequisites: " + str(v.get("missing")))

	def test_c1_idempotent_line_codes_and_rollup(self) -> None:
		self._skip_if_no_pp()
		self._ensure_budget_and_dia()
		if not frappe.db.exists("Demand", {"demand_id": "DIA-MOH-2026-0004"}):
			run_seed_dia_basic()

		out1 = sws.run()
		self.assertTrue(out1.get("ok"))
		pkg = out1.get("package")
		self.assertTrue(pkg)

		out2 = sws.run()
		self.assertTrue(out2.get("ok"))
		self.assertEqual(out2.get("package"), pkg)

		codes = frappe.get_all(
			"Procurement Package Line",
			filters={"package_id": pkg, "is_active": 1},
			pluck="package_line_code",
		)
		self.assertEqual(len(codes), 2)
		self.assertIn(sws.LINE_CODE_1, codes)
		self.assertIn(sws.LINE_CODE_2, codes)

		lines = frappe.get_all(
			"Procurement Package Line",
			filters={"package_id": pkg, "is_active": 1},
			fields=["amount"],
		)
		line_sum = flt(sum(flt(r.amount) for r in lines))
		pkg_ev = flt(frappe.db.get_value("Procurement Package", pkg, "estimated_value"))
		self.assertLess(abs(line_sum - pkg_ev), 0.02, (line_sum, pkg_ev))

	def test_c1_collision_non_works_package_code(self) -> None:
		self._skip_if_no_pp()
		self._ensure_budget_and_dia()
		if not frappe.db.exists("Demand", {"demand_id": "DIA-MOH-2026-0004"}):
			run_seed_dia_basic()
		if not frappe.db.get_value("Procurement Template", {"template_code": TPL_MED}, "name"):
			run_f1(ensure_dia=True)
			frappe.db.commit()
			_delete_package_cascade_by_code(sws.PKG_CODE)

		tpl_med = frappe.db.get_value("Procurement Template", {"template_code": TPL_MED}, "name")
		if not tpl_med:
			self.skipTest("TPL-MED-001 template missing for collision stub")

		plan_code = f"C1-COLL-{frappe.generate_hash(length=6)}"
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": "C1 collision stub plan",
				"plan_code": plan_code,
				"fiscal_year": 2026,
				"procuring_entity": C.ENTITY_MOH,
				"currency": "KES",
				"status": "Draft",
				"is_active": 1,
			}
		)
		plan.insert(ignore_permissions=True)

		try:
			pkg = frappe.get_doc(
				{
					"doctype": "Procurement Package",
					"package_code": sws.PKG_CODE,
					"package_name": "C1 collision stub (non-Works)",
					"planner_notes": "test stub",
					"plan_id": plan.name,
					"template_id": tpl_med,
					"procurement_method": "Open Tender",
					"contract_type": "Fixed Price",
					"currency": "KES",
					"estimated_value": 1_000_000.0,
					"status": "Draft",
					"is_active": 1,
					"risk_profile_id": frappe.db.get_value("Procurement Template", tpl_med, "risk_profile_id"),
					"kpi_profile_id": frappe.db.get_value("Procurement Template", tpl_med, "kpi_profile_id"),
					"decision_criteria_profile_id": frappe.db.get_value(
						"Procurement Template", tpl_med, "decision_criteria_profile_id"
					),
					"vendor_management_profile_id": frappe.db.get_value(
						"Procurement Template", tpl_med, "vendor_management_profile_id"
					),
				}
			)
			pkg.insert(ignore_permissions=True)
			frappe.db.commit()

			with self.assertRaises(ValidationError) as ctx:
				sws.run()
			combined = " ".join(
				filter(
					None,
					(str(ctx.exception), getattr(ctx.exception, "title", None)),
				)
			).lower()
			self.assertTrue("collision" in combined or "non-works" in combined, combined)
		finally:
			_delete_package_cascade_by_code(sws.PKG_CODE)
			frappe.delete_doc("Procurement Plan", plan.name, force=True, ignore_permissions=True)
			frappe.db.commit()
