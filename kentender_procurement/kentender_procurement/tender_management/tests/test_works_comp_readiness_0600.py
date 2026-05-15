# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0600 — WorksReadinessService.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_comp_readiness_0600
"""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.boq import StdInstanceBoqService
from kentender_procurement.tender_management.std_instance.generated_output import (
	StdInstanceGeneratedOutputService,
)
from kentender_procurement.tender_management.works_completion.services.drawing_register_completion import (
	WorksDrawingRegisterService,
)
from kentender_procurement.tender_management.works_completion.services.scc_completion import (
	WorksSccCompletionService,
)
from kentender_procurement.tender_management.works_completion.services.works_requirements_completion import (
	WorksRequirementsCompletionService,
)
from kentender_procurement.tender_management.works_completion.services.tds_completion import (
	WorksTdsCompletionService,
)
from kentender_procurement.tender_management.works_completion.services.works_readiness import (
	WorksReadinessService,
)


class TestWorksCompReadiness0600(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _minimal_tender(self) -> str:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WORKS-COMP-0600 Test Tender"
		doc.tender_reference = "WORKSCOMP0600-REF"
		doc.insert(ignore_permissions=True)
		return doc.name

	def _cleanup_tender(self, tender_name: str) -> None:
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"tm2_tender": tender_name},
			pluck="name",
		):
			for out_name in frappe.get_all(
				"Tender STD Generated Output",
				filters={"tender_std_instance": name},
				pluck="name",
			):
				frappe.delete_doc(
					"Tender STD Generated Output",
					out_name,
					force=True,
					ignore_permissions=True,
				)
			for boq_name in frappe.get_all(
				"Tender STD Instance BOQ",
				filters={"tender_std_instance": name},
				pluck="name",
			):
				frappe.delete_doc(
					"Tender STD Instance BOQ",
					boq_name,
					force=True,
					ignore_permissions=True,
				)
			frappe.delete_doc("Tender STD Instance", name, force=True, ignore_permissions=True)
		if frappe.db.exists("Procurement Tender", tender_name):
			frappe.delete_doc("Procurement Tender", tender_name, force=True, ignore_permissions=True)

	def _publish_all_outputs(self, instance_name: str) -> None:
		for fn in (
			StdInstanceGeneratedOutputService.generate_bundle,
			StdInstanceGeneratedOutputService.generate_dsm,
			StdInstanceGeneratedOutputService.generate_dom,
			StdInstanceGeneratedOutputService.generate_dem,
			StdInstanceGeneratedOutputService.generate_dcm,
		):
			out = fn(instance_name)
			StdInstanceGeneratedOutputService.publish_output(out.name)

	def _ensure_minimum_boq(self, instance_name: str) -> None:
		boq = StdInstanceBoqService.create_boq_for_instance(
			instance_name,
			ignore_boq_publication_lock=True,
		)
		boq = StdInstanceBoqService.add_bill(
			boq.name,
			"1",
			"General",
			"Works",
			ignore_boq_publication_lock=True,
		)
		bill_code = (boq.boq_bills or [])[0].bill_instance_code
		StdInstanceBoqService.add_item(
			boq.name,
			bill_code,
			"1.1",
			"Site mobilization",
			"Item",
			1,
			ignore_boq_publication_lock=True,
		)

	def _codes(self, out: dict) -> list[str]:
		return [b["code"] for b in out.get("blockers") or []]

	def _full_tds_payload(self) -> dict:
		return {
			"tender_title": "WORKS-COMP-0600 Tender",
			"procuring_entity_name": "PE Name",
			"project_location": "Nairobi",
			"procurement_method": "Open National",
			"submission_deadline": "2026-08-15 17:00:00",
			"opening_datetime": "2026-08-16 09:00:00",
			"clarification_deadline": "2026-08-10 12:00:00",
			"bid_validity_days": "120",
			"tender_security_required": "0",
			"tender_security_type": "",
			"tender_security_amount": "",
			"tender_security_currency": "",
			"site_visit_required": "0",
			"site_visit_datetime": "",
			"site_visit_location": "",
			"pre_tender_meeting_required": "0",
			"pre_tender_meeting_datetime": "",
			"pre_tender_meeting_location": "",
			"bid_currency": "KES",
			"language": "en",
			"margin_of_preference_applicable": "0",
		}

	def _full_scc_payload(self) -> dict:
		return {
			"scc.completion_period_months": "12",
			"scc.defects_liability_period_months": "12",
			"scc.performance_security_required": "1",
			"scc.performance_security_percentage": "10",
			"scc.retention_percentage": "10",
			"scc.liquidated_damages_rate": "0.05% per day of delay",
			"scc.advance_payment_allowed": "1",
			"scc.insurance_requirements": "Contractors all risks minimum cover per GCC.",
			"bid_currency": "KES",
			"scc.engineer_or_project_manager": "Employer's Representative",
			"scc.payment_terms": "Interim payments against certified works.",
			"scc.dispute_resolution_forum": "ARBITRATION",
		}

	def _valid_drawing_row(self) -> dict:
		return {
			"drawing_code": "DWG-0600",
			"title": "Floor plan",
			"revision": "A",
			"file_reference": "/files/plans/0600.pdf",
			"section_code": "DRAWINGS",
			"classification": "Supplier Facing",
			"issue_status": "Current",
		}

	def test_works_comp_0600_unknown_instance_blocked(self) -> None:
		out = WorksReadinessService.run_works_readiness("STDINST-NONEXISTENT-0600", persist=False)
		self.assertEqual(out["status"], "Blocked")
		self.assertIn("WORKS_INSTANCE_NOT_FOUND", self._codes(out))

	def test_works_comp_0600_boq_missing_has_pack_fields(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			out = WorksReadinessService.run_works_readiness(si.name, persist=False)
			self.assertEqual(out["status"], "Blocked")
			self.assertIn("BOQ_MISSING", self._codes(out))
			for b in out["blockers"]:
				if b["code"] == "BOQ_MISSING":
					self.assertIn("severity", b)
					self.assertIn("resolution_action", b)
					self.assertTrue(str(b["resolution_action"]).strip())
					break
			else:
				self.fail("BOQ_MISSING blocker not found")
		finally:
			self._cleanup_tender(tender)

	def test_works_comp_0600_stale_maps_to_output_stale(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			self._publish_all_outputs(si.name)
			StdInstanceGeneratedOutputService.mark_output_stale(si.name, output_type="DEM")
			out = WorksReadinessService.run_works_readiness(si.name, persist=False)
			self.assertEqual(out["status"], "Blocked")
			self.assertIn("OUTPUT_STALE", self._codes(out))
		finally:
			self._cleanup_tender(tender)

	def test_works_comp_0600_missing_dcm_not_generated(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			for fn in (
				StdInstanceGeneratedOutputService.generate_bundle,
				StdInstanceGeneratedOutputService.generate_dsm,
				StdInstanceGeneratedOutputService.generate_dom,
				StdInstanceGeneratedOutputService.generate_dem,
			):
				out = fn(si.name)
				StdInstanceGeneratedOutputService.publish_output(out.name)
			out = WorksReadinessService.run_works_readiness(si.name, persist=False)
			self.assertEqual(out["status"], "Blocked")
			self.assertIn("DCM_NOT_GENERATED", self._codes(out))
		finally:
			self._cleanup_tender(tender)

	def test_works_comp_0600_ready_persist_matches_doc(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksTdsCompletionService.save_tds_values(si.name, self._full_tds_payload())
			WorksSccCompletionService.save_scc_values(si.name, self._full_scc_payload())
			WorksRequirementsCompletionService.save_works_requirements(
				si.name,
				{"specifications": {"structured_summary": "WORKS-COMP-0600 specification baseline."}},
			)
			self._ensure_minimum_boq(si.name)
			WorksDrawingRegisterService.save_drawing_register(
				si.name,
				{"drawings": [self._valid_drawing_row()]},
			)
			self._publish_all_outputs(si.name)

			res = WorksReadinessService.run_works_readiness(si.name, persist=True)
			self.assertEqual(res["status"], "Ready", res)
			self.assertEqual(res["blockers"], [])
			inst = frappe.get_doc("Tender STD Instance", si.name)
			self.assertEqual((inst.readiness_status or "").strip(), "Ready")
		finally:
			self._cleanup_tender(tender)

	def test_works_comp_0600_failed_output_bundle_render_failed(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksTdsCompletionService.save_tds_values(si.name, self._full_tds_payload())
			WorksSccCompletionService.save_scc_values(si.name, self._full_scc_payload())
			WorksRequirementsCompletionService.save_works_requirements(
				si.name,
				{"specifications": {"structured_summary": "WORKS-COMP-0600 fail-test specifications."}},
			)
			self._ensure_minimum_boq(si.name)
			WorksDrawingRegisterService.save_drawing_register(
				si.name,
				{"drawings": [self._valid_drawing_row()]},
			)
			self._publish_all_outputs(si.name)

			dem_name = frappe.db.get_value("Tender STD Instance", si.name, "current_dem_output_code")
			self.assertTrue(dem_name)
			# Published→Failed is blocked by DB trigger STDINST-1300; simulate Failed for reads only.
			_orig_gv = frappe.db.get_value

			def _patched_get_value(doctype, name, fieldname=None, *args, **kwargs):
				if (
					doctype == "Tender STD Generated Output"
					and name == dem_name
					and fieldname == "output_status"
				):
					return "Failed"
				return _orig_gv(doctype, name, fieldname, *args, **kwargs)

			with patch.object(frappe.db, "get_value", side_effect=_patched_get_value):
				out = WorksReadinessService.run_works_readiness(si.name, persist=False)
			self.assertEqual(out["status"], "Blocked")
			codes = self._codes(out)
			self.assertIn("BUNDLE_RENDER_FAILED", codes)
			self.assertIn("DEM_NOT_GENERATED", codes)
			for b in out["blockers"]:
				if b["code"] == "BUNDLE_RENDER_FAILED":
					self.assertIn("Failed", b["message"])
					break
			else:
				self.fail("BUNDLE_RENDER_FAILED missing")
		finally:
			self._cleanup_tender(tender)
