# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-05 — TM2 Publication Record (immutable, lineage, TM2-PUB-004 gate).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_tm2_publication_record_p1_05
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.tm2_publication_readiness_service import (
	insert_tm2_publication_readiness_record,
)
from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


class TestTM2PublicationRecordP105(_ReleaseProcurementPackageHandoffFixtures):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for row in frappe.get_all(
			"TM2 Publication Record",
			filters={"tender_code": ["like", "TND-P105%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Publication Record", row):
				frappe.delete_doc("TM2 Publication Record", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Publication Readiness",
			filters={"tender_code": ["like", "TND-P105%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Publication Readiness", row):
				frappe.delete_doc("TM2 Publication Readiness", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender STD Binding",
			filters={"tender_code": ["like", "TND-P105%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Tender STD Binding", row):
				frappe.delete_doc("TM2 Tender STD Binding", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("Tender STD Instance", filters={"tm2_tender": ["like", "TND-P105%"]}, pluck="name"):
			if frappe.db.exists("Tender STD Instance", row):
				frappe.delete_doc("Tender STD Instance", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P105%"]}, pluck="name"):
			if frappe.db.exists("TM2 Tender", row):
				frappe.delete_doc("TM2 Tender", row, force=True, ignore_permissions=True)
		super().tearDown()

	def _mk_tm2(self, plan_name: str, pkg_name: str, *, tender_code: str) -> frappe.model.document.Document:
		return frappe.get_doc(
			{
				"doctype": "TM2 Tender",
				"tender_title": "P105 TM2",
				"tender_code": tender_code,
				"procurement_package": pkg_name,
				"procurement_plan": plan_name,
				"procurement_category": "Goods",
				"tender_visibility": "Public",
			}
		).insert(ignore_permissions=True)

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

	def _mk_binding(self, tm2_name: str, si_name: str) -> frappe.model.document.Document:
		ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
		return frappe.get_doc(
			{
				"doctype": "TM2 Tender STD Binding",
				"tm2_tender": tm2_name,
				"std_template": TEMPLATE_CODE,
				"std_template_code": TEMPLATE_CODE,
				"std_template_version_code": ver,
				"std_applicability_profile_code": prof,
				"tender_std_instance": si_name,
				"is_active": 1,
				"binding_status": "Draft",
				"readiness_status": "Not Assessed",
			}
		).insert(ignore_permissions=True)

	def _fixture_ready_stack(self) -> tuple[
		frappe.model.document.Document,
		frappe.model.document.Document,
		frappe.model.document.Document,
	]:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P105-2028-0001")
		si = self._mk_tm2_std_instance(tm2.name)
		bind = self._mk_binding(tm2.name, si.name)
		insert_tm2_publication_readiness_record(
			tm2.name,
			bind.name,
			readiness_status="Ready",
			std_readiness_status="Ready",
			validation_payload={"ok": True},
			bundle_current=True,
			dsm_current=True,
			dom_current=True,
			dem_current=True,
			dcm_current=True,
		)
		read_name = frappe.db.get_value(
			"TM2 Publication Readiness",
			{"tm2_tender": tm2.name, "validation_run_number": 1},
			"name",
		)
		read = frappe.get_doc("TM2 Publication Readiness", read_name)
		return tm2, bind, read

	def _pub_payload(self, tm2_code: str) -> dict:
		return {
			"tender_code": tm2_code,
			"title": "P105 fixture",
			"bundle_output_code": "GB-P105-V1",
			"publication_snapshot_code": "PUBSNAP-P105-V1",
		}

	def test_p105_insert_codes_and_immutable(self) -> None:
		tm2, bind, read = self._fixture_ready_stack()
		frappe.db.set_value("TM2 Tender", tm2.name, "status", "Approved for Publication")
		pub = frappe.get_doc(
			{
				"doctype": "TM2 Publication Record",
				"tm2_tender": tm2.name,
				"tm2_tender_std_binding": bind.name,
				"tm2_publication_readiness": read.name,
				"bundle_output_code": "GB-P105-V1",
				"bundle_output_hash": "HASH-GB-P105-V1",
				"dsm_output_code": "DSM-P105-V1",
				"dom_output_code": "DOM-P105-V1",
				"dem_output_code": "DEM-P105-V1",
				"dcm_output_code": "DCM-P105-V1",
				"publication_snapshot_code": "PUBSNAP-P105-V1",
				"publication_channel": "Supplier Portal",
				"visibility": "Public",
				"publication_payload_snapshot": self._pub_payload(tm2.tender_code),
				"status": "Published",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(pub.publication_code, f"PUB-{tm2.tender_code}-001")
		self.assertEqual(pub.name, pub.publication_code)
		self.assertEqual(pub.readiness_code, read.readiness_code)
		self.assertEqual(pub.binding_code, bind.binding_code)
		pub.reload()
		pub.bundle_output_code = "GB-TAMPERED"
		with self.assertRaises(frappe.ValidationError):
			pub.save(ignore_permissions=True)

	def test_p105_pub_004_requires_approved_status(self) -> None:
		tm2, bind, read = self._fixture_ready_stack()
		frappe.db.set_value("TM2 Tender", tm2.name, "status", "Draft")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "TM2 Publication Record",
					"tm2_tender": tm2.name,
					"tm2_tender_std_binding": bind.name,
					"tm2_publication_readiness": read.name,
					"bundle_output_code": "GB-P105-V1",
					"dsm_output_code": "DSM-P105-V1",
					"dom_output_code": "DOM-P105-V1",
					"dem_output_code": "DEM-P105-V1",
					"dcm_output_code": "DCM-P105-V1",
					"publication_snapshot_code": "PUBSNAP-P105-V1",
					"publication_channel": "Supplier Portal",
					"visibility": "Public",
					"publication_payload_snapshot": self._pub_payload(tm2.tender_code),
					"status": "Published",
				}
			).insert(ignore_permissions=True)

	def test_p105_second_publication_supersedes_first(self) -> None:
		tm2, bind, read = self._fixture_ready_stack()
		frappe.db.set_value("TM2 Tender", tm2.name, "status", "Approved for Publication")
		common = {
			"doctype": "TM2 Publication Record",
			"tm2_tender": tm2.name,
			"tm2_tender_std_binding": bind.name,
			"tm2_publication_readiness": read.name,
			"bundle_output_code": "GB-P105-V1",
			"dsm_output_code": "DSM-P105-V1",
			"dom_output_code": "DOM-P105-V1",
			"dem_output_code": "DEM-P105-V1",
			"dcm_output_code": "DCM-P105-V1",
			"publication_snapshot_code": "PUBSNAP-P105-V1",
			"publication_channel": "Supplier Portal",
			"visibility": "Public",
			"publication_payload_snapshot": self._pub_payload(tm2.tender_code),
			"status": "Published",
		}
		first = frappe.get_doc(dict(common)).insert(ignore_permissions=True)
		second = frappe.get_doc(dict(common)).insert(ignore_permissions=True)
		self.assertEqual(second.publication_code, f"PUB-{tm2.tender_code}-002")
		first.reload()
		self.assertEqual(first.superseded_by_publication, second.name)

	def test_p105_meta_doc9_fields(self) -> None:
		meta = frappe.get_meta("TM2 Publication Record")
		names = {df.fieldname for df in meta.fields}
		for req in (
			"publication_code",
			"tender_code",
			"binding_code",
			"readiness_code",
			"bundle_output_code",
			"bundle_output_hash",
			"dsm_output_code",
			"dom_output_code",
			"dem_output_code",
			"dcm_output_code",
			"publication_snapshot_code",
			"publication_channel",
			"publication_url",
			"visibility",
			"publication_payload_snapshot",
			"published_by",
			"published_at",
			"status",
		):
			self.assertIn(req, names, msg=f"missing field {req}")
