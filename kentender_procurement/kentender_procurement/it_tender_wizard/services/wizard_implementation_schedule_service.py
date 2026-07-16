# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Implementation Schedule composer step payload for ITW-06."""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.it_tender_wizard.services.wizard_instance_service import _get_instance
from kentender_procurement.it_tender_wizard.services.wizard_overview_service import build_configuration_overview
from kentender_procurement.it_tender_wizard.services.wizard_permission_service import (
	PERM_CREATE,
	PERM_VIEW,
	assert_permission,
)

IMPLEMENTATION_SCHEDULE_STEP_CODE = "IMPLEMENTATION_SCHEDULE"

STATUS_DISPLAY_LABELS = {
	"COMPLETE": "Complete",
	"IN_PROGRESS": "In Progress",
	"INCOMPLETE": "Incomplete",
	"NEEDS_REVIEW": "Needs Review",
}

ACCEPTANCE_LABELS = {
	"CRITERIA_DEFINED": "Criteria Defined",
	"MISSING_CRITERIA": "Missing Criteria",
	"NOT_APPLICABLE": "Not Applicable",
}

SINGLE_TURNKEY_DEFAULTS = {
	"expected_delivery_duration": "6 Months",
	"delivery_trigger": "Contract signing and notice to proceed",
	"key_deliverables": (
		"Fully installed, configured, tested, documented, and handed-over data center hardware solution."
	),
	"unified_acceptance_criteria": (
		"Procuring entity confirms complete delivery, installation, testing, training, documentation, "
		"and handover."
	),
	"evidence_required": "Completion report, test results, training records, and handover certificate.",
	"carry_forward_decision": "YES",
}

SINGLE_TURNKEY_FIELD_MAP = {
	"expected_delivery_duration": "single_turnkey_duration_label",
	"delivery_trigger": "single_turnkey_delivery_trigger",
	"key_deliverables": "single_turnkey_key_deliverables",
	"unified_acceptance_criteria": "single_turnkey_acceptance_criteria",
	"evidence_required": "single_turnkey_evidence_required",
	"carry_forward_decision": "single_turnkey_carry_forward_decision",
}


def _json_list(value: Any) -> list[Any]:
	if value is None or value == "":
		return []
	if isinstance(value, list):
		return value
	if isinstance(value, str):
		try:
			parsed = json.loads(value)
		except (TypeError, ValueError):
			return [value.strip()] if value.strip() else []
		return parsed if isinstance(parsed, list) else [parsed]
	return [value]


def _json_dump(value: Any) -> str:
	if value is None:
		return ""
	if isinstance(value, str):
		return value.strip()
	return json.dumps(value)


def _acceptance_label_for_milestone(row: dict[str, Any] | frappe._dict) -> str:
	if not int(row.get("acceptance_required") or 0):
		return ACCEPTANCE_LABELS["NOT_APPLICABLE"]
	if (row.get("acceptance_criteria_text") or "").strip():
		return ACCEPTANCE_LABELS["CRITERIA_DEFINED"]
	return ACCEPTANCE_LABELS["MISSING_CRITERIA"]


def _phase_acceptance_label(phase: dict[str, Any], milestones: list[dict[str, Any]]) -> str:
	phase_milestones = [row for row in milestones if row.get("phase_code") == phase.get("phase_code")]
	if not phase_milestones:
		return ACCEPTANCE_LABELS["MISSING_CRITERIA"]
	required = [row for row in phase_milestones if int(row.get("acceptance_required") or 0)]
	if not required:
		return (phase.get("acceptance_label") or "").strip() or ACCEPTANCE_LABELS["NOT_APPLICABLE"]
	if all((row.get("acceptance_criteria_text") or "").strip() for row in required):
		return ACCEPTANCE_LABELS["CRITERIA_DEFINED"]
	return ACCEPTANCE_LABELS["MISSING_CRITERIA"]


def _milestone_is_complete(row: dict[str, Any] | frappe._dict) -> bool:
	if not all(
		[
			(row.get("milestone_code") or "").strip(),
			(row.get("milestone_type") or "").strip(),
			(row.get("title") or "").strip(),
			(row.get("phase_code") or "").strip(),
		]
	):
		return False
	if int(row.get("acceptance_required") or 0) and not (row.get("acceptance_criteria_text") or "").strip():
		return False
	return True


def _phase_is_complete(phase: dict[str, Any], milestones: list[dict[str, Any]]) -> bool:
	if not all(
		[
			(phase.get("phase_code") or "").strip(),
			(phase.get("title") or "").strip(),
			(phase.get("duration_label") or "").strip(),
			(phase.get("key_deliverable_summary") or "").strip(),
		]
	):
		return False
	phase_milestones = [row for row in milestones if row.get("phase_code") == phase.get("phase_code")]
	if not phase_milestones:
		return False
	return all(_milestone_is_complete(row) for row in phase_milestones)


