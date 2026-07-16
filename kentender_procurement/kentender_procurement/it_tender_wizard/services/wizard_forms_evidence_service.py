# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Forms and Evidence contracts for ITW-10."""

from __future__ import annotations

import json
import re
from typing import Any

import frappe

from kentender_procurement.it_tender_wizard.services.wizard_instance_service import _get_instance
from kentender_procurement.it_tender_wizard.services.wizard_overview_service import build_configuration_overview
from kentender_procurement.it_tender_wizard.services.wizard_permission_service import (
	PERM_CREATE,
	PERM_VIEW,
	assert_permission,
)
from kentender_procurement.it_tender_wizard.services.wizard_state_guard_service import (
	assert_configuration_editable,
)

STEP_CODE = "FORMS_AND_EVIDENCE"
FORMS_AND_EVIDENCE_STEP_CODE = STEP_CODE
SUBMISSION_RULES = {"MANDATORY", "CONDITIONAL", "OPTIONAL"}

STABLE_CODE_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9_-]*$")
REVIEW_STATUSES = {"DRAFT", "NEEDS_REVIEW", "APPROVED", "RETURNED"}


def _public_reference(reference: Any) -> dict[str, str]:
	if not isinstance(reference, dict):
		return {"code": "", "name": ""}
	return {
		"code": str(reference.get("code") or "").strip(),
		"name": str(reference.get("name") or "").strip(),
	}


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
		{"tender_std_instance": instance_name, "step_code": STEP_CODE},
	)
	if step_name:
		frappe.db.set_value(
			"Wizard Step Instance",
			step_name,
			"status",
			"COMPLETE" if complete else "IN_PROGRESS",
		)


def _dedupe_docs(doctype: str, instance_name: str) -> str | None:
	rows = frappe.get_all(
		doctype,
		filters={"tender_std_instance": instance_name},
		fields=["name", "modified"],
		order_by="modified desc",
	)
	if not rows:
		return None
	keeper = rows[0]["name"]
	for row in rows[1:]:
		frappe.delete_doc(doctype, row["name"], ignore_permissions=True)
	return keeper


