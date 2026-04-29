from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe

OUTPUT_TYPES = ("Bundle", "DSM", "DOM", "DEM", "DCM")


def _inst(instance: frappe._dict, key: str):
	"""Field access safe for dict or _dict from as_dict()."""
	if isinstance(instance, dict):
		return instance.get(key)
	return instance.get(key)


def build_output_payload(
	output_type: str,
	instance: frappe._dict,
	context: dict[str, Any],
) -> dict[str, Any]:
	"""Build structured payload and optional hashes for STD Generated Output."""
	if output_type == "Bundle":
		return _build_bundle_payload(instance, context)
	if output_type == "DSM":
		return _build_dsm_payload(instance, context)
	if output_type == "DOM":
		return _build_dom_payload(instance, context)
	if output_type == "DEM":
		return _build_dem_payload(instance, context)
	if output_type == "DCM":
		return _build_dcm_payload(instance, context)
	frappe.throw(f"Unsupported output_type: {output_type}")


def _hash_json(payload: dict[str, Any]) -> str:
	raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
	return hashlib.sha256(raw).hexdigest()


def _build_bundle_payload(instance: frappe._dict, context: dict[str, Any]) -> dict[str, Any]:
	"""STD-CURSOR-0602: supplier-facing bundle manifest (no Preface / Appendix to Preface)."""
	version_code = _inst(instance, "template_version_code")
	profile_code = _inst(instance, "profile_code")
	sections = [
		{"id": "issued_page", "title": "Issued page / tender identification", "source_trace": {"type": "instance", "code": _inst(instance, "instance_code")}},
		{"id": "invitation_to_tender", "title": "Invitation to Tender", "source_trace": {"type": "template_version", "code": version_code}},
		{"id": "section_i_itt", "title": "Section I — ITT", "source_trace": {"type": "template_version", "code": version_code}},
		{"id": "section_ii_tds", "title": "Section II — Tender Data Sheet (TDS)", "source_trace": {"type": "parameter_values", "instance_code": _inst(instance, "instance_code")}},
		{"id": "section_iii_evaluation", "title": "Section III — Evaluation and Qualification Criteria", "source_trace": {"type": "template_version", "code": version_code}},
		{"id": "section_iv_forms", "title": "Section IV — Tendering Forms", "source_trace": {"type": "template_version", "code": version_code}},
		{"id": "section_v_boq", "title": "Section V — Bills of Quantities", "source_trace": {"type": "boq_instance", "instance_code": _inst(instance, "instance_code")}},
		{"id": "section_vi_specifications", "title": "Section VI — Specifications", "source_trace": {"type": "section_attachments", "instance_code": _inst(instance, "instance_code")}},
		{"id": "section_vii_drawings", "title": "Section VII — Drawings", "source_trace": {"type": "section_attachments", "instance_code": _inst(instance, "instance_code")}},
		{"id": "section_viii_gcc", "title": "Section VIII — General Conditions of Contract", "source_trace": {"type": "template_version", "code": version_code}},
		{"id": "section_ix_scc", "title": "Section IX — Special Conditions of Contract (SCC)", "source_trace": {"type": "parameter_values", "instance_code": _inst(instance, "instance_code")}},
		{"id": "section_x_contract_forms", "title": "Section X — Contract Forms", "source_trace": {"type": "template_version", "code": version_code}},
		{"id": "supplier_facing_attachments", "title": "Supplier-facing attachments", "source_trace": {"type": "section_attachments", "instance_code": _inst(instance, "instance_code")}},
	]
	addendum_code = context.get("addendum_code")
	if addendum_code:
		sections.append(
			{
				"id": "addendum_references",
				"title": "Addendum references",
				"source_trace": {"type": "addendum", "code": addendum_code},
			}
		)
	excluded_from_supplier_bundle = [
		{"id": "preface", "reason": "Source evidence / configuration guidance; not included in supplier bundle per STD pack."},
		{"id": "appendix_to_preface", "reason": "Source evidence / configuration guidance; not included in supplier bundle per STD pack."},
	]
	payload = {
		"output_type": "Bundle",
		"manifest_version": 1,
		"instance_code": _inst(instance, "instance_code"),
		"template_version_code": version_code,
		"profile_code": profile_code,
		"sections": sections,
		"excluded_from_supplier_bundle": excluded_from_supplier_bundle,
	}
	out_hash = _hash_json(payload)
	return {"payload": payload, "input_hash": context.get("job_input_hash"), "output_hash": out_hash}


