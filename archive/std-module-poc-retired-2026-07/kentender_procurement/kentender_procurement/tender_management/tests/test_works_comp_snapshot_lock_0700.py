# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0700 — WorksSnapshotLockService (configuration snapshot + approval lock).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_comp_snapshot_lock_0700
"""

from __future__ import annotations

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
from kentender_procurement.tender_management.std_instance.publication_lock import StdPublicationLockService
from kentender_procurement.tender_management.std_instance.snapshot import StdInstanceSnapshotService
from kentender_procurement.tender_management.works_completion.services.drawing_register_completion import (
	WorksDrawingRegisterService,
)
from kentender_procurement.tender_management.works_completion.services.scc_completion import (
	WorksSccCompletionService,
)
from kentender_procurement.tender_management.works_completion.services.snapshot_lock import (
	WorksSnapshotLockService,
)
from kentender_procurement.tender_management.tests.test_works_comp_tds_completion_0200 import (
	_full_tds_payload,
)
from kentender_procurement.tender_management.works_completion.services.tds_completion import (
	WorksTdsCompletionService,
)
from kentender_procurement.tender_management.works_completion.services.works_requirements_completion import (
	WorksRequirementsCompletionService,
)


class TestWorksCompSnapshotLock0700(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _minimal_tender(self) -> str:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WORKS-COMP-0700 Test Tender"
		doc.tender_reference = "WORKSCOMP0700-REF"
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
		if frappe.db.exists("TM2 Tender", tender_name):
			frappe.delete_doc("TM2 Tender", tender_name, force=True, ignore_permissions=True)

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

	def _full_tds_payload(self) -> dict:
		return {
			"tender_title": "WORKS-COMP-0700 Tender",
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
			"drawing_code": "DWG-0700",
			"title": "Floor plan",
			"revision": "A",
			"file_reference": "/files/plans/0700.pdf",
			"section_code": "DRAWINGS",
			"classification": "Supplier Facing",
			"issue_status": "Current",
		}

	def _seed_ready_instance(self, si_name: str) -> None:
		WorksTdsCompletionService.save_tds_values(si_name, self._full_tds_payload())
		WorksSccCompletionService.save_scc_values(si_name, self._full_scc_payload())
		WorksRequirementsCompletionService.save_works_requirements(
			si_name,
			{"specifications": {"structured_summary": "WORKS-COMP-0700 specification baseline."}},
		)
		self._ensure_minimum_boq(si_name)
		WorksDrawingRegisterService.save_drawing_register(
			si_name,
			{"drawings": [self._valid_drawing_row()]},
		)
		self._publish_all_outputs(si_name)

	def test_works_comp_0700_denies_when_not_ready(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			with self.assertRaises(frappe.ValidationError) as ctx:
				WorksSnapshotLockService.create_configuration_snapshot_and_lock(si.name)
			self.assertIn("WORKS_READINESS_REQUIRED_FOR_LOCK", str(ctx.exception))
		finally:
			self._cleanup_tender(tender)

	def test_works_comp_0700_happy_path_snapshot_then_lock(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			self._seed_ready_instance(si.name)
			out = WorksSnapshotLockService.create_configuration_snapshot_and_lock(si.name)
			self.assertTrue(out.get("ok"))
			self.assertEqual(out.get("instance_status"), "Locked for Approval")
			self.assertTrue(out.get("snapshot"))

			snaps = frappe.get_all(
				"Tender STD Instance Snapshot",
				filters={
					"tender_std_instance": si.name,
					"snapshot_type": "Configuration",
					"snapshot_status": "Final",
				},
				pluck="name",
			)
			self.assertTrue(snaps)
			self.assertIn(out["snapshot"], snaps)

			with self.assertRaises(frappe.ValidationError):
				StdPublicationLockService.assert_editable(si.name, operation_label="edit")
		finally:
			self._cleanup_tender(tender)

	def test_works_comp_0700_readiness_evidence_changes_complete_hash(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			s1 = StdInstanceSnapshotService.create_configuration_snapshot(
				si.name,
				"WORKS-COMP-0700 hash test A",
				readiness_evidence={
					"status": "Blocked",
					"blocker_codes": ["BOQ_MISSING"],
					"warnings": [],
				},
			)
			s2 = StdInstanceSnapshotService.create_configuration_snapshot(
				si.name,
				"WORKS-COMP-0700 hash test B",
				readiness_evidence={
					"status": "Ready",
					"blocker_codes": [],
					"warnings": [],
				},
			)
			self.assertNotEqual(s1.complete_instance_hash, s2.complete_instance_hash)
		finally:
			self._cleanup_tender(tender)

	def test_works_comp_0700_return_to_preparation_unlocks_edits(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			self._seed_ready_instance(si.name)
			WorksSnapshotLockService.create_configuration_snapshot_and_lock(si.name)
			self.assertEqual(
				(frappe.db.get_value("Tender STD Instance", si.name, "instance_status") or "").strip(),
				"Locked for Approval",
			)
			WorksSnapshotLockService.return_to_preparation_from_approval_lock(si.name)
			self.assertEqual(
				(frappe.db.get_value("Tender STD Instance", si.name, "instance_status") or "").strip(),
				"In Configuration",
			)
			WorksTdsCompletionService.save_tds_values(
				si.name,
				_full_tds_payload(
					submission_deadline="2027-12-31 17:00:00",
					opening_datetime="2028-01-15 10:00:00",
					clarification_deadline="2027-12-01 12:00:00",
				),
			)
		finally:
			self._cleanup_tender(tender)
