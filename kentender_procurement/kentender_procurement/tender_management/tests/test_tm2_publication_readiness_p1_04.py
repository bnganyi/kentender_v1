# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-04 — TM2 Publication Readiness DocType + service (immutability TM2-PRD-001, supersede TM2-PRD-002).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_tm2_publication_readiness_p1_04
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


class TestTM2PublicationReadinessP104(_ReleaseProcurementPackageHandoffFixtures):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for row in frappe.get_all(
			"TM2 Publication Readiness",
			filters={"tender_code": ["like", "TND-P104%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Publication Readiness", row):
				frappe.delete_doc("TM2 Publication Readiness", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender STD Binding",
			filters={"tender_code": ["like", "TND-P104%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Tender STD Binding", row):
				frappe.delete_doc("TM2 Tender STD Binding", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("Tender STD Instance", filters={"tm2_tender": ["like", "TND-P104%"]}, pluck="name"):
			if frappe.db.exists("Tender STD Instance", row):
				frappe.delete_doc("Tender STD Instance", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P104%"]}, pluck="name"):
			if frappe.db.exists("TM2 Tender", row):
				frappe.delete_doc("TM2 Tender", row, force=True, ignore_permissions=True)
		super().tearDown()

	def _mk_tm2(self, plan_name: str, pkg_name: str, *, tender_code: str) -> frappe.model.document.Document:
		return frappe.get_doc(
			{
				"doctype": "TM2 Tender",
				"tender_title": "P104 TM2",
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

	def _fixture_tender_and_binding(self) -> tuple[frappe.model.document.Document, frappe.model.document.Document]:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P104-2028-0001")
		si = self._mk_tm2_std_instance(tm2.name)
		bind = self._mk_binding(tm2.name, si.name)
		return tm2, bind

	def test_p104_service_insert_and_codes(self) -> None:
		tm2, bind = self._fixture_tender_and_binding()
		payload = {"blockers": [{"code": "DEM_MISSING_OR_STALE"}]}
		doc = insert_tm2_publication_readiness_record(
			tm2.name,
			bind.name,
			readiness_status="Blocked",
			std_readiness_status="Blocked",
			validation_payload=payload,
			dem_current=False,
		)
		self.assertEqual(doc.readiness_code, f"TRD-{tm2.tender_code}-001")
		self.assertEqual(doc.name, doc.readiness_code)
		self.assertEqual(doc.validation_run_number, 1)
		self.assertEqual(doc.binding_code, bind.binding_code)

	def test_p104_second_run_supersedes_first(self) -> None:
		tm2, bind = self._fixture_tender_and_binding()
		first = insert_tm2_publication_readiness_record(
			tm2.name,
			bind.name,
			readiness_status="Blocked",
			std_readiness_status="Blocked",
			validation_payload={"n": 1},
		)
		second = insert_tm2_publication_readiness_record(
			tm2.name,
			bind.name,
			readiness_status="Ready",
			std_readiness_status="Ready",
			validation_payload={"n": 2},
			bundle_current=True,
			dsm_current=True,
			dom_current=True,
			dem_current=True,
			dcm_current=True,
		)
		self.assertEqual(second.readiness_code, f"TRD-{tm2.tender_code}-002")
		first.reload()
		self.assertEqual(first.superseded_by_readiness, second.name)

	def test_p104_immutable_after_insert(self) -> None:
		tm2, bind = self._fixture_tender_and_binding()
		doc = insert_tm2_publication_readiness_record(
			tm2.name,
			bind.name,
			readiness_status="Blocked",
			std_readiness_status="Blocked",
			validation_payload={"k": "v"},
		)
		doc.reload()
		doc.unresolved_blocker_count = 99
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

	def test_p104_prd_004_ready_requires_service_flag(self) -> None:
		tm2, bind = self._fixture_tender_and_binding()
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "TM2 Publication Readiness",
					"tm2_tender": tm2.name,
					"tm2_tender_std_binding": bind.name,
					"validation_run_number": 1,
					"readiness_status": "Ready",
					"std_readiness_status": "Ready",
					"validation_payload": {},
					"validated_at": frappe.utils.now_datetime(),
				}
			).insert(ignore_permissions=True)

	def test_p104_meta_doc9_core_fields(self) -> None:
		meta = frappe.get_meta("TM2 Publication Readiness")
		names = {df.fieldname for df in meta.fields}
		for req in (
			"readiness_code",
			"tender_code",
			"binding_code",
			"validation_run_number",
			"readiness_status",
			"std_readiness_status",
			"bundle_current",
			"dsm_current",
			"dom_current",
			"dem_current",
			"dcm_current",
			"unresolved_blocker_count",
			"warning_count",
			"validation_payload",
			"validated_at",
		):
			self.assertIn(req, names, msg=f"missing field {req}")
