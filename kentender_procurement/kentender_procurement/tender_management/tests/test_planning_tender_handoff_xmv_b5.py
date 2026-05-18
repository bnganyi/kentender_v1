# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""B5 — planning_tender_handoff_xmv (XMV-BND-001 / XMV-PT-001 … 011).

Run:
	bench --site <site> run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_planning_tender_handoff_xmv_b5
"""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services.planning_tender_handoff_xmv import (
	XMV_PT_PLAN_CODES,
	validate_package_for_release_xmv,
)
from frappe.utils import flt

from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
	handoff_integration_test_budget_line_name,
)


class TestPlanningTenderHandoffXmvB5(_ReleaseProcurementPackageHandoffFixtures):
	def test_b5_meta_all_plan_codes_in_module_source(self) -> None:
		self.assertEqual(XMV_PT_PLAN_CODES, {f"XMV-PT-{i:03d}" for i in range(1, 12)})
		src = Path(__file__).resolve().parents[1] / "services" / "planning_tender_handoff_xmv.py"
		text = src.read_text(encoding="utf-8")
		for code in sorted(XMV_PT_PLAN_CODES):
			with self.subTest(code=code):
				self.assertIn(code, text, f"Validator source must reference {code}")

	def test_pt008_critical_when_std_not_allowed_for_tender_creation(self) -> None:
		upsert_std_template()
		std_name = frappe.db.get_value("STD Template", {"template_code": TEMPLATE_CODE}, "name")
		self.assertTrue(std_name)
		prev = frappe.db.get_value("STD Template", std_name, "allowed_for_tender_creation")
		try:
			frappe.db.set_value("STD Template", std_name, "allowed_for_tender_creation", 0)
			plan = self._mk_plan()
			frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
			tpl = self._mk_template()
			pkg = self._mk_package(plan.name, tpl.name)
			self._add_seed_budget_line_and_demand(pkg.name)
			frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
			doc = frappe.get_doc("Procurement Package", pkg.name)
			res = validate_package_for_release_xmv(doc)
			codes = {f.code for f in res.critical}
			self.assertIn("XMV-PT-008", codes)
			self.assertTrue(any("not allowed for tender creation" in f.message for f in res.critical))
		finally:
			frappe.db.set_value("STD Template", std_name, "allowed_for_tender_creation", prev or 1)

	def test_pt009_critical_when_multiple_non_cancelled_tenders(self) -> None:
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")

		def _mk_tm2(ref_suffix: str, *, bypass_duplicate_guard: bool = False) -> str:
			pc_row = frappe.db.get_value(
				"Procurement Package",
				pkg.name,
				["package_code", "plan_id", "currency", "procurement_method", "contract_type"],
				as_dict=True,
			)
			pl_row = frappe.db.get_value(
				"Procurement Plan",
				plan.name,
				["plan_code", "fiscal_year", "procuring_entity", "currency"],
				as_dict=True,
			)
			t = frappe.new_doc("TM2 Tender")
			t.tender_title = f"B5 dup {ref_suffix}"
			t.procurement_package = pkg.name
			t.procurement_plan = plan.name
			t.status = "Draft"
			t.tender_visibility = "Public"
			t.procurement_package_code = (pc_row or {}).get("package_code") or pkg.name
			t.procurement_plan_code = (pl_row or {}).get("plan_code") or ""
			t.procuring_entity_code = (pl_row or {}).get("procuring_entity") or ""
			t.fiscal_year = str((pl_row or {}).get("fiscal_year") or "")
			t.currency = (pc_row or {}).get("currency") or (pl_row or {}).get("currency") or "KES"
			t.procurement_method = (pc_row or {}).get("procurement_method") or "Direct Procurement"
			t.contract_type = (pc_row or {}).get("contract_type")
			t.procurement_category = "Goods"
			if bypass_duplicate_guard:
				t.flags.ignore_validate = True
			t.insert(ignore_permissions=True)
			self._created.append(("TM2 Tender", t.name))
			return t.name

		t1 = _mk_tm2("a")
		t2 = _mk_tm2("b", bypass_duplicate_guard=True)
		self.assertNotEqual(t1, t2)

		doc = frappe.get_doc("Procurement Package", pkg.name)
		res = validate_package_for_release_xmv(doc)
		self.assertTrue(res.has_critical())
		self.assertIn("XMV-PT-009", {f.code for f in res.critical})

	def test_pt006_critical_when_active_line_missing_budget_line(self) -> None:
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")

		ln = frappe.get_all(
			"Procurement Package Line",
			filters={"package_id": pkg.name},
			pluck="name",
			limit=1,
		)[0]
		frappe.db.sql(
			"update `tabProcurement Package Line` set budget_line_id=NULL where name=%s",
			(ln,),
		)
		frappe.db.commit()
		try:
			doc = frappe.get_doc("Procurement Package", pkg.name)
			res = validate_package_for_release_xmv(doc)
			self.assertIn("XMV-PT-006", {f.code for f in res.critical})
		finally:
			bl = handoff_integration_test_budget_line_name()
			if bl:
				frappe.db.set_value("Procurement Package Line", ln, "budget_line_id", bl)
			frappe.db.commit()

	def test_happy_ready_package_has_no_critical_findings(self) -> None:
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		doc = frappe.get_doc("Procurement Package", pkg.name)
		res = validate_package_for_release_xmv(doc)
		self.assertFalse(res.has_critical(), [f.as_dict() for f in res.critical])
		if flt(doc.get("estimated_value")) <= 0:
			self.assertIn("XMV-PT-005", {w.code for w in res.warnings})

	def test_release_service_returns_xmv_findings_on_failure(self) -> None:
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")

		from kentender_procurement.tender_management.services.release_procurement_package_to_tender import (
			release_procurement_package_to_tender,
		)

		std_name = frappe.db.get_value("STD Template", {"template_code": TEMPLATE_CODE}, "name")
		prev = frappe.db.get_value("STD Template", std_name, "allowed_for_tender_creation")
		try:
			frappe.db.set_value("STD Template", std_name, "allowed_for_tender_creation", 0)
			out = release_procurement_package_to_tender(pkg.name)
			self.assertFalse(out.get("ok"), out)
			self.assertIsInstance(out.get("xmv_findings"), list)
			self.assertTrue(any(x.get("code") == "XMV-PT-008" for x in out["xmv_findings"]))
		finally:
			frappe.db.set_value("STD Template", std_name, "allowed_for_tender_creation", prev or 1)