def _derive_phase_status(phase: dict[str, Any], milestones: list[dict[str, Any]]) -> str:
	if _phase_is_complete(phase, milestones):
		return "COMPLETE"
	if (phase.get("title") or "").strip() and any(
		row.get("phase_code") == phase.get("phase_code") for row in milestones
	):
		return "IN_PROGRESS"
	return "INCOMPLETE"


def _serialize_milestone(row: dict[str, Any] | frappe._dict) -> dict[str, Any]:
	return {
		"milestone_id": (row.get("milestone_code") or "").strip(),
		"milestone_code": (row.get("milestone_code") or "").strip(),
		"phase_code": (row.get("phase_code") or "").strip(),
		"milestone_type": (row.get("milestone_type") or "").strip(),
		"title": (row.get("title") or "").strip(),
		"display_order": int(row.get("display_order") or 0),
		"deliverables": _json_list(row.get("deliverables_json")),
		"deliverables_json": (row.get("deliverables_json") or "").strip(),
		"acceptance_criteria_text": (row.get("acceptance_criteria_text") or "").strip(),
		"acceptance_label": _acceptance_label_for_milestone(row),
		"evidence_required": _json_list(row.get("evidence_required_json")),
		"evidence_required_json": (row.get("evidence_required_json") or "").strip(),
		"dependency_milestone_codes": _json_list(row.get("dependency_milestone_codes_json")),
		"dependency_milestone_codes_json": (row.get("dependency_milestone_codes_json") or "").strip(),
		"acceptance_required": int(row.get("acceptance_required") or 0),
		"payment_binding_key": (row.get("payment_binding_key") or "").strip(),
		"status": "COMPLETE" if _milestone_is_complete(row) else "INCOMPLETE",
		"status_label": STATUS_DISPLAY_LABELS.get(
			"COMPLETE" if _milestone_is_complete(row) else "INCOMPLETE",
			"Incomplete",
		),
	}


def _template_phase_defaults() -> dict[str, dict[str, str]]:
	phases, _ = _default_seed_phases_milestones(complete=True)
	return {
		(row.get("phase_code") or "").strip(): {
			"duration_label": (row.get("duration_label") or "").strip(),
			"start_trigger": (row.get("start_trigger") or "").strip(),
			"key_deliverable_summary": (row.get("key_deliverable_summary") or "").strip(),
		}
		for row in phases
	}


