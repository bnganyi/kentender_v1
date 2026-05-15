# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-1300 — pack §20 ``DERIVED-SMOKE-*`` integration smoke tests.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_derived_smoke_1300
"""

from __future__ import annotations

import copy
import json
import uuid
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.derived_models.addendum.derived_model_impact import (
	DerivedModelImpactService,
)
from kentender_procurement.tender_management.derived_models.common.source_trace import (
	DERIVED_SOURCE_TRACE_MISSING,
	validate_derived_output_source_traces,
)
from kentender_procurement.tender_management.derived_models.consumption.manual_rule_denial import (
	BOQ_ARITHMETIC_CORRECTION_STAGE_VIOLATION,
	CONTRACT_BINDING_VIOLATION,
	MANUAL_EVALUATION_CRITERIA_DENIED,
	ManualRuleDenialService,
	MANUAL_OPENING_EVALUATION_FIELD_DENIED,
	MANUAL_SUBMISSION_REQUIREMENT_DENIED,
)
from kentender_procurement.tender_management.derived_models.consumption.output_consumption import (
	CODE_OUTPUT_TYPE_INVALID_FOR_CONSUMER,
	OutputConsumptionService,
)
from kentender_procurement.tender_management.derived_models.dcm.schema import DCM_SCHEMA_INVALID
from kentender_procurement.tender_management.derived_models.dcm.validator import validate_dcm_source_traces
from kentender_procurement.tender_management.derived_models.dem.generator import DemGenerator
from kentender_procurement.tender_management.derived_models.dsm.schema import DSM_PROHIBITED_KEYS
from kentender_procurement.tender_management.derived_models.events.codes import DERIVED_MODEL_CONSUMED
from kentender_procurement.tender_management.derived_models.orchestration import (
	DerivedModelGenerationService,
)
from kentender_procurement.tender_management.derived_models.seeds.seed_derived_moh_1200 import (
	_ensure_package_by_code,
)
from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.boq import (
	StdInstanceBoqService,
	get_boq_for_instance,
)
from kentender_procurement.tender_management.std_instance.generated_output import (
	StdInstanceGeneratedOutputService,
)
from kentender_procurement.tender_management.std_instance.readiness import StdInstanceReadinessService
from kentender_procurement.tender_management.std_instance.snapshot import StdInstanceSnapshotService
from kentender_procurement.tender_management.works_completion.services.boq_completion import (
	WorksBoqCompletionService,
)

SMOKE_PKG = "PKG-DERIVED-SMOKE-1300"


def _msg_title() -> str:
	log = frappe.get_message_log()
	return (log[-1].get("title") or "").strip() if log else ""


def _as_dict(content_json: object) -> dict:
	if isinstance(content_json, dict):
		return content_json
	if isinstance(content_json, str) and content_json.strip():
		return json.loads(content_json)
	return {}


def _first_prohibited_key(obj: object, forbidden: frozenset[str]) -> str | None:
	if isinstance(obj, dict):
		for k, v in obj.items():
			kn = (k or "").strip()
			if kn in forbidden:
				return kn
			found = _first_prohibited_key(v, forbidden)
			if found:
				return found
	elif isinstance(obj, list):
		for it in obj:
			found = _first_prohibited_key(it, forbidden)
			if found:
				return found
	return None


def _cleanup_tender(tender_name: str) -> None:
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


def _new_tender_and_instance() -> tuple[str, str]:
	_ensure_package_by_code(SMOKE_PKG, "DERIVED-1300 smoke package")
	ref = f"DERIVED-SMOKE-1300-{uuid.uuid4().hex[:10]}"
	doc = frappe.new_doc("Procurement Tender")
	doc.std_template = TEMPLATE_CODE
	doc.tender_title = "DERIVED-1300 smoke"
	doc.tender_reference = ref
	doc.procurement_package = SMOKE_PKG
	doc.insert(ignore_permissions=True)
	si = TenderStdBindingService.create_std_instance_for_tm2_tender(
		doc.name,
		ignore_permissions=True,
		record_template_usage=False,
	)
	return doc.name, si.name


def _mark_current_outputs_stale(instance_name: str, output_types: tuple[str, ...]) -> None:
	"""BOQ stale clears pointers but leaves rows ``Current``; new ``markCurrent`` must not collide."""
	for ot in output_types:
		for name in frappe.get_all(
			"Tender STD Generated Output",
			filters={
				"tender_std_instance": instance_name,
				"output_type": ot,
				"output_status": "Current",
			},
			pluck="name",
		):
			StdInstanceGeneratedOutputService.mark_output_stale(instance_name, output_code=name)


def _minimal_boq() -> dict:
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


class TestDerivedSmoke1300(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		frappe.clear_messages()
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	# --- DSM ---

	def test_derived_smoke_dsm_001_from_complete_instance_current(self) -> None:
		tn, si = _new_tender_and_instance()
		try:
			WorksBoqCompletionService.save_boq(si, _minimal_boq())
			out = DerivedModelGenerationService.generate_output(si, "DSM", publish=False)
			name = (out.get("outputs") or {}).get("DSM")
			self.assertTrue(name)
			st = frappe.db.get_value("Tender STD Generated Output", name, "output_status")
			self.assertEqual(st, "Current")
		finally:
			_cleanup_tender(tn)

	def test_derived_smoke_dsm_002_boq_rate_entry_present(self) -> None:
		tn, si = _new_tender_and_instance()
		try:
			WorksBoqCompletionService.save_boq(si, _minimal_boq())
			d = StdInstanceGeneratedOutputService.generate_dsm(si, ignore_generated_output_lock=True)
			cj = _as_dict(d.content_json)
			reqs = cj.get("requirements") or []
			self.assertTrue(any((r.get("requirement_code") or "") == "DSM-BOQ-RATES" for r in reqs))
			self.assertTrue((cj.get("boq_rate_entry") or {}).get("enabled"))
		finally:
			_cleanup_tender(tn)

	def test_derived_smoke_dsm_003_editable_fields_rate_only(self) -> None:
		tn, si = _new_tender_and_instance()
		try:
			WorksBoqCompletionService.save_boq(si, _minimal_boq())
			d = StdInstanceGeneratedOutputService.generate_dsm(si, ignore_generated_output_lock=True)
			cj = _as_dict(d.content_json)
			br = cj.get("boq_rate_entry") or {}
			self.assertEqual(br.get("editable_fields"), ["rate"])
			self.assertEqual(
				set(br.get("locked_fields") or []),
				{"item_number", "description", "unit", "quantity"},
			)
		finally:
			_cleanup_tender(tn)

	def test_derived_smoke_dsm_004_no_arithmetic_correction(self) -> None:
		tn, si = _new_tender_and_instance()
		try:
			WorksBoqCompletionService.save_boq(si, _minimal_boq())
			d = StdInstanceGeneratedOutputService.generate_dsm(si, ignore_generated_output_lock=True)
			cj = _as_dict(d.content_json)
			self.assertIsNone(cj.get("boq_arithmetic_correction"))
			self.assertIsNone(_first_prohibited_key(cj, DSM_PROHIBITED_KEYS))
		finally:
			_cleanup_tender(tn)

	def test_derived_smoke_dsm_005_manual_submission_requirement_denied(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			ManualRuleDenialService.assert_no_manual_submission_requirement(
				{"manual_submission_requirement": True},
			)
		self.assertEqual(_msg_title(), MANUAL_SUBMISSION_REQUIREMENT_DENIED)

	# --- DOM ---

	def test_derived_smoke_dom_001_from_complete_instance_current(self) -> None:
		tn, si = _new_tender_and_instance()
		try:
			WorksBoqCompletionService.save_boq(si, _minimal_boq())
			out = DerivedModelGenerationService.generate_output(si, "DOM", publish=False)
			name = (out.get("outputs") or {}).get("DOM")
			self.assertTrue(name)
			self.assertEqual(
				frappe.db.get_value("Tender STD Generated Output", name, "output_status"),
				"Current",
			)
		finally:
			_cleanup_tender(tn)

	def test_derived_smoke_dom_002_register_fields_present(self) -> None:
		tn, si = _new_tender_and_instance()
		try:
			WorksBoqCompletionService.save_boq(si, _minimal_boq())
			d = StdInstanceGeneratedOutputService.generate_dom(si, ignore_generated_output_lock=True)
			cj = _as_dict(d.content_json)
			codes = {r.get("field_code") for r in (cj.get("register_fields") or [])}
			self.assertTrue({"bidder_name", "submission_timestamp"} <= codes)
		finally:
			_cleanup_tender(tn)

	def test_derived_smoke_dom_003_no_arithmetic_correction(self) -> None:
		tn, si = _new_tender_and_instance()
		try:
			WorksBoqCompletionService.save_boq(si, _minimal_boq())
			d = StdInstanceGeneratedOutputService.generate_dom(si, ignore_generated_output_lock=True)
			cj = _as_dict(d.content_json)
			raw = json.dumps(cj)
			self.assertNotIn("BOQArithmetic", raw)
			self.assertNotIn("boq_arithmetic_correction", raw)
			ManualRuleDenialService.assert_no_manual_opening_evaluation_field(cj)
		finally:
			_cleanup_tender(tn)

	def test_derived_smoke_dom_004_opening_evaluation_field_denied(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			ManualRuleDenialService.assert_no_manual_opening_evaluation_field(
				{"stages": [{"stage_type": "Financial", "label": "x"}]},
			)
		self.assertEqual(_msg_title(), MANUAL_OPENING_EVALUATION_FIELD_DENIED)

	# --- DEM ---

	def test_derived_smoke_dem_001_from_complete_instance_current(self) -> None:
		tn, si = _new_tender_and_instance()
		try:
			WorksBoqCompletionService.save_boq(si, _minimal_boq())
			out = DerivedModelGenerationService.generate_output(si, "DEM", publish=False)
			name = (out.get("outputs") or {}).get("DEM")
			self.assertTrue(name)
			self.assertEqual(
				frappe.db.get_value("Tender STD Generated Output", name, "output_status"),
				"Current",
			)
		finally:
			_cleanup_tender(tn)

	def test_derived_smoke_dem_002_qualification_thresholds_present(self) -> None:
		tn, si = _new_tender_and_instance()
		try:
			WorksBoqCompletionService.save_boq(si, _minimal_boq())
			d = StdInstanceGeneratedOutputService.generate_dem(si, ignore_generated_output_lock=True)
			cj = _as_dict(d.content_json)
			stages = cj.get("stages") or []
			qual = next((s for s in stages if (s.get("stage_type") or "") == "Qualification"), None)
			self.assertTrue(qual)
			self.assertTrue(isinstance(qual.get("rules"), list) and qual["rules"])
		finally:
			_cleanup_tender(tn)

	def test_derived_smoke_dem_003_boq_arithmetic_correction_present(self) -> None:
		tn, si = _new_tender_and_instance()
		try:
			WorksBoqCompletionService.save_boq(si, _minimal_boq())
			d = StdInstanceGeneratedOutputService.generate_dem(si, ignore_generated_output_lock=True)
			cj = _as_dict(d.content_json)
			bac = cj.get("boq_arithmetic_correction") or {}
			self.assertTrue(bac.get("enabled"))
			self.assertTrue(bac.get("correction_rules"))
		finally:
			_cleanup_tender(tn)

	def test_derived_smoke_dem_004_manual_criteria_denied(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			ManualRuleDenialService.assert_no_manual_evaluation_criteria({"manual_criteria": {"x": 1}})
		self.assertEqual(_msg_title(), MANUAL_EVALUATION_CRITERIA_DENIED)

	def test_derived_smoke_dem_005_rule_without_source_trace_blocked(self) -> None:
		tn, si = _new_tender_and_instance()
		try:
			WorksBoqCompletionService.save_boq(si, _minimal_boq())
			base = DemGenerator.generateDEM(si)
			bad = copy.deepcopy(base)
			stages = bad.get("stages") or []
			if not stages:
				self.fail("expected DEM stages")
			rules = stages[0].setdefault("rules", [])
			rules.append(
				{
					"rule_code": "DEM-BAD-NOTRACE",
					"rule_type": "PresenceCheck",
					"label": "No trace rule",
					"data_source": "DSM",
					"failure_effect": "Reject",
				},
			)
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				validate_derived_output_source_traces("DEM", bad)
			self.assertEqual(_msg_title(), DERIVED_SOURCE_TRACE_MISSING)
		finally:
			_cleanup_tender(tn)

	# --- DCM ---

	def test_derived_smoke_dcm_001_from_complete_instance_current(self) -> None:
		tn, si = _new_tender_and_instance()
		try:
			WorksBoqCompletionService.save_boq(si, _minimal_boq())
			out = DerivedModelGenerationService.generate_output(si, "DCM", publish=False)
			name = (out.get("outputs") or {}).get("DCM")
			self.assertTrue(name)
			self.assertEqual(
				frappe.db.get_value("Tender STD Generated Output", name, "output_status"),
				"Current",
			)
		finally:
			_cleanup_tender(tn)

	def test_derived_smoke_dcm_002_scc_carry_forward_present(self) -> None:
		tn, si = _new_tender_and_instance()
		try:
			WorksBoqCompletionService.save_boq(si, _minimal_boq())
			d = StdInstanceGeneratedOutputService.generate_dcm(si, ignore_generated_output_lock=True)
			cj = _as_dict(d.content_json)
			docs = cj.get("contract_documents") or []
			codes = {(x.get("document_code") or "").strip() for x in docs if isinstance(x, dict)}
			self.assertIn("DCM-SCC", codes)
		finally:
			_cleanup_tender(tn)

	def test_derived_smoke_dcm_003_price_source_corrected_boq_total(self) -> None:
		tn, si = _new_tender_and_instance()
		try:
			WorksBoqCompletionService.save_boq(si, _minimal_boq())
			d = StdInstanceGeneratedOutputService.generate_dcm(si, ignore_generated_output_lock=True)
			cj = _as_dict(d.content_json)
			ps = cj.get("price_source") or {}
			self.assertEqual(ps.get("source_type"), "CorrectedEvaluatedBOQTotal")
			self.assertFalse(ps.get("manual_override_allowed"))
		finally:
			_cleanup_tender(tn)

	def test_derived_smoke_dcm_004_opening_total_as_contract_price_denied(self) -> None:
		tn, si = _new_tender_and_instance()
		try:
			WorksBoqCompletionService.save_boq(si, _minimal_boq())
			base = _as_dict(
				StdInstanceGeneratedOutputService.generate_dcm(si, ignore_generated_output_lock=True).content_json,
			)
			base["opening_submitted_total_as_contract_price"] = True
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				validate_dcm_source_traces(base)
			self.assertEqual(_msg_title(), DCM_SCHEMA_INVALID)
		finally:
			_cleanup_tender(tn)

	def test_derived_smoke_dcm_005_silent_scc_override_denied(self) -> None:
		tn, si = _new_tender_and_instance()
		try:
			WorksBoqCompletionService.save_boq(si, _minimal_boq())
			base = _as_dict(
				StdInstanceGeneratedOutputService.generate_dcm(si, ignore_generated_output_lock=True).content_json,
			)
			base["silent_scc_override"] = {"cap": 99}
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				validate_dcm_source_traces(base)
			self.assertEqual(_msg_title(), DCM_SCHEMA_INVALID)
		finally:
			_cleanup_tender(tn)

	# --- Cross-model ---

	def test_derived_smoke_x_001_publication_snapshot_all_refs(self) -> None:
		tn, si = _new_tender_and_instance()
		try:
			WorksBoqCompletionService.save_boq(si, _minimal_boq())
			DerivedModelGenerationService.generate_all(si, publish=True)
			snap = StdInstanceSnapshotService.create_publication_snapshot(si, "DERIVED-SMOKE-X-001")
			inst = frappe.get_doc("Tender STD Instance", si)
			self.assertEqual(snap.ref_bundle_output, inst.current_bundle_output_code)
			self.assertEqual(snap.ref_dsm_output, inst.current_dsm_output_code)
			self.assertEqual(snap.ref_dom_output, inst.current_dom_output_code)
			self.assertEqual(snap.ref_dem_output, inst.current_dem_output_code)
			self.assertEqual(snap.ref_dcm_output, inst.current_dcm_output_code)
		finally:
			_cleanup_tender(tn)

	def test_derived_smoke_x_002_stale_dem_blocks_readiness(self) -> None:
		tn, si = _new_tender_and_instance()
		try:
			WorksBoqCompletionService.save_boq(si, _minimal_boq())
			DerivedModelGenerationService.generate_all(si, publish=True)
			dem_name = (frappe.db.get_value("Tender STD Instance", si, "current_dem_output_code") or "").strip()
			self.assertTrue(dem_name)
			StdInstanceGeneratedOutputService.mark_output_stale(si, output_code=dem_name)
			res = StdInstanceReadinessService.evaluate(si, persist=False)
			codes = [b.get("code") for b in (res.get("blockers") or [])]
			self.assertIn("STALE_OUTPUTS_PRESENT", codes)
		finally:
			_cleanup_tender(tn)

	def test_derived_smoke_x_003_boq_change_maps_then_regenerates_four_outputs(self) -> None:
		tn, si = _new_tender_and_instance()
		try:
			WorksBoqCompletionService.save_boq(si, _minimal_boq())
			DerivedModelGenerationService.generate_all(si, publish=False)
			boq = get_boq_for_instance(si)
			self.assertTrue(boq and boq.boq_bills)
			bill = boq.boq_bills[0].bill_instance_code
			StdInstanceBoqService.add_item(
				boq.name,
				bill,
				"1.2",
				"Extra line",
				"m",
				5,
				ignore_boq_publication_lock=True,
			)
			imp = DerivedModelImpactService.get_affected_outputs_for_change("boq_quantity_item_change")
			self.assertEqual(set(imp.get("affected_outputs") or []), {"Bundle", "DSM", "DEM", "DCM"})

			_mark_current_outputs_stale(si, ("Bundle", "DSM", "DEM", "DCM"))
			for ot in ("Bundle", "DSM", "DEM", "DCM"):
				DerivedModelGenerationService.generate_output(si, ot, publish=False)
			# ``markCurrent`` does not populate instance parent pointers (only ``publish_output`` does);
			# smoke asserts fresh **Current** rows exist per affected type.
			for ot in ("Bundle", "DSM", "DEM", "DCM"):
				cur_rows = frappe.get_all(
					"Tender STD Generated Output",
					filters={
						"tender_std_instance": si,
						"output_type": ot,
						"output_status": "Current",
					},
					pluck="name",
				)
				self.assertEqual(len(cur_rows), 1, msg=f"expected one Current {ot}")
				st = frappe.db.get_value("Tender STD Generated Output", cur_rows[0], "output_status")
				self.assertEqual(st, "Current")
		finally:
			_cleanup_tender(tn)

	def test_derived_smoke_x_004_prior_versions_retained(self) -> None:
		tn, si = _new_tender_and_instance()
		try:
			WorksBoqCompletionService.save_boq(si, _minimal_boq())
			DerivedModelGenerationService.generate_output(si, "Bundle", publish=True)
			first = (frappe.db.get_value("Tender STD Instance", si, "current_bundle_output_code") or "").strip()
			boq = get_boq_for_instance(si)
			bill = boq.boq_bills[0].bill_instance_code
			StdInstanceBoqService.add_item(
				boq.name,
				bill,
				"9.9",
				"Change BOQ",
				"ea",
				1,
				ignore_boq_publication_lock=True,
			)
			DerivedModelGenerationService.generate_output(si, "Bundle", publish=True)
			second = (frappe.db.get_value("Tender STD Instance", si, "current_bundle_output_code") or "").strip()
			self.assertNotEqual(first, second)
			self.assertEqual(
				frappe.db.get_value("Tender STD Generated Output", first, "output_status"),
				"Superseded",
			)
			self.assertEqual(
				frappe.db.get_value("Tender STD Generated Output", second, "output_status"),
				"Published",
			)
		finally:
			_cleanup_tender(tn)

	def test_derived_smoke_x_005_consumption_audit_carries_version(self) -> None:
		tn, si = _new_tender_and_instance()
		try:
			WorksBoqCompletionService.save_boq(si, _minimal_boq())
			dsm = StdInstanceGeneratedOutputService.generate_dsm(si, ignore_generated_output_lock=True)
			pub = StdInstanceGeneratedOutputService.publish_output(dsm.name)
			v = int(frappe.db.get_value("Tender STD Generated Output", pub.name, "version_number") or 0)
			with patch(
				"kentender_procurement.tender_management.derived_models.consumption.output_consumption.emit_derived_model_audit",
			) as m:
				OutputConsumptionService.record_consumption(pub.name, "Submission", None, "smoke.actor")
			m.assert_called_once()
			args, kwargs = m.call_args
			self.assertEqual(args[0], DERIVED_MODEL_CONSUMED)
			self.assertEqual(kwargs.get("version_number"), v)
		finally:
			_cleanup_tender(tn)

	def test_derived_smoke_x_006_submission_consume_dem_denied(self) -> None:
		tn, si = _new_tender_and_instance()
		try:
			WorksBoqCompletionService.save_boq(si, _minimal_boq())
			dem = StdInstanceGeneratedOutputService.generate_dem(si, ignore_generated_output_lock=True)
			pub = StdInstanceGeneratedOutputService.publish_output(dem.name)
			res = OutputConsumptionService.validate_consumption(pub.name, "Submission", None)
			self.assertFalse(res.get("allowed"))
			self.assertEqual(res["blockers"][0]["code"], CODE_OUTPUT_TYPE_INVALID_FOR_CONSUMER)
		finally:
			_cleanup_tender(tn)

	def test_derived_smoke_x_007_evaluation_consume_dom_denied(self) -> None:
		tn, si = _new_tender_and_instance()
		try:
			WorksBoqCompletionService.save_boq(si, _minimal_boq())
			dom = StdInstanceGeneratedOutputService.generate_dom(si, ignore_generated_output_lock=True)
			pub = StdInstanceGeneratedOutputService.publish_output(dom.name)
			res = OutputConsumptionService.validate_consumption(pub.name, "Evaluation", None)
			self.assertFalse(res.get("allowed"))
			self.assertEqual(res["blockers"][0]["code"], CODE_OUTPUT_TYPE_INVALID_FOR_CONSUMER)
		finally:
			_cleanup_tender(tn)
