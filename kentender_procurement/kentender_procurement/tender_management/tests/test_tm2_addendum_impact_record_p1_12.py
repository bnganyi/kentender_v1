# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-12 — TM2 Addendum Impact Record (AIR-* codes, TM2-AIR-002, TM2-ADD-003 wiring).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_tm2_addendum_impact_record_p1_12
"""

from __future__ import annotations

import frappe

from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


class TestTM2AddendumImpactRecordP112(_ReleaseProcurementPackageHandoffFixtures):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		self._supplier_names: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for row in frappe.get_all(
			"TM2 Addendum Impact Record",
			filters={"tender_code": ["like", "TND-P112%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Addendum Impact Record", row):
				frappe.delete_doc("TM2 Addendum Impact Record", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Addendum",
			filters={"tender_code": ["like", "TND-P112%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Addendum", row):
				frappe.delete_doc("TM2 Addendum", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Clarification Request",
			filters={"tender_code": ["like", "TND-P112%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Clarification Request", row):
				frappe.delete_doc("TM2 Clarification Request", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Supplier Participation",
			filters={"tender_code": ["like", "TND-P112%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Supplier Participation", row):
				frappe.delete_doc("TM2 Supplier Participation", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender Timeline", filters={"tender_code": ["like", "TND-P112%"]}, pluck="name"
		):
			if frappe.db.exists("TM2 Tender Timeline", row):
				frappe.delete_doc("TM2 Tender Timeline", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P112%"]}, pluck="name"):
			if frappe.db.exists("TM2 Tender", row):
				frappe.delete_doc("TM2 Tender", row, force=True, ignore_permissions=True)
		for sn in self._supplier_names:
			if frappe.db.exists("Supplier", sn):
				frappe.delete_doc("Supplier", sn, force=True, ignore_permissions=True)
		super().tearDown()

	def _supplier_group(self) -> str:
		sg = frappe.db.get_value(
			"Supplier Group",
			{"is_group": 0},
			"name",
			order_by="lft asc",
		)
		if not sg:
			sg = frappe.db.get_value("Supplier Group", {}, "name")
		if not sg:
			frappe.throw("No Supplier Group for P1-12 Supplier fixture")
		return sg

	def _ensure_supplier(self, label: str) -> str:
		supplier_name = f"P112 {label} Supplier"
		existing = frappe.db.get_value("Supplier", {"supplier_name": supplier_name}, "name")
		if existing:
			self._supplier_names.append(existing)
			return existing
		doc = frappe.get_doc(
			{
				"doctype": "Supplier",
				"naming_series": "SUP-.YYYY.-",
				"supplier_name": supplier_name,
				"supplier_type": "Company",
				"supplier_group": self._supplier_group(),
			}
		).insert(ignore_permissions=True)
		self._supplier_names.append(doc.name)
		return doc.name

	def _mk_tm2(self, plan_name: str, pkg_name: str, *, tender_code: str) -> frappe.model.document.Document:
		return frappe.get_doc(
			{
				"doctype": "TM2 Tender",
				"tender_title": "P112 TM2",
				"tender_code": tender_code,
				"procurement_package": pkg_name,
				"procurement_plan": plan_name,
				"procurement_category": "Goods",
				"tender_visibility": "Public",
			}
		).insert(ignore_permissions=True)

	def _published_tm2_and_addendum(self, *, tender_code: str = "TND-P112-2028-0001"):
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code=tender_code)
		tm2.status = "Published"
		tm2.flags.ignore_tm2_tender_governed_status_mutation = True
		tm2.save(ignore_permissions=True)
		ad = frappe.get_doc(
			{
				"doctype": "TM2 Addendum",
				"tm2_tender": tm2.name,
				"title": "Fixture addendum",
				"reason": "Fixture reason for impact tests.",
			}
		).insert(ignore_permissions=True)
		return tm2, ad

	def _mk_impact(self, ad_name: str, **kwargs) -> frappe.model.document.Document:
		payload = kwargs.pop("impact_payload", {"fixture": True})
		row = {
			"doctype": "TM2 Addendum Impact Record",
			"tm2_addendum": ad_name,
			"std_impact_analysis_code": kwargs.pop("std_impact_analysis_code", "STD-IMP-P112-001"),
			"impact_payload": payload,
			**kwargs,
		}
		return frappe.get_doc(row).insert(ignore_permissions=True)

	def test_p112_impact_code_and_prev_revised_refs(self) -> None:
		tm2, ad = self._published_tm2_and_addendum()
		impact = self._mk_impact(
			ad.name,
			previous_bundle_output_code="GB-V1",
			revised_bundle_output_code="GB-V2",
			previous_publication_snapshot_code="PUBSNAP-V1",
			revised_publication_snapshot_code="PUBSNAP-V2",
		)
		self.assertEqual(impact.impact_record_code, f"AIR-{ad.addendum_code}")
		self.assertEqual(impact.name, impact.impact_record_code)
		self.assertEqual(impact.tender_code, tm2.tender_code)
		self.assertEqual(impact.addendum_code, ad.addendum_code)

	def test_p112_only_one_impact_per_addendum(self) -> None:
		tm2, ad = self._published_tm2_and_addendum(tender_code="TND-P112-2028-0002")
		self._mk_impact(ad.name)
		with self.assertRaises(frappe.ValidationError):
			self._mk_impact(ad.name)

	def test_p112_air_002_immutable_after_addendum_issued(self) -> None:
		tm2, ad = self._published_tm2_and_addendum(tender_code="TND-P112-2028-0003")
		impact = self._mk_impact(ad.name)
		ad.reload()
		ad.status = "Issued"
		ad.save(ignore_permissions=True)
		impact.reload()
		impact.revised_bundle_output_code = "SHOULD-NOT-STICK"
		with self.assertRaises(frappe.ValidationError):
			impact.save(ignore_permissions=True)

	def test_p112_add_003_structural_requires_impact_row(self) -> None:
		tm2, ad = self._published_tm2_and_addendum(tender_code="TND-P112-2028-0004")
		ad.reload()
		ad.primary_impact_type = "BOQ Change"
		ad.status = "Pending Approval"
		with self.assertRaises(frappe.ValidationError):
			ad.save(ignore_permissions=True)
		self._mk_impact(ad.name)
		ad.reload()
		ad.primary_impact_type = "BOQ Change"
		ad.status = "Pending Approval"
		ad.save(ignore_permissions=True)

	def test_p112_meta_doc9_fields(self) -> None:
		meta = frappe.get_meta("TM2 Addendum Impact Record")
		names = {df.fieldname for df in meta.fields}
		for req in (
			"impact_record_code",
			"tm2_addendum",
			"addendum_code",
			"tm2_tender",
			"tender_code",
			"std_impact_analysis_code",
			"affected_parameter_refs",
			"affected_section_refs",
			"affected_boq_refs",
			"previous_bundle_output_code",
			"revised_bundle_output_code",
			"previous_dsm_output_code",
			"revised_dsm_output_code",
			"previous_dom_output_code",
			"revised_dom_output_code",
			"previous_dem_output_code",
			"revised_dem_output_code",
			"previous_dcm_output_code",
			"revised_dcm_output_code",
			"previous_publication_snapshot_code",
			"revised_publication_snapshot_code",
			"deadline_extension_required",
			"supplier_acknowledgement_required",
			"bid_resubmission_required",
			"impact_payload",
			"created_at",
		):
			self.assertIn(req, names, msg=f"missing field {req}")
