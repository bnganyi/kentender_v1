# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""C6 — Doc 3 §28–29: WORKS S01 seed verification + §29 tender-stage smoke.

Run::

	bench --site <site> run-tests --app kentender_procurement \\
	  --module kentender_procurement.procurement_planning.tests.test_seed_works_stdint_s01_c6
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds.seed_budget_line_dia import verify_prerequisites_for_dia
from kentender_procurement.demand_intake.seeds.seed_dia_basic import run as run_seed_dia_basic
from kentender_procurement.procurement_planning.seeds import seed_works_stdint_s01 as sws
from kentender_procurement.procurement_planning.seeds import works_stdint_s01_verification as ver
from kentender_procurement.procurement_planning.tests.test_seed_works_stdint_s01_c5 import _c5_cleanup
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE


class TestSeedWorksStdintS01C6(IntegrationTestCase):
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

	def test_c6_section_28_and_29_on_seed_run(self) -> None:
		self._skip_if_no_pp()
		self._ensure_budget_and_dia()
		if not frappe.db.exists("Demand", {"demand_id": "DIA-MOH-2026-0004"}):
			run_seed_dia_basic()

		out = sws.run()
		self.assertTrue(out.get("ok"))
		tender = out.get("tender")
		self.assertTrue(tender)

		s28 = out.get("section_28_verification") or {}
		self.assertTrue(s28.get("all_passed"), s28.get("checks"))

		s29 = out.get("section_29_smoke") or {}
		self.assertTrue(s29.get("ok"), s29)
		self.assertEqual(s29.get("officer_path_required_forms_count"), ver.EXPECTED_REQUIRED_FORMS_INTEGRATED_SEED)
		self.assertEqual(s29.get("required_forms_count"), ver.EXPECTED_REQUIRED_FORMS_PRIMARY_SAMPLE)
		self.assertGreater(int(s29.get("preview_html_length") or 0), 1000)
		self.assertTrue(s29.get("configuration_hash_present"))
		# Doc 5 §25 / WH-013 — hardening + snapshot after §29 smoke
		self.assertEqual(s29.get("hardening_critical_count"), 0, s29)
		self.assertIn(s29.get("works_hardening_status"), ("Pass", "Warning"), s29)
		self.assertTrue(s29.get("hardening_snapshot_hash_present"), s29)
		self.assertTrue(s29.get("hardening_snapshot_json_present"), s29)
		self.assertIn("load_sample_tender_wh013", s29.get("steps") or {}, s29)
		self.assertIn("run_works_tender_stage_hardening", s29.get("steps") or {}, s29)

		td = frappe.get_doc("Procurement Tender", tender)
		self.assertGreaterEqual(len(td.get("boq_items") or []), ver.EXPECTED_BOQ_ROWS)
		self.assertIn("std-poc-preview", (td.generated_tender_pack_html or "").lower())
		self.assertTrue((td.works_hardening_snapshot_hash or "").strip())
		self.assertTrue((td.works_hardening_snapshot_json or "").strip())

	def test_c6_gather_section_28_checks_shape(self) -> None:
		self._skip_if_no_pp()
		self._ensure_budget_and_dia()
		if not frappe.db.exists("Demand", {"demand_id": "DIA-MOH-2026-0004"}):
			run_seed_dia_basic()
		out = sws.run()
		tn = out.get("tender")
		self.assertTrue(tn)
		ch = ver.gather_doc3_section_28_checks(
			tender_name=tn,
			package_name=out["package"],
			plan_name=out["plan"],
			budget_line_name=out["budget_line"],
			demand_ids=(sws.DEMAND_1, sws.DEMAND_2),
			std_template_code=TEMPLATE_CODE,
		)
		self.assertIsInstance(ch.get("checks"), list)
		self.assertGreaterEqual(len(ch["checks"]), 10)
		ids = {c["id"] for c in ch["checks"]}
		self.assertIn("tender_links_std", ids)

	def test_c6_verification_module_smoke_helper(self) -> None:
		self._skip_if_no_pp()
		self._ensure_budget_and_dia()
		if not frappe.db.exists("Demand", {"demand_id": "DIA-MOH-2026-0004"}):
			run_seed_dia_basic()
		sws.run()
		h = ver.run_smoke_for_package_code(sws.PKG_CODE)
		self.assertTrue(h.get("ok"), h)
		sm = h.get("section_29_smoke") or {}
		self.assertTrue(sm.get("ok"), sm)
		# Second smoke call may short-circuit to hardening-only re-run (tender already WH-013 complete).
		self.assertTrue(
			sm.get("rerun_wh013_short_circuit")
			or "load_sample_tender_wh013" in (sm.get("steps") or {}),
			sm,
		)
		self.assertEqual(sm.get("hardening_critical_count"), 0, sm)
