# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-1200 — Works completion smoke tests (pack §22).

Maps **WORKS-SMOKE-*** codes to test methods::

	WORKS-SMOKE-TDS-001  → test_works_smoke_tds_001_valid_submission_opening_dates
	WORKS-SMOKE-TDS-002  → test_works_smoke_tds_002_opening_before_submission
	WORKS-SMOKE-TDS-003  → test_works_smoke_tds_003_security_required_amount_missing
	WORKS-SMOKE-REQ-001  → test_works_smoke_req_001_specifications_missing
	WORKS-SMOKE-REQ-002  → test_works_smoke_req_002_drawing_file_missing
	WORKS-SMOKE-REQ-003  → test_works_smoke_req_003_drawing_section_invalid
	WORKS-SMOKE-BOQ-001  → test_works_smoke_boq_001_boq_missing
	WORKS-SMOKE-BOQ-002  → test_works_smoke_boq_002_item_quantity_missing
	WORKS-SMOKE-BOQ-003  → test_works_smoke_boq_003_duplicate_item_number
	WORKS-SMOKE-BOQ-004  → test_works_smoke_boq_004_supplier_rate_denied
	WORKS-SMOKE-SCC-001  → test_works_smoke_scc_001_completion_period_missing
	WORKS-SMOKE-SCC-002  → test_works_smoke_scc_002_ld_cap_invalid
	WORKS-SMOKE-OUT-001  → test_works_smoke_out_001_generate_all_outputs_current
	WORKS-SMOKE-OUT-002  → test_works_smoke_out_002_boq_change_marks_stale
	WORKS-SMOKE-OUT-003  → test_works_smoke_out_003_submission_deadline_change_marks_stale
	WORKS-SMOKE-OUT-004  → test_works_smoke_out_004_manual_evaluation_denied
	WORKS-SMOKE-OUT-005  → test_works_smoke_out_005_dom_arithmetic_correction_denied
	WORKS-SMOKE-READY-001 → test_works_smoke_ready_001_complete_instance_ready
	WORKS-SMOKE-READY-002 → test_works_smoke_ready_002_stale_output_blocked
	WORKS-SMOKE-READY-003 → test_works_smoke_ready_003_missing_dcm_blocked
	WORKS-SMOKE-LOCK-001 → test_works_smoke_lock_001_lock_ready_instance_allowed
	WORKS-SMOKE-LOCK-002 → test_works_smoke_lock_002_edit_locked_instance_denied
	WORKS-SMOKE-LOCK-003 → test_works_smoke_lock_003_edit_published_locked_denied

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_comp_smoke_1200
"""

from __future__ import annotations

import secrets

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
	OUTPUT_TYPES,
	StdInstanceGeneratedOutputService,
)
from kentender_procurement.tender_management.std_instance.parameter import parse_outputs_stale_flags
from kentender_procurement.tender_management.std_instance.publication_lock import StdPublicationLockService
from kentender_procurement.tender_management.works_completion.services.boq_completion import (
	WorksBoqCompletionService,
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


def _tds_base(**overrides: object) -> dict[str, object]:
	p: dict[str, object] = {
		"tender_title": "WORKS-SMOKE-1200 Tender",
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
	p.update(overrides)
	return p


def _minimal_boq_payload() -> dict:
	return {
		"header": {"currency": "USD"},
		"bills": [
			{
				"bill_number": "B1",
				"bill_title": "Preliminaries",
				"bill_type": "Standard",
				"order_index": 0,
				"items": [
					{
						"item_number": "1.1",
						"description": "Site clearance",
						"unit": "m2",
						"quantity": 100,
						"item_type": "Normal",
						"supplier_input_mode": "Rate Only",
					},
				],
			},
		],
	}


def _boq_payload_alt_quantity() -> dict:
	p = _minimal_boq_payload()
	p["bills"][0]["items"][0]["quantity"] = 200
	return p


class TestWorksCompSmoke1200(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _ref(self, tag: str) -> str:
		return f"WKSM1200-{tag}-{secrets.token_hex(4)}"

	def _new_tender(self, tag: str) -> str:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = f"WORKS-COMP-1200 {tag}"
		doc.tender_reference = self._ref(tag)
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

	def _codes(self, out: dict) -> list[str]:
		return [b["code"] for b in out.get("blockers") or []]

	def _bind(self, tender: str):
		return TenderStdBindingService.create_std_instance_for_tm2_tender(
			tender,
			ignore_permissions=True,
			record_template_usage=False,
		)

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

	def _ensure_minimum_boq_std(self, instance_name: str) -> None:
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

	def _full_scc(self) -> dict:
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

	def _drawing_row_ok(self, code: str) -> dict:
		return {
			"drawing_code": code,
			"title": "Plan",
			"revision": "A",
			"file_reference": f"/files/smoke1200/{code}.pdf",
			"section_code": "DRAWINGS",
			"classification": "Supplier Facing",
			"issue_status": "Current",
		}

	def _seed_ready_instance(self, si_name: str) -> None:
		WorksTdsCompletionService.save_tds_values(si_name, _tds_base())
		WorksSccCompletionService.save_scc_values(si_name, self._full_scc())
		WorksRequirementsCompletionService.save_works_requirements(
			si_name,
			{"specifications": {"structured_summary": "WORKS-SMOKE-1200 specification baseline."}},
		)
		self._ensure_minimum_boq_std(si_name)
		WorksDrawingRegisterService.save_drawing_register(
			si_name,
			{"drawings": [self._drawing_row_ok("DWG-SMK")]},
		)
		self._publish_all_outputs(si_name)

	def test_works_smoke_tds_001_valid_submission_opening_dates(self) -> None:
		tender = self._new_tender("TDS001")
		try:
			si = self._bind(tender)
			out = WorksTdsCompletionService.validate_tds_values(si.name, prospective_values=_tds_base())
			self.assertTrue(out["valid"], out)
		finally:
			self._cleanup_tender(tender)

	def test_works_smoke_tds_002_opening_before_submission(self) -> None:
		tender = self._new_tender("TDS002")
		try:
			si = self._bind(tender)
			bad = _tds_base(
				submission_deadline="2026-08-15 17:00:00",
				opening_datetime="2026-08-14 09:00:00",
			)
			out = WorksTdsCompletionService.validate_tds_values(si.name, prospective_values=bad)
			self.assertFalse(out["valid"], out)
			self.assertIn("TDS_OPENING_DATETIME_INVALID", self._codes(out))
		finally:
			self._cleanup_tender(tender)

	def test_works_smoke_tds_003_security_required_amount_missing(self) -> None:
		tender = self._new_tender("TDS003")
		try:
			si = self._bind(tender)
			bad = _tds_base(
				tender_security_required="1",
				tender_security_type="Bid Bond",
				tender_security_amount="",
				tender_security_currency="USD",
			)
			out = WorksTdsCompletionService.validate_tds_values(si.name, prospective_values=bad)
			self.assertFalse(out["valid"], out)
			self.assertIn("TENDER_SECURITY_AMOUNT_MISSING", self._codes(out))
		finally:
			self._cleanup_tender(tender)

	def test_works_smoke_req_001_specifications_missing(self) -> None:
		tender = self._new_tender("REQ001")
		try:
			si = self._bind(tender)
			out = WorksRequirementsCompletionService.validate_works_requirements(si.name)
			self.assertFalse(out["valid"], out)
			self.assertIn("WORKS_SPECIFICATIONS_MISSING", self._codes(out))
		finally:
			self._cleanup_tender(tender)

	def test_works_smoke_req_002_drawing_file_missing(self) -> None:
		tender = self._new_tender("REQ002")
		try:
			si = self._bind(tender)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			doc.append(
				"drawing_register",
				{
					"register_row_code": f"STD-DR-{frappe.generate_hash(length=10)}",
					"drawing_code": "DWG-NOF",
					"title": "No file",
					"revision": "1",
					"file_reference": "",
					"section_code": "DRAWINGS",
					"classification": "Supplier Facing",
					"issue_status": "Current",
				},
			)
			doc.flags.ignore_mandatory = True
			doc.save(ignore_permissions=True)
			out = WorksDrawingRegisterService.validate_drawing_register(si.name)
			self.assertFalse(out["valid"], out)
			self.assertIn("DRAWING_FILE_MISSING", self._codes(out))
		finally:
			self._cleanup_tender(tender)

	def test_works_smoke_req_003_drawing_section_invalid(self) -> None:
		tender = self._new_tender("REQ003")
		try:
			si = self._bind(tender)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			doc.append(
				"drawing_register",
				{
					"register_row_code": f"STD-DR-{frappe.generate_hash(length=10)}",
					"drawing_code": "DWG-X",
					"title": "Plan",
					"revision": "1",
					"file_reference": "/f.pdf",
					"section_code": "SPECIFICATIONS",
					"classification": "Supplier Facing",
					"issue_status": "Current",
				},
			)
			doc.save(ignore_permissions=True)
			out = WorksDrawingRegisterService.validate_drawing_register(si.name)
			self.assertFalse(out["valid"], out)
			self.assertIn("DRAWING_SECTION_INVALID", self._codes(out))
		finally:
			self._cleanup_tender(tender)

	def test_works_smoke_boq_001_boq_missing(self) -> None:
		tender = self._new_tender("BOQ001")
		try:
			si = self._bind(tender)
			out = WorksBoqCompletionService.validate_boq(si.name)
			self.assertFalse(out["valid"], out)
			self.assertIn("BOQ_MISSING", self._codes(out))
		finally:
			self._cleanup_tender(tender)

	def test_works_smoke_boq_002_item_quantity_missing(self) -> None:
		tender = self._new_tender("BOQ002")
		try:
			si = self._bind(tender)
			boq = StdInstanceBoqService.create_boq_for_instance(
				si.name,
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
				"Zero qty",
				"m2",
				0,
				item_type="Normal",
				supplier_input_mode="Rate Only",
				ignore_boq_publication_lock=True,
			)
			out = WorksBoqCompletionService.validate_boq(si.name)
			self.assertFalse(out["valid"], out)
			self.assertIn("BOQ_ITEM_QUANTITY_MISSING", self._codes(out))
		finally:
			self._cleanup_tender(tender)

	def test_works_smoke_boq_003_duplicate_item_number(self) -> None:
		tender = self._new_tender("BOQ003")
		try:
			si = self._bind(tender)
			p = _minimal_boq_payload()
			p["bills"][0]["items"].append(
				{
					"item_number": "1.1",
					"description": "Dup",
					"unit": "m2",
					"quantity": 50,
					"item_type": "Normal",
					"supplier_input_mode": "Rate Only",
				}
			)
			with self.assertRaises(frappe.ValidationError) as ctx:
				WorksBoqCompletionService.save_boq(si.name, p)
			msg = str(ctx.exception)
			self.assertIn("Duplicate item_number", msg)
			self.assertIn("BOQ validation failed", msg)
		finally:
			self._cleanup_tender(tender)

	def test_works_smoke_boq_004_supplier_rate_denied(self) -> None:
		tender = self._new_tender("BOQ004")
		try:
			si = self._bind(tender)
			p = _minimal_boq_payload()
			p["header"]["supplier_rate"] = 99
			with self.assertRaises(frappe.ValidationError):
				WorksBoqCompletionService.save_boq(si.name, p)
		finally:
			self._cleanup_tender(tender)

	def test_works_smoke_scc_001_completion_period_missing(self) -> None:
		tender = self._new_tender("SCC001")
		try:
			si = self._bind(tender)
			out = WorksSccCompletionService.validate_scc_values(si.name)
			self.assertFalse(out["valid"], out)
			self.assertIn("SCC_COMPLETION_PERIOD_MISSING", self._codes(out))
		finally:
			self._cleanup_tender(tender)

	def test_works_smoke_scc_002_ld_cap_invalid(self) -> None:
		tender = self._new_tender("SCC002")
		try:
			si = self._bind(tender)
			prospective = {
				"scc.completion_period_months": "12",
				"scc.defects_liability_period_months": "12",
				"scc.performance_security_required": "0",
				"scc.retention_percentage": "20",
				"scc.liquidated_damages_rate": "0.1% per day",
				"scc.maximum_liquidated_damages_percent": "10",
				"bid_currency": "KES",
				"scc.insurance_requirements": "CAR minimum",
				"scc.advance_payment_allowed": "0",
				"scc.engineer_or_project_manager": "Rep",
				"scc.payment_terms": "Net 30",
				"scc.dispute_resolution_forum": "COURTS",
			}
			out = WorksSccCompletionService.validate_scc_values(si.name, prospective_patch=prospective)
			self.assertFalse(out["valid"], out)
			self.assertIn("SCC_LD_CAP_INVALID", self._codes(out))
		finally:
			self._cleanup_tender(tender)

	def test_works_smoke_out_001_generate_all_outputs_current(self) -> None:
		tender = self._new_tender("OUT001")
		try:
			si = self._bind(tender)
			WorksBoqCompletionService.save_boq(si.name, _minimal_boq_payload())
			out = WorksOutputGenerationService.generate_all_works_outputs(si.name)
			self.assertTrue(out.get("ok"))
			self.assertEqual(set((out.get("outputs") or {}).keys()), set(OUTPUT_TYPES))
			for label, name in (out.get("outputs") or {}).items():
				row = frappe.get_doc("Tender STD Generated Output", name)
				self.assertEqual(row.output_type, label)
				self.assertEqual(row.output_status, "Published")
			inst = frappe.get_doc("Tender STD Instance", si.name)
			flags = parse_outputs_stale_flags(inst)
			for k in OUTPUT_TYPES:
				self.assertNotIn(k, flags)
		finally:
			self._cleanup_tender(tender)

	def test_works_smoke_out_002_boq_change_marks_stale(self) -> None:
		tender = self._new_tender("OUT002")
		try:
			si = self._bind(tender)
			WorksBoqCompletionService.save_boq(si.name, _minimal_boq_payload())
			WorksOutputGenerationService.generate_all_works_outputs(si.name)
			WorksBoqCompletionService.save_boq(si.name, _boq_payload_alt_quantity())
			inst = frappe.get_doc("Tender STD Instance", si.name)
			flags = parse_outputs_stale_flags(inst)
			for k in ("Bundle", "DSM", "DEM", "DCM"):
				self.assertIn(k, flags, msg=f"missing stale flag {k}: {flags}")
		finally:
			self._cleanup_tender(tender)

	def test_works_smoke_out_003_submission_deadline_change_marks_stale(self) -> None:
		tender = self._new_tender("OUT003")
		try:
			si = self._bind(tender)
			WorksBoqCompletionService.save_boq(si.name, _minimal_boq_payload())
			WorksTdsCompletionService.save_tds_values(si.name, _tds_base())
			WorksOutputGenerationService.generate_all_works_outputs(si.name)
			WorksTdsCompletionService.save_tds_values(
				si.name,
				_tds_base(submission_deadline="2026-10-01 12:00:00", opening_datetime="2026-10-02 09:00:00"),
			)
			inst = frappe.get_doc("Tender STD Instance", si.name)
			flags = parse_outputs_stale_flags(inst)
			for k in ("Bundle", "DSM", "DOM"):
				self.assertIn(k, flags, msg=f"missing stale flag {k}: {flags}")
		finally:
			self._cleanup_tender(tender)

	def test_works_smoke_out_004_manual_evaluation_denied(self) -> None:
		tender = self._new_tender("OUT004")
		try:
			si = self._bind(tender)
			with self.assertRaises(frappe.ValidationError) as ctx:
				WorksEvaluationOptionsService.save_evaluation_options(
					si.name,
					{"custom_scoring_rules": {"weight": 99}},
				)
			self.assertIn(DENY_CODE, str(ctx.exception))
		finally:
			self._cleanup_tender(tender)

	def test_works_smoke_out_005_dom_arithmetic_correction_denied(self) -> None:
		tender = self._new_tender("OUT005")
		try:
			si = self._bind(tender)
			p = _minimal_boq_payload()
			p["bills"][0]["items"][0]["arithmetic_correction_amount"] = 100
			with self.assertRaises(frappe.ValidationError) as ctx:
				WorksBoqCompletionService.save_boq(si.name, p)
			msg = str(ctx.exception)
			self.assertTrue(
				"not allowed" in msg.lower() or "supplier rates" in msg.lower() or "arithmetic" in msg.lower(),
				msg=msg,
			)
		finally:
			self._cleanup_tender(tender)

	def test_works_smoke_ready_001_complete_instance_ready(self) -> None:
		tender = self._new_tender("RDY001")
		try:
			si = self._bind(tender)
			self._seed_ready_instance(si.name)
			res = WorksReadinessService.run_works_readiness(si.name, persist=False)
			self.assertEqual(res["status"], "Ready", res)
			self.assertEqual(res.get("blockers"), [])
		finally:
			self._cleanup_tender(tender)

	def test_works_smoke_ready_002_stale_output_blocked(self) -> None:
		tender = self._new_tender("RDY002")
		try:
			si = self._bind(tender)
			self._publish_all_outputs(si.name)
			StdInstanceGeneratedOutputService.mark_output_stale(si.name, output_type="DEM")
			out = WorksReadinessService.run_works_readiness(si.name, persist=False)
			self.assertEqual(out["status"], "Blocked")
			self.assertIn("OUTPUT_STALE", self._codes(out))
		finally:
			self._cleanup_tender(tender)

	def test_works_smoke_ready_003_missing_dcm_blocked(self) -> None:
		tender = self._new_tender("RDY003")
		try:
			si = self._bind(tender)
			for fn in (
				StdInstanceGeneratedOutputService.generate_bundle,
				StdInstanceGeneratedOutputService.generate_dsm,
				StdInstanceGeneratedOutputService.generate_dom,
				StdInstanceGeneratedOutputService.generate_dem,
			):
				o = fn(si.name)
				StdInstanceGeneratedOutputService.publish_output(o.name)
			out = WorksReadinessService.run_works_readiness(si.name, persist=False)
			self.assertEqual(out["status"], "Blocked")
			self.assertIn("DCM_NOT_GENERATED", self._codes(out))
		finally:
			self._cleanup_tender(tender)

	def test_works_smoke_lock_001_lock_ready_instance_allowed(self) -> None:
		tender = self._new_tender("LCK001")
		try:
			si = self._bind(tender)
			self._seed_ready_instance(si.name)
			out = WorksSnapshotLockService.create_configuration_snapshot_and_lock(si.name)
			self.assertTrue(out.get("ok"))
			self.assertEqual(out.get("instance_status"), "Locked for Approval")
			self.assertTrue(out.get("snapshot"))
		finally:
			self._cleanup_tender(tender)

	def test_works_smoke_lock_002_edit_locked_instance_denied(self) -> None:
		tender = self._new_tender("LCK002")
		try:
			si = self._bind(tender)
			self._seed_ready_instance(si.name)
			WorksSnapshotLockService.create_configuration_snapshot_and_lock(si.name)
			with self.assertRaises(frappe.ValidationError):
				StdPublicationLockService.assert_editable(si.name, operation_label="edit")
		finally:
			self._cleanup_tender(tender)

	def test_works_smoke_lock_003_edit_published_locked_denied(self) -> None:
		tender = self._new_tender("LCK003")
		try:
			si = self._bind(tender)
			frappe.db.set_value("Tender STD Instance", si.name, "instance_status", "Published Locked")
			with self.assertRaises(frappe.ValidationError) as ctx:
				WorksTdsCompletionService.save_tds_values(si.name, _tds_base(tender_title="Should not save"))
			msg = str(ctx.exception)
			self.assertIn("Cannot save TDS values", msg)
			self.assertIn("cannot be edited", msg.lower())
		finally:
			self._cleanup_tender(tender)
