# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0900 — Works completion ``WORKS_*`` audit events.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_comp_audit_0900
"""

from __future__ import annotations

import json

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
from kentender_procurement.tender_management.std_instance.parameter import StdInstanceParameterService
from kentender_procurement.tender_management.std_instance.generated_output import (
	StdInstanceGeneratedOutputService,
)
from kentender_procurement.tender_management.works_completion.audit import (
	WORKS_CONFIGURATION_SNAPSHOT_CREATED,
	WORKS_EDIT_DENIED_LOCKED,
	WORKS_EVALUATION_OPTIONS_CHANGED,
	WORKS_LOCKED_FOR_APPROVAL,
	WORKS_MANUAL_CRITERIA_DENIED,
	WORKS_OUTPUTS_GENERATED,
	WORKS_READINESS_BLOCKED,
	WORKS_READINESS_RUN,
	WORKS_RETURNED_TO_PREPARATION,
	WORKS_TDS_VALUES_CHANGED,
)
from kentender_procurement.tender_management.works_completion.services.drawing_register_completion import (
	WorksDrawingRegisterService,
)
from kentender_procurement.tender_management.works_completion.services.evaluation_options_completion import (
	DENY_CODE,
	WorksEvaluationOptionsService,
)
from kentender_procurement.tender_management.works_completion.services.output_generation import (
	WorksOutputGenerationService,
)
from kentender_procurement.tender_management.works_completion.services.scc_completion import (
	WorksSccCompletionService,
)
from kentender_procurement.tender_management.works_completion.services.snapshot_lock import (
	WorksSnapshotLockService,
)
from kentender_procurement.tender_management.works_completion.services.tds_completion import (
	WorksTdsCompletionService,
)
from kentender_procurement.tender_management.works_completion.services.works_readiness import (
	WorksReadinessService,
)
from kentender_procurement.tender_management.works_completion.services.works_requirements_completion import (
	WorksRequirementsCompletionService,
)


def _parse_metadata_row(row: dict) -> dict:
	md = row.get("metadata") or {}
	if isinstance(md, str):
		md = json.loads(md)
	return md if isinstance(md, dict) else {}


class TestWorksCompAudit0900(IntegrationTestCase):
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
		doc.tender_title = "WORKS-COMP-0900 Test Tender"
		doc.tender_reference = f"WORKSCOMP0900-{frappe.generate_hash(length=8)}"
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
			"tender_title": "WORKS-COMP-0900 Tender",
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
			"drawing_code": "DWG-0900",
			"title": "Floor plan",
			"revision": "A",
			"file_reference": "/files/plans/0900.pdf",
			"section_code": "DRAWINGS",
			"classification": "Supplier Facing",
			"issue_status": "Current",
		}

	def _seed_ready_instance(self, si_name: str) -> None:
		WorksTdsCompletionService.save_tds_values(si_name, self._full_tds_payload())
		WorksSccCompletionService.save_scc_values(si_name, self._full_scc_payload())
		WorksRequirementsCompletionService.save_works_requirements(
			si_name,
			{"specifications": {"structured_summary": "WORKS-COMP-0900 specification baseline."}},
		)
		self._ensure_minimum_boq(si_name)
		WorksDrawingRegisterService.save_drawing_register(
			si_name,
			{"drawings": [self._valid_drawing_row()]},
		)
		self._publish_all_outputs(si_name)

	def test_works_comp_0900_tds_save_emits_works_tds_changed(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			base = frappe.db.count(
				"Audit Event",
				{"event_type": WORKS_TDS_VALUES_CHANGED, "document_name": si.name},
			)
			WorksTdsCompletionService.save_tds_values(si.name, self._full_tds_payload())
			after = frappe.db.count(
				"Audit Event",
				{"event_type": WORKS_TDS_VALUES_CHANGED, "document_name": si.name},
			)
			self.assertEqual(after, base + 1)
			rows = frappe.get_all(
				"Audit Event",
				filters={"event_type": WORKS_TDS_VALUES_CHANGED, "document_name": si.name},
				fields=["metadata"],
				order_by="creation desc",
				limit=1,
			)
			meta = _parse_metadata_row(rows[0])
			self.assertIn("tender_code", meta)
			self.assertIn("affected_outputs", meta)
			self.assertIsInstance(meta["affected_outputs"], list)
		finally:
			self._cleanup_tender(tender)

	def test_works_comp_0900_generate_outputs_emits_works_outputs_generated(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			self._seed_ready_instance(si.name)
			base = frappe.db.count(
				"Audit Event",
				{"event_type": WORKS_OUTPUTS_GENERATED, "document_name": si.name},
			)
			WorksOutputGenerationService.generate_all_works_outputs(si.name)
			after = frappe.db.count(
				"Audit Event",
				{"event_type": WORKS_OUTPUTS_GENERATED, "document_name": si.name},
			)
			self.assertEqual(after, base + 1)
			rows = frappe.get_all(
				"Audit Event",
				filters={"event_type": WORKS_OUTPUTS_GENERATED, "document_name": si.name},
				fields=["metadata"],
				order_by="creation desc",
				limit=1,
			)
			meta = _parse_metadata_row(rows[0])
			self.assertEqual(
				sorted(meta.get("affected_outputs") or []),
				["Bundle", "DCM", "DEM", "DOM", "DSM"],
			)
		finally:
			self._cleanup_tender(tender)

	def test_works_comp_0900_readiness_emits_run_and_blocked_when_blocked(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			rb = frappe.db.count(
				"Audit Event",
				{"event_type": WORKS_READINESS_RUN, "document_name": si.name},
			)
			bb = frappe.db.count(
				"Audit Event",
				{"event_type": WORKS_READINESS_BLOCKED, "document_name": si.name},
			)
			out = WorksReadinessService.run_works_readiness(si.name, persist=False)
			self.assertEqual(out["status"], "Blocked")
			self.assertEqual(
				frappe.db.count(
					"Audit Event",
					{"event_type": WORKS_READINESS_RUN, "document_name": si.name},
				),
				rb + 1,
			)
			self.assertEqual(
				frappe.db.count(
					"Audit Event",
					{"event_type": WORKS_READINESS_BLOCKED, "document_name": si.name},
				),
				bb + 1,
			)
		finally:
			self._cleanup_tender(tender)

	def test_works_comp_0900_snapshot_lock_emits_works_snapshot_and_lock(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			self._seed_ready_instance(si.name)
			WorksReadinessService.run_works_readiness(si.name, persist=True)
			cs0 = frappe.db.count(
				"Audit Event",
				{"event_type": WORKS_CONFIGURATION_SNAPSHOT_CREATED, "document_name": si.name},
			)
			lk0 = frappe.db.count(
				"Audit Event",
				{"event_type": WORKS_LOCKED_FOR_APPROVAL, "document_name": si.name},
			)
			WorksSnapshotLockService.create_configuration_snapshot_and_lock(si.name)
			self.assertEqual(
				frappe.db.count(
					"Audit Event",
					{"event_type": WORKS_CONFIGURATION_SNAPSHOT_CREATED, "document_name": si.name},
				),
				cs0 + 1,
			)
			self.assertEqual(
				frappe.db.count(
					"Audit Event",
					{"event_type": WORKS_LOCKED_FOR_APPROVAL, "document_name": si.name},
				),
				lk0 + 1,
			)
		finally:
			self._cleanup_tender(tender)

	def test_works_comp_0900_manual_criteria_denial_emits_works_audit(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			base = frappe.db.count(
				"Audit Event",
				{"event_type": WORKS_MANUAL_CRITERIA_DENIED, "document_name": si.name},
			)
			with self.assertRaises(frappe.ValidationError) as ctx:
				WorksEvaluationOptionsService.save_evaluation_options(
					si.name,
					{"custom_scoring_rules": {"weight": 99}},
				)
			self.assertIn(DENY_CODE, str(ctx.exception))
			self.assertEqual(
				frappe.db.count(
					"Audit Event",
					{"event_type": WORKS_MANUAL_CRITERIA_DENIED, "document_name": si.name},
				),
				base + 1,
			)
		finally:
			self._cleanup_tender(tender)

	def test_works_comp_0900_evaluation_options_save_emits_works_eval_changed(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			base = frappe.db.count(
				"Audit Event",
				{"event_type": WORKS_EVALUATION_OPTIONS_CHANGED, "document_name": si.name},
			)
			WorksEvaluationOptionsService.save_evaluation_options(
				si.name,
				{"key_personnel_required": "1"},
			)
			self.assertEqual(
				frappe.db.count(
					"Audit Event",
					{"event_type": WORKS_EVALUATION_OPTIONS_CHANGED, "document_name": si.name},
				),
				base + 1,
			)
		finally:
			self._cleanup_tender(tender)

	def test_works_comp_0900_works_edit_denied_locked_on_parameter_context_fail(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			ap = (frappe.db.get_value("Tender STD Instance", si.name, "applicability_profile_code") or "").strip()
			frappe.db.set_value("Tender STD Instance", si.name, "applicability_profile_code", ap + "-INVALID")
			base = frappe.db.count(
				"Audit Event",
				{"event_type": WORKS_EDIT_DENIED_LOCKED, "document_name": si.name},
			)
			with self.assertRaises(frappe.ValidationError):
				StdInstanceParameterService.set_parameter_value(si.name, "submission_deadline", "2027-01-01")
			self.assertGreater(
				frappe.db.count(
					"Audit Event",
					{"event_type": WORKS_EDIT_DENIED_LOCKED, "document_name": si.name},
				),
				base,
			)
		finally:
			self._cleanup_tender(tender)

	def test_works_comp_0900_return_to_preparation_emits_audit(self) -> None:
		from kentender_procurement.tender_management.std_instance.publication_lock import StdPublicationLockService
		from kentender_procurement.tender_management.std_instance.state import StdInstanceStateService

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
			base = frappe.db.count(
				"Audit Event",
				{"event_type": WORKS_RETURNED_TO_PREPARATION, "document_name": si.name},
			)
			WorksSnapshotLockService.return_to_preparation_from_approval_lock(si.name)
			self.assertEqual(
				frappe.db.count(
					"Audit Event",
					{"event_type": WORKS_RETURNED_TO_PREPARATION, "document_name": si.name},
				),
				base + 1,
			)
			self.assertEqual(
				(frappe.db.get_value("Tender STD Instance", si.name, "instance_status") or "").strip(),
				"In Configuration",
			)
		finally:
			self._cleanup_tender(tender)
