# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""C2 — Doc 3 §16 STD row after loader; §17 mapping after WORKS S01 seed.

Also cited for **§E E2** / **PT-HANDOFF-AC-005**: ``default_std_template`` on the
planning template links to the Works STD row after integrated seed (**WORKS-SEED-AC-005**).

Run::

	bench --site <site> run-tests --app kentender_procurement \\
	  --module kentender_procurement.procurement_planning.tests.test_seed_works_stdint_s01_c2
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds.seed_budget_line_dia import verify_prerequisites_for_dia
from kentender_procurement.demand_intake.seeds.seed_dia_basic import run as run_seed_dia_basic
from kentender_procurement.procurement_planning.seeds import seed_works_stdint_s01 as sws
from kentender_procurement.procurement_planning.seeds.works_std_seed_requirements import (
	verify_std_template_doc3_section_16,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
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


def _c2_works_seed_cleanup() -> None:
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


class TestSeedWorksStdintS01C2(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		_c2_works_seed_cleanup()
		frappe.db.commit()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		try:
			_c2_works_seed_cleanup()
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

	def test_c2_section_16_after_upsert_std_template_only(self) -> None:
		self._skip_if_no_pp()
		if not frappe.db.exists("DocType", "STD Template"):
			self.skipTest("STD Template not installed")
		upsert_std_template()
		name = verify_std_template_doc3_section_16(TEMPLATE_CODE)
		self.assertTrue(name)
		self.assertEqual(
			frappe.db.get_value("STD Template", name, "template_code"),
			TEMPLATE_CODE,
		)

	def test_c2_section_16_and_section_17_after_works_seed_run(self) -> None:
		self._skip_if_no_pp()
		self._ensure_budget_and_dia()
		if not frappe.db.exists("Demand", {"demand_id": "DIA-MOH-2026-0004"}):
			run_seed_dia_basic()

		out = sws.run()
		self.assertTrue(out.get("ok"))
		std_name = verify_std_template_doc3_section_16(TEMPLATE_CODE)
		tpl = frappe.db.get_value("Procurement Template", {"template_code": sws.TPL_CODE}, "name")
		self.assertTrue(tpl)
		linked = frappe.db.get_value("Procurement Template", tpl, "default_std_template")
		self.assertEqual(linked, std_name)
