# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""IT Requirements composer step payload for ITW-05 / ITW-05-R1."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.it_tender_wizard.services.wizard_instance_service import _get_instance
from kentender_procurement.it_tender_wizard.services.wizard_overview_service import build_configuration_overview
from kentender_procurement.it_tender_wizard.services.wizard_permission_service import (
	PERM_CREATE,
	PERM_VIEW,
	assert_permission,
)

IT_REQUIREMENTS_STEP_CODE = "IT_REQUIREMENTS"

FORBIDDEN_DISPLAY_LABELS = (
	"Evidence Set",
	"Acceptance Set",
	"Scored (15%)",
)

SECTION_META: dict[str, str] = {
	"technical_3_0": "3.0 Technical Requirements",
	"security_4_0": "4.0 Security & Compliance",
	"functional_2_0": "2.0 Functional Requirements",
	"service_5_0": "5.0 Service Requirements",
}

TREATMENT_TO_PRIORITY = {
	"Mandatory": "MANDATORY",
	"Evaluation-linked": "SCORED",
	"Informational": "INFORMATIONAL",
}

PRIORITY_TO_TREATMENT = {
	"MANDATORY": "Mandatory",
	"SCORED": "Evaluation-linked",
	"DESIRABLE": "Informational",
	"INFORMATIONAL": "Informational",
}

TYPE_TO_CATEGORY = {
	"ARCHITECTURAL": "Hardware",
	"PERFORMANCE": "Hardware",
	"FUNCTIONAL": "Software",
	"SECURITY": "Security",
	"SERVICE": "Support",
}

RESPONSE_FORMAT_LABELS = {
	"YES_NO": "Yes/No",
	"NUMERIC": "Numeric Value",
	"DOCUMENT_EVIDENCE": "Document Upload",
	"NARRATIVE": "Narrative",
	"COMPLIANCE_MATRIX": "Compliance Matrix",
	"UPLOAD": "Document Upload",
	"NOT_REQUIRED": "Not Required",
}

RESPONSE_FORMAT_REVERSE = {
	"Yes/No": "YES_NO",
	"Numeric Value": "NUMERIC",
	"Numeric": "NUMERIC",
	"Document Upload": "DOCUMENT_EVIDENCE",
	"Upload": "UPLOAD",
	"Narrative": "NARRATIVE",
	"Compliance Matrix": "COMPLIANCE_MATRIX",
	"Not Required": "NOT_REQUIRED",
}

EVIDENCE_LEVEL_LABELS = {
	"REQUIRED": "Evidence Required",
	"OPTIONAL": "Evidence Optional",
	"NOT_REQUIRED": "No Evidence Required",
}

EVIDENCE_LEVEL_REVERSE = {
	"Evidence Required": "REQUIRED",
	"Evidence Optional": "OPTIONAL",
	"No Evidence Required": "NOT_REQUIRED",
}

EVALUATION_CRITERION_LABELS = {
	"technical_solution_proposal": "Technical Solution Proposal",
	"security_controls": "Security Controls",
	"service_levels": "Service Levels",
}

STATUS_DISPLAY_LABELS = {
	"COMPLETE": "Complete",
	"NEEDS_REVIEW": "Needs Review",
	"MISSING_REQUIRED": "Missing Required Fields",
	"WARNING": "Warning",
}


def _category_for_row(row: dict[str, Any] | frappe._dict) -> str:
	category = (row.get("category") or "").strip()
	if category:
		return category
	return TYPE_TO_CATEGORY.get((row.get("requirement_type") or "").strip(), "Software")


def _evidence_level_for_row(row: dict[str, Any] | frappe._dict) -> str:
	level = (row.get("evidence_level") or "").strip()
	if level:
		return level
	return "REQUIRED" if int(row.get("evidence_required") or 0) else "NOT_REQUIRED"


def _treatment_label(priority: str) -> str:
	return PRIORITY_TO_TREATMENT.get((priority or "").strip(), "Informational")


def _evaluation_linked(priority: str, evaluation_binding: str) -> bool:
	return (priority or "").strip() == "SCORED" or bool((evaluation_binding or "").strip())


