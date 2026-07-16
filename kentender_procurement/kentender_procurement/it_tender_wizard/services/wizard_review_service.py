# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Review and Approval contracts for ITW-13."""

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

STEP_CODE = "REVIEW_AND_APPROVAL"
REVIEW_AND_APPROVAL_STEP_CODE = STEP_CODE
DECISIONS = {"PENDING", "APPROVED", "RETURNED"}

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


def _default_seed_decisions(*, complete: bool) -> list[dict[str, Any]]:
	rows = [
		{
			"stage_code": "PROCUREMENT_REVIEW",
			"stage_title": "Procurement Review",
			"decision": "APPROVED" if complete else "PENDING",
			"comment": "Seed procurement review stage.",
			"decided_by": "Administrator" if complete else "",
			"decided_at": frappe.utils.now_datetime() if complete else None,
		},
		{
			"stage_code": "LEGAL_REVIEW",
			"stage_title": "Legal Review",
			"decision": "APPROVED" if complete else "PENDING",
			"comment": "Seed legal review stage.",
			"decided_by": "Administrator" if complete else "",
			"decided_at": frappe.utils.now_datetime() if complete else None,
		},
	]
	for display_order, row in enumerate(rows, start=1):
		row["display_order"] = display_order
	return rows


def _append_decision(doc, raw: dict[str, Any]) -> None:
	doc.append(
		"decisions",
		{
			"stage_code": str(raw.get("stage_code") or "").strip().upper(),
			"stage_title": str(raw.get("stage_title") or "").strip(),
			"decision": str(raw.get("decision") or "PENDING").strip(),
			"comment": str(raw.get("comment") or "").strip(),
			"decided_by": str(raw.get("decided_by") or "").strip(),
			"decided_at": raw.get("decided_at"),
			"display_order": int(raw.get("display_order") or 0),
		},
	)


def _ensure_review_doc(instance_name: str, *, seed_complete: bool | None = None):
	name = _dedupe_docs("Tender STD Review", instance_name)
	if name:
		return frappe.get_doc("Tender STD Review", name)
	doc = frappe.get_doc(
		{
			"doctype": "Tender STD Review",
			"tender_std_instance": instance_name,
			"review_code": STEP_CODE,
			"review_title": "Review and Approval",
			"description": "Review stages and decisions for the configuration.",
			"review_status": "APPROVED" if seed_complete else "DRAFT",
			"lock_status": "UNLOCKED",
		}
	)
	for row in _default_seed_decisions(complete=bool(seed_complete)):
		_append_decision(doc, row)
	try:
		doc.insert(ignore_permissions=True)
	except (frappe.DuplicateEntryError, frappe.UniqueValidationError):
		frappe.db.rollback()
		name = _dedupe_docs("Tender STD Review", instance_name)
		if not name:
			raise
		return frappe.get_doc("Tender STD Review", name)
	return doc


def _serialize_decision(row: dict[str, Any] | frappe._dict) -> dict[str, Any]:
	code = str(row.get("stage_code") or "").strip()
	return {
		"stage_id": code,
		"stage_code": code,
		"stage_title": str(row.get("stage_title") or "").strip(),
		"decision": str(row.get("decision") or "").strip(),
		"comment": str(row.get("comment") or "").strip(),
		"decided_by": str(row.get("decided_by") or "").strip(),
		"decided_at": str(row.get("decided_at") or "") if row.get("decided_at") else "",
		"display_order": int(row.get("display_order") or 0),
	}


def _validate_decisions(items: list[dict[str, Any]]) -> None:
	codes: set[str] = set()
	for raw in items:
		code = str(raw.get("stage_code") or "").strip().upper()
		if not code or not STABLE_CODE_PATTERN.fullmatch(code):
			frappe.throw("Review stage code is required and must use uppercase letters, numbers, hyphens, or underscores.")
		if code in codes:
			frappe.throw(f"Duplicate review stage code: {code}")
		codes.add(code)
		if not str(raw.get("stage_title") or "").strip():
			frappe.throw(f"Review stage {code} requires a title.")
		if str(raw.get("decision") or "").strip() not in DECISIONS:
			frappe.throw(f"Review stage {code} has an invalid decision.")


def _build_payload(configuration_id: str, doc, overview: dict[str, Any]) -> dict[str, Any]:
	decisions = [_serialize_decision(row.as_dict()) for row in doc.decisions]
	approved = sum(1 for d in decisions if d["decision"] == "APPROVED")
	payload = _overview_context(configuration_id, doc.tender_std_instance, overview)
	payload.update(
		{
			"review_code": str(doc.review_code or "").strip(),
			"review_title": str(doc.review_title or "").strip(),
			"description": str(doc.description or "").strip(),
			"review_status": str(doc.review_status or "").strip(),
			"lock_status": str(doc.lock_status or "").strip(),
			"decisions": decisions,
			"completion": {
				"completed": approved,
				"total": len(decisions),
				"percent": int(round(approved / len(decisions) * 100)) if decisions else 0,
			},
		}
	)
	return payload


def get_review_and_approval(configuration_id: str) -> dict[str, Any]:
	assert_permission(PERM_VIEW)
	instance = _get_instance(configuration_id)
	doc = _ensure_review_doc(instance.name)
	return _build_payload(configuration_id, doc, build_configuration_overview(configuration_id))


def save_review_and_approval(configuration_id: str, payload: dict[str, Any]) -> dict[str, Any]:
	assert_permission(PERM_CREATE)
	instance = _get_instance(configuration_id)
	assert_configuration_editable(instance.wizard_state)
	doc = _ensure_review_doc(instance.name)
	if str(doc.lock_status or "").strip() != "UNLOCKED":
		frappe.throw(
			f"Review is locked with status {doc.lock_status}.",
			title="ITW_REVIEW_LOCKED",
			exc=frappe.ValidationError,
		)
	items = list(payload.get("decisions") or [])
	_validate_decisions(items)
	doc.set("decisions", [])
	for row in items:
		_append_decision(doc, row)
	if payload.get("review_title") is not None:
		doc.review_title = str(payload.get("review_title") or "").strip()
	if payload.get("description") is not None:
		doc.description = str(payload.get("description") or "").strip()
	if payload.get("review_status") is not None:
		doc.review_status = str(payload.get("review_status") or "").strip()
	doc.save(ignore_permissions=True)
	decisions = [_serialize_decision(row.as_dict()) for row in doc.decisions]
	complete = bool(decisions) and all(d["decision"] == "APPROVED" for d in decisions)
	_update_step_status(instance.name, complete=complete)
	return _build_payload(configuration_id, doc, build_configuration_overview(configuration_id))