def _schedule_field_sources(
	phase: dict[str, Any],
	milestones: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
	code = (phase.get("phase_code") or "").strip()
	template = _template_phase_defaults().get(code, {})

	def _editable_source(
		field_key: str,
		*,
		template_key: str | None = None,
		default_type: str,
		default_label: str,
	) -> dict[str, Any]:
		template_key = template_key or field_key
		current = (phase.get(field_key) or "").strip()
		template_value = (template.get(template_key) or current).strip()
		if current == template_value:
			return {
				"source_type": default_type,
				"source_label": default_label,
				"template_value": template_value,
				"editable": True,
				"locked": False,
			}
		return {
			"source_type": "USER_ENTERED",
			"source_label": "User-entered",
			"template_value": template_value,
			"editable": True,
			"locked": False,
		}

	deliverable = (phase.get("key_deliverable_summary") or "").strip()
	template_deliverable = (template.get("key_deliverable_summary") or "").strip()
	if deliverable and deliverable != template_deliverable:
		deliverable_source = {
			"source_type": "USER_ENTERED",
			"source_label": "User-entered",
			"template_value": template_deliverable,
			"editable": True,
			"locked": False,
		}
	else:
		deliverable_source = {
			"source_type": "TEMPLATE",
			"source_label": "Template + user configuration",
			"template_value": template_deliverable,
			"editable": True,
			"locked": False,
		}

	acceptance_milestone = next(
		(row for row in milestones if int(row.get("acceptance_required") or 0)),
		milestones[0] if milestones else None,
	)
	acceptance_text = (acceptance_milestone or {}).get("acceptance_criteria_text") or ""
	acceptance_source = {
		"source_type": "USER_ENTERED" if (acceptance_text or "").strip() else "TEMPLATE",
		"source_label": "User configuration"
		if (acceptance_text or "").strip()
		else "User configuration (template-assisted)",
		"template_value": (acceptance_text or "").strip(),
		"editable": True,
		"locked": False,
	}

	evidence_values = []
	if acceptance_milestone:
		evidence_values = _json_list(acceptance_milestone.get("evidence_required_json"))
	evidence_source = {
		"source_type": "TEMPLATE" if evidence_values else "USER_ENTERED",
		"source_label": "Template + user configuration",
		"template_value": "\n".join(evidence_values),
		"editable": True,
		"locked": False,
	}

	return {
		"phase_code": {
			"source_type": "SYSTEM",
			"source_label": "System-generated phase identifier",
			"template_value": code,
			"editable": False,
			"locked": True,
		},
		"display_order": {
			"source_type": "SYSTEM",
			"source_label": "System-generated sequence number",
			"template_value": str(phase.get("display_order") or ""),
			"editable": False,
			"locked": True,
		},
		"duration_label": _editable_source(
			"duration_label",
			default_type="TEMPLATE",
			default_label="Standard IT Schedule Template",
		),
		"start_trigger": _editable_source(
			"start_trigger",
			default_type="DERIVED",
			default_label="Derived from phase sequence",
		),
		"deliverables": deliverable_source,
		"acceptance_criteria": acceptance_source,
		"evidence_required": evidence_source,
		"carry_forward_to_contract": {
			"source_type": "DEFAULT",
			"source_label": "Schedule defaults (editable)",
			"template_value": "1",
			"editable": True,
			"locked": False,
		},
	}


def _serialize_phase(
	phase: dict[str, Any] | frappe._dict,
	milestones: list[dict[str, Any]],
) -> dict[str, Any]:
	phase_code = (phase.get("phase_code") or "").strip()
	phase_milestones = sorted(
		[_serialize_milestone(row) for row in milestones if row.get("phase_code") == phase_code],
		key=lambda row: row.get("display_order") or 0,
	)
	status = _derive_phase_status(dict(phase), [dict(row) for row in milestones if row.get("phase_code") == phase_code])
	field_sources = _schedule_field_sources(dict(phase), phase_milestones)
	return {
		"phase_id": phase_code,
		"phase_code": phase_code,
		"title": (phase.get("title") or "").strip(),
		"description": (phase.get("description") or "").strip(),
		"display_order": int(phase.get("display_order") or 0),
		"duration_label": (phase.get("duration_label") or "").strip(),
		"start_trigger": (phase.get("start_trigger") or "").strip(),
		"key_deliverable_summary": (phase.get("key_deliverable_summary") or "").strip(),
		"acceptance_label": _phase_acceptance_label(dict(phase), milestones),
		"status": status,
		"status_label": STATUS_DISPLAY_LABELS.get(status, status),
		"requires_acceptance_certificate": int(phase.get("requires_acceptance_certificate") or 0),
		"payment_linked": int(phase.get("payment_linked") or 0),
		"carry_forward_to_contract": int(phase.get("carry_forward_to_contract") or 0),
		"field_sources": field_sources,
		"milestones": phase_milestones,
	}


def compute_schedule_completion(phases: list[dict[str, Any]]) -> dict[str, Any]:
	total_phases = len(phases)
	completed_phases = sum(1 for phase in phases if phase.get("status") == "COMPLETE")
	total_milestones = sum(len(phase.get("milestones") or []) for phase in phases)
	completed_milestones = sum(
		1
		for phase in phases
		for milestone in phase.get("milestones") or []
		if milestone.get("status") == "COMPLETE"
	)
	missing_acceptance = sum(
		1
		for phase in phases
		for milestone in phase.get("milestones") or []
		if milestone.get("acceptance_label") == ACCEPTANCE_LABELS["MISSING_CRITERIA"]
	)
	missing_phase_milestones = sum(
		1 for phase in phases if not (phase.get("milestones") or []) and phase.get("status") != "COMPLETE"
	)
	percent = int(round((completed_phases / total_phases) * 100)) if total_phases else 0
	missing_fields: list[str] = []
	if completed_phases < total_phases:
		missing_fields.append(f"{total_phases - completed_phases} incomplete phase(s)")
	return {
		"completed_phases": completed_phases,
		"total_phases": total_phases,
		"completed_milestones": completed_milestones,
		"total_milestones": total_milestones,
		"missing_fields": missing_fields,
		"percent": percent,
		"gaps": {
			"missing_acceptance_criteria": missing_acceptance,
			"missing_phase_milestones": missing_phase_milestones,
			"incomplete_phases": total_phases - completed_phases,
		},
	}


def _serialize_single_turnkey(doc) -> dict[str, str]:
	return {
		key: (doc.get(fieldname) or SINGLE_TURNKEY_DEFAULTS[key]).strip()
		for key, fieldname in SINGLE_TURNKEY_FIELD_MAP.items()
	}


def _validate_single_turnkey(values: dict[str, Any]) -> None:
	required = {
		"expected_delivery_duration": "Expected delivery duration",
		"delivery_trigger": "Delivery trigger",
		"key_deliverables": "Key deliverables",
		"unified_acceptance_criteria": "Unified acceptance criteria",
		"evidence_required": "Evidence required",
		"carry_forward_decision": "Contract carry-forward decision",
	}
	for fieldname, label in required.items():
		if not str(values.get(fieldname) or "").strip():
			frappe.throw(f"{label} is required for Single Turnkey Delivery.")
	if str(values.get("carry_forward_decision") or "").strip() not in {"YES", "NO"}:
		frappe.throw("Contract carry-forward decision must be Yes or No.")


def _single_turnkey_completion(values: dict[str, Any]) -> dict[str, Any]:
	missing = [
		key
		for key in SINGLE_TURNKEY_FIELD_MAP
		if not str(values.get(key) or "").strip()
	]
	complete = not missing and str(values.get("carry_forward_decision") or "").strip() in {"YES", "NO"}
	return {
		"completed_phases": 1 if complete else 0,
		"total_phases": 1,
		"completed_milestones": 1 if complete else 0,
		"total_milestones": 1,
		"missing_fields": missing,
		"percent": 100 if complete else 0,
		"gaps": {
			"missing_acceptance_criteria": 0
			if str(values.get("unified_acceptance_criteria") or "").strip()
			else 1,
			"missing_phase_milestones": 0,
			"incomplete_phases": 0 if complete else 1,
		},
	}


def _validate_milestone_order(milestones: list[dict[str, Any]]) -> None:
	testing_order = None
	go_live_order = None
	for row in milestones:
		milestone_type = (row.get("milestone_type") or "").strip()
		display_order = int(row.get("display_order") or 0)
		if milestone_type == "TESTING":
			testing_order = display_order if testing_order is None else min(testing_order, display_order)
		if milestone_type == "GO_LIVE":
			go_live_order = display_order if go_live_order is None else max(go_live_order, display_order)
	if testing_order is not None and go_live_order is not None and go_live_order <= testing_order:
		frappe.throw("Go-live cannot precede testing milestones.")


def _validate_acceptance_criteria(milestones: list[dict[str, Any]]) -> None:
	for row in milestones:
		if not int(row.get("acceptance_required") or 0):
			continue
		code = (row.get("milestone_code") or "").strip()
		if not (row.get("acceptance_criteria_text") or "").strip():
			frappe.throw(f"Acceptance criteria are required for milestone {code or '(unknown)'}.")


def _default_milestone(
	*,
	phase_code: str,
	milestone_code: str,
	milestone_type: str,
	title: str,
	display_order: int,
	acceptance_required: bool = False,
	acceptance_criteria_text: str = "",
	deliverables: list[str] | None = None,
	evidence_required: list[str] | None = None,
	dependency_codes: list[str] | None = None,
	payment_binding_key: str = "",
) -> dict[str, Any]:
	return {
		"phase_code": phase_code,
		"milestone_code": milestone_code,
		"milestone_type": milestone_type,
		"title": title,
		"display_order": display_order,
		"deliverables_json": _json_dump(deliverables or []),
		"acceptance_criteria_text": acceptance_criteria_text,
		"evidence_required_json": _json_dump(evidence_required or []),
		"dependency_milestone_codes_json": _json_dump(dependency_codes or []),
		"acceptance_required": 1 if acceptance_required else 0,
		"payment_binding_key": payment_binding_key,
	}


def _default_seed_phases_milestones(*, complete: bool) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
	phases = [
		{
			"phase_code": "PHASE_1",
			"title": "Phase 1 — Foundation and Mobilisation",
			"description": "Project kickoff, requirements confirmation, and core configuration.",
			"display_order": 1,
			"duration_label": "3 Months",
			"start_trigger": "Contract signing and notice to proceed",
			"key_deliverable_summary": "Approved project plan, configured core modules, and signed requirements baseline.",
			"acceptance_label": ACCEPTANCE_LABELS["CRITERIA_DEFINED"],
			"status": "COMPLETE",
			"requires_acceptance_certificate": 1,
			"payment_linked": 1,
			"carry_forward_to_contract": 1,
		},
		{
			"phase_code": "PHASE_2",
			"title": "Phase 2 — Build, Integration, and Testing",
			"description": "Data migration, integration, and formal testing cycles.",
			"display_order": 2,
			"duration_label": "6 Months",
			"start_trigger": "Phase 1 operational acceptance certificate",
			"key_deliverable_summary": "Integrated solution with signed SIT/UAT evidence.",
			"acceptance_label": ACCEPTANCE_LABELS["CRITERIA_DEFINED"],
			"status": "COMPLETE",
			"requires_acceptance_certificate": 1,
			"payment_linked": 1,
			"carry_forward_to_contract": 1,
		},
		{
			"phase_code": "PHASE_3",
			"title": "Phase 3 — Deployment and Operational Acceptance",
			"description": "Production go-live, operational acceptance, and hypercare support.",
			"display_order": 3,
			"duration_label": "9 Months",
			"start_trigger": "Phase 2 UAT sign-off",
			"key_deliverable_summary": "" if not complete else "Production deployment with signed operational acceptance certificate.",
			"acceptance_label": ACCEPTANCE_LABELS["CRITERIA_DEFINED"]
			if complete
			else ACCEPTANCE_LABELS["MISSING_CRITERIA"],
			"status": "COMPLETE" if complete else "IN_PROGRESS",
			"requires_acceptance_certificate": 1,
			"payment_linked": 1,
			"carry_forward_to_contract": 1,
		},
	]
	milestones = [
		_default_milestone(
			phase_code="PHASE_1",
			milestone_code="PH1-KICKOFF",
			milestone_type="KICKOFF",
			title="Project Kickoff",
			display_order=1,
			deliverables=["Signed project charter", "Mobilisation plan"],
		),
		_default_milestone(
			phase_code="PHASE_1",
			milestone_code="PH1-REQ",
			milestone_type="SCOPING_REQUIREMENTS",
			title="Requirements Confirmation",
			display_order=2,
			acceptance_required=True,
			acceptance_criteria_text="Procuring entity signs requirements baseline document.",
			deliverables=["Signed requirements baseline"],
			evidence_required=["Requirements sign-off minutes"],
		),
		_default_milestone(
			phase_code="PHASE_1",
			milestone_code="PH1-CONFIG",
			milestone_type="DESIGN_CONFIGURATION",
			title="Core Configuration Complete",
			display_order=3,
			acceptance_required=True,
			acceptance_criteria_text="Core modules configured and reviewed by technical team.",
			deliverables=["Configured core modules"],
		),
		_default_milestone(
			phase_code="PHASE_2",
			milestone_code="PH2-MIGRATION",
			milestone_type="DATA_MIGRATION",
			title="Data Migration Complete",
			display_order=4,
			deliverables=["Migration reconciliation report"],
		),
		_default_milestone(
			phase_code="PHASE_2",
			milestone_code="PH2-INTEGRATION",
			milestone_type="INTEGRATION",
			title="Integration Complete",
			display_order=5,
			deliverables=["Interface test results"],
		),
		_default_milestone(
			phase_code="PHASE_2",
			milestone_code="PH2-TESTING",
			milestone_type="TESTING",
			title="SIT and UAT Complete",
			display_order=6,
			acceptance_required=True,
			acceptance_criteria_text="Signed UAT report with no open critical defects.",
			deliverables=["UAT report", "Defect closure log"],
			evidence_required=["Signed UAT certificate"],
			dependency_codes=["PH2-INTEGRATION"],
			payment_binding_key="phase_1_uat",
		),
		_default_milestone(
			phase_code="PHASE_3",
			milestone_code="PH3-GOLIVE",
			milestone_type="GO_LIVE",
			title="Production Go-Live",
			display_order=7,
			acceptance_required=True,
			acceptance_criteria_text="Production cutover completed with rollback plan executed successfully."
			if complete
			else "",
			deliverables=["Go-live checklist", "Cutover report"],
			dependency_codes=["PH2-TESTING"],
		),
		_default_milestone(
			phase_code="PHASE_3",
			milestone_code="PH3-OA",
			milestone_type="OPERATIONAL_ACCEPTANCE",
			title="Operational Acceptance Certificate",
			display_order=8,
			acceptance_required=True,
			acceptance_criteria_text="Operational acceptance certificate signed by procuring entity."
			if complete
			else "",
			deliverables=["Signed operational acceptance certificate"],
			evidence_required=["Acceptance certificate"] if complete else [],
			payment_binding_key="operational_acceptance",
		),
		_default_milestone(
			phase_code="PHASE_3",
			milestone_code="PH3-SUPPORT",
			milestone_type="POST_IMPLEMENTATION_SUPPORT",
			title="Hypercare Support Complete",
			display_order=9,
			deliverables=["Hypercare closure report"] if complete else [],
		),
	]
	if not complete:
		phases[2]["key_deliverable_summary"] = ""
		phases[2]["acceptance_label"] = ACCEPTANCE_LABELS["MISSING_CRITERIA"]
	return phases, milestones


def _dedupe_schedule_docs(instance_name: str) -> str | None:
	rows = frappe.get_all(
		"Tender STD Implementation Schedule",
		filters={"tender_std_instance": instance_name},
		fields=["name", "modified"],
		order_by="modified desc",
	)
	if not rows:
		return None
	if len(rows) == 1:
		return rows[0]["name"]
	keeper = rows[0]["name"]
	for row in rows[1:]:
		frappe.delete_doc("Tender STD Implementation Schedule", row["name"], ignore_permissions=True)
	return keeper


def _schedule_doc_name(instance_name: str) -> str | None:
	return _dedupe_schedule_docs(instance_name)


def _ensure_schedule_doc(instance_name: str, *, seed_complete: bool | None = None) -> frappe.model.document.Document:
	name = _schedule_doc_name(instance_name)
	if name:
		return frappe.get_doc("Tender STD Implementation Schedule", name)
	complete = True if seed_complete is None else seed_complete
	phases, milestones = _default_seed_phases_milestones(complete=complete)
	doc = frappe.get_doc(
		{
			"doctype": "Tender STD Implementation Schedule",
			"tender_std_instance": instance_name,
			"implementation_model": "PHASED",
			"selected_phase_code": "PHASE_2",
			"total_duration_label": "18 Months",
			"phases": phases,
			"milestones": milestones,
		}
	)
	try:
		doc.insert(ignore_permissions=True)
	except (frappe.DuplicateEntryError, frappe.UniqueValidationError):
		frappe.db.rollback()
		name = _schedule_doc_name(instance_name)
		if not name:
			raise
		return frappe.get_doc("Tender STD Implementation Schedule", name)
	return doc


def _latest_validation_counts(instance_name: str) -> tuple[int, int]:
	row = frappe.db.get_value(
		"Wizard Progress Snapshot",
		{"tender_std_instance": instance_name},
		["blocking_findings_count", "warning_findings_count"],
		as_dict=True,
		order_by="creation desc",
	)
	if not row:
		return 0, 0
	return int(row.blocking_findings_count or 0), int(row.warning_findings_count or 0)


def _update_step_status(instance_name: str, *, complete: bool) -> None:
	step_name = frappe.db.get_value(
		"Wizard Step Instance",
		{"tender_std_instance": instance_name, "step_code": IMPLEMENTATION_SCHEDULE_STEP_CODE},
	)
	if not step_name:
		return
	status = "COMPLETE" if complete else "IN_PROGRESS"
	frappe.db.set_value("Wizard Step Instance", step_name, "status", status)


def _normalize_milestone_row(row: dict[str, Any]) -> dict[str, Any]:
	normalized = dict(row)
	if "deliverables" in row and "deliverables_json" not in row:
		normalized["deliverables_json"] = _json_dump(row.get("deliverables"))
	if "evidence_required" in row and "evidence_required_json" not in row:
		normalized["evidence_required_json"] = _json_dump(row.get("evidence_required"))
	if "dependency_milestone_codes" in row and "dependency_milestone_codes_json" not in row:
		normalized["dependency_milestone_codes_json"] = _json_dump(row.get("dependency_milestone_codes"))
	return normalized


def _flatten_payload_rows(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
	phases: list[dict[str, Any]] = []
	milestones: list[dict[str, Any]] = []
	for raw_phase in payload.get("phases") or []:
		phase = dict(raw_phase)
		phase_milestones = phase.pop("milestones", None) or []
		phases.append(phase)
		for raw_milestone in phase_milestones:
			milestones.append(_normalize_milestone_row(raw_milestone))
	if payload.get("milestones"):
		for raw_milestone in payload.get("milestones") or []:
			milestones.append(_normalize_milestone_row(raw_milestone))
	return phases, milestones


def _validate_schedule_payload(phases: list[dict[str, Any]], milestones: list[dict[str, Any]]) -> None:
	phase_codes: set[str] = set()
	for phase in phases:
		code = (phase.get("phase_code") or "").strip()
		if not code:
			frappe.throw("Phase code is required for every phase.")
		if code in phase_codes:
			frappe.throw(f"Duplicate phase code: {code}")
		phase_codes.add(code)
	milestone_codes: set[str] = set()
	for row in milestones:
		code = (row.get("milestone_code") or "").strip()
		if not code:
			frappe.throw("Milestone code is required for every milestone.")
		if code in milestone_codes:
			frappe.throw(f"Duplicate milestone code: {code}")
		milestone_codes.add(code)
		phase_code = (row.get("phase_code") or "").strip()
		if phase_code and phase_codes and phase_code not in phase_codes:
			frappe.throw(f"Milestone {code} references unknown phase {phase_code}.")
	_validate_milestone_order(milestones)
	_validate_acceptance_criteria(milestones)


def _apply_schedule_to_doc(
	doc,
	phases: list[dict[str, Any]],
	milestones: list[dict[str, Any]],
) -> None:
	doc.set("phases", [])
	for phase in phases:
		doc.append(
			"phases",
			{
				"phase_code": (phase.get("phase_code") or "").strip(),
				"title": (phase.get("title") or "").strip(),
				"description": (phase.get("description") or "").strip(),
				"display_order": int(phase.get("display_order") or 0),
				"duration_label": (phase.get("duration_label") or "").strip(),
				"start_trigger": (phase.get("start_trigger") or "").strip(),
				"key_deliverable_summary": (phase.get("key_deliverable_summary") or "").strip(),
				"acceptance_label": (phase.get("acceptance_label") or "").strip(),
				"status": (phase.get("status") or "INCOMPLETE").strip(),
				"requires_acceptance_certificate": 1 if phase.get("requires_acceptance_certificate") else 0,
				"payment_linked": 1 if phase.get("payment_linked") else 0,
				"carry_forward_to_contract": 1 if phase.get("carry_forward_to_contract") else 0,
			},
		)
	doc.set("milestones", [])
	for row in milestones:
		normalized = _normalize_milestone_row(row)
		doc.append(
			"milestones",
			{
				"phase_code": (normalized.get("phase_code") or "").strip(),
				"milestone_code": (normalized.get("milestone_code") or "").strip(),
				"milestone_type": (normalized.get("milestone_type") or "").strip(),
				"title": (normalized.get("title") or "").strip(),
				"display_order": int(normalized.get("display_order") or 0),
				"deliverables_json": (normalized.get("deliverables_json") or "").strip(),
				"acceptance_criteria_text": (normalized.get("acceptance_criteria_text") or "").strip(),
				"evidence_required_json": (normalized.get("evidence_required_json") or "").strip(),
				"dependency_milestone_codes_json": (normalized.get("dependency_milestone_codes_json") or "").strip(),
				"acceptance_required": 1 if normalized.get("acceptance_required") else 0,
				"payment_binding_key": (normalized.get("payment_binding_key") or "").strip(),
			},
		)


def _build_payload(configuration_id: str, doc, overview: dict[str, Any]) -> dict[str, Any]:
	raw_phases = [row.as_dict() for row in doc.phases]
	raw_milestones = [row.as_dict() for row in doc.milestones]
	serialized_phases = [
		_serialize_phase(phase, raw_milestones)
		for phase in sorted(raw_phases, key=lambda row: int(row.get("display_order") or 0))
	]
	implementation_model = (doc.implementation_model or "PHASED").strip()
	single_turnkey = _serialize_single_turnkey(doc)
	completion = (
		_single_turnkey_completion(single_turnkey)
		if implementation_model == "SINGLE_TURNKEY"
		else compute_schedule_completion(serialized_phases)
	)
	blockers, warnings = _latest_validation_counts(doc.tender_std_instance)
	selected_phase_code = (doc.selected_phase_code or "").strip() or (
		serialized_phases[0]["phase_code"] if serialized_phases else ""
	)
	tender_number = (
		frappe.db.get_value(
			"Tender STD TDS",
			{"tender_std_instance": doc.tender_std_instance},
			"tender_number",
		)
		or ""
	).strip()
	return {
		"configuration_id": configuration_id,
		"tender_number": tender_number,
		"title": overview.get("title"),
		"state_label": overview.get("state_label"),
		"completion_percent": overview.get("completion_percent"),
		"planning_package": overview.get("planning_package"),
		"procuring_entity": overview.get("procuring_entity"),
		"method": overview.get("method"),
		"validation": {
			"blockers": blockers,
			"warnings": warnings,
		},
		"std_template_version_label": overview.get("std_template_version_label"),
		"std_template_version_id": overview.get("std_template_version_id"),
		"implementation_model": implementation_model,
		"single_turnkey": single_turnkey,
		"selected_phase_id": selected_phase_code,
		"selected_phase_code": selected_phase_code,
		"total_duration_label": (doc.total_duration_label or "").strip(),
		"phases": serialized_phases,
		"completion": completion,
	}


def get_implementation_schedule(configuration_id: str) -> dict[str, Any]:
	assert_permission(PERM_VIEW)
	instance = _get_instance(configuration_id)
	overview = build_configuration_overview(configuration_id)
	doc = _ensure_schedule_doc(instance.name)
	return _build_payload(configuration_id, doc, overview)


def save_implementation_schedule(configuration_id: str, payload: dict[str, Any]) -> dict[str, Any]:
	assert_permission(PERM_CREATE)
	instance = _get_instance(configuration_id)
	doc = _ensure_schedule_doc(instance.name)
	requested_model = (payload.get("implementation_model") or doc.implementation_model or "PHASED").strip()
	if requested_model not in {"PHASED", "SINGLE_TURNKEY"}:
		frappe.throw("Implementation model must be Phased Delivery or Single Turnkey Delivery.")

	if requested_model == "SINGLE_TURNKEY":
		turnkey = _serialize_single_turnkey(doc)
		turnkey.update(
			{
				key: str(value or "").strip()
				for key, value in (payload.get("single_turnkey") or {}).items()
				if key in SINGLE_TURNKEY_FIELD_MAP
			}
		)
		_validate_single_turnkey(turnkey)
		doc.implementation_model = requested_model
		for key, fieldname in SINGLE_TURNKEY_FIELD_MAP.items():
			doc.set(fieldname, turnkey[key])
		doc.save(ignore_permissions=True)
		_update_step_status(instance.name, complete=True)
		return get_implementation_schedule(configuration_id)

	model_only_switch = (
		requested_model == "PHASED"
		and payload.get("implementation_model") == "PHASED"
		and not any(key in payload for key in ("phases", "milestones", "selected_phase"))
	)
	if model_only_switch:
		doc.implementation_model = "PHASED"
		doc.save(ignore_permissions=True)
		phased = _build_payload(
			configuration_id,
			doc,
			build_configuration_overview(configuration_id),
		)
		completion = phased["completion"]
		complete = (
			completion["completed_phases"] == completion["total_phases"]
			and completion["gaps"]["missing_acceptance_criteria"] == 0
			and completion["gaps"]["missing_phase_milestones"] == 0
		)
		_update_step_status(instance.name, complete=complete)
		return phased

	phases = payload.get("phases")
	milestones = payload.get("milestones")
	selected_only = False
	if phases is None and milestones is None:
		selected = payload.get("selected_phase") or {}
		if selected:
			existing_phases = {row.phase_code: row.as_dict() for row in doc.phases}
			existing_milestones = [row.as_dict() for row in doc.milestones]
			code = (selected.get("phase_code") or doc.selected_phase_code or "").strip()
			if code and code in existing_phases:
				selected_copy = dict(selected)
				selected_milestones = selected_copy.pop("milestones", None) or []
				existing_phases[code].update(selected_copy)
				phases = list(existing_phases.values())
				if selected_milestones:
					existing_milestones = [
						row for row in existing_milestones if row.get("phase_code") != code
					]
					for row in selected_milestones:
						existing_milestones.append(_normalize_milestone_row(row))
				milestones = existing_milestones
				selected_only = True
			else:
				phases = [row.as_dict() for row in doc.phases]
				milestones = [row.as_dict() for row in doc.milestones]
		else:
			phases = [row.as_dict() for row in doc.phases]
			milestones = [row.as_dict() for row in doc.milestones]
	else:
		if phases is None:
			phases = [row.as_dict() for row in doc.phases]
		if milestones is None:
			phases, milestones = _flatten_payload_rows({"phases": phases})
		else:
			flat_phases = []
			for raw_phase in phases:
				phase = dict(raw_phase)
				phase.pop("milestones", None)
				flat_phases.append(phase)
			phases = flat_phases
			milestones = [_normalize_milestone_row(row) for row in milestones]
	if payload.get("implementation_model"):
		doc.implementation_model = (payload.get("implementation_model") or "PHASED").strip()
	if payload.get("total_duration_label") is not None:
		doc.total_duration_label = (payload.get("total_duration_label") or "").strip()
	if selected_only:
		code = (payload.get("selected_phase_id") or doc.selected_phase_code or "").strip()
		target_phase = next((row for row in phases if row.get("phase_code") == code), None)
		if target_phase and not (target_phase.get("title") or "").strip():
			frappe.throw(f"Phase {code} requires a title.")
	else:
		_validate_schedule_payload(phases, milestones)
	_apply_schedule_to_doc(doc, phases, milestones)
	if payload.get("selected_phase_id"):
		doc.selected_phase_code = (payload.get("selected_phase_id") or "").strip()
	elif payload.get("selected_phase_code"):
		doc.selected_phase_code = (payload.get("selected_phase_code") or "").strip()
	elif payload.get("selected_phase", {}).get("phase_code"):
		doc.selected_phase_code = (payload["selected_phase"]["phase_code"] or "").strip()
	doc.save(ignore_permissions=True)
	raw_phases = [row.as_dict() for row in doc.phases]
	raw_milestones = [row.as_dict() for row in doc.milestones]
	serialized_phases = [
		_serialize_phase(phase, raw_milestones)
		for phase in sorted(raw_phases, key=lambda row: int(row.get("display_order") or 0))
	]
	completion = compute_schedule_completion(serialized_phases)
	complete = (
		completion["completed_phases"] == completion["total_phases"]
		and completion["gaps"]["missing_acceptance_criteria"] == 0
		and completion["gaps"]["missing_phase_milestones"] == 0
	)
	_update_step_status(instance.name, complete=complete)
	return get_implementation_schedule(configuration_id)