def _bidder_evidence_label(row: dict[str, Any] | frappe._dict) -> str:
	level = _evidence_level_for_row(row)
	instruction = (row.get("evidence_instruction") or "").strip()
	if level == "NOT_REQUIRED":
		return "No Evidence Required"
	if level == "OPTIONAL":
		return "Evidence Optional"
	if not instruction:
		return "Missing Evidence Instruction"
	return "Evidence Required"


def _acceptance_label(row: dict[str, Any] | frappe._dict) -> str:
	criteria = (row.get("acceptance_criteria") or "").strip()
	priority = (row.get("priority") or "").strip()
	if criteria:
		return "Criteria Defined"
	if priority in {"", "INFORMATIONAL", "DESIRABLE"}:
		return "Not Applicable"
	return "Missing Criteria"


def _contract_carry_forward_summary(row: dict[str, Any] | frappe._dict) -> str:
	if int(row.get("contract_carry_forward") or 0):
		return "Yes"
	if (row.get("priority") or "").strip() == "MANDATORY":
		return "To Be Decided"
	return "No"


def _derive_item_status(row: dict[str, Any] | frappe._dict) -> str:
	if not _item_is_complete(row):
		return "MISSING_REQUIRED"
	priority = (row.get("priority") or "").strip()
	evaluation_binding = (row.get("evaluation_binding") or "").strip()
	if priority == "SCORED" and not evaluation_binding:
		return "NEEDS_REVIEW"
	if _bidder_evidence_label(row) == "Missing Evidence Instruction":
		return "WARNING"
	if not (row.get("acceptance_criteria") or "").strip() and priority == "MANDATORY":
		return "WARNING"
	if _has_vendor_neutrality_warning(row):
		return "WARNING"
	return "COMPLETE"


def _has_vendor_neutrality_warning(row: dict[str, Any] | frappe._dict) -> bool:
	text = f"{row.get('title') or ''} {row.get('description') or ''}".lower()
	return (row.get("requirement_code") or "").strip() == "3.2" or "proprietary architecture" in text


def _item_warnings(row: dict[str, Any] | frappe._dict) -> list[str]:
	warnings: list[str] = []
	if not (row.get("description") or "").strip():
		warnings.append("Missing mandatory requirement description.")
	if _bidder_evidence_label(row) == "Missing Evidence Instruction":
		warnings.append("Evidence instruction missing.")
	if _acceptance_label(row) == "Missing Criteria":
		warnings.append("Acceptance criteria missing.")
	if (row.get("priority") or "").strip() == "SCORED" and not (row.get("evaluation_binding") or "").strip():
		warnings.append("Evaluation-linked requirement has no related evaluation criterion.")
	if _has_vendor_neutrality_warning(row):
		warnings.append(
			"Potential vendor-neutrality issue. Ensure capacity and performance requirements "
			"do not favor a specific proprietary architecture unless justified."
		)
	return warnings


def _item_is_complete(row: dict[str, Any] | frappe._dict) -> bool:
	return all(
		[
			(row.get("requirement_code") or "").strip(),
			(row.get("title") or "").strip(),
			(row.get("description") or "").strip(),
			(row.get("requirement_type") or "").strip(),
			(row.get("priority") or "").strip(),
		]
	)


def _enrich_seed_defaults(item: dict[str, Any]) -> dict[str, Any]:
	item = dict(item)
	item.setdefault("category", _category_for_row(item))
	item.setdefault("evidence_level", _evidence_level_for_row(item))
	item.setdefault(
		"bidder_instruction",
		f"Respond to requirement {item.get('requirement_code')} per the stated format.",
	)
	if int(item.get("evidence_required") or 0):
		item.setdefault(
			"evidence_instruction",
			"Provide supporting documentation or datasheet evidence for this requirement.",
		)
	else:
		item.setdefault("evidence_instruction", "")
	item.setdefault(
		"acceptance_criteria",
		"Procuring entity will verify compliance against the stated requirement during evaluation and delivery.",
	)
	return item