def _boq_rows_for_instance(instance_code: str) -> list[dict[str, Any]]:
	if not frappe.db.table_exists("STD BOQ Item Instance"):
		return []
	rows = frappe.db.sql(
		"""
		SELECT ii.item_instance_code, ii.item_number, ii.description, ii.unit, ii.quantity, ii.rate, ii.amount,
			bi.bill_instance_code, bi.bill_number, bi.bill_title
		FROM `tabSTD BOQ Item Instance` ii
		INNER JOIN `tabSTD BOQ Bill Instance` bi ON bi.bill_instance_code = ii.bill_instance_code
		INNER JOIN `tabSTD BOQ Instance` bq ON bq.boq_instance_code = bi.boq_instance_code
		WHERE bq.instance_code = %s
		ORDER BY bi.order_index, ii.item_number
		""",
		(instance_code,),
		as_dict=True,
	)
	return rows or []


def _build_dsm_payload(instance: frappe._dict, context: dict[str, Any]) -> dict[str, Any]:
	"""STD-CURSOR-0603: supplier submission model; BOQ lines are read-only except rate where applicable."""
	boq_items = _boq_rows_for_instance(_inst(instance, "instance_code"))
	boq_dsm = []
	for row in boq_items:
		boq_dsm.append(
			{
				"item_number": {"editable": False, "value": row.get("item_number")},
				"description": {"editable": False, "value": row.get("description")},
				"unit": {"editable": False, "value": row.get("unit")},
				"quantity": {"editable": False, "value": row.get("quantity")},
				"rate": {"editable": True, "value": row.get("rate")},
				"amount": {"editable": False, "computed": True, "value": row.get("amount")},
				"item_type": "priced_boq_line",
			}
		)
	groups = [
		{"group_id": "administrative_forms", "title": "Administrative forms", "source_trace": {"type": "template_version", "code": _inst(instance, "template_version_code")}},
		{"group_id": "declarations", "title": "Declarations", "source_trace": {"type": "template_version", "code": _inst(instance, "template_version_code")}},
		{"group_id": "tender_security", "title": "Tender security / tender-securing declaration", "source_trace": {"type": "template_version", "code": _inst(instance, "template_version_code")}},
		{"group_id": "technical_proposal", "title": "Technical proposal / method statement", "source_trace": {"type": "template_version", "code": _inst(instance, "template_version_code")}},
		{"group_id": "work_programme", "title": "Work programme", "source_trace": {"type": "template_version", "code": _inst(instance, "template_version_code")}},
		{"group_id": "hse_es", "title": "HSE / environmental and social submissions", "source_trace": {"type": "template_version", "code": _inst(instance, "template_version_code")}},
		{"group_id": "qualification_evidence", "title": "Qualification evidence", "source_trace": {"type": "template_version", "code": _inst(instance, "template_version_code")}},
		{"group_id": "financial_capacity", "title": "Financial capacity evidence", "source_trace": {"type": "template_version", "code": _inst(instance, "template_version_code")}},
		{"group_id": "personnel_schedules", "title": "Personnel schedules", "source_trace": {"type": "template_version", "code": _inst(instance, "template_version_code")}},
		{"group_id": "equipment_schedules", "title": "Equipment schedules", "source_trace": {"type": "template_version", "code": _inst(instance, "template_version_code")}},
		{"group_id": "subcontracting_schedules", "title": "Subcontracting schedules", "source_trace": {"type": "template_version", "code": _inst(instance, "template_version_code")}},
		{"group_id": "priced_boq", "title": "Priced BOQ rate-entry requirements", "fields": boq_dsm, "source_trace": {"type": "boq_instance", "instance_code": _inst(instance, "instance_code")}},
		{"group_id": "addendum_acknowledgements", "title": "Addendum acknowledgements", "source_trace": {"type": "addendum_or_none", "code": context.get("addendum_code")}},
	]
	payload = {
		"output_type": "DSM",
		"read_only_model": True,
		"instance_code": _inst(instance, "instance_code"),
		"groups": groups,
	}
	return {"payload": payload, "input_hash": context.get("job_input_hash"), "output_hash": _hash_json(payload)}


