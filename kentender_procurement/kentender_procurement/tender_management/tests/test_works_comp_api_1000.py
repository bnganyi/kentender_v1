# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-1000 — Works completion whitelisted API."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.api import works_completion as works_api
from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.publication_lock import StdPublicationLockService
from kentender_procurement.tender_management.std_instance.state import StdInstanceStateService


class TestWorksCompApi1000(IntegrationTestCase):
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
		doc.tender_title = "WORKS-COMP-1000 Test Tender"
		doc.tender_reference = f"WORKSCOMP1000-{frappe.generate_hash(length=8)}"
		doc.insert(ignore_permissions=True)
		return doc.name

	def _cleanup_tender(self, tender_name: str) -> None:
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"tm2_tender": tender_name},
			pluck="name",
		):
			for snap_name in frappe.get_all(
				"Tender STD Instance Snapshot",
				filters={"tender_std_instance": name},
				pluck="name",
			):
				frappe.delete_doc(
					"Tender STD Instance Snapshot",
					snap_name,
					force=True,
					ignore_permissions=True,
				)
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

	def _minimal_tds_payload(self) -> dict:
		return {
			"tender_title": "WORKS-COMP-1000 Tender",
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

	def test_works_comp_1000_get_completion_status_ok(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			out = works_api.get_works_completion_status(si.name)
			self.assertTrue(out.get("ok"), out)
			self.assertEqual(out.get("code"), "WORKS_COMPLETION_STATUS")
			status = out.get("status") or {}
			self.assertIn("stages", status)
			self.assertIn("overall_status", status)
		finally:
			self._cleanup_tender(tender)

	def test_works_comp_1000_save_tds_values_ok(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			out = works_api.save_works_tds_values(si.name, self._minimal_tds_payload())
			self.assertTrue(out.get("ok"), out)
			self.assertEqual(out.get("code"), "WORKS_TDS_SAVED")
			self.assertTrue((out.get("result") or {}).get("ok"))
		finally:
			self._cleanup_tender(tender)

	def test_works_comp_1000_save_boq_validation_error_envelope(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			out = works_api.save_works_boq(si.name, {"bills": [], "header": {"currency": "USD"}})
			self.assertFalse(out.get("ok"), out)
			code = (out.get("code") or "").strip()
			# Service throws ``ValidationError`` with a human title (not UPPER_SNAKE) → generic API code.
			self.assertEqual(code, "STD_API_VALIDATION_FAILED", msg=str(out))
		finally:
			self._cleanup_tender(tender)

	def test_works_comp_1000_guest_denied_on_mutation(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			frappe.set_user("Guest")
			out = works_api.save_works_tds_values(si.name, self._minimal_tds_payload())
			self.assertFalse(out.get("ok"), out)
			self.assertEqual(out.get("code"), "STD_API_PERMISSION_DENIED")
		finally:
			frappe.set_user("Administrator")
			self._cleanup_tender(tender)

	def test_works_comp_1000_readiness_persist_false_ok_as_admin(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			out = works_api.run_works_readiness(si.name, persist=False)
			self.assertTrue(out.get("ok"), out)
			self.assertEqual(out.get("code"), "WORKS_READINESS_RUN")
			self.assertIn("status", out.get("result") or {})
		finally:
			self._cleanup_tender(tender)

	def test_works_comp_1000_return_to_preparation_api(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			for step in ("In Configuration", "Ready for Publication"):
				StdInstanceStateService.apply_transition(si.name, step, ignore_permissions=True)
			StdPublicationLockService.lock_for_approval(si.name, ignore_permissions=True)
			out = works_api.return_works_instance_to_preparation(si.name)
			self.assertTrue(out.get("ok"), out)
			self.assertEqual(out.get("code"), "WORKS_RETURNED_TO_PREPARATION")
			self.assertEqual((out.get("result") or {}).get("instance_status"), "In Configuration")
		finally:
			self._cleanup_tender(tender)
