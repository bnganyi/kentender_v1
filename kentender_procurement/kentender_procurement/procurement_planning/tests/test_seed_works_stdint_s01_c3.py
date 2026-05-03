# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""C3 — Doc 3 §18.1: WORKS S01 seed releases package via workflow (Ready → Released + tender).

Run::

	bench --site <site> run-tests --app kentender_procurement \\
	  --module kentender_procurement.procurement_planning.tests.test_seed_works_stdint_s01_c3
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds.seed_budget_line_dia import verify_prerequisites_for_dia
from kentender_procurement.demand_intake.seeds.seed_dia_basic import run as run_seed_dia_basic
from kentender_procurement.procurement_planning.seeds import seed_works_stdint_s01 as sws
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE


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


def _c3_works_seed_cleanup() -> None:
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


class TestSeedWorksStdintS01C3(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		_c3_works_seed_cleanup()
		frappe.db.commit()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		try:
			_c3_works_seed_cleanup()
			frappe.db.commit()
		finally:
			super().tearDown()

	def _skip_if_no_pp(self) -> None:
		if not frappe.db.exists("DocType", "Procurement Plan"):
			self.skipTest("Procurement Plan not installed")
		if not frappe.db.exists("DocType", "Procurement Tender"):
			self.skipTest("Procurement Tender not installed")

	def _ensure_budget_and_dia(self) -> None:
		v = verify_prerequisites_for_dia()
		if not v.get("ok"):
			self.skipTest("Budget / DIA prerequisites: " + str(v.get("missing")))

	def test_c3_release_via_workflow_and_doc18_1_assertions(self) -> None:
		self._skip_if_no_pp()
		self._ensure_budget_and_dia()
		if not frappe.db.exists("Demand", {"demand_id": "DIA-MOH-2026-0004"}):
			run_seed_dia_basic()

		out = sws.run()
		self.assertTrue(out.get("ok"))
		self.assertFalse(out.get("release_skipped"))
		pkg = out.get("package")
		plan = out.get("plan")
		tender = out.get("tender")
		self.assertTrue(pkg and plan and tender)

		self.assertEqual(
			(frappe.db.get_value("Procurement Package", pkg, "status") or "").strip(),
			"Released to Tender",
		)
		self.assertEqual(
			(frappe.db.get_value("Procurement Plan", plan, "status") or "").strip(),
			"Approved",
		)
		self.assertEqual(frappe.db.get_value("Procurement Tender", tender, "procurement_package"), pkg)
		self.assertEqual(frappe.db.get_value("Procurement Tender", tender, "procurement_plan"), plan)
		std = frappe.db.get_value("Procurement Tender", tender, "std_template")
		self.assertTrue(std)
		self.assertEqual(
			frappe.db.get_value("STD Template", std, "template_code"),
			TEMPLATE_CODE,
		)
		self.assertTrue((frappe.db.get_value("Procurement Tender", tender, "configuration_json") or "").strip())

	def test_c3_idempotent_second_run_same_tender(self) -> None:
		self._skip_if_no_pp()
		self._ensure_budget_and_dia()
		if not frappe.db.exists("Demand", {"demand_id": "DIA-MOH-2026-0004"}):
			run_seed_dia_basic()

		first = sws.run()
		self.assertTrue(first.get("ok"))
		t1 = first.get("tender")
		second = sws.run()
		self.assertTrue(second.get("ok"))
		self.assertTrue(second.get("release_skipped"))
		self.assertEqual(second.get("tender"), t1)

		active = frappe.get_all(
			"Procurement Tender",
			filters={"procurement_package": first.get("package"), "tender_status": ("!=", "Cancelled")},
			pluck="name",
		)
		self.assertEqual(len(active), 1)
