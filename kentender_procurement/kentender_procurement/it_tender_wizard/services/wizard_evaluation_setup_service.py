# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Evaluation Setup contracts for ITW-09."""

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

STEP_CODE = "EVALUATION_SETUP"
EVALUATION_SETUP_STEP_CODE = STEP_CODE
CRITERION_TYPES = {"MANDATORY", "SCORED", "INFORMATIONAL"}

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
			"criterion_code": "EV-MAND-001",
			"title": "Mandatory Technical Compliance",
			"criterion_type": "MANDATORY",
			"weight_marks": 0,
			"pass_mark": 1,
			"linked_requirement_code": "3.1",
			"evidence_instruction": "Confirm mandatory requirements are met.",
		},
		{
			"criterion_code": "EV-SCORE-001",
			"title": "Functional Fit",
			"criterion_type": "SCORED",
			"weight_marks": 40,
			"pass_mark": 24,
			"linked_requirement_code": "3.2",
			"evidence_instruction": "Describe functional coverage against requirements.",
		},
		{
			"criterion_code": "EV-SCORE-002",
			"title": "Implementation Approach",
			"criterion_type": "SCORED",
			"weight_marks": 30,
			"pass_mark": 18,
			"linked_requirement_code": "3.3",
			"evidence_instruction": "Describe delivery methodology and governance.",
		},
		{
			"criterion_code": "EV-INFO-001",
			"title": "Reference Sites",
			"criterion_type": "INFORMATIONAL",
			"weight_marks": 0,
			"pass_mark": 0,
			"evidence_instruction": "Provide reference deployments for information only.",
		},
	]
	for display_order, row in enumerate(rows, start=1):
		row["display_order"] = display_order
	return rows


def _append_item(doc, raw: dict[str, Any]) -> None:
	doc.append(
		"criteria",
		{
			"criterion_code": str(raw.get("criterion_code") or "").strip().upper(),
			"title": str(raw.get("title") or "").strip(),
			"criterion_type": str(raw.get("criterion_type") or "SCORED").strip(),
			"weight_marks": float(raw.get("weight_marks") or 0),
			"pass_mark": float(raw.get("pass_mark") or 0),
			"linked_requirement_code": str(raw.get("linked_requirement_code") or "").strip(),
			"evidence_instruction": str(raw.get("evidence_instruction") or "").strip(),
			"display_order": int(raw.get("display_order") or 0),
		},
	)


def _ensure_evaluation_setup_doc(instance_name: str, *, seed_complete: bool | None = None):
	name = _dedupe_docs("Tender STD Evaluation", instance_name)
	if name:
		return frappe.get_doc("Tender STD Evaluation", name)
	doc = frappe.get_doc(
		{
			"doctype": "Tender STD Evaluation",
			"tender_std_instance": instance_name,
			"evaluation_code": STEP_CODE,
			"evaluation_title": "Evaluation Setup",
			"description": "Scored and mandatory evaluation criteria for the tender.",
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
		name = _dedupe_docs("Tender STD Evaluation", instance_name)
		if not name:
			raise
		return frappe.get_doc("Tender STD Evaluation", name)
	return doc


def _serialize_item(row: dict[str, Any] | frappe._dict) -> dict[str, Any]:
	code = str(row.get("criterion_code") or "").strip()
	return {
		"criterion_id": code,
		"criterion_code": code,
		"title": str(row.get("title") or "").strip(),
		"criterion_type": str(row.get("criterion_type") or "").strip(),
		"weight_marks": float(row.get("weight_marks") or 0),
		"pass_mark": float(row.get("pass_mark") or 0),
		"linked_requirement_code": str(row.get("linked_requirement_code") or "").strip(),
		"evidence_instruction": str(row.get("evidence_instruction") or "").strip(),
		"display_order": int(row.get("display_order") or 0),
	}


def _validate_items(items: list[dict[str, Any]]) -> None:
	codes: set[str] = set()
	for raw in items:
		code = str(raw.get("criterion_code") or "").strip().upper()
		if not code or not STABLE_CODE_PATTERN.fullmatch(code):
			frappe.throw("Criterion code is required and must use uppercase letters, numbers, hyphens, or underscores.")
		if code in codes:
			frappe.throw(f"Duplicate criterion code: {code}")
		codes.add(code)
		if not str(raw.get("title") or "").strip():
			frappe.throw(f"Criterion {code} requires a title.")
		ctype = str(raw.get("criterion_type") or "").strip()
		if ctype not in CRITERION_TYPES:
			frappe.throw(f"Criterion {code} has an invalid type.")
		weight = float(raw.get("weight_marks") or 0)
		if ctype == "SCORED" and weight <= 0:
			frappe.throw(f"Scored criterion {code} requires weight_marks > 0.")


def _item_complete(item: dict[str, Any]) -> bool:
	ctype = item.get("criterion_type")
	if ctype == "SCORED":
		return bool(item.get("criterion_code") and item.get("title") and float(item.get("weight_marks") or 0) > 0)
	return bool(item.get("criterion_code") and item.get("title") and ctype in CRITERION_TYPES)


def _build_payload(configuration_id: str, doc, overview: dict[str, Any]) -> dict[str, Any]:
	items = [_serialize_item(row.as_dict()) for row in doc.criteria]
	completed = sum(1 for item in items if _item_complete(item))
	payload = _overview_context(configuration_id, doc.tender_std_instance, overview)
	payload.update(
		{
			"evaluation_code": str(doc.evaluation_code or "").strip(),
			"evaluation_title": str(doc.evaluation_title or "").strip(),
			"description": str(doc.description or "").strip(),
			"review_status": str(doc.review_status or "").strip(),
			"lock_status": str(doc.lock_status or "").strip(),
			"criteria": items,
			"completion": {
				"completed": completed,
				"total": len(items),
				"percent": int(round(completed / len(items) * 100)) if items else 0,
			},
		}
	)
	return payload


def get_evaluation_setup(configuration_id: str) -> dict[str, Any]:
	assert_permission(PERM_VIEW)
	instance = _get_instance(configuration_id)
	doc = _ensure_evaluation_setup_doc(instance.name)
	return _build_payload(configuration_id, doc, build_configuration_overview(configuration_id))


def save_evaluation_setup(configuration_id: str, payload: dict[str, Any]) -> dict[str, Any]:
	assert_permission(PERM_CREATE)
	instance = _get_instance(configuration_id)
	assert_configuration_editable(instance.wizard_state)
	doc = _ensure_evaluation_setup_doc(instance.name)
	if str(doc.lock_status or "").strip() != "UNLOCKED":
		frappe.throw(
			f"Evaluation setup is locked with status {doc.lock_status}.",
			title="ITW_EVALUATION_LOCKED",
			exc=frappe.ValidationError,
		)
	items = list(payload.get("criteria") or payload.get("items") or [])
	_validate_items(items)
	doc.set("criteria", [])
	for row in items:
		_append_item(doc, row)
	if payload.get("evaluation_title") is not None:
		doc.evaluation_title = str(payload.get("evaluation_title") or "").strip()
	if payload.get("description") is not None:
		doc.description = str(payload.get("description") or "").strip()
	if payload.get("review_status") is not None:
		doc.review_status = str(payload.get("review_status") or "").strip()
	doc.save(ignore_permissions=True)
	serialized = [_serialize_item(row.as_dict()) for row in doc.criteria]
	complete = bool(serialized) and all(_item_complete(item) for item in serialized) and str(doc.review_status) == "APPROVED"
	_update_step_status(instance.name, complete=complete)
	return _build_payload(configuration_id, doc, build_configuration_overview(configuration_id))