def _build_dom_payload(instance: frappe._dict, context: dict[str, Any]) -> dict[str, Any]:
	"""STD-CURSOR-0604: opening register model — opening-time fields only (no evaluation outcomes)."""
	payload = {
		"output_type": "DOM",
		"read_only_model": True,
		"instance_code": _inst(instance, "instance_code"),
		"opening_fields": [
			{"field_key": "supplier_identity", "source_trace": {"type": "itt_tds", "version_code": _inst(instance, "template_version_code")}},
			{"field_key": "bid_submission_timestamp", "source_trace": {"type": "itt_tds", "version_code": _inst(instance, "template_version_code")}},
			{"field_key": "withdrawal_substitution_modification_status", "source_trace": {"type": "itt_tds", "version_code": _inst(instance, "template_version_code")}},
			{"field_key": "tender_price_submitted_boq_total", "source_trace": {"type": "opening_disclosure_rules", "version_code": _inst(instance, "template_version_code")}},
			{"field_key": "discounts", "source_trace": {"type": "itt_tds", "version_code": _inst(instance, "template_version_code")}},
			{"field_key": "alternative_tender_indicator", "source_trace": {"type": "profile", "code": _inst(instance, "profile_code")}},
			{"field_key": "tender_security_presence", "source_trace": {"type": "itt_tds", "version_code": _inst(instance, "template_version_code")}},
			{"field_key": "pages_submitted_count", "source_trace": {"type": "itt_tds", "version_code": _inst(instance, "template_version_code")}},
			{"field_key": "addendum_acknowledgement_status", "source_trace": {"type": "addendum_or_none", "code": context.get("addendum_code")}},
			{"field_key": "opening_date_time_place", "source_trace": {"type": "parameter_values", "instance_code": _inst(instance, "instance_code")}},
		],
		"prohibited_dom_fields": [
			"responsiveness_outcome",
			"qualification_outcome",
			"arithmetic_correction_result",
			"corrected_evaluated_price",
			"ranking",
			"hidden_evaluation_notes",
		],
	}
	return {"payload": payload, "input_hash": context.get("job_input_hash"), "output_hash": _hash_json(payload)}


def _build_dem_payload(instance: frappe._dict, context: dict[str, Any]) -> dict[str, Any]:
	"""STD-CURSOR-0605: evaluation model with mandatory source trace per rule."""
	stages = [
		"Preliminary Responsiveness",
		"Eligibility",
		"Mandatory Administrative Compliance",
		"Tender Security Compliance",
		"Technical Responsiveness",
		"Qualification",
		"Financial Evaluation",
		"Arithmetic Correction",
		"Preference / Reservation",
		"Ranking",
		"Award Recommendation",
	]
	rules = []
	order_index = 0
	for stage in stages:
		order_index += 1
		rules.append(
			{
				"rule_code": f"DEM-{stage[:4].upper()}-{order_index}",
				"stage": stage,
				"source_object_type": "STD Template Version",
				"source_object_code": _inst(instance, "template_version_code"),
				"rule_type": "section_iii_mapped",
				"evaluation_expression_or_reference": f"section_iii::{stage}",
				"outcome_type": "pass_fail",
				"failure_reason_template": f"Failed at {stage}",
				"stops_evaluation": stage in ("Preliminary Responsiveness", "Eligibility"),
				"order_index": order_index,
			}
		)
	qual_rule_index = order_index + 1
	rules.append(
		{
			"rule_code": "DEM-QUAL-FORM-1",
			"stage": "Qualification",
			"source_object_type": "STD Instance",
			"source_object_code": _inst(instance, "instance_code"),
			"rule_type": "qualification_form",
			"evaluation_expression_or_reference": "forms::qualification",
			"outcome_type": "pass_fail",
			"failure_reason_template": "Qualification form criterion not met",
			"stops_evaluation": False,
			"order_index": qual_rule_index,
		}
	)
	boq_rule_index = qual_rule_index + 1
	boq_instance_code = frappe.db.get_value(
		"STD BOQ Instance", {"instance_code": _inst(instance, "instance_code")}, "boq_instance_code"
	)
	if boq_instance_code:
		rules.append(
			{
				"rule_code": "DEM-BOQ-ARITH-1",
				"stage": "Arithmetic Correction",
				"source_object_type": "STD BOQ Instance",
				"source_object_code": boq_instance_code,
				"rule_type": "boq_arithmetic",
				"evaluation_expression_or_reference": "boq::arithmetic_correction",
				"outcome_type": "numeric_adjustment",
				"failure_reason_template": "Arithmetic correction applied",
				"stops_evaluation": False,
				"order_index": boq_rule_index,
			}
		)
	payload = {
		"output_type": "DEM",
		"read_only_model": True,
		"instance_code": _inst(instance, "instance_code"),
		"stages": stages,
		"rules": rules,
		"manual_downstream_criteria": [],
		"note": "No DEM rule without source_object_type and source_object_code.",
	}
	return {"payload": payload, "input_hash": context.get("job_input_hash"), "output_hash": _hash_json(payload)}


