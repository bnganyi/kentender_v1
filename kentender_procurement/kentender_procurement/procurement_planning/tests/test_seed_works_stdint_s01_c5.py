# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""C5 — Doc 3 §20: WORKS S01 seed applies labelled sample officer completion on tender JSON.

After WH-013, ``load_sample_tender`` (§29 smoke) replaces many flat keys with the primary
``sample_tender.json`` values; §20 **SEED.* / merge version** markers are re-stamped so
idempotency and audit labelling still hold.

Run::

	bench --site <site> run-tests --app kentender_procurement \\
	  --module kentender_procurement.procurement_planning.tests.test_seed_works_stdint_s01_c5
"""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds.seed_budget_line_dia import verify_prerequisites_for_dia
from kentender_procurement.demand_intake.seeds.seed_dia_basic import run as run_seed_dia_basic
from kentender_procurement.procurement_planning.seeds import seed_works_stdint_s01 as sws


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


def _c5_cleanup() -> None:
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


class TestSeedWorksStdintS01C5(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		_c5_cleanup()
		frappe.db.commit()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		try:
			_c5_cleanup()
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

	def test_c5_sample_officer_label_and_values_in_configuration_json(self) -> None:
		self._skip_if_no_pp()
		self._ensure_budget_and_dia()
		if not frappe.db.exists("Demand", {"demand_id": "DIA-MOH-2026-0004"}):
			run_seed_dia_basic()

		out = sws.run()
		self.assertTrue(out.get("ok"))
		self.assertTrue(out.get("sample_officer_completion_applied"))
		tender = out.get("tender")
		self.assertTrue(tender)
		cfg = json.loads(frappe.db.get_value("Procurement Tender", tender, "configuration_json") or "{}")
		self.assertEqual(cfg.get("SEED.STDINT_WORKS_S01.SAMPLE_OFFICER_APPLIED"), 1)
		label = cfg.get("SEED.STDINT_WORKS_S01.SAMPLE_OFFICER_LABEL") or ""
		self.assertIn("doc 3 §20", label.lower())
		self.assertIn("not planning authority", label.lower())
		# Officer-only merge used 90 days / int flags; primary sample (post WH-013) uses 120 / booleans.
		self.assertEqual(cfg.get("DATES.TENDER_VALIDITY_DAYS"), 120)
		self.assertTrue(cfg.get("DATES.SITE_VISIT_REQUIRED") in (True, 1))
		self.assertEqual(cfg.get("SECURITY.TENDER_SECURITY_MODE"), "TENDER_SECURITY")
		self.assertTrue(cfg.get("PARTICIPATION.JV_ALLOWED") in (True, 1))
		self.assertTrue(cfg.get("WORKS.DAYWORKS_INCLUDED") in (True, 1))
		self.assertEqual(cfg.get("SEED.STDINT_WORKS_S01.SAMPLE_OFFICER_MERGE_VERSION"), sws._SAMPLE_OFFICER_MERGE_VERSION)
		self.assertEqual(cfg.get("CONTRACT.DEFECTS_LIABILITY_PERIOD_MONTHS"), 12)

	def test_c5_idempotent_second_run_skips_reapply(self) -> None:
		self._skip_if_no_pp()
		self._ensure_budget_and_dia()
		if not frappe.db.exists("Demand", {"demand_id": "DIA-MOH-2026-0004"}):
			run_seed_dia_basic()

		first = sws.run()
		self.assertTrue(first.get("sample_officer_completion_applied"))
		second = sws.run()
		self.assertTrue(second.get("ok"))
		self.assertFalse(second.get("sample_officer_completion_applied"))