def _dedupe_requirements_docs(instance_name: str) -> str | None:
	rows = frappe.get_all(
		"Tender STD IT Requirements",
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
		frappe.delete_doc("Tender STD IT Requirements", row["name"], ignore_permissions=True)
	return keeper


def _requirements_doc_name(instance_name: str) -> str | None:
	return _dedupe_requirements_docs(instance_name)


def _default_seed_items(*, complete: bool) -> list[dict[str, Any]]:
	items: list[dict[str, Any]] = [
		_enrich_seed_defaults(
			{
				"requirement_code": "3.1",
				"title": "Server Processor Architecture",
				"description": "The proposed servers must use x86-64 architecture with a minimum of 32 cores per host.",
				"section_key": "technical_3_0",
				"requirement_type": "ARCHITECTURAL",
				"category": "Hardware",
				"priority": "MANDATORY",
				"supplier_response_required": 1,
				"evidence_required": 1,
				"evidence_level": "REQUIRED",
				"response_format": "YES_NO",
				"evaluation_binding": "technical_solution_proposal",
				"contract_carry_forward": 1,
			}
		),
		_enrich_seed_defaults(
			{
				"requirement_code": "3.2",
				"title": "Storage Array Capacity (Usable)",
				"description": (
					"The proposed solution must provide a minimum of 50TB usable All-Flash NVMe storage "
					"capacity after RAID penalty and formatting."
				),
				"section_key": "technical_3_0",
				"requirement_type": "PERFORMANCE",
				"category": "Hardware",
				"priority": "SCORED",
				"supplier_response_required": 1,
				"evidence_required": 1,
				"evidence_level": "REQUIRED",
				"response_format": "NUMERIC",
				"evaluation_binding": "" if not complete else "technical_solution_proposal",
				"contract_carry_forward": 1,
			}
		),
		_enrich_seed_defaults(
			{
				"requirement_code": "3.3",
				"title": "Network Interface Bandwidth",
				"description": "Each compute node must provide dual 25GbE network interfaces with redundant paths.",
				"section_key": "technical_3_0",
				"requirement_type": "ARCHITECTURAL",
				"category": "Hardware",
				"priority": "MANDATORY",
				"supplier_response_required": 1,
				"evidence_required": 1,
				"evidence_level": "REQUIRED",
				"response_format": "YES_NO",
				"evaluation_binding": "technical_solution_proposal",
				"contract_carry_forward": 0,
			}
		),
	]
	for index in range(4, 13):
		items.append(
			_enrich_seed_defaults(
				{
					"requirement_code": f"3.{index}",
					"title": f"Technical Requirement {index}",
					"description": f"Technical specification requirement {index} for data center refresh.",
					"section_key": "technical_3_0",
					"requirement_type": "FUNCTIONAL",
					"category": "Software",
					"priority": "MANDATORY" if index % 2 else "INFORMATIONAL",
					"supplier_response_required": 1,
					"evidence_required": 1,
					"evidence_level": "REQUIRED",
					"response_format": "YES_NO",
					"evaluation_binding": "technical_solution_proposal",
					"contract_carry_forward": 0,
				}
			)
		)
	for index in range(1, 6):
		items.append(
			_enrich_seed_defaults(
				{
					"requirement_code": f"4.{index}",
					"title": f"Security Requirement {index}",
					"description": "" if (not complete and index > 3) else f"Security and compliance control {index}.",
					"section_key": "security_4_0",
					"requirement_type": "SECURITY",
					"category": "Security",
					"priority": "MANDATORY",
					"supplier_response_required": 1,
					"evidence_required": 1,
					"evidence_level": "REQUIRED",
					"response_format": "YES_NO",
					"evaluation_binding": "" if (not complete and index == 2) else "security_controls",
					"contract_carry_forward": 1,
				}
			)
		)
	for index in range(1, 9):
		items.append(
			_enrich_seed_defaults(
				{
					"requirement_code": f"2.{index}",
					"title": f"Functional Requirement {index}",
					"description": "" if (not complete and index > 6) else f"Functional capability requirement {index}.",
					"section_key": "functional_2_0",
					"requirement_type": "FUNCTIONAL",
					"category": "Software",
					"priority": "MANDATORY",
					"supplier_response_required": 1,
					"evidence_required": 0,
					"evidence_level": "NOT_REQUIRED",
					"response_format": "YES_NO",
					"evaluation_binding": "",
					"contract_carry_forward": 0,
					"acceptance_criteria": "" if (not complete and index > 6) else "Criteria Defined placeholder",
				}
			)
		)
	for index in range(1, 6):
		items.append(
			_enrich_seed_defaults(
				{
					"requirement_code": f"5.{index}",
					"title": f"Service Requirement {index}",
					"description": f"Support and maintenance obligation {index}.",
					"section_key": "service_5_0",
					"requirement_type": "SERVICE",
					"category": "Support",
					"priority": "MANDATORY",
					"supplier_response_required": 1,
					"evidence_required": 1,
					"evidence_level": "REQUIRED",
					"response_format": "DOCUMENT_EVIDENCE",
					"evaluation_binding": "service_levels",
					"contract_carry_forward": 1,
				}
			)
		)
	if not complete:
		items[1]["evaluation_binding"] = ""
		items[1]["evidence_instruction"] = ""
		items[12]["description"] = ""
		items[13]["description"] = ""
		items[18]["description"] = ""
		items[18]["acceptance_criteria"] = ""
	return items


def _serialize_item(row: dict[str, Any] | frappe._dict) -> dict[str, Any]:
	code = (row.get("requirement_code") or "").strip()
	priority = (row.get("priority") or "").strip()
	evidence_required = int(row.get("evidence_required") or 0)
	evaluation_binding = (row.get("evaluation_binding") or "").strip()
	description = (row.get("description") or "").strip()
	requirement_type = (row.get("requirement_type") or "").strip()
	category = _category_for_row(row)
	treatment = _treatment_label(priority)
	status = _derive_item_status(row)
	summary = description[:80] + ("…" if len(description) > 80 else "") if description else ""
	return {
		"item_id": code,
		"requirement_code": code,
		"title": (row.get("title") or "").strip(),
		"description": description,
		"summary": summary,
		"section_key": (row.get("section_key") or "").strip(),
		"category": category,
		"requirement_type": requirement_type,
		"priority": priority,
		"treatment": treatment,
		"treatment_label": treatment,
		"evaluation_linked": _evaluation_linked(priority, evaluation_binding),
		"evaluation_linked_label": "Linked to Evaluation" if _evaluation_linked(priority, evaluation_binding) else "",
		"supplier_response_required": int(row.get("supplier_response_required") or 0),
		"evidence_required": evidence_required,
		"evidence_level": _evidence_level_for_row(row),
		"evidence_level_label": _bidder_evidence_label(row),
		"evidence_instruction": (row.get("evidence_instruction") or "").strip(),
		"bidder_instruction": (row.get("bidder_instruction") or "").strip(),
		"acceptance_criteria": (row.get("acceptance_criteria") or "").strip(),
		"acceptance_label": _acceptance_label(row),
		"response_format": (row.get("response_format") or "").strip(),
		"response_format_label": RESPONSE_FORMAT_LABELS.get(
			(row.get("response_format") or "").strip(),
			(row.get("response_format") or "").strip() or "—",
		),
		"evaluation_binding": evaluation_binding,
		"evaluation_criterion_label": EVALUATION_CRITERION_LABELS.get(
			evaluation_binding,
			evaluation_binding.replace("_", " ").title() if evaluation_binding else "—",
		),
		"contract_carry_forward": int(row.get("contract_carry_forward") or 0),
		"contract_carry_forward_summary": _contract_carry_forward_summary(row),
		"template_locked": int(row.get("template_locked") or 0),
		"status": status,
		"status_label": STATUS_DISPLAY_LABELS.get(status, status),
		"warnings": _item_warnings(row),
	}


def compute_requirements_completion(items: list[dict[str, Any]]) -> dict[str, Any]:
	total = len(items)
	completed = sum(
		1 for row in items if (row.get("status") or _derive_item_status(row)) != "MISSING_REQUIRED"
	)
	missing_fields: list[str] = []
	if completed < total:
		missing_fields.append(f"{total - completed} incomplete requirement(s)")
	missing_mandatory = sum(
		1
		for row in items
		if (row.get("priority") or row.get("treatment")) in {"MANDATORY", "Mandatory"}
		and row.get("status") == "MISSING_REQUIRED"
	)
	missing_evidence_instructions = sum(
		1 for row in items if row.get("evidence_level_label") == "Missing Evidence Instruction"
	)
	missing_acceptance_criteria = sum(1 for row in items if row.get("acceptance_label") == "Missing Criteria")
	vendor_warnings = sum(1 for row in items if _has_vendor_neutrality_warning(row))
	percent = int(round((completed / total) * 100)) if total else 0
	return {
		"completed": completed,
		"total": total,
		"missing_fields": missing_fields,
		"percent": percent,
		"gaps": {
			"missing_mandatory": missing_mandatory,
			"missing_evidence_instructions": missing_evidence_instructions,
			"missing_acceptance_criteria": missing_acceptance_criteria,
			"vendor_neutrality_warnings": vendor_warnings,
		},
	}


def _group_sections(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
	sections: dict[str, list[dict[str, Any]]] = {}
	for row in items:
		key = row.get("section_key") or "uncategorized"
		sections.setdefault(key, []).append(row)
	result = []
	for section_key in sorted(sections, key=lambda key: list(SECTION_META.keys()).index(key) if key in SECTION_META else 99):
		section_items = sorted(sections[section_key], key=lambda row: row.get("requirement_code") or "")
		result.append(
			{
				"section_key": section_key,
				"title": SECTION_META.get(section_key, section_key),
				"item_count": len(section_items),
				"items": section_items,
			}
		)
	return result


def _ensure_requirements_doc(instance_name: str, *, seed_complete: bool | None = None) -> frappe.model.document.Document:
	name = _requirements_doc_name(instance_name)
	if name:
		return frappe.get_doc("Tender STD IT Requirements", name)
	complete = True if seed_complete is None else seed_complete
	doc = frappe.get_doc(
		{
			"doctype": "Tender STD IT Requirements",
			"tender_std_instance": instance_name,
			"selected_item_code": "3.2",
			"items": _default_seed_items(complete=complete),
		}
	)
	try:
		doc.insert(ignore_permissions=True)
	except (frappe.DuplicateEntryError, frappe.UniqueValidationError):
		frappe.db.rollback()
		name = _requirements_doc_name(instance_name)
		if not name:
			raise
		return frappe.get_doc("Tender STD IT Requirements", name)
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
		{"tender_std_instance": instance_name, "step_code": IT_REQUIREMENTS_STEP_CODE},
	)
	if not step_name:
		return
	status = "COMPLETE" if complete else "IN_PROGRESS"
	frappe.db.set_value("Wizard Step Instance", step_name, "status", status)


def _normalize_incoming_row(row: dict[str, Any]) -> dict[str, Any]:
	normalized = dict(row)
	treatment = (row.get("treatment") or row.get("treatment_label") or "").strip()
	if treatment:
		normalized["priority"] = TREATMENT_TO_PRIORITY.get(treatment, normalized.get("priority") or "MANDATORY")
	response_label = (row.get("response_format_label") or row.get("response_format") or "").strip()
	if response_label in RESPONSE_FORMAT_REVERSE:
		normalized["response_format"] = RESPONSE_FORMAT_REVERSE[response_label]
	evidence_label = (row.get("evidence_level_label") or row.get("evidence_level") or "").strip()
	if evidence_label in EVIDENCE_LEVEL_REVERSE:
		normalized["evidence_level"] = EVIDENCE_LEVEL_REVERSE[evidence_label]
		normalized["evidence_required"] = 0 if normalized["evidence_level"] == "NOT_REQUIRED" else 1
	return normalized


def _validate_items_payload(items: list[dict[str, Any]]) -> None:
	codes: set[str] = set()
	for row in items:
		code = (row.get("requirement_code") or "").strip()
		if not code:
			frappe.throw("Requirement code is required for every item.")
		if code in codes:
			frappe.throw(f"Duplicate requirement code: {code}")
		codes.add(code)
		priority = (row.get("priority") or "").strip()
		if priority == "MANDATORY":
			if not (row.get("title") or "").strip():
				frappe.throw(f"Mandatory requirement {code} requires a title.")
			if not (row.get("description") or "").strip():
				frappe.throw(f"Mandatory requirement {code} requires a description.")
			if not (row.get("requirement_type") or "").strip():
				frappe.throw(f"Mandatory requirement {code} requires a requirement type.")


def _apply_items_to_doc(doc, items: list[dict[str, Any]]) -> None:
	doc.set("items", [])
	for raw in items:
		row = _normalize_incoming_row(raw)
		doc.append(
			"items",
			{
				"requirement_code": (row.get("requirement_code") or "").strip(),
				"title": (row.get("title") or "").strip(),
				"description": (row.get("description") or "").strip(),
				"section_key": (row.get("section_key") or "").strip(),
				"category": _category_for_row(row),
				"requirement_type": (row.get("requirement_type") or "").strip(),
				"priority": (row.get("priority") or "MANDATORY").strip(),
				"supplier_response_required": 1 if row.get("supplier_response_required") else 0,
				"evidence_required": 1 if row.get("evidence_required") else 0,
				"evidence_level": _evidence_level_for_row(row),
				"evidence_instruction": (row.get("evidence_instruction") or "").strip(),
				"response_format": (row.get("response_format") or "YES_NO").strip() or "YES_NO",
				"bidder_instruction": (row.get("bidder_instruction") or "").strip(),
				"acceptance_criteria": (row.get("acceptance_criteria") or "").strip(),
				"evaluation_binding": (row.get("evaluation_binding") or "").strip(),
				"contract_carry_forward": 1 if row.get("contract_carry_forward") else 0,
				"template_locked": 1 if row.get("template_locked") else 0,
				"field_sources_json": (row.get("field_sources_json") or "").strip(),
			},
		)


def _build_payload(configuration_id: str, doc, overview: dict[str, Any]) -> dict[str, Any]:
	raw_rows = [row.as_dict() for row in doc.items]
	serialized = [_serialize_item(row) for row in raw_rows]
	completion = compute_requirements_completion(serialized)
	blockers, warnings = _latest_validation_counts(doc.tender_std_instance)
	selected_item_code = (doc.selected_item_code or "").strip() or (serialized[0]["requirement_code"] if serialized else "")
	return {
		"configuration_id": configuration_id,
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
		"selected_item_id": selected_item_code,
		"sections": _group_sections(serialized),
		"completion": completion,
	}


def get_it_requirements(configuration_id: str) -> dict[str, Any]:
	assert_permission(PERM_VIEW)
	instance = _get_instance(configuration_id)
	overview = build_configuration_overview(configuration_id)
	doc = _ensure_requirements_doc(instance.name)
	return _build_payload(configuration_id, doc, overview)


def save_it_requirements(configuration_id: str, payload: dict[str, Any]) -> dict[str, Any]:
	assert_permission(PERM_CREATE)
	instance = _get_instance(configuration_id)
	doc = _ensure_requirements_doc(instance.name)
	items = payload.get("items")
	selected_only = False
	if items is None:
		selected = payload.get("selected_item") or {}
		if selected:
			existing = {row.requirement_code: row.as_dict() for row in doc.items}
			code = (selected.get("requirement_code") or doc.selected_item_code or "").strip()
			if code and code in existing:
				existing[code].update(_normalize_incoming_row(selected))
				items = list(existing.values())
				selected_only = True
			else:
				items = [row.as_dict() for row in doc.items]
		else:
			items = [row.as_dict() for row in doc.items]
	if selected_only:
		code = (payload.get("selected_item_id") or doc.selected_item_code or "").strip()
		target = next((row for row in items if row.get("requirement_code") == code), None)
		if target:
			_validate_items_payload([target])
	else:
		_validate_items_payload(items)
	_apply_items_to_doc(doc, items)
	if payload.get("selected_item_id"):
		doc.selected_item_code = (payload.get("selected_item_id") or "").strip()
	elif payload.get("selected_item", {}).get("requirement_code"):
		doc.selected_item_code = (payload["selected_item"]["requirement_code"] or "").strip()
	doc.save(ignore_permissions=True)
	serialized = [_serialize_item(row.as_dict()) for row in doc.items]
	completion = compute_requirements_completion(serialized)
	complete = (
		not completion["gaps"]["missing_mandatory"]
		and not completion["gaps"]["missing_evidence_instructions"]
		and not completion["gaps"]["missing_acceptance_criteria"]
	)
	_update_step_status(instance.name, complete=complete)
	return get_it_requirements(configuration_id)