def _build_dcm_payload(instance: frappe._dict, context: dict[str, Any]) -> dict[str, Any]:
	"""STD-CURSOR-0606: contract carry-forward; contract price from evaluation/award, not raw BOQ total."""
	payload = {
		"output_type": "DCM",
		"read_only_model": True,
		"instance_code": _inst(instance, "instance_code"),
		"carry_forward": {
			"contract_title": {"source_trace": {"type": "parameter_values", "instance_code": _inst(instance, "instance_code")}},
			"procuring_entity": {"source_trace": {"type": "parameter_values", "instance_code": _inst(instance, "instance_code")}},
			"awarded_supplier_placeholder": {"source_trace": {"type": "award_record", "note": "placeholder until award binding"}},
			"site_location": {"source_trace": {"type": "works_requirements", "instance_code": _inst(instance, "instance_code")}},
			"works_requirements_reference": {"source_trace": {"type": "works_requirements", "instance_code": _inst(instance, "instance_code")}},
			"final_boq_reference": {"source_trace": {"type": "boq_instance", "instance_code": _inst(instance, "instance_code")}},
			"corrected_evaluated_contract_price": {
				"source_rule": "corrected evaluated BOQ total from Evaluation/Award",
				"source_trace": {"type": "evaluation_award", "instance_code": _inst(instance, "instance_code")},
				"disallowed_sources": ["raw_submitted_boq_total", "opening_total", "manual_contract_entry"],
			},
			"completion_period": {"source_trace": {"type": "parameter_values", "instance_code": _inst(instance, "instance_code")}},
			"performance_security": {"source_trace": {"type": "gcc_scc", "version_code": _inst(instance, "template_version_code")}},
			"retention": {"source_trace": {"type": "gcc_scc", "version_code": _inst(instance, "template_version_code")}},
			"defects_liability_period": {"source_trace": {"type": "gcc_scc", "version_code": _inst(instance, "template_version_code")}},
			"payment_terms": {"source_trace": {"type": "gcc_scc", "version_code": _inst(instance, "template_version_code")}},
			"contract_forms": {"source_trace": {"type": "template_version", "code": _inst(instance, "template_version_code")}},
			"scc_values": {"source_trace": {"type": "parameter_values", "instance_code": _inst(instance, "instance_code")}},
			"gcc_source_reference": {"source_trace": {"type": "template_version", "code": _inst(instance, "template_version_code")}},
			"addendum_history": {"source_trace": {"type": "addendum_chain", "instance_code": _inst(instance, "instance_code")}},
		},
	}
	return {"payload": payload, "input_hash": context.get("job_input_hash"), "output_hash": _hash_json(payload)}
