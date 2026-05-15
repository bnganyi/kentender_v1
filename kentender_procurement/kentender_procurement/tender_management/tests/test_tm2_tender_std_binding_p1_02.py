# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-02 — TM2 Tender STD Binding: active uniqueness, codes, published lock, parent sync.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_tm2_tender_std_binding_p1_02
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


class TestTM2TenderStdBindingP102(_ReleaseProcurementPackageHandoffFixtures):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for row in frappe.get_all(
			"TM2 Tender STD Binding",
			filters={"tender_code": ["like", "TND-P102%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Tender STD Binding", row):
				frappe.delete_doc("TM2 Tender STD Binding", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("Tender STD Instance", filters={"tm2_tender": ["like", "TND-P102%"]}, pluck="name"):
			if frappe.db.exists("Tender STD Instance", row):
				frappe.delete_doc("Tender STD Instance", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P102%"]}, pluck="name"):
			if frappe.db.exists("TM2 Tender", row):
				frappe.delete_doc("TM2 Tender", row, force=True, ignore_permissions=True)
		super().tearDown()

	def _mk_tm2(self, plan_name: str, pkg_name: str, *, tender_code: str | None = None) -> frappe.model.document.Document:
		payload = {
			"doctype": "TM2 Tender",
			"tender_title": "P102 TM2",
			"procurement_package": pkg_name,
			"procurement_plan": plan_name,
			"procurement_category": "Goods",
			"tender_visibility": "Public",
		}
		if tender_code:
			payload["tender_code"] = tender_code
		doc = frappe.get_doc(payload).insert(ignore_permissions=True)
		return doc

	def _mk_tm2_std_instance(self, tm2_name: str) -> frappe.model.document.Document:
		ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
		return frappe.get_doc(
			{
				"doctype": "Tender STD Instance",
				"naming_series": "STDINST-.#####",
				"tm2_tender": tm2_name,
				"template_version_code": ver,
				"applicability_profile_code": prof,
				"procurement_category": "WORKS",
				"procurement_method": "OPEN_COMPETITIVE_TENDERING",
				"instance_status": "Draft",
				"readiness_status": "Not Ready",
				"created_from_tender_context": 1,
			}
		).insert(ignore_permissions=True)

	def _mk_binding(
		self,
		tm2_name: str,
		si_name: str,
		*,
		binding_code: str | None = None,
		is_active: int = 1,
		binding_status: str = "Draft",
		readiness_status: str = "Not Ready",
	) -> frappe.model.document.Document:
		ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
		payload = {
			"doctype": "TM2 Tender STD Binding",
			"tm2_tender": tm2_name,
			"std_template": TEMPLATE_CODE,
			"std_template_code": TEMPLATE_CODE,
			"std_template_version_code": ver,
			"std_applicability_profile_code": prof,
			"tender_std_instance": si_name,
			"is_active": is_active,
			"binding_status": binding_status,
			"readiness_status": readiness_status,
		}
		if binding_code:
			payload["binding_code"] = binding_code
		return frappe.get_doc(payload).insert(ignore_permissions=True)

	def test_p102_insert_sets_std_bound_on_parent(self) -> None:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P102-2028-0001")
		si = self._mk_tm2_std_instance(tm2.name)
		b = self._mk_binding(tm2.name, si.name, readiness_status="Ready")
		self.assertTrue(b.binding_code.startswith(f"TSB-{tm2.tender_code}-"))
		std_bound = int(frappe.db.get_value("TM2 Tender", tm2.name, "std_bound") or 0)
		self.assertEqual(std_bound, 1)
		self.assertEqual(frappe.db.get_value("TM2 Tender", tm2.name, "std_readiness_status"), "Ready")

	def test_p102_second_active_binding_rejected(self) -> None:
		plan = self._mk_plan(fiscal_year=2027)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P102-2027-0001")
		si1 = self._mk_tm2_std_instance(tm2.name)
		self._mk_binding(tm2.name, si1.name)
		ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
		doc2 = frappe.get_doc(
			{
				"doctype": "TM2 Tender STD Binding",
				"tm2_tender": tm2.name,
				"std_template": TEMPLATE_CODE,
				"std_template_code": TEMPLATE_CODE,
				"std_template_version_code": ver,
				"std_applicability_profile_code": prof,
				"tender_std_instance": si1.name,
				"is_active": 1,
				"binding_status": "Draft",
				"readiness_status": "Not Ready",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc2.insert(ignore_permissions=True)

	def test_p102_duplicate_binding_code_rejected(self) -> None:
		plan = self._mk_plan(fiscal_year=2026)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2a = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P102-2026-0001")
		tm2b = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P102-2026-0002")
		sia = self._mk_tm2_std_instance(tm2a.name)
		sib = self._mk_tm2_std_instance(tm2b.name)
		code = "TSB-P102-DUP-FIXED-001"
		self._mk_binding(tm2a.name, sia.name, binding_code=code)
		ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
		doc2 = frappe.get_doc(
			{
				"doctype": "TM2 Tender STD Binding",
				"tm2_tender": tm2b.name,
				"binding_code": code,
				"std_template": TEMPLATE_CODE,
				"std_template_code": TEMPLATE_CODE,
				"std_template_version_code": ver,
				"std_applicability_profile_code": prof,
				"tender_std_instance": sib.name,
				"is_active": 0,
				"binding_status": "Draft",
				"readiness_status": "Not Ready",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc2.insert(ignore_permissions=True)

	def test_p102_published_binding_immutable(self) -> None:
		plan = self._mk_plan(fiscal_year=2030)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P102-2030-0001")
		si = self._mk_tm2_std_instance(tm2.name)
		b = self._mk_binding(tm2.name, si.name)
		b.binding_status = "Published"
		b.save(ignore_permissions=True)
		b.reload()
		b.std_applicability_profile_code = "CHANGED-PROFILE"
		with self.assertRaises(frappe.ValidationError):
			b.save(ignore_permissions=True)

	def test_p102_meta_doc9_minimum_fields(self) -> None:
		meta = frappe.get_meta("TM2 Tender STD Binding")
		for fn in (
			"binding_code",
			"tender_code",
			"std_template_code",
			"std_template_version_code",
			"std_applicability_profile_code",
			"tender_std_instance_code",
			"bundle_output_code",
			"dsm_output_code",
			"dom_output_code",
			"dem_output_code",
			"dcm_output_code",
			"publication_snapshot_code",
			"binding_status",
			"readiness_status",
			"published_snapshot_hash",
			"is_active",
		):
			with self.subTest(fieldname=fn):
				self.assertIsNotNone(meta.get_field(fn), f"missing {fn}")

	def test_p102_tsi_requires_xor_parent(self) -> None:
		ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
		doc = frappe.get_doc(
			{
				"doctype": "Tender STD Instance",
				"naming_series": "STDINST-.#####",
				"template_version_code": ver,
				"applicability_profile_code": prof,
				"procurement_category": "WORKS",
				"procurement_method": "OPEN_COMPETITIVE_TENDERING",
				"instance_status": "Draft",
				"readiness_status": "Not Ready",
				"created_from_tender_context": 1,
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True)