def _overview_context(configuration_id: str, instance_name: str, overview: dict[str, Any]) -> dict[str, Any]:
	blockers, warnings = _latest_validation_counts(instance_name)
	tender_number = (
		frappe.db.get_value(
			"Tender STD TDS",
			{"tender_std_instance": instance_name},
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
		"planning_package": _public_reference(overview.get("planning_package")),
		"procuring_entity": _public_reference(overview.get("procuring_entity")),
		"method": _public_reference(overview.get("method")),
		"validation": {"blockers": blockers, "warnings": warnings},
	}


def _default_seed_items(*, complete: bool) -> list[dict[str, Any]]:
	rows = [
		{
			"item_code": "FORM-TECH-001",
			"title": "Technical Proposal Form",
			"submission_rule": "MANDATORY",
			"accepted_format": "PDF",
			"bidder_instruction": "Submit the completed technical proposal form.",
			"linked_requirement_code": "3.1",
			"linked_criterion_code": "EV-SCORE-001",
		},
		{
			"item_code": "FORM-FIN-001",
			"title": "Price Schedule Form",
			"submission_rule": "MANDATORY",
			"accepted_format": "XLSX",
			"bidder_instruction": "Complete all mandatory price lines.",
			"linked_criterion_code": "EV-SCORE-002",
		},
		{
			"item_code": "EVID-REF-001",
			"title": "Reference Letters",
			"submission_rule": "OPTIONAL",
			"accepted_format": "PDF",
			"bidder_instruction": "Optional reference letters from prior clients.",
		},
	]
	for display_order, row in enumerate(rows, start=1):
		row["display_order"] = display_order
	return rows


def _append_item(doc, raw: dict[str, Any]) -> None:
	doc.append(
		"items",
		{
			"item_code": str(raw.get("item_code") or "").strip().upper(),
			"title": str(raw.get("title") or "").strip(),
			"submission_rule": str(raw.get("submission_rule") or "MANDATORY").strip(),
			"accepted_format": str(raw.get("accepted_format") or "").strip(),
			"bidder_instruction": str(raw.get("bidder_instruction") or "").strip(),
			"linked_requirement_code": str(raw.get("linked_requirement_code") or "").strip(),
			"linked_criterion_code": str(raw.get("linked_criterion_code") or "").strip(),
			"display_order": int(raw.get("display_order") or 0),
		},
	)


def _ensure_forms_evidence_doc(instance_name: str, *, seed_complete: bool | None = None):
	name = _dedupe_docs("Tender STD Forms Evidence", instance_name)
	if name:
		return frappe.get_doc("Tender STD Forms Evidence", name)
	doc = frappe.get_doc(
		{
			"doctype": "Tender STD Forms Evidence",
			"tender_std_instance": instance_name,
			"forms_code": STEP_CODE,
			"forms_title": "Forms and Evidence",
			"description": "Bidder submission forms and evidence requirements.",
			"review_status": "APPROVED" if seed_complete else "DRAFT",
			"lock_status": "UNLOCKED",
		}
	)
	for row in _default_seed_items(complete=bool(seed_complete)):
		_append_item(doc, row)
	try:
		doc.insert(ignore_permissions=True)
	except (frappe.DuplicateEntryError, frappe.UniqueValidationError):
		frappe.db.rollback()
		name = _dedupe_docs("Tender STD Forms Evidence", instance_name)
		if not name:
			raise
		return frappe.get_doc("Tender STD Forms Evidence", name)
	return doc


def _serialize_item(row: dict[str, Any] | frappe._dict) -> dict[str, Any]:
	code = str(row.get("item_code") or "").strip()
	return {
		"item_id": code,
		"item_code": code,
		"title": str(row.get("title") or "").strip(),
		"submission_rule": str(row.get("submission_rule") or "").strip(),
		"accepted_format": str(row.get("accepted_format") or "").strip(),
		"bidder_instruction": str(row.get("bidder_instruction") or "").strip(),
		"linked_requirement_code": str(row.get("linked_requirement_code") or "").strip(),
		"linked_criterion_code": str(row.get("linked_criterion_code") or "").strip(),
		"display_order": int(row.get("display_order") or 0),
	}


def _validate_items(items: list[dict[str, Any]]) -> None:
	codes: set[str] = set()
	for raw in items:
		code = str(raw.get("item_code") or "").strip().upper()
		if not code or not STABLE_CODE_PATTERN.fullmatch(code):
			frappe.throw("Form evidence item code is required and must use uppercase letters, numbers, hyphens, or underscores.")
		if code in codes:
			frappe.throw(f"Duplicate form evidence item code: {code}")
		codes.add(code)
		if not str(raw.get("title") or "").strip():
			frappe.throw(f"Form evidence item {code} requires a title.")
		if str(raw.get("submission_rule") or "").strip() not in SUBMISSION_RULES:
			frappe.throw(f"Form evidence item {code} has an invalid submission rule.")


def _item_complete(item: dict[str, Any]) -> bool:
	return bool(item.get("item_code") and item.get("title") and item.get("submission_rule") in SUBMISSION_RULES)


def _build_payload(configuration_id: str, doc, overview: dict[str, Any]) -> dict[str, Any]:
	items = [_serialize_item(row.as_dict()) for row in doc.items]
	completed = sum(1 for item in items if _item_complete(item))
	payload = _overview_context(configuration_id, doc.tender_std_instance, overview)
	payload.update(
		{
			"forms_code": str(doc.forms_code or "").strip(),
			"forms_title": str(doc.forms_title or "").strip(),
			"description": str(doc.description or "").strip(),
			"review_status": str(doc.review_status or "").strip(),
			"lock_status": str(doc.lock_status or "").strip(),
			"items": items,
			"completion": {
				"completed": completed,
				"total": len(items),
				"percent": int(round(completed / len(items) * 100)) if items else 0,
			},
		}
	)
	return payload


def get_forms_and_evidence(configuration_id: str) -> dict[str, Any]:
	assert_permission(PERM_VIEW)
	instance = _get_instance(configuration_id)
	doc = _ensure_forms_evidence_doc(instance.name)
	return _build_payload(configuration_id, doc, build_configuration_overview(configuration_id))


def save_forms_and_evidence(configuration_id: str, payload: dict[str, Any]) -> dict[str, Any]:
	assert_permission(PERM_CREATE)
	instance = _get_instance(configuration_id)
	assert_configuration_editable(instance.wizard_state)
	doc = _ensure_forms_evidence_doc(instance.name)
	if str(doc.lock_status or "").strip() != "UNLOCKED":
		frappe.throw(
			f"Forms and evidence is locked with status {doc.lock_status}.",
			title="ITW_FORMS_LOCKED",
			exc=frappe.ValidationError,
		)
	items = list(payload.get("items") or [])
	_validate_items(items)
	doc.set("items", [])
	for row in items:
		_append_item(doc, row)
	if payload.get("forms_title") is not None:
		doc.forms_title = str(payload.get("forms_title") or "").strip()
	if payload.get("description") is not None:
		doc.description = str(payload.get("description") or "").strip()
	if payload.get("review_status") is not None:
		doc.review_status = str(payload.get("review_status") or "").strip()
	doc.save(ignore_permissions=True)
	serialized = [_serialize_item(row.as_dict()) for row in doc.items]
	complete = bool(serialized) and all(_item_complete(item) for item in serialized) and str(doc.review_status) == "APPROVED"
	_update_step_status(instance.name, complete=complete)
	return _build_payload(configuration_id, doc, build_configuration_overview(configuration_id))
